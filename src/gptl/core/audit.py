"""
Module: Audit Events
Purpose: Typed append-only audit events.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalTimestamp,
    NonNegativeInt,
    OpaqueId,
    Sha256Hex,
    TermId,
)


class PreflightRefusalAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_id: OpaqueId
    run_id: OpaqueId
    sequence: NonNegativeInt
    event_type_id: TermId
    decision_hash: Sha256Hex
    requested_pack_id: OpaqueId | None
    refusal_type: Literal["PACK_VERSION_UNAVAILABLE"]
    display_registry_ref: GovernedRef
    display_template_ref: GovernedRef
    as_of_time: CanonicalTimestamp
    context_kind: Literal["PREFLIGHT"]


class SnapshotDecisionAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_id: OpaqueId
    run_id: OpaqueId
    sequence: NonNegativeInt
    event_type_id: TermId
    output_kind: Literal["TIER1_DECISION", "TIER2_ADVISORY"]
    output_hash: Sha256Hex
    snapshot_hash: Sha256Hex
    as_of_time: CanonicalTimestamp
    context_kind: Literal["SNAPSHOT_BOUND"]
