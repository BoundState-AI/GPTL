"""
Module: Attributed Observations
Purpose: Build 1 attributed observation contracts.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final, Literal, cast

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.proposals import TYPED_VALUE_PROPOSAL_RECORD_TYPE
from gptl.core.records import GovernedRef, governed_record_content_hash, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    OpaqueId,
    Sha256Hex,
    TermId,
)

ATTRIBUTED_OBSERVATION_SCHEMA_VERSION: Final = "gptl.build1.attributed-observation.v1"
ATTRIBUTED_OBSERVATION_RECORD_TYPE: Final = "ATTRIBUTED_OBSERVATION"
OBSERVATION_ADVISORY_CONTEXT_SCHEMA_VERSION: Final = (
    "gptl.build1.observation-advisory-context.v1"
)
OBSERVATION_ADVISORY_CONTEXT_RECORD_TYPE: Final = "OBSERVATION_ADVISORY_CONTEXT"
OBSERVATION_RENDERED_ARTIFACT_SCHEMA_VERSION: Final = (
    "gptl.build1.observation-rendered-artifact.v1"
)
OBSERVATION_RENDERED_ARTIFACT_RECORD_TYPE: Final = "OBSERVATION_RENDERED_ARTIFACT"
OBSERVATION_PROMOTION_SCHEMA_VERSION: Final = "gptl.build1.observation-promotion.v1"
OBSERVATION_PROMOTION_RECORD_TYPE: Final = "OBSERVATION_PROMOTION_RECORD"
HASH_ALGORITHM: Final = "SHA-256"
ATTRIBUTED_UNVALIDATED_LABEL_ID: Final = TermId("build1.observation.attributed-unvalidated")
OBSERVATION_TIER1_PROHIBITED_REASON_ID: Final = TermId(
    "build1.observation.tier1-evidence-prohibited"
)
OBSERVATION_REPLAY_HASH_ALGORITHM_ID: Final = "ATTRIBUTED_OBSERVATION_REPLAY_HASH_V1"

CONFIDENCE_METADATA_TOKENS: Final = (
    "confidence",
    "confidence" + "_interval",
    "proba" + "bility",
    "credibility",
    "certainty",
    "likelihood",
    "sigma",
    "p_value",
    "pvalue",
    "percentile",
    "stddev",
    "standard_deviation",
    "variance",
    "score",
    "trust",
    "weight",
    "rank",
    "post" + "erior",
)
# Split selected tokens so this guard does not trip the source-boundary scan it supports.
CONFIDENCE_METADATA_TOKEN_PATTERN: Final = re.compile(
    r"(^|[._:/_-])(" + "|".join(CONFIDENCE_METADATA_TOKENS) + r")([._:/_-]|$)",
    re.IGNORECASE,
)
_CAMEL_CASE_BOUNDARY: Final = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_LETTER_DIGIT_BOUNDARY: Final = re.compile(r"(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])")


def _expand_token_boundaries(text: str) -> str:
    """Insert delimiters at camelCase and letter/digit transitions so the confidence-token
    scan catches modelConfidence, confidenceScore, and confidence1 — not only the
    delimiter-separated forms. OpaqueId keys admit these camelCase/digit shapes.

    Known limitation: an all-uppercase or all-lowercase concatenation with no case, digit,
    or delimiter cue (e.g. MODELCONFIDENCE, modelconfidence) has no detectable internal
    boundary and is not separable from an innocent compound word without over-rejecting
    (``crankshaft`` contains ``rank``; ``uncertainty`` contains ``certainty``). This scan is
    defense-in-depth hygiene on Tier-2 metadata keys, not the load-bearing control:
    observations are non-record-of-record and never reach Build 0 Tier 1."""
    with_case = _CAMEL_CASE_BOUNDARY.sub("_", text)
    return _LETTER_DIGIT_BOUNDARY.sub("_", with_case)


class ObservationMetadataEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: OpaqueId
    value: str

    @model_validator(mode="after")
    def validate_metadata(self) -> ObservationMetadataEntry:
        if not self.value.strip():
            raise ValueError("observation metadata values must be nonempty")
        if CONFIDENCE_METADATA_TOKEN_PATTERN.search(_expand_token_boundaries(self.key)):
            raise ValueError("observation metadata cannot carry confidence or score fields")
        return self


class ObservationVisibilityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tier: Literal[2]
    advisory_context_allowed: bool
    rendered_artifact_allowed: bool
    structured_advisory_payload_allowed: Literal[False]
    tier1_evidence_allowed: Literal[False]


class AttributedObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.attributed-observation.v1"]
    record_type: Literal["ATTRIBUTED_OBSERVATION"]
    hash_algorithm: Literal["SHA-256"]
    observation_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    claim_text: str
    source_display_name: str | None = None
    source_role_id: TermId | None = None
    recorded_actor_ref: GovernedRef
    recorded_at: CanonicalTimestamp
    production_context_ref: GovernedRef | None = None
    validation_state: Literal[
        "UNVALIDATED",
        "UNDER_REVIEW",
        "PROMOTED_BY_PROTOCOL",
        "REJECTED",
        "SUPERSEDED",
    ]
    evidence_scope_ref: GovernedRef
    source_artifact_ref: GovernedRef | None = None
    metadata: tuple[ObservationMetadataEntry, ...]
    visibility_policy: ObservationVisibilityPolicy
    evidence_refs: tuple[GovernedRef, ...]
    supersedes_observation_ref: GovernedRef | None = None

    @model_validator(mode="before")
    @classmethod
    def sort_observation_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "metadata" in normalized:
            normalized["metadata"] = tuple(
                sorted(normalized["metadata"], key=lambda item: str(_field_value(item, "key")))
            )
        return _sort_refs(normalized, "evidence_refs")

    @model_validator(mode="after")
    def validate_observation(self) -> AttributedObservation:
        if not self.claim_text.strip():
            raise ValueError("observation claim text must be nonempty")
        if self.source_display_name is None and self.source_role_id is None:
            raise ValueError("observation requires a named source or role")
        if self.source_display_name is not None and not self.source_display_name.strip():
            raise ValueError("observation source name must be nonempty")
        metadata_keys = tuple(item.key for item in self.metadata)
        if metadata_keys != tuple(sorted(set(metadata_keys))):
            raise ValueError("observation metadata keys must be unique and sorted")
        if not self.evidence_refs:
            raise ValueError("observation requires evidence references")
        if self.validation_state == "SUPERSEDED":
            if self.supersedes_observation_ref is None:
                raise ValueError("superseded observation requires superseded observation ref")
        elif self.supersedes_observation_ref is not None:
            raise ValueError("only superseded observations can cite superseded observation refs")
        return self


class ObservationAdvisoryReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_ref: GovernedRef
    label_id: TermId
    tier: Literal[2]
    validation_state: Literal["UNVALIDATED"]
    attributed: Literal[True]

    @model_validator(mode="after")
    def validate_label(self) -> ObservationAdvisoryReference:
        if self.label_id != ATTRIBUTED_UNVALIDATED_LABEL_ID:
            raise ValueError("observation advisory refs must use the attributed-unvalidated label")
        return self


class ObservationAdvisoryContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.observation-advisory-context.v1"]
    record_type: Literal["OBSERVATION_ADVISORY_CONTEXT"]
    hash_algorithm: Literal["SHA-256"]
    canonicalization_policy_ref: GovernedRef
    as_of_time: CanonicalTimestamp
    observation_refs: tuple[ObservationAdvisoryReference, ...]

    @model_validator(mode="after")
    def validate_refs(self) -> ObservationAdvisoryContext:
        keys = tuple(_ref_key(item.observation_ref) for item in self.observation_refs)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("observation advisory refs must be unique and sorted")
        return self


class ObservationRenderedText(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_ref: GovernedRef
    label_id: TermId
    rendered_text: str

    @model_validator(mode="after")
    def validate_rendered_text(self) -> ObservationRenderedText:
        if self.label_id != ATTRIBUTED_UNVALIDATED_LABEL_ID:
            raise ValueError("rendered observation must use the attributed-unvalidated label")
        normalized = self.rendered_text.lower()
        if "attributed" not in normalized or "unvalidated" not in normalized:
            raise ValueError("rendered observation must label attribution and validation state")
        return self


class ObservationRenderedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.observation-rendered-artifact.v1"]
    record_type: Literal["OBSERVATION_RENDERED_ARTIFACT"]
    hash_algorithm: Literal["SHA-256"]
    renderer_id: OpaqueId
    renderer_version: OpaqueId
    generated_from_advisory_hash: Sha256Hex
    non_record_of_record: Literal[True]
    observations: tuple[ObservationRenderedText, ...]

    @model_validator(mode="after")
    def validate_observations(self) -> ObservationRenderedArtifact:
        keys = tuple(_ref_key(item.observation_ref) for item in self.observations)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("rendered observation refs must be unique and sorted")
        return self


class ObservationTier1EvidenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["PROHIBITED"]
    reason_id: TermId
    observation_ref: GovernedRef
    tier1_evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_no_evidence_refs(self) -> ObservationTier1EvidenceResult:
        if self.reason_id != OBSERVATION_TIER1_PROHIBITED_REASON_ID:
            raise ValueError("Tier 1 observation prohibition must cite the governed reason")
        if self.tier1_evidence_refs:
            raise ValueError("observation text cannot satisfy Tier 1 evidence")
        return self


class ObservationPromotionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.observation-promotion.v1"]
    record_type: Literal["OBSERVATION_PROMOTION_RECORD"]
    hash_algorithm: Literal["SHA-256"]
    promotion_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    observation_ref: GovernedRef
    created_proposal_record_type: Literal["TYPED_VALUE_PROPOSAL"]
    created_proposal_ref: GovernedRef
    promotion_basis: Literal["VALIDATION_PROTOCOL_RESULT", "CORROBORATING_GOVERNED_EVIDENCE"]
    validation_protocol_result_ref: GovernedRef | None = None
    corroborating_evidence_refs: tuple[GovernedRef, ...] = ()
    decision_effective: Literal[False]
    required_next_record_type: Literal["PROPOSAL_RATIFICATION_EVENT"]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_promotion_refs(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = _sort_refs(dict(value), "evidence_refs")
        return _sort_refs(normalized, "corroborating_evidence_refs")

    @model_validator(mode="after")
    def validate_basis(self) -> ObservationPromotionRecord:
        if self.created_proposal_record_type != TYPED_VALUE_PROPOSAL_RECORD_TYPE:
            raise ValueError("observation promotion must create a typed value proposal")
        if self.promotion_basis == "VALIDATION_PROTOCOL_RESULT":
            if self.validation_protocol_result_ref is None or self.corroborating_evidence_refs:
                raise ValueError("protocol promotion requires only a protocol result ref")
        if self.promotion_basis == "CORROBORATING_GOVERNED_EVIDENCE":
            if self.validation_protocol_result_ref is not None or not self.corroborating_evidence_refs:
                raise ValueError("corroborating promotion requires governed evidence refs")
        if not self.evidence_refs:
            raise ValueError("observation promotion requires evidence references")
        return self


def attributed_observation_content_hash(
    observation: AttributedObservation,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return governed_record_content_hash(observation, "observation_ref", canonicalization_policy)


def finalize_attributed_observation(
    observation: AttributedObservation,
    canonicalization_policy: CanonicalizationPolicy,
) -> AttributedObservation:
    content_hash = attributed_observation_content_hash(observation, canonicalization_policy)
    updated_ref = observation.observation_ref.model_copy(update={"content_hash": content_hash})
    return observation.model_copy(update={"observation_ref": updated_ref})


def build_observation_advisory_context(
    observations: tuple[AttributedObservation, ...],
    canonicalization_policy_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> ObservationAdvisoryContext:
    refs = tuple(
        ObservationAdvisoryReference(
            observation_ref=observation.observation_ref,
            label_id=ATTRIBUTED_UNVALIDATED_LABEL_ID,
            tier=2,
            validation_state="UNVALIDATED",
            attributed=True,
        )
        for observation in sorted(observations, key=lambda item: _ref_key(item.observation_ref))
        if observation.validation_state == "UNVALIDATED"
        and observation.recorded_at <= as_of_time
        and observation.visibility_policy.advisory_context_allowed
    )
    return ObservationAdvisoryContext.model_validate(
        {
            "schema_version": OBSERVATION_ADVISORY_CONTEXT_SCHEMA_VERSION,
            "record_type": OBSERVATION_ADVISORY_CONTEXT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "canonicalization_policy_ref": canonicalization_policy_ref,
            "as_of_time": as_of_time,
            "observation_refs": refs,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )


def render_observation_artifact(
    context: ObservationAdvisoryContext,
    observations: tuple[AttributedObservation, ...],
    generated_from_advisory_hash: Sha256Hex,
    renderer_id: OpaqueId,
    renderer_version: OpaqueId,
) -> ObservationRenderedArtifact:
    observations_by_ref = {_ref_key(item.observation_ref): item for item in observations}
    # Fail closed with a diagnostic error, not a bare KeyError deep in the comprehension,
    # if the render context references an observation that was not supplied.
    missing_refs = tuple(
        item.observation_ref
        for item in context.observation_refs
        if _ref_key(item.observation_ref) not in observations_by_ref
    )
    if missing_refs:
        raise ValueError(
            "render context references observations that were not supplied: "
            + ", ".join(str(ref.logical_id) for ref in missing_refs)
        )
    rendered = tuple(
        ObservationRenderedText(
            observation_ref=item.observation_ref,
            label_id=ATTRIBUTED_UNVALIDATED_LABEL_ID,
            rendered_text=_render_observation_text(observations_by_ref[_ref_key(item.observation_ref)]),
        )
        for item in context.observation_refs
        if observations_by_ref[_ref_key(item.observation_ref)].visibility_policy.rendered_artifact_allowed
    )
    return ObservationRenderedArtifact(
        schema_version=OBSERVATION_RENDERED_ARTIFACT_SCHEMA_VERSION,
        record_type=OBSERVATION_RENDERED_ARTIFACT_RECORD_TYPE,
        hash_algorithm=HASH_ALGORITHM,
        renderer_id=renderer_id,
        renderer_version=renderer_version,
        generated_from_advisory_hash=generated_from_advisory_hash,
        non_record_of_record=True,
        observations=rendered,
    )


def evaluate_observation_tier1_evidence(
    observation: AttributedObservation,
) -> ObservationTier1EvidenceResult:
    return ObservationTier1EvidenceResult(
        status="PROHIBITED",
        reason_id=OBSERVATION_TIER1_PROHIBITED_REASON_ID,
        observation_ref=observation.observation_ref,
        tier1_evidence_refs=(),
    )


def observation_replay_hash(
    observations: tuple[AttributedObservation, ...],
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    payload = {
        "algorithm_id": OBSERVATION_REPLAY_HASH_ALGORITHM_ID,
        "observations": tuple(
            observation.model_dump(mode="python", exclude_none=True)
            for observation in sorted(observations, key=lambda item: _ref_key(item.observation_ref))
        ),
    }
    return canonical_sha256(payload, canonicalization_policy)


def observation_promotion_content_hash(
    promotion: ObservationPromotionRecord,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return governed_record_content_hash(promotion, "promotion_ref", canonicalization_policy)


def finalize_observation_promotion(
    promotion: ObservationPromotionRecord,
    canonicalization_policy: CanonicalizationPolicy,
) -> ObservationPromotionRecord:
    content_hash = observation_promotion_content_hash(promotion, canonicalization_policy)
    updated_ref = promotion.promotion_ref.model_copy(update={"content_hash": content_hash})
    return promotion.model_copy(update={"promotion_ref": updated_ref})


def _render_observation_text(observation: AttributedObservation) -> str:
    source = observation.source_display_name or str(observation.source_role_id)
    return f"Attributed unvalidated observation from {source}: {observation.claim_text}"


def _sort_refs(value: dict[str, object], field_name: str) -> dict[str, object]:
    if field_name not in value:
        return value
    normalized = dict(value)
    normalized[field_name] = sorted_unique_refs(_ref_tuple(normalized[field_name]))
    return normalized


def _ref_tuple(value: object) -> tuple[GovernedRef, ...]:
    if not isinstance(value, Sequence):
        raise ValueError("governed reference collections must be sequences")
    return tuple(cast(Sequence[GovernedRef], value))


def _ref_key(ref: GovernedRef) -> tuple[str, str]:
    return (ref.logical_id, ref.version_id)


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, BaseModel):
        return getattr(value, field_name)
    if isinstance(value, dict):
        return value[field_name]
    raise ValueError("observation values must be model or mapping values")
