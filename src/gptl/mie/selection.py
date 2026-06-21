"""Scoped candidate selection without cross-mechanism competition."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.directives import DisplayDirective
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import CanonicalDecimal, TermId


class SelectionBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    selection_group_ref: GovernedRef
    precedence_rank: CanonicalDecimal


class SelectionGroupRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    group_ref: GovernedRef
    rationale: DisplayDirective
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> SelectionGroupRecord:
        keys = tuple((item.logical_id, item.version_id) for item in self.evidence_refs)
        if not keys or len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
            raise ValueError("selection-group evidence must be nonempty, unique, and sorted")
        return self


class SelectableRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_ref: GovernedRef
    record_kind: Literal["FAILURE_MODE", "MSA_STUDY"]
    overlap_scope_id: TermId
    selection_binding: SelectionBinding | None


class SelectionConfigurationError(ValueError):
    pass


def validate_selection_configuration(records: tuple[SelectableRecord, ...]) -> None:
    grouped_ranks: dict[tuple[str, str], set[CanonicalDecimal]] = {}
    msa_scopes: dict[TermId, list[SelectableRecord]] = {}
    for record in records:
        binding = record.selection_binding
        if binding is not None:
            key = (
                binding.selection_group_ref.logical_id,
                binding.selection_group_ref.version_id,
            )
            ranks = grouped_ranks.setdefault(key, set())
            if binding.precedence_rank in ranks:
                raise SelectionConfigurationError("selection group has a precedence-rank tie")
            ranks.add(binding.precedence_rank)
        if record.record_kind == "MSA_STUDY":
            msa_scopes.setdefault(record.overlap_scope_id, []).append(record)
    for records_in_scope in msa_scopes.values():
        if len(records_in_scope) < 2:
            continue
        groups = {
            (
                item.selection_binding.selection_group_ref.logical_id,
                item.selection_binding.selection_group_ref.version_id,
            )
            for item in records_in_scope
            if item.selection_binding is not None
        }
        if len(groups) != 1 or any(item.selection_binding is None for item in records_in_scope):
            raise SelectionConfigurationError(
                "overlapping MSA studies require one explicit selection group"
            )


def selected_record_refs(records: tuple[SelectableRecord, ...]) -> tuple[GovernedRef, ...]:
    ungrouped: list[GovernedRef] = []
    grouped: dict[tuple[str, str], list[SelectableRecord]] = {}
    for record in records:
        binding = record.selection_binding
        if binding is None:
            ungrouped.append(record.record_ref)
            continue
        key = (
            binding.selection_group_ref.logical_id,
            binding.selection_group_ref.version_id,
        )
        grouped.setdefault(key, []).append(record)
    selected = list(ungrouped)
    for alternatives in grouped.values():
        winner = min(alternatives, key=_selection_key)
        selected.append(winner.record_ref)
    return sorted_unique_refs(tuple(selected))


def _selection_key(record: SelectableRecord) -> tuple[CanonicalDecimal, str, str]:
    binding = record.selection_binding
    if binding is None:
        raise SelectionConfigurationError("grouped candidate is missing its binding")
    return (
        binding.precedence_rank,
        record.record_ref.logical_id,
        record.record_ref.version_id,
    )
