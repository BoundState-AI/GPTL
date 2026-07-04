"""Build 1 designed-validation protocol contracts."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Final, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gptl.core.canonical import CanonicalizationError, canonical_decimal, canonical_sha256
from gptl.core.proposal_ratification import PROPOSAL_RATIFICATION_RECORD_TYPE
from gptl.core.proposals import TYPED_VALUE_PROPOSAL_RECORD_TYPE
from gptl.core.records import GovernedRef, governed_record_content_hash, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalDecimal,
    CanonicalizationPolicy,
    CanonicalTimestamp,
    FieldId,
    OpaqueId,
    Sha256Hex,
    TermId,
    UnitId,
)
from gptl.mie.predicates import NumericValue, UnitRegistry, convert_numeric_value

DESIGNED_VALIDATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "gptl.build1.designed-validation-protocol.v1"
)
DESIGNED_VALIDATION_PROTOCOL_RECORD_TYPE: Final = "DESIGNED_VALIDATION_PROTOCOL"
DESIGNED_VALIDATION_RESULT_SCHEMA_VERSION: Final = "gptl.build1.designed-validation-result.v1"
DESIGNED_VALIDATION_RESULT_RECORD_TYPE: Final = "DESIGNED_VALIDATION_RESULT"
VALIDATION_PREDICATE_TEMPLATE_VERSION: Final = "VALIDATION_PREDICATE_TEMPLATES_V1"
VALIDATION_RESULT_REPLAY_HASH_ALGORITHM_ID: Final = "DESIGNED_VALIDATION_RESULT_REPLAY_HASH_V1"
HASH_ALGORITHM: Final = "SHA-256"

VALIDATION_PROTOCOL_VALIDATED_REASON_ID: Final = TermId("build1.validation-protocol.validated")
VALIDATION_PROTOCOL_NOT_VALIDATED_REASON_ID: Final = TermId(
    "build1.validation-protocol.not-validated"
)
VALIDATION_PROTOCOL_INVALID_EXECUTION_REASON_ID: Final = TermId(
    "build1.validation-protocol.invalid-execution"
)

ValidationPredicateResult = Literal[
    "TRUE",
    "FALSE",
    "MISSING_DATA",
    "INVALID_OPERAND",
    "CONFIGURATION_INVALID",
]
ProtocolTerminalState = Literal[
    "VALIDATED",
    "NOT_VALIDATED",
    "INCONCLUSIVE",
    "INVALID_PROTOCOL_EXECUTION",
]


class ValidationNumericValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["NUMERIC"]
    value: CanonicalDecimal
    unit_id: UnitId


class ValidationTermValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["TERM"]
    value: TermId


class ValidationTimestampValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["TIMESTAMP"]
    value: CanonicalTimestamp


ValidationScalarValue = Annotated[
    ValidationNumericValue | ValidationTermValue | ValidationTimestampValue,
    Field(discriminator="kind"),
]


class ValidationFieldValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_id: FieldId
    value: ValidationScalarValue
    operand_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_refs(value, "evidence_refs")

    @model_validator(mode="after")
    def validate_evidence(self) -> ValidationFieldValue:
        if not self.evidence_refs:
            raise ValueError("validation field value requires evidence references")
        return self


class PredicateBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate_ref: GovernedRef
    template_version: Literal["VALIDATION_PREDICATE_TEMPLATES_V1"]
    template_id: OpaqueId
    canonicalization_policy_ref: GovernedRef
    missing_data_behavior: Literal["MISSING_DATA"]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_refs(value, "evidence_refs")

    @model_validator(mode="after")
    def validate_evidence(self) -> PredicateBase:
        if not self.evidence_refs:
            raise ValueError("validation predicate requires evidence references")
        return self


class RequiredPresentPredicate(PredicateBase):
    template_id: Literal["REQUIRED_PRESENT"]
    field_id: FieldId


class TermEqualsPredicate(PredicateBase):
    template_id: Literal["TERM_EQUALS"]
    field_id: FieldId
    expected_term_ref: TermId


class DecimalEqualsPredicate(PredicateBase):
    template_id: Literal["DECIMAL_EQUALS"]
    field_id: FieldId
    expected_decimal: CanonicalDecimal
    unit_id: UnitId
    unit_registry_ref: GovernedRef


class DecimalInClosedRangePredicate(PredicateBase):
    template_id: Literal["DECIMAL_IN_CLOSED_RANGE"]
    field_id: FieldId
    lower_decimal: CanonicalDecimal
    upper_decimal: CanonicalDecimal
    unit_id: UnitId
    unit_registry_ref: GovernedRef

    @model_validator(mode="after")
    def validate_range(self) -> DecimalInClosedRangePredicate:
        if self.lower_decimal > self.upper_decimal:
            raise ValueError("validation decimal range lower bound cannot exceed upper bound")
        return self


class TimestampInClosedIntervalPredicate(PredicateBase):
    template_id: Literal["TIMESTAMP_IN_CLOSED_INTERVAL"]
    field_id: FieldId
    start_timestamp: CanonicalTimestamp
    end_timestamp: CanonicalTimestamp

    @model_validator(mode="after")
    def validate_interval(self) -> TimestampInClosedIntervalPredicate:
        if self.start_timestamp > self.end_timestamp:
            raise ValueError("validation timestamp interval start cannot exceed end")
        return self


class UnitCompatiblePredicate(PredicateBase):
    template_id: Literal["UNIT_COMPATIBLE"]
    field_id: FieldId
    unit_id: UnitId
    unit_registry_ref: GovernedRef


class AllOfPredicate(PredicateBase):
    template_id: Literal["ALL_OF"]
    predicate_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_predicate_refs(cls, value: object) -> object:
        return _sort_refs(value, "predicate_refs")

    @model_validator(mode="after")
    def validate_terms(self) -> AllOfPredicate:
        if not self.predicate_refs:
            raise ValueError("ALL_OF validation predicate requires child predicate refs")
        return self


class UnsupportedValidationPredicate(PredicateBase):
    pass


ValidationPredicate = (
    RequiredPresentPredicate
    | TermEqualsPredicate
    | DecimalEqualsPredicate
    | DecimalInClosedRangePredicate
    | TimestampInClosedIntervalPredicate
    | UnitCompatiblePredicate
    | AllOfPredicate
    | UnsupportedValidationPredicate
)


class DesignedValidationProtocol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.designed-validation-protocol.v1"]
    record_type: Literal["DESIGNED_VALIDATION_PROTOCOL"]
    hash_algorithm: Literal["SHA-256"]
    protocol_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    predicate_template_version: Literal["VALIDATION_PREDICATE_TEMPLATES_V1"]
    hypothesis_text: str
    required_field_ids: tuple[FieldId, ...]
    required_method_capability_ids: tuple[TermId, ...]
    required_tool_capability_ids: tuple[TermId, ...]
    required_input_record_refs: tuple[GovernedRef, ...]
    acceptance_criteria: tuple[ValidationPredicate, ...]
    root_predicate_ref: GovernedRef
    executor_role_id: TermId
    reviewer_role_id: TermId
    authority_policy_ref: GovernedRef
    same_actor_allowed: bool
    allowed_terminal_states: tuple[ProtocolTerminalState, ...]
    allows_observation_promotion: bool
    allowed_output_target_record_types: tuple[TermId, ...]
    result_schema_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_protocol_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        for field_name in (
            "required_field_ids",
            "required_method_capability_ids",
            "required_tool_capability_ids",
            "allowed_terminal_states",
            "allowed_output_target_record_types",
        ):
            if field_name in normalized:
                normalized[field_name] = tuple(sorted(normalized[field_name]))
        for field_name in ("required_input_record_refs", "evidence_refs"):
            normalized = _sort_ref_mapping(normalized, field_name)
        if "acceptance_criteria" in normalized:
            normalized["acceptance_criteria"] = tuple(
                sorted(
                    normalized["acceptance_criteria"],
                    key=lambda item: _ref_value_key(item, "predicate_ref"),
                )
            )
        return normalized

    @model_validator(mode="after")
    def validate_protocol(self) -> DesignedValidationProtocol:
        if not self.hypothesis_text.strip():
            raise ValueError("designed-validation protocol requires a hypothesis")
        if not self.required_field_ids:
            raise ValueError("designed-validation protocol requires data fields")
        _validate_unique_sorted(self.required_field_ids, "required fields")
        _validate_unique_sorted(self.required_method_capability_ids, "method capability IDs")
        _validate_unique_sorted(self.required_tool_capability_ids, "tool capability IDs")
        _validate_ref_order(self.required_input_record_refs, "required input records")
        if not self.acceptance_criteria:
            raise ValueError("designed-validation protocol requires acceptance criteria")
        predicate_refs = tuple(item.predicate_ref for item in self.acceptance_criteria)
        _validate_ref_order(predicate_refs, "acceptance criteria")
        if self.root_predicate_ref not in predicate_refs:
            raise ValueError("root predicate must be one of the acceptance criteria")
        if not self.allowed_terminal_states:
            raise ValueError("protocol requires allowed terminal states")
        _validate_unique_sorted(self.allowed_terminal_states, "allowed terminal states")
        _validate_unique_sorted(self.allowed_output_target_record_types, "output target types")
        if self.allows_observation_promotion and not self.allowed_output_target_record_types:
            raise ValueError("observation promotion requires allowed output target types")
        if not self.evidence_refs:
            raise ValueError("designed-validation protocol requires evidence references")
        return self


class DesignedValidationExecutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result_ref: GovernedRef
    claimed_executor_actor_ref: GovernedRef
    claimed_reviewer_actor_ref: GovernedRef
    executor_role_id: TermId
    reviewer_role_id: TermId
    authority_policy_ref: GovernedRef
    authorization_event_ref: GovernedRef
    reviewer_event_ref: GovernedRef
    recorded_at: CanonicalTimestamp
    collected_source_artifact_refs: tuple[GovernedRef, ...]
    collected_proposal_refs: tuple[GovernedRef, ...]
    observation_ref: GovernedRef | None = None
    output_target_record_type: TermId | None = None
    requested_created_proposal_refs: tuple[GovernedRef, ...] = ()
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_execution_refs(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        for field_name in (
            "collected_source_artifact_refs",
            "collected_proposal_refs",
            "requested_created_proposal_refs",
            "evidence_refs",
        ):
            normalized = _sort_ref_mapping(normalized, field_name)
        return normalized

    @model_validator(mode="after")
    def validate_execution_input(self) -> DesignedValidationExecutionInput:
        for values, label in (
            (self.collected_source_artifact_refs, "collected source artifacts"),
            (self.collected_proposal_refs, "collected proposals"),
            (self.requested_created_proposal_refs, "requested created proposals"),
            (self.evidence_refs, "execution evidence"),
        ):
            _validate_ref_order(values, label)
        if not self.evidence_refs:
            raise ValueError("designed-validation result requires execution evidence")
        if (self.observation_ref is None) != (self.output_target_record_type is None):
            raise ValueError("observation promotion requires both observation and output target")
        return self


class ValidationPredicateEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate_ref: GovernedRef
    template_id: OpaqueId
    result: ValidationPredicateResult
    missing_field_ids: tuple[FieldId, ...]
    operand_refs: tuple[GovernedRef, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evaluation_refs(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        normalized = _sort_ref_mapping(normalized, "operand_refs")
        normalized = _sort_ref_mapping(normalized, "evidence_refs")
        if "missing_field_ids" in normalized:
            normalized["missing_field_ids"] = tuple(
                sorted(cast(Sequence[FieldId], normalized["missing_field_ids"]))
            )
        return normalized

    @model_validator(mode="after")
    def validate_evaluation(self) -> ValidationPredicateEvaluation:
        _validate_unique_sorted(self.missing_field_ids, "missing fields")
        _validate_ref_order(self.operand_refs, "operand refs")
        _validate_ref_order(self.evidence_refs, "predicate evidence")
        if self.result == "MISSING_DATA":
            if not self.missing_field_ids:
                raise ValueError("missing-data predicate evaluation requires missing fields")
        elif self.missing_field_ids:
            raise ValueError("only missing-data predicate evaluations carry missing fields")
        return self


class DesignedValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.designed-validation-result.v1"]
    record_type: Literal["DESIGNED_VALIDATION_RESULT"]
    hash_algorithm: Literal["SHA-256"]
    result_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    protocol_ref: GovernedRef
    predicate_template_version: Literal["VALIDATION_PREDICATE_TEMPLATES_V1"]
    unit_registry_ref: GovernedRef
    claimed_executor_actor_ref: GovernedRef
    claimed_reviewer_actor_ref: GovernedRef
    executor_role_id: TermId
    reviewer_role_id: TermId
    authority_policy_ref: GovernedRef
    authorization_event_ref: GovernedRef
    reviewer_event_ref: GovernedRef
    recorded_at: CanonicalTimestamp
    collected_source_artifact_refs: tuple[GovernedRef, ...]
    collected_proposal_refs: tuple[GovernedRef, ...]
    operand_refs: tuple[GovernedRef, ...]
    predicate_evaluations: tuple[ValidationPredicateEvaluation, ...]
    terminal_state: ProtocolTerminalState
    reason_id: TermId
    observation_ref: GovernedRef | None
    output_target_record_type: TermId | None
    created_proposal_record_type: Literal["TYPED_VALUE_PROPOSAL"] | None
    created_proposal_refs: tuple[GovernedRef, ...]
    decision_effective: Literal[False]
    required_next_record_type: Literal["PROPOSAL_RATIFICATION_EVENT"] | None
    qualifies_method_or_process: Literal[False]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_result_refs(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        for field_name in (
            "collected_source_artifact_refs",
            "collected_proposal_refs",
            "operand_refs",
            "created_proposal_refs",
            "evidence_refs",
        ):
            normalized = _sort_ref_mapping(normalized, field_name)
        if "predicate_evaluations" in normalized:
            normalized["predicate_evaluations"] = tuple(
                sorted(
                    normalized["predicate_evaluations"],
                    key=lambda item: _ref_value_key(item, "predicate_ref"),
                )
            )
        return normalized

    @model_validator(mode="after")
    def validate_result(self) -> DesignedValidationResult:
        for values, label in (
            (self.collected_source_artifact_refs, "collected source artifacts"),
            (self.collected_proposal_refs, "collected proposals"),
            (self.operand_refs, "operand refs"),
            (self.created_proposal_refs, "created proposal refs"),
            (self.evidence_refs, "result evidence"),
        ):
            _validate_ref_order(values, label)
        if not self.evidence_refs:
            raise ValueError("designed-validation result requires evidence references")
        evaluation_refs = tuple(item.predicate_ref for item in self.predicate_evaluations)
        _validate_ref_order(evaluation_refs, "predicate evaluations")
        if self.created_proposal_refs:
            if self.created_proposal_record_type != TYPED_VALUE_PROPOSAL_RECORD_TYPE:
                raise ValueError("validation result can create only typed value proposals")
            if self.required_next_record_type != PROPOSAL_RATIFICATION_RECORD_TYPE:
                raise ValueError("created validation proposals still require ratification")
            if self.terminal_state != "VALIDATED":
                raise ValueError("only validated protocol results may request proposals")
        elif self.created_proposal_record_type is not None or self.required_next_record_type is not None:
            raise ValueError("proposal metadata requires created proposal refs")
        if (self.observation_ref is None) != (self.output_target_record_type is None):
            raise ValueError("observation-derived result requires observation and output target")
        if self.terminal_state == "VALIDATED":
            if any(item.result != "TRUE" for item in self.predicate_evaluations):
                raise ValueError("validated protocol requires every predicate to evaluate TRUE")
        if self.terminal_state == "INVALID_PROTOCOL_EXECUTION":
            invalid_results = {"INVALID_OPERAND", "CONFIGURATION_INVALID"}
            if not any(item.result in invalid_results for item in self.predicate_evaluations):
                raise ValueError("invalid protocol execution requires invalid predicate evidence")
        return self


def evaluate_designed_validation_protocol(
    protocol: DesignedValidationProtocol,
    execution: DesignedValidationExecutionInput,
    field_values: tuple[ValidationFieldValue, ...],
    unit_registry: UnitRegistry,
    canonicalization_policy: CanonicalizationPolicy,
) -> DesignedValidationResult:
    duplicate_fields = _duplicate_field_ids(field_values)
    values_by_field = {item.field_id: item for item in field_values}
    criteria_by_ref = {item.predicate_ref: item for item in protocol.acceptance_criteria}
    evaluations = tuple(
        _evaluate_predicate(
            predicate,
            criteria_by_ref,
            values_by_field,
            protocol,
            unit_registry,
            canonicalization_policy,
        )
        for predicate in protocol.acceptance_criteria
    )
    if duplicate_fields:
        evaluations = _replace_evaluation(
            evaluations,
            _configuration_invalid_evaluation(
                protocol.root_predicate_ref,
                "FIELD_VALUE_DUPLICATE",
            ),
        )
    root_evaluation = next(
        item for item in evaluations if item.predicate_ref == protocol.root_predicate_ref
    )
    terminal_state = _terminal_state(root_evaluation, evaluations, protocol.required_field_ids, values_by_field)
    if _invalid_execution_authority(protocol, execution):
        terminal_state = "INVALID_PROTOCOL_EXECUTION"
        evaluations = _replace_evaluation(
            evaluations,
            _configuration_invalid_evaluation(
                protocol.root_predicate_ref,
                "EXECUTION_AUTHORITY_MISMATCH",
            ),
        )
    if _invalid_observation_promotion_request(protocol, execution, terminal_state):
        terminal_state = "INVALID_PROTOCOL_EXECUTION"
        evaluations = _replace_evaluation(
            evaluations,
            _configuration_invalid_evaluation(
                protocol.root_predicate_ref,
                "OBSERVATION_PROMOTION_NOT_ALLOWED",
            ),
        )
    if terminal_state not in protocol.allowed_terminal_states:
        terminal_state = "INVALID_PROTOCOL_EXECUTION"
        evaluations = _replace_evaluation(
            evaluations,
            _configuration_invalid_evaluation(
                protocol.root_predicate_ref,
                "TERMINAL_STATE_NOT_ALLOWED",
            ),
        )
    created_refs = _created_proposal_refs(protocol, execution, terminal_state)
    reason_id = {
        "VALIDATED": VALIDATION_PROTOCOL_VALIDATED_REASON_ID,
        "NOT_VALIDATED": VALIDATION_PROTOCOL_NOT_VALIDATED_REASON_ID,
        "INCONCLUSIVE": VALIDATION_PROTOCOL_NOT_VALIDATED_REASON_ID,
        "INVALID_PROTOCOL_EXECUTION": VALIDATION_PROTOCOL_INVALID_EXECUTION_REASON_ID,
    }[terminal_state]
    result = DesignedValidationResult.model_validate(
        {
            "schema_version": DESIGNED_VALIDATION_RESULT_SCHEMA_VERSION,
            "record_type": DESIGNED_VALIDATION_RESULT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "result_ref": execution.result_ref,
            "canonicalization_policy_ref": protocol.canonicalization_policy_ref,
            "protocol_ref": protocol.protocol_ref,
            "predicate_template_version": VALIDATION_PREDICATE_TEMPLATE_VERSION,
            "unit_registry_ref": unit_registry.registry_ref,
            "claimed_executor_actor_ref": execution.claimed_executor_actor_ref,
            "claimed_reviewer_actor_ref": execution.claimed_reviewer_actor_ref,
            "executor_role_id": execution.executor_role_id,
            "reviewer_role_id": execution.reviewer_role_id,
            "authority_policy_ref": execution.authority_policy_ref,
            "authorization_event_ref": execution.authorization_event_ref,
            "reviewer_event_ref": execution.reviewer_event_ref,
            "recorded_at": execution.recorded_at,
            "collected_source_artifact_refs": execution.collected_source_artifact_refs,
            "collected_proposal_refs": execution.collected_proposal_refs,
            "operand_refs": tuple(item.operand_ref for item in field_values),
            "predicate_evaluations": evaluations,
            "terminal_state": terminal_state,
            "reason_id": reason_id,
            "observation_ref": execution.observation_ref,
            "output_target_record_type": execution.output_target_record_type,
            "created_proposal_record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE
            if created_refs
            else None,
            "created_proposal_refs": created_refs,
            "decision_effective": False,
            "required_next_record_type": PROPOSAL_RATIFICATION_RECORD_TYPE
            if created_refs
            else None,
            "qualifies_method_or_process": False,
            "evidence_refs": execution.evidence_refs,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )
    return finalize_designed_validation_result(result, canonicalization_policy)


def designed_validation_protocol_content_hash(
    protocol: DesignedValidationProtocol,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return governed_record_content_hash(protocol, "protocol_ref", canonicalization_policy)


def finalize_designed_validation_protocol(
    protocol: DesignedValidationProtocol,
    canonicalization_policy: CanonicalizationPolicy,
) -> DesignedValidationProtocol:
    content_hash = designed_validation_protocol_content_hash(protocol, canonicalization_policy)
    updated_ref = protocol.protocol_ref.model_copy(update={"content_hash": content_hash})
    return protocol.model_copy(update={"protocol_ref": updated_ref})


def designed_validation_result_content_hash(
    result: DesignedValidationResult,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return governed_record_content_hash(result, "result_ref", canonicalization_policy)


def finalize_designed_validation_result(
    result: DesignedValidationResult,
    canonicalization_policy: CanonicalizationPolicy,
) -> DesignedValidationResult:
    content_hash = designed_validation_result_content_hash(result, canonicalization_policy)
    updated_ref = result.result_ref.model_copy(update={"content_hash": content_hash})
    return result.model_copy(update={"result_ref": updated_ref})


def designed_validation_result_replay_hash(
    protocol: DesignedValidationProtocol,
    result: DesignedValidationResult,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    payload = {
        "algorithm_id": VALIDATION_RESULT_REPLAY_HASH_ALGORITHM_ID,
        "protocol_ref": protocol.protocol_ref,
        "protocol_content_hash": protocol.protocol_ref.content_hash,
        "result": result.model_dump(mode="python", exclude_none=True),
    }
    return canonical_sha256(payload, canonicalization_policy)


def _evaluate_predicate(
    predicate: ValidationPredicate,
    criteria_by_ref: dict[GovernedRef, ValidationPredicate],
    values_by_field: dict[FieldId, ValidationFieldValue],
    protocol: DesignedValidationProtocol,
    unit_registry: UnitRegistry,
    canonicalization_policy: CanonicalizationPolicy,
) -> ValidationPredicateEvaluation:
    if isinstance(predicate, UnsupportedValidationPredicate):
        return _configuration_invalid_evaluation(predicate.predicate_ref, predicate.template_id)
    if (
        predicate.template_version != protocol.predicate_template_version
        or predicate.canonicalization_policy_ref != protocol.canonicalization_policy_ref
    ):
        return _configuration_invalid_evaluation(predicate.predicate_ref, predicate.template_id)
    if isinstance(predicate, RequiredPresentPredicate):
        return _field_presence_evaluation(predicate, values_by_field)
    if isinstance(predicate, TermEqualsPredicate):
        return _term_equals_evaluation(predicate, values_by_field)
    if isinstance(predicate, DecimalEqualsPredicate):
        return _decimal_equals_evaluation(predicate, values_by_field, unit_registry, canonicalization_policy)
    if isinstance(predicate, DecimalInClosedRangePredicate):
        return _decimal_range_evaluation(predicate, values_by_field, unit_registry, canonicalization_policy)
    if isinstance(predicate, TimestampInClosedIntervalPredicate):
        return _timestamp_interval_evaluation(predicate, values_by_field)
    if isinstance(predicate, UnitCompatiblePredicate):
        return _unit_compatible_evaluation(predicate, values_by_field, unit_registry)
    return _all_of_evaluation(predicate, criteria_by_ref, values_by_field, protocol, unit_registry, canonicalization_policy)


def _field_presence_evaluation(
    predicate: RequiredPresentPredicate,
    values_by_field: dict[FieldId, ValidationFieldValue],
) -> ValidationPredicateEvaluation:
    value = values_by_field.get(predicate.field_id)
    if value is None:
        return _missing_evaluation(predicate, predicate.field_id)
    return _predicate_evaluation(predicate, "TRUE", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)


def _term_equals_evaluation(
    predicate: TermEqualsPredicate,
    values_by_field: dict[FieldId, ValidationFieldValue],
) -> ValidationPredicateEvaluation:
    value = values_by_field.get(predicate.field_id)
    if value is None:
        return _missing_evaluation(predicate, predicate.field_id)
    if not isinstance(value.value, ValidationTermValue):
        return _predicate_evaluation(predicate, "INVALID_OPERAND", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)
    result: ValidationPredicateResult = (
        "TRUE" if value.value.value == predicate.expected_term_ref else "FALSE"
    )
    return _predicate_evaluation(predicate, result, operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)


def _decimal_equals_evaluation(
    predicate: DecimalEqualsPredicate,
    values_by_field: dict[FieldId, ValidationFieldValue],
    unit_registry: UnitRegistry,
    canonicalization_policy: CanonicalizationPolicy,
) -> ValidationPredicateEvaluation:
    if predicate.unit_registry_ref != unit_registry.registry_ref:
        return _configuration_invalid_evaluation(predicate.predicate_ref, predicate.template_id)
    value = values_by_field.get(predicate.field_id)
    if value is None:
        return _missing_evaluation(predicate, predicate.field_id)
    converted = _converted_numeric_value(value, predicate.unit_id, unit_registry, canonicalization_policy)
    if converted is None:
        return _predicate_evaluation(predicate, "INVALID_OPERAND", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)
    expected = _canonical_decimal(predicate.expected_decimal, canonicalization_policy)
    if expected is None:
        return _predicate_evaluation(predicate, "INVALID_OPERAND", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)
    result: ValidationPredicateResult = "TRUE" if converted == expected else "FALSE"
    return _predicate_evaluation(predicate, result, operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)


def _decimal_range_evaluation(
    predicate: DecimalInClosedRangePredicate,
    values_by_field: dict[FieldId, ValidationFieldValue],
    unit_registry: UnitRegistry,
    canonicalization_policy: CanonicalizationPolicy,
) -> ValidationPredicateEvaluation:
    if predicate.unit_registry_ref != unit_registry.registry_ref:
        return _configuration_invalid_evaluation(predicate.predicate_ref, predicate.template_id)
    value = values_by_field.get(predicate.field_id)
    if value is None:
        return _missing_evaluation(predicate, predicate.field_id)
    converted = _converted_numeric_value(value, predicate.unit_id, unit_registry, canonicalization_policy)
    lower = _canonical_decimal(predicate.lower_decimal, canonicalization_policy)
    upper = _canonical_decimal(predicate.upper_decimal, canonicalization_policy)
    if converted is None or lower is None or upper is None:
        return _predicate_evaluation(predicate, "INVALID_OPERAND", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)
    result: ValidationPredicateResult = "TRUE" if lower <= converted <= upper else "FALSE"
    return _predicate_evaluation(predicate, result, operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)


def _timestamp_interval_evaluation(
    predicate: TimestampInClosedIntervalPredicate,
    values_by_field: dict[FieldId, ValidationFieldValue],
) -> ValidationPredicateEvaluation:
    value = values_by_field.get(predicate.field_id)
    if value is None:
        return _missing_evaluation(predicate, predicate.field_id)
    if not isinstance(value.value, ValidationTimestampValue):
        return _predicate_evaluation(predicate, "INVALID_OPERAND", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)
    result: ValidationPredicateResult = (
        "TRUE" if predicate.start_timestamp <= value.value.value <= predicate.end_timestamp else "FALSE"
    )
    return _predicate_evaluation(predicate, result, operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)


def _unit_compatible_evaluation(
    predicate: UnitCompatiblePredicate,
    values_by_field: dict[FieldId, ValidationFieldValue],
    unit_registry: UnitRegistry,
) -> ValidationPredicateEvaluation:
    if predicate.unit_registry_ref != unit_registry.registry_ref:
        return _configuration_invalid_evaluation(predicate.predicate_ref, predicate.template_id)
    value = values_by_field.get(predicate.field_id)
    if value is None:
        return _missing_evaluation(predicate, predicate.field_id)
    if not isinstance(value.value, ValidationNumericValue):
        return _predicate_evaluation(predicate, "INVALID_OPERAND", operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)
    units = {item.unit_id: item for item in unit_registry.units}
    observed_unit = units.get(value.value.unit_id)
    expected_unit = units.get(predicate.unit_id)
    if observed_unit is None or expected_unit is None:
        result: ValidationPredicateResult = "INVALID_OPERAND"
    else:
        result = "TRUE" if observed_unit.dimension_id == expected_unit.dimension_id else "FALSE"
    return _predicate_evaluation(predicate, result, operand_refs=(value.operand_ref,), evidence_refs=value.evidence_refs)


def _all_of_evaluation(
    predicate: AllOfPredicate,
    criteria_by_ref: dict[GovernedRef, ValidationPredicate],
    values_by_field: dict[FieldId, ValidationFieldValue],
    protocol: DesignedValidationProtocol,
    unit_registry: UnitRegistry,
    canonicalization_policy: CanonicalizationPolicy,
) -> ValidationPredicateEvaluation:
    child_evaluations: list[ValidationPredicateEvaluation] = []
    for predicate_ref in predicate.predicate_refs:
        child = criteria_by_ref.get(predicate_ref)
        if child is None:
            return _configuration_invalid_evaluation(predicate.predicate_ref, predicate.template_id)
        child_evaluations.append(
            _evaluate_predicate(
                child,
                criteria_by_ref,
                values_by_field,
                protocol,
                unit_registry,
                canonicalization_policy,
            )
        )
    child_results = {item.result for item in child_evaluations}
    operand_refs = tuple(ref for item in child_evaluations for ref in item.operand_refs)
    evidence_refs = tuple(ref for item in child_evaluations for ref in item.evidence_refs)
    missing_fields = tuple(sorted({field for item in child_evaluations for field in item.missing_field_ids}))
    if "CONFIGURATION_INVALID" in child_results:
        result: ValidationPredicateResult = "CONFIGURATION_INVALID"
    elif "INVALID_OPERAND" in child_results:
        result = "INVALID_OPERAND"
    elif "FALSE" in child_results:
        result = "FALSE"
    elif "MISSING_DATA" in child_results:
        result = "MISSING_DATA"
    else:
        result = "TRUE"
    return _predicate_evaluation(
        predicate,
        result,
        missing_field_ids=missing_fields,
        operand_refs=operand_refs,
        evidence_refs=evidence_refs,
    )


def _converted_numeric_value(
    field_value: ValidationFieldValue,
    target_unit_id: UnitId,
    unit_registry: UnitRegistry,
    canonicalization_policy: CanonicalizationPolicy,
) -> Decimal | None:
    if not isinstance(field_value.value, ValidationNumericValue):
        return None
    converted = convert_numeric_value(
        NumericValue(
            kind="NUMERIC",
            value=field_value.value.value,
            unit_id=field_value.value.unit_id,
        ),
        target_unit_id,
        unit_registry,
        canonicalization_policy,
    )
    if not isinstance(converted, NumericValue):
        return None
    return _canonical_decimal(converted.value, canonicalization_policy)


def _canonical_decimal(value: CanonicalDecimal, policy: CanonicalizationPolicy) -> Decimal | None:
    try:
        return Decimal(canonical_decimal(value, policy))
    except CanonicalizationError:
        return None


def _predicate_evaluation(
    predicate: PredicateBase,
    result: ValidationPredicateResult,
    *,
    missing_field_ids: tuple[FieldId, ...] = (),
    operand_refs: tuple[GovernedRef, ...] = (),
    evidence_refs: tuple[GovernedRef, ...] = (),
) -> ValidationPredicateEvaluation:
    return ValidationPredicateEvaluation(
        predicate_ref=predicate.predicate_ref,
        template_id=predicate.template_id,
        result=result,
        missing_field_ids=missing_field_ids,
        operand_refs=operand_refs,
        evidence_refs=evidence_refs,
    )


def _missing_evaluation(
    predicate: PredicateBase,
    field_id: FieldId,
) -> ValidationPredicateEvaluation:
    return _predicate_evaluation(predicate, "MISSING_DATA", missing_field_ids=(field_id,))


def _configuration_invalid_evaluation(
    predicate_ref: GovernedRef,
    template_id: OpaqueId,
) -> ValidationPredicateEvaluation:
    return ValidationPredicateEvaluation(
        predicate_ref=predicate_ref,
        template_id=template_id,
        result="CONFIGURATION_INVALID",
        missing_field_ids=(),
        operand_refs=(),
        evidence_refs=(),
    )


def _terminal_state(
    root_evaluation: ValidationPredicateEvaluation,
    evaluations: tuple[ValidationPredicateEvaluation, ...],
    required_field_ids: tuple[FieldId, ...],
    values_by_field: dict[FieldId, ValidationFieldValue],
) -> ProtocolTerminalState:
    results = {item.result for item in evaluations}
    if "CONFIGURATION_INVALID" in results or "INVALID_OPERAND" in results:
        return "INVALID_PROTOCOL_EXECUTION"
    if any(field_id not in values_by_field for field_id in required_field_ids):
        return "NOT_VALIDATED"
    if root_evaluation.result == "TRUE":
        return "VALIDATED"
    return "NOT_VALIDATED"


def _created_proposal_refs(
    protocol: DesignedValidationProtocol,
    execution: DesignedValidationExecutionInput,
    terminal_state: ProtocolTerminalState,
) -> tuple[GovernedRef, ...]:
    if terminal_state != "VALIDATED":
        return ()
    if not execution.requested_created_proposal_refs:
        return ()
    if execution.observation_ref is not None:
        if not protocol.allows_observation_promotion:
            return ()
        if execution.output_target_record_type not in protocol.allowed_output_target_record_types:
            return ()
    return execution.requested_created_proposal_refs


def _invalid_execution_authority(
    protocol: DesignedValidationProtocol,
    execution: DesignedValidationExecutionInput,
) -> bool:
    if execution.executor_role_id != protocol.executor_role_id:
        return True
    if execution.reviewer_role_id != protocol.reviewer_role_id:
        return True
    if execution.authority_policy_ref != protocol.authority_policy_ref:
        return True
    return (
        execution.claimed_executor_actor_ref == execution.claimed_reviewer_actor_ref
        and not protocol.same_actor_allowed
    )


def _invalid_observation_promotion_request(
    protocol: DesignedValidationProtocol,
    execution: DesignedValidationExecutionInput,
    terminal_state: ProtocolTerminalState,
) -> bool:
    if terminal_state != "VALIDATED":
        return False
    if not execution.requested_created_proposal_refs or execution.observation_ref is None:
        return False
    return (
        not protocol.allows_observation_promotion
        or execution.output_target_record_type not in protocol.allowed_output_target_record_types
    )


def _duplicate_field_ids(values: tuple[ValidationFieldValue, ...]) -> tuple[FieldId, ...]:
    seen: set[FieldId] = set()
    duplicates: set[FieldId] = set()
    for value in values:
        if value.field_id in seen:
            duplicates.add(value.field_id)
        seen.add(value.field_id)
    return tuple(sorted(duplicates))


def _evaluation_key(evaluation: ValidationPredicateEvaluation) -> tuple[str, str]:
    return _ref_key(evaluation.predicate_ref)


def _replace_evaluation(
    evaluations: tuple[ValidationPredicateEvaluation, ...],
    replacement: ValidationPredicateEvaluation,
) -> tuple[ValidationPredicateEvaluation, ...]:
    return tuple(
        sorted(
            (
                replacement if item.predicate_ref == replacement.predicate_ref else item
                for item in evaluations
            ),
            key=_evaluation_key,
        )
    )


def _sort_refs(value: object, field_name: str) -> object:
    if not isinstance(value, dict) or field_name not in value:
        return value
    return _sort_ref_mapping(dict(value), field_name)


def _sort_ref_mapping(value: dict[str, object], field_name: str) -> dict[str, object]:
    if field_name not in value:
        return value
    normalized = dict(value)
    normalized[field_name] = sorted_unique_refs(
        tuple(cast(Sequence[GovernedRef], normalized[field_name]))
    )
    return normalized


def _validate_unique_sorted(values: tuple[object, ...], label: str) -> None:
    keys = tuple(str(item) for item in values)
    if keys != tuple(sorted(set(keys))):
        raise ValueError(f"validation protocol {label} must be unique and sorted")


def _validate_ref_order(refs: tuple[GovernedRef, ...], label: str) -> None:
    keys = tuple(_ref_key(item) for item in refs)
    if keys != tuple(sorted(set(keys))):
        raise ValueError(f"validation protocol {label} must be unique and sorted")


def _ref_key(ref: GovernedRef) -> tuple[str, str]:
    return (ref.logical_id, ref.version_id)


def _ref_value_key(value: object, field_name: str) -> tuple[str, str]:
    ref = _field_value(value, field_name)
    if isinstance(ref, GovernedRef):
        return _ref_key(ref)
    if isinstance(ref, dict):
        return (str(ref["logical_id"]), str(ref["version_id"]))
    raise ValueError("validation protocol reference values must be model or mapping values")


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, BaseModel):
        return getattr(value, field_name)
    if isinstance(value, dict):
        return value[field_name]
    raise ValueError("validation protocol values must be model or mapping values")
