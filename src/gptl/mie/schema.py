"""MIE canonical output schemas implemented through Slice 3."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    UnitId,
)
from gptl.mie.calibration import CalibrationEvaluation
from gptl.mie.predicates import ApplicabilityEvaluation, ApplicabilityTruth


class RefusalType(str, Enum):
    MSA_UNCHARACTERIZED = "MSA_UNCHARACTERIZED"
    UNKNOWN_METHOD_OR_FAILURE_MODE = "UNKNOWN_METHOD_OR_FAILURE_MODE"
    MISSING_REQUIRED_EVIDENCE = "MISSING_REQUIRED_EVIDENCE"
    STALE_OR_INVALID_CALIBRATION = "STALE_OR_INVALID_CALIBRATION"
    PACK_VERSION_UNAVAILABLE = "PACK_VERSION_UNAVAILABLE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    ENGINE_FAILURE = "ENGINE_FAILURE"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_type_id: TermId
    record_ref: GovernedRef
    evidence_location: EvidenceLocator


class CandidateAssessment(BaseModel):
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
    def validate_state(self) -> CandidateAssessment:
        for values, label in (
            (self.evidence_refs, "evidence_refs"),
            (self.rule_refs, "rule_refs"),
        ):
            _validate_ref_order(values, label)
        if self.applicability == ApplicabilityTruth.UNKNOWN:
            if (
                self.evidence_state != "APPLICABILITY_UNRESOLVED"
                or self.status != "APPLICABILITY_UNRESOLVED"
            ):
                raise ValueError("UNKNOWN applicability must remain unresolved")
            if self.signature_match_score is not None or self.candidate_support_score is not None:
                raise ValueError("unresolved applicability cannot carry scores")
        return self


class CandidateConfigurationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    applicability_evaluation: ApplicabilityEvaluation
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_issue(self) -> CandidateConfigurationIssue:
        if self.applicability_evaluation.truth != ApplicabilityTruth.INVALID:
            raise ValueError("candidate configuration issue requires INVALID applicability")
        _validate_ref_order(self.evidence_refs, "evidence_refs")
        if self.applicability_evaluation.predicate_ref not in self.evidence_refs:
            raise ValueError("candidate configuration issue must cite its predicate")
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


class BoundDecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    context_kind: Literal["SNAPSHOT_BOUND"]
    pack_ref: GovernedRef
    engine_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    knowledge_snapshot_hash: Sha256Hex


class PreflightRefusalContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    context_kind: Literal["PREFLIGHT"]
    requested_pack_id: OpaqueId | None
    failure_stage_id: TermId


RefusalContext = Annotated[
    BoundDecisionContext | PreflightRefusalContext,
    Field(discriminator="context_kind"),
]


class RefusalDecision(DecisionHeader):
    verdict: Literal["REFUSED"]
    refusal_type: RefusalType
    context: RefusalContext
    method_ref: GovernedRef | None
    route_reason_id: TermId | None
    calibration_evaluation: CalibrationEvaluation | None
    msa_applicability_evaluations: tuple[ApplicabilityEvaluation, ...] | None
    assessments: tuple[CandidateAssessment, ...]
    configuration_issues: tuple[CandidateConfigurationIssue, ...] | None
    citations: tuple[Citation, ...]
    missing_field_ids: tuple[FieldId, ...]
    required_human_action: DisplayDirective
    audit_event_ids: tuple[OpaqueId, ...]

    @model_validator(mode="after")
    def validate_refusal(self) -> RefusalDecision:
        if self.context.context_kind == "PREFLIGHT":
            if (
                self.method_ref is not None
                or self.assessments
                or self.configuration_issues is not None
                or self.calibration_evaluation is not None
                or self.msa_applicability_evaluations is not None
                or self.citations
            ):
                raise ValueError("preflight refusal cannot contain bound evidence records")
        elif self.method_ref is None:
            raise ValueError("snapshot-bound refusal requires a method ref")
        assessment_keys = tuple(
            (item.candidate_ref.logical_id, item.candidate_ref.version_id)
            for item in self.assessments
        )
        if assessment_keys != tuple(sorted(set(assessment_keys))):
            raise ValueError("candidate assessments must be unique and sorted")
        if self.configuration_issues is not None:
            issue_keys = tuple(
                (item.candidate_ref.logical_id, item.candidate_ref.version_id)
                for item in self.configuration_issues
            )
            if not issue_keys or issue_keys != tuple(sorted(set(issue_keys))):
                raise ValueError("configuration issues must be nonempty, unique, and sorted")
            if self.refusal_type != RefusalType.CONFIGURATION_INVALID:
                raise ValueError("configuration issues require CONFIGURATION_INVALID refusal")
        if self.msa_applicability_evaluations is not None:
            evaluation_keys = tuple(
                (item.predicate_ref.logical_id, item.predicate_ref.version_id)
                for item in self.msa_applicability_evaluations
            )
            if evaluation_keys != tuple(sorted(set(evaluation_keys))):
                raise ValueError("MSA applicability evaluations must be unique and sorted")
        citation_keys = tuple(
            (
                item.record_type_id,
                item.record_ref.logical_id,
                item.record_ref.version_id,
                item.evidence_location,
            )
            for item in self.citations
        )
        if citation_keys != tuple(sorted(set(citation_keys))):
            raise ValueError("citations must be unique and sorted")
        for values, label in (
            (self.missing_field_ids, "missing_field_ids"),
            (self.audit_event_ids, "audit_event_ids"),
        ):
            if len(values) != len(set(values)) or values != tuple(sorted(values)):
                raise ValueError(f"{label} must be unique and sorted")
        if not self.audit_event_ids:
            raise ValueError("refusal decision requires an audit event")
        return self


class InvestigationDecision(DecisionHeader):
    context: BoundDecisionContext
    method_ref: GovernedRef
    route_reason_id: TermId
    calibration_evaluation: CalibrationEvaluation
    msa_applicability_evaluations: tuple[ApplicabilityEvaluation, ...]
    assessments: tuple[CandidateAssessment, ...]
    citations: tuple[Citation, ...]
    missing_field_ids: tuple[FieldId, ...]
    required_human_action: DisplayDirective
    audit_event_ids: tuple[OpaqueId, ...]

    @model_validator(mode="after")
    def validate_investigation(self) -> InvestigationDecision:
        assessment_keys = tuple(
            (item.candidate_ref.logical_id, item.candidate_ref.version_id)
            for item in self.assessments
        )
        if assessment_keys != tuple(sorted(set(assessment_keys))):
            raise ValueError("candidate assessments must be unique and sorted")
        evaluation_keys = tuple(
            (item.predicate_ref.logical_id, item.predicate_ref.version_id)
            for item in self.msa_applicability_evaluations
        )
        if evaluation_keys != tuple(sorted(set(evaluation_keys))):
            raise ValueError("MSA applicability evaluations must be unique and sorted")
        citation_keys = tuple(
            (
                item.record_type_id,
                item.record_ref.logical_id,
                item.record_ref.version_id,
                item.evidence_location,
            )
            for item in self.citations
        )
        if citation_keys != tuple(sorted(set(citation_keys))):
            raise ValueError("citations must be unique and sorted")
        if not self.citations:
            raise ValueError("investigation decision requires authoritative citations")
        for values, label in (
            (self.missing_field_ids, "missing_field_ids"),
            (self.audit_event_ids, "audit_event_ids"),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"{label} must be unique and sorted")
        if not self.audit_event_ids:
            raise ValueError("investigation decision requires an audit event")
        return self


class WithinMeasurementVariationDecision(InvestigationDecision):
    verdict: Literal["WITHIN_MEASUREMENT_VARIATION"]
    msa_study_ref: GovernedRef
    measured_deviation: CanonicalDecimal
    measured_uncertainty: CanonicalDecimal
    uncertainty_unit_id: UnitId

    @model_validator(mode="after")
    def validate_measurement_values(self) -> WithinMeasurementVariationDecision:
        if self.measured_deviation < Decimal("0") or self.measured_uncertainty < Decimal("0"):
            raise ValueError("measurement comparison values cannot be negative")
        return self


class IndeterminateDecision(InvestigationDecision):
    verdict: Literal["INDETERMINATE"]
    msa_study_ref: GovernedRef
    measured_deviation: CanonicalDecimal
    measured_uncertainty: CanonicalDecimal
    uncertainty_unit_id: UnitId
    open_discriminator_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_open_discriminators(self) -> IndeterminateDecision:
        _validate_ref_order(self.open_discriminator_refs, "open_discriminator_refs")
        if not self.open_discriminator_refs:
            raise ValueError("indeterminate decision requires an open discriminator")
        if self.measured_deviation < Decimal("0") or self.measured_uncertainty < Decimal("0"):
            raise ValueError("measurement comparison values cannot be negative")
        return self


Tier1Decision = Annotated[
    RefusalDecision | WithinMeasurementVariationDecision | IndeterminateDecision,
    Field(discriminator="verdict"),
]


class Tier1Output(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_kind: Literal["TIER1_DECISION"]
    decision: Tier1Decision
    decision_hash: Sha256Hex


class AdvisoryDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: OpaqueId
    case_id: OpaqueId
    tier: Literal[2]
    status: Literal["ADVISORY_NO_VERDICT"]
    dispositional: Literal[False]
    non_record_of_record: Literal[True]
    operational_mode: Literal["RESEARCH_ONLY", "QUALIFIED"]
    engine_id: OpaqueId
    engine_version: OpaqueId
    context: BoundDecisionContext
    as_of_time: CanonicalTimestamp
    method_resolution: Literal["RESOLVED", "AMBIGUOUS", "UNKNOWN"]
    method_ref: GovernedRef | None
    route_reason_id: TermId | None
    proposed_field_ids: tuple[FieldId, ...]
    candidate_failure_mode_refs: tuple[GovernedRef, ...]
    applicability_evaluations: tuple[ApplicabilityEvaluation, ...]
    open_discriminator_refs: tuple[GovernedRef, ...]
    required_measurement_ids: tuple[TermId, ...]
    required_record_type_ids: tuple[TermId, ...]
    tier1_eligibility_gap_ids: tuple[TermId, ...]
    next_steps: tuple[DisplayDirective, ...]
    citations: tuple[Citation, ...]
    audit_event_ids: tuple[OpaqueId, ...]

    @model_validator(mode="after")
    def validate_advisory(self) -> AdvisoryDecision:
        if self.method_resolution == "RESOLVED" and self.method_ref is None:
            raise ValueError("resolved advisory requires method ref")
        for values, label in (
            (self.proposed_field_ids, "proposed_field_ids"),
            (self.required_measurement_ids, "required_measurement_ids"),
            (self.required_record_type_ids, "required_record_type_ids"),
            (self.tier1_eligibility_gap_ids, "tier1_eligibility_gap_ids"),
            (self.audit_event_ids, "audit_event_ids"),
        ):
            if len(values) != len(set(values)) or values != tuple(sorted(values)):
                raise ValueError(f"{label} must be unique and sorted")
        _validate_ref_order(self.candidate_failure_mode_refs, "candidate_failure_mode_refs")
        _validate_ref_order(self.open_discriminator_refs, "open_discriminator_refs")
        if not self.audit_event_ids:
            raise ValueError("advisory requires an audit event")
        return self


class Tier2Output(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_kind: Literal["TIER2_ADVISORY"]
    advisory: AdvisoryDecision
    advisory_hash: Sha256Hex


MIEOutput = Annotated[Tier1Output | Tier2Output, Field(discriminator="output_kind")]


def _validate_ref_order(refs: tuple[GovernedRef, ...], label: str) -> None:
    keys = tuple((item.logical_id, item.version_id) for item in refs)
    if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
        raise ValueError(f"{label} must be unique and sorted")
