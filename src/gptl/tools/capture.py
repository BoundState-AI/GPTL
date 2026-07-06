"""Build 2 tool capture contract: backend findings become governed proposals.

``assemble_tool_capture`` is the deterministic seam between an analysis backend (model,
parser, or human transcription UI) and the Build 1 record system. Given validated
findings it constructs real ``TypedValueProposal``s (``MODEL_ASSISTED``, state
``PROPOSED``, authored by the agent actor) and real ``AttributedObservation``s — nothing
more. The bundle model enforces those properties structurally, so a tool agent cannot
mint a ratified value, advance its own proposal, or touch Build 0 Tier 1: everything it
emits still faces the Slice 3 validator and the Slice 4 human ratification gate, where
separation of duties bars the agent actor from ratifying its own capture.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.observations import (
    ATTRIBUTED_OBSERVATION_RECORD_TYPE,
    ATTRIBUTED_OBSERVATION_SCHEMA_VERSION,
    AttributedObservation,
    ObservationMetadataEntry,
    ObservationVisibilityPolicy,
    finalize_attributed_observation,
)
from gptl.core.observations import HASH_ALGORITHM as OBSERVATION_HASH_ALGORITHM
from gptl.core.proposals import HASH_ALGORITHM as PROPOSAL_HASH_ALGORITHM
from gptl.core.proposals import (
    TYPED_VALUE_PROPOSAL_RECORD_TYPE,
    TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
    ProposalEvidenceLocation,
    ProposalIdentity,
    ProposalOnlyEvidence,
    ProposalTarget,
    RawByteRangeEvidence,
    TypedValueProposal,
    finalize_typed_value_proposal,
)
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    NonNegativeInt,
    Sha256Hex,
    TermId,
)
from gptl.mie.predicates import ScalarValue
from gptl.tools.taxonomy import AnalyticalToolDefinition

CAPTURE_READY_REASON_ID: Final = TermId("build2.capture.ready")
CAPTURE_SOURCE_CLASS_MISMATCH_REASON_ID: Final = TermId("build2.capture.source-class-mismatch")
CAPTURE_AGENT_ROLE_MISMATCH_REASON_ID: Final = TermId("build2.capture.agent-role-mismatch")
CAPTURE_METHOD_NOT_ALLOWED_REASON_ID: Final = TermId(
    "build2.capture.model-assisted-not-allowed"
)
CAPTURE_FINDINGS_REJECTED_REASON_ID: Final = TermId("build2.capture.findings-rejected")

FINDING_MEASUREMENT_CLASS_NOT_ALLOWED_REASON_ID: Final = TermId(
    "build2.finding.measurement-class-not-allowed"
)
FINDING_OBSERVATION_CLASS_NOT_ALLOWED_REASON_ID: Final = TermId(
    "build2.finding.observation-class-not-allowed"
)
FINDING_EVIDENCE_WRONG_ARTIFACT_REASON_ID: Final = TermId(
    "build2.finding.evidence-wrong-artifact"
)
FINDING_EVIDENCE_PROPOSAL_ONLY_REASON_ID: Final = TermId(
    "build2.finding.evidence-proposal-only"
)
FINDING_EVIDENCE_HASH_MISMATCH_REASON_ID: Final = TermId(
    "build2.finding.evidence-hash-mismatch"
)
FINDING_METADATA_KEY_RESERVED_REASON_ID: Final = TermId(
    "build2.finding.metadata-key-reserved"
)

OBSERVATION_CLASS_METADATA_KEY: Final = "observation-class"


class ToolAgentIdentity(BaseModel):
    """The acting agent, as a governed actor with a governed role."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_ref: GovernedRef
    role_id: TermId
    display_name: str

    @model_validator(mode="after")
    def validate_display_name(self) -> ToolAgentIdentity:
        if not self.display_name.strip():
            raise ValueError("agent display name must be nonempty")
        return self


class CandidateMeasurement(BaseModel):
    """A quantitative finding a backend proposes for governed capture.

    ``extra="forbid"`` and the absence of any score-like field make it structurally
    impossible for a backend to attach fabricated model self-assessments.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    measurement_class_id: TermId
    identity: ProposalIdentity
    target: ProposalTarget
    proposed_value: ScalarValue
    evidence_location: ProposalEvidenceLocation


class CandidateObservation(BaseModel):
    """A qualitative, attributed claim a backend proposes as Tier-2 context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_class_id: TermId
    claim_text: str
    metadata: tuple[ObservationMetadataEntry, ...] = ()

    @model_validator(mode="after")
    def validate_claim(self) -> CandidateObservation:
        if not self.claim_text.strip():
            raise ValueError("observation claim text must be nonempty")
        return self


class ToolAnalysisFindings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["FINDINGS"]
    measurements: tuple[CandidateMeasurement, ...]
    observations: tuple[CandidateObservation, ...]

    @model_validator(mode="after")
    def validate_findings(self) -> ToolAnalysisFindings:
        if not self.measurements and not self.observations:
            raise ValueError("findings must contain at least one measurement or observation")
        return self


class ToolAnalysisUnavailable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["UNAVAILABLE"]
    reason_id: TermId


ToolAnalysisOutcome = ToolAnalysisFindings | ToolAnalysisUnavailable


class ToolCaptureRequest(BaseModel):
    """One registered source artifact offered to a tool agent for capture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_type_id: TermId
    source_artifact_ref: GovernedRef
    source_class_id: TermId
    source_raw_byte_hash: Sha256Hex
    source_bytes: bytes
    evidence_scope_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    recorded_at: CanonicalTimestamp
    production_context_ref: GovernedRef | None = None


class ToolFindingIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_kind: Literal["MEASUREMENT", "OBSERVATION"]
    finding_index: NonNegativeInt
    reason_id: TermId


class ToolCaptureBundle(BaseModel):
    """A successful capture: proposals and observations, both pre-ratification.

    The after-validator is the structural firewall for this layer: every proposal is
    MODEL_ASSISTED, in state PROPOSED, and authored by the capturing agent; every
    observation is UNVALIDATED and recorded by that same agent. Advancing a proposal is
    Slice 3's deterministic validator; making it decision-effective is Slice 4's human
    ratification gate — never this bundle.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["CAPTURE_READY"]
    reason_id: TermId
    tool_ref: GovernedRef
    agent_actor_ref: GovernedRef
    source_artifact_ref: GovernedRef
    proposals: tuple[TypedValueProposal, ...]
    observations: tuple[AttributedObservation, ...]

    @model_validator(mode="after")
    def validate_bundle(self) -> ToolCaptureBundle:
        for proposal in self.proposals:
            if proposal.proposal_method != "MODEL_ASSISTED":
                raise ValueError("tool capture proposals must be MODEL_ASSISTED")
            if proposal.validation_state != "PROPOSED":
                raise ValueError("tool capture proposals must start in PROPOSED state")
            if proposal.claimed_proposer_ref != self.agent_actor_ref:
                raise ValueError("tool capture proposals must be authored by the agent actor")
            if proposal.source_artifact_ref != self.source_artifact_ref:
                raise ValueError("tool capture proposals must cite the captured artifact")
        for observation in self.observations:
            if observation.validation_state != "UNVALIDATED":
                raise ValueError("tool capture observations must start UNVALIDATED")
            if observation.recorded_actor_ref != self.agent_actor_ref:
                raise ValueError("tool capture observations must be recorded by the agent actor")
        if not self.proposals and not self.observations:
            raise ValueError("capture bundle must contain at least one proposal or observation")
        return self


class ToolCaptureRefused(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["CAPTURE_REFUSED"]
    reason_id: TermId
    tool_type_id: TermId
    source_artifact_ref: GovernedRef | None = None
    finding_issues: tuple[ToolFindingIssue, ...] = ()


ToolCaptureResult = ToolCaptureBundle | ToolCaptureRefused


def agent_observation_visibility_policy() -> ObservationVisibilityPolicy:
    """Conservative Tier-2 visibility for agent-recorded observations."""
    return ObservationVisibilityPolicy(
        tier=2,
        advisory_context_allowed=True,
        rendered_artifact_allowed=True,
        structured_advisory_payload_allowed=False,
        tier1_evidence_allowed=False,
    )


def assemble_tool_capture(
    tool: AnalyticalToolDefinition,
    agent: ToolAgentIdentity,
    request: ToolCaptureRequest,
    findings: ToolAnalysisFindings,
    ref_factory: Callable[[str], GovernedRef],
    canonicalization_policy: CanonicalizationPolicy,
) -> ToolCaptureResult:
    """Deterministically assemble governed records from validated backend findings.

    All-or-nothing: any invalid finding refuses the whole capture with each offending
    finding named, rather than silently admitting the clean subset.
    """
    if request.source_class_id not in tool.emitted_source_class_ids:
        return _refused(tool, request, CAPTURE_SOURCE_CLASS_MISMATCH_REASON_ID)
    if agent.role_id != tool.agent_role_id:
        return _refused(tool, request, CAPTURE_AGENT_ROLE_MISMATCH_REASON_ID)
    if "MODEL_ASSISTED" not in tool.allowed_proposal_methods:
        return _refused(tool, request, CAPTURE_METHOD_NOT_ALLOWED_REASON_ID)

    issues = _finding_issues(tool, request, findings)
    if issues:
        return ToolCaptureRefused(
            status="CAPTURE_REFUSED",
            reason_id=CAPTURE_FINDINGS_REJECTED_REASON_ID,
            tool_type_id=tool.tool_type_id,
            source_artifact_ref=request.source_artifact_ref,
            finding_issues=issues,
        )

    context = {"canonicalization_policy": canonicalization_policy}
    creation_event_ref = ref_factory(
        f"{request.source_artifact_ref.logical_id}.agent-capture-event"
    )

    proposals = []
    for index, finding in enumerate(findings.measurements):
        proposal = TypedValueProposal.model_validate(
            {
                "schema_version": TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
                "record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
                "hash_algorithm": PROPOSAL_HASH_ALGORITHM,
                "proposal_ref": ref_factory(
                    f"{request.source_artifact_ref.logical_id}.agent-proposal.{index + 1}"
                ),
                "canonicalization_policy_ref": request.canonicalization_policy_ref,
                "evidence_scope_ref": request.evidence_scope_ref,
                "source_artifact_ref": request.source_artifact_ref,
                "source_raw_byte_hash": request.source_raw_byte_hash,
                "identity": finding.identity,
                "claimed_proposer_ref": agent.actor_ref,
                "proposal_method": "MODEL_ASSISTED",
                "creation_event_ref": creation_event_ref,
                "target": finding.target,
                "proposed_value": finding.proposed_value,
                "evidence_location": finding.evidence_location,
                "validation_state": "PROPOSED",
            },
            context=context,
        )
        proposals.append(finalize_typed_value_proposal(proposal, canonicalization_policy))

    observations = []
    for index, noted in enumerate(findings.observations):
        class_entry = ObservationMetadataEntry(
            key=OBSERVATION_CLASS_METADATA_KEY,
            value=str(noted.observation_class_id),
        )
        observation = AttributedObservation.model_validate(
            {
                "schema_version": ATTRIBUTED_OBSERVATION_SCHEMA_VERSION,
                "record_type": ATTRIBUTED_OBSERVATION_RECORD_TYPE,
                "hash_algorithm": OBSERVATION_HASH_ALGORITHM,
                "observation_ref": ref_factory(
                    f"{request.source_artifact_ref.logical_id}.agent-observation.{index + 1}"
                ),
                "canonicalization_policy_ref": request.canonicalization_policy_ref,
                "claim_text": noted.claim_text,
                "source_display_name": agent.display_name,
                "source_role_id": agent.role_id,
                "recorded_actor_ref": agent.actor_ref,
                "recorded_at": request.recorded_at,
                "production_context_ref": request.production_context_ref,
                "validation_state": "UNVALIDATED",
                "evidence_scope_ref": request.evidence_scope_ref,
                "source_artifact_ref": request.source_artifact_ref,
                "metadata": (class_entry, *noted.metadata),
                "visibility_policy": agent_observation_visibility_policy(),
                "evidence_refs": (request.source_artifact_ref,),
            },
            context=context,
        )
        observations.append(
            finalize_attributed_observation(observation, canonicalization_policy)
        )

    return ToolCaptureBundle(
        status="CAPTURE_READY",
        reason_id=CAPTURE_READY_REASON_ID,
        tool_ref=tool.tool_ref,
        agent_actor_ref=agent.actor_ref,
        source_artifact_ref=request.source_artifact_ref,
        proposals=tuple(proposals),
        observations=tuple(observations),
    )


def _finding_issues(
    tool: AnalyticalToolDefinition,
    request: ToolCaptureRequest,
    findings: ToolAnalysisFindings,
) -> tuple[ToolFindingIssue, ...]:
    issues: list[ToolFindingIssue] = []
    for index, measurement in enumerate(findings.measurements):
        if measurement.measurement_class_id not in tool.measurement_class_ids:
            issues.append(
                _issue("MEASUREMENT", index, FINDING_MEASUREMENT_CLASS_NOT_ALLOWED_REASON_ID)
            )
        location = measurement.evidence_location
        if isinstance(location, ProposalOnlyEvidence):
            issues.append(_issue("MEASUREMENT", index, FINDING_EVIDENCE_PROPOSAL_ONLY_REASON_ID))
            continue
        if location.source_artifact_ref != request.source_artifact_ref:
            issues.append(_issue("MEASUREMENT", index, FINDING_EVIDENCE_WRONG_ARTIFACT_REASON_ID))
        if (
            isinstance(location, RawByteRangeEvidence)
            and location.raw_byte_hash != request.source_raw_byte_hash
        ):
            issues.append(_issue("MEASUREMENT", index, FINDING_EVIDENCE_HASH_MISMATCH_REASON_ID))

    allowed_observation_classes = set(tool.observation_class_ids) | set(
        tool.measurement_class_ids
    )
    for index, observation in enumerate(findings.observations):
        if observation.observation_class_id not in allowed_observation_classes:
            issues.append(
                _issue("OBSERVATION", index, FINDING_OBSERVATION_CLASS_NOT_ALLOWED_REASON_ID)
            )
        if any(
            entry.key == OBSERVATION_CLASS_METADATA_KEY for entry in observation.metadata
        ):
            issues.append(_issue("OBSERVATION", index, FINDING_METADATA_KEY_RESERVED_REASON_ID))
    return tuple(issues)


def _issue(
    kind: Literal["MEASUREMENT", "OBSERVATION"],
    index: int,
    reason_id: TermId,
) -> ToolFindingIssue:
    return ToolFindingIssue(finding_kind=kind, finding_index=index, reason_id=reason_id)


def _refused(
    tool: AnalyticalToolDefinition,
    request: ToolCaptureRequest,
    reason_id: TermId,
) -> ToolCaptureRefused:
    return ToolCaptureRefused(
        status="CAPTURE_REFUSED",
        reason_id=reason_id,
        tool_type_id=tool.tool_type_id,
        source_artifact_ref=request.source_artifact_ref,
    )
