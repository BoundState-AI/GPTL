from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Literal, cast

from gptl.core.canonical import canonical_sha256
from gptl.core.proposal_ratification import (
    ACTIVE_VALUE_CONFLICT_REASON_ID,
    ACTIVE_VALUE_RESOLVED_REASON_ID,
    ACTIVE_VALUE_RESOLVER_POLICY_RECORD_TYPE,
    ACTIVE_VALUE_RESOLVER_POLICY_SCHEMA_VERSION,
    ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
    ACTOR_RECORD_RECORD_TYPE,
    ACTOR_RECORD_SCHEMA_VERSION,
    AUTHORITY_INELIGIBLE_REASON_ID,
    AUTHORITY_POLICY_RECORD_TYPE,
    AUTHORITY_POLICY_SCHEMA_VERSION,
    AUTHORIZATION_EVENT_RECORD_TYPE,
    AUTHORIZATION_EVENT_SCHEMA_VERSION,
    HASH_ALGORITHM,
    PROPOSAL_HASH_MISMATCH_REASON_ID,
    PROPOSAL_NOT_READY_REASON_ID,
    PROPOSAL_RATIFICATION_RECORD_TYPE,
    PROPOSAL_RATIFICATION_SCHEMA_VERSION,
    RATIFICATION_INTEGRITY_FAILURE_REASON_ID,
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
    active_value_state_hash,
    active_value_state_payload,
    evaluate_active_values,
    proposed_value_hash,
)
from gptl.core.proposals import (
    HASH_ALGORITHM as PROPOSAL_HASH_ALGORITHM,
)
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
LATER_AS_OF = "2026-07-02T12:00:00.000Z"
SOURCE_RAW_HASH = "a" * 64


def test_ratified_ready_proposal_becomes_single_active_value(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    event = _ratification_event(build1_ref_factory, proposal)

    result = _evaluate(build1_ref_factory, (proposal,), (event,))

    assert result.status == "RESOLVED"
    assert result.reason_id == ACTIVE_VALUE_RESOLVED_REASON_ID
    assert result.active_proposal_refs == (proposal.proposal_ref,)
    assert result.target_states[0].active_value_outcome == "ONE_ACTIVE_VALUE"
    assert result.active_value_state_hash == active_value_state_hash(
        result.target_states,
        _resolver_policy(build1_ref_factory),
        AS_OF,
        canonicalization_policy(),
    )


def test_ratification_verifies_proposal_content_hash_before_eligibility(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    event = _ratification_event(
        build1_ref_factory,
        proposal,
        proposal_content_hash="0" * 64,
    )

    result = _evaluate(build1_ref_factory, (proposal,), (event,))

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (PROPOSAL_HASH_MISMATCH_REASON_ID,)
    assert result.active_proposal_refs == ()


def test_ratification_rejects_proposal_not_ready_for_ratification(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory, validation_state="PROPOSED")
    event = _ratification_event(build1_ref_factory, proposal)

    result = _evaluate(build1_ref_factory, (proposal,), (event,))

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (PROPOSAL_NOT_READY_REASON_ID,)
    assert result.active_proposal_refs == ()


def test_authority_role_authorization_and_separation_of_duties_are_required(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    same_actor_event = _ratification_event(
        build1_ref_factory,
        proposal,
        ratifier_ref=build1_ref_factory("build1.actor.proposer"),
        claimed_proposer_ref=build1_ref_factory("build1.actor.proposer"),
    )

    result = _evaluate(build1_ref_factory, (proposal,), (same_actor_event,))

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (AUTHORITY_INELIGIBLE_REASON_ID,)


def test_ratification_requires_active_local_actor_records(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    event = _ratification_event(build1_ref_factory, proposal)

    result = _evaluate(build1_ref_factory, (proposal,), (event,), actor_records=())

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (AUTHORITY_INELIGIBLE_REASON_ID,)


def test_ineligible_ratification_fails_entire_snapshot_bind(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    valid = _proposal(build1_ref_factory)
    unrelated_invalid = _proposal(
        build1_ref_factory,
        proposal_ref=_proposal_ref("build1.proposal.width", 1),
        target_ref=build1_ref_factory("build1.target.specimen-2"),
        value=Decimal("10.0000"),
    )
    valid_event = _ratification_event(
        build1_ref_factory,
        valid,
        event_ref=build1_ref_factory("build1.ratification.valid"),
    )
    invalid_event = _ratification_event(
        build1_ref_factory,
        unrelated_invalid,
        event_ref=build1_ref_factory("build1.ratification.invalid"),
        ratifier_ref=build1_ref_factory("build1.actor.unassigned"),
        claimed_proposer_ref=build1_ref_factory("build1.actor.proposer"),
    )

    result = _evaluate(
        build1_ref_factory,
        (valid, unrelated_invalid),
        (valid_event, invalid_event),
    )

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (AUTHORITY_INELIGIBLE_REASON_ID,)
    assert result.active_proposal_refs == ()
    assert result.target_states[0].active_ratified_event_refs == (
        valid_event.ratification_event_ref,
    )


def test_single_actor_ratification_requires_explicit_policy_basis(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    actor = build1_ref_factory("build1.actor.proposer")
    event = _ratification_event(
        build1_ref_factory,
        proposal,
        ratifier_ref=actor,
        claimed_proposer_ref=actor,
        same_actor_allowed=True,
        single_actor_policy_basis_ref=build1_ref_factory("build1.authority.policy"),
    )

    result = _evaluate(
        build1_ref_factory,
        (proposal,),
        (event,),
        authority_policy=_authority_policy(build1_ref_factory, same_actor_allowed=True),
        role_assignments=(_role_assignment(build1_ref_factory, actor_ref=actor),),
        authorizations=(_authorization_event(build1_ref_factory, actor_ref=actor),),
    )

    assert result.status == "RESOLVED"
    assert result.active_proposal_refs == (proposal.proposal_ref,)


def test_ratification_reconciles_event_proposer_against_recorded_proposal_author(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    # The proposal records its author; the same actor also happens to hold a valid
    # reviewer role + authorization, so separation of duties is the ONLY remaining gate.
    # The event tries to slip past it by naming a *different* proposer than the one the
    # proposal actually records — which, absent reconciliation, reads as an independent
    # reviewer and ratifies. The gate must reject the mismatch as authority-ineligible.
    author = build1_ref_factory("build1.actor.proposer")
    proposal = _proposal(build1_ref_factory, claimed_proposer_ref=author)
    disguised_event = _ratification_event(
        build1_ref_factory,
        proposal,
        ratifier_ref=author,
        claimed_proposer_ref=build1_ref_factory("build1.actor.reviewer"),
    )

    result = _evaluate(
        build1_ref_factory,
        (proposal,),
        (disguised_event,),
        role_assignments=(_role_assignment(build1_ref_factory, actor_ref=author),),
        authorizations=(_authorization_event(build1_ref_factory, actor_ref=author),),
    )

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (AUTHORITY_INELIGIBLE_REASON_ID,)
    assert result.active_proposal_refs == ()


def test_ratification_rejects_proposal_with_no_recorded_author(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    # A proposal with no recorded author cannot be independence-checked, so it must be
    # ineligible for ratification (fail closed) — otherwise a dual-hatted author self-
    # ratifies by leaving the proposer OFF the proposal and naming any other actor on the
    # event, and separation of duties (which reads the event) never fires. AUTH-1 omit path.
    author = build1_ref_factory("build1.actor.proposer")
    proposal = _proposal(build1_ref_factory, omit_proposer=True)
    disguised_event = _ratification_event(
        build1_ref_factory,
        proposal,
        ratifier_ref=author,
        claimed_proposer_ref=build1_ref_factory("build1.actor.reviewer"),
    )

    result = _evaluate(
        build1_ref_factory,
        (proposal,),
        (disguised_event,),
        role_assignments=(_role_assignment(build1_ref_factory, actor_ref=author),),
        authorizations=(_authorization_event(build1_ref_factory, actor_ref=author),),
    )

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert result.diagnostics == (AUTHORITY_INELIGIBLE_REASON_ID,)
    assert result.active_proposal_refs == ()


def test_future_recorded_backdated_ratification_affects_only_later_run(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    event = _ratification_event(
        build1_ref_factory,
        proposal,
        effective_at="2026-07-01T00:00:00.000Z",
        recorded_at="2026-07-01T18:00:00.000Z",
    )

    current = _evaluate(build1_ref_factory, (proposal,), (event,), as_of_time=AS_OF)
    later = _evaluate(build1_ref_factory, (proposal,), (event,), as_of_time=LATER_AS_OF)

    assert current.status == "RESOLVED"
    assert current.target_states == ()
    assert later.status == "RESOLVED"
    assert later.active_proposal_refs == (proposal.proposal_ref,)


def test_rejected_and_correction_requested_events_do_not_create_active_values(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    rejected = _ratification_event(
        build1_ref_factory,
        proposal,
        event_ref=build1_ref_factory("build1.ratification.rejected"),
        decision="REJECTED",
    )
    correction = _ratification_event(
        build1_ref_factory,
        proposal,
        event_ref=build1_ref_factory("build1.ratification.correction"),
        decision="CORRECTION_REQUESTED",
    )

    result = _evaluate(build1_ref_factory, (proposal,), (rejected, correction))

    assert result.status == "RESOLVED"
    assert result.target_states[0].active_value_outcome == "NO_ACTIVE_VALUE"
    assert result.target_states[0].proposal_refs == (proposal.proposal_ref,)
    assert result.target_states[0].proposal_content_hashes == (proposal.proposal_ref.content_hash,)
    assert result.active_proposal_refs == ()


def test_duplicate_active_ratification_heads_fail_closed_with_conflict_refs(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    first = _proposal(build1_ref_factory)
    second = _proposal(
        build1_ref_factory,
        proposal_ref=_proposal_ref("build1.proposal.hardness", 2),
        value=Decimal("42.0000"),
    )
    first_event = _ratification_event(
        build1_ref_factory,
        first,
        event_ref=build1_ref_factory("build1.ratification.1"),
    )
    second_event = _ratification_event(
        build1_ref_factory,
        second,
        event_ref=build1_ref_factory("build1.ratification.2"),
    )

    result = _evaluate(build1_ref_factory, (first, second), (first_event, second_event))

    assert result.status == "ACTIVE_VALUE_CONFLICT"
    assert result.reason_id == ACTIVE_VALUE_CONFLICT_REASON_ID
    assert result.active_proposal_refs == ()
    assert result.target_states[0].active_value_outcome == "ACTIVE_VALUE_CONFLICT"
    assert result.target_states[0].conflicting_event_refs == (
        first_event.ratification_event_ref,
        second_event.ratification_event_ref,
    )


def test_supersession_leaves_one_active_ratified_head(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    first = _proposal(build1_ref_factory)
    second = _proposal(
        build1_ref_factory,
        proposal_ref=_proposal_ref("build1.proposal.hardness", 2),
        value=Decimal("42.0000"),
    )
    first_event = _ratification_event(
        build1_ref_factory,
        first,
        event_ref=build1_ref_factory("build1.ratification.1"),
    )
    second_event = _ratification_event(
        build1_ref_factory,
        second,
        event_ref=build1_ref_factory("build1.ratification.2"),
        supersedes_ratification_event_ref=first_event.ratification_event_ref,
    )

    result = _evaluate(build1_ref_factory, (first, second), (first_event, second_event))

    assert result.status == "RESOLVED"
    assert result.target_states[0].active_value_outcome == "ONE_ACTIVE_VALUE"
    assert result.target_states[0].active_ratified_event_refs == (
        second_event.ratification_event_ref,
    )
    assert result.active_proposal_refs == (second.proposal_ref,)


def test_active_value_state_payload_omits_raw_values_and_reviewer_prose(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    event = _ratification_event(
        build1_ref_factory,
        proposal,
        reviewer_note="non-authoritative note",
    )
    result = _evaluate(build1_ref_factory, (proposal,), (event,))

    payload = active_value_state_payload(
        result.target_states,
        _resolver_policy(build1_ref_factory),
        AS_OF,
    )
    payload_hash = canonical_sha256(payload, canonicalization_policy())

    assert payload["algorithm_id"] == ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID
    assert set(payload) == {
        "algorithm_id",
        "as_of_time",
        "canonicalization_policy_ref",
        "resolver_policy_ref",
        "target_states",
    }
    target_state = cast(tuple[dict[str, object], ...], payload["target_states"])[0]
    assert set(target_state) == {
        "target_key",
        "eligible_event_refs",
        "non_superseded_event_refs",
        "active_ratified_event_refs",
        "proposal_refs",
        "proposal_content_hashes",
        "active_value_outcome",
    }
    assert payload_hash == result.active_value_state_hash
    assert "41.2500" not in repr(payload)
    assert "non-authoritative note" not in repr(payload)


def test_slice_4_runtime_source_guard(
    runtime_source_guard: Callable[[tuple[Path, ...]], None],
) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard(
        (repository_root / "src" / "gptl" / "core" / "proposal_ratification.py",)
    )


def _evaluate(
    build1_ref_factory: Callable[[str], GovernedRef],
    proposals: tuple[TypedValueProposal, ...],
    events: tuple[ProposalRatificationEvent, ...],
    *,
    actor_records: tuple[ActorRecord, ...] | None = None,
    authority_policy: AuthorityPolicy | None = None,
    role_assignments: tuple[RoleAssignmentEvent, ...] | None = None,
    authorizations: tuple[AuthorizationEvent, ...] | None = None,
    as_of_time: str = AS_OF,
) -> ActiveValueResolutionResult:
    return evaluate_active_values(
        proposals,
        events,
        actor_records if actor_records is not None else _actor_records(build1_ref_factory),
        authority_policy if authority_policy is not None else _authority_policy(build1_ref_factory),
        role_assignments
        if role_assignments is not None
        else (_role_assignment(build1_ref_factory),),
        authorizations
        if authorizations is not None
        else (_authorization_event(build1_ref_factory),),
        _resolver_policy(build1_ref_factory),
        build1_ref_factory("build1.scope.candidate"),
        as_of_time,
        canonicalization_policy(),
    )


def _proposal(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    proposal_ref: GovernedRef | None = None,
    target_ref: GovernedRef | None = None,
    value: Decimal = Decimal("41.2500"),
    validation_state: Literal[
        "PROPOSED",
        "VALIDATION_FAILED",
        "READY_FOR_RATIFICATION",
        "REJECTED",
        "SUPERSEDED",
    ] = "READY_FOR_RATIFICATION",
    claimed_proposer_ref: GovernedRef | None = None,
    omit_proposer: bool = False,
) -> TypedValueProposal:
    target = target_ref or build1_ref_factory("build1.target.specimen-1")
    proposer_ref = (
        None if omit_proposer else claimed_proposer_ref or build1_ref_factory("build1.actor.proposer")
    )
    proposal = TypedValueProposal.model_validate(
        {
            "claimed_proposer_ref": proposer_ref,
            "schema_version": TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
            "record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
            "hash_algorithm": PROPOSAL_HASH_ALGORITHM,
            "proposal_ref": proposal_ref or _proposal_ref("build1.proposal.hardness", 1),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "source_artifact_ref": build1_ref_factory("build1.source.fixture-1"),
            "source_raw_byte_hash": SOURCE_RAW_HASH,
            "identity": {
                "identity_mode": "EXISTING_GOVERNED_REF",
                "target_ref": target,
            },
            "proposal_method": "MANUAL_TRANSLATION",
            "creation_event_ref": build1_ref_factory("build1.proposal.creation-event"),
            "target": _target(target),
            "proposed_value": {"kind": "NUMERIC", "value": value, "unit_id": "unit.hrc"},
            "evidence_location": {
                "locator_class": "RAW_BYTE_RANGE",
                "source_artifact_ref": build1_ref_factory("build1.source.fixture-1"),
                "start_byte": 0,
                "end_byte": 5,
                "raw_byte_hash": SOURCE_RAW_HASH,
            },
            "validation_state": validation_state,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return finalize_typed_value_proposal(proposal, canonicalization_policy())


def _target(target_ref: GovernedRef) -> ProposalTarget:
    return ProposalTarget.model_validate(
        {
            "target_record_type": "record.material-specimen",
            "target_logical_id": target_ref.logical_id,
            "target_schema_version": "schema.specimen.v1",
            "semantic_field_path": "field.hardness",
            "context_key": {"side": "side.left", "replicate": 1},
        }
    )


def _ratification_event(
    build1_ref_factory: Callable[[str], GovernedRef],
    proposal: TypedValueProposal,
    *,
    event_ref: GovernedRef | None = None,
    decision: str = "RATIFIED",
    proposal_content_hash: str | None = None,
    ratifier_ref: GovernedRef | None = None,
    claimed_proposer_ref: GovernedRef | None = None,
    same_actor_allowed: bool = False,
    single_actor_policy_basis_ref: GovernedRef | None = None,
    supersedes_ratification_event_ref: GovernedRef | None = None,
    effective_at: str = AS_OF,
    recorded_at: str = AS_OF,
    reviewer_note: str | None = None,
) -> ProposalRatificationEvent:
    actor = ratifier_ref or build1_ref_factory("build1.actor.reviewer")
    return ProposalRatificationEvent.model_validate(
        {
            "schema_version": PROPOSAL_RATIFICATION_SCHEMA_VERSION,
            "record_type": PROPOSAL_RATIFICATION_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "ratification_event_ref": event_ref
            or build1_ref_factory("build1.ratification.1"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "proposal_ref": proposal.proposal_ref,
            "proposal_content_hash": proposal_content_hash
            or proposal.proposal_ref.content_hash,
            "proposed_value_hash": proposed_value_hash(proposal, canonicalization_policy()),
            "ratifying_actor_ref": actor,
            "ratifying_role_id": "role.materials-reviewer",
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "authorization_event_ref": build1_ref_factory("build1.authorization.reviewer"),
            "decision": decision,
            "effective_at": effective_at,
            "recorded_at": recorded_at,
            "evidence_refs": (build1_ref_factory("build1.evidence.review"),),
            "reviewer_note": reviewer_note,
            "supersedes_ratification_event_ref": supersedes_ratification_event_ref,
            "same_actor_allowed": same_actor_allowed,
            "single_actor_policy_basis_ref": single_actor_policy_basis_ref,
            "claimed_proposer_ref": claimed_proposer_ref
            or build1_ref_factory("build1.actor.proposer"),
            "claimed_ratifier_ref": actor,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _authority_policy(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    same_actor_allowed: bool = False,
) -> AuthorityPolicy:
    return AuthorityPolicy.model_validate(
        {
            "schema_version": AUTHORITY_POLICY_SCHEMA_VERSION,
            "record_type": AUTHORITY_POLICY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "policy_ref": build1_ref_factory("build1.authority.policy"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "actor_refs": (
                build1_ref_factory("build1.actor.proposer"),
                build1_ref_factory("build1.actor.reviewer"),
            ),
            "permissions": (
                AuthorityPermission(
                    role_id=TermId("role.materials-reviewer"),
                    action_id=RATIFY_PROPOSAL_ACTION_ID,
                    scope_ref=build1_ref_factory("build1.scope.candidate"),
                    target_record_types=(TermId("record.material-specimen"),),
                    same_actor_allowed=same_actor_allowed,
                ),
            ),
            "evidence_refs": (build1_ref_factory("build1.evidence.authority-policy"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _actor_records(build1_ref_factory: Callable[[str], GovernedRef]) -> tuple[ActorRecord, ...]:
    return (
        _actor_record(build1_ref_factory, build1_ref_factory("build1.actor.proposer")),
        _actor_record(build1_ref_factory, build1_ref_factory("build1.actor.reviewer")),
    )


def _actor_record(
    build1_ref_factory: Callable[[str], GovernedRef],
    actor_ref: GovernedRef,
) -> ActorRecord:
    return ActorRecord.model_validate(
        {
            "schema_version": ACTOR_RECORD_SCHEMA_VERSION,
            "record_type": ACTOR_RECORD_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "actor_ref": actor_ref,
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "recorded_at": "2026-06-01T00:00:00.000Z",
            "evidence_refs": (build1_ref_factory("build1.evidence.actor-registry"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _role_assignment(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    actor_ref: GovernedRef | None = None,
) -> RoleAssignmentEvent:
    return RoleAssignmentEvent.model_validate(
        {
            "schema_version": ROLE_ASSIGNMENT_SCHEMA_VERSION,
            "record_type": ROLE_ASSIGNMENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "assignment_ref": build1_ref_factory("build1.role-assignment.reviewer"),
            "actor_ref": actor_ref or build1_ref_factory("build1.actor.reviewer"),
            "role_id": "role.materials-reviewer",
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "scope_ref": build1_ref_factory("build1.scope.candidate"),
            "state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "recorded_at": "2026-06-01T00:00:00.000Z",
            "evidence_refs": (build1_ref_factory("build1.evidence.role-assignment"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _authorization_event(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    actor_ref: GovernedRef | None = None,
) -> AuthorizationEvent:
    return AuthorizationEvent.model_validate(
        {
            "schema_version": AUTHORIZATION_EVENT_SCHEMA_VERSION,
            "record_type": AUTHORIZATION_EVENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "authorization_ref": build1_ref_factory("build1.authorization.reviewer"),
            "actor_ref": actor_ref or build1_ref_factory("build1.actor.reviewer"),
            "role_id": "role.materials-reviewer",
            "action_id": RATIFY_PROPOSAL_ACTION_ID,
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "scope_ref": build1_ref_factory("build1.scope.candidate"),
            "target_record_type": "record.material-specimen",
            "state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "recorded_at": "2026-06-01T00:00:00.000Z",
            "evidence_refs": (build1_ref_factory("build1.evidence.authorization"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _resolver_policy(build1_ref_factory: Callable[[str], GovernedRef]) -> ActiveValueResolverPolicy:
    return ActiveValueResolverPolicy.model_validate(
        {
            "schema_version": ACTIVE_VALUE_RESOLVER_POLICY_SCHEMA_VERSION,
            "record_type": ACTIVE_VALUE_RESOLVER_POLICY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "resolver_policy_ref": build1_ref_factory("build1.active-value-resolver.policy"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "algorithm_id": ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
            "evidence_refs": (build1_ref_factory("build1.evidence.active-resolver"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _proposal_ref(logical_id: str, version_number: int) -> GovernedRef:
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v{version_number}"),
        version_number=version_number,
        content_hash="0" * 64,
    )
