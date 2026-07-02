"""Build 1 raw source artifact registration contracts."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Final, Literal, Protocol

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.capabilities import (
    CapabilityProfile,
    CaptureProfileNotReady,
    CaptureProfileReady,
    SourceStoragePolicy,
    evaluate_capture_profile,
)
from gptl.core.records import GovernedRef, governed_record_content_hash, sorted_unique_refs
from gptl.core.scope import EvidenceScopeV1, ScopeTermRegistry
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    NonNegativeInt,
    OpaqueId,
    PositiveInt,
    Sha256Hex,
    TermId,
)

SOURCE_ARTIFACT_SCHEMA_VERSION: Final = "gptl.build1.source-artifact.v1"
SOURCE_ARTIFACT_RECORD_TYPE: Final = "SOURCE_ARTIFACT"
SOURCE_RAW_BYTES_RECORD_TYPE: Final = "SOURCE_RAW_BYTES"
SOURCE_REGISTRATION_AUDIT_SCHEMA_VERSION: Final = "gptl.build1.source-registration-audit.v1"
SOURCE_REGISTRATION_AUDIT_EVENT_RECORD_TYPE: Final = "SOURCE_REGISTRATION_AUDIT_EVENT"
SOURCE_REGISTRATION_ACCEPTED_REASON_ID: Final = TermId("build1.source.registration-accepted")
SOURCE_PAYLOAD_TOO_LARGE_REASON_ID: Final = TermId("build1.source.payload-too-large")
SOURCE_CONFIGURATION_INVALID_REASON_ID: Final = TermId("build1.source.configuration-invalid")
SOURCE_GOVERNANCE_REF_MISMATCH_REASON_ID: Final = TermId(
    "build1.source.governance-ref-mismatch"
)
SOURCE_PARSER_ELIGIBILITY_UNKNOWN_REASON_ID: Final = TermId(
    "build1.source.parser-eligibility-unknown"
)
SOURCE_STREAM_CONTRACT_VIOLATION_REASON_ID: Final = TermId(
    "build1.source.stream-contract-violation"
)
HASH_ALGORITHM: Final = "SHA-256"
SOURCE_STREAM_CHUNK_BYTES: Final = io.DEFAULT_BUFFER_SIZE
OVER_LIMIT_PROBE_BYTES: Final = 1
SOURCE_REGISTRATION_AUDIT_SEQUENCE: Final = 0


class RawByteStream(Protocol):
    def read(self, size: int = -1) -> bytes: ...


class ParserEligibility(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal[
        "UNPARSED",
        "PARSER_UNAVAILABLE",
        "PARSER_UNSUPPORTED",
        "PARSER_READY",
        "PARSER_FAILED",
    ]
    parser_algorithm_refs: tuple[GovernedRef, ...] = ()
    reason_id: TermId | None = None

    @model_validator(mode="before")
    @classmethod
    def sort_algorithm_refs(cls, value: object) -> object:
        if not isinstance(value, dict) or "parser_algorithm_refs" not in value:
            return value
        normalized = dict(value)
        normalized["parser_algorithm_refs"] = sorted_unique_refs(
            tuple(normalized["parser_algorithm_refs"])
        )
        return normalized

    @model_validator(mode="after")
    def validate_status_payload(self) -> ParserEligibility:
        if self.status == "PARSER_READY":
            if not self.parser_algorithm_refs or self.reason_id is not None:
                raise ValueError("parser-ready source requires parser algorithms and no reason")
            return self
        if self.status == "PARSER_FAILED":
            if not self.parser_algorithm_refs or self.reason_id is None:
                raise ValueError("parser-failed source requires parser algorithms and reason")
            return self
        if self.status in {"PARSER_UNAVAILABLE", "PARSER_UNSUPPORTED"}:
            if self.parser_algorithm_refs or self.reason_id is None:
                raise ValueError("parser-ineligible source requires reason and no algorithms")
            return self
        if self.parser_algorithm_refs or self.reason_id is not None:
            raise ValueError("unparsed source cannot bind parser algorithms or reason")
        return self


class ParserEligibilityRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_class_id: TermId
    media_type: OpaqueId
    parser_eligibility: ParserEligibility


class ParserEligibilityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_ref: GovernedRef
    rules: tuple[ParserEligibilityRule, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_rules(cls, value: object) -> object:
        if not isinstance(value, dict) or "rules" not in value:
            return value
        normalized = dict(value)
        normalized["rules"] = tuple(
            sorted(
                normalized["rules"],
                key=lambda item: (
                    str(_field_value(item, "source_class_id")),
                    str(_field_value(item, "media_type")),
                ),
            )
        )
        return normalized

    @model_validator(mode="after")
    def validate_rules(self) -> ParserEligibilityPolicy:
        if not self.rules:
            raise ValueError("parser eligibility policy requires at least one rule")
        keys = tuple((rule.source_class_id, rule.media_type) for rule in self.rules)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("parser eligibility rules must be unique and sorted")
        return self


class SourceArtifactRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_artifact_id: OpaqueId
    source_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    media_type: OpaqueId
    filename: str | None = None
    external_identifier: str | None = None
    source_class_id: TermId
    claimed_origin_id: TermId
    submitter_ref: GovernedRef
    received_at: CanonicalTimestamp
    asserted_source_time: CanonicalTimestamp | None = None
    evidence_scope_ref: GovernedRef
    capability_profile_ref: GovernedRef
    parser_eligibility_policy_ref: GovernedRef

    @model_validator(mode="after")
    def validate_metadata(self) -> SourceArtifactRegistrationRequest:
        if self.filename is not None and not self.filename.strip():
            raise ValueError("source filename cannot be blank")
        if self.external_identifier is not None and not self.external_identifier.strip():
            raise ValueError("source external identifier cannot be blank")
        return self


class SourceArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.source-artifact.v1"]
    record_type: Literal["SOURCE_ARTIFACT"]
    hash_algorithm: Literal["SHA-256"]
    source_artifact_id: OpaqueId
    source_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    raw_byte_hash: Sha256Hex
    byte_length: NonNegativeInt
    media_type: OpaqueId
    filename: str | None = None
    external_identifier: str | None = None
    source_class_id: TermId
    claimed_origin_id: TermId
    submitter_ref: GovernedRef
    received_at: CanonicalTimestamp
    asserted_source_time: CanonicalTimestamp | None = None
    evidence_scope_ref: GovernedRef
    capability_profile_ref: GovernedRef
    storage_policy_ref: GovernedRef
    parser_eligibility_policy_ref: GovernedRef
    parser_eligibility: ParserEligibility


class SourcePayloadTooLarge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["PAYLOAD_TOO_LARGE"]
    reason_id: TermId
    source_artifact_id: OpaqueId
    max_bytes_per_source_record: PositiveInt
    observed_bytes_before_rejection: PositiveInt


class SourceStreamContractViolation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["STREAM_CONTRACT_VIOLATION"]
    reason_id: TermId
    source_artifact_id: OpaqueId
    requested_read_bytes: PositiveInt
    observed_chunk_bytes: PositiveInt


class SourceConfigurationInvalid(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["CONFIGURATION_INVALID"]
    reason_id: TermId
    source_artifact_id: OpaqueId
    issue_id: TermId
    expected_ref: GovernedRef | None = None
    actual_ref: GovernedRef | None = None


class SourceRegistrationAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: OpaqueId
    source_artifact_id: OpaqueId
    sequence: NonNegativeInt
    schema_version: Literal["gptl.build1.source-registration-audit.v1"]
    record_type: Literal["SOURCE_REGISTRATION_AUDIT_EVENT"]
    hash_algorithm: Literal["SHA-256"]
    reason_id: TermId
    source_ref: GovernedRef
    raw_byte_hash: Sha256Hex
    byte_length: NonNegativeInt
    capability_profile_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    parser_eligibility_policy_ref: GovernedRef
    event_time: CanonicalTimestamp


class SourceRegistrationAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["REGISTERED"]
    reason_id: TermId
    source_record: SourceArtifactRecord
    raw_bytes: bytes
    audit_event: SourceRegistrationAuditEvent


class SourceRegistrationRejected(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["REJECTED"]
    reason_id: TermId
    source_artifact_id: OpaqueId
    capture_result: CaptureProfileNotReady


SourceRegistrationResult = (
    SourceRegistrationAccepted
    | SourceRegistrationRejected
    | SourcePayloadTooLarge
    | SourceStreamContractViolation
    | SourceConfigurationInvalid
)


@dataclass(frozen=True)
class RawPayload:
    raw_bytes: bytes
    raw_byte_hash: str
    byte_length: int


def compute_raw_byte_hash(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def read_raw_payload_with_limit(
    stream: RawByteStream,
    max_bytes_per_source_record: PositiveInt,
    source_artifact_id: OpaqueId,
) -> RawPayload | SourcePayloadTooLarge | SourceStreamContractViolation:
    payload = bytearray()
    while True:
        remaining = max_bytes_per_source_record - len(payload)
        read_size = min(SOURCE_STREAM_CHUNK_BYTES, remaining + OVER_LIMIT_PROBE_BYTES)
        chunk = stream.read(read_size)
        if len(chunk) > read_size:
            return SourceStreamContractViolation(
                status="STREAM_CONTRACT_VIOLATION",
                reason_id=SOURCE_STREAM_CONTRACT_VIOLATION_REASON_ID,
                source_artifact_id=source_artifact_id,
                requested_read_bytes=read_size,
                observed_chunk_bytes=len(chunk),
            )
        if not chunk:
            raw_bytes = bytes(payload)
            return RawPayload(
                raw_bytes=raw_bytes,
                raw_byte_hash=compute_raw_byte_hash(raw_bytes),
                byte_length=len(raw_bytes),
            )
        if len(payload) + len(chunk) > max_bytes_per_source_record:
            return SourcePayloadTooLarge(
                status="PAYLOAD_TOO_LARGE",
                reason_id=SOURCE_PAYLOAD_TOO_LARGE_REASON_ID,
                source_artifact_id=source_artifact_id,
                max_bytes_per_source_record=max_bytes_per_source_record,
                observed_bytes_before_rejection=len(payload) + len(chunk),
            )
        payload.extend(chunk)


def prepare_source_registration(
    request: SourceArtifactRegistrationRequest,
    raw_stream: RawByteStream,
    capability_profile: CapabilityProfile,
    candidate_scope: EvidenceScopeV1,
    run_scope: EvidenceScopeV1,
    scope_term_registry: ScopeTermRegistry,
    parser_eligibility_policy: ParserEligibilityPolicy,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
    canonicalization_policy_ref: GovernedRef,
) -> SourceRegistrationResult:
    mismatch = _validate_registration_refs(
        request,
        capability_profile,
        candidate_scope,
        parser_eligibility_policy,
        canonicalization_policy_ref,
    )
    if mismatch is not None:
        return mismatch

    readiness = evaluate_capture_profile(
        capability_profile,
        candidate_scope,
        run_scope,
        scope_term_registry,
        request.source_class_id,
        as_of_time,
    )
    if isinstance(readiness, CaptureProfileNotReady):
        return SourceRegistrationRejected(
            status="REJECTED",
            reason_id=readiness.reason_id,
            source_artifact_id=request.source_artifact_id,
            capture_result=readiness,
        )

    storage_policy = _storage_policy_for_readiness(capability_profile, readiness)
    parser_eligibility = govern_parser_eligibility(
        parser_eligibility_policy,
        request.source_class_id,
        request.media_type,
        request.source_artifact_id,
    )
    if isinstance(parser_eligibility, SourceConfigurationInvalid):
        return parser_eligibility

    raw_payload = read_raw_payload_with_limit(
        raw_stream,
        storage_policy.max_bytes_per_source_record,
        request.source_artifact_id,
    )
    if isinstance(raw_payload, (SourcePayloadTooLarge, SourceStreamContractViolation)):
        return raw_payload

    source_record = SourceArtifactRecord.model_validate(
        {
            "schema_version": SOURCE_ARTIFACT_SCHEMA_VERSION,
            "record_type": SOURCE_ARTIFACT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "source_artifact_id": request.source_artifact_id,
            "source_ref": request.source_ref,
            "canonicalization_policy_ref": request.canonicalization_policy_ref,
            "lifecycle_state": request.lifecycle_state,
            "raw_byte_hash": raw_payload.raw_byte_hash,
            "byte_length": raw_payload.byte_length,
            "media_type": request.media_type,
            "filename": request.filename,
            "external_identifier": request.external_identifier,
            "source_class_id": request.source_class_id,
            "claimed_origin_id": request.claimed_origin_id,
            "submitter_ref": request.submitter_ref,
            "received_at": request.received_at,
            "asserted_source_time": request.asserted_source_time,
            "evidence_scope_ref": request.evidence_scope_ref,
            "capability_profile_ref": request.capability_profile_ref,
            "storage_policy_ref": readiness.storage_policy_ref,
            "parser_eligibility_policy_ref": request.parser_eligibility_policy_ref,
            "parser_eligibility": parser_eligibility,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )
    finalized_record = finalize_source_artifact_record(source_record, canonicalization_policy)
    return SourceRegistrationAccepted(
        status="REGISTERED",
        reason_id=SOURCE_REGISTRATION_ACCEPTED_REASON_ID,
        source_record=finalized_record,
        raw_bytes=raw_payload.raw_bytes,
        audit_event=_source_registration_audit_event(finalized_record, canonicalization_policy),
    )


def govern_parser_eligibility(
    policy: ParserEligibilityPolicy,
    source_class_id: TermId,
    media_type: OpaqueId,
    source_artifact_id: OpaqueId,
) -> ParserEligibility | SourceConfigurationInvalid:
    for rule in policy.rules:
        if rule.source_class_id == source_class_id and rule.media_type == media_type:
            return rule.parser_eligibility
    return SourceConfigurationInvalid(
        status="CONFIGURATION_INVALID",
        reason_id=SOURCE_CONFIGURATION_INVALID_REASON_ID,
        source_artifact_id=source_artifact_id,
        issue_id=SOURCE_PARSER_ELIGIBILITY_UNKNOWN_REASON_ID,
    )


def source_artifact_content_hash(
    source_record: SourceArtifactRecord,
    canonicalization_policy: CanonicalizationPolicy,
) -> str:
    return governed_record_content_hash(source_record, "source_ref", canonicalization_policy)


def finalize_source_artifact_record(
    source_record: SourceArtifactRecord,
    canonicalization_policy: CanonicalizationPolicy,
) -> SourceArtifactRecord:
    content_hash = source_artifact_content_hash(source_record, canonicalization_policy)
    updated_ref = source_record.source_ref.model_copy(update={"content_hash": content_hash})
    return source_record.model_copy(update={"source_ref": updated_ref})


def verify_source_registration(
    registration: SourceRegistrationAccepted,
    canonicalization_policy: CanonicalizationPolicy,
) -> None:
    record = registration.source_record
    if (
        registration.reason_id != SOURCE_REGISTRATION_ACCEPTED_REASON_ID
        or registration.audit_event.reason_id != SOURCE_REGISTRATION_ACCEPTED_REASON_ID
    ):
        raise ValueError("source registration reason mismatch")
    if registration.source_record.raw_byte_hash != compute_raw_byte_hash(registration.raw_bytes):
        raise ValueError("source raw bytes do not match raw byte hash")
    expected_content_hash = source_artifact_content_hash(
        registration.source_record,
        canonicalization_policy,
    )
    if registration.source_record.source_ref.content_hash != expected_content_hash:
        raise ValueError("source artifact content hash mismatch")
    if (
        registration.audit_event.source_artifact_id != record.source_artifact_id
        or registration.audit_event.source_ref != record.source_ref
        or registration.audit_event.raw_byte_hash != record.raw_byte_hash
        or registration.audit_event.byte_length != record.byte_length
        or registration.audit_event.capability_profile_ref != record.capability_profile_ref
        or registration.audit_event.evidence_scope_ref != record.evidence_scope_ref
        or registration.audit_event.canonicalization_policy_ref != record.canonicalization_policy_ref
        or registration.audit_event.parser_eligibility_policy_ref
        != record.parser_eligibility_policy_ref
    ):
        raise ValueError("source registration audit event does not match source record")


def _storage_policy_for_readiness(
    capability_profile: CapabilityProfile,
    readiness: CaptureProfileReady,
) -> SourceStoragePolicy:
    for storage_policy in capability_profile.storage_policies:
        if storage_policy.storage_policy_ref == readiness.storage_policy_ref:
            return storage_policy
    raise ValueError("capture readiness resolved an undeclared storage policy")


def _validate_registration_refs(
    request: SourceArtifactRegistrationRequest,
    capability_profile: CapabilityProfile,
    candidate_scope: EvidenceScopeV1,
    parser_eligibility_policy: ParserEligibilityPolicy,
    canonicalization_policy_ref: GovernedRef,
) -> SourceConfigurationInvalid | None:
    checks = (
        (request.capability_profile_ref, capability_profile.profile_ref),
        (request.evidence_scope_ref, candidate_scope.scope_ref),
        (request.parser_eligibility_policy_ref, parser_eligibility_policy.policy_ref),
        (request.canonicalization_policy_ref, canonicalization_policy_ref),
    )
    for actual_ref, expected_ref in checks:
        if actual_ref != expected_ref:
            return SourceConfigurationInvalid(
                status="CONFIGURATION_INVALID",
                reason_id=SOURCE_CONFIGURATION_INVALID_REASON_ID,
                source_artifact_id=request.source_artifact_id,
                issue_id=SOURCE_GOVERNANCE_REF_MISMATCH_REASON_ID,
                expected_ref=expected_ref,
                actual_ref=actual_ref,
            )
    return None


def _source_registration_audit_event(
    source_record: SourceArtifactRecord,
    canonicalization_policy: CanonicalizationPolicy,
) -> SourceRegistrationAuditEvent:
    return SourceRegistrationAuditEvent.model_validate(
        {
            "event_id": f"{source_record.source_artifact_id}:registration-audit",
            "source_artifact_id": source_record.source_artifact_id,
            "sequence": SOURCE_REGISTRATION_AUDIT_SEQUENCE,
            "schema_version": SOURCE_REGISTRATION_AUDIT_SCHEMA_VERSION,
            "record_type": SOURCE_REGISTRATION_AUDIT_EVENT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "reason_id": SOURCE_REGISTRATION_ACCEPTED_REASON_ID,
            "source_ref": source_record.source_ref,
            "raw_byte_hash": source_record.raw_byte_hash,
            "byte_length": source_record.byte_length,
            "capability_profile_ref": source_record.capability_profile_ref,
            "evidence_scope_ref": source_record.evidence_scope_ref,
            "canonicalization_policy_ref": source_record.canonicalization_policy_ref,
            "parser_eligibility_policy_ref": source_record.parser_eligibility_policy_ref,
            "event_time": source_record.received_at,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, BaseModel):
        return getattr(value, field_name)
    if isinstance(value, dict):
        return value[field_name]
    raise ValueError("parser eligibility rules must be model or mapping values")
