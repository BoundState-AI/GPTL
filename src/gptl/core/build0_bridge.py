"""
Module: Build 0 Bridge and Capture Gate
Purpose: Build 1 capture gate and Build 0 bridge contracts.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from typing import Final, Literal, cast

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.canonical import CanonicalizationError, canonical_sha256
from gptl.core.observations import AttributedObservation
from gptl.core.proposal_ratification import ActiveValueResolutionResult
from gptl.core.proposals import (
    TYPED_VALUE_PROPOSAL_RECORD_TYPE,
    ProposalEvidenceLocation,
    ProposalOnlyEvidence,
    TypedValueProposal,
    active_value_key_payload,
)
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    OpaqueId,
    Sha256Hex,
    TermId,
)
from gptl.core.snapshot import KnowledgeSnapshot, build_snapshot, snapshot_hash
from gptl.mie.predicates import ScalarValue

BUILD0_BRIDGE_CAPTURE_GATE_SCHEMA_VERSION: Final = "gptl.build1.build0-capture-gate.v1"
BUILD0_BRIDGE_CAPTURE_GATE_RECORD_TYPE: Final = "BUILD1_BUILD0_CAPTURE_GATE"
BUILD0_BOUND_VALUE_ROW_SCHEMA_VERSION: Final = "gptl.build1.build0-bound-value-row.v1"
BUILD0_BOUND_VALUE_ROW_KIND: Final = "BUILD0_TIER1_GOVERNED_VALUE_ROW"
BUILD0_BRIDGE_REQUEST_SCHEMA_VERSION: Final = "gptl.build1.build0-bridge-request.v1"
BUILD0_BRIDGE_REQUEST_RECORD_TYPE: Final = "BUILD1_BUILD0_BRIDGE_REQUEST"
BRIDGE_ATTEMPT_SCHEMA_VERSION: Final = "gptl.build1.bridge-attempt.v1"
BRIDGE_ATTEMPT_RECORD_TYPE: Final = "BUILD1_BRIDGE_ATTEMPT"
BUILD1_BRIDGE_REPLAY_CAPSULE_SCHEMA_VERSION: Final = "gptl.build1.bridge-replay-capsule.v1"
BUILD1_BRIDGE_REPLAY_CAPSULE_RECORD_TYPE: Final = "BUILD1_BRIDGE_REPLAY_CAPSULE"
HASH_ALGORITHM: Final = "SHA-256"
BUILD1_EXACT_REPLAY_ALGORITHM_ID: Final = "BUILD1_EXACT_REPLAY_V1"
BUILD0_POSTGRES_ADVISORY_LOCK_SCOPE: Final = "POSTGRES_TRANSACTION"

CAPTURE_READY_REASON_ID: Final = TermId("build1.bridge.capture-ready")
BRIDGE_INTEGRITY_FAILURE_REASON_ID: Final = TermId("build1.bridge.integrity-failure")
BRIDGE_SCOPE_INCOMPATIBLE_REASON_ID: Final = TermId("build1.bridge.scope-incompatible")
BRIDGE_AUTHORITY_INELIGIBLE_REASON_ID: Final = TermId("build1.bridge.authority-ineligible")
BRIDGE_IDENTITY_UNRESOLVED_REASON_ID: Final = TermId("build1.bridge.identity-unresolved")
BRIDGE_IDENTITY_COLLISION_REASON_ID: Final = TermId("build1.bridge.identity-collision")
BRIDGE_CONTEXT_KEY_UNDEFINED_REASON_ID: Final = TermId("build1.bridge.context-key-undefined")
BRIDGE_EVIDENCE_NOT_RATIFIABLE_REASON_ID: Final = TermId(
    "build1.bridge.evidence-not-ratifiable"
)
BRIDGE_ACTIVE_VALUE_CONFLICT_REASON_ID: Final = TermId("build1.bridge.active-value-conflict")
BRIDGE_MISSING_RATIFICATION_REASON_ID: Final = TermId("build1.bridge.missing-ratification")
BRIDGE_CAPABILITY_GAP_REASON_ID: Final = TermId("build1.bridge.capability-gap")
BRIDGE_PARSER_GAP_REASON_ID: Final = TermId("build1.bridge.parser-gap")
BRIDGE_ADVISORY_ONLY_OBSERVATION_REASON_ID: Final = TermId(
    "build1.bridge.advisory-only-observation"
)
BRIDGE_NUMERIC_POLICY_MISMATCH_REASON_ID: Final = TermId(
    "build1.bridge.numeric-policy-mismatch"
)
BRIDGE_RETRY_MISMATCH_REASON_ID: Final = TermId("build1.bridge.retry-mismatch")
BRIDGE_DUPLICATE_WRITE_UNRECONCILED_REASON_ID: Final = TermId(
    "build1.bridge.duplicate-write-unreconciled"
)
BRIDGE_BUILD0_FAILURE_REASON_ID: Final = TermId("build1.bridge.build0-failed")

CaptureGateStatus = Literal["BUILD0_REQUEST_READY", "FAIL_CLOSED", "ADVISORY_GAP"]
DiagnosticClassification = Literal["FAIL_CLOSED", "ADVISORY_GAP"]
ScopeStatus = Literal["COMPATIBLE", "INCOMPATIBLE"]
AuthorityStatus = Literal["ELIGIBLE", "INELIGIBLE", "MISSING_POLICY"]
IdentityStatus = Literal["RESOLVED", "UNRESOLVED", "COLLISION"]
ContextKeyStatus = Literal["DEFINED", "UNDEFINED"]
EvidenceLocatorStatus = Literal["RATIFIABLE", "NOT_RATIFIABLE"]
CapabilityStatus = Literal["SUPPORTED", "UNKNOWN", "UNSUPPORTED", "AMBIGUOUS"]
ParserStatus = Literal[
    "PARSER_READY",
    "UNPARSED",
    "PARSER_UNAVAILABLE",
    "PARSER_UNSUPPORTED",
    "PARSER_FAILED",
]
ValidationProtocolStatus = Literal[
    "NOT_REQUESTED",
    "VALIDATED",
    "NOT_VALIDATED",
    "INVALID_PROTOCOL_EXECUTION",
    "CONFIGURATION_INVALID",
]
BridgeAttemptLifecycleState = Literal[
    "CAPTURE_BOUND",
    "BUILD0_REQUEST_CREATED",
    "BUILD0_PERSISTED",
    "FINALIZED",
    "BUILD0_FAILED",
    "BRIDGE_INTEGRITY_FAILURE",
]


class BridgeCallerIds(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: OpaqueId
    decision_id: OpaqueId
    case_id: OpaqueId
    audit_event_id: OpaqueId
    snapshot_id: OpaqueId
    replay_id: OpaqueId


class Build0SnapshotBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: OpaqueId
    as_of_time: CanonicalTimestamp
    pack_ref: GovernedRef
    engine_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    algorithm_refs: tuple[GovernedRef, ...]
    unit_registry_ref: GovernedRef
    field_registry_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    serialization_policy_ref: GovernedRef
    lexical_policy_ref: GovernedRef

    @model_validator(mode="before")
    @classmethod
    def sort_algorithm_refs(cls, value: object) -> object:
        if not isinstance(value, dict) or "algorithm_refs" not in value:
            return value
        normalized = dict(value)
        normalized["algorithm_refs"] = sorted_unique_refs(tuple(normalized["algorithm_refs"]))
        return normalized


class Build0BoundValueRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.build0-bound-value-row.v1"]
    row_kind: Literal["BUILD0_TIER1_GOVERNED_VALUE_ROW"]
    proposal_record_type: Literal["TYPED_VALUE_PROPOSAL"]
    proposal_ref: GovernedRef
    proposal_content_hash: Sha256Hex
    target_key: dict[str, object]
    typed_canonical_value: ScalarValue
    evidence_location: ProposalEvidenceLocation
    canonicalization_policy_ref: GovernedRef

    @model_validator(mode="after")
    def validate_hash_binding(self) -> Build0BoundValueRow:
        if self.proposal_content_hash != self.proposal_ref.content_hash:
            raise ValueError("bound row proposal hash must match governed proposal reference")
        return self


class CaptureGateDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reason_id: TermId
    classification: DiagnosticClassification
    proposal_ref: GovernedRef | None = None
    target_key: dict[str, object] | None = None
    capability_ref: GovernedRef | None = None
    source_artifact_ref: GovernedRef | None = None
    parser_algorithm_refs: tuple[GovernedRef, ...] = ()
    conflicting_event_refs: tuple[GovernedRef, ...] = ()
    supporting_refs: tuple[GovernedRef, ...] = ()
    upstream_diagnostics: tuple[TermId, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def sort_ref_fields(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        for field_name in (
            "parser_algorithm_refs",
            "conflicting_event_refs",
            "supporting_refs",
        ):
            if field_name in normalized:
                normalized[field_name] = sorted_unique_refs(tuple(normalized[field_name]))
        if "upstream_diagnostics" in normalized:
            normalized["upstream_diagnostics"] = tuple(sorted(normalized["upstream_diagnostics"]))
        return normalized


class CaptureGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.build0-capture-gate.v1"]
    record_type: Literal["BUILD1_BUILD0_CAPTURE_GATE"]
    hash_algorithm: Literal["SHA-256"]
    gate_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    as_of_time: CanonicalTimestamp
    status: CaptureGateStatus
    reason_id: TermId
    capability_status: CapabilityStatus
    parser_status: ParserStatus
    validation_protocol_status: ValidationProtocolStatus
    active_value_state_hash: Sha256Hex
    bound_value_rows: tuple[Build0BoundValueRow, ...]
    observation_refs: tuple[GovernedRef, ...]
    selected_upstream_refs: tuple[GovernedRef, ...]
    diagnostics: tuple[CaptureGateDiagnostic, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_gate_fields(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "bound_value_rows" in normalized:
            normalized["bound_value_rows"] = tuple(
                sorted(
                    normalized["bound_value_rows"],
                    key=lambda item: _row_sort_key(cast(object, item)),
                )
            )
        for field_name in ("observation_refs", "selected_upstream_refs"):
            if field_name in normalized:
                normalized[field_name] = sorted_unique_refs(tuple(normalized[field_name]))
        if "diagnostics" in normalized:
            normalized["diagnostics"] = tuple(
                sorted(
                    normalized["diagnostics"],
                    key=lambda item: _diagnostic_sort_key(cast(object, item)),
                )
            )
        return normalized

    @model_validator(mode="after")
    def validate_status_shape(self) -> CaptureGateResult:
        has_fail_closed = any(item.classification == "FAIL_CLOSED" for item in self.diagnostics)
        if self.status == "BUILD0_REQUEST_READY":
            if not self.bound_value_rows or self.reason_id != CAPTURE_READY_REASON_ID:
                raise ValueError("ready capture gate requires bound rows and ready reason")
            if has_fail_closed:
                raise ValueError("ready capture gate cannot carry fail-closed diagnostics")
            return self
        if self.bound_value_rows:
            raise ValueError("non-ready capture gate cannot bind Build 0 value rows")
        if self.status == "FAIL_CLOSED":
            if not has_fail_closed:
                raise ValueError("fail-closed capture gate requires fail-closed diagnostics")
            return self
        if not self.diagnostics or has_fail_closed:
            raise ValueError("advisory-gap capture gate requires advisory diagnostics only")
        return self


class Build0BridgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.build0-bridge-request.v1"]
    record_type: Literal["BUILD1_BUILD0_BRIDGE_REQUEST"]
    hash_algorithm: Literal["SHA-256"]
    request_ref: GovernedRef
    caller_ids: BridgeCallerIds
    capture_gate_ref: GovernedRef
    snapshot: KnowledgeSnapshot
    snapshot_hash: Sha256Hex
    bound_value_rows: tuple[Build0BoundValueRow, ...]
    observation_refs: tuple[GovernedRef, ...]
    build0_lock_scope: Literal["POSTGRES_TRANSACTION"]

    @model_validator(mode="before")
    @classmethod
    def sort_request_fields(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "bound_value_rows" in normalized:
            normalized["bound_value_rows"] = tuple(
                sorted(
                    normalized["bound_value_rows"],
                    key=lambda item: _row_sort_key(cast(object, item)),
                )
            )
        if "observation_refs" in normalized:
            normalized["observation_refs"] = sorted_unique_refs(
                tuple(normalized["observation_refs"])
            )
        return normalized

    @model_validator(mode="after")
    def validate_request(self) -> Build0BridgeRequest:
        if not self.bound_value_rows:
            raise ValueError("Build 0 bridge request requires at least one bound row")
        if self.capture_gate_ref not in self.snapshot.bound_versions:
            raise ValueError("bridge request snapshot must bind the capture gate")
        return self


class ExistingBuild0RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    caller_ids: BridgeCallerIds
    build0_request_hash: Sha256Hex
    build0_output_hash: Sha256Hex
    build0_replay_hash: Sha256Hex


class BridgeAttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.bridge-attempt.v1"]
    record_type: Literal["BUILD1_BRIDGE_ATTEMPT"]
    hash_algorithm: Literal["SHA-256"]
    attempt_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: BridgeAttemptLifecycleState
    caller_ids: BridgeCallerIds
    capture_gate_ref: GovernedRef
    build0_request_ref: GovernedRef
    build0_request_hash: Sha256Hex
    build0_output_hash: Sha256Hex | None = None
    build0_replay_hash: Sha256Hex | None = None
    failure_reason_id: TermId | None = None
    build0_lock_scope: Literal["POSTGRES_TRANSACTION"]

    @model_validator(mode="after")
    def validate_lifecycle_payload(self) -> BridgeAttemptRecord:
        has_build0_hashes = self.build0_output_hash is not None and self.build0_replay_hash is not None
        if self.lifecycle_state in {"BUILD0_PERSISTED", "FINALIZED"}:
            if not has_build0_hashes or self.failure_reason_id is not None:
                raise ValueError("persisted bridge attempt requires Build 0 output hashes only")
            return self
        if self.lifecycle_state in {"BUILD0_FAILED", "BRIDGE_INTEGRITY_FAILURE"}:
            if self.failure_reason_id is None:
                raise ValueError("terminal failed bridge attempt requires a reason")
            return self
        if has_build0_hashes or self.failure_reason_id is not None:
            raise ValueError("pre-invocation bridge attempt cannot carry terminal payload")
        return self


class Build1BridgeReplayCapsule(BaseModel):
    """Binds the upstream provenance chain for exact Build 1 replay.

    `upstream_refs` completeness is a CALLER-TRUST boundary in this build: the capsule
    records the refs it is given (caller-supplied plus the capture-gate subset) and does
    not structurally verify that every plan §551 provenance category is present. Structural
    completeness / missing-record verification is scheduled for the Slice 8 replay engine
    (BUILD1_EXACT_REPLAY_V1, plan §11), which fails closed on absent records. This capsule
    never feeds `bound_value_rows`, so an incomplete upstream set is an auditability gap,
    not a Tier 1 firewall path.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.bridge-replay-capsule.v1"]
    record_type: Literal["BUILD1_BRIDGE_REPLAY_CAPSULE"]
    hash_algorithm: Literal["SHA-256"]
    replay_ref: GovernedRef
    algorithm_id: Literal["BUILD1_EXACT_REPLAY_V1"]
    caller_ids: BridgeCallerIds
    capture_gate_hash: Sha256Hex
    build0_request_hash: Sha256Hex
    upstream_refs: tuple[GovernedRef, ...]
    build0_output_hash: Sha256Hex | None = None
    build0_replay_hash: Sha256Hex | None = None

    @model_validator(mode="before")
    @classmethod
    def sort_upstream_refs(cls, value: object) -> object:
        if not isinstance(value, dict) or "upstream_refs" not in value:
            return value
        normalized = dict(value)
        normalized["upstream_refs"] = sorted_unique_refs(tuple(normalized["upstream_refs"]))
        return normalized


def evaluate_capture_gate(
    *,
    gate_ref: GovernedRef,
    canonicalization_policy_ref: GovernedRef,
    active_values: ActiveValueResolutionResult,
    proposals: tuple[TypedValueProposal, ...],
    observations: tuple[AttributedObservation, ...],
    capability_status: CapabilityStatus,
    parser_status: ParserStatus,
    validation_protocol_status: ValidationProtocolStatus,
    scope_status: ScopeStatus,
    authority_status: AuthorityStatus,
    identity_status: IdentityStatus,
    context_key_status: ContextKeyStatus,
    evidence_locator_status: EvidenceLocatorStatus,
    build0_canonicalization_policy_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> CaptureGateResult:
    observation_refs = _active_observation_refs(observations, as_of_time)
    selected_refs = _selected_upstream_refs(gate_ref, active_values, proposals, observation_refs)

    failure = _first_fail_closed_diagnostic(
        active_values=active_values,
        proposals=proposals,
        scope_status=scope_status,
        authority_status=authority_status,
        identity_status=identity_status,
        context_key_status=context_key_status,
        evidence_locator_status=evidence_locator_status,
        build0_canonicalization_policy_ref=build0_canonicalization_policy_ref,
        canonicalization_policy=canonicalization_policy,
    )
    if failure is not None:
        return _capture_gate_result(
            gate_ref=gate_ref,
            canonicalization_policy_ref=canonicalization_policy_ref,
            canonicalization_policy=canonicalization_policy,
            as_of_time=as_of_time,
            status="FAIL_CLOSED",
            reason_id=failure.reason_id,
            capability_status=capability_status,
            parser_status=parser_status,
            validation_protocol_status=validation_protocol_status,
            active_value_state_hash=active_values.active_value_state_hash,
            bound_value_rows=(),
            observation_refs=observation_refs,
            selected_upstream_refs=selected_refs,
            diagnostics=(failure,),
        )

    gap = _first_advisory_gap_diagnostic(
        active_values=active_values,
        proposals=proposals,
        observations=observations,
        observation_refs=observation_refs,
        capability_status=capability_status,
        parser_status=parser_status,
    )
    if gap is not None:
        return _capture_gate_result(
            gate_ref=gate_ref,
            canonicalization_policy_ref=canonicalization_policy_ref,
            canonicalization_policy=canonicalization_policy,
            as_of_time=as_of_time,
            status="ADVISORY_GAP",
            reason_id=gap.reason_id,
            capability_status=capability_status,
            parser_status=parser_status,
            validation_protocol_status=validation_protocol_status,
            active_value_state_hash=active_values.active_value_state_hash,
            bound_value_rows=(),
            observation_refs=observation_refs,
            selected_upstream_refs=selected_refs,
            diagnostics=(gap,),
        )

    rows = _bound_rows_for_active_refs(
        active_values.active_proposal_refs,
        proposals,
        canonicalization_policy,
    )
    diagnostics = _ready_advisory_diagnostics(observation_refs)
    return _capture_gate_result(
        gate_ref=gate_ref,
        canonicalization_policy_ref=canonicalization_policy_ref,
        canonicalization_policy=canonicalization_policy,
        as_of_time=as_of_time,
        status="BUILD0_REQUEST_READY",
        reason_id=CAPTURE_READY_REASON_ID,
        capability_status=capability_status,
        parser_status=parser_status,
        validation_protocol_status=validation_protocol_status,
        active_value_state_hash=active_values.active_value_state_hash,
        bound_value_rows=rows,
        observation_refs=observation_refs,
        selected_upstream_refs=selected_refs,
        diagnostics=diagnostics,
    )


def assemble_build0_bridge_request(
    *,
    request_ref: GovernedRef,
    caller_ids: BridgeCallerIds,
    capture_gate: CaptureGateResult,
    snapshot_binding: Build0SnapshotBinding,
    canonicalization_policy: CanonicalizationPolicy,
) -> Build0BridgeRequest | None:
    if capture_gate.status != "BUILD0_REQUEST_READY":
        return None

    snapshot = build_snapshot(
        snapshot_id=caller_ids.snapshot_id,
        as_of_time=snapshot_binding.as_of_time,
        pack_ref=snapshot_binding.pack_ref,
        engine_policy_ref=snapshot_binding.engine_policy_ref,
        evidence_scope_ref=snapshot_binding.evidence_scope_ref,
        algorithm_refs=snapshot_binding.algorithm_refs,
        unit_registry_ref=snapshot_binding.unit_registry_ref,
        field_registry_ref=snapshot_binding.field_registry_ref,
        canonicalization_policy_ref=snapshot_binding.canonicalization_policy_ref,
        serialization_policy_ref=snapshot_binding.serialization_policy_ref,
        lexical_policy_ref=snapshot_binding.lexical_policy_ref,
        ratification_state_hash=capture_gate.active_value_state_hash,
        used_refs=(*_row_bound_refs(capture_gate.bound_value_rows), capture_gate.gate_ref),
        ratification_events=(),
        policy=canonicalization_policy,
    )
    return Build0BridgeRequest.model_validate(
        {
            "schema_version": BUILD0_BRIDGE_REQUEST_SCHEMA_VERSION,
            "record_type": BUILD0_BRIDGE_REQUEST_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "request_ref": request_ref,
            "caller_ids": caller_ids,
            "capture_gate_ref": capture_gate.gate_ref,
            "snapshot": snapshot,
            "snapshot_hash": snapshot_hash(snapshot, canonicalization_policy),
            "bound_value_rows": capture_gate.bound_value_rows,
            "observation_refs": capture_gate.observation_refs,
            "build0_lock_scope": BUILD0_POSTGRES_ADVISORY_LOCK_SCOPE,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )


def build0_bridge_request_hash(
    request: Build0BridgeRequest,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(request, canonicalization_policy)


def capture_gate_hash(
    capture_gate: CaptureGateResult,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(capture_gate, canonicalization_policy)


def create_capture_bound_attempt(
    *,
    attempt_ref: GovernedRef,
    canonicalization_policy_ref: GovernedRef,
    caller_ids: BridgeCallerIds,
    capture_gate_ref: GovernedRef,
    build0_request_ref: GovernedRef,
    build0_request_hash_value: Sha256Hex,
) -> BridgeAttemptRecord:
    return BridgeAttemptRecord(
        schema_version=BRIDGE_ATTEMPT_SCHEMA_VERSION,
        record_type=BRIDGE_ATTEMPT_RECORD_TYPE,
        hash_algorithm=HASH_ALGORITHM,
        attempt_ref=attempt_ref,
        canonicalization_policy_ref=canonicalization_policy_ref,
        lifecycle_state="CAPTURE_BOUND",
        caller_ids=caller_ids,
        capture_gate_ref=capture_gate_ref,
        build0_request_ref=build0_request_ref,
        build0_request_hash=build0_request_hash_value,
        build0_lock_scope=BUILD0_POSTGRES_ADVISORY_LOCK_SCOPE,
    )


def mark_build0_request_created(attempt: BridgeAttemptRecord) -> BridgeAttemptRecord:
    return attempt.model_copy(update={"lifecycle_state": "BUILD0_REQUEST_CREATED"})


def mark_build0_failed(
    attempt: BridgeAttemptRecord,
    failure_reason_id: TermId = BRIDGE_BUILD0_FAILURE_REASON_ID,
) -> BridgeAttemptRecord:
    return attempt.model_copy(
        update={
            "lifecycle_state": "BUILD0_FAILED",
            "failure_reason_id": failure_reason_id,
        }
    )


def reconcile_bridge_retry(
    *,
    attempt: BridgeAttemptRecord,
    caller_ids: BridgeCallerIds,
    build0_request_hash_value: Sha256Hex,
    existing_run: ExistingBuild0RunRecord | None,
    duplicate_insert_observed: bool,
) -> BridgeAttemptRecord:
    if caller_ids != attempt.caller_ids or build0_request_hash_value != attempt.build0_request_hash:
        return _integrity_failed_attempt(attempt, BRIDGE_RETRY_MISMATCH_REASON_ID)

    if existing_run is not None:
        return _reconcile_existing_run(attempt, existing_run)

    if duplicate_insert_observed:
        return _integrity_failed_attempt(attempt, BRIDGE_DUPLICATE_WRITE_UNRECONCILED_REASON_ID)

    return mark_build0_request_created(attempt)


def build_replay_capsule(
    *,
    replay_ref: GovernedRef,
    caller_ids: BridgeCallerIds,
    capture_gate: CaptureGateResult,
    build0_request_hash_value: Sha256Hex,
    upstream_refs: tuple[GovernedRef, ...],
    canonicalization_policy: CanonicalizationPolicy,
    build0_output_hash: Sha256Hex | None = None,
    build0_replay_hash: Sha256Hex | None = None,
) -> Build1BridgeReplayCapsule:
    return Build1BridgeReplayCapsule.model_validate(
        {
            "schema_version": BUILD1_BRIDGE_REPLAY_CAPSULE_SCHEMA_VERSION,
            "record_type": BUILD1_BRIDGE_REPLAY_CAPSULE_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "replay_ref": replay_ref,
            "algorithm_id": BUILD1_EXACT_REPLAY_ALGORITHM_ID,
            "caller_ids": caller_ids,
            "capture_gate_hash": capture_gate_hash(capture_gate, canonicalization_policy),
            "build0_request_hash": build0_request_hash_value,
            "upstream_refs": (*upstream_refs, *capture_gate.selected_upstream_refs),
            "build0_output_hash": build0_output_hash,
            "build0_replay_hash": build0_replay_hash,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )


def build1_bridge_replay_hash(
    capsule: Build1BridgeReplayCapsule,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(capsule, canonicalization_policy)


def _first_fail_closed_diagnostic(
    *,
    active_values: ActiveValueResolutionResult,
    proposals: tuple[TypedValueProposal, ...],
    scope_status: ScopeStatus,
    authority_status: AuthorityStatus,
    identity_status: IdentityStatus,
    context_key_status: ContextKeyStatus,
    evidence_locator_status: EvidenceLocatorStatus,
    build0_canonicalization_policy_ref: GovernedRef,
    canonicalization_policy: CanonicalizationPolicy,
) -> CaptureGateDiagnostic | None:
    if active_values.status == "INTEGRITY_FAILURE":
        return _diagnostic(
            BRIDGE_INTEGRITY_FAILURE_REASON_ID,
            "FAIL_CLOSED",
            upstream_diagnostics=active_values.diagnostics,
            supporting_refs=active_values.active_proposal_refs,
        )
    if scope_status == "INCOMPATIBLE":
        return _diagnostic(BRIDGE_SCOPE_INCOMPATIBLE_REASON_ID, "FAIL_CLOSED")
    if authority_status in {"INELIGIBLE", "MISSING_POLICY"}:
        return _diagnostic(BRIDGE_AUTHORITY_INELIGIBLE_REASON_ID, "FAIL_CLOSED")
    if identity_status == "UNRESOLVED":
        return _diagnostic(BRIDGE_IDENTITY_UNRESOLVED_REASON_ID, "FAIL_CLOSED")
    if identity_status == "COLLISION":
        return _diagnostic(BRIDGE_IDENTITY_COLLISION_REASON_ID, "FAIL_CLOSED")
    if context_key_status == "UNDEFINED":
        return _diagnostic(BRIDGE_CONTEXT_KEY_UNDEFINED_REASON_ID, "FAIL_CLOSED")
    if evidence_locator_status == "NOT_RATIFIABLE" or _has_unratifiable_evidence(proposals):
        return _diagnostic(BRIDGE_EVIDENCE_NOT_RATIFIABLE_REASON_ID, "FAIL_CLOSED")
    if active_values.status == "ACTIVE_VALUE_CONFLICT":
        return _diagnostic(
            BRIDGE_ACTIVE_VALUE_CONFLICT_REASON_ID,
            "FAIL_CLOSED",
            conflicting_event_refs=_conflicting_event_refs(active_values),
        )
    if _has_numeric_policy_mismatch(
        active_values.active_proposal_refs,
        proposals,
        build0_canonicalization_policy_ref,
        canonicalization_policy,
    ):
        return _diagnostic(BRIDGE_NUMERIC_POLICY_MISMATCH_REASON_ID, "FAIL_CLOSED")
    return None


def _first_advisory_gap_diagnostic(
    *,
    active_values: ActiveValueResolutionResult,
    proposals: tuple[TypedValueProposal, ...],
    observations: tuple[AttributedObservation, ...],
    observation_refs: tuple[GovernedRef, ...],
    capability_status: CapabilityStatus,
    parser_status: ParserStatus,
) -> CaptureGateDiagnostic | None:
    if not proposals and observation_refs:
        return _diagnostic(
            BRIDGE_ADVISORY_ONLY_OBSERVATION_REASON_ID,
            "ADVISORY_GAP",
            supporting_refs=observation_refs,
        )
    if active_values.status == "RESOLVED" and not active_values.active_proposal_refs:
        return _diagnostic(BRIDGE_MISSING_RATIFICATION_REASON_ID, "ADVISORY_GAP")
    if capability_status != "SUPPORTED":
        return _diagnostic(BRIDGE_CAPABILITY_GAP_REASON_ID, "ADVISORY_GAP")
    if parser_status in {"PARSER_UNAVAILABLE", "PARSER_UNSUPPORTED", "PARSER_FAILED"}:
        return _diagnostic(BRIDGE_PARSER_GAP_REASON_ID, "ADVISORY_GAP")
    if not proposals and observations:
        return _diagnostic(
            BRIDGE_ADVISORY_ONLY_OBSERVATION_REASON_ID,
            "ADVISORY_GAP",
            supporting_refs=observation_refs,
        )
    return None


def _bound_rows_for_active_refs(
    active_proposal_refs: tuple[GovernedRef, ...],
    proposals: tuple[TypedValueProposal, ...],
    canonicalization_policy: CanonicalizationPolicy,
) -> tuple[Build0BoundValueRow, ...]:
    proposals_by_key = {_ref_key(proposal.proposal_ref): proposal for proposal in proposals}
    rows = []
    for active_ref in active_proposal_refs:
        proposal = proposals_by_key[_ref_key(active_ref)]
        rows.append(
            Build0BoundValueRow.model_validate(
                {
                    "schema_version": BUILD0_BOUND_VALUE_ROW_SCHEMA_VERSION,
                    "row_kind": BUILD0_BOUND_VALUE_ROW_KIND,
                    "proposal_record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
                    "proposal_ref": proposal.proposal_ref,
                    "proposal_content_hash": proposal.proposal_ref.content_hash,
                    "target_key": active_value_key_payload(
                        proposal.target,
                        canonicalization_policy,
                    ),
                    "typed_canonical_value": proposal.proposed_value,
                    "evidence_location": proposal.evidence_location,
                    "canonicalization_policy_ref": proposal.canonicalization_policy_ref,
                },
                context={"canonicalization_policy": canonicalization_policy},
            )
        )
    return tuple(sorted(rows, key=_row_sort_key))


def _active_observation_refs(
    observations: tuple[AttributedObservation, ...],
    as_of_time: CanonicalTimestamp,
) -> tuple[GovernedRef, ...]:
    refs = tuple(
        observation.observation_ref
        for observation in observations
        if observation.validation_state == "UNVALIDATED"
        and observation.recorded_at <= as_of_time
        and observation.visibility_policy.advisory_context_allowed
    )
    return sorted_unique_refs(refs)


def _selected_upstream_refs(
    gate_ref: GovernedRef,
    active_values: ActiveValueResolutionResult,
    proposals: tuple[TypedValueProposal, ...],
    observation_refs: tuple[GovernedRef, ...],
) -> tuple[GovernedRef, ...]:
    state_event_refs = tuple(
        event_ref
        for state in active_values.target_states
        for event_ref in (
            *state.eligible_event_refs,
            *state.non_superseded_event_refs,
            *state.active_ratified_event_refs,
            *(state.conflicting_event_refs or ()),
        )
    )
    return sorted_unique_refs(
        (
            gate_ref,
            *(proposal.proposal_ref for proposal in proposals),
            *active_values.active_proposal_refs,
            *state_event_refs,
            *observation_refs,
        )
    )


def _ready_advisory_diagnostics(
    observation_refs: tuple[GovernedRef, ...],
) -> tuple[CaptureGateDiagnostic, ...]:
    if not observation_refs:
        return ()
    return (
        _diagnostic(
            BRIDGE_ADVISORY_ONLY_OBSERVATION_REASON_ID,
            "ADVISORY_GAP",
            supporting_refs=observation_refs,
        ),
    )


def _has_unratifiable_evidence(proposals: tuple[TypedValueProposal, ...]) -> bool:
    return any(isinstance(proposal.evidence_location, ProposalOnlyEvidence) for proposal in proposals)


def _has_numeric_policy_mismatch(
    active_proposal_refs: tuple[GovernedRef, ...],
    proposals: tuple[TypedValueProposal, ...],
    build0_canonicalization_policy_ref: GovernedRef,
    canonicalization_policy: CanonicalizationPolicy,
) -> bool:
    proposals_by_key = {_ref_key(proposal.proposal_ref): proposal for proposal in proposals}
    for active_ref in active_proposal_refs:
        proposal = proposals_by_key.get(_ref_key(active_ref))
        if proposal is None:
            return True
        # Intentional fail-closed strictness: Build 0 Tier 1 admits a proposal only when it
        # was canonicalized under Build 0's own policy ref. The plan's byte-identical
        # re-canonicalization fallback (§10) is deliberately NOT implemented here — re-
        # canonicalizing under a differently-identified policy would sever content-hash
        # provenance, so such a proposal fails closed (over-refusal, never a Tier 1 leak).
        if proposal.canonicalization_policy_ref != build0_canonicalization_policy_ref:
            return True
        try:
            canonical_sha256(proposal.proposed_value, canonicalization_policy)
        except CanonicalizationError:
            return True
    return False


def _conflicting_event_refs(
    active_values: ActiveValueResolutionResult,
) -> tuple[GovernedRef, ...]:
    return sorted_unique_refs(
        tuple(
            event_ref
            for state in active_values.target_states
            for event_ref in (state.conflicting_event_refs or ())
        )
    )


def _row_bound_refs(rows: tuple[Build0BoundValueRow, ...]) -> tuple[GovernedRef, ...]:
    return sorted_unique_refs(
        tuple(
            ref
            for row in rows
            for ref in (row.proposal_ref, row.evidence_location.source_artifact_ref)
        )
    )


def _capture_gate_result(
    *,
    gate_ref: GovernedRef,
    canonicalization_policy_ref: GovernedRef,
    canonicalization_policy: CanonicalizationPolicy,
    as_of_time: CanonicalTimestamp,
    status: CaptureGateStatus,
    reason_id: TermId,
    capability_status: CapabilityStatus,
    parser_status: ParserStatus,
    validation_protocol_status: ValidationProtocolStatus,
    active_value_state_hash: Sha256Hex,
    bound_value_rows: tuple[Build0BoundValueRow, ...],
    observation_refs: tuple[GovernedRef, ...],
    selected_upstream_refs: tuple[GovernedRef, ...],
    diagnostics: tuple[CaptureGateDiagnostic, ...],
) -> CaptureGateResult:
    return CaptureGateResult.model_validate(
        {
            "schema_version": BUILD0_BRIDGE_CAPTURE_GATE_SCHEMA_VERSION,
            "record_type": BUILD0_BRIDGE_CAPTURE_GATE_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "gate_ref": gate_ref,
            "canonicalization_policy_ref": canonicalization_policy_ref,
            "as_of_time": as_of_time,
            "status": status,
            "reason_id": reason_id,
            "capability_status": capability_status,
            "parser_status": parser_status,
            "validation_protocol_status": validation_protocol_status,
            "active_value_state_hash": active_value_state_hash,
            "bound_value_rows": bound_value_rows,
            "observation_refs": observation_refs,
            "selected_upstream_refs": selected_upstream_refs,
            "diagnostics": diagnostics,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )


def _diagnostic(
    reason_id: TermId,
    classification: DiagnosticClassification,
    *,
    proposal_ref: GovernedRef | None = None,
    target_key: dict[str, object] | None = None,
    capability_ref: GovernedRef | None = None,
    source_artifact_ref: GovernedRef | None = None,
    parser_algorithm_refs: tuple[GovernedRef, ...] = (),
    conflicting_event_refs: tuple[GovernedRef, ...] = (),
    supporting_refs: tuple[GovernedRef, ...] = (),
    upstream_diagnostics: tuple[TermId, ...] = (),
) -> CaptureGateDiagnostic:
    return CaptureGateDiagnostic(
        reason_id=reason_id,
        classification=classification,
        proposal_ref=proposal_ref,
        target_key=target_key,
        capability_ref=capability_ref,
        source_artifact_ref=source_artifact_ref,
        parser_algorithm_refs=parser_algorithm_refs,
        conflicting_event_refs=conflicting_event_refs,
        supporting_refs=supporting_refs,
        upstream_diagnostics=upstream_diagnostics,
    )


def _reconcile_existing_run(
    attempt: BridgeAttemptRecord,
    existing_run: ExistingBuild0RunRecord,
) -> BridgeAttemptRecord:
    if (
        existing_run.caller_ids != attempt.caller_ids
        or existing_run.build0_request_hash != attempt.build0_request_hash
    ):
        return _integrity_failed_attempt(attempt, BRIDGE_RETRY_MISMATCH_REASON_ID)
    if attempt.lifecycle_state in {"BUILD0_PERSISTED", "FINALIZED"}:
        if (
            attempt.build0_output_hash != existing_run.build0_output_hash
            or attempt.build0_replay_hash != existing_run.build0_replay_hash
        ):
            return _integrity_failed_attempt(attempt, BRIDGE_RETRY_MISMATCH_REASON_ID)
    return attempt.model_copy(
        update={
            "lifecycle_state": "BUILD0_PERSISTED",
            "build0_output_hash": existing_run.build0_output_hash,
            "build0_replay_hash": existing_run.build0_replay_hash,
            "failure_reason_id": None,
        }
    )


def _integrity_failed_attempt(
    attempt: BridgeAttemptRecord,
    reason_id: TermId,
) -> BridgeAttemptRecord:
    return attempt.model_copy(
        update={
            "lifecycle_state": "BRIDGE_INTEGRITY_FAILURE",
            "failure_reason_id": reason_id,
            "build0_output_hash": None,
            "build0_replay_hash": None,
        }
    )


def _row_sort_key(row: object) -> tuple[str, str, str]:
    if isinstance(row, Build0BoundValueRow):
        return (
            str(row.proposal_ref.logical_id),
            str(row.proposal_ref.version_id),
            str(row.target_key),
        )
    if isinstance(row, dict):
        proposal_ref = row["proposal_ref"]
        if isinstance(proposal_ref, GovernedRef):
            return (
                str(proposal_ref.logical_id),
                str(proposal_ref.version_id),
                str(row["target_key"]),
            )
        proposal_mapping = cast(dict[str, object], proposal_ref)
        return (
            str(proposal_mapping["logical_id"]),
            str(proposal_mapping["version_id"]),
            str(row["target_key"]),
        )
    raise ValueError("bound rows must be model or mapping values")


def _diagnostic_sort_key(value: object) -> tuple[str, str, str]:
    if isinstance(value, CaptureGateDiagnostic):
        proposal_ref = value.proposal_ref
        return (
            str(value.reason_id),
            str(proposal_ref.logical_id if proposal_ref is not None else ""),
            str(proposal_ref.version_id if proposal_ref is not None else ""),
        )
    if isinstance(value, dict):
        proposal_ref = value.get("proposal_ref")
        if isinstance(proposal_ref, GovernedRef):
            return (
                str(value["reason_id"]),
                str(proposal_ref.logical_id),
                str(proposal_ref.version_id),
            )
        if isinstance(proposal_ref, dict):
            return (
                str(value["reason_id"]),
                str(proposal_ref["logical_id"]),
                str(proposal_ref["version_id"]),
            )
        return (str(value["reason_id"]), "", "")
    raise ValueError("diagnostics must be model or mapping values")


def _ref_key(ref: GovernedRef) -> tuple[str, str]:
    return (str(ref.logical_id), str(ref.version_id))
