from __future__ import annotations

from decimal import Decimal

import pytest

from gptl.mie.selection import (
    SelectableRecord,
    SelectionBinding,
    SelectionConfigurationError,
    selected_record_refs,
    validate_selection_configuration,
)
from gptl.slice2_fixture import governed_ref


def _record(
    logical_id: str,
    record_kind: str = "FAILURE_MODE",
    scope: str | None = None,
    group: str | None = None,
    rank: str | None = None,
) -> SelectableRecord:
    binding = None
    if group is not None and rank is not None:
        binding = SelectionBinding(
            selection_group_ref=governed_ref(group),
            precedence_rank=Decimal(rank),
        )
    return SelectableRecord.model_validate(
        {
            "record_ref": governed_ref(logical_id),
            "record_kind": record_kind,
            "overlap_scope_id": scope or f"scope.{logical_id}",
            "selection_binding": binding,
        }
    )


def test_selection_preserves_distinct_ungrouped_records_and_group_winner() -> None:
    records = (
        _record("failure.a"),
        _record("failure.b"),
        _record("failure.group-high", group="group.shared", rank="2"),
        _record("failure.group-low", group="group.shared", rank="1"),
    )

    validate_selection_configuration(records)
    selected = selected_record_refs(records)

    assert tuple(item.logical_id for item in selected) == (
        "failure.a",
        "failure.b",
        "failure.group-low",
    )


def test_selection_group_rank_tie_is_invalid_configuration() -> None:
    records = (
        _record("failure.a", group="group.shared", rank="1"),
        _record("failure.b", group="group.shared", rank="1"),
    )

    with pytest.raises(SelectionConfigurationError, match="precedence-rank tie"):
        validate_selection_configuration(records)


def test_overlapping_ungrouped_msa_records_are_invalid_configuration() -> None:
    records = (
        _record("msa.a", "MSA_STUDY", scope="scope.overlap"),
        _record("msa.b", "MSA_STUDY", scope="scope.overlap"),
    )

    with pytest.raises(SelectionConfigurationError, match="explicit selection group"):
        validate_selection_configuration(records)
