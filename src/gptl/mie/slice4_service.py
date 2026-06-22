"""Deterministic Slice 4 signature, discrimination, and confirmation routing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from gptl.core.directives import DisplayDirective
from gptl.core.persistence import SLICE4_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import TermId
from gptl.mie.candidates import CandidatePackConfigurationError, load_candidate_set
from gptl.mie.diagnostics import (
    AttestationEvent,
    AuthorizedRolePolicy,
    CandidateDiagnosticContract,
    ConfirmationEvaluation,
    ConfirmTest,
    DiagnosticActiveState,
    DiagnosticConfigurationError,
    DiagnosticEngineError,
    DiagnosticIntegrityError,
    DiagnosticRoutePolicy,
    Discriminator,
    DiscriminatorResult,
    EvidenceTypeAssertion,
    GovernedNumericPolicy,
    HumanAttestedConfirmTest,
    RoleAuthorizationEvent,
    SignatureFeature,
    StructuredConfirmTest,
    SupportEvaluation,
    evaluate_confirmation,
    evaluate_discriminators,
    evaluate_signature,
    evaluate_support,
    evaluated_fraction,
    numeric_policy_by_ref,
    resolve_diagnostic_active_state,
)
from gptl.mie.predicates import ApplicabilityTruth
from gptl.mie.schema import (
    CandidateAssessment,
    CandidateConfigurationIssue,
    Citation,
    IndeterminateDecision,
    MethodArtifactDecision,
    RefusalType,
)
from gptl.mie.slice2_service import (
    Slice2ExecutionResult,
    Slice2Request,
    build_snapshot_refusal,
)
from gptl.mie.slice3_service import (
    Slice3OutsideVariationReady,
    Slice3Policy,
    Slice3Runtime,
    build_investigation_result,
    investigation_header,
    prepare_msa_calibration_gate,
    sorted_citations,
)


class Slice4RouteReasons(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    diagnostic_configuration_invalid: TermId
    diagnostic_engine_failure: TermId
    diagnostic_integrity_failure: TermId
    method_artifact: TermId
    diagnostic_indeterminate: TermId

    @model_validator(mode="after")
    def validate_unique(self) -> Slice4RouteReasons:
        values = tuple(self.model_dump(mode="python").values())
        if values != tuple(dict.fromkeys(values)):
            raise ValueError("Slice 4 route reasons must be distinct")
        return self


class Slice4Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice3_policy: Slice3Policy
    route_policy_ref: GovernedRef
    route_reasons: Slice4RouteReasons
    method_artifact_action: DisplayDirective
    indeterminate_action: DisplayDirective
    engine_failure_action: DisplayDirective
    what_would_change_artifact: tuple[DisplayDirective, ...]
    method_artifact_event_type_id: TermId
    indeterminate_event_type_id: TermId

    def model_post_init(self, context: object) -> None:
        directives = (
            self.method_artifact_action,
            self.indeterminate_action,
            self.engine_failure_action,
            *self.what_would_change_artifact,
        )
        if not self.what_would_change_artifact:
            raise ValueError("Slice 4 artifact policy requires a change directive")
        template_ids = tuple(item.template_id for item in self.what_would_change_artifact)
        if template_ids != tuple(sorted(set(template_ids))):
            raise ValueError("artifact change directives must be unique and sorted")
        for directive in directives:
            self.slice3_policy.slice2_policy.display_registry.validate_directive(directive)


class Slice4Runtime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice3_runtime: Slice3Runtime
    diagnostic_route_policy: DiagnosticRoutePolicy
    numeric_policies: tuple[GovernedNumericPolicy, ...]
    candidate_contracts: tuple[CandidateDiagnosticContract, ...]
    signature_features: tuple[SignatureFeature, ...]
    discriminators: tuple[Discriminator, ...]
    discriminator_results: tuple[DiscriminatorResult, ...]
    confirm_tests: tuple[ConfirmTest, ...]
    evidence_type_assertions: tuple[EvidenceTypeAssertion, ...]
    role_policies: tuple[AuthorizedRolePolicy, ...]
    role_authorization_events: tuple[RoleAuthorizationEvent, ...]
    attestation_events: tuple[AttestationEvent, ...]

    @model_validator(mode="after")
    def validate_order_and_bindings(self) -> Slice4Runtime:
        pack = self.slice3_runtime.slice2_runtime.pack
        pack_refs = pack.manifest.candidate_refs
        contract_refs = tuple(item.failure_mode_ref for item in self.candidate_contracts)
        if contract_refs != pack_refs:
            raise ValueError("every published candidate requires one ordered diagnostic contract")
        _validate_model_ref_order(
            self.numeric_policies,
            lambda item: item.policy_ref,
            "numeric policies",
        )
        _validate_model_ref_order(
            self.candidate_contracts,
            lambda item: item.contract_ref,
            "candidate diagnostic contracts",
        )
        _validate_model_ref_order(
            self.signature_features,
            lambda item: item.feature_ref,
            "signature features",
        )
        _validate_model_ref_order(
            self.discriminators,
            lambda item: item.discriminator_ref,
            "discriminators",
        )
        _validate_versioned_event_order(
            self.discriminator_results,
            lambda item: item.result_ref,
            "discriminator results",
        )
        _validate_model_ref_order(
            self.confirm_tests,
            lambda item: item.test_ref,
            "confirm tests",
        )
        _validate_model_ref_order(
            self.evidence_type_assertions,
            lambda item: item.evidence_ref,
            "evidence type assertions",
        )
        _validate_model_ref_order(
            self.role_policies,
            lambda item: item.policy_ref,
            "role policies",
        )
        _validate_versioned_event_order(
            self.role_authorization_events,
            lambda item: item.event_ref,
            "role authorization events",
        )
        _validate_versioned_event_order(
            self.attestation_events,
            lambda item: item.attestation_ref,
            "attestation events",
        )
        contract_by_candidate = {item.failure_mode_ref: item for item in self.candidate_contracts}
        expected_feature_refs = sorted_unique_refs(
            tuple(ref for item in self.candidate_contracts for ref in item.signature_feature_refs)
        )
        if tuple(item.feature_ref for item in self.signature_features) != expected_feature_refs:
            raise ValueError("signature feature set must resolve every contract exactly")
        if any(
            item.candidate_ref not in contract_by_candidate
            or item.feature_ref
            not in contract_by_candidate[item.candidate_ref].signature_feature_refs
            for item in self.signature_features
        ):
            raise ValueError("signature feature candidate binding mismatch")
        expected_discriminator_refs = sorted_unique_refs(
            tuple(ref for item in self.candidate_contracts for ref in item.discriminator_refs)
        )
        if (
            tuple(item.discriminator_ref for item in self.discriminators)
            != expected_discriminator_refs
        ):
            raise ValueError("discriminator set must resolve every contract exactly")
        if any(
            item.candidate_ref not in contract_by_candidate
            or item.discriminator_ref
            not in contract_by_candidate[item.candidate_ref].discriminator_refs
            for item in self.discriminators
        ):
            raise ValueError("discriminator candidate binding mismatch")
        expected_numeric_refs = sorted_unique_refs(
            (
                self.diagnostic_route_policy.delta_dominance_policy_ref,
                self.diagnostic_route_policy.high_power_threshold_policy_ref,
                *(item.min_signature_coverage_policy_ref for item in self.candidate_contracts),
                *(item.tau_confirm_policy_ref for item in self.candidate_contracts),
                *(item.tau_verdict_policy_ref for item in self.candidate_contracts),
                *(item.weight_policy_ref for item in self.signature_features),
                *(item.discriminating_power_policy_ref for item in self.discriminators),
            )
        )
        if tuple(item.policy_ref for item in self.numeric_policies) != expected_numeric_refs:
            raise ValueError("diagnostic numeric policy set must resolve exactly")
        if any(item.scope_ref != pack.manifest.pack_ref for item in self.numeric_policies):
            raise ValueError("diagnostic numeric policy scope must bind the exact pack")
        known_discriminators = set(item.discriminator_ref for item in self.discriminators)
        if any(
            item.discriminator_ref not in known_discriminators
            for item in self.discriminator_results
        ):
            raise ValueError("discriminator result references an unpublished discriminator")
        if sorted_unique_refs(
            tuple(item.confirm_test_ref for item in self.candidate_contracts)
        ) != tuple(item.test_ref for item in self.confirm_tests):
            raise ValueError("candidate confirm tests must resolve exactly")
        if any(item.method_ref != pack.manifest.method_ref for item in self.role_policies):
            raise ValueError("role policy method binding mismatch")
        if any(
            item.failure_mode_ref not in pack_refs or item.method_ref != pack.manifest.method_ref
            for item in self.attestation_events
        ):
            raise ValueError("attestation candidate or method binding mismatch")
        return self


@dataclass(frozen=True)
class _EvaluatedCandidate:
    assessment: CandidateAssessment
    contract: CandidateDiagnosticContract
    support: SupportEvaluation | None
    confirmation: ConfirmationEvaluation | None
    discriminators: tuple[Discriminator, ...]


def build_artifact_confirmation(
    request: Slice2Request,
    runtime: Slice4Runtime,
    policy: Slice4Policy,
) -> Slice2ExecutionResult:
    _validate_snapshot_bindings(runtime, policy)
    prepared = prepare_msa_calibration_gate(
        request,
        runtime.slice3_runtime,
        policy.slice3_policy,
    )
    if isinstance(prepared, Slice2ExecutionResult):
        return prepared
    diagnostic_citations = _diagnostic_citations(runtime)
    try:
        active_state = resolve_diagnostic_active_state(
            runtime.discriminator_results,
            runtime.role_authorization_events,
            runtime.attestation_events,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
    except DiagnosticIntegrityError:
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.INTEGRITY_FAILURE,
            policy.route_reasons.diagnostic_integrity_failure,
            (),
            None,
            sorted_citations((*prepared.citations, *diagnostic_citations)),
        )
    except DiagnosticConfigurationError:
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.CONFIGURATION_INVALID,
            policy.route_reasons.diagnostic_configuration_invalid,
            (),
            None,
            sorted_citations((*prepared.citations, *diagnostic_citations)),
        )
    try:
        candidates = load_candidate_set(
            runtime.slice3_runtime.slice2_runtime.pack,
            prepared.context_values,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
    except CandidatePackConfigurationError:
        refusal_citations = sorted_citations((*prepared.citations, *diagnostic_citations))
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.CONFIGURATION_INVALID,
            policy.route_reasons.diagnostic_configuration_invalid,
            (),
            None,
            refusal_citations,
        )
    base_citations = sorted_citations(
        (*prepared.citations, *candidates.citations, *diagnostic_citations)
    )
    if candidates.has_invalid:
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.CONFIGURATION_INVALID,
            policy.route_reasons.diagnostic_configuration_invalid,
            candidates.assessments,
            candidates.configuration_issues,
            base_citations,
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
            runtime.slice3_runtime.slice2_runtime,
            policy.slice3_policy.slice2_policy,
            prepared.intake.snapshot,
            prepared.intake.context,
            RefusalType.MISSING_REQUIRED_EVIDENCE,
            policy.slice3_policy.slice2_policy.missing_evidence_action,
            policy.slice3_policy.route_reasons.candidate_missing_context,
            prepared.calibration,
            prepared.msa.applicability_evaluations,
            candidates.assessments,
            None,
            base_citations,
            missing_fields,
        )
    try:
        evaluated = _evaluate_candidates(request, runtime, policy, prepared, candidates.assessments)
        return _route_diagnostic_result(
            request,
            runtime,
            policy,
            prepared,
            evaluated,
            active_state,
            base_citations,
        )
    except DiagnosticConfigurationError:
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.CONFIGURATION_INVALID,
            policy.route_reasons.diagnostic_configuration_invalid,
            candidates.assessments,
            None,
            base_citations,
        )
    except DiagnosticIntegrityError:
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.INTEGRITY_FAILURE,
            policy.route_reasons.diagnostic_integrity_failure,
            candidates.assessments,
            None,
            base_citations,
        )
    except (DiagnosticEngineError, ValidationError):
        return _diagnostic_refusal(
            request,
            runtime,
            policy,
            prepared,
            RefusalType.ENGINE_FAILURE,
            policy.route_reasons.diagnostic_engine_failure,
            candidates.assessments,
            None,
            base_citations,
        )


def execute_artifact_confirmation(
    request: Slice2Request,
    runtime: Slice4Runtime,
    policy: Slice4Policy,
    store: PostgresRunStore,
) -> Slice2ExecutionResult:
    result = build_artifact_confirmation(request, runtime, policy)
    store.persist_snapshot_run(
        request.run_id,
        result.output,
        result.snapshot,
        result.audit_events,
        result.bound_versions,
        SLICE4_RUN_SCHEMA_VERSION,
    )
    return result


def _evaluate_candidates(
    request: Slice2Request,
    runtime: Slice4Runtime,
    policy: Slice4Policy,
    prepared: Slice3OutsideVariationReady,
    assessments: tuple[CandidateAssessment, ...],
) -> tuple[_EvaluatedCandidate, ...]:
    contracts = {item.failure_mode_ref: item for item in runtime.candidate_contracts}
    evaluated: list[_EvaluatedCandidate] = []
    for assessment in assessments:
        contract = contracts[assessment.candidate_ref]
        if assessment.applicability != ApplicabilityTruth.TRUE:
            evaluated.append(_EvaluatedCandidate(assessment, contract, None, None, ()))
            continue
        features = tuple(
            item
            for item in runtime.signature_features
            if item.candidate_ref == contract.failure_mode_ref
        )
        signature = evaluate_signature(
            contract,
            features,
            prepared.context_values,
            runtime.numeric_policies,
            runtime.slice3_runtime.slice2_runtime.pack.field_registry,
            runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
            runtime.diagnostic_route_policy,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
        if signature.evidence_state == "OPEN_UNASSESSED":
            open_assessment = _assessment(
                assessment,
                "OPEN_UNASSESSED",
                "OPEN_UNASSESSED",
                signature.signature_match_score,
                signature.signature_coverage,
                None,
                signature.evidence_refs,
                (
                    contract.contract_ref,
                    contract.min_signature_coverage_policy_ref,
                ),
            )
            evaluated.append(_EvaluatedCandidate(open_assessment, contract, None, None, ()))
            continue
        discriminators = tuple(
            item
            for item in runtime.discriminators
            if item.candidate_ref == contract.failure_mode_ref
        )
        discriminator_keys = {
            (item.discriminator_ref.logical_id, item.discriminator_ref.version_id)
            for item in discriminators
        }
        results = tuple(
            item
            for item in runtime.discriminator_results
            if (
                item.discriminator_ref.logical_id,
                item.discriminator_ref.version_id,
            )
            in discriminator_keys
        )
        discriminator_evaluations = evaluate_discriminators(
            contract,
            discriminators,
            results,
            prepared.context_values,
            runtime.slice3_runtime.slice2_runtime.pack.field_registry,
            runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
        support = evaluate_support(
            signature,
            discriminator_evaluations,
            discriminators,
            runtime.numeric_policies,
            runtime.diagnostic_route_policy,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
        confirm_test = _confirm_test(contract.confirm_test_ref, runtime.confirm_tests)
        confirmation = evaluate_confirmation(
            contract,
            confirm_test,
            prepared.context_values,
            runtime.evidence_type_assertions,
            runtime.role_policies,
            runtime.role_authorization_events,
            tuple(
                item
                for item in runtime.attestation_events
                if item.failure_mode_ref == contract.failure_mode_ref
            ),
            runtime.slice3_runtime.slice2_runtime.pack.manifest.method_ref,
            runtime.slice3_runtime.slice2_runtime.pack.field_registry,
            runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
        min_coverage = numeric_policy_by_ref(
            contract.min_signature_coverage_policy_ref,
            runtime.numeric_policies,
            "MIN_SIGNATURE_COVERAGE",
            runtime.diagnostic_route_policy.dimensionless_unit_id,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
        ).value
        tau_confirm = numeric_policy_by_ref(
            contract.tau_confirm_policy_ref,
            runtime.numeric_policies,
            "TAU_CONFIRM",
            runtime.diagnostic_route_policy.dimensionless_unit_id,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
        ).value
        confirmed = (
            signature.signature_coverage >= min_coverage
            and support.support_score >= tau_confirm
            and confirmation.satisfied
        )
        final_assessment = _assessment(
            assessment,
            "EVALUABLE",
            "CONFIRMED" if confirmed else "CANDIDATE",
            signature.signature_match_score,
            signature.signature_coverage,
            support.support_score,
            sorted_unique_refs(
                (
                    *signature.evidence_refs,
                    *support.evidence_refs,
                    *confirmation.evidence_refs,
                )
            ),
            (
                runtime.diagnostic_route_policy.combine_algorithm_ref,
                runtime.diagnostic_route_policy.delta_dominance_policy_ref,
                contract.contract_ref,
                contract.min_signature_coverage_policy_ref,
                contract.tau_confirm_policy_ref,
                contract.tau_verdict_policy_ref,
                confirm_test.test_ref,
            ),
        )
        evaluated.append(
            _EvaluatedCandidate(
                final_assessment,
                contract,
                support,
                confirmation,
                discriminators,
            )
        )
    return tuple(
        sorted(
            evaluated,
            key=lambda item: (
                item.assessment.candidate_ref.logical_id,
                item.assessment.candidate_ref.version_id,
            ),
        )
    )


def _route_diagnostic_result(
    request: Slice2Request,
    runtime: Slice4Runtime,
    policy: Slice4Policy,
    prepared: Slice3OutsideVariationReady,
    evaluated: tuple[_EvaluatedCandidate, ...],
    active_state: DiagnosticActiveState,
    citations: tuple[Citation, ...],
) -> Slice2ExecutionResult:
    assessments = tuple(item.assessment for item in evaluated)
    evaluable = tuple(item for item in evaluated if item.support is not None)
    confirmed = tuple(item for item in evaluable if item.assessment.status == "CONFIRMED")
    delta = numeric_policy_by_ref(
        runtime.diagnostic_route_policy.delta_dominance_policy_ref,
        runtime.numeric_policies,
        "DELTA_DOMINANCE",
        runtime.diagnostic_route_policy.dimensionless_unit_id,
        request.as_of_time,
        policy.slice3_policy.slice2_policy.operational_mode,
    ).value
    dominant: list[_EvaluatedCandidate] = []
    for candidate in confirmed:
        if candidate.support is None:
            continue
        tau_verdict = numeric_policy_by_ref(
            candidate.contract.tau_verdict_policy_ref,
            runtime.numeric_policies,
            "TAU_VERDICT",
            runtime.diagnostic_route_policy.dimensionless_unit_id,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
        ).value
        other_scores = tuple(
            item.support.support_score
            for item in evaluable
            if item.support is not None
            and item.contract.contract_ref != candidate.contract.contract_ref
        )
        dominance_satisfied = (
            not other_scores or candidate.support.support_score - max(other_scores) >= delta
        )
        if candidate.support.support_score >= tau_verdict and dominance_satisfied:
            dominant.append(candidate)
    all_discriminator_evaluations = tuple(
        evaluation
        for item in evaluable
        if item.support is not None
        for evaluation in item.support.discriminator_evaluations
    )
    all_discriminators = tuple(
        discriminator for item in evaluable for discriminator in item.discriminators
    )
    if len(dominant) == 1:
        fraction = evaluated_fraction(
            all_discriminator_evaluations,
            all_discriminators,
            runtime.numeric_policies,
            runtime.diagnostic_route_policy,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
        return _artifact_result(
            request,
            runtime,
            policy,
            prepared,
            assessments,
            dominant[0],
            fraction,
            active_state,
            citations,
        )
    open_refs = sorted_unique_refs(
        tuple(
            discriminator.discriminator_ref
            for item in evaluated
            if item.assessment.status != "CONFIRMED" or len(confirmed) > 1
            for discriminator in item.discriminators
        )
    )
    if not open_refs:
        open_refs = sorted_unique_refs(
            tuple(item.discriminator_ref for item in runtime.discriminators)
        )
    if prepared.msa.selected_study_ref is None or prepared.msa.measured_uncertainty is None:
        raise DiagnosticEngineError("outside-variation continuation lost selected MSA")
    decision = IndeterminateDecision.model_validate(
        {
            **investigation_header(
                request,
                runtime.slice3_runtime,
                policy.slice3_policy,
                prepared.intake,
                prepared.calibration,
                prepared.msa,
            ),
            "verdict": "INDETERMINATE",
            "route_reason_id": policy.route_reasons.diagnostic_indeterminate,
            "assessments": assessments,
            "citations": citations,
            "required_human_action": policy.indeterminate_action,
            "msa_study_ref": prepared.msa.selected_study_ref,
            "measured_deviation": prepared.msa.measured_deviation.value,
            "measured_uncertainty": prepared.msa.measured_uncertainty.value,
            "uncertainty_unit_id": prepared.msa.measured_uncertainty.unit_id,
            "diagnostic_state_hash": active_state.state_hash,
            "open_discriminator_refs": open_refs,
        },
        context={
            "canonicalization_policy": policy.slice3_policy.slice2_policy.canonicalization_policy
        },
    )
    return build_investigation_result(
        request,
        runtime.slice3_runtime,
        policy.slice3_policy,
        prepared.intake,
        decision,
        policy.indeterminate_event_type_id,
    )


def _artifact_result(
    request: Slice2Request,
    runtime: Slice4Runtime,
    policy: Slice4Policy,
    prepared: Slice3OutsideVariationReady,
    assessments: tuple[CandidateAssessment, ...],
    dominant: _EvaluatedCandidate,
    fraction: Decimal,
    active_state: DiagnosticActiveState,
    citations: tuple[Citation, ...],
) -> Slice2ExecutionResult:
    if (
        dominant.confirmation is None
        or prepared.msa.selected_study_ref is None
        or prepared.msa.measured_uncertainty is None
    ):
        raise DiagnosticEngineError("artifact verdict lost required evidence")
    confirm_refs = {
        (item.logical_id, item.version_id) for item in dominant.confirmation.evidence_refs
    }
    confirm_citations = tuple(
        item
        for item in citations
        if (item.record_ref.logical_id, item.record_ref.version_id) in confirm_refs
    )
    decision = MethodArtifactDecision.model_validate(
        {
            **investigation_header(
                request,
                runtime.slice3_runtime,
                policy.slice3_policy,
                prepared.intake,
                prepared.calibration,
                prepared.msa,
            ),
            "verdict": "METHOD_ARTIFACT",
            "route_reason_id": policy.route_reasons.method_artifact,
            "assessments": assessments,
            "citations": citations,
            "required_human_action": policy.method_artifact_action,
            "msa_study_ref": prepared.msa.selected_study_ref,
            "measured_deviation": prepared.msa.measured_deviation.value,
            "measured_uncertainty": prepared.msa.measured_uncertainty.value,
            "uncertainty_unit_id": prepared.msa.measured_uncertainty.unit_id,
            "diagnostic_state_hash": active_state.state_hash,
            "confirmed_candidate_ref": dominant.assessment.candidate_ref,
            "evaluated_fraction_within_published_catalog": fraction,
            "confirm_evidence": confirm_citations,
            "what_would_change_this": policy.what_would_change_artifact,
        },
        context={
            "canonicalization_policy": policy.slice3_policy.slice2_policy.canonicalization_policy
        },
    )
    return build_investigation_result(
        request,
        runtime.slice3_runtime,
        policy.slice3_policy,
        prepared.intake,
        decision,
        policy.method_artifact_event_type_id,
    )


def _diagnostic_refusal(
    request: Slice2Request,
    runtime: Slice4Runtime,
    policy: Slice4Policy,
    prepared: Slice3OutsideVariationReady,
    refusal_type: RefusalType,
    route_reason_id: TermId,
    assessments: tuple[CandidateAssessment, ...],
    configuration_issues: tuple[CandidateConfigurationIssue, ...] | None,
    citations: tuple[Citation, ...],
) -> Slice2ExecutionResult:
    if refusal_type == RefusalType.INTEGRITY_FAILURE:
        action = policy.slice3_policy.slice2_policy.integrity_action
    elif refusal_type == RefusalType.ENGINE_FAILURE:
        action = policy.engine_failure_action
    else:
        action = policy.slice3_policy.slice2_policy.configuration_action
    return build_snapshot_refusal(
        request,
        runtime.slice3_runtime.slice2_runtime,
        policy.slice3_policy.slice2_policy,
        prepared.intake.snapshot,
        prepared.intake.context,
        refusal_type,
        action,
        route_reason_id,
        prepared.calibration,
        prepared.msa.applicability_evaluations,
        assessments,
        configuration_issues,
        citations,
        (),
    )


def _assessment(
    base: CandidateAssessment,
    evidence_state: str,
    status: str,
    signature_match_score: Decimal | None,
    signature_coverage: Decimal,
    candidate_support_score: Decimal | None,
    evidence_refs: tuple[GovernedRef, ...],
    rule_refs: tuple[GovernedRef, ...],
) -> CandidateAssessment:
    return CandidateAssessment.model_validate(
        {
            **base.model_dump(mode="python"),
            "evidence_state": evidence_state,
            "status": status,
            "signature_match_score": signature_match_score,
            "signature_coverage": signature_coverage,
            "candidate_support_score": candidate_support_score,
            "evidence_refs": sorted_unique_refs((*base.evidence_refs, *evidence_refs)),
            "rule_refs": sorted_unique_refs((*base.rule_refs, *rule_refs)),
        }
    )


def _confirm_test(
    ref: GovernedRef,
    tests: tuple[ConfirmTest, ...],
) -> StructuredConfirmTest | HumanAttestedConfirmTest:
    matches = tuple(item for item in tests if item.test_ref == ref)
    if len(matches) != 1:
        raise DiagnosticConfigurationError("confirm test reference must resolve exactly once")
    return matches[0]


def _diagnostic_citations(runtime: Slice4Runtime) -> tuple[Citation, ...]:
    records = (
        runtime.numeric_policies,
        runtime.candidate_contracts,
        runtime.signature_features,
        runtime.discriminators,
        runtime.discriminator_results,
        runtime.confirm_tests,
        runtime.evidence_type_assertions,
        runtime.role_policies,
        runtime.role_authorization_events,
        runtime.attestation_events,
        (runtime.diagnostic_route_policy,),
    )
    citations = tuple(
        Citation(
            record_type_id=item.record_type_id,
            record_ref=_record_ref(item),
            evidence_location=item.evidence_location,
        )
        for group in records
        for item in group
    )
    return sorted_citations(citations)


def _record_ref(item: object) -> GovernedRef:
    for attribute in (
        "contract_ref",
        "feature_ref",
        "result_ref",
        "test_ref",
        "evidence_ref",
        "event_ref",
        "attestation_ref",
        "discriminator_ref",
        "policy_ref",
    ):
        value = getattr(item, attribute, None)
        if isinstance(value, GovernedRef):
            return value
    raise DiagnosticConfigurationError("citable diagnostic record has no governed identity")


def _validate_snapshot_bindings(runtime: Slice4Runtime, policy: Slice4Policy) -> None:
    expected = (
        policy.route_policy_ref,
        *diagnostic_bound_refs(runtime),
    )
    actual = {
        (item.logical_id, item.version_id): item
        for item in runtime.slice3_runtime.slice2_runtime.additional_bound_refs
    }
    mismatched = tuple(
        item
        for item in sorted_unique_refs(expected)
        if actual.get((item.logical_id, item.version_id)) != item
    )
    if mismatched:
        raise ValueError("Slice 4 snapshot bindings omit or conflict with diagnostic records")


def diagnostic_bound_refs(runtime: Slice4Runtime) -> tuple[GovernedRef, ...]:
    return (
        runtime.diagnostic_route_policy.policy_ref,
        runtime.diagnostic_route_policy.combine_algorithm_ref,
        *runtime.diagnostic_route_policy.evidence_refs,
        *(
            ref
            for item in runtime.numeric_policies
            for ref in (
                item.policy_ref,
                item.scope_ref,
                item.derivation_ref,
                *item.governing_source_refs,
                item.validation_corpus_ref,
                *item.evidence_refs,
            )
        ),
        *(
            ref
            for item in runtime.candidate_contracts
            for ref in (
                item.contract_ref,
                item.failure_mode_ref,
                *item.signature_feature_refs,
                *item.discriminator_refs,
                item.confirm_test_ref,
                item.min_signature_coverage_policy_ref,
                item.tau_confirm_policy_ref,
                item.tau_verdict_policy_ref,
                *item.evidence_refs,
            )
        ),
        *(
            ref
            for item in runtime.signature_features
            for ref in (
                item.feature_ref,
                item.candidate_ref,
                item.predicate_ref,
                item.weight_policy_ref,
                *item.evidence_refs,
            )
        ),
        *(
            ref
            for item in runtime.discriminators
            for ref in (
                item.discriminator_ref,
                item.candidate_ref,
                item.artifact_predicate_ref,
                item.real_predicate_ref,
                item.discriminating_power_policy_ref,
                *item.evidence_refs,
            )
        ),
        *(
            ref
            for item in runtime.discriminator_results
            for ref in (
                item.result_ref,
                item.discriminator_ref,
                *((item.observed_value_ref,) if item.observed_value_ref is not None else ()),
            )
        ),
        *(
            ref
            for item in runtime.confirm_tests
            for ref in (
                item.test_ref,
                *((item.predicate_ref,) if isinstance(item, StructuredConfirmTest) else ()),
                *(
                    (item.authorized_role_policy_ref,)
                    if isinstance(item, HumanAttestedConfirmTest)
                    else ()
                ),
                *item.evidence_refs,
            )
        ),
        *(item.evidence_ref for item in runtime.evidence_type_assertions),
        *(ref for item in runtime.role_policies for ref in (item.policy_ref, *item.evidence_refs)),
        *(
            ref
            for item in runtime.role_authorization_events
            for ref in (item.event_ref, item.policy_ref)
        ),
        *(
            ref
            for item in runtime.attestation_events
            for ref in (
                item.attestation_ref,
                item.failure_mode_ref,
                item.method_ref,
                *item.supporting_evidence_refs,
            )
        ),
    )


_RecordT = TypeVar("_RecordT")


def _validate_model_ref_order(
    values: tuple[_RecordT, ...],
    ref_getter: Callable[[_RecordT], GovernedRef],
    label: str,
) -> None:
    refs = tuple(ref_getter(item) for item in values)
    if refs and sorted_unique_refs(refs) != refs:
        raise ValueError(f"{label} must be unique and sorted")


def _validate_versioned_event_order(
    values: tuple[_RecordT, ...],
    ref_getter: Callable[[_RecordT], GovernedRef],
    label: str,
) -> None:
    refs = tuple(ref_getter(item) for item in values)
    keys = tuple((item.logical_id, item.version_number, item.version_id) for item in refs)
    if keys != tuple(sorted(set(keys))):
        raise ValueError(f"{label} must be unique and version-sorted")
