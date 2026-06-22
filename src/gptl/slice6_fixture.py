"""Governed synthetic Slice 6 advisory fixtures."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from gptl.core.directives import DisplayDirective, DisplayTemplate, DisplayTemplateRegistry
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import EvidenceLocator, FieldId, TemplateId, TermId
from gptl.mie.advisory import (
    RETRIEVAL_LANE_ORDER,
    AdvisoryCatalog,
    AdvisoryQuery,
    AdvisoryRouteRule,
    LexicalResolverPolicy,
    MethodAdvisoryRecord,
    RetrievalWeight,
    RouteTrigger,
)
from gptl.mie.calibration import CalibrationRecord
from gptl.mie.slice2_service import Slice2Policy, Slice2Request
from gptl.mie.slice3_service import Slice3Policy
from gptl.mie.slice4_service import Slice4Policy
from gptl.mie.slice5_service import Slice5Policy, Slice5Runtime
from gptl.mie.slice6_service import (
    Slice6Policy,
    Slice6Runtime,
    advisory_bound_refs,
)
from gptl.slice2_fixture import FIELD_MODE, canonicalization_policy, governed_ref
from gptl.slice4_fixture import AS_OF, FIELD_PEAK_SHAPE, FIELD_REFERENCE_RESCAN
from gptl.slice5_fixture import slice5_policy, slice5_runtime

METHOD_PRIMARY_REF = governed_ref("method.eds-reference")
METHOD_SECONDARY_REF = governed_ref("method.eds-secondary")
SECONDARY_FAILURE_REF = governed_ref("failure.secondary-spectrum")
TERM_SPECTROSCOPY = TermId("method-family.spectroscopy")
INSTRUMENT_EDS = TermId("instrument-type.eds")
FAILURE_CLASS_SPECTRAL = TermId("failure-class.spectral-interference")
MEASUREMENT_MSA = TermId("measurement.msa-characterization")
RECORD_CALIBRATION = TermId("record.calibration")
RECORD_MSA = TermId("record.msa-study")

AdvisoryScenario = Literal[
    "UNRATIFIED_INTAKE",
    "AMBIGUOUS_METHOD",
    "UNKNOWN_METHOD",
    "MISSING_MSA",
    "UNIMPLEMENTED_MSA",
    "STALE_CALIBRATION",
    "UNAVAILABLE_CALIBRATION",
    "UNKNOWN_APPLICABILITY",
]


def slice6_policy() -> Slice6Policy:
    base = slice5_policy()
    additions = tuple(
        DisplayTemplate(
            template_id=TemplateId(template_id),
            template_ref=governed_ref(f"template.{template_id}"),
            parameter_specs=(),
        )
        for template_id in (
            "action.complete-applicability-context",
            "action.register-method",
            "action.resolve-method-alias",
        )
    )
    registry = DisplayTemplateRegistry(
        registry_ref=governed_ref("display-registry.slice6"),
        templates=tuple(
            sorted(
                (
                    *base.slice4_policy.slice3_policy.slice2_policy.display_registry.templates,
                    *additions,
                ),
                key=lambda item: item.template_id,
            )
        ),
    )
    slice2 = Slice2Policy.model_validate(
        {
            **base.slice4_policy.slice3_policy.slice2_policy.model_dump(mode="python"),
            "engine_version": "slice6.v1",
            "display_registry": registry,
        }
    )
    slice3 = Slice3Policy.model_validate(
        {
            **base.slice4_policy.slice3_policy.model_dump(mode="python"),
            "slice2_policy": slice2,
        }
    )
    slice4 = Slice4Policy.model_validate(
        {
            **base.slice4_policy.model_dump(mode="python"),
            "slice3_policy": slice3,
        }
    )
    slice5 = Slice5Policy.model_validate(
        {
            **base.model_dump(mode="python"),
            "slice4_policy": slice4,
        }
    )
    return Slice6Policy(
        slice5_policy=slice5,
        route_policy_ref=governed_ref("route-policy.slice6"),
        advisory_event_type_id=TermId("audit.tier2-advisory"),
    )


def slice6_request(suffix: str) -> Slice2Request:
    pack_ref = slice5_runtime(
        "COMPLETE"
    ).slice4_runtime.slice3_runtime.slice2_runtime.pack.manifest.pack_ref
    return Slice2Request.model_validate(
        {
            "run_id": f"run.slice6.{suffix}",
            "decision_id": f"decision.slice6.{suffix}",
            "case_id": f"case.slice6.{suffix}",
            "audit_event_id": f"audit.slice6.{suffix}.0",
            "snapshot_id": f"snapshot.slice6.{suffix}",
            "requested_pack_version_id": pack_ref.version_id,
            "as_of_time": AS_OF,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def slice6_query(scenario: AdvisoryScenario) -> AdvisoryQuery:
    method_text = {
        "AMBIGUOUS_METHOD": "eds",
        "UNKNOWN_METHOD": "raman spectroscopy",
    }.get(scenario, METHOD_PRIMARY_REF.logical_id)
    return AdvisoryQuery(
        query_ref=governed_ref(f"advisory-query.{scenario.lower()}"),
        record_type_id=TermId("record.advisory-query"),
        evidence_location=EvidenceLocator("fixture:advisory-query"),
        method_text=method_text,
        controlled_term_ids=(),
        observable_ids=(),
        instrument_type_ids=(),
        failure_class_ids=(),
        evidence_refs=(governed_ref(f"evidence.advisory-query.{scenario.lower()}"),),
    )


def slice6_runtime(scenario: AdvisoryScenario) -> Slice6Runtime:
    policy = slice6_policy()
    runtime5 = (
        slice5_runtime("UNKNOWN_APPLICABILITY")
        if scenario == "UNKNOWN_APPLICABILITY"
        else slice5_runtime("COMPLETE")
    )
    runtime5 = _slice6_engine_runtime(runtime5)
    if scenario == "UNRATIFIED_INTAKE":
        runtime5 = _unratified_runtime(runtime5)
    elif scenario == "MISSING_MSA":
        runtime5 = _update_slice3(runtime5, msa_studies=())
    elif scenario == "UNIMPLEMENTED_MSA":
        contract = runtime5.slice4_runtime.slice3_runtime.measurement_contract.model_copy(
            update={"msa_class_id": TermId("msa-class.unimplemented")}
        )
        runtime5 = _update_slice3(runtime5, measurement_contract=contract)
    elif scenario == "STALE_CALIBRATION":
        calibration = runtime5.slice4_runtime.slice3_runtime.calibration.model_copy(
            update={"valid_until": "2026-06-21T11:00:00.000Z"}
        )
        runtime5 = _update_slice3(runtime5, calibration=calibration)
    elif scenario == "UNAVAILABLE_CALIBRATION":
        current = runtime5.slice4_runtime.slice3_runtime.calibration
        calibration = CalibrationRecord.model_validate(
            {
                **current.model_dump(mode="python"),
                "status": "UNAVAILABLE",
                "valid_from": None,
                "valid_until": None,
            },
            context={"canonicalization_policy": canonicalization_policy()},
        )
        runtime5 = _update_slice3(runtime5, calibration=calibration)
    catalog = advisory_catalog(runtime5)
    resolver = lexical_resolver_policy(runtime5)
    rules = advisory_route_rules(policy)
    provisional = Slice6Runtime(
        slice5_runtime=runtime5,
        catalog=catalog,
        resolver_policy=resolver,
        route_rules=rules,
    )
    additional = sorted_unique_refs(
        (
            *runtime5.slice4_runtime.slice3_runtime.slice2_runtime.additional_bound_refs,
            policy.route_policy_ref,
            *advisory_bound_refs(provisional),
        )
    )
    slice2 = runtime5.slice4_runtime.slice3_runtime.slice2_runtime.model_copy(
        update={"additional_bound_refs": additional}
    )
    slice3 = runtime5.slice4_runtime.slice3_runtime.model_copy(update={"slice2_runtime": slice2})
    slice4 = runtime5.slice4_runtime.model_copy(update={"slice3_runtime": slice3})
    bound5 = runtime5.model_copy(update={"slice4_runtime": slice4})
    return Slice6Runtime.model_validate(
        {
            **provisional.model_dump(mode="python"),
            "slice5_runtime": bound5,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def lexical_resolver_policy(runtime: Slice5Runtime) -> LexicalResolverPolicy:
    runtime5 = runtime
    lexical_ref = (
        runtime5.slice4_runtime.slice3_runtime.slice2_runtime.pack.engine_policy.lexical_policy_ref
    )
    return LexicalResolverPolicy.model_validate(
        {
            "policy_ref": lexical_ref,
            "record_type_id": "record.lexical-resolver-policy",
            "evidence_location": "fixture:lexical-resolver-policy",
            "algorithm_id": "BUILD0_LEXICAL_V1",
            "normalization_id": "NFKC_CASEFOLD_ASCII_ALNUM_V1",
            "retrieval_order": RETRIEVAL_LANE_ORDER,
            "weights": (
                RetrievalWeight(lane="EXACT", value=Decimal("1.00")),
                RetrievalWeight(lane="CONTROLLED_TERM", value=Decimal("0.80")),
                RetrievalWeight(lane="RELATIONAL", value=Decimal("0.60")),
                RetrievalWeight(lane="LEXICAL", value=Decimal("0.20")),
            ),
            "minimum_score": Decimal("0.20"),
            "evidence_refs": (governed_ref("evidence.lexical-resolver-policy"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def advisory_catalog(runtime: Slice5Runtime) -> AdvisoryCatalog:
    runtime5 = runtime
    primary_candidates = (
        runtime5.slice4_runtime.slice3_runtime.slice2_runtime.pack.manifest.candidate_refs
    )
    methods = (
        _method_record(
            "eds-primary",
            METHOD_PRIMARY_REF,
            ("eds", "eds reference"),
            ("analysis", "dispersive", "eds", "energy", "reference", "spectral", "spectrum"),
            primary_candidates,
            (FIELD_PEAK_SHAPE, FIELD_REFERENCE_RESCAN),
        ),
        _method_record(
            "eds-secondary",
            METHOD_SECONDARY_REF,
            ("eds", "secondary eds"),
            ("analysis", "eds", "secondary", "spectral"),
            (SECONDARY_FAILURE_REF,),
            (FIELD_PEAK_SHAPE,),
        ),
    )
    return AdvisoryCatalog(
        catalog_ref=governed_ref("advisory-catalog.slice6"),
        record_type_id=TermId("record.advisory-catalog"),
        evidence_location=EvidenceLocator("fixture:advisory-catalog"),
        methods=methods,
        evidence_refs=(governed_ref("evidence.advisory-catalog"),),
    )


def advisory_route_rules(policy: Slice6Policy) -> tuple[AdvisoryRouteRule, ...]:
    policy3 = policy.slice5_policy.slice4_policy.slice3_policy
    policy2 = policy3.slice2_policy
    return (
        _route_rule(
            "00-method-ambiguous",
            "METHOD_AMBIGUOUS",
            None,
            "route.advisory-method-ambiguous",
            "gap.method-ambiguous",
            (),
            (),
            (),
            "action.resolve-method-alias",
        ),
        _route_rule(
            "01-method-unknown",
            "METHOD_UNKNOWN",
            None,
            "route.advisory-method-unknown",
            "gap.method-unknown",
            (),
            (),
            (),
            "action.register-method",
        ),
        _route_rule(
            "02-calibration-stale",
            "TIER1_ROUTE_REASON",
            policy3.route_reasons.calibration_stale,
            "route.advisory-calibration-stale",
            "gap.calibration-stale",
            (),
            (),
            (RECORD_CALIBRATION,),
            "action.correct-calibration",
        ),
        _route_rule(
            "03-calibration-unavailable",
            "TIER1_ROUTE_REASON",
            policy3.route_reasons.calibration_unavailable,
            "route.advisory-calibration-unavailable",
            "gap.calibration-unavailable",
            (),
            (),
            (RECORD_CALIBRATION,),
            "action.provide-calibration",
        ),
        _route_rule(
            "04-applicability-unknown",
            "TIER1_ROUTE_REASON",
            policy3.route_reasons.candidate_missing_context,
            "route.advisory-applicability-unknown",
            "gap.applicability-unknown",
            (FIELD_PEAK_SHAPE,),
            (),
            (),
            "action.complete-applicability-context",
        ),
        _route_rule(
            "05-intake-unratified",
            "TIER1_ROUTE_REASON",
            policy2.unratified_route_reason_id,
            "route.advisory-intake-unratified",
            "gap.intake-unratified",
            (FIELD_MODE,),
            (),
            (),
            policy2.unratified_next_step.template_id,
        ),
        _route_rule(
            "06-msa-unimplemented",
            "TIER1_ROUTE_REASON",
            policy3.route_reasons.msa_unimplemented_class,
            "route.advisory-msa-unimplemented",
            "gap.msa-unimplemented",
            (),
            (MEASUREMENT_MSA,),
            (RECORD_MSA,),
            "action.provide-qualified-msa",
        ),
        _route_rule(
            "07-msa-missing",
            "TIER1_ROUTE_REASON",
            policy3.route_reasons.msa_missing,
            "route.advisory-msa-missing",
            "gap.msa-missing",
            (),
            (MEASUREMENT_MSA,),
            (RECORD_MSA,),
            "action.provide-qualified-msa",
        ),
    )


def _route_rule(
    name: str,
    trigger: RouteTrigger,
    source: TermId | None,
    route: str,
    gap: str,
    fields: tuple[FieldId, ...],
    measurements: tuple[TermId, ...],
    records: tuple[TermId, ...],
    action: str,
) -> AdvisoryRouteRule:
    return AdvisoryRouteRule.model_validate(
        {
            "rule_ref": governed_ref(f"advisory-rule.{name}"),
            "record_type_id": "record.advisory-route-rule",
            "evidence_location": "fixture:advisory-route-rule",
            "trigger": trigger,
            "source_route_reason_id": source,
            "advisory_route_reason_id": route,
            "eligibility_gap_id": gap,
            "proposed_field_ids": fields,
            "required_measurement_ids": measurements,
            "required_record_type_ids": records,
            "next_step": _directive(action),
            "evidence_refs": (governed_ref(f"evidence.advisory-rule.{name}"),),
        }
    )


def _method_record(
    name: str,
    method_ref: GovernedRef,
    aliases: tuple[str, ...],
    lexical_tokens: tuple[str, ...],
    candidates: tuple[GovernedRef, ...],
    observables: tuple[FieldId, ...],
) -> MethodAdvisoryRecord:
    return MethodAdvisoryRecord(
        record_ref=governed_ref(f"advisory-method.{name}"),
        record_type_id=TermId("record.method-advisory"),
        evidence_location=EvidenceLocator("fixture:method-advisory"),
        method_ref=method_ref,
        aliases=aliases,
        controlled_term_ids=(TERM_SPECTROSCOPY,),
        observable_ids=tuple(sorted(observables)),
        instrument_type_ids=(INSTRUMENT_EDS,),
        failure_class_ids=(FAILURE_CLASS_SPECTRAL,),
        lexical_tokens=lexical_tokens,
        candidate_failure_mode_refs=candidates,
        evidence_refs=(governed_ref(f"evidence.method-advisory.{name}"),),
    )


def _slice6_engine_runtime(runtime: Slice5Runtime) -> Slice5Runtime:
    slice3 = runtime.slice4_runtime.slice3_runtime
    registry = slice3.implemented_msa_classes.model_copy(update={"engine_version": "slice6.v1"})
    return _update_slice3(runtime, implemented_msa_classes=registry)


def _unratified_runtime(runtime: Slice5Runtime) -> Slice5Runtime:
    slice2 = runtime.slice4_runtime.slice3_runtime.slice2_runtime
    values = tuple(
        item.model_copy(update={"source_kind": "HUMAN_ENTERED", "ratification_event_ref": None})
        if item.field_id == FIELD_MODE
        else item
        for item in slice2.intake.values
    )
    changed2 = slice2.model_copy(
        update={
            "intake": slice2.intake.model_copy(update={"values": values}),
            "ratification_events": (),
        }
    )
    slice3 = runtime.slice4_runtime.slice3_runtime.model_copy(update={"slice2_runtime": changed2})
    slice4 = runtime.slice4_runtime.model_copy(update={"slice3_runtime": slice3})
    return runtime.model_copy(update={"slice4_runtime": slice4})


def _update_slice3(runtime: Slice5Runtime, **updates: object) -> Slice5Runtime:
    slice3 = runtime.slice4_runtime.slice3_runtime.model_copy(update=updates)
    slice4 = runtime.slice4_runtime.model_copy(update={"slice3_runtime": slice3})
    return runtime.model_copy(update={"slice4_runtime": slice4})


def _directive(template_id: str) -> DisplayDirective:
    return DisplayDirective(template_id=TemplateId(template_id), params=())
