"""Governed synthetic Slice 2 pack, policy, and intake fixtures."""

from __future__ import annotations

import hashlib
from decimal import Decimal

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
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    EvidenceLocator,
    FieldId,
    LogicalId,
    TemplateId,
    TermId,
    UnitId,
    VersionId,
)
from gptl.mie.predicates import (
    EnumValue,
    EqualityComparison,
    FieldDefinition,
    FieldRegistry,
    MembershipComparison,
    NumericValue,
    OrderedComparison,
    Predicate,
    RangeComparison,
    RangeOperand,
    UnitDefinition,
    UnitRegistry,
)
from gptl.mie.records import (
    AuthorityPackManifest,
    CandidatePack,
    EnginePolicyManifest,
    FailureModeRecord,
)
from gptl.mie.selection import SelectionBinding, SelectionGroupRecord
from gptl.mie.slice2_service import (
    Slice2Policy,
    Slice2Request,
    Slice2Runtime,
)

ORIGINAL_AS_OF = "2026-06-21T12:00:00.000Z"
REVOKED_AS_OF = "2026-06-22T12:00:00.000Z"
FIELD_ENVIRONMENT = FieldId("field.environment")
FIELD_MODE = FieldId("field.mode")
FIELD_TEMPERATURE = FieldId("field.temperature")
UNIT_CELSIUS = UnitId("unit.celsius")
UNIT_KELVIN = UnitId("unit.kelvin")
UNIT_MM = UnitId("unit.mm")
ENVIRONMENT_DRY = TermId("environment.dry")
ENVIRONMENT_HUMID = TermId("environment.humid")
MODE_PRODUCTION = TermId("mode.production")
MODE_TEST = TermId("mode.test")
DIMENSION_TEMPERATURE = TermId("dimension.temperature")
DIMENSION_LENGTH = TermId("dimension.length")


def canonicalization_policy() -> CanonicalizationPolicy:
    return CanonicalizationPolicy(
        policy_id="canonical-policy.slice2",
        policy_version="1",
        timestamp_fraction_digits=3,
        decimal_scale=4,
        decimal_rounding="ROUND_HALF_EVEN",
        decimal_max_integer_digits=18,
        decimal_overflow="REJECT",
    )


def governed_ref(logical_id: str, version: int = 1) -> GovernedRef:
    version_id = f"{logical_id}.v{version}"
    digest = hashlib.sha256(f"fixture:{version_id}".encode()).hexdigest()
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(version_id),
        version_number=version,
        content_hash=digest,
    )


def display_registry() -> DisplayTemplateRegistry:
    template_ids = (
        "action.correct-configuration",
        "action.correct-integrity-failure",
        "action.provide-missing-context",
        "action.ratify-input",
        "rationale.grouped-alternatives",
    )
    return DisplayTemplateRegistry(
        registry_ref=governed_ref("display-registry.slice2"),
        templates=tuple(
            DisplayTemplate(
                template_id=TemplateId(template_id),
                template_ref=governed_ref(f"template.{template_id}"),
                parameter_specs=(),
            )
            for template_id in template_ids
        ),
    )


def slice2_policy() -> Slice2Policy:
    registry = display_registry()
    return Slice2Policy(
        canonicalization_policy=canonicalization_policy(),
        operational_mode="RESEARCH_ONLY",
        engine_id="mie.diagnostic-engine",
        engine_version="slice2.v1",
        display_registry=registry,
        missing_evidence_action=_directive("action.provide-missing-context"),
        configuration_action=_directive("action.correct-configuration"),
        integrity_action=_directive("action.correct-integrity-failure"),
        unratified_next_step=_directive("action.ratify-input"),
        tier1_unratified_gap_id=TermId("gap.unratified-input"),
        unratified_route_reason_id=TermId("route.intake-unratified"),
        integrity_failure_route_reason_id=TermId("route.intake-integrity-failure"),
        configuration_invalid_route_reason_id=TermId("route.candidate-configuration-invalid"),
        missing_context_route_reason_id=TermId("route.candidate-context-missing"),
        snapshot_refusal_event_type_id=TermId("audit.snapshot-refusal"),
        advisory_event_type_id=TermId("audit.unratified-advisory"),
        required_measurement_ids=(),
        required_record_type_ids=(TermId("record.ratification-event"),),
    )


def candidate_pack() -> CandidatePack:
    method_ref = governed_ref("method.reference-optical")
    policy_ref = governed_ref("engine-policy.slice2")
    scope_ref = governed_ref("evidence-scope.test-fixture")
    fields = _field_registry()
    units = _unit_registry()
    group = SelectionGroupRecord(
        group_ref=governed_ref("selection-group.preparation-alternatives"),
        rationale=_directive("rationale.grouped-alternatives"),
        evidence_refs=(governed_ref("evidence.selection-rationale"),),
    )
    candidates = _candidate_records(method_ref, group.group_ref)
    manifest = AuthorityPackManifest(
        pack_ref=governed_ref("pack.slice2-reference"),
        computation_type="DIAGNOSTIC",
        lifecycle="PUBLISHED",
        fixture_class="REFERENCE",
        method_ref=method_ref,
        engine_policy_ref=policy_ref,
        evidence_scope_ref=scope_ref,
        candidate_refs=tuple(item.failure_mode_ref for item in candidates),
        selection_group_refs=(group.group_ref,),
    )
    engine_policy = EnginePolicyManifest(
        policy_ref=policy_ref,
        applicability_algorithm_ref=governed_ref("algorithm.applicability-kleene"),
        canonicalization_policy_ref=governed_ref("policy.canonicalization.slice2"),
        serialization_policy_ref=governed_ref("policy.serialization.rfc8785"),
        lexical_policy_ref=governed_ref("policy.lexical.none-slice2"),
        field_registry_ref=fields.registry_ref,
        unit_registry_ref=units.registry_ref,
        required_intake_field_ids=(
            FIELD_MODE,
            FIELD_TEMPERATURE,
        ),
    )
    return CandidatePack(
        manifest=manifest,
        engine_policy=engine_policy,
        field_registry=fields,
        unit_registry=units,
        candidates=candidates,
        selection_groups=(group,),
    )


def invalid_unit_pack() -> CandidatePack:
    pack = candidate_pack()
    target = pack.candidates[-1]
    invalid_predicate = Predicate(
        kind="comparison",
        comparison=EqualityComparison(
            op="eq",
            field_id=FIELD_TEMPERATURE,
            operand=NumericValue(
                kind="NUMERIC",
                value=Decimal("1"),
                unit_id=UNIT_MM,
            ),
        ),
    )
    replacement = FailureModeRecord.model_validate(
        {
            **target.model_dump(mode="python"),
            "applicability_predicate": invalid_predicate,
        }
    )
    candidates = (*pack.candidates[:-1], replacement)
    return CandidatePack(
        manifest=pack.manifest,
        engine_policy=pack.engine_policy,
        field_registry=pack.field_registry,
        unit_registry=pack.unit_registry,
        candidates=candidates,
        selection_groups=pack.selection_groups,
    )


def tied_selection_pack() -> CandidatePack:
    pack = candidate_pack()
    candidates = []
    for candidate in pack.candidates:
        if candidate.failure_mode_ref.logical_id == "failure.group-high":
            candidate = FailureModeRecord.model_validate(
                {
                    **candidate.model_dump(mode="python"),
                    "selection_binding": SelectionBinding(
                        selection_group_ref=pack.selection_groups[0].group_ref,
                        precedence_rank=Decimal("1"),
                    ),
                }
            )
        candidates.append(candidate)
    return CandidatePack(
        manifest=pack.manifest,
        engine_policy=pack.engine_policy,
        field_registry=pack.field_registry,
        unit_registry=pack.unit_registry,
        candidates=tuple(candidates),
        selection_groups=pack.selection_groups,
    )


def slice2_request(
    suffix: str = "unknown",
    as_of_time: str = ORIGINAL_AS_OF,
) -> Slice2Request:
    policy = canonicalization_policy()
    return Slice2Request.model_validate(
        {
            "run_id": f"run.slice2.{suffix}",
            "decision_id": f"decision.slice2.{suffix}",
            "case_id": f"case.slice2.{suffix}",
            "audit_event_id": f"audit.slice2.{suffix}.0",
            "snapshot_id": f"snapshot.slice2.{suffix}",
            "requested_pack_version_id": candidate_pack().manifest.pack_ref.version_id,
            "as_of_time": as_of_time,
        },
        context={"canonicalization_policy": policy},
    )


def ratified_runtime(
    include_environment: bool = False,
    pack: CandidatePack | None = None,
) -> Slice2Runtime:
    selected_pack = pack or candidate_pack()
    intake, event = _intake(include_environment=include_environment)
    return Slice2Runtime(
        pack=selected_pack,
        intake=intake,
        ratification_events=(event,),
        additional_bound_refs=(governed_ref("actor.reference-operator"),),
    )


def unratified_runtime() -> Slice2Runtime:
    intake, _ = _intake(include_environment=False)
    return Slice2Runtime(
        pack=candidate_pack(),
        intake=intake,
        ratification_events=(),
        additional_bound_refs=(governed_ref("actor.reference-operator"),),
    )


def revoked_runtime() -> Slice2Runtime:
    intake, active = _intake(include_environment=False)
    revocation = RatificationEvent.model_validate(
        {
            "event_ref": governed_ref("ratification.mode", version=2),
            "value_id": active.value_id,
            "field_id": active.field_id,
            "value_hash": active.value_hash,
            "source_ref": active.source_ref,
            "actor_id": "actor.reference-operator",
            "governing_pack_ref": active.governing_pack_ref,
            "effective_at": REVOKED_AS_OF,
            "recorded_at": REVOKED_AS_OF,
            "state": "REVOKED",
            "supersedes_version_id": active.event_ref.version_id,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return Slice2Runtime(
        pack=candidate_pack(),
        intake=intake,
        ratification_events=(active, revocation),
        additional_bound_refs=(governed_ref("actor.reference-operator"),),
    )


def _field_registry() -> FieldRegistry:
    return FieldRegistry(
        registry_ref=governed_ref("field-registry.slice2"),
        fields=(
            FieldDefinition(
                field_id=FIELD_ENVIRONMENT,
                value_kind="ENUM",
                canonical_unit_id=None,
                allowed_terms=(ENVIRONMENT_DRY, ENVIRONMENT_HUMID),
            ),
            FieldDefinition(
                field_id=FIELD_MODE,
                value_kind="ENUM",
                canonical_unit_id=None,
                allowed_terms=(MODE_PRODUCTION, MODE_TEST),
            ),
            FieldDefinition(
                field_id=FIELD_TEMPERATURE,
                value_kind="NUMERIC",
                canonical_unit_id=UNIT_CELSIUS,
                allowed_terms=(),
            ),
        ),
    )


def _unit_registry() -> UnitRegistry:
    return UnitRegistry(
        registry_ref=governed_ref("unit-registry.slice2"),
        units=(
            UnitDefinition(
                unit_id=UNIT_CELSIUS,
                dimension_id=DIMENSION_TEMPERATURE,
                scale_to_base=Decimal("1"),
                offset_to_base=Decimal("0"),
            ),
            UnitDefinition(
                unit_id=UNIT_KELVIN,
                dimension_id=DIMENSION_TEMPERATURE,
                scale_to_base=Decimal("1"),
                offset_to_base=Decimal("-273.15"),
            ),
            UnitDefinition(
                unit_id=UNIT_MM,
                dimension_id=DIMENSION_LENGTH,
                scale_to_base=Decimal("1"),
                offset_to_base=Decimal("0"),
            ),
        ),
    )


def _candidate_records(
    method_ref: GovernedRef,
    group_ref: GovernedRef,
) -> tuple[FailureModeRecord, ...]:
    mode_production = Predicate(
        kind="comparison",
        comparison=MembershipComparison(
            op="in",
            field_id=FIELD_MODE,
            allowed_terms=(MODE_PRODUCTION,),
        ),
    )
    records = (
        _candidate(
            "failure.false",
            method_ref,
            Predicate(
                kind="comparison",
                comparison=OrderedComparison(
                    op="gt",
                    field_id=FIELD_TEMPERATURE,
                    operand=NumericValue(
                        kind="NUMERIC",
                        value=Decimal("100"),
                        unit_id=UNIT_CELSIUS,
                    ),
                ),
            ),
        ),
        _candidate(
            "failure.group-high",
            method_ref,
            mode_production,
            SelectionBinding(
                selection_group_ref=group_ref,
                precedence_rank=Decimal("2"),
            ),
        ),
        _candidate(
            "failure.group-low",
            method_ref,
            mode_production,
            SelectionBinding(
                selection_group_ref=group_ref,
                precedence_rank=Decimal("1"),
            ),
        ),
        _candidate(
            "failure.true-a",
            method_ref,
            Predicate(
                kind="comparison",
                comparison=RangeComparison(
                    op="range",
                    field_id=FIELD_TEMPERATURE,
                    operand=RangeOperand(
                        low=Decimal("20"),
                        high=Decimal("30"),
                        unit_id=UNIT_CELSIUS,
                        low_bound="INCLUSIVE",
                        high_bound="INCLUSIVE",
                    ),
                ),
            ),
        ),
        _candidate("failure.true-b", method_ref, mode_production),
        _candidate(
            "failure.unknown",
            method_ref,
            Predicate(
                kind="comparison",
                comparison=EqualityComparison(
                    op="eq",
                    field_id=FIELD_ENVIRONMENT,
                    operand=EnumValue(kind="ENUM", value=ENVIRONMENT_HUMID),
                ),
            ),
        ),
    )
    return records


def _candidate(
    logical_id: str,
    method_ref: GovernedRef,
    predicate: Predicate,
    binding: SelectionBinding | None = None,
) -> FailureModeRecord:
    return FailureModeRecord(
        failure_mode_ref=governed_ref(logical_id),
        method_ref=method_ref,
        mechanism_id=TermId(f"mechanism.{logical_id.removeprefix('failure.')}"),
        overlap_scope_id=TermId(f"scope.{logical_id}"),
        predicate_ref=governed_ref(f"predicate.{logical_id}"),
        predicate_record_type_id=TermId("record.applicability-predicate"),
        predicate_evidence_location=EvidenceLocator("fixture:predicate"),
        applicability_predicate=predicate,
        selection_binding=binding,
        evidence_refs=(governed_ref(f"evidence.{logical_id}"),),
        lifecycle="PUBLISHED",
    )


def _intake(include_environment: bool) -> tuple[IntakeRecord, RatificationEvent]:
    policy = canonicalization_policy()
    mode_value = EnumValue(kind="ENUM", value=MODE_PRODUCTION)
    mode_source = governed_ref("source.operator-mode-entry")
    mode_event_ref = governed_ref("ratification.mode")
    mode_hash = intake_value_hash(FIELD_MODE, mode_value, policy)
    mode = IntakeValue(
        value_id="value.mode",
        field_id=FIELD_MODE,
        value=mode_value,
        value_hash=mode_hash,
        source_kind="HUMAN_SUPPLIED",
        source_ref=mode_source,
        ratification_event_ref=mode_event_ref,
    )
    temperature_value = NumericValue(
        kind="NUMERIC",
        value=Decimal("25"),
        unit_id=UNIT_CELSIUS,
    )
    temperature = IntakeValue(
        value_id="value.temperature",
        field_id=FIELD_TEMPERATURE,
        value=temperature_value,
        value_hash=intake_value_hash(FIELD_TEMPERATURE, temperature_value, policy),
        source_kind="INSTRUMENT_EMITTED",
        source_ref=governed_ref("source.instrument-temperature"),
        ratification_event_ref=None,
    )
    values = [mode, temperature]
    if include_environment:
        environment_value = EnumValue(kind="ENUM", value=ENVIRONMENT_HUMID)
        values.append(
            IntakeValue(
                value_id="value.environment",
                field_id=FIELD_ENVIRONMENT,
                value=environment_value,
                value_hash=intake_value_hash(
                    FIELD_ENVIRONMENT,
                    environment_value,
                    policy,
                ),
                source_kind="INSTRUMENT_EMITTED",
                source_ref=governed_ref("source.instrument-environment"),
                ratification_event_ref=None,
            )
        )
    values.sort(key=lambda item: (item.field_id, item.value_id))
    pack_ref = candidate_pack().manifest.pack_ref
    event = RatificationEvent.model_validate(
        {
            "event_ref": mode_event_ref,
            "value_id": mode.value_id,
            "field_id": mode.field_id,
            "value_hash": mode.value_hash,
            "source_ref": mode.source_ref,
            "actor_id": "actor.reference-operator",
            "governing_pack_ref": pack_ref,
            "effective_at": ORIGINAL_AS_OF,
            "recorded_at": ORIGINAL_AS_OF,
            "state": "ACTIVE",
            "supersedes_version_id": None,
        },
        context={"canonicalization_policy": policy},
    )
    return (
        IntakeRecord(
            intake_ref=governed_ref("intake.slice2-reference"),
            values=tuple(values),
        ),
        event,
    )


def _directive(template_id: str) -> DisplayDirective:
    return DisplayDirective(template_id=TemplateId(template_id), params=())
