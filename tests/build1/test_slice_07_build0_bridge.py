from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Literal, cast

import pytest

from gptl.core.build0_bridge import (
    BRIDGE_ACTIVE_VALUE_CONFLICT_REASON_ID,
    BRIDGE_ADVISORY_ONLY_OBSERVATION_REASON_ID,
    BRIDGE_AUTHORITY_INELIGIBLE_REASON_ID,
    BRIDGE_CAPABILITY_GAP_REASON_ID,
    BRIDGE_CONTEXT_KEY_UNDEFINED_REASON_ID,
    BRIDGE_DUPLICATE_WRITE_UNRECONCILED_REASON_ID,
    BRIDGE_IDENTITY_COLLISION_REASON_ID,
    BRIDGE_IDENTITY_UNRESOLVED_REASON_ID,
    BRIDGE_MISSING_RATIFICATION_REASON_ID,
    BRIDGE_NUMERIC_POLICY_MISMATCH_REASON_ID,
    BRIDGE_PARSER_GAP_REASON_ID,
    BRIDGE_RETRY_MISMATCH_REASON_ID,
    BRIDGE_SCOPE_INCOMPATIBLE_REASON_ID,
    BUILD0_POSTGRES_ADVISORY_LOCK_SCOPE,
    BUILD1_EXACT_REPLAY_ALGORITHM_ID,
    BridgeAttemptRecord,
    BridgeCallerIds,
    Build0SnapshotBinding,
    CaptureGateResult,
    ExistingBuild0RunRecord,
    assemble_build0_bridge_request,
    build0_bridge_request_hash,
    build1_bridge_replay_hash,
    build_replay_capsule,
    create_capture_bound_attempt,
    evaluate_capture_gate,
    reconcile_bridge_retry,
)
from gptl.core.observations import (
    ATTRIBUTED_OBSERVATION_RECORD_TYPE,
    ATTRIBUTED_OBSERVATION_SCHEMA_VERSION,
    AttributedObservation,
    ObservationVisibilityPolicy,
    finalize_attributed_observation,
)
from gptl.core.observations import (
    HASH_ALGORITHM as OBSERVATION_HASH_ALGORITHM,
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
from gptl.core.proposal_ratification import (
    HASH_ALGORITHM as RATIFICATION_HASH_ALGORITHM,
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
from gptl.core.snapshot import KnowledgeSnapshot
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-07-01T12:00:00.000Z"
SOURCE_RAW_HASH = "a" * 64
OUTPUT_HASH = "b" * 64
REPLAY_HASH = "c" * 64


def test_ratified_proposal_becomes_build0_snapshot_request(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))

    gate = _gate(build1_ref_factory, active_values, (proposal,))
    request = assemble_build0_bridge_request(
        request_ref=build1_ref_factory("build1.bridge.request"),
        caller_ids=_caller_ids(),
        capture_gate=gate,
        snapshot_binding=_snapshot_binding(build1_ref_factory),
        canonicalization_policy=canonicalization_policy(),
    )

    assert gate.status == "BUILD0_REQUEST_READY"
    assert len(gate.bound_value_rows) == 1
    assert gate.bound_value_rows[0].proposal_ref == proposal.proposal_ref
    assert gate.bound_value_rows[0].typed_canonical_value == proposal.proposed_value
    assert request is not None
    assert isinstance(request.snapshot, KnowledgeSnapshot)
    assert request.snapshot.schema_version == "gptl.snapshot.v1"
    assert request.snapshot.ratification_state_hash == active_values.active_value_state_hash
    assert request.bound_value_rows == gate.bound_value_rows
    assert request.build0_lock_scope == BUILD0_POSTGRES_ADVISORY_LOCK_SCOPE
    assert build0_bridge_request_hash(request, canonicalization_policy()) == build0_bridge_request_hash(
        request,
        canonicalization_policy(),
    )


def test_unratified_equivalent_stops_before_tier1(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), ())

    gate = _gate(build1_ref_factory, active_values, (proposal,))

    assert gate.status == "ADVISORY_GAP"
    assert gate.reason_id == BRIDGE_MISSING_RATIFICATION_REASON_ID
    assert gate.bound_value_rows == ()
    assert assemble_build0_bridge_request(
        request_ref=build1_ref_factory("build1.bridge.request"),
        caller_ids=_caller_ids(),
        capture_gate=gate,
        snapshot_binding=_snapshot_binding(build1_ref_factory),
        canonicalization_policy=canonicalization_policy(),
    ) is None


def test_unsupported_capability_is_gap_not_negative_evidence(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))

    gate = _gate(
        build1_ref_factory,
        active_values,
        (proposal,),
        capability_status="UNSUPPORTED",
    )

    assert gate.status == "ADVISORY_GAP"
    assert gate.reason_id == BRIDGE_CAPABILITY_GAP_REASON_ID
    assert gate.bound_value_rows == ()
    assert all(diagnostic.classification == "ADVISORY_GAP" for diagnostic in gate.diagnostics)


@pytest.mark.parametrize(
    ("field_name", "field_value", "reason_id"),
    (
        ("scope_status", "INCOMPATIBLE", BRIDGE_SCOPE_INCOMPATIBLE_REASON_ID),
        ("authority_status", "MISSING_POLICY", BRIDGE_AUTHORITY_INELIGIBLE_REASON_ID),
        ("identity_status", "UNRESOLVED", BRIDGE_IDENTITY_UNRESOLVED_REASON_ID),
        ("identity_status", "COLLISION", BRIDGE_IDENTITY_COLLISION_REASON_ID),
        ("context_key_status", "UNDEFINED", BRIDGE_CONTEXT_KEY_UNDEFINED_REASON_ID),
    ),
)
def test_fail_closed_precedence_blocks_build0_request(
    build1_ref_factory: Callable[[str], GovernedRef],
    field_name: str,
    field_value: str,
    reason_id: TermId,
) -> None:
    proposal = _proposal(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))

    gate = _fail_closed_gate(build1_ref_factory, active_values, proposal, field_name, field_value)

    assert gate.status == "FAIL_CLOSED"
    assert gate.reason_id == reason_id
    assert gate.bound_value_rows == ()


def test_active_value_conflict_fails_before_build0(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    first = _proposal(build1_ref_factory)
    second = _proposal(
        build1_ref_factory,
        proposal_ref=_proposal_ref("build1.proposal.hardness", 2),
        value=Decimal("42.0000"),
    )
    active_values = _evaluate_active(
        build1_ref_factory,
        (first, second),
        (
            _ratification(build1_ref_factory, first, event_ref=build1_ref_factory("build1.ratification.1")),
            _ratification(build1_ref_factory, second, event_ref=build1_ref_factory("build1.ratification.2")),
        ),
    )

    gate = _gate(build1_ref_factory, active_values, (first, second))

    assert active_values.status == "ACTIVE_VALUE_CONFLICT"
    assert gate.status == "FAIL_CLOSED"
    assert gate.reason_id == BRIDGE_ACTIVE_VALUE_CONFLICT_REASON_ID
    assert gate.diagnostics[0].conflicting_event_refs


def test_parser_gap_stops_without_reclassifying_as_negative_evidence(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))

    gate = _gate(build1_ref_factory, active_values, (proposal,), parser_status="PARSER_FAILED")

    assert gate.status == "ADVISORY_GAP"
    assert gate.reason_id == BRIDGE_PARSER_GAP_REASON_ID
    assert gate.bound_value_rows == ()


def test_numeric_policy_mismatch_fails_before_build0(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(
        build1_ref_factory,
        canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy.v2"),
    )
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))

    gate = _gate(build1_ref_factory, active_values, (proposal,))

    assert gate.status == "FAIL_CLOSED"
    assert gate.reason_id == BRIDGE_NUMERIC_POLICY_MISMATCH_REASON_ID
    assert gate.bound_value_rows == ()


def test_observations_are_capture_context_only(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    observation = _observation(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))

    gate = _gate(build1_ref_factory, active_values, (proposal,), observations=(observation,))
    request = assemble_build0_bridge_request(
        request_ref=build1_ref_factory("build1.bridge.request"),
        caller_ids=_caller_ids(),
        capture_gate=gate,
        snapshot_binding=_snapshot_binding(build1_ref_factory),
        canonicalization_policy=canonicalization_policy(),
    )

    assert gate.status == "BUILD0_REQUEST_READY"
    assert gate.observation_refs == (observation.observation_ref,)
    assert request is not None
    assert observation.observation_ref not in request.snapshot.bound_versions
    assert observation.claim_text not in repr(request.model_dump(mode="python"))
    assert request.bound_value_rows == gate.bound_value_rows


def test_observation_only_capture_is_advisory_gap(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    observation = _observation(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (), ())

    gate = _gate(build1_ref_factory, active_values, (), observations=(observation,))

    assert gate.status == "ADVISORY_GAP"
    assert gate.reason_id == BRIDGE_ADVISORY_ONLY_OBSERVATION_REASON_ID
    assert gate.bound_value_rows == ()


def test_retry_changed_request_hash_fails_closed(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    attempt = _attempt(build1_ref_factory)

    result = reconcile_bridge_retry(
        attempt=attempt,
        caller_ids=_caller_ids(),
        build0_request_hash_value="d" * 64,
        existing_run=None,
        duplicate_insert_observed=False,
    )

    assert result.lifecycle_state == "BRIDGE_INTEGRITY_FAILURE"
    assert result.failure_reason_id == BRIDGE_RETRY_MISMATCH_REASON_ID


def test_retry_reconciles_by_reading_existing_build0_run(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    attempt = _attempt(build1_ref_factory)
    existing = ExistingBuild0RunRecord(
        caller_ids=_caller_ids(),
        build0_request_hash=attempt.build0_request_hash,
        build0_output_hash=OUTPUT_HASH,
        build0_replay_hash=REPLAY_HASH,
    )

    result = reconcile_bridge_retry(
        attempt=attempt,
        caller_ids=_caller_ids(),
        build0_request_hash_value=attempt.build0_request_hash,
        existing_run=existing,
        duplicate_insert_observed=True,
    )

    assert result.lifecycle_state == "BUILD0_PERSISTED"
    assert result.build0_output_hash == OUTPUT_HASH
    assert result.build0_replay_hash == REPLAY_HASH
    assert result.failure_reason_id is None


def test_duplicate_write_without_read_is_not_success(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    attempt = _attempt(build1_ref_factory)

    result = reconcile_bridge_retry(
        attempt=attempt,
        caller_ids=_caller_ids(),
        build0_request_hash_value=attempt.build0_request_hash,
        existing_run=None,
        duplicate_insert_observed=True,
    )

    assert result.lifecycle_state == "BRIDGE_INTEGRITY_FAILURE"
    assert result.failure_reason_id == BRIDGE_DUPLICATE_WRITE_UNRECONCILED_REASON_ID


def test_replay_capsule_binds_upstream_chain_order_independently(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(build1_ref_factory)
    active_values = _evaluate_active(build1_ref_factory, (proposal,), (_ratification(build1_ref_factory, proposal),))
    gate = _gate(build1_ref_factory, active_values, (proposal,))
    request_hash = "e" * 64
    first_upstream = (
        build1_ref_factory("build1.source.fixture-1"),
        build1_ref_factory("build1.authority.policy"),
    )
    second_upstream = tuple(reversed(first_upstream))

    first = build_replay_capsule(
        replay_ref=build1_ref_factory("build1.bridge.replay"),
        caller_ids=_caller_ids(),
        capture_gate=gate,
        build0_request_hash_value=request_hash,
        upstream_refs=first_upstream,
        canonicalization_policy=canonicalization_policy(),
    )
    second = build_replay_capsule(
        replay_ref=build1_ref_factory("build1.bridge.replay"),
        caller_ids=_caller_ids(),
        capture_gate=gate,
        build0_request_hash_value=request_hash,
        upstream_refs=second_upstream,
        canonicalization_policy=canonicalization_policy(),
    )

    assert first.algorithm_id == BUILD1_EXACT_REPLAY_ALGORITHM_ID
    assert first.upstream_refs == second.upstream_refs
    assert build1_bridge_replay_hash(first, canonicalization_policy()) == build1_bridge_replay_hash(
        second,
        canonicalization_policy(),
    )


def test_slice_7_runtime_source_guard(
    runtime_source_guard: Callable[[tuple[Path, ...]], None],
) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard((repository_root / "src" / "gptl" / "core" / "build0_bridge.py",))


def _gate(
    build1_ref_factory: Callable[[str], GovernedRef],
    active_values: ActiveValueResolutionResult,
    proposals: tuple[TypedValueProposal, ...],
    *,
    observations: tuple[AttributedObservation, ...] = (),
    capability_status: Literal["SUPPORTED", "UNKNOWN", "UNSUPPORTED", "AMBIGUOUS"] = "SUPPORTED",
    parser_status: Literal[
        "PARSER_READY",
        "UNPARSED",
        "PARSER_UNAVAILABLE",
        "PARSER_UNSUPPORTED",
        "PARSER_FAILED",
    ] = "PARSER_READY",
    scope_status: Literal["COMPATIBLE", "INCOMPATIBLE"] = "COMPATIBLE",
    authority_status: Literal["ELIGIBLE", "INELIGIBLE", "MISSING_POLICY"] = "ELIGIBLE",
    identity_status: Literal["RESOLVED", "UNRESOLVED", "COLLISION"] = "RESOLVED",
    context_key_status: Literal["DEFINED", "UNDEFINED"] = "DEFINED",
) -> CaptureGateResult:
    return evaluate_capture_gate(
        gate_ref=build1_ref_factory("build1.bridge.capture-gate"),
        canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy"),
        active_values=active_values,
        proposals=proposals,
        observations=observations,
        capability_status=capability_status,
        parser_status=parser_status,
        validation_protocol_status="NOT_REQUESTED",
        scope_status=scope_status,
        authority_status=authority_status,
        identity_status=identity_status,
        context_key_status=context_key_status,
        evidence_locator_status="RATIFIABLE",
        build0_canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy"),
        as_of_time=AS_OF,
        canonicalization_policy=canonicalization_policy(),
    )


def _fail_closed_gate(
    build1_ref_factory: Callable[[str], GovernedRef],
    active_values: ActiveValueResolutionResult,
    proposal: TypedValueProposal,
    field_name: str,
    field_value: str,
) -> CaptureGateResult:
    if field_name == "scope_status":
        return _gate(
            build1_ref_factory,
            active_values,
            (proposal,),
            scope_status=cast(Literal["INCOMPATIBLE"], field_value),
        )
    if field_name == "authority_status":
        return _gate(
            build1_ref_factory,
            active_values,
            (proposal,),
            authority_status=cast(Literal["MISSING_POLICY"], field_value),
        )
    if field_name == "identity_status":
        return _gate(
            build1_ref_factory,
            active_values,
            (proposal,),
            identity_status=cast(Literal["UNRESOLVED", "COLLISION"], field_value),
        )
    return _gate(
        build1_ref_factory,
        active_values,
        (proposal,),
        context_key_status=cast(Literal["UNDEFINED"], field_value),
    )


def _evaluate_active(
    build1_ref_factory: Callable[[str], GovernedRef],
    proposals: tuple[TypedValueProposal, ...],
    events: tuple[ProposalRatificationEvent, ...],
) -> ActiveValueResolutionResult:
    return evaluate_active_values(
        proposals,
        events,
        _actors(build1_ref_factory),
        _authority_policy(build1_ref_factory),
        (_role_assignment(build1_ref_factory),),
        (_authorization(build1_ref_factory),),
        _resolver_policy(build1_ref_factory),
        build1_ref_factory("build1.scope.candidate"),
        AS_OF,
        canonicalization_policy(),
    )


def _proposal(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    proposal_ref: GovernedRef | None = None,
    value: Decimal = Decimal("41.2500"),
    canonicalization_policy_ref: GovernedRef | None = None,
) -> TypedValueProposal:
    proposal = TypedValueProposal.model_validate(
        {
            "schema_version": TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
            "record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
            "hash_algorithm": PROPOSAL_HASH_ALGORITHM,
            "proposal_ref": proposal_ref or _proposal_ref("build1.proposal.hardness", 1),
            "canonicalization_policy_ref": canonicalization_policy_ref
            or build1_ref_factory("build1.canonicalization.policy"),
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "source_artifact_ref": build1_ref_factory("build1.source.fixture-1"),
            "source_raw_byte_hash": SOURCE_RAW_HASH,
            "identity": {
                "identity_mode": "EXISTING_GOVERNED_REF",
                "target_ref": build1_ref_factory("build1.target.specimen-1"),
            },
            "proposal_method": "MANUAL_TRANSLATION",
            "creation_event_ref": build1_ref_factory("build1.proposal.creation-event"),
            "target": _target(build1_ref_factory),
            "proposed_value": {"kind": "NUMERIC", "value": value, "unit_id": "unit.hrc"},
            "evidence_location": {
                "locator_class": "RAW_BYTE_RANGE",
                "source_artifact_ref": build1_ref_factory("build1.source.fixture-1"),
                "start_byte": 0,
                "end_byte": 5,
                "raw_byte_hash": SOURCE_RAW_HASH,
            },
            "validation_state": "READY_FOR_RATIFICATION",
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return finalize_typed_value_proposal(proposal, canonicalization_policy())


def _target(build1_ref_factory: Callable[[str], GovernedRef]) -> ProposalTarget:
    return ProposalTarget.model_validate(
        {
            "target_record_type": "record.material-specimen",
            "target_logical_id": build1_ref_factory("build1.target.specimen-1").logical_id,
            "target_schema_version": "schema.specimen.v1",
            "semantic_field_path": "field.hardness",
            "context_key": {"side": "side.left", "replicate": 1},
        }
    )


def _ratification(
    build1_ref_factory: Callable[[str], GovernedRef],
    proposal: TypedValueProposal,
    *,
    event_ref: GovernedRef | None = None,
) -> ProposalRatificationEvent:
    return ProposalRatificationEvent.model_validate(
        {
            "schema_version": PROPOSAL_RATIFICATION_SCHEMA_VERSION,
            "record_type": PROPOSAL_RATIFICATION_RECORD_TYPE,
            "hash_algorithm": RATIFICATION_HASH_ALGORITHM,
            "ratification_event_ref": event_ref or build1_ref_factory("build1.ratification.1"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "proposal_ref": proposal.proposal_ref,
            "proposal_content_hash": proposal.proposal_ref.content_hash,
            "proposed_value_hash": proposed_value_hash(proposal, canonicalization_policy()),
            "ratifying_actor_ref": build1_ref_factory("build1.actor.reviewer"),
            "ratifying_role_id": "role.materials-reviewer",
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "authorization_event_ref": build1_ref_factory("build1.authorization.reviewer"),
            "decision": "RATIFIED",
            "effective_at": AS_OF,
            "recorded_at": AS_OF,
            "evidence_refs": (build1_ref_factory("build1.evidence.review"),),
            "claimed_proposer_ref": build1_ref_factory("build1.actor.proposer"),
            "claimed_ratifier_ref": build1_ref_factory("build1.actor.reviewer"),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _actors(build1_ref_factory: Callable[[str], GovernedRef]) -> tuple[ActorRecord, ...]:
    return (
        _actor(build1_ref_factory, build1_ref_factory("build1.actor.proposer")),
        _actor(build1_ref_factory, build1_ref_factory("build1.actor.reviewer")),
    )


def _actor(
    build1_ref_factory: Callable[[str], GovernedRef],
    actor_ref: GovernedRef,
) -> ActorRecord:
    return ActorRecord.model_validate(
        {
            "schema_version": ACTOR_RECORD_SCHEMA_VERSION,
            "record_type": ACTOR_RECORD_RECORD_TYPE,
            "hash_algorithm": RATIFICATION_HASH_ALGORITHM,
            "actor_ref": actor_ref,
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "recorded_at": "2026-06-01T00:00:00.000Z",
            "evidence_refs": (build1_ref_factory("build1.evidence.actor-registry"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _authority_policy(build1_ref_factory: Callable[[str], GovernedRef]) -> AuthorityPolicy:
    return AuthorityPolicy.model_validate(
        {
            "schema_version": AUTHORITY_POLICY_SCHEMA_VERSION,
            "record_type": AUTHORITY_POLICY_RECORD_TYPE,
            "hash_algorithm": RATIFICATION_HASH_ALGORITHM,
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
                    same_actor_allowed=False,
                ),
            ),
            "evidence_refs": (build1_ref_factory("build1.evidence.authority-policy"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _role_assignment(build1_ref_factory: Callable[[str], GovernedRef]) -> RoleAssignmentEvent:
    return RoleAssignmentEvent.model_validate(
        {
            "schema_version": ROLE_ASSIGNMENT_SCHEMA_VERSION,
            "record_type": ROLE_ASSIGNMENT_RECORD_TYPE,
            "hash_algorithm": RATIFICATION_HASH_ALGORITHM,
            "assignment_ref": build1_ref_factory("build1.role-assignment.reviewer"),
            "actor_ref": build1_ref_factory("build1.actor.reviewer"),
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


def _authorization(build1_ref_factory: Callable[[str], GovernedRef]) -> AuthorizationEvent:
    return AuthorizationEvent.model_validate(
        {
            "schema_version": AUTHORIZATION_EVENT_SCHEMA_VERSION,
            "record_type": AUTHORIZATION_EVENT_RECORD_TYPE,
            "hash_algorithm": RATIFICATION_HASH_ALGORITHM,
            "authorization_ref": build1_ref_factory("build1.authorization.reviewer"),
            "actor_ref": build1_ref_factory("build1.actor.reviewer"),
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
            "hash_algorithm": RATIFICATION_HASH_ALGORITHM,
            "resolver_policy_ref": build1_ref_factory("build1.active-value-resolver.policy"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "algorithm_id": ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
            "evidence_refs": (build1_ref_factory("build1.evidence.active-resolver"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _observation(build1_ref_factory: Callable[[str], GovernedRef]) -> AttributedObservation:
    observation = AttributedObservation.model_validate(
        {
            "schema_version": ATTRIBUTED_OBSERVATION_SCHEMA_VERSION,
            "record_type": ATTRIBUTED_OBSERVATION_RECORD_TYPE,
            "hash_algorithm": OBSERVATION_HASH_ALGORITHM,
            "observation_ref": build1_ref_factory("build1.observation.shift-note"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "claim_text": "Second shift reports blue discoloration after the bake cycle.",
            "source_display_name": "Second shift technician",
            "recorded_actor_ref": build1_ref_factory("build1.actor.observer"),
            "recorded_at": AS_OF,
            "validation_state": "UNVALIDATED",
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "source_artifact_ref": build1_ref_factory("build1.source.shift-note"),
            "metadata": (),
            "visibility_policy": ObservationVisibilityPolicy(
                tier=2,
                advisory_context_allowed=True,
                rendered_artifact_allowed=True,
                structured_advisory_payload_allowed=False,
                tier1_evidence_allowed=False,
            ),
            "evidence_refs": (build1_ref_factory("build1.evidence.shift-note"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return finalize_attributed_observation(observation, canonicalization_policy())


def _snapshot_binding(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> Build0SnapshotBinding:
    return Build0SnapshotBinding.model_validate(
        {
            "snapshot_id": _caller_ids().snapshot_id,
            "as_of_time": AS_OF,
            "pack_ref": build1_ref_factory("build0.pack.mie"),
            "engine_policy_ref": build1_ref_factory("build0.engine-policy.mie"),
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "algorithm_refs": (build1_ref_factory("build0.algorithm.route"),),
            "unit_registry_ref": build1_ref_factory("build0.unit-registry"),
            "field_registry_ref": build1_ref_factory("build0.field-registry"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "serialization_policy_ref": build1_ref_factory("build0.serialization-policy"),
            "lexical_policy_ref": build1_ref_factory("build0.lexical-policy"),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _caller_ids() -> BridgeCallerIds:
    return BridgeCallerIds(
        run_id="run.build1.slice7",
        decision_id="decision.build1.slice7",
        case_id="case.build1.slice7",
        audit_event_id="audit.build1.slice7",
        snapshot_id="snapshot.build1.slice7",
        replay_id="replay.build1.slice7",
    )


def _attempt(build1_ref_factory: Callable[[str], GovernedRef]) -> BridgeAttemptRecord:
    return create_capture_bound_attempt(
        attempt_ref=build1_ref_factory("build1.bridge.attempt"),
        canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy"),
        caller_ids=_caller_ids(),
        capture_gate_ref=build1_ref_factory("build1.bridge.capture-gate"),
        build0_request_ref=build1_ref_factory("build1.bridge.request"),
        build0_request_hash_value="e" * 64,
    )


def _proposal_ref(logical_id: str, version_number: int) -> GovernedRef:
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v{version_number}"),
        version_number=version_number,
        content_hash="0" * 64,
    )
