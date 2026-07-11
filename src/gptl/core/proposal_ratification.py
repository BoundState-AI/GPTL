"""
Module: Proposal Ratification
Purpose: Build 1 proposal ratification and active-value resolution.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.proposals import (
    TypedValueProposal,
    active_value_key_payload,
    typed_value_proposal_content_hash,
)
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    Sha256Hex,
    TermId,
)

PROPOSAL_RATIFICATION_SCHEMA_VERSION: Final = "gptl.build1.proposal-ratification.v1"
PROPOSAL_RATIFICATION_RECORD_TYPE: Final = "PROPOSAL_RATIFICATION_EVENT"
AUTHORITY_POLICY_SCHEMA_VERSION: Final = "gptl.build1.authority-policy.v1"
AUTHORITY_POLICY_RECORD_TYPE: Final = "AUTHORITY_POLICY"
ROLE_ASSIGNMENT_SCHEMA_VERSION: Final = "gptl.build1.role-assignment.v1"
ROLE_ASSIGNMENT_RECORD_TYPE: Final = "ROLE_ASSIGNMENT_EVENT"
AUTHORIZATION_EVENT_SCHEMA_VERSION: Final = "gptl.build1.authorization-event.v1"
AUTHORIZATION_EVENT_RECORD_TYPE: Final = "AUTHORIZATION_EVENT"
ACTIVE_VALUE_RESOLVER_POLICY_SCHEMA_VERSION: Final = (
    "gptl.build1.active-value-resolver-policy.v1"
)
ACTIVE_VALUE_RESOLVER_POLICY_RECORD_TYPE: Final = "ACTIVE_VALUE_RESOLVER_POLICY"
ACTOR_RECORD_SCHEMA_VERSION: Final = "gptl.build1.actor-record.v1"
ACTOR_RECORD_RECORD_TYPE: Final = "ACTOR_RECORD"
HASH_ALGORITHM: Final = "SHA-256"
ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID: Final = "ACTIVE_VALUE_STATE_HASH_V1"
RATIFY_PROPOSAL_ACTION_ID: Final = TermId("build1.action.ratify-proposal")

ACTIVE_VALUE_RESOLVED_REASON_ID: Final = TermId("build1.active-value.resolved")
ACTIVE_VALUE_CONFLICT_REASON_ID: Final = TermId("build1.active-value.conflict")
AUTHORITY_INELIGIBLE_REASON_ID: Final = TermId("build1.authority.ineligible")
RATIFICATION_INTEGRITY_FAILURE_REASON_ID: Final = TermId(
    "build1.ratification.integrity-failure"
)
PROPOSAL_HASH_MISMATCH_REASON_ID: Final = TermId("build1.ratification.proposal-hash-mismatch")
PROPOSAL_NOT_READY_REASON_ID: Final = TermId("build1.ratification.proposal-not-ready")


class ActorRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.actor-record.v1"]
    record_type: Literal["ACTOR_RECORD"]
    hash_algorithm: Literal["SHA-256"]
    actor_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    expires_at: CanonicalTimestamp | None = None
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_evidence_refs(value)

    @model_validator(mode="after")
    def validate_evidence(self) -> ActorRecord:
        if self.expires_at is not None and self.expires_at <= self.effective_at:
            raise ValueError("actor record expiration must be after effective time")
        if not self.evidence_refs:
            raise ValueError("actor record requires evidence references")
        return self


class AuthorityPermission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role_id: TermId
    action_id: TermId
    scope_ref: GovernedRef
    target_record_types: tuple[TermId, ...]
    same_actor_allowed: bool

    @model_validator(mode="before")
    @classmethod
    def sort_target_record_types(cls, value: object) -> object:
        if not isinstance(value, dict) or "target_record_types" not in value:
            return value
        normalized = dict(value)
        normalized["target_record_types"] = tuple(sorted(normalized["target_record_types"]))
        return normalized

    @model_validator(mode="after")
    def validate_targets(self) -> AuthorityPermission:
        if not self.target_record_types:
            raise ValueError("authority permission requires target record types")
        if self.target_record_types != tuple(sorted(set(self.target_record_types))):
            raise ValueError("authority permission target types must be unique and sorted")
        return self


class AuthorityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.authority-policy.v1"]
    record_type: Literal["AUTHORITY_POLICY"]
    hash_algorithm: Literal["SHA-256"]
    policy_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    effective_at: CanonicalTimestamp
    expires_at: CanonicalTimestamp | None = None
    actor_refs: tuple[GovernedRef, ...]
    permissions: tuple[AuthorityPermission, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_policy_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "permissions" in normalized:
            normalized["permissions"] = tuple(
                sorted(
                    normalized["permissions"],
                    key=lambda item: (
                        str(_field_value(item, "role_id")),
                        str(_field_value(item, "action_id")),
                        _ref_value_key(item, "scope_ref"),
                    ),
                )
            )
        if "actor_refs" in normalized:
            normalized["actor_refs"] = sorted_unique_refs(tuple(normalized["actor_refs"]))
        return _sort_evidence_refs(normalized)

    @model_validator(mode="after")
    def validate_policy(self) -> AuthorityPolicy:
        if self.expires_at is not None and self.expires_at <= self.effective_at:
            raise ValueError("authority policy expiration must be after effective time")
        if not self.actor_refs:
            raise ValueError("authority policy requires actor references")
        actor_keys = tuple(_ref_key(item) for item in self.actor_refs)
        if actor_keys != tuple(sorted(set(actor_keys))):
            raise ValueError("authority policy actor refs must be unique and sorted")
        if not self.permissions:
            raise ValueError("authority policy requires permissions")
        if not self.evidence_refs:
            raise ValueError("authority policy requires evidence references")
        keys = tuple(
            (item.role_id, item.action_id, _ref_key(item.scope_ref)) for item in self.permissions
        )
        if keys != tuple(sorted(set(keys))):
            raise ValueError("authority permissions must be unique and sorted")
        return self


class RoleAssignmentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.role-assignment.v1"]
    record_type: Literal["ROLE_ASSIGNMENT_EVENT"]
    hash_algorithm: Literal["SHA-256"]
    assignment_ref: GovernedRef
    actor_ref: GovernedRef
    role_id: TermId
    authority_policy_ref: GovernedRef
    scope_ref: GovernedRef
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    supersedes_assignment_ref: GovernedRef | None = None
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_evidence_refs(value)

    @model_validator(mode="after")
    def validate_state(self) -> RoleAssignmentEvent:
        if self.state != "ACTIVE" and self.supersedes_assignment_ref is None:
            raise ValueError("terminal role assignment requires superseded assignment")
        if not self.evidence_refs:
            raise ValueError("role assignment requires evidence references")
        return self


class AuthorizationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.authorization-event.v1"]
    record_type: Literal["AUTHORIZATION_EVENT"]
    hash_algorithm: Literal["SHA-256"]
    authorization_ref: GovernedRef
    actor_ref: GovernedRef
    role_id: TermId
    action_id: TermId
    authority_policy_ref: GovernedRef
    scope_ref: GovernedRef
    target_record_type: TermId
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    supersedes_authorization_ref: GovernedRef | None = None
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_evidence_refs(value)

    @model_validator(mode="after")
    def validate_state(self) -> AuthorizationEvent:
        if self.state != "ACTIVE" and self.supersedes_authorization_ref is None:
            raise ValueError("terminal authorization requires superseded authorization")
        if not self.evidence_refs:
            raise ValueError("authorization event requires evidence references")
        return self


class ProposalRatificationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.proposal-ratification.v1"]
    record_type: Literal["PROPOSAL_RATIFICATION_EVENT"]
    hash_algorithm: Literal["SHA-256"]
    ratification_event_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    proposal_ref: GovernedRef
    proposal_content_hash: Sha256Hex
    proposed_value_hash: Sha256Hex
    ratifying_actor_ref: GovernedRef
    ratifying_role_id: TermId
    authority_policy_ref: GovernedRef
    authorization_event_ref: GovernedRef
    decision: Literal["RATIFIED", "REJECTED", "CORRECTION_REQUESTED", "SUPERSEDED"]
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    evidence_refs: tuple[GovernedRef, ...]
    reviewer_note: str | None = None
    supersedes_ratification_event_ref: GovernedRef | None = None
    same_actor_allowed: bool = False
    single_actor_policy_basis_ref: GovernedRef | None = None
    claimed_proposer_ref: GovernedRef | None = None
    claimed_executor_ref: GovernedRef | None = None
    claimed_ratifier_ref: GovernedRef

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_evidence_refs(value)

    @model_validator(mode="after")
    def validate_shape(self) -> ProposalRatificationEvent:
        if not self.evidence_refs:
            raise ValueError("ratification event requires evidence references")
        if self.claimed_ratifier_ref != self.ratifying_actor_ref:
            raise ValueError("claimed ratifier must match ratifying actor")
        if self.decision == "SUPERSEDED" and self.supersedes_ratification_event_ref is None:
            raise ValueError("superseded ratification requires superseded event reference")
        if self.same_actor_allowed and self.single_actor_policy_basis_ref is None:
            raise ValueError("same-actor ratification requires policy basis")
        if not self.same_actor_allowed and self.single_actor_policy_basis_ref is not None:
            raise ValueError("single-actor basis requires same_actor_allowed")
        return self


class ActiveValueResolverPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.active-value-resolver-policy.v1"]
    record_type: Literal["ACTIVE_VALUE_RESOLVER_POLICY"]
    hash_algorithm: Literal["SHA-256"]
    resolver_policy_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    algorithm_id: Literal["ACTIVE_VALUE_STATE_HASH_V1"]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        return _sort_evidence_refs(value)

    @model_validator(mode="after")
    def validate_policy(self) -> ActiveValueResolverPolicy:
        if not self.evidence_refs:
            raise ValueError("active-value resolver policy requires evidence references")
        return self


class ActiveValueTargetState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target_key: dict[str, object]
    eligible_event_refs: tuple[GovernedRef, ...]
    non_superseded_event_refs: tuple[GovernedRef, ...]
    active_ratified_event_refs: tuple[GovernedRef, ...]
    proposal_refs: tuple[GovernedRef, ...]
    proposal_content_hashes: tuple[Sha256Hex, ...]
    active_value_outcome: Literal["NO_ACTIVE_VALUE", "ONE_ACTIVE_VALUE", "ACTIVE_VALUE_CONFLICT"]
    conflicting_event_refs: tuple[GovernedRef, ...] | None = None


class ActiveValueResolutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["RESOLVED", "ACTIVE_VALUE_CONFLICT", "INTEGRITY_FAILURE"]
    reason_id: TermId
    target_states: tuple[ActiveValueTargetState, ...]
    active_value_state_hash: Sha256Hex
    active_proposal_refs: tuple[GovernedRef, ...]
    diagnostics: tuple[TermId, ...] = ()


def proposed_value_hash(
    proposal: TypedValueProposal,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(proposal.proposed_value, canonicalization_policy)


def evaluate_active_values(
    proposals: tuple[TypedValueProposal, ...],
    ratification_events: tuple[ProposalRatificationEvent, ...],
    actor_records: tuple[ActorRecord, ...],
    authority_policy: AuthorityPolicy,
    role_assignments: tuple[RoleAssignmentEvent, ...],
    authorization_events: tuple[AuthorizationEvent, ...],
    resolver_policy: ActiveValueResolverPolicy,
    scope_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> ActiveValueResolutionResult:
    proposal_by_ref = {_ref_key(proposal.proposal_ref): proposal for proposal in proposals}
    eligible: list[tuple[ProposalRatificationEvent, TypedValueProposal]] = []
    diagnostics: set[TermId] = set()
    for event in ratification_events:
        if event.recorded_at > as_of_time or event.effective_at > as_of_time:
            continue
        proposal = proposal_by_ref.get(_ref_key(event.proposal_ref))
        if proposal is None:
            diagnostics.add(PROPOSAL_HASH_MISMATCH_REASON_ID)
            continue
        issue = _event_eligibility_issue(
            event,
            proposal,
            actor_records,
            authority_policy,
            role_assignments,
            authorization_events,
            scope_ref,
            as_of_time,
            canonicalization_policy,
        )
        if issue is None:
            eligible.append((event, proposal))
        else:
            diagnostics.add(issue)

    states = _target_states(eligible, canonicalization_policy)
    state_hash = active_value_state_hash(
        states,
        resolver_policy,
        as_of_time,
        canonicalization_policy,
    )
    active_event_keys = {
        _ref_key(state.active_ratified_event_refs[0])
        for state in states
        if state.active_value_outcome == "ONE_ACTIVE_VALUE"
        and len(state.active_ratified_event_refs) == 1
    }
    active_refs = tuple(
        proposal.proposal_ref
        for event, proposal in eligible
        if _ref_key(event.ratification_event_ref) in active_event_keys
    )
    has_conflict = any(state.active_value_outcome == "ACTIVE_VALUE_CONFLICT" for state in states)
    if has_conflict:
        return ActiveValueResolutionResult(
            status="ACTIVE_VALUE_CONFLICT",
            reason_id=ACTIVE_VALUE_CONFLICT_REASON_ID,
            target_states=states,
            active_value_state_hash=state_hash,
            active_proposal_refs=(),
            diagnostics=tuple(sorted(diagnostics)),
        )
    if diagnostics:
        # Snapshot binding is all-or-nothing: silently excluding a malformed or
        # unauthorized ratification would let a run ignore evidence it actually bound.
        return ActiveValueResolutionResult(
            status="INTEGRITY_FAILURE",
            reason_id=RATIFICATION_INTEGRITY_FAILURE_REASON_ID,
            target_states=states,
            active_value_state_hash=state_hash,
            active_proposal_refs=(),
            diagnostics=tuple(sorted(diagnostics)),
        )
    return ActiveValueResolutionResult(
        status="RESOLVED",
        reason_id=ACTIVE_VALUE_RESOLVED_REASON_ID,
        target_states=states,
        active_value_state_hash=state_hash,
        active_proposal_refs=tuple(sorted(active_refs, key=_ref_key)),
        diagnostics=(),
    )


def active_value_state_hash(
    target_states: tuple[ActiveValueTargetState, ...],
    resolver_policy: ActiveValueResolverPolicy,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(
        active_value_state_payload(
            target_states,
            resolver_policy,
            as_of_time,
        ),
        canonicalization_policy,
    )


def active_value_state_payload(
    target_states: tuple[ActiveValueTargetState, ...],
    resolver_policy: ActiveValueResolverPolicy,
    as_of_time: CanonicalTimestamp,
) -> dict[str, object]:
    return {
        "algorithm_id": ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
        "as_of_time": as_of_time,
        "canonicalization_policy_ref": resolver_policy.canonicalization_policy_ref,
        "resolver_policy_ref": resolver_policy.resolver_policy_ref,
        "target_states": tuple(
            state.model_dump(mode="python", exclude_none=True) for state in target_states
        ),
    }


def _event_eligibility_issue(
    event: ProposalRatificationEvent,
    proposal: TypedValueProposal,
    actor_records: tuple[ActorRecord, ...],
    authority_policy: AuthorityPolicy,
    role_assignments: tuple[RoleAssignmentEvent, ...],
    authorization_events: tuple[AuthorizationEvent, ...],
    scope_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> TermId | None:
    if proposal.validation_state != "READY_FOR_RATIFICATION":
        return PROPOSAL_NOT_READY_REASON_ID
    if (
        event.proposal_ref != proposal.proposal_ref
        or event.proposal_content_hash
        != typed_value_proposal_content_hash(proposal, canonicalization_policy)
        or event.proposed_value_hash != proposed_value_hash(proposal, canonicalization_policy)
    ):
        return PROPOSAL_HASH_MISMATCH_REASON_ID
    # Separation of duties must anchor on the authorship the system already holds on the
    # bound proposal, not on the event's self-declaration. A proposal with no recorded
    # author cannot be independence-checked, so it is ineligible for ratification (fail
    # closed); when an author IS recorded, the event must declare exactly that actor.
    # Together these stop an author from self-ratifying by either omitting the author on
    # the proposal or altering the declared proposer on the event.
    if (
        proposal.claimed_proposer_ref is None
        or event.claimed_proposer_ref != proposal.claimed_proposer_ref
    ):
        return AUTHORITY_INELIGIBLE_REASON_ID
    if not _claimed_actors_active(actor_records, event, as_of_time):
        return AUTHORITY_INELIGIBLE_REASON_ID
    if not _authority_policy_active(authority_policy, scope_ref, as_of_time):
        return AUTHORITY_INELIGIBLE_REASON_ID
    permission = _permission_for_event(authority_policy, event, proposal, scope_ref)
    if permission is None:
        return AUTHORITY_INELIGIBLE_REASON_ID
    if not _has_active_role_assignment(role_assignments, event, scope_ref, as_of_time):
        return AUTHORITY_INELIGIBLE_REASON_ID
    if not _has_active_authorization(authorization_events, event, proposal, scope_ref, as_of_time):
        return AUTHORITY_INELIGIBLE_REASON_ID
    if _violates_separation_of_duties(event, permission):
        return AUTHORITY_INELIGIBLE_REASON_ID
    return None


def _target_states(
    eligible: list[tuple[ProposalRatificationEvent, TypedValueProposal]],
    canonicalization_policy: CanonicalizationPolicy,
) -> tuple[ActiveValueTargetState, ...]:
    grouped: dict[Sha256Hex, list[tuple[ProposalRatificationEvent, TypedValueProposal]]] = {}
    target_keys: dict[Sha256Hex, dict[str, object]] = {}
    for event, proposal in eligible:
        target_key = active_value_key_payload(proposal.target, canonicalization_policy)
        target_hash = canonical_sha256(target_key, canonicalization_policy)
        grouped.setdefault(target_hash, []).append((event, proposal))
        target_keys[target_hash] = target_key

    states: list[ActiveValueTargetState] = []
    for target_hash in sorted(grouped):
        target_items = grouped[target_hash]
        eligible_events = tuple(sorted((item[0].ratification_event_ref for item in target_items), key=_ref_key))
        non_superseded_items = _remove_superseded(target_items)
        non_superseded_events = tuple(
            sorted((item[0].ratification_event_ref for item in non_superseded_items), key=_ref_key)
        )
        active_items = tuple(item for item in non_superseded_items if item[0].decision == "RATIFIED")
        active_events = tuple(sorted((item[0].ratification_event_ref for item in active_items), key=_ref_key))
        proposal_refs = sorted_unique_refs(tuple(item[1].proposal_ref for item in target_items))
        proposal_hashes = tuple(sorted({item[1].proposal_ref.content_hash for item in target_items}))
        outcome: Literal["NO_ACTIVE_VALUE", "ONE_ACTIVE_VALUE", "ACTIVE_VALUE_CONFLICT"]
        if len(active_events) == 0:
            outcome = "NO_ACTIVE_VALUE"
            conflicts = None
        elif len(active_events) == 1:
            outcome = "ONE_ACTIVE_VALUE"
            conflicts = None
        else:
            outcome = "ACTIVE_VALUE_CONFLICT"
            conflicts = active_events
        states.append(
            ActiveValueTargetState(
                target_key=target_keys[target_hash],
                eligible_event_refs=eligible_events,
                non_superseded_event_refs=non_superseded_events,
                active_ratified_event_refs=active_events,
                proposal_refs=proposal_refs,
                proposal_content_hashes=proposal_hashes,
                active_value_outcome=outcome,
                conflicting_event_refs=conflicts,
            )
        )
    return tuple(
        sorted(
            states,
            key=lambda item: (
                str(item.target_key["target_record_type"]),
                str(item.target_key["target_logical_id"]),
                str(item.target_key["semantic_field_path"]),
                str(item.target_key["context_key_hash"]),
            ),
        )
    )


def _remove_superseded(
    items: list[tuple[ProposalRatificationEvent, TypedValueProposal]],
) -> tuple[tuple[ProposalRatificationEvent, TypedValueProposal], ...]:
    superseded = {
        item[0].supersedes_ratification_event_ref
        for item in items
        if item[0].supersedes_ratification_event_ref is not None
    }
    return tuple(item for item in items if item[0].ratification_event_ref not in superseded)


def _authority_policy_active(
    authority_policy: AuthorityPolicy,
    scope_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
) -> bool:
    return (
        authority_policy.lifecycle_state == "ACTIVE"
        and authority_policy.effective_at <= as_of_time
        and (authority_policy.expires_at is None or authority_policy.expires_at > as_of_time)
        and any(permission.scope_ref == scope_ref for permission in authority_policy.permissions)
    )


def _permission_for_event(
    authority_policy: AuthorityPolicy,
    event: ProposalRatificationEvent,
    proposal: TypedValueProposal,
    scope_ref: GovernedRef,
) -> AuthorityPermission | None:
    if event.authority_policy_ref != authority_policy.policy_ref:
        return None
    if event.ratifying_actor_ref not in authority_policy.actor_refs:
        return None
    for permission in authority_policy.permissions:
        if (
            permission.role_id == event.ratifying_role_id
            and permission.action_id == RATIFY_PROPOSAL_ACTION_ID
            and permission.scope_ref == scope_ref
            and proposal.target.target_record_type in permission.target_record_types
        ):
            return permission
    return None


def _claimed_actors_active(
    actor_records: tuple[ActorRecord, ...],
    event: ProposalRatificationEvent,
    as_of_time: CanonicalTimestamp,
) -> bool:
    active_actor_keys = {
        _ref_key(record.actor_ref)
        for record in actor_records
        if record.lifecycle_state == "ACTIVE"
        and record.effective_at <= as_of_time
        and record.recorded_at <= as_of_time
        and (record.expires_at is None or record.expires_at > as_of_time)
    }
    required_actor_keys = {
        _ref_key(event.ratifying_actor_ref),
        _ref_key(event.claimed_ratifier_ref),
    }
    if event.claimed_proposer_ref is not None:
        required_actor_keys.add(_ref_key(event.claimed_proposer_ref))
    if event.claimed_executor_ref is not None:
        required_actor_keys.add(_ref_key(event.claimed_executor_ref))
    return required_actor_keys <= active_actor_keys


def _has_active_role_assignment(
    assignments: tuple[RoleAssignmentEvent, ...],
    event: ProposalRatificationEvent,
    scope_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
) -> bool:
    return any(
        assignment.state == "ACTIVE"
        and assignment.actor_ref == event.ratifying_actor_ref
        and assignment.role_id == event.ratifying_role_id
        and assignment.authority_policy_ref == event.authority_policy_ref
        and assignment.scope_ref == scope_ref
        and assignment.effective_at <= as_of_time
        and assignment.recorded_at <= as_of_time
        for assignment in assignments
    )


def _has_active_authorization(
    authorizations: tuple[AuthorizationEvent, ...],
    event: ProposalRatificationEvent,
    proposal: TypedValueProposal,
    scope_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
) -> bool:
    return any(
        authorization.state == "ACTIVE"
        and authorization.authorization_ref == event.authorization_event_ref
        and authorization.actor_ref == event.ratifying_actor_ref
        and authorization.role_id == event.ratifying_role_id
        and authorization.action_id == RATIFY_PROPOSAL_ACTION_ID
        and authorization.authority_policy_ref == event.authority_policy_ref
        and authorization.scope_ref == scope_ref
        and authorization.target_record_type == proposal.target.target_record_type
        and authorization.effective_at <= as_of_time
        and authorization.recorded_at <= as_of_time
        for authorization in authorizations
    )


def _violates_separation_of_duties(
    event: ProposalRatificationEvent,
    permission: AuthorityPermission,
) -> bool:
    same_actor = event.ratifying_actor_ref in (
        event.claimed_proposer_ref,
        event.claimed_executor_ref,
    )
    if not same_actor:
        return event.same_actor_allowed
    if not permission.same_actor_allowed:
        return True
    return not (
        event.same_actor_allowed
        and event.single_actor_policy_basis_ref is not None
        and event.single_actor_policy_basis_ref == event.authority_policy_ref
    )


def _sort_evidence_refs(value: object) -> object:
    if not isinstance(value, dict) or "evidence_refs" not in value:
        return value
    normalized = dict(value)
    normalized["evidence_refs"] = sorted_unique_refs(tuple(normalized["evidence_refs"]))
    return normalized


def _ref_key(ref: GovernedRef) -> tuple[str, str]:
    return (ref.logical_id, ref.version_id)


def _ref_value_key(value: object, field_name: str) -> tuple[str, str]:
    ref = _field_value(value, field_name)
    if isinstance(ref, GovernedRef):
        return _ref_key(ref)
    if isinstance(ref, dict):
        return (str(ref["logical_id"]), str(ref["version_id"]))
    raise ValueError("governed reference values must be model or mapping values")


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, BaseModel):
        return getattr(value, field_name)
    if isinstance(value, dict):
        return value[field_name]
    raise ValueError("ratification values must be model or mapping values")
