from __future__ import annotations

import hashlib
from collections.abc import Callable
from decimal import Decimal

import pytest
from pydantic import ValidationError

from gptl.core.proposal_ratification import (
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
    PROPOSAL_RATIFICATION_RECORD_TYPE,
    PROPOSAL_RATIFICATION_SCHEMA_VERSION,
    RATIFICATION_INTEGRITY_FAILURE_REASON_ID,
    RATIFY_PROPOSAL_ACTION_ID,
    ROLE_ASSIGNMENT_RECORD_TYPE,
    ROLE_ASSIGNMENT_SCHEMA_VERSION,
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
from gptl.core.proposals import TypedValueProposal, finalize_typed_value_proposal
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import TermId
from gptl.slice1_fixture import canonicalization_policy
from gptl.tools.agents import (
    CAPTURE_BACKEND_CONTRACT_VIOLATION_REASON_ID,
    CAPTURE_BACKEND_FAILED_REASON_ID,
    CAPTURE_BACKEND_UNAVAILABLE_REASON_ID,
    CAPTURE_SOURCE_TAMPERED_REASON_ID,
    CAPTURE_TOOL_NOT_ASSIGNED_REASON_ID,
    ToolAnalysisTask,
    spectral_tool_agents,
    visual_tool_agent,
)
from gptl.tools.capture import (
    CAPTURE_FINDINGS_REJECTED_REASON_ID,
    FINDING_MEASUREMENT_CLASS_NOT_ALLOWED_REASON_ID,
    OBSERVATION_CLASS_METADATA_KEY,
    CandidateMeasurement,
    CandidateObservation,
    ToolAgentIdentity,
    ToolAnalysisFindings,
    ToolAnalysisOutcome,
    ToolAnalysisUnavailable,
    ToolCaptureBundle,
    ToolCaptureRefused,
    ToolCaptureRequest,
)
from gptl.tools.standard_pack import (
    ROLE_SPECTRAL_CAPTURE_AGENT,
    ROLE_VISUAL_CAPTURE_AGENT,
    standard_tool_registry,
)

AS_OF = "2026-07-01T12:00:00.000Z"
SINCE = "2026-06-01T00:00:00.000Z"
SEM_IMAGE_BYTES = b"synthetic-sem-micrograph-fixture-bytes"
SEM_IMAGE_HASH = hashlib.sha256(SEM_IMAGE_BYTES).hexdigest()
REVIEWER_ROLE = TermId("role.materials-reviewer")


class _FindingsBackend:
    def __init__(self, findings: ToolAnalysisFindings) -> None:
        self.findings = findings

    def analyze(self, task: ToolAnalysisTask) -> ToolAnalysisOutcome:
        return self.findings


class _UnavailableBackend:
    def analyze(self, task: ToolAnalysisTask) -> ToolAnalysisOutcome:
        return ToolAnalysisUnavailable(
            status="UNAVAILABLE",
            reason_id=TermId("build2.backend.model-endpoint-unreachable"),
        )


class _RaisingBackend:
    def analyze(self, task: ToolAnalysisTask) -> ToolAnalysisOutcome:
        raise RuntimeError("backend fault")


class _ContractViolatingBackend:
    def analyze(self, task: ToolAnalysisTask) -> ToolAnalysisOutcome:
        return "not a findings model"  # type: ignore[return-value]


def test_visual_agent_captures_sem_micrograph_as_governed_records(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    agent = _visual_agent(build2_ref_factory)
    bundle = agent.capture(
        _sem_request(build2_ref_factory),
        build2_ref_factory,
        canonicalization_policy(),
    )

    assert isinstance(bundle, ToolCaptureBundle)
    assert len(bundle.proposals) == 1
    proposal = bundle.proposals[0]
    assert proposal.proposal_method == "MODEL_ASSISTED"
    assert proposal.validation_state == "PROPOSED"
    assert proposal.claimed_proposer_ref == agent.identity.actor_ref
    assert proposal.source_artifact_ref == bundle.source_artifact_ref
    assert proposal.proposal_ref.content_hash != "0" * 64

    assert len(bundle.observations) == 1
    observation = bundle.observations[0]
    assert observation.validation_state == "UNVALIDATED"
    assert observation.recorded_actor_ref == agent.identity.actor_ref
    assert observation.visibility_policy.tier1_evidence_allowed is False
    class_entries = [
        entry
        for entry in observation.metadata
        if entry.key == OBSERVATION_CLASS_METADATA_KEY
    ]
    assert [entry.value for entry in class_entries] == [
        "observation-class.fractography-features"
    ]


def test_visual_agent_serves_the_whole_imaging_family_and_nothing_else(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    agent = _visual_agent(build2_ref_factory)

    assert agent.tool_type_ids == (
        TermId("tool.fib"),
        TermId("tool.optical-microscopy"),
        TermId("tool.sem"),
        TermId("tool.tem"),
    )

    xrd_request = _sem_request(build2_ref_factory).model_copy(
        update={"tool_type_id": TermId("tool.xrd")}
    )
    refused = agent.capture(xrd_request, build2_ref_factory, canonicalization_policy())
    assert isinstance(refused, ToolCaptureRefused)
    assert refused.reason_id == CAPTURE_TOOL_NOT_ASSIGNED_REASON_ID


def test_spectral_factory_builds_one_agent_per_spectral_tool(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    registry = standard_tool_registry(canonicalization_policy())
    identity = ToolAgentIdentity(
        actor_ref=build2_ref_factory("build2.actor.spectral-agent"),
        role_id=ROLE_SPECTRAL_CAPTURE_AGENT,
        display_name="Spectral capture agent",
    )
    agents = spectral_tool_agents(registry, identity, lambda tool: _UnavailableBackend())

    assert len(agents) == len(registry.tools_for_modality("SPECTRAL"))
    assert all(len(agent.tool_type_ids) == 1 for agent in agents)
    covered = tuple(agent.tool_type_ids[0] for agent in agents)
    assert covered == tuple(
        tool.tool_type_id for tool in registry.tools_for_modality("SPECTRAL")
    )


def test_tampered_source_bytes_are_refused_before_the_backend_runs(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    agent = _visual_agent(build2_ref_factory, backend=_RaisingBackend())
    request = _sem_request(build2_ref_factory).model_copy(
        update={"source_bytes": b"tampered-bytes"}
    )

    result = agent.capture(request, build2_ref_factory, canonicalization_policy())

    assert isinstance(result, ToolCaptureRefused)
    assert result.reason_id == CAPTURE_SOURCE_TAMPERED_REASON_ID


@pytest.mark.parametrize(
    ("backend", "expected_reason"),
    (
        (_UnavailableBackend(), CAPTURE_BACKEND_UNAVAILABLE_REASON_ID),
        (_RaisingBackend(), CAPTURE_BACKEND_FAILED_REASON_ID),
        (_ContractViolatingBackend(), CAPTURE_BACKEND_CONTRACT_VIOLATION_REASON_ID),
    ),
)
def test_backend_faults_become_typed_refusals(
    build2_ref_factory: Callable[[str], GovernedRef],
    backend: object,
    expected_reason: TermId,
) -> None:
    agent = _visual_agent(build2_ref_factory, backend=backend)

    result = agent.capture(
        _sem_request(build2_ref_factory), build2_ref_factory, canonicalization_policy()
    )

    assert isinstance(result, ToolCaptureRefused)
    assert result.reason_id == expected_reason


def test_one_disallowed_finding_rejects_the_whole_capture(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    good = _grain_size_measurement(build2_ref_factory)
    bad = good.model_copy(
        update={"measurement_class_id": TermId("measurement.residual-stress")}
    )
    findings = ToolAnalysisFindings(status="FINDINGS", measurements=(good, bad), observations=())
    agent = _visual_agent(build2_ref_factory, backend=_FindingsBackend(findings))

    result = agent.capture(
        _sem_request(build2_ref_factory), build2_ref_factory, canonicalization_policy()
    )

    assert isinstance(result, ToolCaptureRefused)
    assert result.reason_id == CAPTURE_FINDINGS_REJECTED_REASON_ID
    assert [
        (issue.finding_index, issue.reason_id) for issue in result.finding_issues
    ] == [(1, FINDING_MEASUREMENT_CLASS_NOT_ALLOWED_REASON_ID)]


def test_backend_cannot_express_a_confidence_field(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    measurement_payload = _grain_size_measurement(build2_ref_factory).model_dump(mode="python")
    measurement_payload["model_score"] = "0.97"
    with pytest.raises(ValidationError):
        CandidateMeasurement.model_validate(measurement_payload)

    with pytest.raises(ValidationError, match="confidence or score"):
        CandidateObservation.model_validate(
            {
                "observation_class_id": "observation-class.fractography-features",
                "claim_text": "Dimpled rupture across the fracture surface.",
                "metadata": ({"key": "modelConfidence", "value": "high"},),
            }
        )


def test_agent_cannot_ratify_its_own_capture_but_a_human_can(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    # The crown property of the tool layer: an agent's capture converges on the same
    # Slice 4 human gate as everything else, and separation of duties bars the agent
    # actor from ratifying its own proposal even when it holds a reviewer role.
    agent = _visual_agent(build2_ref_factory)
    bundle = agent.capture(
        _sem_request(build2_ref_factory), build2_ref_factory, canonicalization_policy()
    )
    assert isinstance(bundle, ToolCaptureBundle)

    ready = finalize_typed_value_proposal(
        bundle.proposals[0].model_copy(update={"validation_state": "READY_FOR_RATIFICATION"}),
        canonicalization_policy(),
    )
    agent_actor = agent.identity.actor_ref
    human_reviewer = build2_ref_factory("build2.actor.human-reviewer")

    self_ratified = _evaluate_ratification(
        build2_ref_factory, ready, ratifier=agent_actor, proposer=agent_actor
    )
    assert self_ratified.status == "INTEGRITY_FAILURE"
    assert self_ratified.reason_id == RATIFICATION_INTEGRITY_FAILURE_REASON_ID
    assert self_ratified.diagnostics == (AUTHORITY_INELIGIBLE_REASON_ID,)
    assert self_ratified.active_proposal_refs == ()

    human_ratified = _evaluate_ratification(
        build2_ref_factory, ready, ratifier=human_reviewer, proposer=agent_actor
    )
    assert human_ratified.status == "RESOLVED"
    assert human_ratified.active_proposal_refs == (ready.proposal_ref,)


# ── fixtures ───────────────────────────────────────────────────────────────────────────


def _visual_agent(
    build2_ref_factory: Callable[[str], GovernedRef],
    *,
    backend: object | None = None,
):
    registry = standard_tool_registry(canonicalization_policy())
    identity = ToolAgentIdentity(
        actor_ref=build2_ref_factory("build2.actor.visual-agent"),
        role_id=ROLE_VISUAL_CAPTURE_AGENT,
        display_name="Visual capture agent",
    )
    default_findings = ToolAnalysisFindings(
        status="FINDINGS",
        measurements=(_grain_size_measurement(build2_ref_factory),),
        observations=(
            CandidateObservation(
                observation_class_id=TermId("observation-class.fractography-features"),
                claim_text="Dimpled rupture across the fracture surface near the aft edge.",
            ),
        ),
    )
    return visual_tool_agent(
        registry,
        identity,
        backend if backend is not None else _FindingsBackend(default_findings),  # type: ignore[arg-type]
    )


def _sem_request(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> ToolCaptureRequest:
    return ToolCaptureRequest.model_validate(
        {
            "tool_type_id": "tool.sem",
            "source_artifact_ref": build2_ref_factory("build2.source.sem-micrograph-1"),
            "source_class_id": "source-class.sem-micrograph",
            "source_raw_byte_hash": SEM_IMAGE_HASH,
            "source_bytes": SEM_IMAGE_BYTES,
            "evidence_scope_ref": build2_ref_factory("build2.scope.candidate"),
            "canonicalization_policy_ref": build2_ref_factory("build2.canonicalization.policy"),
            "recorded_at": AS_OF,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _grain_size_measurement(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> CandidateMeasurement:
    target_ref = build2_ref_factory("build2.target.specimen-1")
    return CandidateMeasurement.model_validate(
        {
            "measurement_class_id": "measurement.grain-size",
            "identity": {
                "identity_mode": "EXISTING_GOVERNED_REF",
                "target_ref": target_ref,
            },
            "target": {
                "target_record_type": "record.material-specimen",
                "target_logical_id": target_ref.logical_id,
                "target_schema_version": "schema.specimen.v1",
                "semantic_field_path": "field.grain-size",
                "context_key": {"replicate": 1},
            },
            "proposed_value": {
                "kind": "NUMERIC",
                "value": Decimal("11.5000"),
                "unit_id": "unit.astm-grain-size-number",
            },
            "evidence_location": {
                "locator_class": "RAW_BYTE_RANGE",
                "source_artifact_ref": build2_ref_factory("build2.source.sem-micrograph-1"),
                "start_byte": 0,
                "end_byte": len(SEM_IMAGE_BYTES),
                "raw_byte_hash": SEM_IMAGE_HASH,
            },
        }
    )


def _evaluate_ratification(
    build2_ref_factory: Callable[[str], GovernedRef],
    proposal: TypedValueProposal,
    *,
    ratifier: GovernedRef,
    proposer: GovernedRef,
):
    policy = canonicalization_policy()
    event = ProposalRatificationEvent.model_validate(
        {
            "schema_version": PROPOSAL_RATIFICATION_SCHEMA_VERSION,
            "record_type": PROPOSAL_RATIFICATION_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "ratification_event_ref": build2_ref_factory("build2.ratification.1"),
            "canonicalization_policy_ref": build2_ref_factory("build2.canonicalization.policy"),
            "proposal_ref": proposal.proposal_ref,
            "proposal_content_hash": proposal.proposal_ref.content_hash,
            "proposed_value_hash": proposed_value_hash(proposal, policy),
            "ratifying_actor_ref": ratifier,
            "ratifying_role_id": REVIEWER_ROLE,
            "authority_policy_ref": build2_ref_factory("build2.authority.policy"),
            "authorization_event_ref": build2_ref_factory("build2.authorization.ratifier"),
            "decision": "RATIFIED",
            "effective_at": AS_OF,
            "recorded_at": AS_OF,
            "evidence_refs": (build2_ref_factory("build2.evidence.review"),),
            "claimed_proposer_ref": proposer,
            "claimed_ratifier_ref": ratifier,
        },
        context={"canonicalization_policy": policy},
    )
    actors = tuple(
        ActorRecord.model_validate(
            {
                "schema_version": ACTOR_RECORD_SCHEMA_VERSION,
                "record_type": ACTOR_RECORD_RECORD_TYPE,
                "hash_algorithm": HASH_ALGORITHM,
                "actor_ref": actor_ref,
                "canonicalization_policy_ref": build2_ref_factory(
                    "build2.canonicalization.policy"
                ),
                "lifecycle_state": "ACTIVE",
                "effective_at": SINCE,
                "recorded_at": SINCE,
                "evidence_refs": (build2_ref_factory("build2.evidence.actor-registry"),),
            },
            context={"canonicalization_policy": policy},
        )
        for actor_ref in {
            (ratifier.logical_id, ratifier.version_id): ratifier,
            (proposer.logical_id, proposer.version_id): proposer,
        }.values()
    )
    authority_policy = AuthorityPolicy.model_validate(
        {
            "schema_version": AUTHORITY_POLICY_SCHEMA_VERSION,
            "record_type": AUTHORITY_POLICY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "policy_ref": build2_ref_factory("build2.authority.policy"),
            "canonicalization_policy_ref": build2_ref_factory("build2.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "effective_at": SINCE,
            "actor_refs": tuple(actor.actor_ref for actor in actors),
            "permissions": (
                AuthorityPermission(
                    role_id=REVIEWER_ROLE,
                    action_id=RATIFY_PROPOSAL_ACTION_ID,
                    scope_ref=build2_ref_factory("build2.scope.candidate"),
                    target_record_types=(TermId("record.material-specimen"),),
                    same_actor_allowed=False,
                ),
            ),
            "evidence_refs": (build2_ref_factory("build2.evidence.authority-policy"),),
        },
        context={"canonicalization_policy": policy},
    )
    role_assignment = RoleAssignmentEvent.model_validate(
        {
            "schema_version": ROLE_ASSIGNMENT_SCHEMA_VERSION,
            "record_type": ROLE_ASSIGNMENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "assignment_ref": build2_ref_factory("build2.role-assignment.ratifier"),
            "actor_ref": ratifier,
            "role_id": REVIEWER_ROLE,
            "authority_policy_ref": build2_ref_factory("build2.authority.policy"),
            "scope_ref": build2_ref_factory("build2.scope.candidate"),
            "state": "ACTIVE",
            "effective_at": SINCE,
            "recorded_at": SINCE,
            "evidence_refs": (build2_ref_factory("build2.evidence.role-assignment"),),
        },
        context={"canonicalization_policy": policy},
    )
    authorization = AuthorizationEvent.model_validate(
        {
            "schema_version": AUTHORIZATION_EVENT_SCHEMA_VERSION,
            "record_type": AUTHORIZATION_EVENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "authorization_ref": build2_ref_factory("build2.authorization.ratifier"),
            "actor_ref": ratifier,
            "role_id": REVIEWER_ROLE,
            "action_id": RATIFY_PROPOSAL_ACTION_ID,
            "authority_policy_ref": build2_ref_factory("build2.authority.policy"),
            "scope_ref": build2_ref_factory("build2.scope.candidate"),
            "target_record_type": "record.material-specimen",
            "state": "ACTIVE",
            "effective_at": SINCE,
            "recorded_at": SINCE,
            "evidence_refs": (build2_ref_factory("build2.evidence.authorization"),),
        },
        context={"canonicalization_policy": policy},
    )
    resolver_policy = ActiveValueResolverPolicy.model_validate(
        {
            "schema_version": ACTIVE_VALUE_RESOLVER_POLICY_SCHEMA_VERSION,
            "record_type": ACTIVE_VALUE_RESOLVER_POLICY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "resolver_policy_ref": build2_ref_factory("build2.active-value-resolver.policy"),
            "canonicalization_policy_ref": build2_ref_factory("build2.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "algorithm_id": ACTIVE_VALUE_STATE_HASH_ALGORITHM_ID,
            "evidence_refs": (build2_ref_factory("build2.evidence.active-resolver"),),
        },
        context={"canonicalization_policy": policy},
    )
    return evaluate_active_values(
        (proposal,),
        (event,),
        actors,
        authority_policy,
        (role_assignment,),
        (authorization,),
        resolver_policy,
        build2_ref_factory("build2.scope.candidate"),
        AS_OF,
        policy,
    )
