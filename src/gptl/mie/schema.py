"""Slice 1 MIE canonical output schema."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.directives import DisplayDirective
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalDecimal,
    CanonicalTimestamp,
    EvidenceLocator,
    FieldId,
    OpaqueId,
    Sha256Hex,
    TermId,
)


class RefusalType(str, Enum):
    MSA_UNCHARACTERIZED = "MSA_UNCHARACTERIZED"
    UNKNOWN_METHOD_OR_FAILURE_MODE = "UNKNOWN_METHOD_OR_FAILURE_MODE"
    MISSING_REQUIRED_EVIDENCE = "MISSING_REQUIRED_EVIDENCE"
    STALE_OR_INVALID_CALIBRATION = "STALE_OR_INVALID_CALIBRATION"
    PACK_VERSION_UNAVAILABLE = "PACK_VERSION_UNAVAILABLE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    ENGINE_FAILURE = "ENGINE_FAILURE"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"


class ApplicabilityTruth(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_type_id: TermId
    record_ref: GovernedRef
    evidence_location: EvidenceLocator


class CandidateAssessment(BaseModel):
    """Complete shape reserved now so refusals cannot hide untyped content."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    applicability: ApplicabilityTruth
    evidence_state: Literal[
        "ELIMINATED", "OPEN_UNASSESSED", "EVALUABLE", "APPLICABILITY_UNRESOLVED"
    ]
    status: Literal[
        "ELIMINATED",
        "OPEN_UNASSESSED",
        "CANDIDATE",
        "CONFIRMED",
        "RULED_OUT",
        "APPLICABILITY_UNRESOLVED",
    ]
    signature_match_score: CanonicalDecimal | None
    signature_coverage: CanonicalDecimal
    candidate_support_score: CanonicalDecimal | None
    evidence_refs: tuple[GovernedRef, ...]
    rule_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_reference_order(self) -> "CandidateAssessment":
        for values, label in (
            (self.evidence_refs, "evidence_refs"),
            (self.rule_refs, "rule_refs"),
        ):
            keys = tuple((item.logical_id, item.version_id) for item in values)
            if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
                raise ValueError(f"{label} must be unique and canonically sorted")
        return self


class DecisionHeader(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: OpaqueId
    case_id: OpaqueId
    tier: Literal[1]
    dispositional: Literal[False]
    non_record_of_record: Literal[True]
    operational_mode: Literal["RESEARCH_ONLY", "QUALIFIED"]
    engine_id: OpaqueId
    engine_version: OpaqueId
    as_of_time: CanonicalTimestamp


class PreflightRefusalContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    context_kind: Literal["PREFLIGHT"]
    requested_pack_id: OpaqueId | None
    failure_stage_id: TermId


class RefusalDecision(DecisionHeader):
    verdict: Literal["REFUSED"]
    refusal_type: RefusalType
    context: PreflightRefusalContext
    method_ref: GovernedRef | None
    assessments: tuple[CandidateAssessment, ...]
    citations: tuple[Citation, ...]
    missing_field_ids: tuple[FieldId, ...]
    required_human_action: DisplayDirective
    audit_event_ids: tuple[OpaqueId, ...]

    @model_validator(mode="after")
    def validate_preflight_boundary(self) -> "RefusalDecision":
        if self.method_ref is not None or self.assessments or self.citations:
            raise ValueError("preflight refusal cannot contain bound evidence records")
        for values, label in (
            (self.missing_field_ids, "missing_field_ids"),
            (self.audit_event_ids, "audit_event_ids"),
        ):
            if len(values) != len(set(values)) or values != tuple(sorted(values)):
                raise ValueError(f"{label} must be unique and lexicographically sorted")
        if not self.audit_event_ids:
            raise ValueError("refusal decision requires an audit event")
        return self


class Tier1Output(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_kind: Literal["TIER1_DECISION"]
    decision: RefusalDecision
    decision_hash: Sha256Hex
