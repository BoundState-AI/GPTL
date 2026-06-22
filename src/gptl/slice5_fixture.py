"""Governed synthetic Slice 5 bounded-catalog fixtures."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from gptl.core.directives import (
    DisplayDirective,
    DisplayParam,
    DisplayParameterSpec,
    DisplayTemplate,
    DisplayTemplateRegistry,
    GovernedDisplayValue,
    TermDisplayValue,
)
from gptl.core.ratification import IntakeRecord, IntakeValue, intake_value_hash
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import EvidenceLocator, FieldId, TemplateId, TermId
from gptl.mie.diagnostics import GovernedNumericPolicy
from gptl.mie.negative import (
    CatalogKnownGap,
    HardEliminationRule,
    NegativeRoutePolicy,
    RuleOutEvidenceRequirement,
)
from gptl.mie.predicates import (
    EnumValue,
    FieldRegistry,
    MembershipComparison,
    Predicate,
)
from gptl.mie.slice2_service import Slice2Policy, Slice2Request
from gptl.mie.slice3_service import Slice3Policy
from gptl.mie.slice4_service import Slice4Policy, Slice4Runtime
from gptl.mie.slice5_service import (
    Slice5Policy,
    Slice5RouteReasons,
    Slice5Runtime,
    negative_bound_refs,
)
from gptl.slice2_fixture import (
    ENVIRONMENT_HUMID,
    FIELD_ENVIRONMENT,
    canonicalization_policy,
    governed_ref,
)
from gptl.slice4_fixture import (
    AS_OF,
    FIELD_PEAK_SHAPE,
    FIELD_REFERENCE_RESCAN,
    PEAK_ISOLATED,
    PEAK_OVERLAP,
    RESCAN_REAL,
    UNIT_DIMENSIONLESS,
    slice4_candidate_pack,
    slice4_policy,
    slice4_runtime,
)

PEAK_AMBIGUOUS = TermId("eds-peak-shape.ambiguous")
KNOWN_GAP_CATEGORY = TermId("catalog-gap.unpublished-detector-effects")

NegativeScenario = Literal[
    "COMPLETE",
    "LOW_SUPPORT_WITH_INCONCLUSIVE",
    "OPEN_UNASSESSED",
    "UNKNOWN_APPLICABILITY",
    "UNKNOWN_DENOMINATOR",
    "FRACTION_BELOW_MINIMUM",
    "POSITIVE_PRECEDENCE",
]


def slice5_policy() -> Slice5Policy:
    base = slice4_policy()
    additions = (
        DisplayTemplate(
            template_id=TemplateId("action.enable-known-gap"),
            template_ref=governed_ref("template.action.enable-known-gap"),
            parameter_specs=(
                DisplayParameterSpec(
                    key_id=TermId("param.gap-ref"),
                    value_kind="GOVERNED_REF",
                    required=True,
                ),
            ),
        ),
        DisplayTemplate(
            template_id=TemplateId("action.review-bounded-negative"),
            template_ref=governed_ref("template.action.review-bounded-negative"),
            parameter_specs=(),
        ),
        DisplayTemplate(
            template_id=TemplateId("boundary.published-catalog"),
            template_ref=governed_ref("template.boundary.published-catalog"),
            parameter_specs=(
                DisplayParameterSpec(
                    key_id=TermId("param.pack-ref"),
                    value_kind="GOVERNED_REF",
                    required=True,
                ),
            ),
        ),
        DisplayTemplate(
            template_id=TemplateId("gap.why-unevaluated"),
            template_ref=governed_ref("template.gap.why-unevaluated"),
            parameter_specs=(
                DisplayParameterSpec(
                    key_id=TermId("param.category-id"),
                    value_kind="TERM_REF",
                    required=True,
                ),
            ),
        ),
    )
    registry = DisplayTemplateRegistry(
        registry_ref=governed_ref("display-registry.slice5"),
        templates=tuple(
            sorted(
                (*base.slice3_policy.slice2_policy.display_registry.templates, *additions),
                key=lambda item: item.template_id,
            )
        ),
    )
    slice2 = Slice2Policy.model_validate(
        {
            **base.slice3_policy.slice2_policy.model_dump(mode="python"),
            "engine_version": "slice5.v1",
            "display_registry": registry,
        }
    )
    slice3 = Slice3Policy.model_validate(
        {
            **base.slice3_policy.model_dump(mode="python"),
            "slice2_policy": slice2,
        }
    )
    slice4 = Slice4Policy.model_validate(
        {
            **base.model_dump(mode="python"),
            "slice3_policy": slice3,
        }
    )
    catalog_pack_ref = slice4_candidate_pack().manifest.pack_ref
    return Slice5Policy(
        slice4_policy=slice4,
        route_policy_ref=governed_ref("route-policy.slice5"),
        route_reasons=Slice5RouteReasons(
            known_artifacts_excluded=TermId("route.known-artifacts-excluded")
        ),
        known_artifacts_excluded_action=_directive("action.review-bounded-negative"),
        catalog_boundary=_directive(
            "boundary.published-catalog",
            (
                DisplayParam(
                    key_id=TermId("param.pack-ref"),
                    value=GovernedDisplayValue(kind="GOVERNED_REF", value=catalog_pack_ref),
                ),
            ),
        ),
        known_artifacts_excluded_event_type_id=TermId("audit.known-artifacts-excluded"),
    )


def slice5_request(suffix: str) -> Slice2Request:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    return Slice2Request.model_validate(
        {
            "run_id": f"run.slice5.{suffix}",
            "decision_id": f"decision.slice5.{suffix}",
            "case_id": f"case.slice5.{suffix}",
            "audit_event_id": f"audit.slice5.{suffix}.0",
            "snapshot_id": f"snapshot.slice5.{suffix}",
            "requested_pack_version_id": runtime.slice3_runtime.slice2_runtime.pack.manifest.pack_ref.version_id,
            "as_of_time": AS_OF,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def slice5_runtime(scenario: NegativeScenario) -> Slice5Runtime:
    policy = slice5_policy()
    runtime4 = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    slice3 = runtime4.slice3_runtime.model_copy(
        update={
            "implemented_msa_classes": runtime4.slice3_runtime.implemented_msa_classes.model_copy(
                update={"engine_version": "slice5.v1"}
            )
        }
    )
    runtime4 = runtime4.model_copy(update={"slice3_runtime": slice3})
    if scenario != "POSITIVE_PRECEDENCE":
        runtime4 = _negative_observations(runtime4, scenario)
    if scenario == "UNKNOWN_DENOMINATOR":
        runtime4 = runtime4.model_copy(
            update={
                "numeric_policies": tuple(
                    item.model_copy(update={"value": Decimal("0.90")})
                    if item.policy_kind == "HIGH_POWER_THRESHOLD"
                    else item
                    for item in runtime4.numeric_policies
                )
            }
        )
    numeric_policies = _negative_numeric_policies(
        runtime4.slice3_runtime.slice2_runtime.pack.manifest.pack_ref,
        Decimal("1.00") if scenario == "FRACTION_BELOW_MINIMUM" else Decimal("0.60"),
    )
    drift_ref, peak_ref = runtime4.slice3_runtime.slice2_runtime.pack.manifest.candidate_refs
    drift_discriminators = tuple(
        item.discriminator_ref
        for item in runtime4.discriminators
        if item.candidate_ref == drift_ref
    )
    peak_discriminators = tuple(
        item.discriminator_ref for item in runtime4.discriminators if item.candidate_ref == peak_ref
    )
    requirements = tuple(
        sorted(
            (
                _rule_out_requirement(drift_ref, drift_discriminators),
                _rule_out_requirement(peak_ref, peak_discriminators),
            ),
            key=lambda item: item.requirement_ref.logical_id,
        )
    )
    hard_rules = (
        HardEliminationRule(
            rule_ref=governed_ref("elimination-rule.detector-drift-humid"),
            record_type_id=TermId("record.hard-elimination-rule"),
            evidence_location=EvidenceLocator("fixture:hard-elimination-rule"),
            candidate_ref=drift_ref,
            predicate_ref=governed_ref("predicate.eliminate-detector-drift-humid"),
            predicate=Predicate(
                kind="comparison",
                comparison=MembershipComparison(
                    op="in",
                    field_id=FIELD_ENVIRONMENT,
                    allowed_terms=(ENVIRONMENT_HUMID,),
                ),
            ),
            evidence_refs=(governed_ref("evidence.eliminate-detector-drift-humid"),),
        ),
    )
    gap_ref = governed_ref("known-gap.unpublished-detector-effects")
    gaps = (
        CatalogKnownGap(
            gap_ref=gap_ref,
            record_type_id=TermId("record.catalog-known-gap"),
            evidence_location=EvidenceLocator("fixture:catalog-known-gap"),
            category_id=KNOWN_GAP_CATEGORY,
            why_unevaluated=_directive(
                "gap.why-unevaluated",
                (
                    DisplayParam(
                        key_id=TermId("param.category-id"),
                        value=TermDisplayValue(
                            kind="TERM_REF",
                            value=KNOWN_GAP_CATEGORY,
                        ),
                    ),
                ),
            ),
            what_would_enable=_directive(
                "action.enable-known-gap",
                (
                    DisplayParam(
                        key_id=TermId("param.gap-ref"),
                        value=GovernedDisplayValue(kind="GOVERNED_REF", value=gap_ref),
                    ),
                ),
            ),
            evidence_refs=(governed_ref("evidence.known-gap.detector-effects"),),
        ),
    )
    negative_route_policy = NegativeRoutePolicy(
        policy_ref=governed_ref("negative-route-policy.slice5"),
        record_type_id=TermId("record.negative-route-policy"),
        evidence_location=EvidenceLocator("fixture:negative-route-policy"),
        min_evaluated_fraction_policy_ref=governed_ref(
            "numeric-policy.min-catalog-evaluated-fraction"
        ),
        evidence_refs=(governed_ref("evidence.negative-route-policy"),),
    )
    provisional = Slice5Runtime(
        slice4_runtime=runtime4,
        negative_route_policy=negative_route_policy,
        numeric_policies=numeric_policies,
        hard_elimination_rules=hard_rules,
        rule_out_requirements=requirements,
        known_gaps=gaps,
    )
    additional = sorted_unique_refs(
        (
            *runtime4.slice3_runtime.slice2_runtime.additional_bound_refs,
            policy.route_policy_ref,
            *negative_bound_refs(provisional),
        )
    )
    slice2 = runtime4.slice3_runtime.slice2_runtime.model_copy(
        update={"additional_bound_refs": additional}
    )
    slice3 = runtime4.slice3_runtime.model_copy(update={"slice2_runtime": slice2})
    bound4 = runtime4.model_copy(update={"slice3_runtime": slice3})
    return Slice5Runtime.model_validate(
        {
            **provisional.model_dump(mode="python"),
            "slice4_runtime": bound4,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _negative_observations(
    runtime: Slice4Runtime,
    scenario: NegativeScenario,
) -> Slice4Runtime:
    runtime4 = runtime
    slice2 = runtime4.slice3_runtime.slice2_runtime
    retained = tuple(
        item
        for item in slice2.intake.values
        if item.field_id not in {FIELD_PEAK_SHAPE, FIELD_REFERENCE_RESCAN}
    )
    if scenario == "OPEN_UNASSESSED":
        values = retained
    elif scenario == "UNKNOWN_APPLICABILITY":
        values = (*retained, _instrument_value(FIELD_REFERENCE_RESCAN, RESCAN_REAL))
        candidates = tuple(
            item.model_copy(
                update={
                    "applicability_predicate": Predicate(
                        kind="comparison",
                        comparison=MembershipComparison(
                            op="in",
                            field_id=FIELD_PEAK_SHAPE,
                            allowed_terms=(PEAK_ISOLATED, PEAK_OVERLAP),
                        ),
                    )
                }
            )
            for item in slice2.pack.candidates
        )
        pack = slice2.pack.model_copy(update={"candidates": candidates})
        slice2 = slice2.model_copy(update={"pack": pack})
    else:
        peak = PEAK_AMBIGUOUS if scenario == "LOW_SUPPORT_WITH_INCONCLUSIVE" else PEAK_ISOLATED
        values = (
            *retained,
            _instrument_value(FIELD_PEAK_SHAPE, peak),
            _instrument_value(FIELD_REFERENCE_RESCAN, RESCAN_REAL),
        )
        if peak == PEAK_AMBIGUOUS:
            registry = slice2.pack.field_registry
            fields = tuple(
                item.model_copy(
                    update={"allowed_terms": tuple(sorted((*item.allowed_terms, PEAK_AMBIGUOUS)))}
                )
                if item.field_id == FIELD_PEAK_SHAPE
                else item
                for item in registry.fields
            )
            pack = slice2.pack.model_copy(
                update={
                    "field_registry": FieldRegistry(
                        registry_ref=registry.registry_ref,
                        fields=fields,
                    )
                }
            )
            slice2 = slice2.model_copy(update={"pack": pack})
    intake = IntakeRecord(
        intake_ref=governed_ref("intake.slice5-eds"),
        values=tuple(sorted(values, key=lambda item: (item.field_id, item.value_id))),
    )
    slice2 = slice2.model_copy(update={"intake": intake})
    slice3 = runtime4.slice3_runtime.model_copy(update={"slice2_runtime": slice2})
    return runtime4.model_copy(update={"slice3_runtime": slice3})


def _negative_numeric_policies(
    pack_ref: GovernedRef,
    minimum_fraction: Decimal,
) -> tuple[GovernedNumericPolicy, ...]:
    return tuple(
        sorted(
            (
                _numeric_policy(
                    "min-catalog-evaluated-fraction",
                    "MIN_CATALOG_EVALUATED_FRACTION",
                    minimum_fraction,
                    pack_ref,
                ),
                _numeric_policy(
                    "tau-ruleout",
                    "TAU_RULEOUT",
                    Decimal("0.10"),
                    pack_ref,
                ),
            ),
            key=lambda item: item.policy_ref.logical_id,
        )
    )


def _numeric_policy(
    name: str,
    kind: str,
    value: Decimal,
    pack_ref: GovernedRef,
) -> GovernedNumericPolicy:
    return GovernedNumericPolicy.model_validate(
        {
            "policy_ref": governed_ref(f"numeric-policy.{name}"),
            "record_type_id": "record.governed-numeric-policy",
            "evidence_location": "fixture:negative-numeric-policy",
            "policy_kind": kind,
            "value": value,
            "unit_id": UNIT_DIMENSIONLESS,
            "scope_ref": pack_ref,
            "derivation_ref": governed_ref(f"derivation.{name}"),
            "governing_source_refs": (governed_ref(f"source.numeric-policy.{name}"),),
            "owner_id": "actor.negative-policy-owner",
            "approver_id": "actor.negative-policy-approver",
            "qualification_state": "RESEARCH_ONLY",
            "validation_corpus_ref": governed_ref("validation-corpus.slice5-synthetic"),
            "validation_result": "PASS",
            "effective_at": "2026-06-20T00:00:00.000Z",
            "expires_at": "2026-06-22T23:59:59.999Z",
            "evidence_refs": (governed_ref(f"evidence.numeric-policy.{name}"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _rule_out_requirement(
    candidate_ref: GovernedRef,
    discriminator_refs: tuple[GovernedRef, ...],
) -> RuleOutEvidenceRequirement:
    name = candidate_ref.logical_id.removeprefix("failure.")
    return RuleOutEvidenceRequirement(
        requirement_ref=governed_ref(f"rule-out-requirement.{name}"),
        record_type_id=TermId("record.rule-out-evidence-requirement"),
        evidence_location=EvidenceLocator("fixture:rule-out-requirement"),
        candidate_ref=candidate_ref,
        required_discriminator_refs=discriminator_refs,
        aggregation="ALL_CONSISTENT_WITH_REAL",
        tau_ruleout_policy_ref=governed_ref("numeric-policy.tau-ruleout"),
        evidence_refs=(governed_ref(f"evidence.rule-out-requirement.{name}"),),
    )


def _instrument_value(field_id: FieldId, term_id: TermId) -> IntakeValue:
    value = EnumValue(kind="ENUM", value=term_id)
    suffix = field_id.removeprefix("field.")
    return IntakeValue(
        value_id=f"value.slice5.{suffix}",
        field_id=field_id,
        value=value,
        value_hash=intake_value_hash(field_id, value, canonicalization_policy()),
        source_kind="INSTRUMENT_EMITTED",
        source_ref=governed_ref(f"source.slice5.{suffix}"),
        ratification_event_ref=None,
    )


def _directive(
    template_id: str,
    params: tuple[DisplayParam, ...] = (),
) -> DisplayDirective:
    return DisplayDirective(template_id=TemplateId(template_id), params=params)
