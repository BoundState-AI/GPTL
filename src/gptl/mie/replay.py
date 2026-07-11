"""
Module: Historical Replay
Purpose: Exact-input historical replay and integrity contracts.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from gptl.core.audit import PreflightRefusalAuditEvent, SnapshotDecisionAuditEvent
from gptl.core.canonical import CanonicalizationError, canonical_bytes
from gptl.core.pack_registry import ExactPackRegistry
from gptl.core.persistence import (
    SCHEMA_VERSION,
    SLICE3_RUN_SCHEMA_VERSION,
    SLICE4_RUN_SCHEMA_VERSION,
    SLICE5_RUN_SCHEMA_VERSION,
    SLICE6_RUN_SCHEMA_VERSION,
    SNAPSHOT_RUN_SCHEMA_VERSION,
    PersistenceIntegrityError,
    PostgresRunStore,
    ReplayCapsulePayload,
    StoredRun,
)
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    EvidenceLocator,
    OpaqueId,
    Sha256Hex,
    TermId,
    VersionId,
)
from gptl.core.snapshot import KnowledgeSnapshot, snapshot_hash
from gptl.mie.advisory import AdvisoryQuery
from gptl.mie.schema import AdvisoryDecision, MIEOutput, Tier1Decision, Tier1Output
from gptl.mie.service import (
    SafeRefusalPolicy,
    SafeRefusalRequest,
    build_safe_refusal,
)
from gptl.mie.slice2_service import (
    Slice2ExecutionResult,
    Slice2Policy,
    Slice2Request,
    Slice2Runtime,
    build_candidate_preservation,
)
from gptl.mie.slice3_service import Slice3Policy, Slice3Runtime, build_msa_calibration_gate
from gptl.mie.slice4_service import Slice4Policy, Slice4Runtime, build_artifact_confirmation
from gptl.mie.slice5_service import Slice5Policy, Slice5Runtime, build_honest_negative
from gptl.mie.slice6_service import (
    Slice6Policy,
    Slice6Runtime,
    build_tier2_advisory,
)

ReplayRecipeKind = Literal[
    "SAFE_REFUSAL",
    "CANDIDATE_PRESERVATION",
    "MSA_GATE",
    "ARTIFACT_CONFIRMATION",
    "HONEST_NEGATIVE",
    "TIER2_ADVISORY",
]
PackLifecycleState = Literal["PUBLISHED", "DEPRECATED", "REVOKED"]


class ReplayPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    algorithm_id: Literal["BUILD0_EXACT_REPLAY_V1"]
    recipe_schema_version: Literal["gptl.replay-recipe.v1"]
    canonicalization_policy: CanonicalizationPolicy
    run_missing_reason_id: TermId
    capsule_missing_reason_id: TermId
    stored_content_invalid_reason_id: TermId
    recipe_invalid_reason_id: TermId
    algorithm_unavailable_reason_id: TermId
    replay_mismatch_reason_id: TermId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_reason_ids(self) -> ReplayPolicy:
        reasons = (
            self.run_missing_reason_id,
            self.capsule_missing_reason_id,
            self.stored_content_invalid_reason_id,
            self.recipe_invalid_reason_id,
            self.algorithm_unavailable_reason_id,
            self.replay_mismatch_reason_id,
        )
        if len(reasons) != len(set(reasons)):
            raise ValueError("replay integrity reasons must be distinct")
        _validate_refs(self.evidence_refs, "replay policy evidence")
        return self


class SafeRefusalReplayRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recipe_kind: Literal["SAFE_REFUSAL"]
    request: SafeRefusalRequest
    pack_registry: ExactPackRegistry
    policy: SafeRefusalPolicy


class CandidatePreservationReplayRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recipe_kind: Literal["CANDIDATE_PRESERVATION"]
    request: Slice2Request
    runtime: Slice2Runtime
    policy: Slice2Policy


class MSAGateReplayRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recipe_kind: Literal["MSA_GATE"]
    request: Slice2Request
    runtime: Slice3Runtime
    policy: Slice3Policy


class ArtifactConfirmationReplayRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recipe_kind: Literal["ARTIFACT_CONFIRMATION"]
    request: Slice2Request
    runtime: Slice4Runtime
    policy: Slice4Policy


class HonestNegativeReplayRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recipe_kind: Literal["HONEST_NEGATIVE"]
    request: Slice2Request
    runtime: Slice5Runtime
    policy: Slice5Policy


class Tier2AdvisoryReplayRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recipe_kind: Literal["TIER2_ADVISORY"]
    request: Slice2Request
    query: AdvisoryQuery
    runtime: Slice6Runtime
    policy: Slice6Policy


ReplayRecipe = Annotated[
    SafeRefusalReplayRecipe
    | CandidatePreservationReplayRecipe
    | MSAGateReplayRecipe
    | ArtifactConfirmationReplayRecipe
    | HonestNegativeReplayRecipe
    | Tier2AdvisoryReplayRecipe,
    Field(discriminator="recipe_kind"),
]
REPLAY_RECIPE_ADAPTER: TypeAdapter[ReplayRecipe] = TypeAdapter(ReplayRecipe)


class ReplayVerified(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    replay_id: OpaqueId
    run_id: OpaqueId
    status: Literal["VERIFIED"]
    algorithm_id: Literal["BUILD0_EXACT_REPLAY_V1"]
    replay_policy_ref: GovernedRef
    recipe_schema_version: Literal["gptl.replay-recipe.v1"]
    source_run_schema_version: OpaqueId
    output_hash: Sha256Hex
    snapshot_hash: Sha256Hex | None
    bound_version_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_snapshot_shape(self) -> ReplayVerified:
        if (self.snapshot_hash is None) != (not self.bound_version_refs):
            raise ValueError("replay snapshot hash and bound versions must appear together")
        if sorted_unique_refs(self.bound_version_refs) != self.bound_version_refs:
            raise ValueError("replay bound versions must be unique and sorted")
        return self


class ReplayIntegrityFailure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    replay_id: OpaqueId
    run_id: OpaqueId
    status: Literal["INTEGRITY_FAILURE"]
    algorithm_id: Literal["BUILD0_EXACT_REPLAY_V1"]
    replay_policy_ref: GovernedRef
    reason_id: TermId


ReplayResult = Annotated[
    ReplayVerified | ReplayIntegrityFailure,
    Field(discriminator="status"),
]


class PackLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    pack_ref: GovernedRef
    state: PackLifecycleState
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    supersedes_version_id: VersionId | None
    actor_id: OpaqueId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> PackLifecycleEvent:
        _validate_refs(self.evidence_refs, "pack lifecycle event evidence")
        return self


class PackLifecycleCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    catalog_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    pack_refs: tuple[GovernedRef, ...]
    events: tuple[PackLifecycleEvent, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_chains(self) -> PackLifecycleCatalog:
        if not self.pack_refs or sorted_unique_refs(self.pack_refs) != self.pack_refs:
            raise ValueError("pack lifecycle catalog requires unique sorted pack versions")
        _validate_refs(self.evidence_refs, "pack lifecycle catalog evidence")
        pack_set = set(self.pack_refs)
        if any(item.pack_ref not in pack_set for item in self.events):
            raise ValueError("pack lifecycle event references an uncataloged pack")
        event_keys = tuple(
            (
                item.pack_ref.logical_id,
                item.pack_ref.version_number,
                item.event_ref.version_number,
                item.event_ref.version_id,
            )
            for item in self.events
        )
        if event_keys != tuple(sorted(set(event_keys))):
            raise ValueError("pack lifecycle events must be unique and sorted")
        for pack_ref in self.pack_refs:
            chain = tuple(item for item in self.events if item.pack_ref == pack_ref)
            if not chain or chain[0].state != "PUBLISHED" or chain[0].supersedes_version_id:
                raise ValueError("pack lifecycle chain must begin with publication")
            for previous, current in pairwise(chain):
                if current.supersedes_version_id != previous.event_ref.version_id:
                    raise ValueError("pack lifecycle chain must supersede its exact predecessor")
        return self


class PackLifecyclePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    eligible_reason_id: TermId
    unavailable_reason_id: TermId
    deprecated_reason_id: TermId
    revoked_reason_id: TermId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_reason_ids(self) -> PackLifecyclePolicy:
        reasons = (
            self.eligible_reason_id,
            self.unavailable_reason_id,
            self.deprecated_reason_id,
            self.revoked_reason_id,
        )
        if len(reasons) != len(set(reasons)):
            raise ValueError("pack lifecycle reasons must be distinct")
        _validate_refs(self.evidence_refs, "pack lifecycle policy evidence")
        return self


class PackEligibilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["ELIGIBLE", "INELIGIBLE"]
    pack_ref: GovernedRef | None
    lifecycle_state: PackLifecycleState | None
    reason_id: TermId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_result(self) -> PackEligibilityResult:
        if (self.pack_ref is None) != (self.lifecycle_state is None):
            raise ValueError("pack eligibility identity and lifecycle state must appear together")
        if self.status == "ELIGIBLE" and self.lifecycle_state != "PUBLISHED":
            raise ValueError("only a published exact pack version is eligible")
        if self.status == "INELIGIBLE" and self.lifecycle_state == "PUBLISHED":
            raise ValueError("published exact pack version cannot be marked ineligible")
        _validate_refs(self.evidence_refs, "pack eligibility evidence")
        return self


@dataclass(frozen=True)
class ReplayExecution:
    output: MIEOutput
    snapshot: KnowledgeSnapshot | None
    audit_events: tuple[PreflightRefusalAuditEvent | SnapshotDecisionAuditEvent, ...]
    bound_versions: tuple[GovernedRef, ...]
    schema_version: str


def execute_replayable_run(
    recipe: ReplayRecipe,
    replay_policy: ReplayPolicy,
    store: PostgresRunStore,
) -> ReplayExecution:
    """Execute and atomically persist the exact recipe required for later replay."""
    _validate_recipe_policy(recipe, replay_policy)
    execution = _execute_recipe(recipe)
    capsule = ReplayCapsulePayload(
        algorithm_id=replay_policy.algorithm_id,
        recipe_schema_version=replay_policy.recipe_schema_version,
        replay_policy_ref=replay_policy.policy_ref,
        payload=_recipe_bytes(recipe, replay_policy.canonicalization_policy),
    )
    if execution.snapshot is None:
        if not isinstance(execution.output, Tier1Output):
            raise ValueError("preflight replay recipe must produce Tier 1 output")
        preflight_events = tuple(
            item for item in execution.audit_events if isinstance(item, PreflightRefusalAuditEvent)
        )
        if len(preflight_events) != len(execution.audit_events):
            raise ValueError("preflight replay recipe emitted snapshot audit events")
        store.persist_replayable_preflight_run(
            recipe.request.run_id,
            execution.output,
            preflight_events,
            capsule,
        )
    else:
        snapshot_events = tuple(
            item for item in execution.audit_events if isinstance(item, SnapshotDecisionAuditEvent)
        )
        if len(snapshot_events) != len(execution.audit_events):
            raise ValueError("snapshot replay recipe emitted preflight audit events")
        store.persist_replayable_snapshot_run(
            recipe.request.run_id,
            execution.output,
            execution.snapshot,
            snapshot_events,
            execution.bound_versions,
            execution.schema_version,
            capsule,
        )
    return execution


def verify_persisted_replay(
    replay_id: OpaqueId,
    run_id: OpaqueId,
    store: PostgresRunStore,
    replay_policy: ReplayPolicy,
) -> ReplayResult:
    """Re-execute only the stored exact recipe and fail closed on any byte-level drift."""
    try:
        stored = store.load_run(run_id)
    except (PersistenceIntegrityError, CanonicalizationError):
        return _failure(
            replay_id, run_id, replay_policy, replay_policy.stored_content_invalid_reason_id
        )
    if stored is None:
        return _failure(replay_id, run_id, replay_policy, replay_policy.run_missing_reason_id)
    capsule = stored.replay_capsule
    if capsule is None:
        return _failure(replay_id, run_id, replay_policy, replay_policy.capsule_missing_reason_id)
    if capsule.algorithm_id != replay_policy.algorithm_id:
        return _failure(
            replay_id,
            run_id,
            replay_policy,
            replay_policy.algorithm_unavailable_reason_id,
        )
    if capsule.replay_policy_ref != replay_policy.policy_ref:
        return _failure(replay_id, run_id, replay_policy, replay_policy.recipe_invalid_reason_id)
    if capsule.recipe_schema_version != replay_policy.recipe_schema_version:
        return _failure(replay_id, run_id, replay_policy, replay_policy.recipe_invalid_reason_id)
    validation_context = {"canonicalization_policy": replay_policy.canonicalization_policy}
    try:
        recipe = REPLAY_RECIPE_ADAPTER.validate_json(capsule.payload, context=validation_context)
        _validate_recipe_policy(recipe, replay_policy)
        if recipe.request.run_id != run_id:
            raise ValueError("replay recipe run identity mismatch")
        if _recipe_bytes(recipe, replay_policy.canonicalization_policy) != capsule.payload:
            raise ValueError("replay recipe is not canonical")
    except (ValidationError, ValueError, CanonicalizationError):
        return _failure(replay_id, run_id, replay_policy, replay_policy.recipe_invalid_reason_id)
    try:
        execution = _execute_recipe(recipe)
        _verify_execution(stored, execution, replay_policy.canonicalization_policy)
    except Exception:
        # A historical algorithm that now crashes is unavailable for replay; no
        # implementation exception may be mistaken for a verified old decision.
        return _failure(replay_id, run_id, replay_policy, replay_policy.replay_mismatch_reason_id)
    return ReplayVerified(
        replay_id=replay_id,
        run_id=run_id,
        status="VERIFIED",
        algorithm_id=replay_policy.algorithm_id,
        replay_policy_ref=replay_policy.policy_ref,
        recipe_schema_version=replay_policy.recipe_schema_version,
        source_run_schema_version=stored.schema_version,
        output_hash=_output_hash(execution.output),
        snapshot_hash=(
            snapshot_hash(execution.snapshot, replay_policy.canonicalization_policy)
            if execution.snapshot is not None
            else None
        ),
        bound_version_refs=execution.bound_versions,
    )


def evaluate_pack_eligibility(
    requested_pack_version_id: VersionId,
    as_of_time: CanonicalTimestamp,
    catalog: PackLifecycleCatalog,
    policy: PackLifecyclePolicy,
) -> PackEligibilityResult:
    """Evaluate an exact pack as-of; canonical timestamps make lexical ordering chronological."""
    matches = tuple(
        item for item in catalog.pack_refs if item.version_id == requested_pack_version_id
    )
    base_evidence = sorted_unique_refs(
        (
            catalog.catalog_ref,
            *catalog.evidence_refs,
            policy.policy_ref,
            *policy.evidence_refs,
        )
    )
    if len(matches) != 1:
        return PackEligibilityResult(
            status="INELIGIBLE",
            pack_ref=None,
            lifecycle_state=None,
            reason_id=policy.unavailable_reason_id,
            evidence_refs=base_evidence,
        )
    pack_ref = matches[0]
    eligible_events = tuple(
        item
        for item in catalog.events
        if item.pack_ref == pack_ref
        and item.effective_at <= as_of_time
        and item.recorded_at <= as_of_time
    )
    heads = tuple(
        item
        for item in eligible_events
        if not any(
            candidate.supersedes_version_id == item.event_ref.version_id
            for candidate in eligible_events
        )
    )
    if len(heads) != 1:
        return PackEligibilityResult(
            status="INELIGIBLE",
            pack_ref=None,
            lifecycle_state=None,
            reason_id=policy.unavailable_reason_id,
            evidence_refs=base_evidence,
        )
    state = heads[0].state
    reason = {
        "PUBLISHED": policy.eligible_reason_id,
        "DEPRECATED": policy.deprecated_reason_id,
        "REVOKED": policy.revoked_reason_id,
    }[state]
    return PackEligibilityResult(
        status="ELIGIBLE" if state == "PUBLISHED" else "INELIGIBLE",
        pack_ref=pack_ref,
        lifecycle_state=state,
        reason_id=reason,
        evidence_refs=sorted_unique_refs(
            (
                *base_evidence,
                heads[0].event_ref,
                *heads[0].evidence_refs,
            )
        ),
    )


def _execute_recipe(recipe: ReplayRecipe) -> ReplayExecution:
    if isinstance(recipe, SafeRefusalReplayRecipe):
        safe_result = build_safe_refusal(recipe.request, recipe.pack_registry, recipe.policy)
        return ReplayExecution(
            output=safe_result.output,
            snapshot=None,
            audit_events=safe_result.audit_events,
            bound_versions=(),
            schema_version=SCHEMA_VERSION,
        )
    slice_result: Slice2ExecutionResult
    schema_version: str
    if isinstance(recipe, CandidatePreservationReplayRecipe):
        slice_result = build_candidate_preservation(recipe.request, recipe.runtime, recipe.policy)
        schema_version = SNAPSHOT_RUN_SCHEMA_VERSION
    elif isinstance(recipe, MSAGateReplayRecipe):
        slice_result = build_msa_calibration_gate(recipe.request, recipe.runtime, recipe.policy)
        schema_version = SLICE3_RUN_SCHEMA_VERSION
    elif isinstance(recipe, ArtifactConfirmationReplayRecipe):
        slice_result = build_artifact_confirmation(recipe.request, recipe.runtime, recipe.policy)
        schema_version = SLICE4_RUN_SCHEMA_VERSION
    elif isinstance(recipe, HonestNegativeReplayRecipe):
        slice_result = build_honest_negative(recipe.request, recipe.runtime, recipe.policy)
        schema_version = SLICE5_RUN_SCHEMA_VERSION
    else:
        slice_result = build_tier2_advisory(
            recipe.request,
            recipe.query,
            recipe.runtime,
            recipe.policy,
        )
        schema_version = SLICE6_RUN_SCHEMA_VERSION
    return ReplayExecution(
        output=slice_result.output,
        snapshot=slice_result.snapshot,
        audit_events=slice_result.audit_events,
        bound_versions=slice_result.bound_versions,
        schema_version=schema_version,
    )


def _verify_execution(
    stored: StoredRun,
    execution: ReplayExecution,
    policy: CanonicalizationPolicy,
) -> None:
    if stored.schema_version != execution.schema_version:
        raise PersistenceIntegrityError("replay run schema mismatch")
    if stored.payload != canonical_bytes(execution.output, policy):
        raise PersistenceIntegrityError("replayed output differs from stored output")
    expected_audits = tuple(canonical_bytes(item, policy) for item in execution.audit_events)
    if stored.audit_payloads != expected_audits:
        raise PersistenceIntegrityError("replayed audit differs from stored audit")
    if execution.snapshot is None:
        if (
            stored.snapshot_payload is not None
            or stored.citation_payloads
            or stored.bound_version_payloads
        ):
            raise PersistenceIntegrityError("preflight replay acquired snapshot-bound content")
        return
    if stored.snapshot_payload != canonical_bytes(execution.snapshot, policy):
        raise PersistenceIntegrityError("replayed snapshot differs from stored snapshot")
    body: Tier1Decision | AdvisoryDecision = (
        execution.output.decision
        if isinstance(execution.output, Tier1Output)
        else execution.output.advisory
    )
    expected_citations = tuple(sorted(canonical_bytes(item, policy) for item in body.citations))
    if tuple(sorted(stored.citation_payloads)) != expected_citations:
        raise PersistenceIntegrityError("replayed citations differ from stored citations")
    expected_versions = tuple(
        sorted(canonical_bytes(item, policy) for item in execution.bound_versions)
    )
    if tuple(sorted(stored.bound_version_payloads)) != expected_versions:
        raise PersistenceIntegrityError("replayed bound versions differ from stored versions")


def _validate_recipe_policy(recipe: ReplayRecipe, replay_policy: ReplayPolicy) -> None:
    recipe_policy = _recipe_canonicalization_policy(recipe)
    recipe_parameters = recipe_policy.model_dump(
        mode="python",
        exclude={"policy_id", "policy_version"},
    )
    replay_parameters = replay_policy.canonicalization_policy.model_dump(
        mode="python",
        exclude={"policy_id", "policy_version"},
    )
    if recipe_parameters != replay_parameters:
        raise ValueError("replay recipe canonicalization parameters mismatch")


def _recipe_canonicalization_policy(recipe: ReplayRecipe) -> CanonicalizationPolicy:
    if isinstance(recipe, SafeRefusalReplayRecipe):
        return recipe.policy.canonicalization_policy
    if isinstance(recipe, CandidatePreservationReplayRecipe):
        return recipe.policy.canonicalization_policy
    if isinstance(recipe, MSAGateReplayRecipe):
        return recipe.policy.slice2_policy.canonicalization_policy
    if isinstance(recipe, ArtifactConfirmationReplayRecipe):
        return recipe.policy.slice3_policy.slice2_policy.canonicalization_policy
    if isinstance(recipe, HonestNegativeReplayRecipe):
        return recipe.policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    return recipe.policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy


def _output_hash(output: MIEOutput) -> str:
    return output.decision_hash if isinstance(output, Tier1Output) else output.advisory_hash


def _recipe_bytes(recipe: ReplayRecipe, policy: CanonicalizationPolicy) -> bytes:
    # Replay input must retain explicit nulls because existing executable schemas
    # use them to distinguish a complete no-value field from an omitted field.
    return canonical_bytes(recipe.model_dump(mode="python", exclude_none=False), policy)


def _failure(
    replay_id: OpaqueId,
    run_id: OpaqueId,
    policy: ReplayPolicy,
    reason_id: TermId,
) -> ReplayIntegrityFailure:
    return ReplayIntegrityFailure(
        replay_id=replay_id,
        run_id=run_id,
        status="INTEGRITY_FAILURE",
        algorithm_id=policy.algorithm_id,
        replay_policy_ref=policy.policy_ref,
        reason_id=reason_id,
    )


def _validate_refs(refs: tuple[GovernedRef, ...], label: str) -> None:
    if not refs or sorted_unique_refs(refs) != refs:
        raise ValueError(f"{label} must be nonempty, unique, and sorted")
