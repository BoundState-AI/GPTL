"""
Module: Governed Pack Records
Purpose: Slice 2 governed pack, policy, and candidate records.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import EvidenceLocator, FieldId, TermId
from gptl.mie.predicates import FieldRegistry, Predicate, UnitRegistry
from gptl.mie.selection import SelectionBinding, SelectionGroupRecord


class EnginePolicyManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    applicability_algorithm_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    serialization_policy_ref: GovernedRef
    lexical_policy_ref: GovernedRef
    field_registry_ref: GovernedRef
    unit_registry_ref: GovernedRef
    required_intake_field_ids: tuple[FieldId, ...]

    @model_validator(mode="after")
    def validate_required_fields(self) -> EnginePolicyManifest:
        if not self.required_intake_field_ids:
            raise ValueError("engine policy requires explicit intake fields")
        if self.required_intake_field_ids != tuple(sorted(set(self.required_intake_field_ids))):
            raise ValueError("required intake fields must be unique and sorted")
        return self


class FailureModeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    failure_mode_ref: GovernedRef
    method_ref: GovernedRef
    mechanism_id: TermId
    overlap_scope_id: TermId
    predicate_ref: GovernedRef
    predicate_record_type_id: TermId
    predicate_evidence_location: EvidenceLocator
    applicability_predicate: Predicate
    selection_binding: SelectionBinding | None
    evidence_refs: tuple[GovernedRef, ...]
    lifecycle: Literal["PUBLISHED"]

    @model_validator(mode="after")
    def validate_evidence(self) -> FailureModeRecord:
        keys = tuple((item.logical_id, item.version_id) for item in self.evidence_refs)
        if not keys or len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
            raise ValueError("failure-mode evidence must be nonempty, unique, and sorted")
        return self


class AuthorityPackManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    pack_ref: GovernedRef
    computation_type: Literal["DIAGNOSTIC"]
    lifecycle: Literal["PUBLISHED"]
    fixture_class: Literal["SYNTHETIC", "REFERENCE"]
    method_ref: GovernedRef
    engine_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    candidate_refs: tuple[GovernedRef, ...]
    selection_group_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_refs(self) -> AuthorityPackManifest:
        if not self.candidate_refs:
            raise ValueError("published pack candidate set cannot be empty")
        _validate_ref_order(self.candidate_refs, "candidate_refs")
        _validate_ref_order(self.selection_group_refs, "selection_group_refs")
        return self


class CandidatePack(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    manifest: AuthorityPackManifest
    engine_policy: EnginePolicyManifest
    field_registry: FieldRegistry
    unit_registry: UnitRegistry
    candidates: tuple[FailureModeRecord, ...]
    selection_groups: tuple[SelectionGroupRecord, ...]

    @model_validator(mode="after")
    def validate_manifest_bindings(self) -> CandidatePack:
        candidate_refs = tuple(item.failure_mode_ref for item in self.candidates)
        _validate_ref_order(candidate_refs, "candidate records")
        if candidate_refs != self.manifest.candidate_refs:
            raise ValueError("pack manifest candidate refs do not match candidate records")
        group_refs = tuple(item.group_ref for item in self.selection_groups)
        _validate_ref_order(group_refs, "selection groups")
        if group_refs != self.manifest.selection_group_refs:
            raise ValueError("pack manifest selection refs do not match group records")
        if self.engine_policy.policy_ref != self.manifest.engine_policy_ref:
            raise ValueError("pack manifest engine policy ref mismatch")
        if self.field_registry.registry_ref != self.engine_policy.field_registry_ref:
            raise ValueError("engine policy field registry ref mismatch")
        if self.unit_registry.registry_ref != self.engine_policy.unit_registry_ref:
            raise ValueError("engine policy unit registry ref mismatch")
        if any(item.method_ref != self.manifest.method_ref for item in self.candidates):
            raise ValueError("candidate method ref does not match pack method")
        known_groups = {(item.logical_id, item.version_id) for item in group_refs}
        if any(
            item.selection_binding is not None
            and (
                item.selection_binding.selection_group_ref.logical_id,
                item.selection_binding.selection_group_ref.version_id,
            )
            not in known_groups
            for item in self.candidates
        ):
            raise ValueError("candidate references an unknown selection group")
        return self


def _validate_ref_order(refs: tuple[GovernedRef, ...], label: str) -> None:
    keys = tuple((item.logical_id, item.version_id) for item in refs)
    if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
        raise ValueError(f"{label} must be unique and sorted")
