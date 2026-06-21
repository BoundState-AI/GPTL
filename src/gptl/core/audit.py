"""Typed append-only audit events for Slice 1."""

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
