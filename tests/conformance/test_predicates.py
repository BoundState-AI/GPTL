from __future__ import annotations

from decimal import Decimal
from itertools import product

import pytest
from pydantic import ValidationError

from gptl.mie.predicates import (
    ApplicabilityError,
    ApplicabilityTruth,
    ContextValue,
    EqualityComparison,
    NumericValue,
    OrderedComparison,
    Predicate,
    PredicateConfigurationError,
    PresenceComparison,
    evaluate_applicability,
    sorted_predicates,
    validate_predicate_configuration,
)
from gptl.slice2_fixture import (
    FIELD_ENVIRONMENT,
    FIELD_MODE,
    FIELD_TEMPERATURE,
    MODE_PRODUCTION,
    UNIT_CELSIUS,
    UNIT_KELVIN,
    UNIT_MM,
    candidate_pack,
    canonicalization_policy,
    governed_ref,
)


def _temperature(value: str, unit_id: str = UNIT_CELSIUS) -> ContextValue:
    return ContextValue(
        value_id=f"value.temperature.{value}.{unit_id}",
        field_id=FIELD_TEMPERATURE,
        value=NumericValue(kind="NUMERIC", value=Decimal(value), unit_id=unit_id),
        evidence_refs=(governed_ref("evidence.temperature"),),
    )


def _evaluate(
    predicate: Predicate,
    context_values: tuple[ContextValue, ...] = (),
) -> tuple[ApplicabilityTruth, ApplicabilityError | None]:
    pack = candidate_pack()
    result = evaluate_applicability(
        predicate,
        governed_ref("predicate.test"),
        context_values,
        pack.field_registry,
        pack.unit_registry,
        canonicalization_policy(),
    )
    return result.truth, result.error_code


def _leaf(truth: ApplicabilityTruth) -> Predicate:
    if truth == ApplicabilityTruth.TRUE:
        field_id = FIELD_TEMPERATURE
        op = "present"
    elif truth == ApplicabilityTruth.FALSE:
        field_id = FIELD_TEMPERATURE
        op = "absent"
    elif truth == ApplicabilityTruth.UNKNOWN:
        field_id = FIELD_ENVIRONMENT
        op = "present"
    else:
        field_id = "field.not-registered"
        op = "present"
    return Predicate(
        kind="comparison",
        comparison=PresenceComparison(op=op, field_id=field_id),
    )


def _distinct_leaf(truth: ApplicabilityTruth) -> Predicate:
    return Predicate(kind="not", term=Predicate(kind="not", term=_leaf(truth)))


def _all_precedence(value: ApplicabilityTruth) -> int:
    return {
        ApplicabilityTruth.FALSE: 0,
        ApplicabilityTruth.UNKNOWN: 1,
        ApplicabilityTruth.TRUE: 2,
        ApplicabilityTruth.INVALID: 3,
    }[value]


def _any_precedence(value: ApplicabilityTruth) -> int:
    return {
        ApplicabilityTruth.TRUE: 0,
        ApplicabilityTruth.UNKNOWN: 1,
        ApplicabilityTruth.FALSE: 2,
        ApplicabilityTruth.INVALID: 3,
    }[value]


@pytest.mark.parametrize(
    "kind,left,right,expected",
    tuple(
        (kind, left, right, expected)
        for kind in ("all", "any")
        for left, right in product(ApplicabilityTruth, repeat=2)
        for expected in (
            ApplicabilityTruth.INVALID
            if ApplicabilityTruth.INVALID in (left, right)
            else (
                min((left, right), key=_all_precedence)
                if kind == "all"
                else min((left, right), key=_any_precedence)
            ),
        )
    ),
)
def test_logical_truth_tables_are_exhaustive(
    kind: str,
    left: ApplicabilityTruth,
    right: ApplicabilityTruth,
    expected: ApplicabilityTruth,
) -> None:
    predicate = Predicate(
        kind=kind,
        terms=sorted_predicates(_leaf(left), _distinct_leaf(right)),
    )

    truth, _ = _evaluate(predicate, (_temperature("25"),))

    assert truth == expected


@pytest.mark.parametrize(
    "truth,expected",
    (
        (ApplicabilityTruth.TRUE, ApplicabilityTruth.FALSE),
        (ApplicabilityTruth.FALSE, ApplicabilityTruth.TRUE),
        (ApplicabilityTruth.UNKNOWN, ApplicabilityTruth.UNKNOWN),
        (ApplicabilityTruth.INVALID, ApplicabilityTruth.INVALID),
    ),
)
def test_not_truth_table_is_exhaustive(
    truth: ApplicabilityTruth,
    expected: ApplicabilityTruth,
) -> None:
    predicate = Predicate(kind="not", term=_leaf(truth))

    actual, _ = _evaluate(predicate, (_temperature("25"),))

    assert actual == expected


def test_missing_registered_field_is_unknown_with_no_evidence() -> None:
    predicate = Predicate(
        kind="comparison",
        comparison=PresenceComparison(op="present", field_id=FIELD_ENVIRONMENT),
    )
    pack = candidate_pack()

    result = evaluate_applicability(
        predicate,
        governed_ref("predicate.missing"),
        (),
        pack.field_registry,
        pack.unit_registry,
        canonicalization_policy(),
    )

    assert result.truth == ApplicabilityTruth.UNKNOWN
    assert result.missing_field_ids == (FIELD_ENVIRONMENT,)
    assert result.evidence_refs == ()


@pytest.mark.parametrize(
    "value,low_bound,high_bound,expected",
    (
        ("20", "INCLUSIVE", "INCLUSIVE", ApplicabilityTruth.TRUE),
        ("20", "EXCLUSIVE", "INCLUSIVE", ApplicabilityTruth.FALSE),
        ("30", "INCLUSIVE", "INCLUSIVE", ApplicabilityTruth.TRUE),
        ("30", "INCLUSIVE", "EXCLUSIVE", ApplicabilityTruth.FALSE),
    ),
)
def test_range_boundaries_are_explicit(
    value: str,
    low_bound: str,
    high_bound: str,
    expected: ApplicabilityTruth,
) -> None:
    predicate = Predicate.model_validate(
        {
            "kind": "comparison",
            "comparison": {
                "op": "range",
                "field_id": FIELD_TEMPERATURE,
                "operand": {
                    "low": Decimal("20"),
                    "high": Decimal("30"),
                    "unit_id": UNIT_CELSIUS,
                    "low_bound": low_bound,
                    "high_bound": high_bound,
                },
            },
        }
    )

    truth, _ = _evaluate(predicate, (_temperature(value),))

    assert truth == expected


def test_snapshot_bound_unit_conversion_is_used_for_comparison() -> None:
    predicate = Predicate(
        kind="comparison",
        comparison=EqualityComparison(
            op="eq",
            field_id=FIELD_TEMPERATURE,
            operand=NumericValue(
                kind="NUMERIC",
                value=Decimal("298.15"),
                unit_id=UNIT_KELVIN,
            ),
        ),
    )

    truth, error = _evaluate(predicate, (_temperature("25"),))

    assert truth == ApplicabilityTruth.TRUE
    assert error is None


def test_incompatible_runtime_unit_is_invalid() -> None:
    predicate = Predicate(
        kind="comparison",
        comparison=OrderedComparison(
            op="gt",
            field_id=FIELD_TEMPERATURE,
            operand=NumericValue(kind="NUMERIC", value=Decimal("1"), unit_id=UNIT_MM),
        ),
    )

    truth, error = _evaluate(predicate, (_temperature("25"),))

    assert truth == ApplicabilityTruth.INVALID
    assert error == ApplicabilityError.UNIT_MISMATCH


def test_numeric_policy_overflow_is_invalid_instead_of_escaping_evaluation() -> None:
    predicate = Predicate(
        kind="comparison",
        comparison=OrderedComparison(
            op="gt",
            field_id=FIELD_TEMPERATURE,
            operand=NumericValue(
                kind="NUMERIC",
                value=Decimal("9999999999999999999"),
                unit_id=UNIT_CELSIUS,
            ),
        ),
    )

    truth, error = _evaluate(predicate, (_temperature("25"),))

    assert truth == ApplicabilityTruth.INVALID
    assert error == ApplicabilityError.TYPE_MISMATCH


def test_incompatible_declared_unit_fails_pack_validation() -> None:
    pack = candidate_pack()
    predicate = Predicate(
        kind="comparison",
        comparison=OrderedComparison(
            op="gt",
            field_id=FIELD_TEMPERATURE,
            operand=NumericValue(kind="NUMERIC", value=Decimal("1"), unit_id=UNIT_MM),
        ),
    )

    with pytest.raises(PredicateConfigurationError, match="incompatible"):
        validate_predicate_configuration(predicate, pack.field_registry, pack.unit_registry)


@pytest.mark.parametrize(
    "payload,error",
    (
        (
            {"kind": "all", "terms": []},
            "logical predicate has an invalid shape",
        ),
        (
            {
                "kind": "comparison",
                "comparison": {
                    "op": "in",
                    "field_id": FIELD_MODE,
                    "allowed_terms": [],
                },
            },
            "membership terms cannot be empty",
        ),
        (
            {
                "kind": "comparison",
                "comparison": {
                    "op": "in",
                    "field_id": FIELD_MODE,
                    "allowed_terms": [MODE_PRODUCTION, MODE_PRODUCTION],
                },
            },
            "membership terms must be unique",
        ),
        (
            {
                "kind": "comparison",
                "comparison": {
                    "op": "range",
                    "field_id": FIELD_TEMPERATURE,
                    "operand": {
                        "low": Decimal("30"),
                        "high": Decimal("20"),
                        "unit_id": UNIT_CELSIUS,
                        "low_bound": "INCLUSIVE",
                        "high_bound": "INCLUSIVE",
                    },
                },
            },
            "range low cannot exceed high",
        ),
    ),
)
def test_malformed_closed_ast_is_rejected(payload: object, error: str) -> None:
    with pytest.raises(ValidationError, match=error):
        Predicate.model_validate(payload)
