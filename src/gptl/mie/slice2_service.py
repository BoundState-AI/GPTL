"""Deterministic Slice 2 candidate-preservation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.audit import SnapshotDecisionAuditEvent
from gptl.core.canonical import canonical_sha256
from gptl.core.directives import DisplayDirective, DisplayTemplateRegistry
from gptl.core.persistence import SNAPSHOT_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.ratification import (
    IntakeRecord,
    IntakeValue,
    RatificationEvent,
    RatificationGateResult,
    evaluate_ratification_gate,
)
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    FieldId,
    OpaqueId,
    TermId,
)
from gptl.core.snapshot import KnowledgeSnapshot, build_snapshot, snapshot_hash
from gptl.mie.calibration import CalibrationEvaluation
from gptl.mie.candidates import (
    CandidatePackConfigurationError,
    CandidateSetResult,
    load_candidate_set,
)
from gptl.mie.predicates import ApplicabilityEvaluation, ApplicabilityTruth, ContextValue
from gptl.mie.records import CandidatePack
from gptl.mie.schema import (
    AdvisoryDecision,
    BoundDecisionContext,
    CandidateAssessment,
    CandidateConfigurationIssue,
    Citation,
    MIEOutput,
    RefusalDecision,
    RefusalType,
    Tier1Output,
    Tier2Output,
)


class Slice2Request(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: OpaqueId
    decision_id: OpaqueId
    case_id: OpaqueId
    audit_event_id: OpaqueId
    snapshot_id: OpaqueId
    requested_pack_version_id: OpaqueId
    as_of_time: CanonicalTimestamp


class Slice2Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    canonicalization_policy: CanonicalizationPolicy
    operational_mode: Literal["RESEARCH_ONLY"]
    engine_id: OpaqueId
    engine_version: OpaqueId
    display_registry: DisplayTemplateRegistry
    missing_evidence_action: DisplayDirective
    configuration_action: DisplayDirective
    integrity_action: DisplayDirective
    unratified_next_step: DisplayDirective
    tier1_unratified_gap_id: TermId
    unratified_route_reason_id: TermId
    integrity_failure_route_reason_id: TermId
    configuration_invalid_route_reason_id: TermId
    missing_context_route_reason_id: TermId
    snapshot_refusal_event_type_id: TermId
    advisory_event_type_id: TermId
    required_measurement_ids: tuple[TermId, ...]
    required_record_type_ids: tuple[TermId, ...]

    def model_post_init(self, context: object) -> None:
        for directive in (
            self.missing_evidence_action,
            self.configuration_action,
            self.integrity_action,
            self.unratified_next_step,
        ):
            self.display_registry.validate_directive(directive)


class Slice2Runtime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    pack: CandidatePack
    intake: IntakeRecord
    ratification_events: tuple[RatificationEvent, ...]
    additional_bound_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_order(self) -> Slice2Runtime:
        event_keys = tuple(
            (item.event_ref.logical_id, item.event_ref.version_id)
            for item in self.ratification_events
        )
        if event_keys != tuple(sorted(set(event_keys))):
            raise ValueError("ratification events must be unique and sorted")
        ref_keys = tuple((item.logical_id, item.version_id) for item in self.additional_bound_refs)
        if ref_keys != tuple(sorted(set(ref_keys))):
            raise ValueError("additional bound refs must be unique and sorted")
        return self


@dataclass(frozen=True)
class Slice2ExecutionResult:
    output: MIEOutput
    snapshot: KnowledgeSnapshot
    audit_events: tuple[SnapshotDecisionAuditEvent, ...]
    bound_versions: tuple[GovernedRef, ...]


@dataclass(frozen=True)
class Slice2IntakeReady:
    gate: RatificationGateResult
    snapshot: KnowledgeSnapshot
    context: BoundDecisionContext


class CandidateSetReadyForLaterSlice(RuntimeError):
    def __init__(
        self,
        candidate_set: CandidateSetResult,
        snapshot: KnowledgeSnapshot,
    ) -> None:
        super().__init__("candidate set is resolved; MSA routing begins in Slice 3")
        self.candidate_set = candidate_set
        self.snapshot = snapshot


class PackVersionBindingError(ValueError):
    pass


class RatificationStateBindingError(ValueError):
    pass


def build_candidate_preservation(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
) -> Slice2ExecutionResult:
    intake_result = prepare_snapshot_bound_intake(request, runtime, policy)
    if isinstance(intake_result, Slice2ExecutionResult):
        return intake_result
    gate = intake_result.gate
    snapshot = intake_result.snapshot
    context = intake_result.context
    pack = runtime.pack
    context_values = context_values_from_intake(gate.admitted_values)
    try:
        candidate_set = load_candidate_set(
            pack,
            context_values,
            policy.canonicalization_policy,
        )
    except CandidatePackConfigurationError:
        return build_snapshot_refusal(
            request,
            runtime,
            policy,
            snapshot,
            context,
            RefusalType.CONFIGURATION_INVALID,
            policy.configuration_action,
            policy.configuration_invalid_route_reason_id,
            None,
            None,
            (),
            None,
            (),
            (),
        )
    if candidate_set.has_invalid:
        return build_snapshot_refusal(
            request,
            runtime,
            policy,
            snapshot,
            context,
            RefusalType.CONFIGURATION_INVALID,
            policy.configuration_action,
            policy.configuration_invalid_route_reason_id,
            None,
            None,
            candidate_set.assessments,
            candidate_set.configuration_issues,
            candidate_set.citations,
            (),
        )
    if candidate_set.has_unknown:
        missing_fields = tuple(
            sorted(
                {
                    field
                    for evaluation in candidate_set.applicability_evaluations
                    if evaluation.truth == ApplicabilityTruth.UNKNOWN
                    for field in evaluation.missing_field_ids
                }
            )
        )
        return build_snapshot_refusal(
            request,
            runtime,
            policy,
            snapshot,
            context,
            RefusalType.MISSING_REQUIRED_EVIDENCE,
            policy.missing_evidence_action,
            policy.missing_context_route_reason_id,
            None,
            None,
            candidate_set.assessments,
            None,
            candidate_set.citations,
            missing_fields,
        )
    raise CandidateSetReadyForLaterSlice(candidate_set, snapshot)


def prepare_snapshot_bound_intake(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
) -> Slice2IntakeReady | Slice2ExecutionResult:
    pack = runtime.pack
    if request.requested_pack_version_id != pack.manifest.pack_ref.version_id:
        raise PackVersionBindingError("Slice 2 requires an exact loaded pack version")
    runtime_gate = evaluate_ratification_gate(
        runtime.intake,
        runtime.ratification_events,
        pack.manifest.pack_ref,
        request.as_of_time,
        policy.canonicalization_policy,
    )
    snapshot = _build_runtime_snapshot(request, runtime, policy, runtime_gate.active_state_hash)
    # Eligibility must consume the event set that became durable. Reusing only
    # pre-snapshot state would allow later snapshot assembly changes to escape replay.
    gate = evaluate_ratification_gate(
        runtime.intake,
        snapshot.ratification_events,
        snapshot.pack_ref,
        snapshot.as_of_time,
        policy.canonicalization_policy,
    )
    if gate.active_state_hash != snapshot.ratification_state_hash:
        raise RatificationStateBindingError("snapshot ratification state hash mismatch")
    snapshot_digest = snapshot_hash(snapshot, policy.canonicalization_policy)
    context = BoundDecisionContext(
        context_kind="SNAPSHOT_BOUND",
        pack_ref=pack.manifest.pack_ref,
        engine_policy_ref=pack.engine_policy.policy_ref,
        evidence_scope_ref=pack.manifest.evidence_scope_ref,
        knowledge_snapshot_hash=snapshot_digest,
    )
    if gate.integrity_failure_field_ids:
        return build_snapshot_refusal(
            request,
            runtime,
            policy,
            snapshot,
            context,
            RefusalType.INTEGRITY_FAILURE,
            policy.integrity_action,
            policy.integrity_failure_route_reason_id,
            None,
            None,
            (),
            None,
            (),
            (),
        )
    present_fields = {item.field_id for item in runtime.intake.values}
    missing_required = set(pack.engine_policy.required_intake_field_ids) - present_fields
    unratified_fields = tuple(sorted(set(gate.unratified_field_ids) | missing_required))
    if not gate.eligible or unratified_fields:
        return _advisory_result(
            request,
            runtime,
            policy,
            snapshot,
            context,
            unratified_fields,
        )
    return Slice2IntakeReady(gate=gate, snapshot=snapshot, context=context)


def execute_candidate_preservation(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
    store: PostgresRunStore,
) -> Slice2ExecutionResult:
    result = build_candidate_preservation(request, runtime, policy)
    store.persist_snapshot_run(
        request.run_id,
        result.output,
        result.snapshot,
        result.audit_events,
        result.bound_versions,
        SNAPSHOT_RUN_SCHEMA_VERSION,
    )
    return result


def _build_runtime_snapshot(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
    ratification_state_hash: str,
) -> KnowledgeSnapshot:
    pack = runtime.pack
    candidate_refs = tuple(
        ref
        for candidate in pack.candidates
        for ref in (
            candidate.failure_mode_ref,
            candidate.predicate_ref,
            *candidate.evidence_refs,
        )
    )
    group_refs = tuple(
        ref for group in pack.selection_groups for ref in (group.group_ref, *group.evidence_refs)
    )
    intake_refs = (
        runtime.intake.intake_ref,
        *(value.source_ref for value in runtime.intake.values),
        *(
            value.ratification_event_ref
            for value in runtime.intake.values
            if value.ratification_event_ref is not None
        ),
    )
    display_refs = (
        policy.display_registry.registry_ref,
        *(template.template_ref for template in policy.display_registry.templates),
    )
    return build_snapshot(
        snapshot_id=request.snapshot_id,
        as_of_time=request.as_of_time,
        pack_ref=pack.manifest.pack_ref,
        engine_policy_ref=pack.engine_policy.policy_ref,
        evidence_scope_ref=pack.manifest.evidence_scope_ref,
        algorithm_refs=(pack.engine_policy.applicability_algorithm_ref,),
        unit_registry_ref=pack.unit_registry.registry_ref,
        field_registry_ref=pack.field_registry.registry_ref,
        canonicalization_policy_ref=pack.engine_policy.canonicalization_policy_ref,
        serialization_policy_ref=pack.engine_policy.serialization_policy_ref,
        lexical_policy_ref=pack.engine_policy.lexical_policy_ref,
        ratification_state_hash=ratification_state_hash,
        used_refs=(
            pack.manifest.method_ref,
            *candidate_refs,
            *group_refs,
            *intake_refs,
            *display_refs,
            *runtime.additional_bound_refs,
        ),
        ratification_events=runtime.ratification_events,
        policy=policy.canonicalization_policy,
    )


def context_values_from_intake(values: tuple[IntakeValue, ...]) -> tuple[ContextValue, ...]:
    context_values = []
    for raw_value in values:
        refs = [raw_value.source_ref]
        if raw_value.ratification_event_ref is not None:
            refs.append(raw_value.ratification_event_ref)
        refs.sort(key=lambda item: (item.logical_id, item.version_id))
        context_values.append(
            ContextValue(
                value_id=raw_value.value_id,
                field_id=raw_value.field_id,
                value=raw_value.value,
                evidence_refs=tuple(refs),
            )
        )
    context_values.sort(key=lambda item: (item.field_id, item.value_id))
    return tuple(context_values)


def build_snapshot_refusal(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
    snapshot: KnowledgeSnapshot,
    context: BoundDecisionContext,
    refusal_type: RefusalType,
    action: DisplayDirective,
    route_reason_id: TermId | None,
    calibration_evaluation: CalibrationEvaluation | None,
    msa_applicability_evaluations: tuple[ApplicabilityEvaluation, ...] | None,
    assessments: tuple[CandidateAssessment, ...],
    configuration_issues: tuple[CandidateConfigurationIssue, ...] | None,
    citations: tuple[Citation, ...],
    missing_field_ids: tuple[FieldId, ...],
) -> Slice2ExecutionResult:
    validation_context = {"canonicalization_policy": policy.canonicalization_policy}
    decision = RefusalDecision.model_validate(
        {
            "decision_id": request.decision_id,
            "case_id": request.case_id,
            "tier": 1,
            "dispositional": False,
            "non_record_of_record": True,
            "operational_mode": policy.operational_mode,
            "engine_id": policy.engine_id,
            "engine_version": policy.engine_version,
            "as_of_time": request.as_of_time,
            "verdict": "REFUSED",
            "refusal_type": refusal_type,
            "context": context,
            "method_ref": runtime.pack.manifest.method_ref,
            "route_reason_id": route_reason_id,
            "calibration_evaluation": calibration_evaluation,
            "msa_applicability_evaluations": msa_applicability_evaluations,
            "assessments": assessments,
            "configuration_issues": configuration_issues,
            "citations": citations,
            "missing_field_ids": missing_field_ids,
            "required_human_action": action,
            "audit_event_ids": (request.audit_event_id,),
        },
        context=validation_context,
    )
    decision_digest = canonical_sha256(decision, policy.canonicalization_policy)
    output = Tier1Output(
        output_kind="TIER1_DECISION",
        decision=decision,
        decision_hash=decision_digest,
    )
    return finalize_snapshot_output(
        request,
        runtime,
        policy,
        snapshot,
        output,
        decision_digest,
        policy.snapshot_refusal_event_type_id,
    )


def _advisory_result(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
    snapshot: KnowledgeSnapshot,
    context: BoundDecisionContext,
    proposed_fields: tuple[FieldId, ...],
) -> Slice2ExecutionResult:
    validation_context = {"canonicalization_policy": policy.canonicalization_policy}
    advisory = AdvisoryDecision.model_validate(
        {
            "decision_id": request.decision_id,
            "case_id": request.case_id,
            "tier": 2,
            "status": "ADVISORY_NO_VERDICT",
            "dispositional": False,
            "non_record_of_record": True,
            "operational_mode": policy.operational_mode,
            "engine_id": policy.engine_id,
            "engine_version": policy.engine_version,
            "context": context,
            "as_of_time": request.as_of_time,
            "method_resolution": "RESOLVED",
            "method_ref": runtime.pack.manifest.method_ref,
            "route_reason_id": policy.unratified_route_reason_id,
            "proposed_field_ids": proposed_fields,
            "candidate_failure_mode_refs": runtime.pack.manifest.candidate_refs,
            "applicability_evaluations": (),
            "open_discriminator_refs": (),
            "required_measurement_ids": policy.required_measurement_ids,
            "required_record_type_ids": policy.required_record_type_ids,
            "tier1_eligibility_gap_ids": (policy.tier1_unratified_gap_id,),
            "next_steps": (policy.unratified_next_step,),
            "citations": (),
            "audit_event_ids": (request.audit_event_id,),
        },
        context=validation_context,
    )
    advisory_digest = canonical_sha256(advisory, policy.canonicalization_policy)
    output = Tier2Output(
        output_kind="TIER2_ADVISORY",
        advisory=advisory,
        advisory_hash=advisory_digest,
    )
    return finalize_snapshot_output(
        request,
        runtime,
        policy,
        snapshot,
        output,
        advisory_digest,
        policy.advisory_event_type_id,
    )


def finalize_snapshot_output(
    request: Slice2Request,
    runtime: Slice2Runtime,
    policy: Slice2Policy,
    snapshot: KnowledgeSnapshot,
    output: MIEOutput,
    output_hash: str,
    event_type_id: TermId,
) -> Slice2ExecutionResult:
    digest = snapshot_hash(snapshot, policy.canonicalization_policy)
    audit_event = SnapshotDecisionAuditEvent.model_validate(
        {
            "event_id": request.audit_event_id,
            "run_id": request.run_id,
            "sequence": 0,
            "event_type_id": event_type_id,
            "output_kind": output.output_kind,
            "output_hash": output_hash,
            "snapshot_hash": digest,
            "as_of_time": request.as_of_time,
            "context_kind": "SNAPSHOT_BOUND",
        },
        context={"canonicalization_policy": policy.canonicalization_policy},
    )
    return Slice2ExecutionResult(
        output=output,
        snapshot=snapshot,
        audit_events=(audit_event,),
        bound_versions=snapshot.bound_versions,
    )
