from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

from gptl.core.proposal_ratification import PROPOSAL_RATIFICATION_RECORD_TYPE
from gptl.core.proposals import TYPED_VALUE_PROPOSAL_RECORD_TYPE
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import FieldId, LogicalId, TermId, UnitId, VersionId
from gptl.core.validation_protocols import (
    DESIGNED_VALIDATION_PROTOCOL_RECORD_TYPE,
    DESIGNED_VALIDATION_PROTOCOL_SCHEMA_VERSION,
    HASH_ALGORITHM,
    VALIDATION_PREDICATE_TEMPLATE_VERSION,
    AllOfPredicate,
    DecimalInClosedRangePredicate,
    DesignedValidationExecutionInput,
    DesignedValidationProtocol,
    RequiredPresentPredicate,
    TermEqualsPredicate,
    TimestampInClosedIntervalPredicate,
    UnitCompatiblePredicate,
    UnsupportedValidationPredicate,
    ValidationFieldValue,
    ValidationNumericValue,
    ValidationTermValue,
    designed_validation_result_replay_hash,
    evaluate_designed_validation_protocol,
    finalize_designed_validation_protocol,
)
from gptl.mie.predicates import UnitDefinition, UnitRegistry
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-07-01T12:00:00.000Z"
TEMP_FIELD = FieldId("field.temperature")
STATUS_FIELD = FieldId("field.visual-status")
TIME_FIELD = FieldId("field.observed-at")
SPECIMEN_RECORD_TYPE = TermId("record.material-specimen")
CELSIUS_UNIT = UnitId("unit.celsius")


def test_validated_protocol_can_request_typed_proposal_but_requires_ratification(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    protocol = _protocol(build1_ref_factory, allows_observation_promotion=True)
    execution = _execution(
        build1_ref_factory,
        observation_ref=build1_ref_factory("build1.observation.temperature-note"),
        output_target_record_type=SPECIMEN_RECORD_TYPE,
        requested_created_proposal_refs=(build1_ref_factory("build1.proposal.from-protocol"),),
    )

    result = evaluate_designed_validation_protocol(
        protocol,
        execution,
        (
            _numeric_value(build1_ref_factory, TEMP_FIELD, Decimal("50.0000")),
            _term_value(build1_ref_factory, STATUS_FIELD, TermId("visual-status.acceptable")),
        ),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "VALIDATED"
    assert {item.result for item in result.predicate_evaluations} == {"TRUE"}
    assert result.created_proposal_record_type == TYPED_VALUE_PROPOSAL_RECORD_TYPE
    assert result.created_proposal_refs == (build1_ref_factory("build1.proposal.from-protocol"),)
    assert result.decision_effective is False
    assert result.required_next_record_type == PROPOSAL_RATIFICATION_RECORD_TYPE
    assert result.qualifies_method_or_process is False


def test_missing_required_data_returns_explicit_non_validation(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    protocol = _protocol(build1_ref_factory)

    result = evaluate_designed_validation_protocol(
        protocol,
        _execution(build1_ref_factory),
        (),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "NOT_VALIDATED"
    assert result.created_proposal_refs == ()
    assert any(item.result == "MISSING_DATA" for item in result.predicate_evaluations)
    assert result.predicate_evaluations[0].missing_field_ids


def test_unsupported_predicate_template_is_configuration_invalid(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    predicate = UnsupportedValidationPredicate(
        predicate_ref=_ref("build1.validation-predicate.unsupported", 1),
        template_version=VALIDATION_PREDICATE_TEMPLATE_VERSION,
        template_id="OR",
        canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy"),
        missing_data_behavior="MISSING_DATA",
        evidence_refs=(build1_ref_factory("build1.evidence.validation-protocol"),),
    )
    protocol = _protocol(
        build1_ref_factory,
        acceptance_criteria=(predicate,),
        root_predicate_ref=predicate.predicate_ref,
    )

    result = evaluate_designed_validation_protocol(
        protocol,
        _execution(build1_ref_factory),
        (_numeric_value(build1_ref_factory, TEMP_FIELD, Decimal("50.0000")),),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "INVALID_PROTOCOL_EXECUTION"
    assert result.predicate_evaluations[0].result == "CONFIGURATION_INVALID"


def test_observation_promotion_target_must_be_allowed_by_protocol(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    protocol = _protocol(build1_ref_factory, allows_observation_promotion=False)
    execution = _execution(
        build1_ref_factory,
        observation_ref=build1_ref_factory("build1.observation.temperature-note"),
        output_target_record_type=SPECIMEN_RECORD_TYPE,
        requested_created_proposal_refs=(build1_ref_factory("build1.proposal.from-protocol"),),
    )

    result = evaluate_designed_validation_protocol(
        protocol,
        execution,
        (
            _numeric_value(build1_ref_factory, TEMP_FIELD, Decimal("50.0000")),
            _term_value(build1_ref_factory, STATUS_FIELD, TermId("visual-status.acceptable")),
        ),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "INVALID_PROTOCOL_EXECUTION"
    assert result.created_proposal_refs == ()
    assert any(item.result == "CONFIGURATION_INVALID" for item in result.predicate_evaluations)


def test_execution_authority_and_separation_of_duties_are_enforced(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    protocol = _protocol(build1_ref_factory)
    actor = build1_ref_factory("build1.actor.executor")

    result = evaluate_designed_validation_protocol(
        protocol,
        _execution(
            build1_ref_factory,
            claimed_executor_actor_ref=actor,
            claimed_reviewer_actor_ref=actor,
        ),
        (
            _numeric_value(build1_ref_factory, TEMP_FIELD, Decimal("50.0000")),
            _term_value(build1_ref_factory, STATUS_FIELD, TermId("visual-status.acceptable")),
        ),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "INVALID_PROTOCOL_EXECUTION"
    assert result.claimed_executor_actor_ref == actor
    assert result.claimed_reviewer_actor_ref == actor
    assert any(item.result == "CONFIGURATION_INVALID" for item in result.predicate_evaluations)


def test_unit_incompatibility_is_invalid_operand_not_validation(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    protocol = _protocol(build1_ref_factory)

    result = evaluate_designed_validation_protocol(
        protocol,
        _execution(build1_ref_factory),
        (
            _numeric_value(build1_ref_factory, TEMP_FIELD, Decimal("50.0000"), unit_id=UnitId("unit.mm")),
            _term_value(build1_ref_factory, STATUS_FIELD, TermId("visual-status.acceptable")),
        ),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "INVALID_PROTOCOL_EXECUTION"
    assert any(item.result == "INVALID_OPERAND" for item in result.predicate_evaluations)
    assert result.created_proposal_refs == ()


def test_timestamp_interval_template_is_deterministic(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    predicate = TimestampInClosedIntervalPredicate.model_validate(
        {
            "predicate_ref": _ref("build1.validation-predicate.timestamp", 1),
            "template_version": VALIDATION_PREDICATE_TEMPLATE_VERSION,
            "template_id": "TIMESTAMP_IN_CLOSED_INTERVAL",
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "missing_data_behavior": "MISSING_DATA",
            "field_id": TIME_FIELD,
            "start_timestamp": "2026-07-01T00:00:00.000Z",
            "end_timestamp": "2026-07-02T00:00:00.000Z",
            "evidence_refs": (build1_ref_factory("build1.evidence.validation-protocol"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    protocol = _protocol(
        build1_ref_factory,
        required_field_ids=(TIME_FIELD,),
        acceptance_criteria=(predicate,),
        root_predicate_ref=predicate.predicate_ref,
    )

    result = evaluate_designed_validation_protocol(
        protocol,
        _execution(build1_ref_factory),
        (_timestamp_value(build1_ref_factory, TIME_FIELD, AS_OF),),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert result.terminal_state == "VALIDATED"
    assert result.predicate_evaluations[0].result == "TRUE"


def test_validation_result_replay_hash_is_order_independent(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    protocol = _protocol(build1_ref_factory)
    execution = _execution(build1_ref_factory)
    values = (
        _numeric_value(build1_ref_factory, TEMP_FIELD, Decimal("50.0000")),
        _term_value(build1_ref_factory, STATUS_FIELD, TermId("visual-status.acceptable")),
    )

    first = evaluate_designed_validation_protocol(
        protocol,
        execution,
        values,
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )
    second = evaluate_designed_validation_protocol(
        protocol,
        execution,
        tuple(reversed(values)),
        _unit_registry(build1_ref_factory),
        canonicalization_policy(),
    )

    assert protocol.protocol_ref.content_hash != "0" * 64
    assert designed_validation_result_replay_hash(
        protocol=protocol,
        result=first,
        canonicalization_policy=canonicalization_policy(),
    ) == designed_validation_result_replay_hash(
        protocol=protocol,
        result=second,
        canonicalization_policy=canonicalization_policy(),
    )


def test_slice_6_runtime_source_guard(
    runtime_source_guard: Callable[[tuple[Path, ...]], None],
) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard(
        (repository_root / "src" / "gptl" / "core" / "validation_protocols.py",)
    )


def _protocol(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    required_field_ids: tuple[FieldId, ...] = (TEMP_FIELD, STATUS_FIELD),
    acceptance_criteria: tuple[object, ...] | None = None,
    root_predicate_ref: GovernedRef | None = None,
    allows_observation_promotion: bool = False,
) -> DesignedValidationProtocol:
    criteria = acceptance_criteria or _default_predicates(build1_ref_factory)
    root_ref = root_predicate_ref or _ref("build1.validation-predicate.all", 1)
    protocol = DesignedValidationProtocol.model_validate(
        {
            "schema_version": DESIGNED_VALIDATION_PROTOCOL_SCHEMA_VERSION,
            "record_type": DESIGNED_VALIDATION_PROTOCOL_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "protocol_ref": _ref("build1.validation-protocol.temperature-check", 1),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "predicate_template_version": VALIDATION_PREDICATE_TEMPLATE_VERSION,
            "hypothesis_text": "The observed discoloration is acceptable after the bake cycle.",
            "required_field_ids": required_field_ids,
            "required_method_capability_ids": (TermId("capability.visual-inspection"),),
            "required_tool_capability_ids": (TermId("capability.temperature-log"),),
            "required_input_record_refs": (build1_ref_factory("build1.source.shift-note"),),
            "acceptance_criteria": criteria,
            "root_predicate_ref": root_ref,
            "executor_role_id": TermId("role.validation-executor"),
            "reviewer_role_id": TermId("role.materials-reviewer"),
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "same_actor_allowed": False,
            "allowed_terminal_states": (
                "INVALID_PROTOCOL_EXECUTION",
                "NOT_VALIDATED",
                "VALIDATED",
            ),
            "allows_observation_promotion": allows_observation_promotion,
            "allowed_output_target_record_types": (SPECIMEN_RECORD_TYPE,)
            if allows_observation_promotion
            else (),
            "result_schema_ref": build1_ref_factory("build1.validation-result.schema"),
            "evidence_refs": (build1_ref_factory("build1.evidence.validation-protocol"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return finalize_designed_validation_protocol(protocol, canonicalization_policy())


def _default_predicates(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> tuple[object, ...]:
    policy_ref = build1_ref_factory("build1.canonicalization.policy")
    evidence_ref = build1_ref_factory("build1.evidence.validation-protocol")
    unit_registry_ref = build1_ref_factory("build1.unit-registry")
    present = RequiredPresentPredicate(
        predicate_ref=_ref("build1.validation-predicate.present", 1),
        template_version=VALIDATION_PREDICATE_TEMPLATE_VERSION,
        template_id="REQUIRED_PRESENT",
        canonicalization_policy_ref=policy_ref,
        missing_data_behavior="MISSING_DATA",
        field_id=TEMP_FIELD,
        evidence_refs=(evidence_ref,),
    )
    range_check = DecimalInClosedRangePredicate(
        predicate_ref=_ref("build1.validation-predicate.temperature-range", 1),
        template_version=VALIDATION_PREDICATE_TEMPLATE_VERSION,
        template_id="DECIMAL_IN_CLOSED_RANGE",
        canonicalization_policy_ref=policy_ref,
        missing_data_behavior="MISSING_DATA",
        field_id=TEMP_FIELD,
        lower_decimal=Decimal("45.0000"),
        upper_decimal=Decimal("55.0000"),
        unit_id=UnitId("unit.celsius"),
        unit_registry_ref=unit_registry_ref,
        evidence_refs=(evidence_ref,),
    )
    term_check = UnitCompatiblePredicate(
        predicate_ref=_ref("build1.validation-predicate.unit-compatible", 1),
        template_version=VALIDATION_PREDICATE_TEMPLATE_VERSION,
        template_id="UNIT_COMPATIBLE",
        canonicalization_policy_ref=policy_ref,
        missing_data_behavior="MISSING_DATA",
        field_id=TEMP_FIELD,
        unit_id=UnitId("unit.celsius"),
        unit_registry_ref=unit_registry_ref,
        evidence_refs=(evidence_ref,),
    )
    status_check = TermEqualsPredicate(
        predicate_ref=_ref("build1.validation-predicate.status-placeholder", 1),
        template_version=VALIDATION_PREDICATE_TEMPLATE_VERSION,
        template_id="TERM_EQUALS",
        canonicalization_policy_ref=policy_ref,
        missing_data_behavior="MISSING_DATA",
        field_id=STATUS_FIELD,
        expected_term_ref=TermId("visual-status.acceptable"),
        evidence_refs=(evidence_ref,),
    )
    all_of = AllOfPredicate(
        predicate_ref=_ref("build1.validation-predicate.all", 1),
        template_version=VALIDATION_PREDICATE_TEMPLATE_VERSION,
        template_id="ALL_OF",
        canonicalization_policy_ref=policy_ref,
        missing_data_behavior="MISSING_DATA",
        predicate_refs=(
            present.predicate_ref,
            range_check.predicate_ref,
            term_check.predicate_ref,
            _ref("build1.validation-predicate.status-placeholder", 1),
        ),
        evidence_refs=(evidence_ref,),
    )
    return (all_of, present, range_check, term_check, status_check)


def _execution(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    claimed_executor_actor_ref: GovernedRef | None = None,
    claimed_reviewer_actor_ref: GovernedRef | None = None,
    observation_ref: GovernedRef | None = None,
    output_target_record_type: TermId | None = None,
    requested_created_proposal_refs: tuple[GovernedRef, ...] = (),
) -> DesignedValidationExecutionInput:
    return DesignedValidationExecutionInput.model_validate(
        {
            "result_ref": _ref("build1.validation-result.temperature-check", 1),
            "claimed_executor_actor_ref": claimed_executor_actor_ref
            or build1_ref_factory("build1.actor.executor"),
            "claimed_reviewer_actor_ref": claimed_reviewer_actor_ref
            or build1_ref_factory("build1.actor.reviewer"),
            "executor_role_id": TermId("role.validation-executor"),
            "reviewer_role_id": TermId("role.materials-reviewer"),
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "authorization_event_ref": build1_ref_factory("build1.authorization.executor"),
            "reviewer_event_ref": build1_ref_factory("build1.ratification.validation-review"),
            "recorded_at": AS_OF,
            "collected_source_artifact_refs": (build1_ref_factory("build1.source.validation-run"),),
            "collected_proposal_refs": (),
            "observation_ref": observation_ref,
            "output_target_record_type": output_target_record_type,
            "requested_created_proposal_refs": requested_created_proposal_refs,
            "evidence_refs": (build1_ref_factory("build1.evidence.validation-execution"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _numeric_value(
    build1_ref_factory: Callable[[str], GovernedRef],
    field_id: FieldId,
    value: Decimal,
    *,
    unit_id: UnitId = CELSIUS_UNIT,
) -> ValidationFieldValue:
    return ValidationFieldValue(
        field_id=field_id,
        value=ValidationNumericValue(kind="NUMERIC", value=value, unit_id=unit_id),
        operand_ref=build1_ref_factory(f"build1.operand.{field_id}"),
        evidence_refs=(build1_ref_factory("build1.evidence.validation-value"),),
    )


def _term_value(
    build1_ref_factory: Callable[[str], GovernedRef],
    field_id: FieldId,
    value: TermId,
) -> ValidationFieldValue:
    return ValidationFieldValue(
        field_id=field_id,
        value=ValidationTermValue(kind="TERM", value=value),
        operand_ref=build1_ref_factory(f"build1.operand.{field_id}"),
        evidence_refs=(build1_ref_factory("build1.evidence.validation-value"),),
    )


def _timestamp_value(
    build1_ref_factory: Callable[[str], GovernedRef],
    field_id: FieldId,
    value: str,
) -> ValidationFieldValue:
    return ValidationFieldValue.model_validate(
        {
            "field_id": field_id,
            "value": {"kind": "TIMESTAMP", "value": value},
            "operand_ref": build1_ref_factory(f"build1.operand.{field_id}"),
            "evidence_refs": (build1_ref_factory("build1.evidence.validation-value"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _unit_registry(build1_ref_factory: Callable[[str], GovernedRef]) -> UnitRegistry:
    return UnitRegistry(
        registry_ref=build1_ref_factory("build1.unit-registry"),
        units=(
            UnitDefinition(
                unit_id=UnitId("unit.celsius"),
                dimension_id=TermId("dimension.temperature"),
                scale_to_base=Decimal("1.0000"),
                offset_to_base=Decimal("0.0000"),
            ),
            UnitDefinition(
                unit_id=UnitId("unit.mm"),
                dimension_id=TermId("dimension.length"),
                scale_to_base=Decimal("1.0000"),
                offset_to_base=Decimal("0.0000"),
            ),
        ),
    )


def _ref(logical_id: str, version_number: int) -> GovernedRef:
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v{version_number}"),
        version_number=version_number,
        content_hash="0" * 64,
    )
