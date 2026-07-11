"""
Module: Slice 3 Calibration and MSA Service
Purpose: Deterministic Slice 3 calibration and MSA routing.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.directives import DisplayDirective
from gptl.core.persistence import SLICE3_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import TermId
from gptl.mie.calibration import (
    CalibrationEvaluation,
    CalibrationRecord,
    CalibrationTruth,
    CalibrationValidityPolicy,
    MeasurementRunContext,
    evaluate_calibration,
)
from gptl.mie.candidates import CandidatePackConfigurationError, load_candidate_set
from gptl.mie.msa import (
    EvidenceScopeRecord,
    ImplementedMSAClassRegistry,
    MethodMeasurementContract,
    MSAGateOutcome,
    MSAGateReason,
    MSAGateResult,
    MSAStudy,
    evaluate_msa_gate,
)
from gptl.mie.predicates import ContextValue, NumericValue
from gptl.mie.schema import (
    Citation,
    IndeterminateDecision,
    KnownArtifactsExcludedDecision,
    MethodArtifactDecision,
    RefusalType,
    Tier1Output,
    WithinMeasurementVariationDecision,
)
from gptl.mie.selection import SelectionGroupRecord
from gptl.mie.slice2_service import (
    Slice2ExecutionResult,
    Slice2IntakeReady,
    Slice2Policy,
    Slice2Request,
    Slice2Runtime,
    build_snapshot_refusal,
    context_values_from_intake,
    finalize_snapshot_output,
    prepare_snapshot_bound_intake,
)


class Slice3RouteReasons(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    calibration_stale: TermId
    calibration_invalid: TermId
    calibration_unavailable: TermId
    msa_missing: TermId
    msa_unqualified: TermId
    msa_unknown_applicability: TermId
    msa_not_applicable: TermId
    msa_scope_mismatch: TermId
    msa_unimplemented_class: TermId
    msa_configuration_invalid: TermId
    within_variation: TermId
    outside_variation: TermId
    candidate_configuration_invalid: TermId
    candidate_missing_context: TermId

    @model_validator(mode="after")
    def validate_unique(self) -> Slice3RouteReasons:
        values = tuple(self.model_dump(mode="python").values())
        if len(values) != len(set(values)):
            raise ValueError("Slice 3 route reasons must be distinct")
        return self


class Slice3Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice2_policy: Slice2Policy
    route_policy_ref: GovernedRef
    route_reasons: Slice3RouteReasons
    msa_uncharacterized_precedence: tuple[MSAGateReason, ...]
    calibration_invalid_action: DisplayDirective
    calibration_unavailable_action: DisplayDirective
    msa_uncharacterized_action: DisplayDirective
    within_variation_action: DisplayDirective
    indeterminate_action: DisplayDirective
    within_variation_event_type_id: TermId
    indeterminate_event_type_id: TermId

    def model_post_init(self, context: object) -> None:
        required_reasons = {
            MSAGateReason.UNKNOWN_APPLICABILITY,
            MSAGateReason.SCOPE_MISMATCH,
            MSAGateReason.UNQUALIFIED_STUDY,
            MSAGateReason.NOT_APPLICABLE,
        }
        if (
            len(self.msa_uncharacterized_precedence)
            != len(set(self.msa_uncharacterized_precedence))
            or set(self.msa_uncharacterized_precedence) != required_reasons
        ):
            raise ValueError("MSA uncharacterized precedence must contain every governed reason")
        for directive in (
            self.calibration_invalid_action,
            self.calibration_unavailable_action,
            self.msa_uncharacterized_action,
            self.within_variation_action,
            self.indeterminate_action,
        ):
            self.slice2_policy.display_registry.validate_directive(directive)


class Slice3Runtime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice2_runtime: Slice2Runtime
    run_context: MeasurementRunContext
    calibration: CalibrationRecord
    calibration_policy: CalibrationValidityPolicy
    implemented_msa_classes: ImplementedMSAClassRegistry
    evidence_scopes: tuple[EvidenceScopeRecord, ...]
    msa_studies: tuple[MSAStudy, ...]
    msa_selection_groups: tuple[SelectionGroupRecord, ...]
    measurement_contract: MethodMeasurementContract
    open_discriminator_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_bindings(self) -> Slice3Runtime:
        pack = self.slice2_runtime.pack
        if self.run_context.calibration_ref != self.calibration.calibration_ref:
            raise ValueError("run context calibration ref mismatch")
        if self.run_context.instrument_ref != self.calibration.instrument_ref:
            raise ValueError("run context instrument ref mismatch")
        if self.run_context.evidence_scope_ref != pack.manifest.evidence_scope_ref:
            raise ValueError("run context evidence scope mismatch")
        if self.measurement_contract.method_ref != pack.manifest.method_ref:
            raise ValueError("measurement contract method ref mismatch")
        scope_keys = tuple(
            (item.scope_ref.logical_id, item.scope_ref.version_id) for item in self.evidence_scopes
        )
        if scope_keys != tuple(sorted(set(scope_keys))):
            raise ValueError("evidence scopes must be unique and sorted")
        if self.run_context.evidence_scope_ref not in tuple(
            item.scope_ref for item in self.evidence_scopes
        ):
            raise ValueError("run evidence scope record is missing")
        study_keys = tuple(
            (item.study_ref.logical_id, item.study_ref.version_id) for item in self.msa_studies
        )
        if study_keys != tuple(sorted(set(study_keys))):
            raise ValueError("MSA studies must be unique and sorted")
        group_refs = tuple(item.group_ref for item in self.msa_selection_groups)
        if sorted_unique_refs(group_refs) != group_refs:
            raise ValueError("MSA selection groups must be unique and sorted")
        if sorted_unique_refs(self.open_discriminator_refs) != self.open_discriminator_refs:
            raise ValueError("open discriminator refs must be unique and sorted")
        return self


@dataclass(frozen=True)
class Slice3OutsideVariationReady:
    intake: Slice2IntakeReady
    calibration: CalibrationEvaluation
    msa: MSAGateResult
    citations: tuple[Citation, ...]
    context_values: tuple[ContextValue, ...]


def build_msa_calibration_gate(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
) -> Slice2ExecutionResult:
    prepared = prepare_msa_calibration_gate(request, runtime, policy)
    if isinstance(prepared, Slice2ExecutionResult):
        return prepared
    return _outside_variation_result(
        request,
        runtime,
        policy,
        prepared.intake,
        prepared.calibration,
        prepared.msa,
        prepared.citations,
        prepared.context_values,
    )


def prepare_msa_calibration_gate(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
) -> Slice3OutsideVariationReady | Slice2ExecutionResult:
    _validate_snapshot_bindings(runtime, policy)
    intake_result = prepare_snapshot_bound_intake(
        request,
        runtime.slice2_runtime,
        policy.slice2_policy,
    )
    if isinstance(intake_result, Slice2ExecutionResult):
        return intake_result
    calibration = evaluate_calibration(
        runtime.calibration,
        runtime.calibration_policy,
        request.as_of_time,
    )
    calibration_citations = (_calibration_citation(runtime.calibration),)
    if calibration.state in {CalibrationTruth.STALE, CalibrationTruth.INVALID}:
        reason = (
            policy.route_reasons.calibration_stale
            if calibration.state == CalibrationTruth.STALE
            else policy.route_reasons.calibration_invalid
        )
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.STALE_OR_INVALID_CALIBRATION,
            policy.calibration_invalid_action,
            reason,
            calibration,
            None,
            (),
            None,
            calibration_citations,
            (),
        )
    if calibration.state == CalibrationTruth.UNAVAILABLE:
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.MISSING_REQUIRED_EVIDENCE,
            policy.calibration_unavailable_action,
            policy.route_reasons.calibration_unavailable,
            calibration,
            None,
            (),
            None,
            calibration_citations,
            (),
        )
    if (
        runtime.implemented_msa_classes.engine_id != policy.slice2_policy.engine_id
        or runtime.implemented_msa_classes.engine_version != policy.slice2_policy.engine_version
    ):
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.CONFIGURATION_INVALID,
            policy.slice2_policy.configuration_action,
            policy.route_reasons.msa_configuration_invalid,
            calibration,
            (),
            (),
            None,
            calibration_citations,
            (),
        )
    context_values = context_values_from_intake(intake_result.gate.admitted_values)
    deviation = next(
        (
            item.value
            for item in context_values
            if item.field_id == runtime.measurement_contract.deviation_field_id
            and isinstance(item.value, NumericValue)
        ),
        None,
    )
    if deviation is None or deviation.value < 0:
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.CONFIGURATION_INVALID,
            policy.slice2_policy.configuration_action,
            policy.route_reasons.msa_configuration_invalid,
            calibration,
            (),
            (),
            None,
            calibration_citations,
            (),
        )
    msa = evaluate_msa_gate(
        runtime.msa_studies,
        runtime.implemented_msa_classes,
        runtime.evidence_scopes,
        runtime.msa_selection_groups,
        runtime.run_context.evidence_scope_ref,
        runtime.measurement_contract,
        deviation,
        context_values,
        runtime.slice2_runtime.pack.field_registry,
        runtime.slice2_runtime.pack.unit_registry,
        request.as_of_time,
        policy.slice2_policy.canonicalization_policy,
        policy.msa_uncharacterized_precedence,
    )
    msa_citations = _msa_citations(runtime.msa_studies, msa)
    citations = sorted_citations((*calibration_citations, *msa_citations))
    if msa.outcome == MSAGateOutcome.CONFIGURATION_INVALID:
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.CONFIGURATION_INVALID,
            policy.slice2_policy.configuration_action,
            _msa_reason_id(msa.reason, policy.route_reasons),
            calibration,
            msa.applicability_evaluations,
            (),
            None,
            citations,
            (),
        )
    if msa.outcome == MSAGateOutcome.UNCHARACTERIZED:
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.MSA_UNCHARACTERIZED,
            policy.msa_uncharacterized_action,
            _msa_reason_id(msa.reason, policy.route_reasons),
            calibration,
            msa.applicability_evaluations,
            (),
            None,
            citations,
            (),
        )
    if msa.outcome == MSAGateOutcome.WITHIN_VARIATION:
        return _within_variation_result(
            request,
            runtime,
            policy,
            intake_result,
            calibration,
            msa,
            citations,
        )
    return Slice3OutsideVariationReady(
        intake=intake_result,
        calibration=calibration,
        msa=msa,
        citations=citations,
        context_values=context_values,
    )


def execute_msa_calibration_gate(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
    store: PostgresRunStore,
) -> Slice2ExecutionResult:
    result = build_msa_calibration_gate(request, runtime, policy)
    store.persist_snapshot_run(
        request.run_id,
        result.output,
        result.snapshot,
        result.audit_events,
        result.bound_versions,
        SLICE3_RUN_SCHEMA_VERSION,
    )
    return result


def _within_variation_result(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
    intake_result: Slice2IntakeReady,
    calibration: CalibrationEvaluation,
    msa: MSAGateResult,
    citations: tuple[Citation, ...],
) -> Slice2ExecutionResult:
    if msa.selected_study_ref is None or msa.measured_uncertainty is None:
        raise ValueError("within-variation result requires one selected MSA study")
    decision = WithinMeasurementVariationDecision.model_validate(
        {
            **investigation_header(request, runtime, policy, intake_result, calibration, msa),
            "verdict": "WITHIN_MEASUREMENT_VARIATION",
            "assessments": (),
            "citations": citations,
            "required_human_action": policy.within_variation_action,
            "msa_study_ref": msa.selected_study_ref,
            "measured_deviation": msa.measured_deviation.value,
            "measured_uncertainty": msa.measured_uncertainty.value,
            "uncertainty_unit_id": msa.measured_uncertainty.unit_id,
        },
        context={"canonicalization_policy": policy.slice2_policy.canonicalization_policy},
    )
    return build_investigation_result(
        request,
        runtime,
        policy,
        intake_result,
        decision,
        policy.within_variation_event_type_id,
    )


def _outside_variation_result(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
    intake_result: Slice2IntakeReady,
    calibration: CalibrationEvaluation,
    msa: MSAGateResult,
    citations: tuple[Citation, ...],
    context_values: tuple[ContextValue, ...],
) -> Slice2ExecutionResult:
    try:
        candidates = load_candidate_set(
            runtime.slice2_runtime.pack,
            context_values,
            policy.slice2_policy.canonicalization_policy,
        )
    except CandidatePackConfigurationError:
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.CONFIGURATION_INVALID,
            policy.slice2_policy.configuration_action,
            policy.route_reasons.candidate_configuration_invalid,
            calibration,
            msa.applicability_evaluations,
            (),
            None,
            citations,
            (),
        )
    combined_citations = sorted_citations((*citations, *candidates.citations))
    if candidates.has_invalid:
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.CONFIGURATION_INVALID,
            policy.slice2_policy.configuration_action,
            policy.route_reasons.candidate_configuration_invalid,
            calibration,
            msa.applicability_evaluations,
            candidates.assessments,
            candidates.configuration_issues,
            combined_citations,
            (),
        )
    if candidates.has_unknown:
        missing_fields = tuple(
            sorted(
                {
                    field
                    for evaluation in candidates.applicability_evaluations
                    for field in evaluation.missing_field_ids
                }
            )
        )
        return build_snapshot_refusal(
            request,
            runtime.slice2_runtime,
            policy.slice2_policy,
            intake_result.snapshot,
            intake_result.context,
            RefusalType.MISSING_REQUIRED_EVIDENCE,
            policy.slice2_policy.missing_evidence_action,
            policy.route_reasons.candidate_missing_context,
            calibration,
            msa.applicability_evaluations,
            candidates.assessments,
            None,
            combined_citations,
            missing_fields,
        )
    if msa.selected_study_ref is None:
        raise ValueError("outside-variation result requires one selected MSA study")
    if msa.measured_uncertainty is None:
        raise ValueError("outside-variation result requires compared uncertainty")
    decision = IndeterminateDecision.model_validate(
        {
            **investigation_header(request, runtime, policy, intake_result, calibration, msa),
            "verdict": "INDETERMINATE",
            "assessments": candidates.assessments,
            "citations": combined_citations,
            "required_human_action": policy.indeterminate_action,
            "msa_study_ref": msa.selected_study_ref,
            "measured_deviation": msa.measured_deviation.value,
            "measured_uncertainty": msa.measured_uncertainty.value,
            "uncertainty_unit_id": msa.measured_uncertainty.unit_id,
            "diagnostic_state_hash": None,
            "open_discriminator_refs": runtime.open_discriminator_refs,
        },
        context={"canonicalization_policy": policy.slice2_policy.canonicalization_policy},
    )
    return build_investigation_result(
        request,
        runtime,
        policy,
        intake_result,
        decision,
        policy.indeterminate_event_type_id,
    )


def investigation_header(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
    intake_result: Slice2IntakeReady,
    calibration: CalibrationEvaluation,
    msa: MSAGateResult,
) -> dict[str, object]:
    return {
        "decision_id": request.decision_id,
        "case_id": request.case_id,
        "tier": 1,
        "dispositional": False,
        "non_record_of_record": True,
        "operational_mode": policy.slice2_policy.operational_mode,
        "engine_id": policy.slice2_policy.engine_id,
        "engine_version": policy.slice2_policy.engine_version,
        "as_of_time": request.as_of_time,
        "context": intake_result.context,
        "method_ref": runtime.slice2_runtime.pack.manifest.method_ref,
        "route_reason_id": _msa_reason_id(msa.reason, policy.route_reasons),
        "calibration_evaluation": calibration,
        "msa_applicability_evaluations": msa.applicability_evaluations,
        "missing_field_ids": (),
        "audit_event_ids": (request.audit_event_id,),
    }


def build_investigation_result(
    request: Slice2Request,
    runtime: Slice3Runtime,
    policy: Slice3Policy,
    intake_result: Slice2IntakeReady,
    decision: (
        WithinMeasurementVariationDecision
        | IndeterminateDecision
        | MethodArtifactDecision
        | KnownArtifactsExcludedDecision
    ),
    event_type_id: TermId,
) -> Slice2ExecutionResult:
    decision_hash = canonical_sha256(
        decision,
        policy.slice2_policy.canonicalization_policy,
    )
    output = Tier1Output(
        output_kind="TIER1_DECISION",
        decision=decision,
        decision_hash=decision_hash,
    )
    return finalize_snapshot_output(
        request,
        runtime.slice2_runtime,
        policy.slice2_policy,
        intake_result.snapshot,
        output,
        decision_hash,
        event_type_id,
    )


def _validate_snapshot_bindings(runtime: Slice3Runtime, policy: Slice3Policy) -> None:
    expected = (
        runtime.run_context.run_context_ref,
        runtime.run_context.instrument_ref,
        *runtime.run_context.evidence_refs,
        runtime.calibration.calibration_ref,
        runtime.calibration.instrument_ref,
        *runtime.calibration.evidence_refs,
        runtime.calibration_policy.policy_ref,
        runtime.implemented_msa_classes.registry_ref,
        runtime.measurement_contract.contract_ref,
        *runtime.measurement_contract.evidence_refs,
        *(item.scope_ref for item in runtime.evidence_scopes),
        *(
            ref
            for group in runtime.msa_selection_groups
            for ref in (group.group_ref, *group.evidence_refs)
        ),
        *(
            ref
            for study in runtime.msa_studies
            for ref in (
                study.study_ref,
                study.predicate_ref,
                study.qualification_scope_ref,
                *study.capability_evidence_refs,
            )
        ),
        *runtime.open_discriminator_refs,
        policy.route_policy_ref,
    )
    actual = {
        (item.logical_id, item.version_id): item
        for item in runtime.slice2_runtime.additional_bound_refs
    }
    mismatched = [
        item
        for item in sorted_unique_refs(expected)
        if actual.get((item.logical_id, item.version_id)) != item
    ]
    if mismatched:
        raise ValueError("Slice 3 snapshot bindings omit or conflict with runtime records")


def _calibration_citation(record: CalibrationRecord) -> Citation:
    return Citation(
        record_type_id=record.record_type_id,
        record_ref=record.calibration_ref,
        evidence_location=record.evidence_location,
    )


def _msa_citations(
    studies: tuple[MSAStudy, ...],
    result: MSAGateResult,
) -> tuple[Citation, ...]:
    evaluated_predicates = {item.predicate_ref for item in result.applicability_evaluations}
    selected = result.selected_study_ref
    evidence_refs = set(result.evidence_refs)
    return sorted_citations(
        tuple(
            Citation(
                record_type_id=study.study_record_type_id,
                record_ref=study.study_ref,
                evidence_location=study.study_evidence_location,
            )
            for study in studies
            if study.predicate_ref in evaluated_predicates
            or study.study_ref == selected
            or study.study_ref in evidence_refs
        )
    )


def sorted_citations(citations: tuple[Citation, ...]) -> tuple[Citation, ...]:
    unique: dict[tuple[str, str], Citation] = {}
    for item in citations:
        key = (item.record_ref.logical_id, item.record_ref.version_id)
        existing = unique.get(key)
        if existing is not None and existing != item:
            raise ValueError("citation identity resolved to conflicting governed metadata")
        unique[key] = item
    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                item.record_type_id,
                item.record_ref.logical_id,
                item.record_ref.version_id,
                item.evidence_location,
            ),
        )
    )


def _msa_reason_id(reason: MSAGateReason, routes: Slice3RouteReasons) -> TermId:
    return {
        MSAGateReason.MISSING_STUDY: routes.msa_missing,
        MSAGateReason.UNQUALIFIED_STUDY: routes.msa_unqualified,
        MSAGateReason.UNKNOWN_APPLICABILITY: routes.msa_unknown_applicability,
        MSAGateReason.NOT_APPLICABLE: routes.msa_not_applicable,
        MSAGateReason.SCOPE_MISMATCH: routes.msa_scope_mismatch,
        MSAGateReason.UNIMPLEMENTED_CLASS: routes.msa_unimplemented_class,
        MSAGateReason.INVALID_CONFIGURATION: routes.msa_configuration_invalid,
        MSAGateReason.WITHIN_VARIATION: routes.within_variation,
        MSAGateReason.OUTSIDE_VARIATION: routes.outside_variation,
    }[reason]
