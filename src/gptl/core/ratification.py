"""Immutable intake provenance and snapshot-bound ratification gates."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    FieldId,
    OpaqueId,
    Sha256Hex,
    VersionId,
)
from gptl.mie.predicates import ScalarValue


class RatificationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_ref: GovernedRef
    value_id: OpaqueId
    field_id: FieldId
    value_hash: Sha256Hex
    source_ref: GovernedRef
    actor_id: OpaqueId
    governing_pack_ref: GovernedRef
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    supersedes_version_id: VersionId | None

    @model_validator(mode="after")
    def validate_state(self) -> RatificationEvent:
        if self.state != "ACTIVE" and self.supersedes_version_id is None:
            raise ValueError("terminal ratification state requires superseded version")
        return self


class IntakeValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    value_id: OpaqueId
    field_id: FieldId
    value: ScalarValue
    value_hash: Sha256Hex
    source_kind: Literal["INSTRUMENT_EMITTED", "HUMAN_SUPPLIED"]
    source_ref: GovernedRef
    ratification_event_ref: GovernedRef | None

    @model_validator(mode="after")
    def validate_provenance_shape(self) -> IntakeValue:
        if self.source_kind == "INSTRUMENT_EMITTED":
            if self.ratification_event_ref is not None:
                raise ValueError("instrument value cannot carry a ratification event")
        elif self.ratification_event_ref is None:
            raise ValueError("human value requires a ratification event reference")
        return self


class IntakeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    intake_ref: GovernedRef
    values: tuple[IntakeValue, ...]

    @model_validator(mode="after")
    def validate_value_order(self) -> IntakeRecord:
        keys = tuple((item.field_id, item.value_id) for item in self.values)
        if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
            raise ValueError("intake values must be unique and sorted")
        field_ids = tuple(item.field_id for item in self.values)
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("scalar intake fields cannot have multiple values")
        return self


class RatificationGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    eligible: bool
    admitted_values: tuple[IntakeValue, ...]
    unratified_field_ids: tuple[FieldId, ...]
    evidence_refs: tuple[GovernedRef, ...]
    active_state_hash: Sha256Hex


def evaluate_ratification_gate(
    intake: IntakeRecord,
    events: tuple[RatificationEvent, ...],
    pack_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
    policy: CanonicalizationPolicy,
) -> RatificationGateResult:
    events_by_ref = {
        (event.event_ref.logical_id, event.event_ref.version_id): event for event in events
    }
    admitted: list[IntakeValue] = []
    unratified: set[FieldId] = set()
    evidence: list[GovernedRef] = []
    active_event_refs: list[GovernedRef] = []
    for value in intake.values:
        evidence.append(value.source_ref)
        if value.source_kind == "INSTRUMENT_EMITTED":
            admitted.append(value)
            continue
        event_ref = value.ratification_event_ref
        event = (
            events_by_ref.get((event_ref.logical_id, event_ref.version_id))
            if event_ref is not None
            else None
        )
        if event is None or not _event_matches(value, event, pack_ref, as_of_time):
            unratified.add(value.field_id)
            continue
        superseded = any(
            _event_supersedes(value, event, candidate, pack_ref, as_of_time) for candidate in events
        )
        if superseded:
            unratified.add(value.field_id)
            continue
        admitted.append(value)
        active_event_refs.append(event.event_ref)
        evidence.append(event.event_ref)
    unratified_field_ids = tuple(sorted(unratified))
    ordered_active_refs = tuple(
        sorted(
            active_event_refs,
            key=lambda item: (item.logical_id, item.version_id),
        )
    )
    return RatificationGateResult(
        eligible=not unratified and len(admitted) == len(intake.values),
        admitted_values=tuple(admitted),
        unratified_field_ids=unratified_field_ids,
        evidence_refs=sorted_unique_refs(tuple(evidence)),
        active_state_hash=canonical_sha256(
            {
                "as_of_time": as_of_time,
                "governing_pack_ref": pack_ref,
                "active_event_refs": ordered_active_refs,
                "unratified_field_ids": unratified_field_ids,
            },
            policy,
        ),
    )


def intake_value_hash(
    field_id: FieldId,
    value: ScalarValue,
    policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(
        {"field_id": field_id, "value": value},
        policy,
    )


def _event_matches(
    value: IntakeValue,
    event: RatificationEvent,
    pack_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
) -> bool:
    return (
        event.state == "ACTIVE"
        and event.event_ref == value.ratification_event_ref
        and event.value_id == value.value_id
        and event.field_id == value.field_id
        and event.value_hash == value.value_hash
        and event.source_ref == value.source_ref
        and event.governing_pack_ref == pack_ref
        and event.effective_at <= as_of_time
    )


def _event_supersedes(
    value: IntakeValue,
    active_event: RatificationEvent,
    candidate: RatificationEvent,
    pack_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
) -> bool:
    return (
        candidate.supersedes_version_id == active_event.event_ref.version_id
        and candidate.event_ref.logical_id == active_event.event_ref.logical_id
        and candidate.value_id == value.value_id
        and candidate.field_id == value.field_id
        and candidate.value_hash == value.value_hash
        and candidate.source_ref == value.source_ref
        and candidate.governing_pack_ref == pack_ref
        and candidate.effective_at <= as_of_time
    )
