"""Deterministic Slice 1 safe-refusal use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from gptl.core.audit import PreflightRefusalAuditEvent
from gptl.core.canonical import canonical_sha256
from gptl.core.directives import DisplayDirective, DisplayTemplateRegistry
from gptl.core.pack_registry import ExactPackRegistry
from gptl.core.persistence import PostgresRunStore
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    OpaqueId,
    TermId,
)
from gptl.mie.schema import RefusalDecision, RefusalType, Tier1Output


class PackAvailableForLaterSlice(RuntimeError):
    pass


class SafeRefusalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: OpaqueId
    decision_id: OpaqueId
    case_id: OpaqueId
    audit_event_id: OpaqueId
    requested_pack_id: OpaqueId
    as_of_time: CanonicalTimestamp


class SafeRefusalPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    canonicalization_policy: CanonicalizationPolicy
    operational_mode: Literal["RESEARCH_ONLY"]
    engine_id: OpaqueId
    engine_version: OpaqueId
    failure_stage_id: TermId
    audit_event_type_id: TermId
    required_human_action: DisplayDirective
    display_registry: DisplayTemplateRegistry

    def model_post_init(self, __context: object) -> None:
        self.display_registry.validate_directive(self.required_human_action)


@dataclass(frozen=True)
class SafeRefusalResult:
    output: Tier1Output
    audit_events: tuple[PreflightRefusalAuditEvent, ...]


def build_safe_refusal(
    request: SafeRefusalRequest,
    pack_registry: ExactPackRegistry,
    policy: SafeRefusalPolicy,
) -> SafeRefusalResult:
    # A present pack cannot truthfully produce PACK_VERSION_UNAVAILABLE, while
    # executing it here would claim authority assigned to Slice 2.
    if pack_registry.contains_exact(request.requested_pack_id):
        raise PackAvailableForLaterSlice(
            "requested pack exists; execution is implemented by a later slice"
        )
    policy.display_registry.validate_directive(policy.required_human_action)
    display_template = next(
        template
        for template in policy.display_registry.templates
        if template.template_id == policy.required_human_action.template_id
    )
    validation_context = {"canonicalization_policy": policy.canonicalization_policy}
    decision = RefusalDecision.model_validate(
        {
            "decision_id": request.decision_id,
            "case_id": request.case_id,
            "tier": 1,
            "dispositional": False,
            "non_record_of_record": True,
            "operational_mode": policy.operational_mode,
            "engine_id": policy.engine_id,
            "engine_version": policy.engine_version,
            "as_of_time": request.as_of_time,
            "verdict": "REFUSED",
            "refusal_type": RefusalType.PACK_VERSION_UNAVAILABLE,
            "context": {
                "context_kind": "PREFLIGHT",
                "requested_pack_id": request.requested_pack_id,
                "failure_stage_id": policy.failure_stage_id,
            },
            "method_ref": None,
            "assessments": (),
            "citations": (),
            "missing_field_ids": (),
            "required_human_action": policy.required_human_action,
            "audit_event_ids": (request.audit_event_id,),
        },
        context=validation_context,
    )
    decision_hash = canonical_sha256(decision, policy.canonicalization_policy)
    output = Tier1Output.model_validate(
        {
            "output_kind": "TIER1_DECISION",
            "decision": decision,
            "decision_hash": decision_hash,
        },
        context=validation_context,
    )
    audit_event = PreflightRefusalAuditEvent.model_validate(
        {
            "event_id": request.audit_event_id,
            "run_id": request.run_id,
            "sequence": 0,
            "event_type_id": policy.audit_event_type_id,
            "decision_hash": decision_hash,
            "requested_pack_id": request.requested_pack_id,
            "refusal_type": RefusalType.PACK_VERSION_UNAVAILABLE,
            "display_registry_ref": policy.display_registry.registry_ref,
            "display_template_ref": display_template.template_ref,
            "as_of_time": request.as_of_time,
            "context_kind": "PREFLIGHT",
        },
        context=validation_context,
    )
    return SafeRefusalResult(output=output, audit_events=(audit_event,))


def execute_safe_refusal(
    request: SafeRefusalRequest,
    pack_registry: ExactPackRegistry,
    policy: SafeRefusalPolicy,
    store: PostgresRunStore,
) -> SafeRefusalResult:
    result = build_safe_refusal(request, pack_registry, policy)
    store.persist_preflight_run(request.run_id, result.output, result.audit_events)
    return result
