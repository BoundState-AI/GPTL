"""Governed synthetic Slice 3 calibration and MSA fixtures."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from gptl.core.directives import (
    DisplayDirective,
    DisplayTemplate,
    DisplayTemplateRegistry,
)
from gptl.core.ratification import (
    IntakeRecord,
    IntakeValue,
    RatificationEvent,
    intake_value_hash,
)
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import FieldId, TemplateId, TermId, UnitId
from gptl.mie.calibration import (
    CalibrationRecord,
    CalibrationValidityPolicy,
    MeasurementRunContext,
)
from gptl.mie.msa import (
    EvidenceScopeRecord,
    ImplementedMSAClassRegistry,
    MethodMeasurementContract,
    MSAGateReason,
    MSAStudy,
)
from gptl.mie.predicates import (
    EnumValue,
    EqualityComparison,
    FieldDefinition,
    FieldRegistry,
    NumericValue,
    OrderedComparison,
    Predicate,
    PresenceComparison,
    UnitDefinition,
    UnitRegistry,
)
from gptl.mie.records import AuthorityPackManifest, CandidatePack, EnginePolicyManifest
from gptl.mie.selection import SelectionBinding, SelectionGroupRecord
from gptl.mie.slice2_service import Slice2Policy, Slice2Request, Slice2Runtime
from gptl.mie.slice3_service import (
    Slice3Policy,
    Slice3RouteReasons,
    Slice3Runtime,
)
from gptl.slice2_fixture import (
    DIMENSION_LENGTH,
    FIELD_ENVIRONMENT,
    FIELD_MODE,
    FIELD_TEMPERATURE,
    ORIGINAL_AS_OF,
    UNIT_CELSIUS,
    UNIT_MM,
    candidate_pack,
    canonicalization_policy,
    governed_ref,
    ratified_runtime,
    slice2_policy,
    slice2_request,
)

FIELD_DEVIATION = FieldId("field.measured-deviation")
FIELD_MSA_CONDITION = FieldId("field.msa-condition")
UNIT_MICROMETER = UnitId("unit.micrometer")
MSA_CONDITION_REFERENCE = TermId("msa-condition.reference")
MSA_CLASS_QUANT_NONDESTRUCTIVE = TermId("msa-class.quant-nondestructive")
MSA_CLASS_DESTRUCTIVE = TermId("msa-class.destructive")
TEST_SCOPE_REF = governed_ref("evidence-scope.slice3-test")
OTHER_TEST_SCOPE_REF = governed_ref("evidence-scope.slice3-other-test")
BENCH_SCOPE_REF = governed_ref("evidence-scope.slice3-bench")
SLICE3_AS_OF = ORIGINAL_AS_OF
VALID_FROM = "2026-06-20T12:00:00.000Z"
VALID_UNTIL = "2026-06-22T12:00:00.000Z"
STALE_UNTIL = "2026-06-21T11:59:59.999Z"

CalibrationScenario = Literal["VALID", "STALE", "INVALID", "UNAVAILABLE"]
MSAScenario = Literal[
    "QUALIFIED",
    "MISSING",
    "UNQUALIFIED",
    "UNKNOWN",
    "NOT_APPLICABLE",
    "UNIMPLEMENTED",
    "SCOPE_MISMATCH",
    "NON_TEST_SCOPE",
    "INVALID_UNIT",
    "GROUPED_PRECEDENCE",
    "GROUPED_TIE",
]


def slice3_policy() -> Slice3Policy:
    base = slice2_policy()
    template_ids = (
        "action.collect-signature-evidence",
        "action.correct-calibration",
        "action.provide-calibration",
        "action.provide-qualified-msa",
        "action.review-within-variation",
    )
    additions = tuple(
        DisplayTemplate(
            template_id=TemplateId(template_id),
            template_ref=governed_ref(f"template.{template_id}"),
            parameter_specs=(),
        )
        for template_id in template_ids
    )
    registry = DisplayTemplateRegistry(
        registry_ref=governed_ref("display-registry.slice3"),
        templates=tuple(
            sorted((*base.display_registry.templates, *additions), key=lambda x: x.template_id)
        ),
    )
    slice2 = Slice2Policy.model_validate(
        {
            **base.model_dump(mode="python"),
            "engine_version": "slice3.v1",
            "display_registry": registry,
        }
    )
    return Slice3Policy(
        slice2_policy=slice2,
        route_policy_ref=governed_ref("route-policy.slice3"),
        route_reasons=Slice3RouteReasons(
            calibration_stale=TermId("route.calibration-stale"),
            calibration_invalid=TermId("route.calibration-invalid"),
            calibration_unavailable=TermId("route.calibration-unavailable"),
            msa_missing=TermId("route.msa-missing"),
            msa_unqualified=TermId("route.msa-unqualified"),
            msa_unknown_applicability=TermId("route.msa-applicability-unknown"),
            msa_not_applicable=TermId("route.msa-not-applicable"),
            msa_scope_mismatch=TermId("route.msa-scope-mismatch"),
            msa_unimplemented_class=TermId("route.msa-class-unimplemented"),
            msa_configuration_invalid=TermId("route.msa-configuration-invalid"),
            within_variation=TermId("route.within-measurement-variation"),
            outside_variation=TermId("route.outside-measurement-variation"),
            candidate_configuration_invalid=TermId("route.candidate-configuration-invalid"),
            candidate_missing_context=TermId("route.candidate-context-missing"),
        ),
        msa_uncharacterized_precedence=(
            MSAGateReason.UNKNOWN_APPLICABILITY,
            MSAGateReason.SCOPE_MISMATCH,
            MSAGateReason.UNQUALIFIED_STUDY,
            MSAGateReason.NOT_APPLICABLE,
        ),
        calibration_invalid_action=_directive("action.correct-calibration"),
        calibration_unavailable_action=_directive("action.provide-calibration"),
        msa_uncharacterized_action=_directive("action.provide-qualified-msa"),
        within_variation_action=_directive("action.review-within-variation"),
        indeterminate_action=_directive("action.collect-signature-evidence"),
        within_variation_event_type_id=TermId("audit.within-measurement-variation"),
        indeterminate_event_type_id=TermId("audit.indeterminate-no-signature"),
    )


def slice3_request(suffix: str) -> Slice2Request:
    request = slice2_request(f"slice3-{suffix}", SLICE3_AS_OF)
    return request.model_copy(
        update={
            "requested_pack_version_id": slice3_candidate_pack(
                TEST_SCOPE_REF
            ).manifest.pack_ref.version_id
        }
    )


def slice3_runtime(
    calibration_scenario: CalibrationScenario,
    msa_scenario: MSAScenario,
    deviation: Decimal,
    ratified: bool,
) -> Slice3Runtime:
    policy = slice3_policy()
    run_scope_ref = BENCH_SCOPE_REF if msa_scenario == "NON_TEST_SCOPE" else TEST_SCOPE_REF
    pack = slice3_candidate_pack(run_scope_ref)
    intake, active_event = _slice3_intake(pack, deviation)
    calibration = _calibration(calibration_scenario)
    calibration_policy = CalibrationValidityPolicy(
        policy_ref=governed_ref("calibration-policy.slice3"),
        interval_rule="VALID_FROM_INCLUSIVE_VALID_UNTIL_INCLUSIVE",
        before_valid_from_result="INVALID",
        after_valid_until_result="STALE",
    )
    run_context = MeasurementRunContext(
        run_context_ref=governed_ref("run-context.slice3"),
        instrument_ref=calibration.instrument_ref,
        calibration_ref=calibration.calibration_ref,
        evidence_scope_ref=run_scope_ref,
        evidence_refs=(governed_ref("evidence.run-context.slice3"),),
    )
    scopes = tuple(
        sorted(
            (
                EvidenceScopeRecord(scope_ref=BENCH_SCOPE_REF, scope_kind="BENCH"),
                EvidenceScopeRecord(scope_ref=OTHER_TEST_SCOPE_REF, scope_kind="TEST_FIXTURE"),
                EvidenceScopeRecord(scope_ref=TEST_SCOPE_REF, scope_kind="TEST_FIXTURE"),
            ),
            key=lambda item: (item.scope_ref.logical_id, item.scope_ref.version_id),
        )
    )
    studies, groups, method_class = _msa_records(pack, msa_scenario)
    registry = ImplementedMSAClassRegistry(
        registry_ref=governed_ref("msa-class-registry.slice3"),
        engine_id=policy.slice2_policy.engine_id,
        engine_version=policy.slice2_policy.engine_version,
        implemented_class_ids=(MSA_CLASS_QUANT_NONDESTRUCTIVE,),
    )
    measurement_contract = MethodMeasurementContract(
        contract_ref=governed_ref("measurement-contract.slice3"),
        method_ref=pack.manifest.method_ref,
        msa_class_id=method_class,
        deviation_field_id=FIELD_DEVIATION,
        evidence_refs=(governed_ref("evidence.measurement-contract.slice3"),),
    )
    open_discriminators = (
        governed_ref("discriminator.slice3.primary"),
        governed_ref("discriminator.slice3.secondary"),
    )
    additional_refs = sorted_unique_refs(
        (
            governed_ref("actor.reference-operator"),
            run_context.run_context_ref,
            run_context.instrument_ref,
            *run_context.evidence_refs,
            calibration.calibration_ref,
            calibration.instrument_ref,
            *calibration.evidence_refs,
            calibration_policy.policy_ref,
            registry.registry_ref,
            measurement_contract.contract_ref,
            *measurement_contract.evidence_refs,
            *(item.scope_ref for item in scopes),
            *(ref for group in groups for ref in (group.group_ref, *group.evidence_refs)),
            *(
                ref
                for study in studies
                for ref in (
                    study.study_ref,
                    study.predicate_ref,
                    study.qualification_scope_ref,
                    *study.capability_evidence_refs,
                )
            ),
            *open_discriminators,
            policy.route_policy_ref,
        )
    )
    slice2_runtime = Slice2Runtime(
        pack=pack,
        intake=intake,
        ratification_events=(active_event,) if ratified else (),
        additional_bound_refs=additional_refs,
    )
    return Slice3Runtime(
        slice2_runtime=slice2_runtime,
        run_context=run_context,
        calibration=calibration,
        calibration_policy=calibration_policy,
        implemented_msa_classes=registry,
        evidence_scopes=scopes,
        msa_studies=studies,
        msa_selection_groups=groups,
        measurement_contract=measurement_contract,
        open_discriminator_refs=open_discriminators,
    )


def slice3_candidate_pack(evidence_scope_ref: GovernedRef) -> CandidatePack:
    base = candidate_pack()
    field_registry = FieldRegistry(
        registry_ref=governed_ref("field-registry.slice3"),
        fields=tuple(
            sorted(
                (
                    *base.field_registry.fields,
                    FieldDefinition(
                        field_id=FIELD_DEVIATION,
                        value_kind="NUMERIC",
                        canonical_unit_id=UNIT_MM,
                        allowed_terms=(),
                    ),
                    FieldDefinition(
                        field_id=FIELD_MSA_CONDITION,
                        value_kind="ENUM",
                        canonical_unit_id=None,
                        allowed_terms=(MSA_CONDITION_REFERENCE,),
                    ),
                ),
                key=lambda item: item.field_id,
            )
        ),
    )
    policy_ref = governed_ref("engine-policy.slice3")
    unit_registry = UnitRegistry(
        registry_ref=governed_ref("unit-registry.slice3"),
        units=tuple(
            sorted(
                (
                    *base.unit_registry.units,
                    UnitDefinition(
                        unit_id=UNIT_MICROMETER,
                        dimension_id=DIMENSION_LENGTH,
                        scale_to_base=Decimal("0.001"),
                        offset_to_base=Decimal("0"),
                    ),
                ),
                key=lambda item: item.unit_id,
            )
        ),
    )
    engine_policy = EnginePolicyManifest(
        policy_ref=policy_ref,
        applicability_algorithm_ref=base.engine_policy.applicability_algorithm_ref,
        canonicalization_policy_ref=base.engine_policy.canonicalization_policy_ref,
        serialization_policy_ref=base.engine_policy.serialization_policy_ref,
        lexical_policy_ref=base.engine_policy.lexical_policy_ref,
        field_registry_ref=field_registry.registry_ref,
        unit_registry_ref=unit_registry.registry_ref,
        required_intake_field_ids=tuple(
            sorted(
                (
                    FIELD_DEVIATION,
                    FIELD_ENVIRONMENT,
                    FIELD_MODE,
                    FIELD_TEMPERATURE,
                )
            )
        ),
    )
    manifest = AuthorityPackManifest(
        pack_ref=governed_ref("pack.slice3-reference"),
        computation_type=base.manifest.computation_type,
        lifecycle=base.manifest.lifecycle,
        fixture_class=base.manifest.fixture_class,
        method_ref=base.manifest.method_ref,
        engine_policy_ref=policy_ref,
        evidence_scope_ref=evidence_scope_ref,
        candidate_refs=base.manifest.candidate_refs,
        selection_group_refs=base.manifest.selection_group_refs,
    )
    return CandidatePack(
        manifest=manifest,
        engine_policy=engine_policy,
        field_registry=field_registry,
        unit_registry=unit_registry,
        candidates=base.candidates,
        selection_groups=base.selection_groups,
    )


def _slice3_intake(
    pack: CandidatePack,
    deviation: Decimal,
) -> tuple[IntakeRecord, RatificationEvent]:
    base = ratified_runtime(include_environment=True)
    mode_event_ref = governed_ref("ratification.mode.slice3")
    mode_event = base.ratification_events[0].model_copy(
        update={
            "event_ref": mode_event_ref,
            "governing_pack_ref": pack.manifest.pack_ref,
        }
    )
    values = [
        (
            item.model_copy(update={"ratification_event_ref": mode_event_ref})
            if item.field_id == FIELD_MODE
            else item
        )
        for item in base.intake.values
        if item.field_id in {FIELD_ENVIRONMENT, FIELD_MODE, FIELD_TEMPERATURE}
    ]
    deviation_value = NumericValue(kind="NUMERIC", value=deviation, unit_id=UNIT_MM)
    values.append(
        IntakeValue(
            value_id="value.measured-deviation",
            field_id=FIELD_DEVIATION,
            value=deviation_value,
            value_hash=intake_value_hash(
                FIELD_DEVIATION,
                deviation_value,
                canonicalization_policy(),
            ),
            source_kind="INSTRUMENT_EMITTED",
            source_ref=governed_ref("source.instrument-deviation"),
            ratification_event_ref=None,
        )
    )
    values.sort(key=lambda item: (item.field_id, item.value_id))
    return (
        IntakeRecord(
            intake_ref=governed_ref("intake.slice3-reference"),
            values=tuple(values),
        ),
        mode_event,
    )


def _calibration(scenario: CalibrationScenario) -> CalibrationRecord:
    if scenario == "VALID":
        status = "CALIBRATED"
        valid_from = VALID_FROM
        valid_until = VALID_UNTIL
    elif scenario == "STALE":
        status = "CALIBRATED"
        valid_from = VALID_FROM
        valid_until = STALE_UNTIL
    else:
        status = scenario
        valid_from = None
        valid_until = None
    return CalibrationRecord.model_validate(
        {
            "calibration_ref": governed_ref(f"calibration.slice3-{scenario.lower()}"),
            "record_type_id": TermId("record.calibration"),
            "evidence_location": "fixture:calibration",
            "instrument_ref": governed_ref("instrument.slice3-reference"),
            "status": status,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "evidence_refs": (governed_ref(f"evidence.calibration-{scenario.lower()}"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _msa_records(
    pack: CandidatePack,
    scenario: MSAScenario,
) -> tuple[tuple[MSAStudy, ...], tuple[SelectionGroupRecord, ...], TermId]:
    if scenario == "MISSING":
        return (), (), MSA_CLASS_QUANT_NONDESTRUCTIVE
    method_class = (
        MSA_CLASS_DESTRUCTIVE if scenario == "UNIMPLEMENTED" else MSA_CLASS_QUANT_NONDESTRUCTIVE
    )
    predicate = _applicable_predicate()
    if scenario == "UNKNOWN":
        predicate = Predicate(
            kind="comparison",
            comparison=PresenceComparison(op="present", field_id=FIELD_MSA_CONDITION),
        )
    elif scenario == "NOT_APPLICABLE":
        predicate = Predicate(
            kind="comparison",
            comparison=EqualityComparison(
                op="eq",
                field_id=FIELD_MODE,
                operand=EnumValue(kind="ENUM", value=TermId("mode.test")),
            ),
        )
    elif scenario == "INVALID_UNIT":
        predicate = Predicate(
            kind="comparison",
            comparison=OrderedComparison(
                op="gt",
                field_id=FIELD_DEVIATION,
                operand=NumericValue(
                    kind="NUMERIC",
                    value=Decimal("0"),
                    unit_id=UNIT_CELSIUS,
                ),
            ),
        )
    qualification_state = "UNQUALIFIED" if scenario == "UNQUALIFIED" else "QUALIFIED"
    qualification_scope = OTHER_TEST_SCOPE_REF if scenario == "SCOPE_MISMATCH" else TEST_SCOPE_REF
    group: SelectionGroupRecord | None = None
    bindings: tuple[SelectionBinding | None, ...] = (None,)
    uncertainties: tuple[Decimal, ...] = (Decimal("10.0000"),)
    if scenario in {"GROUPED_PRECEDENCE", "GROUPED_TIE"}:
        group = SelectionGroupRecord(
            group_ref=governed_ref("selection-group.msa-alternatives"),
            rationale=_directive("rationale.grouped-alternatives"),
            evidence_refs=(governed_ref("evidence.msa-selection-rationale"),),
        )
        second_rank = Decimal("1") if scenario == "GROUPED_TIE" else Decimal("2")
        bindings = (
            SelectionBinding(
                selection_group_ref=group.group_ref,
                precedence_rank=Decimal("1"),
            ),
            SelectionBinding(
                selection_group_ref=group.group_ref,
                precedence_rank=second_rank,
            ),
        )
        uncertainties = (Decimal("20.0000"), Decimal("5.0000"))
    studies = tuple(
        _msa_study(
            pack,
            logical_suffix=f"{scenario.lower()}-{index}",
            method_class=method_class,
            predicate=predicate,
            uncertainty=uncertainty,
            qualification_state=qualification_state,
            qualification_scope=qualification_scope,
            binding=binding,
        )
        for index, (binding, uncertainty) in enumerate(
            zip(bindings, uncertainties, strict=True),
            start=1,
        )
    )
    return studies, (group,) if group is not None else (), method_class


def _msa_study(
    pack: CandidatePack,
    logical_suffix: str,
    method_class: TermId,
    predicate: Predicate,
    uncertainty: Decimal,
    qualification_state: str,
    qualification_scope: GovernedRef,
    binding: SelectionBinding | None,
) -> MSAStudy:
    return MSAStudy.model_validate(
        {
            "study_ref": governed_ref(f"msa-study.{logical_suffix}"),
            "study_record_type_id": TermId("record.msa-study"),
            "study_evidence_location": "fixture:msa-study",
            "method_ref": pack.manifest.method_ref,
            "msa_class_id": method_class,
            "measurand_field_id": FIELD_DEVIATION,
            "overlap_scope_id": TermId("msa-overlap.reference-method-deviation"),
            "predicate_ref": governed_ref(f"predicate.msa-study.{logical_suffix}"),
            "predicate_record_type_id": TermId("record.applicability-predicate"),
            "predicate_evidence_location": "fixture:msa-predicate",
            "applicability_predicate": predicate,
            "selection_binding": binding,
            "measured_uncertainty": NumericValue(
                kind="NUMERIC",
                value=uncertainty,
                unit_id=UNIT_MICROMETER,
            ),
            "qualification_state": qualification_state,
            "qualification_scope_ref": qualification_scope,
            "fixture_class": "REFERENCE",
            "effective_at": VALID_FROM,
            "expires_at": VALID_UNTIL,
            "capability_evidence_refs": (
                governed_ref(f"evidence.msa-capability.{logical_suffix}"),
            ),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _applicable_predicate() -> Predicate:
    return Predicate(
        kind="comparison",
        comparison=PresenceComparison(op="present", field_id=FIELD_DEVIATION),
    )


def _directive(template_id: str) -> DisplayDirective:
    return DisplayDirective(template_id=TemplateId(template_id), params=())
