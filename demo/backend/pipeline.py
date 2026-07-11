"""
Module: Firewall Demo Pipeline Harness
Purpose: Live GPTL Build 1 firewall demo — runs the REAL governed capture pipeline.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False

This is a demo harness, NOT part of the packaged engine (``src/gptl``). It builds
governed records from a user scenario and runs the actual Slice 4/7 pipeline
(``evaluate_active_values`` -> ``evaluate_capture_gate`` -> ``assemble_build0_bridge_request``)
so the frontend can show a value being ratified *through* — or blocked *at* — the
Build 0 Tier 1 firewall. RESEARCH_ONLY; nothing leaves the process, no persistence.

The demo exposes three honest levers that map to real gate behaviour:
  * ``ratified``            — no ratification event => ADVISORY_GAP (missing ratification)
  * ``independent_review``  — author self-ratifies => FAIL_CLOSED (separation of duties)
  * ``proposal_method``     — MODEL_ASSISTED earns no privilege; outcome is identical
"""

from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from gptl.core.build0_bridge import (
    Build0SnapshotBinding,
    BridgeCallerIds,
    CaptureGateResult,
    assemble_build0_bridge_request,
    evaluate_capture_gate,
)
from gptl.core.proposal_ratification import (
    ACTIVE_VALUE_RESOLVER_POLICY_RECORD_TYPE,
    ACTIVE_VALUE_RESOLVER_POLICY_SCHEMA_VERSION,
    ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
    ACTOR_RECORD_RECORD_TYPE,
    ACTOR_RECORD_SCHEMA_VERSION,
    AUTHORITY_POLICY_RECORD_TYPE,
    AUTHORITY_POLICY_SCHEMA_VERSION,
    AUTHORIZATION_EVENT_RECORD_TYPE,
    AUTHORIZATION_EVENT_SCHEMA_VERSION,
    HASH_ALGORITHM,
    PROPOSAL_RATIFICATION_RECORD_TYPE,
    PROPOSAL_RATIFICATION_SCHEMA_VERSION,
    RATIFY_PROPOSAL_ACTION_ID,
    ROLE_ASSIGNMENT_RECORD_TYPE,
    ROLE_ASSIGNMENT_SCHEMA_VERSION,
    ActiveValueResolutionResult,
    ActiveValueResolverPolicy,
    ActorRecord,
    AuthorityPermission,
    AuthorityPolicy,
    AuthorizationEvent,
    ProposalRatificationEvent,
    RoleAssignmentEvent,
    evaluate_active_values,
    proposed_value_hash,
)
from gptl.core.proposals import HASH_ALGORITHM as PROPOSAL_HASH_ALGORITHM
from gptl.core.proposals import (
    TYPED_VALUE_PROPOSAL_RECORD_TYPE,
    TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
    ProposalTarget,
    TypedValueProposal,
    finalize_typed_value_proposal,
)
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import LogicalId, TermId, VersionId
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-07-01T12:00:00.000Z"
SINCE = "2026-06-01T00:00:00.000Z"
SOURCE_RAW_HASH = "a" * 64
PROPOSER = "gptl.demo.actor.proposer"
REVIEWER = "gptl.demo.actor.reviewer"
REVIEWER_ROLE = "role.materials-reviewer"
SPECIMEN_RECORD_TYPE = "record.material-specimen"

ProposalMethod = Literal["MANUAL_TRANSLATION", "MODEL_ASSISTED", "DETERMINISTIC_PARSER"]

# Friendly, honest one-line explanations keyed by the gate's real reason id.
_REASON_TEXT: dict[str, str] = {
    "build1.bridge.missing-ratification": (
        "No human ratification exists for this value, so it is held as an advisory gap "
        "and never bound into Build 0 Tier 1."
    ),
    "build1.bridge.integrity-failure": (
        "The ratification failed the authority / separation-of-duties gate — the author "
        "cannot ratify their own proposal — so no active value was produced."
    ),
    "build1.bridge.active-value-conflict": (
        "Two ratified values compete for the same target; the bridge fails closed rather "
        "than guess."
    ),
    "build1.bridge.capture-ready": (
        "A single, independently ratified value crossed into Build 0 Tier 1 with full "
        "provenance."
    ),
}


def _ref(logical_id: str) -> GovernedRef:
    """Deterministic governed reference (mirrors the Build 1 test ref factory)."""
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v1"),
        version_number=1,
        content_hash=hashlib.sha256(f"fixture:{logical_id}:v1".encode()).hexdigest(),
    )


class PipelineScenario(BaseModel):
    """User-controlled inputs for one firewall run."""

    model_config = ConfigDict(extra="forbid")

    field_name: str = Field(default="hardness", min_length=1, max_length=64)
    unit_id: str = Field(default="unit.hrc", min_length=1, max_length=64)
    value: str = Field(default="41.2500", min_length=1, max_length=32)
    proposal_method: ProposalMethod = "MANUAL_TRANSLATION"
    ratified: bool = True
    independent_review: bool = True

    @field_validator("value")
    @classmethod
    def _value_is_decimal(cls, raw: str) -> str:
        try:
            Decimal(raw)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("value must be a decimal number") from exc
        return raw


class Stage(BaseModel):
    key: str
    title: str
    status: str
    summary: str
    record_type: str | None = None
    record: dict[str, Any] | None = None


class PipelineResult(BaseModel):
    verdict: Literal["PASSED", "BLOCKED"]
    verdict_reason: str
    gate_status: str
    gate_reason_id: str | None = None
    crossed_firewall: bool
    stages: list[Stage]


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - input guard
        raise ValueError(f"value {value!r} is not a valid decimal") from exc


def _dump(record: Any) -> dict[str, Any]:
    return record.model_dump(mode="json")


def _proposal(scenario: PipelineScenario) -> TypedValueProposal:
    policy = canonicalization_policy()
    target_ref = _ref("gptl.demo.target.specimen-1")
    proposal = TypedValueProposal.model_validate(
        {
            "schema_version": TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
            "record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
            "hash_algorithm": PROPOSAL_HASH_ALGORITHM,
            "proposal_ref": _ref("gptl.demo.proposal.value"),
            "canonicalization_policy_ref": _ref("gptl.demo.canonicalization.policy"),
            "evidence_scope_ref": _ref("gptl.demo.scope.candidate"),
            "source_artifact_ref": _ref("gptl.demo.source.shift-note"),
            "source_raw_byte_hash": SOURCE_RAW_HASH,
            "identity": {
                "identity_mode": "EXISTING_GOVERNED_REF",
                "target_ref": target_ref,
            },
            "claimed_proposer_ref": _ref(PROPOSER),
            "proposal_method": scenario.proposal_method,
            "creation_event_ref": _ref("gptl.demo.proposal.creation-event"),
            "target": ProposalTarget.model_validate(
                {
                    "target_record_type": SPECIMEN_RECORD_TYPE,
                    "target_logical_id": target_ref.logical_id,
                    "target_schema_version": "schema.specimen.v1",
                    "semantic_field_path": f"field.{scenario.field_name}",
                    "context_key": {"side": "side.left", "replicate": 1},
                }
            ),
            "proposed_value": {
                "kind": "NUMERIC",
                "value": _decimal(scenario.value),
                "unit_id": scenario.unit_id,
            },
            "evidence_location": {
                "locator_class": "RAW_BYTE_RANGE",
                "source_artifact_ref": _ref("gptl.demo.source.shift-note"),
                "start_byte": 0,
                "end_byte": 5,
                "raw_byte_hash": SOURCE_RAW_HASH,
            },
            "validation_state": "READY_FOR_RATIFICATION",
        },
        context={"canonicalization_policy": policy},
    )
    return finalize_typed_value_proposal(proposal, policy)


def _ratification(proposal: TypedValueProposal, ratifier: str) -> ProposalRatificationEvent:
    policy = canonicalization_policy()
    return ProposalRatificationEvent.model_validate(
        {
            "schema_version": PROPOSAL_RATIFICATION_SCHEMA_VERSION,
            "record_type": PROPOSAL_RATIFICATION_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "ratification_event_ref": _ref("gptl.demo.ratification.event"),
            "canonicalization_policy_ref": _ref("gptl.demo.canonicalization.policy"),
            "proposal_ref": proposal.proposal_ref,
            "proposal_content_hash": proposal.proposal_ref.content_hash,
            "proposed_value_hash": proposed_value_hash(proposal, policy),
            "ratifying_actor_ref": _ref(ratifier),
            "ratifying_role_id": REVIEWER_ROLE,
            "authority_policy_ref": _ref("gptl.demo.authority.policy"),
            "authorization_event_ref": _ref(f"gptl.demo.authorization.{ratifier}"),
            "decision": "RATIFIED",
            "effective_at": AS_OF,
            "recorded_at": AS_OF,
            "evidence_refs": (_ref("gptl.demo.evidence.review"),),
            "claimed_proposer_ref": _ref(PROPOSER),
            "claimed_ratifier_ref": _ref(ratifier),
        },
        context={"canonicalization_policy": policy},
    )


def _actor(actor_id: str) -> ActorRecord:
    policy = canonicalization_policy()
    return ActorRecord.model_validate(
        {
            "schema_version": ACTOR_RECORD_SCHEMA_VERSION,
            "record_type": ACTOR_RECORD_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "actor_ref": _ref(actor_id),
            "canonicalization_policy_ref": _ref("gptl.demo.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "effective_at": SINCE,
            "recorded_at": SINCE,
            "evidence_refs": (_ref("gptl.demo.evidence.actor-registry"),),
        },
        context={"canonicalization_policy": policy},
    )


def _authority_policy() -> AuthorityPolicy:
    policy = canonicalization_policy()
    return AuthorityPolicy.model_validate(
        {
            "schema_version": AUTHORITY_POLICY_SCHEMA_VERSION,
            "record_type": AUTHORITY_POLICY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "policy_ref": _ref("gptl.demo.authority.policy"),
            "canonicalization_policy_ref": _ref("gptl.demo.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "effective_at": SINCE,
            "actor_refs": (_ref(PROPOSER), _ref(REVIEWER)),
            "permissions": (
                AuthorityPermission(
                    role_id=TermId(REVIEWER_ROLE),
                    action_id=RATIFY_PROPOSAL_ACTION_ID,
                    scope_ref=_ref("gptl.demo.scope.candidate"),
                    target_record_types=(TermId(SPECIMEN_RECORD_TYPE),),
                    same_actor_allowed=False,
                ),
            ),
            "evidence_refs": (_ref("gptl.demo.evidence.authority-policy"),),
        },
        context={"canonicalization_policy": policy},
    )


def _role_assignment(actor_id: str) -> RoleAssignmentEvent:
    policy = canonicalization_policy()
    return RoleAssignmentEvent.model_validate(
        {
            "schema_version": ROLE_ASSIGNMENT_SCHEMA_VERSION,
            "record_type": ROLE_ASSIGNMENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "assignment_ref": _ref(f"gptl.demo.role-assignment.{actor_id}"),
            "actor_ref": _ref(actor_id),
            "role_id": REVIEWER_ROLE,
            "authority_policy_ref": _ref("gptl.demo.authority.policy"),
            "scope_ref": _ref("gptl.demo.scope.candidate"),
            "state": "ACTIVE",
            "effective_at": SINCE,
            "recorded_at": SINCE,
            "evidence_refs": (_ref("gptl.demo.evidence.role-assignment"),),
        },
        context={"canonicalization_policy": policy},
    )


def _authorization(actor_id: str) -> AuthorizationEvent:
    policy = canonicalization_policy()
    return AuthorizationEvent.model_validate(
        {
            "schema_version": AUTHORIZATION_EVENT_SCHEMA_VERSION,
            "record_type": AUTHORIZATION_EVENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "authorization_ref": _ref(f"gptl.demo.authorization.{actor_id}"),
            "actor_ref": _ref(actor_id),
            "role_id": REVIEWER_ROLE,
            "action_id": RATIFY_PROPOSAL_ACTION_ID,
            "authority_policy_ref": _ref("gptl.demo.authority.policy"),
            "scope_ref": _ref("gptl.demo.scope.candidate"),
            "target_record_type": SPECIMEN_RECORD_TYPE,
            "state": "ACTIVE",
            "effective_at": SINCE,
            "recorded_at": SINCE,
            "evidence_refs": (_ref("gptl.demo.evidence.authorization"),),
        },
        context={"canonicalization_policy": policy},
    )


def _resolver_policy() -> ActiveValueResolverPolicy:
    policy = canonicalization_policy()
    return ActiveValueResolverPolicy.model_validate(
        {
            "schema_version": ACTIVE_VALUE_RESOLVER_POLICY_SCHEMA_VERSION,
            "record_type": ACTIVE_VALUE_RESOLVER_POLICY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "resolver_policy_ref": _ref("gptl.demo.active-value-resolver.policy"),
            "canonicalization_policy_ref": _ref("gptl.demo.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "algorithm_id": ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
            "evidence_refs": (_ref("gptl.demo.evidence.active-resolver"),),
        },
        context={"canonicalization_policy": policy},
    )


def _caller_ids() -> BridgeCallerIds:
    return BridgeCallerIds(
        run_id="run.gptl.demo",
        decision_id="decision.gptl.demo",
        case_id="case.gptl.demo",
        audit_event_id="audit.gptl.demo",
        snapshot_id="snapshot.gptl.demo",
        replay_id="replay.gptl.demo",
    )


def _snapshot_binding() -> Build0SnapshotBinding:
    policy = canonicalization_policy()
    return Build0SnapshotBinding.model_validate(
        {
            "snapshot_id": _caller_ids().snapshot_id,
            "as_of_time": AS_OF,
            "pack_ref": _ref("gptl.demo.build0.pack.mie"),
            "engine_policy_ref": _ref("gptl.demo.build0.engine-policy.mie"),
            "evidence_scope_ref": _ref("gptl.demo.scope.candidate"),
            "algorithm_refs": (_ref("gptl.demo.build0.algorithm.route"),),
            "unit_registry_ref": _ref("gptl.demo.build0.unit-registry"),
            "field_registry_ref": _ref("gptl.demo.build0.field-registry"),
            "canonicalization_policy_ref": _ref("gptl.demo.canonicalization.policy"),
            "serialization_policy_ref": _ref("gptl.demo.build0.serialization-policy"),
            "lexical_policy_ref": _ref("gptl.demo.build0.lexical-policy"),
        },
        context={"canonicalization_policy": policy},
    )


def _active_values(
    proposal: TypedValueProposal,
    events: tuple[ProposalRatificationEvent, ...],
    ratifier: str,
) -> ActiveValueResolutionResult:
    return evaluate_active_values(
        (proposal,),
        events,
        (_actor(PROPOSER), _actor(REVIEWER)),
        _authority_policy(),
        (_role_assignment(ratifier),),
        (_authorization(ratifier),),
        _resolver_policy(),
        _ref("gptl.demo.scope.candidate"),
        AS_OF,
        canonicalization_policy(),
    )


def _capture_gate(
    active_values: ActiveValueResolutionResult, proposal: TypedValueProposal
) -> CaptureGateResult:
    return evaluate_capture_gate(
        gate_ref=_ref("gptl.demo.bridge.capture-gate"),
        canonicalization_policy_ref=_ref("gptl.demo.canonicalization.policy"),
        active_values=active_values,
        proposals=(proposal,),
        observations=(),
        capability_status="SUPPORTED",
        parser_status="PARSER_READY",
        validation_protocol_status="NOT_REQUESTED",
        scope_status="COMPATIBLE",
        authority_status="ELIGIBLE",
        identity_status="RESOLVED",
        context_key_status="DEFINED",
        evidence_locator_status="RATIFIABLE",
        build0_canonicalization_policy_ref=_ref("gptl.demo.canonicalization.policy"),
        as_of_time=AS_OF,
        canonicalization_policy=canonicalization_policy(),
    )


def run_pipeline(scenario: PipelineScenario) -> PipelineResult:
    """Run the real Build 1 capture pipeline for one scenario and return a stage trace."""
    policy = canonicalization_policy()
    ratifier = REVIEWER if scenario.independent_review else PROPOSER

    proposal = _proposal(scenario)
    events: tuple[ProposalRatificationEvent, ...] = ()
    ratification: ProposalRatificationEvent | None = None
    if scenario.ratified:
        ratification = _ratification(proposal, ratifier)
        events = (ratification,)

    active_values = _active_values(proposal, events, ratifier)
    gate = _capture_gate(active_values, proposal)

    request = None
    if gate.status == "BUILD0_REQUEST_READY":
        request = assemble_build0_bridge_request(
            request_ref=_ref("gptl.demo.bridge.request"),
            caller_ids=_caller_ids(),
            capture_gate=gate,
            snapshot_binding=_snapshot_binding(),
            canonicalization_policy=policy,
        )

    crossed = request is not None and len(gate.bound_value_rows) > 0
    verdict = "PASSED" if crossed else "BLOCKED"
    reason_id = str(gate.reason_id) if gate.reason_id is not None else None
    verdict_reason = _REASON_TEXT.get(
        reason_id or "",
        "The value crossed into Build 0 Tier 1 with full provenance."
        if crossed
        else "The value was held before Build 0 Tier 1.",
    )

    if active_values.status != "RESOLVED":
        active_summary = (
            "Resolution failed the authority / separation-of-duties gate; no active value "
            "was produced."
        )
    elif active_values.active_proposal_refs:
        active_summary = (
            "One independently ratified value is active and eligible to cross the firewall."
        )
    else:
        active_summary = "No ratified value is active — there is nothing to bind."

    stages: list[Stage] = [
        Stage(
            key="source",
            title="Source artifact",
            status="CAPTURED",
            summary=f"An observation of {scenario.field_name} is captured as a governed source.",
            record_type="SOURCE_ARTIFACT_REF",
            record=_dump(_ref("gptl.demo.source.shift-note")),
        ),
        Stage(
            key="proposal",
            title="Typed proposal",
            status="READY_FOR_RATIFICATION",
            summary=(
                f"{scenario.value} {scenario.unit_id} proposed via "
                f"{scenario.proposal_method.replace('_', ' ').lower()}; carries no confidence score."
            ),
            record_type=proposal.record_type,
            record=_dump(proposal),
        ),
        Stage(
            key="ratification",
            title="Human ratification gate",
            status="RATIFIED" if ratification is not None else "ABSENT",
            summary=(
                (
                    "Ratified by an independent reviewer (author is not the reviewer)."
                    if scenario.independent_review
                    else "Author attempts to ratify their own proposal (separation-of-duties)."
                )
                if ratification is not None
                else "No ratification event was submitted."
            ),
            record_type=ratification.record_type if ratification is not None else None,
            record=_dump(ratification) if ratification is not None else None,
        ),
        Stage(
            key="active_value",
            title="Active-value resolution",
            status=active_values.status,
            summary=active_summary,
            record_type="ACTIVE_VALUE_RESOLUTION",
            record=_dump(active_values),
        ),
        Stage(
            key="firewall",
            title="Build 0 Tier 1 firewall",
            status=gate.status,
            summary=verdict_reason,
            record_type="CAPTURE_GATE_RESULT",
            record=_dump(gate),
        ),
    ]
    if request is not None:
        stages.append(
            Stage(
                key="build0",
                title="Build 0 Tier 1 bound value",
                status="BOUND",
                summary=(
                    f"{len(gate.bound_value_rows)} bound value row crossed the firewall "
                    "with immutable provenance."
                ),
                record_type="BUILD0_BRIDGE_REQUEST",
                record=_dump(request),
            )
        )

    return PipelineResult(
        verdict=verdict,
        verdict_reason=verdict_reason,
        gate_status=gate.status,
        gate_reason_id=reason_id,
        crossed_firewall=crossed,
        stages=stages,
    )
