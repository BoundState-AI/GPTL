"""
Module: Tier 2 Advisory Retrieval
Purpose: Governed deterministic Tier 2 retrieval contracts.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.directives import DisplayDirective
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalDecimal,
    EvidenceLocator,
    FieldId,
    TermId,
)

RetrievalLane = Literal["EXACT", "CONTROLLED_TERM", "RELATIONAL", "LEXICAL"]
RouteTrigger = Literal["METHOD_AMBIGUOUS", "METHOD_UNKNOWN", "TIER1_ROUTE_REASON"]

RETRIEVAL_LANE_ORDER: tuple[RetrievalLane, ...] = (
    "EXACT",
    "CONTROLLED_TERM",
    "RELATIONAL",
    "LEXICAL",
)
ASCII_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
LEXICAL_UNICODE_DATA_VERSION = "3.2.0"
# CPython's default UCD changes across minors; the frozen table keeps governed replay portable.
_LEXICAL_UNICODE_DATABASE = unicodedata.ucd_3_2_0


class RetrievalWeight(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    lane: RetrievalLane
    value: CanonicalDecimal

    @model_validator(mode="after")
    def validate_positive(self) -> RetrievalWeight:
        if self.value <= Decimal("0"):
            raise ValueError("retrieval weight must be positive")
        return self


class LexicalResolverPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    algorithm_id: Literal["BUILD0_LEXICAL_V1"]
    normalization_id: Literal["NFKC_UCD_3_2_ASCII_CASEFOLD_ALNUM_V1"]
    unicode_data_version: Literal["3.2.0"]
    retrieval_order: tuple[RetrievalLane, ...]
    weights: tuple[RetrievalWeight, ...]
    minimum_score: CanonicalDecimal
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_policy(self) -> LexicalResolverPolicy:
        _validate_unicode_data_version(self.unicode_data_version)
        if self.retrieval_order != RETRIEVAL_LANE_ORDER:
            raise ValueError("retrieval order must match the implemented algorithm")
        lanes = tuple(item.lane for item in self.weights)
        if lanes != RETRIEVAL_LANE_ORDER:
            raise ValueError("retrieval weights must cover each lane in declared order")
        if self.minimum_score <= Decimal("0"):
            raise ValueError("minimum retrieval score must be positive")
        _validate_refs(self.evidence_refs, "lexical policy evidence")
        return self


class MethodAdvisoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    method_ref: GovernedRef
    aliases: tuple[str, ...]
    controlled_term_ids: tuple[TermId, ...]
    observable_ids: tuple[FieldId, ...]
    instrument_type_ids: tuple[TermId, ...]
    failure_class_ids: tuple[TermId, ...]
    lexical_tokens: tuple[str, ...]
    candidate_failure_mode_refs: tuple[GovernedRef, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_record(self) -> MethodAdvisoryRecord:
        for values, label in (
            (self.aliases, "method aliases"),
            (self.controlled_term_ids, "controlled terms"),
            (self.observable_ids, "observable IDs"),
            (self.instrument_type_ids, "instrument types"),
            (self.failure_class_ids, "failure classes"),
            (self.lexical_tokens, "lexical tokens"),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"{label} must be unique and sorted")
        if any(normalize_lexical_text(item) != (item,) for item in self.lexical_tokens):
            raise ValueError("lexical tokens must already be normalized single tokens")
        normalized_aliases = tuple(
            " ".join(normalize_lexical_text(alias)) for alias in self.aliases
        )
        if any(not alias for alias in normalized_aliases):
            raise ValueError("method alias must contain a normalized token")
        if len(normalized_aliases) != len(set(normalized_aliases)):
            raise ValueError("method aliases must be unique after normalization")
        _validate_refs(self.candidate_failure_mode_refs, "advisory candidate refs")
        _validate_refs(self.evidence_refs, "method advisory evidence")
        return self


class AdvisoryCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    catalog_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    methods: tuple[MethodAdvisoryRecord, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_catalog(self) -> AdvisoryCatalog:
        refs = tuple(item.record_ref for item in self.methods)
        if not refs or sorted_unique_refs(refs) != refs:
            raise ValueError("advisory methods must be nonempty, unique, and sorted")
        method_refs = tuple(item.method_ref for item in self.methods)
        if sorted_unique_refs(method_refs) != method_refs:
            raise ValueError("advisory method identities must be unique and sorted")
        _validate_refs(self.evidence_refs, "advisory catalog evidence")
        return self


class AdvisoryRouteRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    trigger: RouteTrigger
    source_route_reason_id: TermId | None
    advisory_route_reason_id: TermId
    eligibility_gap_id: TermId
    proposed_field_ids: tuple[FieldId, ...]
    required_measurement_ids: tuple[TermId, ...]
    required_record_type_ids: tuple[TermId, ...]
    next_step: DisplayDirective
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_rule(self) -> AdvisoryRouteRule:
        if (self.trigger == "TIER1_ROUTE_REASON") != (self.source_route_reason_id is not None):
            raise ValueError("only Tier 1 route rules carry a source route reason")
        for values, label in (
            (self.proposed_field_ids, "proposed fields"),
            (self.required_measurement_ids, "required measurements"),
            (self.required_record_type_ids, "required record types"),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"{label} must be unique and sorted")
        _validate_refs(self.evidence_refs, "advisory route-rule evidence")
        return self


class AdvisoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    query_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    method_text: str
    controlled_term_ids: tuple[TermId, ...]
    observable_ids: tuple[FieldId, ...]
    instrument_type_ids: tuple[TermId, ...]
    failure_class_ids: tuple[TermId, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_query(self) -> AdvisoryQuery:
        for values, label in (
            (self.controlled_term_ids, "controlled terms"),
            (self.observable_ids, "observable IDs"),
            (self.instrument_type_ids, "instrument types"),
            (self.failure_class_ids, "failure classes"),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"query {label} must be unique and sorted")
        if not normalize_lexical_text(self.method_text) and not any(
            (
                self.controlled_term_ids,
                self.observable_ids,
                self.instrument_type_ids,
                self.failure_class_ids,
            )
        ):
            raise ValueError("advisory query must contain a resolvable term")
        _validate_refs(self.evidence_refs, "advisory query evidence")
        return self


class MethodResolutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    resolution: Literal["RESOLVED", "AMBIGUOUS", "UNKNOWN"]
    resolved_by_lane: RetrievalLane | None
    method_ref: GovernedRef | None
    ordered_method_refs: tuple[GovernedRef, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_resolution(self) -> MethodResolutionResult:
        keys = tuple(_ref_key(item) for item in self.ordered_method_refs)
        if len(keys) != len(set(keys)):
            raise ValueError("resolved method candidates must be unique")
        if self.resolution == "UNKNOWN":
            if self.resolved_by_lane is not None or self.method_ref is not None or keys:
                raise ValueError("unknown resolution cannot carry a method match")
        elif self.resolved_by_lane is None or not keys:
            raise ValueError("matched resolution requires a retrieval lane and candidates")
        if self.resolution == "RESOLVED":
            if self.method_ref is None or self.method_ref != self.ordered_method_refs[0]:
                raise ValueError("resolved method must be the first ranked candidate")
        elif self.method_ref is not None:
            raise ValueError("ambiguous resolution cannot select a method")
        _validate_refs(self.evidence_refs, "method resolution evidence")
        return self


def normalize_lexical_text(value: str) -> tuple[str, ...]:
    """Normalize against the resolver's fixed Unicode table and ASCII-only fold contract."""
    _validate_unicode_data_version(LEXICAL_UNICODE_DATA_VERSION)
    normalized = _LEXICAL_UNICODE_DATABASE.normalize("NFKC", value)
    ascii_folded = "".join(
        character.lower()
        if "A" <= character <= "Z"
        else character
        if "a" <= character <= "z" or "0" <= character <= "9"
        else " "
        for character in normalized
    )
    return tuple(ASCII_TOKEN_PATTERN.findall(ascii_folded))


def resolve_advisory_method(
    query: AdvisoryQuery,
    catalog: AdvisoryCatalog,
    policy: LexicalResolverPolicy,
    accelerated_method_refs: tuple[GovernedRef, ...] | None = None,
) -> MethodResolutionResult:
    """Resolve a governed query without allowing an accelerator to alter canonical ranking."""
    _validate_unicode_data_version(policy.unicode_data_version)
    query_tokens = set(normalize_lexical_text(query.method_text))
    normalized_text = " ".join(normalize_lexical_text(query.method_text))
    weights = {item.lane: item.value for item in policy.weights}
    ranked: tuple[tuple[MethodAdvisoryRecord, Decimal], ...] = ()
    selected_lane: RetrievalLane | None = None
    for lane in policy.retrieval_order:
        scored = tuple(
            (record, _lane_score(lane, record, query, query_tokens, normalized_text, weights[lane]))
            for record in catalog.methods
        )
        eligible = tuple(
            (record, score)
            for record, score in scored
            if score is not None and (lane == "EXACT" or score >= policy.minimum_score)
        )
        if eligible:
            ranked = tuple(
                sorted(
                    eligible,
                    key=lambda item: (-item[1], _ref_key(item[0].method_ref)),
                )
            )
            selected_lane = lane
            break
    ordered_refs = tuple(item.method_ref for item, _ in ranked)
    if accelerated_method_refs is not None and accelerated_method_refs != ordered_refs:
        raise ValueError("text-search accelerator changed canonical method membership or order")
    evidence_refs = sorted_unique_refs(
        (
            catalog.catalog_ref,
            policy.policy_ref,
            *catalog.evidence_refs,
            *policy.evidence_refs,
            *(item.record_ref for item, _ in ranked),
            *(ref for item, _ in ranked for ref in item.evidence_refs),
        )
    )
    if not ranked:
        return MethodResolutionResult(
            resolution="UNKNOWN",
            resolved_by_lane=None,
            method_ref=None,
            ordered_method_refs=(),
            evidence_refs=evidence_refs,
        )
    top_score = ranked[0][1]
    top_count = sum(score == top_score for _, score in ranked)
    resolution: Literal["RESOLVED", "AMBIGUOUS"] = "RESOLVED" if top_count == 1 else "AMBIGUOUS"
    return MethodResolutionResult(
        resolution=resolution,
        resolved_by_lane=selected_lane,
        method_ref=ordered_refs[0] if resolution == "RESOLVED" else None,
        ordered_method_refs=ordered_refs,
        evidence_refs=evidence_refs,
    )


def _lane_score(
    lane: RetrievalLane,
    record: MethodAdvisoryRecord,
    query: AdvisoryQuery,
    query_tokens: set[str],
    normalized_text: str,
    weight: Decimal,
) -> Decimal | None:
    if lane == "EXACT":
        names = {
            " ".join(normalize_lexical_text(record.method_ref.logical_id)),
            *(" ".join(normalize_lexical_text(item)) for item in record.aliases),
        }
        return weight if normalized_text and normalized_text in names else None
    if lane == "CONTROLLED_TERM":
        matches = len(set(query.controlled_term_ids) & set(record.controlled_term_ids))
    elif lane == "RELATIONAL":
        matches = sum(
            (
                len(set(query.observable_ids) & set(record.observable_ids)),
                len(set(query.instrument_type_ids) & set(record.instrument_type_ids)),
                len(set(query.failure_class_ids) & set(record.failure_class_ids)),
            )
        )
    else:
        matches = len(query_tokens & set(record.lexical_tokens))
    return Decimal(matches) * weight if matches else None


def _ref_key(ref: GovernedRef) -> tuple[str, int, str, str]:
    return (ref.logical_id, ref.version_number, ref.version_id, ref.content_hash)


def _validate_refs(refs: tuple[GovernedRef, ...], label: str) -> None:
    if not refs or sorted_unique_refs(refs) != refs:
        raise ValueError(f"{label} must be nonempty, unique, and sorted")


def _validate_unicode_data_version(expected: str) -> None:
    if _LEXICAL_UNICODE_DATABASE.unidata_version != expected:
        raise ValueError("lexical Unicode data version does not match governed policy")
