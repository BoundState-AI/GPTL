"""Closed applicability predicates and deterministic four-state evaluation."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation, localcontext
from enum import Enum
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gptl.core.canonical import CanonicalizationError, canonical_decimal
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalDecimal,
    CanonicalizationPolicy,
    FieldId,
    OpaqueId,
    TermId,
    UnitId,
)


class ApplicabilityTruth(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


class ApplicabilityError(str, Enum):
    TYPE_MISMATCH = "TYPE_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_AST = "INVALID_AST"
    INVALID_RANGE = "INVALID_RANGE"


ERROR_PRECEDENCE: Final = (
    ApplicabilityError.INVALID_AST,
    ApplicabilityError.INVALID_RANGE,
    ApplicabilityError.UNKNOWN_FIELD,
    ApplicabilityError.TYPE_MISMATCH,
    ApplicabilityError.UNIT_MISMATCH,
)
DECIMAL_OPERATION_CARRY_DIGITS: Final = 1
DECIMAL_PRODUCT_OPERAND_FACTOR: Final = 2


class NumericValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["NUMERIC"]
    value: CanonicalDecimal
    unit_id: UnitId


class EnumValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["ENUM"]
    value: TermId


ScalarValue = Annotated[NumericValue | EnumValue, Field(discriminator="kind")]


class RangeOperand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    low: CanonicalDecimal
    high: CanonicalDecimal
    unit_id: UnitId
    low_bound: Literal["INCLUSIVE", "EXCLUSIVE"]
    high_bound: Literal["INCLUSIVE", "EXCLUSIVE"]

    @model_validator(mode="after")
    def validate_range(self) -> RangeOperand:
        if self.low > self.high:
            raise ValueError("range low cannot exceed high")
        return self


class EqualityComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["eq", "neq"]
    field_id: FieldId
    operand: ScalarValue


class OrderedComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["lt", "lte", "gt", "gte"]
    field_id: FieldId
    operand: NumericValue


class MembershipComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["in"]
    field_id: FieldId
    allowed_terms: tuple[TermId, ...]

    @model_validator(mode="after")
    def validate_terms(self) -> MembershipComparison:
        if not self.allowed_terms:
            raise ValueError("membership terms cannot be empty")
        if len(self.allowed_terms) != len(set(self.allowed_terms)):
            raise ValueError("membership terms must be unique")
        if self.allowed_terms != tuple(sorted(self.allowed_terms)):
            raise ValueError("membership terms must be lexicographically sorted")
        return self


class RangeComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["range"]
    field_id: FieldId
    operand: RangeOperand


class PresenceComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["present", "absent"]
    field_id: FieldId


Comparison = Annotated[
    EqualityComparison
    | OrderedComparison
    | MembershipComparison
    | RangeComparison
    | PresenceComparison,
    Field(discriminator="op"),
]


class Predicate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["comparison", "all", "any", "not"]
    comparison: Comparison | None = None
    terms: tuple[Predicate, ...] | None = None
    term: Predicate | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> Predicate:
        if self.kind == "comparison":
            if self.comparison is None or self.terms is not None or self.term is not None:
                raise ValueError("comparison predicate has an invalid shape")
            return self
        if self.kind in {"all", "any"}:
            if not self.terms or self.comparison is not None or self.term is not None:
                raise ValueError("logical predicate has an invalid shape")
            keys = tuple(predicate_sort_key(item) for item in self.terms)
            if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
                raise ValueError("logical terms must be unique and canonically sorted")
            return self
        if self.term is None or self.comparison is not None or self.terms is not None:
            raise ValueError("not predicate has an invalid shape")
        return self


def predicate_sort_key(predicate: Predicate) -> str:
    return json.dumps(
        predicate.model_dump(mode="json", exclude_none=True),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sorted_predicates(*predicates: Predicate) -> tuple[Predicate, ...]:
    return tuple(sorted(predicates, key=predicate_sort_key))


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    field_id: FieldId
    value_kind: Literal["NUMERIC", "ENUM"]
    canonical_unit_id: UnitId | None
    allowed_terms: tuple[TermId, ...]

    @model_validator(mode="after")
    def validate_definition(self) -> FieldDefinition:
        if self.value_kind == "NUMERIC":
            if self.canonical_unit_id is None or self.allowed_terms:
                raise ValueError("numeric field definition is inconsistent")
        elif self.canonical_unit_id is not None or not self.allowed_terms:
            raise ValueError("enum field definition is inconsistent")
        if len(self.allowed_terms) != len(set(self.allowed_terms)):
            raise ValueError("allowed field terms must be unique")
        if self.allowed_terms != tuple(sorted(self.allowed_terms)):
            raise ValueError("allowed field terms must be sorted")
        return self


class FieldRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    registry_ref: GovernedRef
    fields: tuple[FieldDefinition, ...]

    @model_validator(mode="after")
    def validate_fields(self) -> FieldRegistry:
        ids = tuple(item.field_id for item in self.fields)
        if len(ids) != len(set(ids)) or ids != tuple(sorted(ids)):
            raise ValueError("field definitions must be unique and sorted")
        return self


class UnitDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    unit_id: UnitId
    dimension_id: TermId
    scale_to_base: CanonicalDecimal
    offset_to_base: CanonicalDecimal

    @model_validator(mode="after")
    def validate_scale(self) -> UnitDefinition:
        if self.scale_to_base == 0:
            raise ValueError("unit scale cannot be zero")
        return self


class UnitRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    registry_ref: GovernedRef
    units: tuple[UnitDefinition, ...]

    @model_validator(mode="after")
    def validate_units(self) -> UnitRegistry:
        ids = tuple(item.unit_id for item in self.units)
        if len(ids) != len(set(ids)) or ids != tuple(sorted(ids)):
            raise ValueError("unit definitions must be unique and sorted")
        return self


class ContextValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    value_id: OpaqueId
    field_id: FieldId
    value: ScalarValue
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence_order(self) -> ContextValue:
        keys = tuple((item.logical_id, item.version_id) for item in self.evidence_refs)
        if not keys or len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
            raise ValueError("context evidence references must be nonempty, unique, and sorted")
        return self


class ApplicabilityEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    truth: ApplicabilityTruth
    predicate_ref: GovernedRef
    missing_field_ids: tuple[FieldId, ...]
    error_code: ApplicabilityError | None
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_state(self) -> ApplicabilityEvaluation:
        if (self.truth == ApplicabilityTruth.INVALID) != (self.error_code is not None):
            raise ValueError("INVALID truth and error_code must appear together")
        if self.truth == ApplicabilityTruth.UNKNOWN:
            if not self.missing_field_ids:
                raise ValueError("UNKNOWN evaluation requires missing fields")
        elif self.missing_field_ids:
            raise ValueError("only UNKNOWN evaluation may carry missing fields")
        if self.missing_field_ids != tuple(sorted(set(self.missing_field_ids))):
            raise ValueError("missing fields must be unique and sorted")
        keys = tuple((item.logical_id, item.version_id) for item in self.evidence_refs)
        if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
            raise ValueError("evaluation evidence must be unique and sorted")
        return self


class PredicateConfigurationError(ValueError):
    pass


def validate_predicate_configuration(
    predicate: Predicate,
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
) -> None:
    fields = {item.field_id: item for item in field_registry.fields}
    units = {item.unit_id: item for item in unit_registry.units}
    _validate_predicate(predicate, fields, units)


def _validate_predicate(
    predicate: Predicate,
    fields: dict[FieldId, FieldDefinition],
    units: dict[UnitId, UnitDefinition],
) -> None:
    if predicate.kind == "comparison":
        if predicate.comparison is None:
            raise PredicateConfigurationError("comparison predicate is malformed")
        _validate_comparison(predicate.comparison, fields, units)
        return
    if predicate.kind == "not":
        if predicate.term is None:
            raise PredicateConfigurationError("not predicate is malformed")
        _validate_predicate(predicate.term, fields, units)
        return
    if not predicate.terms:
        raise PredicateConfigurationError("logical predicate is empty")
    for term in predicate.terms:
        _validate_predicate(term, fields, units)


def _validate_comparison(
    comparison: Comparison,
    fields: dict[FieldId, FieldDefinition],
    units: dict[UnitId, UnitDefinition],
) -> None:
    definition = fields.get(comparison.field_id)
    if definition is None:
        raise PredicateConfigurationError("predicate references an unknown field")
    if isinstance(comparison, PresenceComparison):
        return
    if isinstance(comparison, MembershipComparison):
        if definition.value_kind != "ENUM" or not set(comparison.allowed_terms).issubset(
            definition.allowed_terms
        ):
            raise PredicateConfigurationError("membership predicate is incompatible with field")
        return
    if isinstance(comparison, EqualityComparison):
        operand = comparison.operand
        if operand.kind != definition.value_kind:
            raise PredicateConfigurationError("equality operand type does not match field")
        if isinstance(operand, EnumValue):
            if operand.value not in definition.allowed_terms:
                raise PredicateConfigurationError("enum operand is outside the field vocabulary")
            return
        _validate_numeric_unit(definition, operand.unit_id, units)
        return
    if definition.value_kind != "NUMERIC":
        raise PredicateConfigurationError("numeric predicate targets a nonnumeric field")
    if isinstance(comparison, OrderedComparison):
        _validate_numeric_unit(definition, comparison.operand.unit_id, units)
        return
    if isinstance(comparison, RangeComparison):
        _validate_numeric_unit(definition, comparison.operand.unit_id, units)
        return
    raise PredicateConfigurationError("comparison operator is unsupported")


def _validate_numeric_unit(
    definition: FieldDefinition,
    operand_unit_id: UnitId,
    units: dict[UnitId, UnitDefinition],
) -> None:
    if definition.canonical_unit_id is None:
        raise PredicateConfigurationError("numeric field has no canonical unit")
    canonical_unit = units.get(definition.canonical_unit_id)
    operand_unit = units.get(operand_unit_id)
    if canonical_unit is None or operand_unit is None:
        raise PredicateConfigurationError("predicate references an unknown unit")
    if canonical_unit.dimension_id != operand_unit.dimension_id:
        raise PredicateConfigurationError("predicate unit is incompatible with field")


class _EvaluationState(BaseModel):
    model_config = ConfigDict(frozen=True)
    truth: ApplicabilityTruth
    missing: tuple[FieldId, ...] = ()
    error: ApplicabilityError | None = None
    evidence: tuple[GovernedRef, ...] = ()


def evaluate_applicability(
    predicate: Predicate,
    predicate_ref: GovernedRef,
    context_values: tuple[ContextValue, ...],
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
    policy: CanonicalizationPolicy,
) -> ApplicabilityEvaluation:
    values = {item.field_id: item for item in context_values}
    fields = {item.field_id: item for item in field_registry.fields}
    units = {item.unit_id: item for item in unit_registry.units}
    state = _evaluate(predicate, values, fields, units, policy)
    return ApplicabilityEvaluation(
        truth=state.truth,
        predicate_ref=predicate_ref,
        missing_field_ids=tuple(sorted(set(state.missing))),
        error_code=state.error,
        evidence_refs=_sort_refs(state.evidence),
    )


def _evaluate(
    predicate: Predicate,
    values: dict[FieldId, ContextValue],
    fields: dict[FieldId, FieldDefinition],
    units: dict[UnitId, UnitDefinition],
    policy: CanonicalizationPolicy,
) -> _EvaluationState:
    if predicate.kind == "comparison":
        if predicate.comparison is None:
            return _invalid(ApplicabilityError.INVALID_AST)
        return _evaluate_comparison(predicate.comparison, values, fields, units, policy)
    if predicate.kind == "not":
        if predicate.term is None:
            return _invalid(ApplicabilityError.INVALID_AST)
        state = _evaluate(predicate.term, values, fields, units, policy)
        truth = {
            ApplicabilityTruth.TRUE: ApplicabilityTruth.FALSE,
            ApplicabilityTruth.FALSE: ApplicabilityTruth.TRUE,
            ApplicabilityTruth.UNKNOWN: ApplicabilityTruth.UNKNOWN,
            ApplicabilityTruth.INVALID: ApplicabilityTruth.INVALID,
        }[state.truth]
        return state.model_copy(update={"truth": truth})
    if not predicate.terms:
        return _invalid(ApplicabilityError.INVALID_AST)
    states = tuple(_evaluate(item, values, fields, units, policy) for item in predicate.terms)
    return _combine(predicate.kind, states)


def _evaluate_comparison(
    comparison: Comparison,
    values: dict[FieldId, ContextValue],
    fields: dict[FieldId, FieldDefinition],
    units: dict[UnitId, UnitDefinition],
    policy: CanonicalizationPolicy,
) -> _EvaluationState:
    definition = fields.get(comparison.field_id)
    if definition is None:
        return _invalid(ApplicabilityError.UNKNOWN_FIELD)
    observed = values.get(comparison.field_id)
    if observed is None:
        return _EvaluationState(
            truth=ApplicabilityTruth.UNKNOWN,
            missing=(comparison.field_id,),
        )
    evidence = observed.evidence_refs
    if isinstance(comparison, PresenceComparison):
        truth = comparison.op == "present"
        return _boolean_state(truth, evidence)
    if observed.value.kind != definition.value_kind:
        return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
    if isinstance(comparison, MembershipComparison):
        if not isinstance(observed.value, EnumValue):
            return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
        if observed.value.value not in definition.allowed_terms:
            return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
        return _boolean_state(observed.value.value in comparison.allowed_terms, evidence)
    if isinstance(comparison, EqualityComparison):
        return _evaluate_equality(comparison, observed, definition, units, policy)
    if not isinstance(observed.value, NumericValue):
        return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
    if isinstance(comparison, OrderedComparison):
        pair = _numeric_pair(observed.value, comparison.operand, units, policy)
        if isinstance(pair, ApplicabilityError):
            return _invalid(pair, evidence)
        left, right = pair
        truth = {
            "lt": left < right,
            "lte": left <= right,
            "gt": left > right,
            "gte": left >= right,
        }[comparison.op]
        return _boolean_state(truth, evidence)
    if comparison.operand.low > comparison.operand.high:
        return _invalid(ApplicabilityError.INVALID_RANGE, evidence)
    low_pair = _numeric_pair(
        observed.value,
        NumericValue(
            kind="NUMERIC",
            value=comparison.operand.low,
            unit_id=comparison.operand.unit_id,
        ),
        units,
        policy,
    )
    high_pair = _numeric_pair(
        observed.value,
        NumericValue(
            kind="NUMERIC",
            value=comparison.operand.high,
            unit_id=comparison.operand.unit_id,
        ),
        units,
        policy,
    )
    if isinstance(low_pair, ApplicabilityError):
        return _invalid(low_pair, evidence)
    if isinstance(high_pair, ApplicabilityError):
        return _invalid(high_pair, evidence)
    value, low = low_pair
    _, high = high_pair
    lower = value >= low if comparison.operand.low_bound == "INCLUSIVE" else value > low
    upper = value <= high if comparison.operand.high_bound == "INCLUSIVE" else value < high
    return _boolean_state(lower and upper, evidence)


def _evaluate_equality(
    comparison: EqualityComparison,
    observed: ContextValue,
    definition: FieldDefinition,
    units: dict[UnitId, UnitDefinition],
    policy: CanonicalizationPolicy,
) -> _EvaluationState:
    evidence = observed.evidence_refs
    if observed.value.kind != comparison.operand.kind:
        return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
    if isinstance(observed.value, EnumValue) and isinstance(comparison.operand, EnumValue):
        if observed.value.value not in definition.allowed_terms:
            return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
        equal = observed.value.value == comparison.operand.value
    elif isinstance(observed.value, NumericValue) and isinstance(comparison.operand, NumericValue):
        pair = _numeric_pair(observed.value, comparison.operand, units, policy)
        if isinstance(pair, ApplicabilityError):
            return _invalid(pair, evidence)
        equal = pair[0] == pair[1]
    else:
        return _invalid(ApplicabilityError.TYPE_MISMATCH, evidence)
    return _boolean_state(equal if comparison.op == "eq" else not equal, evidence)


def _numeric_pair(
    left: NumericValue,
    right: NumericValue,
    units: dict[UnitId, UnitDefinition],
    policy: CanonicalizationPolicy,
) -> tuple[Decimal, Decimal] | ApplicabilityError:
    left_unit = units.get(left.unit_id)
    right_unit = units.get(right.unit_id)
    if left_unit is None or right_unit is None:
        return ApplicabilityError.UNIT_MISMATCH
    if left_unit.dimension_id != right_unit.dimension_id:
        return ApplicabilityError.UNIT_MISMATCH
    try:
        left_value = Decimal(canonical_decimal(left.value, policy))
        right_value = Decimal(canonical_decimal(right.value, policy))
        left_scale = Decimal(canonical_decimal(left_unit.scale_to_base, policy))
        right_scale = Decimal(canonical_decimal(right_unit.scale_to_base, policy))
        left_offset = Decimal(canonical_decimal(left_unit.offset_to_base, policy))
        right_offset = Decimal(canonical_decimal(right_unit.offset_to_base, policy))
        with localcontext() as context:
            context.prec = (
                DECIMAL_PRODUCT_OPERAND_FACTOR
                * (policy.decimal_max_integer_digits + policy.decimal_scale)
                + DECIMAL_OPERATION_CARRY_DIGITS
            )
            left_base = left_value * left_scale + left_offset
            right_base = right_value * right_scale + right_offset
        return (
            Decimal(canonical_decimal(left_base, policy)),
            Decimal(canonical_decimal(right_base, policy)),
        )
    except (CanonicalizationError, InvalidOperation):
        return ApplicabilityError.TYPE_MISMATCH


def _combine(kind: str, states: tuple[_EvaluationState, ...]) -> _EvaluationState:
    evidence = _sort_refs(tuple(ref for state in states for ref in state.evidence))
    errors = tuple(state.error for state in states if state.error is not None)
    if errors:
        error = min(errors, key=ERROR_PRECEDENCE.index)
        return _invalid(error, evidence)
    missing = tuple(sorted({field for state in states for field in state.missing}))
    truths = {state.truth for state in states}
    if kind == "all":
        if ApplicabilityTruth.FALSE in truths:
            return _EvaluationState(truth=ApplicabilityTruth.FALSE, evidence=evidence)
        if ApplicabilityTruth.UNKNOWN in truths:
            return _EvaluationState(
                truth=ApplicabilityTruth.UNKNOWN,
                missing=missing,
                evidence=evidence,
            )
        return _EvaluationState(truth=ApplicabilityTruth.TRUE, evidence=evidence)
    if ApplicabilityTruth.TRUE in truths:
        return _EvaluationState(truth=ApplicabilityTruth.TRUE, evidence=evidence)
    if ApplicabilityTruth.UNKNOWN in truths:
        return _EvaluationState(
            truth=ApplicabilityTruth.UNKNOWN,
            missing=missing,
            evidence=evidence,
        )
    return _EvaluationState(truth=ApplicabilityTruth.FALSE, evidence=evidence)


def _invalid(
    error: ApplicabilityError,
    evidence: tuple[GovernedRef, ...] = (),
) -> _EvaluationState:
    return _EvaluationState(
        truth=ApplicabilityTruth.INVALID,
        error=error,
        evidence=_sort_refs(evidence),
    )


def _boolean_state(
    value: bool,
    evidence: tuple[GovernedRef, ...],
) -> _EvaluationState:
    return _EvaluationState(
        truth=ApplicabilityTruth.TRUE if value else ApplicabilityTruth.FALSE,
        evidence=_sort_refs(evidence),
    )


def _sort_refs(refs: tuple[GovernedRef, ...]) -> tuple[GovernedRef, ...]:
    return sorted_unique_refs(refs)
