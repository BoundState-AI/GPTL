"""Immutable knowledge-snapshot binding."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.ratification import RatificationEvent
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    OpaqueId,
    Sha256Hex,
)


class KnowledgeSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    snapshot_id: OpaqueId
    schema_version: Literal["gptl.snapshot.v1"]
    as_of_time: CanonicalTimestamp
    hash_algorithm: Literal["SHA-256"]
    pack_ref: GovernedRef
    engine_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    algorithm_refs: tuple[GovernedRef, ...]
    unit_registry_ref: GovernedRef
    field_registry_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    serialization_policy_ref: GovernedRef
    lexical_policy_ref: GovernedRef
    ratification_state_hash: Sha256Hex
    bound_versions: tuple[GovernedRef, ...]
    ratification_events: tuple[RatificationEvent, ...]

    @model_validator(mode="after")
    def validate_order(self) -> KnowledgeSnapshot:
        _validate_ref_order(self.algorithm_refs, "algorithm_refs")
        _validate_ref_order(self.bound_versions, "bound_versions")
        event_keys = tuple(
            (event.event_ref.logical_id, event.event_ref.version_id)
            for event in self.ratification_events
        )
        if len(event_keys) != len(set(event_keys)) or event_keys != tuple(sorted(event_keys)):
            raise ValueError("ratification events must be unique and sorted")
        required = {
            (self.pack_ref.logical_id, self.pack_ref.version_id),
            (self.engine_policy_ref.logical_id, self.engine_policy_ref.version_id),
            (self.evidence_scope_ref.logical_id, self.evidence_scope_ref.version_id),
            (self.unit_registry_ref.logical_id, self.unit_registry_ref.version_id),
            (self.field_registry_ref.logical_id, self.field_registry_ref.version_id),
            (
                self.canonicalization_policy_ref.logical_id,
                self.canonicalization_policy_ref.version_id,
            ),
            (
                self.serialization_policy_ref.logical_id,
                self.serialization_policy_ref.version_id,
            ),
            (self.lexical_policy_ref.logical_id, self.lexical_policy_ref.version_id),
            *((item.logical_id, item.version_id) for item in self.algorithm_refs),
            *(
                (event.event_ref.logical_id, event.event_ref.version_id)
                for event in self.ratification_events
            ),
        }
        actual = {(item.logical_id, item.version_id) for item in self.bound_versions}
        if not required.issubset(actual):
            raise ValueError("snapshot bound versions omit a decision-effective record")
        return self


def build_snapshot(
    snapshot_id: OpaqueId,
    as_of_time: CanonicalTimestamp,
    pack_ref: GovernedRef,
    engine_policy_ref: GovernedRef,
    evidence_scope_ref: GovernedRef,
    algorithm_refs: tuple[GovernedRef, ...],
    unit_registry_ref: GovernedRef,
    field_registry_ref: GovernedRef,
    canonicalization_policy_ref: GovernedRef,
    serialization_policy_ref: GovernedRef,
    lexical_policy_ref: GovernedRef,
    ratification_state_hash: Sha256Hex,
    used_refs: tuple[GovernedRef, ...],
    ratification_events: tuple[RatificationEvent, ...],
    policy: CanonicalizationPolicy,
) -> KnowledgeSnapshot:
    all_refs = (
        pack_ref,
        engine_policy_ref,
        evidence_scope_ref,
        unit_registry_ref,
        field_registry_ref,
        canonicalization_policy_ref,
        serialization_policy_ref,
        lexical_policy_ref,
        *algorithm_refs,
        *(event.event_ref for event in ratification_events),
        *used_refs,
    )
    bound_versions = sorted_unique_refs(all_refs)
    return KnowledgeSnapshot.model_validate(
        {
            "snapshot_id": snapshot_id,
            "schema_version": "gptl.snapshot.v1",
            "as_of_time": as_of_time,
            "hash_algorithm": "SHA-256",
            "pack_ref": pack_ref,
            "engine_policy_ref": engine_policy_ref,
            "evidence_scope_ref": evidence_scope_ref,
            "algorithm_refs": sorted_unique_refs(algorithm_refs),
            "unit_registry_ref": unit_registry_ref,
            "field_registry_ref": field_registry_ref,
            "canonicalization_policy_ref": canonicalization_policy_ref,
            "serialization_policy_ref": serialization_policy_ref,
            "lexical_policy_ref": lexical_policy_ref,
            "ratification_state_hash": ratification_state_hash,
            "bound_versions": bound_versions,
            "ratification_events": tuple(
                sorted(
                    ratification_events,
                    key=lambda event: (
                        event.event_ref.logical_id,
                        event.event_ref.version_id,
                    ),
                )
            ),
        },
        context={"canonicalization_policy": policy},
    )


def snapshot_hash(
    snapshot: KnowledgeSnapshot,
    policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(snapshot, policy)


def _validate_ref_order(refs: tuple[GovernedRef, ...], label: str) -> None:
    keys = tuple((item.logical_id, item.version_id) for item in refs)
    if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
        raise ValueError(f"{label} must be unique and sorted")
