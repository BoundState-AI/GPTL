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
SOURCE_REGISTRATION_ACCEPTED_REASON_ID: Final = TermId("build1.source.registration-accepted")
SOURCE_PAYLOAD_TOO_LARGE_REASON_ID: Final = TermId("build1.source.payload-too-large")
HASH_ALGORITHM: Final = "SHA-256"
SOURCE_STREAM_CHUNK_BYTES: Final = io.DEFAULT_BUFFER_SIZE
OVER_LIMIT_PROBE_BYTES: Final = 1


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
    parser_eligibility: ParserEligibility

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
    parser_eligibility: ParserEligibility


class SourcePayloadTooLarge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["PAYLOAD_TOO_LARGE"]
    reason_id: TermId
    source_artifact_id: OpaqueId
    max_bytes_per_source_record: PositiveInt
    observed_bytes_before_rejection: PositiveInt


class SourceRegistrationAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["REGISTERED"]
    reason_id: TermId
    source_record: SourceArtifactRecord
    raw_bytes: bytes


class SourceRegistrationRejected(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["REJECTED"]
    reason_id: TermId
    source_artifact_id: OpaqueId
    capture_result: CaptureProfileNotReady


SourceRegistrationResult = (
    SourceRegistrationAccepted | SourceRegistrationRejected | SourcePayloadTooLarge
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
) -> RawPayload | SourcePayloadTooLarge:
    payload = bytearray()
    while True:
        remaining = max_bytes_per_source_record - len(payload)
        read_size = min(SOURCE_STREAM_CHUNK_BYTES, remaining + OVER_LIMIT_PROBE_BYTES)
        chunk = stream.read(read_size)
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
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> SourceRegistrationResult:
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
    raw_payload = read_raw_payload_with_limit(
        raw_stream,
        storage_policy.max_bytes_per_source_record,
        request.source_artifact_id,
    )
    if isinstance(raw_payload, SourcePayloadTooLarge):
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
            "parser_eligibility": request.parser_eligibility,
        },
        context={"canonicalization_policy": canonicalization_policy},
    )
    return SourceRegistrationAccepted(
        status="REGISTERED",
        reason_id=SOURCE_REGISTRATION_ACCEPTED_REASON_ID,
        source_record=finalize_source_artifact_record(source_record, canonicalization_policy),
        raw_bytes=raw_payload.raw_bytes,
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
    if registration.source_record.raw_byte_hash != compute_raw_byte_hash(registration.raw_bytes):
        raise ValueError("source raw bytes do not match raw byte hash")
    expected_content_hash = source_artifact_content_hash(
        registration.source_record,
        canonicalization_policy,
    )
    if registration.source_record.source_ref.content_hash != expected_content_hash:
        raise ValueError("source artifact content hash mismatch")


def _storage_policy_for_readiness(
    capability_profile: CapabilityProfile,
    readiness: CaptureProfileReady,
) -> SourceStoragePolicy:
    for storage_policy in capability_profile.storage_policies:
        if storage_policy.storage_policy_ref == readiness.storage_policy_ref:
            return storage_policy
    raise ValueError("capture readiness resolved an undeclared storage policy")
