"""Deterministic Slice 6 Tier 2 advisory orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.persistence import SLICE6_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import TermId
from gptl.mie.advisory import (
    AdvisoryCatalog,
    AdvisoryQuery,
    AdvisoryRouteRule,
    LexicalResolverPolicy,
    MethodAdvisoryRecord,
    MethodResolutionResult,
    resolve_advisory_method,
)
from gptl.mie.candidates import CandidatePackConfigurationError, load_candidate_set
from gptl.mie.predicates import ApplicabilityEvaluation
from gptl.mie.schema import (
    AdvisoryDecision,
    Citation,
    RefusalDecision,
    Tier1Decision,
    Tier1Output,
    Tier2Output,
)
from gptl.mie.slice2_service import (
    Slice2ExecutionResult,
    Slice2Request,
    context_values_from_intake,
    finalize_snapshot_output,
)
from gptl.mie.slice3_service import sorted_citations
from gptl.mie.slice5_service import Slice5Policy, Slice5Runtime, build_honest_negative


class Slice6Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice5_policy: Slice5Policy
    route_policy_ref: GovernedRef
    advisory_event_type_id: TermId


class Slice6Runtime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slice5_runtime: Slice5Runtime
    catalog: AdvisoryCatalog
    resolver_policy: LexicalResolverPolicy
    route_rules: tuple[AdvisoryRouteRule, ...]

    @model_validator(mode="after")
    def validate_order_and_bindings(self) -> Slice6Runtime:
        _validate_model_ref_order(self.route_rules, lambda item: item.rule_ref, "advisory rules")
        trigger_keys = tuple(
            (item.trigger, item.source_route_reason_id or "") for item in self.route_rules
        )
        if trigger_keys != tuple(sorted(set(trigger_keys))):
            raise ValueError("advisory route triggers must be unique and sorted")
        lexical_ref = self.slice5_runtime.slice4_runtime.slice3_runtime.slice2_runtime.pack.engine_policy.lexical_policy_ref
        if self.resolver_policy.policy_ref != lexical_ref:
            raise ValueError("resolver policy must bind the pack lexical-policy reference")
        return self


class AdvisoryConfigurationError(ValueError):
    pass


def build_tier2_advisory(
    request: Slice2Request,
    query: AdvisoryQuery,
    runtime: Slice6Runtime,
    policy: Slice6Policy,
    accelerated_method_refs: tuple[GovernedRef, ...] | None = None,
) -> Slice2ExecutionResult:
    """Build a non-verdict advisory only from an ineligible Tier 1 attempt."""
    _validate_directives(runtime, policy)
    try:
        resolution = resolve_advisory_method(
            query,
            runtime.catalog,
            runtime.resolver_policy,
            accelerated_method_refs,
        )
    except ValueError as exc:
        raise AdvisoryConfigurationError(str(exc)) from exc
    if (
        resolution.resolution == "RESOLVED"
        and resolution.method_ref
        != runtime.slice5_runtime.slice4_runtime.slice3_runtime.slice2_runtime.pack.manifest.method_ref
    ):
        raise AdvisoryConfigurationError("resolved method has no bound Tier 1 runtime")
    effective_runtime = _runtime_with_query_binding(runtime, query)
    tier1_attempt = build_honest_negative(
        request,
        effective_runtime.slice5_runtime,
        policy.slice5_policy,
    )
    _validate_snapshot_bindings(tier1_attempt, effective_runtime, policy, query)
    source_body = _advisory_source_body(resolution, tier1_attempt)
    rule = _route_rule(resolution, source_body, effective_runtime.route_rules)
    applicability_evaluations = _advisory_applicability_evaluations(
        resolution,
        tier1_attempt,
        effective_runtime,
        policy,
    )
    method_records = _method_records_for_resolution(resolution, effective_runtime.catalog.methods)
    candidate_refs = sorted_unique_refs(
        tuple(ref for item in method_records for ref in item.candidate_failure_mode_refs)
    )
    open_discriminators = (
        sorted_unique_refs(
            tuple(
                item.discriminator_ref
                for item in effective_runtime.slice5_runtime.slice4_runtime.discriminators
                if item.candidate_ref in candidate_refs
            )
        )
        if resolution.resolution == "RESOLVED"
        else ()
    )
    source_missing_fields = (
        source_body.missing_field_ids if isinstance(source_body, RefusalDecision) else ()
    )
    proposed_fields = tuple(sorted(set((*rule.proposed_field_ids, *source_missing_fields))))
    citations = sorted_citations(
        (
            *(source_body.citations if resolution.resolution == "RESOLVED" else ()),
            *_advisory_citations(effective_runtime, query, method_records, rule),
        )
    )
    advisory = AdvisoryDecision.model_validate(
        {
            "decision_id": request.decision_id,
            "case_id": request.case_id,
            "tier": 2,
            "status": "ADVISORY_NO_VERDICT",
            "dispositional": False,
            "non_record_of_record": True,
            "operational_mode": policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.operational_mode,
            "engine_id": policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.engine_id,
            "engine_version": policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.engine_version,
            "context": source_body.context,
            "as_of_time": request.as_of_time,
            "method_resolution": resolution.resolution,
            "method_ref": resolution.method_ref,
            "route_reason_id": rule.advisory_route_reason_id,
            "proposed_field_ids": proposed_fields,
            "candidate_failure_mode_refs": candidate_refs,
            "applicability_evaluations": applicability_evaluations,
            "open_discriminator_refs": open_discriminators,
            "required_measurement_ids": rule.required_measurement_ids,
            "required_record_type_ids": rule.required_record_type_ids,
            "tier1_eligibility_gap_ids": (rule.eligibility_gap_id,),
            "next_steps": (rule.next_step,),
            "citations": citations,
            "audit_event_ids": (request.audit_event_id,),
        },
        context={
            "canonicalization_policy": policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
        },
    )
    canonicalization = (
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    )
    advisory_hash = canonical_sha256(advisory, canonicalization)
    output = Tier2Output(
        output_kind="TIER2_ADVISORY",
        advisory=advisory,
        advisory_hash=advisory_hash,
    )
    return finalize_snapshot_output(
        request,
        effective_runtime.slice5_runtime.slice4_runtime.slice3_runtime.slice2_runtime,
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy,
        tier1_attempt.snapshot,
        output,
        advisory_hash,
        policy.advisory_event_type_id,
    )


def execute_tier2_advisory(
    request: Slice2Request,
    query: AdvisoryQuery,
    runtime: Slice6Runtime,
    policy: Slice6Policy,
    store: PostgresRunStore,
    accelerated_method_refs: tuple[GovernedRef, ...] | None = None,
) -> Slice2ExecutionResult:
    """Build and atomically persist a snapshot-bound Tier 2 advisory run."""
    result = build_tier2_advisory(
        request,
        query,
        runtime,
        policy,
        accelerated_method_refs,
    )
    store.persist_snapshot_run(
        request.run_id,
        result.output,
        result.snapshot,
        result.audit_events,
        result.bound_versions,
        SLICE6_RUN_SCHEMA_VERSION,
    )
    return result


def _route_rule(
    resolution: MethodResolutionResult,
    source_body: Tier1Decision | AdvisoryDecision,
    rules: tuple[AdvisoryRouteRule, ...],
) -> AdvisoryRouteRule:
    if resolution.resolution == "UNKNOWN":
        matches = tuple(item for item in rules if item.trigger == "METHOD_UNKNOWN")
    elif resolution.resolution == "AMBIGUOUS":
        matches = tuple(item for item in rules if item.trigger == "METHOD_AMBIGUOUS")
    else:
        source_reason = source_body.route_reason_id
        if source_reason is None:
            raise AdvisoryConfigurationError("Tier 1 attempt has no advisory route reason")
        matches = tuple(
            item
            for item in rules
            if item.trigger == "TIER1_ROUTE_REASON" and item.source_route_reason_id == source_reason
        )
    if len(matches) != 1:
        raise AdvisoryConfigurationError("advisory route rule must resolve exactly once")
    return matches[0]


def _advisory_applicability_evaluations(
    resolution: MethodResolutionResult,
    tier1_attempt: Slice2ExecutionResult,
    runtime: Slice6Runtime,
    policy: Slice6Policy,
) -> tuple[ApplicabilityEvaluation, ...]:
    if resolution.resolution != "RESOLVED" or isinstance(tier1_attempt.output, Tier2Output):
        return ()
    pack = runtime.slice5_runtime.slice4_runtime.slice3_runtime.slice2_runtime.pack
    context_values = context_values_from_intake(
        runtime.slice5_runtime.slice4_runtime.slice3_runtime.slice2_runtime.intake.values
    )
    try:
        candidates = load_candidate_set(
            pack,
            context_values,
            policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy,
        )
    except CandidatePackConfigurationError as exc:
        raise AdvisoryConfigurationError(str(exc)) from exc
    return candidates.applicability_evaluations


def _method_records_for_resolution(
    resolution: MethodResolutionResult,
    methods: tuple[MethodAdvisoryRecord, ...],
) -> tuple[MethodAdvisoryRecord, ...]:
    by_ref = {item.method_ref: item for item in methods}
    try:
        return tuple(by_ref[ref] for ref in resolution.ordered_method_refs)
    except KeyError as exc:
        raise AdvisoryConfigurationError("resolver returned an ungoverned method") from exc


def _advisory_citations(
    runtime: Slice6Runtime,
    query: AdvisoryQuery,
    methods: tuple[MethodAdvisoryRecord, ...],
    rule: AdvisoryRouteRule,
) -> tuple[Citation, ...]:
    records: tuple[
        AdvisoryCatalog
        | LexicalResolverPolicy
        | AdvisoryQuery
        | AdvisoryRouteRule
        | MethodAdvisoryRecord,
        ...,
    ] = (
        runtime.catalog,
        runtime.resolver_policy,
        query,
        rule,
        *methods,
    )
    return sorted_citations(
        tuple(
            Citation(
                record_type_id=item.record_type_id,
                record_ref=_record_ref(item),
                evidence_location=item.evidence_location,
            )
            for item in records
        )
    )


def _record_ref(item: object) -> GovernedRef:
    for attribute in ("catalog_ref", "policy_ref", "query_ref", "rule_ref", "record_ref"):
        value = getattr(item, attribute, None)
        if isinstance(value, GovernedRef):
            return value
    raise AdvisoryConfigurationError("citable advisory record has no governed identity")


def _validate_directives(runtime: Slice6Runtime, policy: Slice6Policy) -> None:
    registry = policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.display_registry
    try:
        for rule in runtime.route_rules:
            registry.validate_directive(rule.next_step)
    except ValueError as exc:
        raise AdvisoryConfigurationError(str(exc)) from exc


def _validate_snapshot_bindings(
    tier1_attempt: Slice2ExecutionResult,
    runtime: Slice6Runtime,
    policy: Slice6Policy,
    query: AdvisoryQuery,
) -> None:
    bound = {
        (item.logical_id, item.version_id): item for item in tier1_attempt.snapshot.bound_versions
    }
    expected = sorted_unique_refs(
        (
            policy.route_policy_ref,
            *advisory_bound_refs(runtime),
            query.query_ref,
            *query.evidence_refs,
        )
    )
    if any(bound.get((item.logical_id, item.version_id)) != item for item in expected):
        raise AdvisoryConfigurationError(
            "Slice 6 snapshot bindings omit or conflict with advisory records"
        )


def _runtime_with_query_binding(
    runtime: Slice6Runtime,
    query: AdvisoryQuery,
) -> Slice6Runtime:
    slice5 = runtime.slice5_runtime
    slice4 = slice5.slice4_runtime
    slice3 = slice4.slice3_runtime
    slice2 = slice3.slice2_runtime
    additional = sorted_unique_refs(
        (*slice2.additional_bound_refs, query.query_ref, *query.evidence_refs)
    )
    bound2 = slice2.model_copy(update={"additional_bound_refs": additional})
    bound3 = slice3.model_copy(update={"slice2_runtime": bound2})
    bound4 = slice4.model_copy(update={"slice3_runtime": bound3})
    bound5 = slice5.model_copy(update={"slice4_runtime": bound4})
    return runtime.model_copy(update={"slice5_runtime": bound5})


def advisory_bound_refs(runtime: Slice6Runtime) -> tuple[GovernedRef, ...]:
    """Return every advisory record that must be present in the decision snapshot."""
    return (
        runtime.catalog.catalog_ref,
        *runtime.catalog.evidence_refs,
        runtime.resolver_policy.policy_ref,
        *runtime.resolver_policy.evidence_refs,
        *(
            ref
            for item in runtime.catalog.methods
            for ref in (
                item.record_ref,
                item.method_ref,
                *item.candidate_failure_mode_refs,
                *item.evidence_refs,
            )
        ),
        *(ref for item in runtime.route_rules for ref in (item.rule_ref, *item.evidence_refs)),
    )


def _advisory_source_body(
    resolution: MethodResolutionResult,
    tier1_attempt: Slice2ExecutionResult,
) -> Tier1Decision | AdvisoryDecision:
    if isinstance(tier1_attempt.output, Tier1Output):
        if resolution.resolution == "RESOLVED" and not isinstance(
            tier1_attempt.output.decision, RefusalDecision
        ):
            raise AdvisoryConfigurationError(
                "Tier 2 advisory cannot consume or replace a Tier 1 verdict"
            )
        return tier1_attempt.output.decision
    return tier1_attempt.output.advisory


_RecordT = TypeVar("_RecordT")


def _validate_model_ref_order(
    values: tuple[_RecordT, ...],
    ref_getter: Callable[[_RecordT], GovernedRef],
    label: str,
) -> None:
    refs = tuple(ref_getter(item) for item in values)
    if refs and sorted_unique_refs(refs) != refs:
        raise ValueError(f"{label} must be unique and sorted")
