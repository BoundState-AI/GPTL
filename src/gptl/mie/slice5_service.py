"""Deterministic Slice 5 bounded-catalog negative routing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from typing import Literal, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from gptl.core.directives import DisplayDirective
from gptl.core.persistence import SLICE5_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import TermId
from gptl.mie.diagnostics import (
    DiagnosticConfigurationError,
    DiagnosticEngineError,
    DiagnosticIntegrityError,
    GovernedNumericPolicy,
    canonical_ratio,
    numeric_policy_by_ref,
)
from gptl.mie.negative import (
    CatalogKnownGap,
    HardEliminationRule,
    NegativeRoutePolicy,
    RuleOutEvidenceRequirement,
)
from gptl.mie.predicates import (
    ApplicabilityTruth,
    PredicateConfigurationError,
    evaluate_applicability,
    validate_predicate_configuration,
)
from gptl.mie.schema import (
    CandidateAssessment,
    Citation,
    EvaluatedArtifact,
    IndeterminateDecision,
    KnownArtifactsExcludedDecision,
    KnownGap,
    RefusalType,
    Tier1Output,
)
from gptl.mie.slice2_service import Slice2ExecutionResult, Slice2Request
from gptl.mie.slice3_service import (
    build_investigation_result,
    investigation_header,
    sorted_citations,
)
from gptl.mie.slice4_service import (
    EvaluatedCandidate,
    Slice4InputsReady,
    Slice4Policy,
    Slice4Runtime,
    build_diagnostic_refusal,
    evaluate_diagnostic_candidates,
    prepare_diagnostic_inputs,
    route_diagnostic_result,
    updated_assessment,
)


class Slice5RouteReasons(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    known_artifacts_excluded: TermId


class Slice5Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice4_policy: Slice4Policy
    route_policy_ref: GovernedRef
    route_reasons: Slice5RouteReasons
    known_artifacts_excluded_action: DisplayDirective
    catalog_boundary: DisplayDirective
    known_artifacts_excluded_event_type_id: TermId

    def model_post_init(self, context: object) -> None:
        registry = self.slice4_policy.slice3_policy.slice2_policy.display_registry
        registry.validate_directive(self.known_artifacts_excluded_action)
        registry.validate_directive(self.catalog_boundary)


class Slice5Runtime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice4_runtime: Slice4Runtime
    negative_route_policy: NegativeRoutePolicy
    numeric_policies: tuple[GovernedNumericPolicy, ...]
    hard_elimination_rules: tuple[HardEliminationRule, ...]
    rule_out_requirements: tuple[RuleOutEvidenceRequirement, ...]
    known_gaps: tuple[CatalogKnownGap, ...]

    @model_validator(mode="after")
    def validate_order_and_bindings(self) -> Slice5Runtime:
        candidate_refs = (
            self.slice4_runtime.slice3_runtime.slice2_runtime.pack.manifest.candidate_refs
        )
        contracts = {
            item.failure_mode_ref: item for item in self.slice4_runtime.candidate_contracts
        }
        _validate_model_ref_order(
            self.numeric_policies,
            lambda item: item.policy_ref,
            "negative numeric policies",
        )
        _validate_model_ref_order(
            self.hard_elimination_rules,
            lambda item: item.rule_ref,
            "hard-elimination rules",
        )
        _validate_model_ref_order(
            self.rule_out_requirements,
            lambda item: item.requirement_ref,
            "rule-out requirements",
        )
        _validate_model_ref_order(self.known_gaps, lambda item: item.gap_ref, "known gaps")
        requirement_candidates = tuple(
            sorted(
                (item.candidate_ref.logical_id, item.candidate_ref.version_id)
                for item in self.rule_out_requirements
            )
        )
        expected_candidates = tuple(
            sorted((item.logical_id, item.version_id) for item in candidate_refs)
        )
        if requirement_candidates != expected_candidates:
            raise ValueError("every published candidate requires one rule-out contract")
        if any(item.candidate_ref not in contracts for item in self.hard_elimination_rules):
            raise ValueError("hard-elimination rule references an unpublished candidate")
        for requirement in self.rule_out_requirements:
            if not set(requirement.required_discriminator_refs).issubset(
                contracts[requirement.candidate_ref].discriminator_refs
            ):
                raise ValueError("rule-out requirement references a foreign discriminator")
        expected_numeric_refs = sorted_unique_refs(
            (
                self.negative_route_policy.min_evaluated_fraction_policy_ref,
                *(item.tau_ruleout_policy_ref for item in self.rule_out_requirements),
            )
        )
        if tuple(item.policy_ref for item in self.numeric_policies) != expected_numeric_refs:
            raise ValueError("negative numeric policy set must resolve exactly")
        pack_ref = self.slice4_runtime.slice3_runtime.slice2_runtime.pack.manifest.pack_ref
        if any(item.scope_ref != pack_ref for item in self.numeric_policies):
            raise ValueError("negative numeric policy scope must bind the exact pack")
        category_ids = tuple(item.category_id for item in self.known_gaps)
        if category_ids != tuple(sorted(set(category_ids))):
            raise ValueError("known gap categories must be unique and sorted")
        return self


def build_honest_negative(
    request: Slice2Request,
    runtime: Slice5Runtime,
    policy: Slice5Policy,
) -> Slice2ExecutionResult:
    inputs = prepare_diagnostic_inputs(request, runtime.slice4_runtime, policy.slice4_policy)
    if isinstance(inputs, Slice2ExecutionResult):
        return inputs
    citations = sorted_citations((*inputs.citations, *_negative_citations(runtime)))
    try:
        _validate_snapshot_bindings(runtime, policy)
        _validate_gap_directives(runtime, policy)
        assessments, ruling_refs = _apply_hard_eliminations(
            request,
            runtime,
            policy,
            inputs,
        )
        evaluated = evaluate_diagnostic_candidates(
            request,
            runtime.slice4_runtime,
            policy.slice4_policy,
            inputs.prepared,
            assessments,
        )
        evaluated, ruling_refs = _apply_rule_outs(
            request,
            runtime,
            policy,
            evaluated,
            ruling_refs,
        )
        positive_or_open = route_diagnostic_result(
            request,
            runtime.slice4_runtime,
            policy.slice4_policy,
            inputs.prepared,
            evaluated,
            inputs.active_state,
            citations,
        )
        if not isinstance(positive_or_open.output, Tier1Output):
            raise DiagnosticEngineError("diagnostic route returned a non-Tier-1 output")
        if not isinstance(positive_or_open.output.decision, IndeterminateDecision):
            return positive_or_open
        fraction = _catalog_evaluated_fraction(request, runtime, policy, evaluated)
        minimum = numeric_policy_by_ref(
            runtime.negative_route_policy.min_evaluated_fraction_policy_ref,
            runtime.numeric_policies,
            "MIN_CATALOG_EVALUATED_FRACTION",
            runtime.slice4_runtime.diagnostic_route_policy.dimensionless_unit_id,
            request.as_of_time,
            policy.slice4_policy.slice3_policy.slice2_policy.operational_mode,
        ).value
        if (
            all(item.assessment.status in {"ELIMINATED", "RULED_OUT"} for item in evaluated)
            and fraction >= minimum
        ):
            return _known_artifacts_excluded_result(
                request,
                runtime,
                policy,
                inputs,
                evaluated,
                ruling_refs,
                fraction,
                citations,
            )
        return positive_or_open
    except DiagnosticConfigurationError:
        return build_diagnostic_refusal(
            request,
            runtime.slice4_runtime,
            policy.slice4_policy,
            inputs.prepared,
            RefusalType.CONFIGURATION_INVALID,
            policy.slice4_policy.route_reasons.diagnostic_configuration_invalid,
            inputs.assessments,
            None,
            citations,
        )
    except DiagnosticIntegrityError:
        return build_diagnostic_refusal(
            request,
            runtime.slice4_runtime,
            policy.slice4_policy,
            inputs.prepared,
            RefusalType.INTEGRITY_FAILURE,
            policy.slice4_policy.route_reasons.diagnostic_integrity_failure,
            inputs.assessments,
            None,
            citations,
        )
    except (DiagnosticEngineError, ValidationError):
        return build_diagnostic_refusal(
            request,
            runtime.slice4_runtime,
            policy.slice4_policy,
            inputs.prepared,
            RefusalType.ENGINE_FAILURE,
            policy.slice4_policy.route_reasons.diagnostic_engine_failure,
            inputs.assessments,
            None,
            citations,
        )


def execute_honest_negative(
    request: Slice2Request,
    runtime: Slice5Runtime,
    policy: Slice5Policy,
    store: PostgresRunStore,
) -> Slice2ExecutionResult:
    result = build_honest_negative(request, runtime, policy)
    store.persist_snapshot_run(
        request.run_id,
        result.output,
        result.snapshot,
        result.audit_events,
        result.bound_versions,
        SLICE5_RUN_SCHEMA_VERSION,
    )
    return result


def _apply_hard_eliminations(
    request: Slice2Request,
    runtime: Slice5Runtime,
    policy: Slice5Policy,
    inputs: Slice4InputsReady,
) -> tuple[tuple[CandidateAssessment, ...], dict[GovernedRef, tuple[GovernedRef, ...]]]:
    pack = runtime.slice4_runtime.slice3_runtime.slice2_runtime.pack
    policy2 = policy.slice4_policy.slice3_policy.slice2_policy
    rules_by_candidate = {
        candidate_ref: tuple(
            item for item in runtime.hard_elimination_rules if item.candidate_ref == candidate_ref
        )
        for candidate_ref in pack.manifest.candidate_refs
    }
    assessments: list[CandidateAssessment] = []
    ruling_refs: dict[GovernedRef, tuple[GovernedRef, ...]] = {}
    for assessment in inputs.assessments:
        if assessment.status == "ELIMINATED":
            ruling_refs[assessment.candidate_ref] = sorted_unique_refs(
                (*assessment.evidence_refs, *assessment.rule_refs)
            )
            assessments.append(assessment)
            continue
        matched_evidence_refs: list[GovernedRef] = []
        matched_rule_refs: list[GovernedRef] = []
        for rule in rules_by_candidate[assessment.candidate_ref]:
            try:
                validate_predicate_configuration(
                    rule.predicate,
                    pack.field_registry,
                    pack.unit_registry,
                )
            except PredicateConfigurationError as exc:
                raise DiagnosticConfigurationError(str(exc)) from exc
            evaluation = evaluate_applicability(
                rule.predicate,
                rule.predicate_ref,
                inputs.prepared.context_values,
                pack.field_registry,
                pack.unit_registry,
                policy2.canonicalization_policy,
            )
            if evaluation.truth == ApplicabilityTruth.INVALID:
                raise DiagnosticConfigurationError("hard-elimination predicate evaluated INVALID")
            if evaluation.truth == ApplicabilityTruth.TRUE:
                matched_rule_refs.extend((rule.rule_ref, rule.predicate_ref))
                matched_evidence_refs.extend(
                    (
                        rule.rule_ref,
                        rule.predicate_ref,
                        *rule.evidence_refs,
                        *evaluation.evidence_refs,
                    )
                )
        if matched_rule_refs:
            evidence_refs = sorted_unique_refs(tuple(matched_evidence_refs))
            rule_refs = sorted_unique_refs(tuple(matched_rule_refs))
            assessment = updated_assessment(
                assessment,
                "ELIMINATED",
                "ELIMINATED",
                None,
                Decimal("0"),
                None,
                evidence_refs,
                rule_refs,
            )
            ruling_refs[assessment.candidate_ref] = sorted_unique_refs((*evidence_refs, *rule_refs))
        assessments.append(assessment)
    return tuple(assessments), ruling_refs


def _apply_rule_outs(
    request: Slice2Request,
    runtime: Slice5Runtime,
    policy: Slice5Policy,
    evaluated: tuple[EvaluatedCandidate, ...],
    ruling_refs: dict[GovernedRef, tuple[GovernedRef, ...]],
) -> tuple[tuple[EvaluatedCandidate, ...], dict[GovernedRef, tuple[GovernedRef, ...]]]:
    requirements = {item.candidate_ref: item for item in runtime.rule_out_requirements}
    changed: list[EvaluatedCandidate] = []
    for candidate in evaluated:
        if candidate.assessment.status != "CANDIDATE" or candidate.support is None:
            changed.append(candidate)
            continue
        requirement = requirements[candidate.assessment.candidate_ref]
        tau = numeric_policy_by_ref(
            requirement.tau_ruleout_policy_ref,
            runtime.numeric_policies,
            "TAU_RULEOUT",
            runtime.slice4_runtime.diagnostic_route_policy.dimensionless_unit_id,
            request.as_of_time,
            policy.slice4_policy.slice3_policy.slice2_policy.operational_mode,
        )
        evaluation_by_ref = {
            item.discriminator_ref: item for item in candidate.support.discriminator_evaluations
        }
        required = tuple(
            evaluation_by_ref.get(ref) for ref in requirement.required_discriminator_refs
        )
        evidence_satisfied = all(
            item is not None and item.outcome == "CONSISTENT_WITH_REAL" for item in required
        )
        if candidate.support.support_score > tau.value or not evidence_satisfied:
            changed.append(candidate)
            continue
        evidence_refs = sorted_unique_refs(
            (
                requirement.requirement_ref,
                requirement.tau_ruleout_policy_ref,
                *requirement.evidence_refs,
                *(ref for item in required if item is not None for ref in item.evidence_refs),
            )
        )
        assessment = updated_assessment(
            candidate.assessment,
            "EVALUABLE",
            "RULED_OUT",
            candidate.assessment.signature_match_score,
            candidate.assessment.signature_coverage,
            candidate.assessment.candidate_support_score,
            evidence_refs,
            (
                requirement.requirement_ref,
                requirement.tau_ruleout_policy_ref,
                *requirement.required_discriminator_refs,
            ),
        )
        ruling_refs[assessment.candidate_ref] = evidence_refs
        changed.append(replace(candidate, assessment=assessment))
    return tuple(changed), ruling_refs


def _catalog_evaluated_fraction(
    request: Slice2Request,
    runtime: Slice5Runtime,
    policy: Slice5Policy,
    evaluated: tuple[EvaluatedCandidate, ...],
) -> Decimal:
    policy4 = policy.slice4_policy
    runtime4 = runtime.slice4_runtime
    threshold = numeric_policy_by_ref(
        runtime4.diagnostic_route_policy.high_power_threshold_policy_ref,
        runtime4.numeric_policies,
        "HIGH_POWER_THRESHOLD",
        runtime4.diagnostic_route_policy.dimensionless_unit_id,
        request.as_of_time,
        policy4.slice3_policy.slice2_policy.operational_mode,
    ).value
    evaluation_by_ref = {
        item.discriminator_ref: item
        for candidate in evaluated
        if candidate.support is not None
        for item in candidate.support.discriminator_evaluations
    }
    applicable_refs = {
        item.assessment.candidate_ref
        for item in evaluated
        if item.assessment.applicability == ApplicabilityTruth.TRUE
    }
    high_power_refs: list[GovernedRef] = []
    for discriminator in runtime4.discriminators:
        if discriminator.candidate_ref not in applicable_refs:
            continue
        power = numeric_policy_by_ref(
            discriminator.discriminating_power_policy_ref,
            runtime4.numeric_policies,
            "DISCRIMINATING_POWER",
            runtime4.diagnostic_route_policy.dimensionless_unit_id,
            request.as_of_time,
            policy4.slice3_policy.slice2_policy.operational_mode,
        ).value
        if power >= threshold:
            high_power_refs.append(discriminator.discriminator_ref)
    if not high_power_refs:
        raise DiagnosticConfigurationError("published candidate set has no known denominator")
    answered = sum(
        evaluation_by_ref.get(ref) is not None and evaluation_by_ref[ref].outcome != "INCONCLUSIVE"
        for ref in high_power_refs
    )
    return canonical_ratio(
        Decimal(answered),
        Decimal(len(high_power_refs)),
        policy4.slice3_policy.slice2_policy.canonicalization_policy,
    )


def _known_artifacts_excluded_result(
    request: Slice2Request,
    runtime: Slice5Runtime,
    policy: Slice5Policy,
    inputs: Slice4InputsReady,
    evaluated: tuple[EvaluatedCandidate, ...],
    ruling_refs: dict[GovernedRef, tuple[GovernedRef, ...]],
    fraction: Decimal,
    citations: tuple[Citation, ...],
) -> Slice2ExecutionResult:
    artifacts: list[EvaluatedArtifact] = []
    requirements = {item.candidate_ref: item for item in runtime.rule_out_requirements}
    for item in evaluated:
        status = item.assessment.status
        if status not in {"ELIMINATED", "RULED_OUT"}:
            raise DiagnosticEngineError("negative verdict received a nonterminal candidate")
        terminal_status: Literal["ELIMINATED", "RULED_OUT"] = (
            "ELIMINATED" if status == "ELIMINATED" else "RULED_OUT"
        )
        refs = ruling_refs.get(item.assessment.candidate_ref, ())
        ruling_citations = _citations_for_refs(citations, refs)
        discriminator_refs = (
            requirements[item.assessment.candidate_ref].required_discriminator_refs
            if status == "RULED_OUT"
            else ()
        )
        artifacts.append(
            EvaluatedArtifact(
                failure_mode_ref=item.assessment.candidate_ref,
                terminal_status=terminal_status,
                discriminator_refs=discriminator_refs,
                ruling_citations=ruling_citations,
            )
        )
    gaps = tuple(
        KnownGap(
            category_id=item.category_id,
            why_unevaluated=item.why_unevaluated,
            what_would_enable=item.what_would_enable,
        )
        for item in runtime.known_gaps
    )
    decision = KnownArtifactsExcludedDecision.model_validate(
        {
            **investigation_header(
                request,
                runtime.slice4_runtime.slice3_runtime,
                policy.slice4_policy.slice3_policy,
                inputs.prepared.intake,
                inputs.prepared.calibration,
                inputs.prepared.msa,
            ),
            "verdict": "KNOWN_ARTIFACTS_EXCLUDED",
            "route_reason_id": policy.route_reasons.known_artifacts_excluded,
            "assessments": tuple(item.assessment for item in evaluated),
            "citations": citations,
            "required_human_action": policy.known_artifacts_excluded_action,
            "artifacts_evaluated": tuple(artifacts),
            "known_unevaluated_gaps": gaps,
            "catalog_boundary": policy.catalog_boundary,
            "evaluated_fraction_within_published_catalog": fraction,
        },
        context={
            "canonicalization_policy": policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
        },
    )
    return build_investigation_result(
        request,
        runtime.slice4_runtime.slice3_runtime,
        policy.slice4_policy.slice3_policy,
        inputs.prepared.intake,
        decision,
        policy.known_artifacts_excluded_event_type_id,
    )


def _negative_citations(runtime: Slice5Runtime) -> tuple[Citation, ...]:
    groups = (
        runtime.numeric_policies,
        runtime.hard_elimination_rules,
        runtime.rule_out_requirements,
        runtime.known_gaps,
        (runtime.negative_route_policy,),
    )
    return sorted_citations(
        tuple(
            Citation(
                record_type_id=item.record_type_id,
                record_ref=_record_ref(item),
                evidence_location=item.evidence_location,
            )
            for group in groups
            for item in group
        )
    )


def _record_ref(item: object) -> GovernedRef:
    for attribute in ("policy_ref", "rule_ref", "requirement_ref", "gap_ref"):
        value = getattr(item, attribute, None)
        if isinstance(value, GovernedRef):
            return value
    raise DiagnosticConfigurationError("citable negative record has no governed identity")


def _citations_for_refs(
    citations: tuple[Citation, ...],
    refs: tuple[GovernedRef, ...],
) -> tuple[Citation, ...]:
    keys = {(item.logical_id, item.version_id) for item in refs}
    selected = tuple(
        item
        for item in citations
        if (item.record_ref.logical_id, item.record_ref.version_id) in keys
    )
    if not selected:
        raise DiagnosticEngineError("terminal exclusion lost its governing citation")
    return sorted_citations(selected)


def _validate_gap_directives(runtime: Slice5Runtime, policy: Slice5Policy) -> None:
    registry = policy.slice4_policy.slice3_policy.slice2_policy.display_registry
    try:
        for gap in runtime.known_gaps:
            registry.validate_directive(gap.why_unevaluated)
            registry.validate_directive(gap.what_would_enable)
    except ValueError as exc:
        raise DiagnosticConfigurationError(str(exc)) from exc


def _validate_snapshot_bindings(runtime: Slice5Runtime, policy: Slice5Policy) -> None:
    expected = sorted_unique_refs((policy.route_policy_ref, *negative_bound_refs(runtime)))
    actual = {
        (item.logical_id, item.version_id): item
        for item in runtime.slice4_runtime.slice3_runtime.slice2_runtime.additional_bound_refs
    }
    if any(actual.get((item.logical_id, item.version_id)) != item for item in expected):
        raise DiagnosticConfigurationError(
            "Slice 5 snapshot bindings omit or conflict with negative records"
        )


def negative_bound_refs(runtime: Slice5Runtime) -> tuple[GovernedRef, ...]:
    return (
        runtime.negative_route_policy.policy_ref,
        runtime.negative_route_policy.min_evaluated_fraction_policy_ref,
        *runtime.negative_route_policy.evidence_refs,
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
            for item in runtime.hard_elimination_rules
            for ref in (
                item.rule_ref,
                item.candidate_ref,
                item.predicate_ref,
                *item.evidence_refs,
            )
        ),
        *(
            ref
            for item in runtime.rule_out_requirements
            for ref in (
                item.requirement_ref,
                item.candidate_ref,
                *item.required_discriminator_refs,
                item.tau_ruleout_policy_ref,
                *item.evidence_refs,
            )
        ),
        *(ref for item in runtime.known_gaps for ref in (item.gap_ref, *item.evidence_refs)),
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
