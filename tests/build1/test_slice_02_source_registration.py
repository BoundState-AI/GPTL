from __future__ import annotations

import hashlib
import io
from collections.abc import Callable

import psycopg
import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.core.capabilities import CapabilityProfile
from gptl.core.persistence import PersistenceIntegrityError, PostgresRunStore
from gptl.core.records import GovernedRef
from gptl.core.scope import (
    CONTEXT_DIMENSION_ID,
    DATA_BOUNDARY_DIMENSION_ID,
    ORGANIZATION_DIMENSION_ID,
    SCOPE_CLASS_DIMENSION_ID,
    SITE_DIMENSION_ID,
    WORKSPACE_DIMENSION_ID,
    EvidenceScopeV1,
    ScopeTermRegistry,
)
from gptl.core.semantic_types import TermId
from gptl.core.source_artifacts import (
    ParserEligibility,
    SourceArtifactRegistrationRequest,
    SourcePayloadTooLarge,
    SourceRegistrationAccepted,
    SourceRegistrationRejected,
    SourceRegistrationResult,
    compute_raw_byte_hash,
    prepare_source_registration,
)
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-06-29T12:00:00.000Z"
RECEIVED_AT = "2026-06-29T12:00:01.000Z"
DEFAULT_ORGANIZATION_ID = TermId("org.boundstate")
DEFAULT_SITE_ID = TermId("site.materials-lab")
DEFAULT_WORKSPACE_ID = TermId("workspace.gptl-build1")
DEFAULT_DATA_BOUNDARY_ID = TermId("boundary.synthetic-build1")
DEFAULT_CONTEXT_ID = TermId("context.slice2")
DEFAULT_SOURCE_CLASS_ID = TermId("source-class.test-report")
DEFAULT_MAX_SOURCE_BYTES = 16
OVERSIZE_SOURCE_BYTES = b"0123456789abcdef-over-limit"
TEXT_LINE_FEED_BYTES = b"alpha\nbeta\n"
TEXT_CRLF_BYTES = b"alpha\r\nbeta\r\n"
BINARY_SOURCE_BYTES = b"\x00\x01raw\xffbytes"


def test_identical_bytes_produce_identical_raw_hash() -> None:
    assert compute_raw_byte_hash(BINARY_SOURCE_BYTES) == compute_raw_byte_hash(BINARY_SOURCE_BYTES)


def test_metadata_changes_content_hash_not_raw_hash(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    first = _accepted_registration(build1_ref_factory, filename="first.csv")
    second = _accepted_registration(build1_ref_factory, filename="second.csv")

    assert first.source_record.raw_byte_hash == second.source_record.raw_byte_hash
    assert first.source_record.source_ref.content_hash != second.source_record.source_ref.content_hash


def test_text_and_binary_artifacts_are_hashed_as_exact_received_bytes(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    line_feed = _accepted_registration(build1_ref_factory, raw_bytes=TEXT_LINE_FEED_BYTES)
    crlf = _accepted_registration(build1_ref_factory, raw_bytes=TEXT_CRLF_BYTES)
    binary = _accepted_registration(build1_ref_factory, raw_bytes=BINARY_SOURCE_BYTES)

    assert line_feed.source_record.raw_byte_hash == compute_raw_byte_hash(TEXT_LINE_FEED_BYTES)
    assert crlf.source_record.raw_byte_hash == compute_raw_byte_hash(TEXT_CRLF_BYTES)
    assert binary.source_record.raw_byte_hash == compute_raw_byte_hash(BINARY_SOURCE_BYTES)
    assert line_feed.source_record.raw_byte_hash != crlf.source_record.raw_byte_hash


def test_over_limit_payload_fails_before_full_buffer_read(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    stream = _TrackingStream(OVERSIZE_SOURCE_BYTES)
    result = _prepare_registration(
        build1_ref_factory,
        raw_stream=stream,
        max_source_bytes=DEFAULT_MAX_SOURCE_BYTES,
    )

    assert isinstance(result, SourcePayloadTooLarge)
    assert result.max_bytes_per_source_record == DEFAULT_MAX_SOURCE_BYTES
    assert result.observed_bytes_before_rejection == DEFAULT_MAX_SOURCE_BYTES + 1
    assert stream.bytes_returned == DEFAULT_MAX_SOURCE_BYTES + 1
    assert stream.bytes_returned < len(OVERSIZE_SOURCE_BYTES)


def test_unsupported_source_class_returns_governed_capture_gap(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    result = _prepare_registration(
        build1_ref_factory,
        source_class_id=TermId("source-class.vendor-binary"),
    )

    assert isinstance(result, SourceRegistrationRejected)
    assert result.capture_result.capability_failure is not None
    assert result.capture_result.capability_failure.status == "UNSUPPORTED"


def test_parser_eligibility_state_is_deterministic_and_replayable(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    algorithm_a = build1_ref_factory("build1.parser.csv")
    algorithm_b = build1_ref_factory("build1.decoder.utf8")
    first = ParserEligibility(
        status="PARSER_READY",
        parser_algorithm_refs=(algorithm_b, algorithm_a),
    )
    second = ParserEligibility(
        status="PARSER_READY",
        parser_algorithm_refs=(algorithm_a, algorithm_b),
    )

    assert canonical_bytes(first, policy) == canonical_bytes(second, policy)
    assert tuple(ref.logical_id for ref in first.parser_algorithm_refs) == (
        "build1.decoder.utf8",
        "build1.parser.csv",
    )


@pytest.mark.parametrize(
    "payload,error",
    (
        ({"status": "PARSER_READY"}, "parser-ready"),
        (
            {
                "status": "PARSER_UNSUPPORTED",
                "parser_algorithm_refs": (),
            },
            "parser-ineligible",
        ),
        (
            {
                "status": "UNPARSED",
                "reason_id": "build1.parser.not-requested",
            },
            "unparsed",
        ),
    ),
)
def test_parser_eligibility_requires_algorithm_or_reason_by_state(
    payload: dict[str, object],
    error: str,
) -> None:
    with pytest.raises(ValidationError, match=error):
        ParserEligibility.model_validate(payload)


def test_raw_bytes_round_trip_exactly_from_postgres(
    postgres_url: str,
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    store = PostgresRunStore(postgres_url, policy)
    store.initialize()
    registration = _accepted_registration(build1_ref_factory, raw_bytes=BINARY_SOURCE_BYTES)

    store.persist_source_registration(registration)
    stored = store.load_source_artifact(registration.source_record.source_artifact_id)

    assert stored is not None
    assert stored.raw_bytes == BINARY_SOURCE_BYTES
    assert stored.raw_byte_hash == compute_raw_byte_hash(BINARY_SOURCE_BYTES)
    assert stored.payload == canonical_bytes(registration.source_record, policy)


def test_failed_source_registration_leaves_no_rows_or_raw_bytes(
    postgres_url: str,
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    store = PostgresRunStore(postgres_url, policy)
    store.initialize()
    registration = _accepted_registration(build1_ref_factory)
    tampered = registration.model_copy(
        update={
            "source_record": registration.source_record.model_copy(
                update={"raw_byte_hash": "0" * 64}
            )
        }
    )

    with pytest.raises((PersistenceIntegrityError, ValueError), match="raw byte"):
        store.persist_source_registration(tampered)

    with psycopg.connect(postgres_url) as connection:
        source_count = connection.execute("SELECT count(*) FROM gptl_source_artifacts").fetchone()
        raw_count = connection.execute("SELECT count(*) FROM gptl_source_raw_bytes").fetchone()

    assert source_count == (0,)
    assert raw_count == (0,)


def test_database_rejects_source_artifact_without_raw_bytes(
    postgres_url: str,
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    store = PostgresRunStore(postgres_url, policy)
    store.initialize()
    registration = _accepted_registration(build1_ref_factory)

    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="raw byte pair"), connection.transaction():
            _insert_source_artifact_metadata(connection, registration, policy)


def test_database_rejects_source_raw_byte_metadata_mismatch(
    postgres_url: str,
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    store = PostgresRunStore(postgres_url, policy)
    store.initialize()
    registration = _accepted_registration(build1_ref_factory)

    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="raw byte metadata mismatch"), connection.transaction():
            _insert_source_artifact_metadata(connection, registration, policy)
            _insert_source_raw_bytes(
                connection,
                registration,
                raw_byte_hash="0" * 64,
                byte_length=len(registration.raw_bytes),
                raw_bytes=registration.raw_bytes,
            )


def test_load_source_artifact_fails_loud_for_historical_orphan_metadata(
    postgres_url: str,
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    store = PostgresRunStore(postgres_url, policy)
    store.initialize()
    registration = _accepted_registration(build1_ref_factory)

    with psycopg.connect(postgres_url) as connection:
        with connection.transaction():
            connection.execute(
                """
                ALTER TABLE gptl_source_artifacts
                DISABLE TRIGGER gptl_source_artifacts_validate_raw_byte_pair
                """
            )
            _insert_source_artifact_metadata(connection, registration, policy)
            connection.execute(
                """
                ALTER TABLE gptl_source_artifacts
                ENABLE TRIGGER gptl_source_artifacts_validate_raw_byte_pair
                """
            )

    with pytest.raises(PersistenceIntegrityError, match="raw bytes are missing"):
        store.load_source_artifact(registration.source_record.source_artifact_id)


def test_load_source_artifact_fails_loud_for_tampered_raw_bytes(
    postgres_url: str,
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    store = PostgresRunStore(postgres_url, policy)
    store.initialize()
    registration = _accepted_registration(build1_ref_factory)

    with psycopg.connect(postgres_url) as connection:
        with connection.transaction():
            _insert_source_artifact_metadata(connection, registration, policy)
            _insert_source_raw_bytes(
                connection,
                registration,
                raw_byte_hash=registration.source_record.raw_byte_hash,
                byte_length=len(registration.raw_bytes),
                raw_bytes=b"tamper-data",
            )

    with pytest.raises(ValueError, match="checksum mismatch"):
        store.load_source_artifact(registration.source_record.source_artifact_id)


def _accepted_registration(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    raw_bytes: bytes = TEXT_LINE_FEED_BYTES,
    filename: str = "source.csv",
) -> SourceRegistrationAccepted:
    result = _prepare_registration(
        build1_ref_factory,
        raw_stream=io.BytesIO(raw_bytes),
        filename=filename,
    )
    assert isinstance(result, SourceRegistrationAccepted)
    return result


def _prepare_registration(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    raw_stream: io.BytesIO | _TrackingStream | None = None,
    filename: str = "source.csv",
    source_class_id: TermId = DEFAULT_SOURCE_CLASS_ID,
    max_source_bytes: int = DEFAULT_MAX_SOURCE_BYTES,
) -> SourceRegistrationResult:
    policy = canonicalization_policy()
    return prepare_source_registration(
        _request(build1_ref_factory, filename=filename, source_class_id=source_class_id),
        raw_stream or io.BytesIO(TEXT_LINE_FEED_BYTES),
        _profile(build1_ref_factory, max_source_bytes=max_source_bytes),
        _scope(build1_ref_factory),
        _scope(build1_ref_factory, ref_id="build1.scope.run"),
        _term_registry(build1_ref_factory),
        AS_OF,
        policy,
    )


def _request(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    filename: str,
    source_class_id: TermId,
) -> SourceArtifactRegistrationRequest:
    policy = canonicalization_policy()
    return SourceArtifactRegistrationRequest.model_validate(
        {
            "source_artifact_id": "source-artifact.fixture-1",
            "source_ref": build1_ref_factory("build1.source.fixture-1"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": "ACTIVE",
            "media_type": "text/csv",
            "filename": filename,
            "external_identifier": "external.fixture-1",
            "source_class_id": source_class_id,
            "claimed_origin_id": "origin.synthetic-fixture",
            "submitter_ref": build1_ref_factory("build1.submitter.materials"),
            "received_at": RECEIVED_AT,
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "capability_profile_ref": build1_ref_factory("build1.capability.profile"),
            "parser_eligibility": {
                "status": "PARSER_UNSUPPORTED",
                "reason_id": "build1.parser.no-governed-parser",
            },
        },
        context={"canonicalization_policy": policy},
    )


def _scope(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    ref_id: str = "build1.scope.candidate",
) -> EvidenceScopeV1:
    return EvidenceScopeV1(
        schema_version="gptl.build1.evidence-scope.v1",
        scope_ref=build1_ref_factory(ref_id),
        canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy"),
        lifecycle_state="ACTIVE",
        scope_class="TEST_FIXTURE",
        organization_id=DEFAULT_ORGANIZATION_ID,
        site_id=DEFAULT_SITE_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        data_boundary_id=DEFAULT_DATA_BOUNDARY_ID,
        context_id=DEFAULT_CONTEXT_ID,
    )


def _term_registry(build1_ref_factory: Callable[[str], GovernedRef]) -> ScopeTermRegistry:
    return ScopeTermRegistry.model_validate(
        {
            "registry_ref": build1_ref_factory("build1.scope-term-registry"),
            "term_sets": (
                {
                    "dimension_id": SCOPE_CLASS_DIMENSION_ID,
                    "allowed_term_ids": ("TEST_FIXTURE",),
                },
                {
                    "dimension_id": ORGANIZATION_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_ORGANIZATION_ID,),
                },
                {
                    "dimension_id": SITE_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_SITE_ID,),
                },
                {
                    "dimension_id": WORKSPACE_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_WORKSPACE_ID,),
                },
                {
                    "dimension_id": DATA_BOUNDARY_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_DATA_BOUNDARY_ID,),
                },
                {
                    "dimension_id": CONTEXT_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_CONTEXT_ID,),
                },
            ),
        }
    )


def _profile(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    max_source_bytes: int,
) -> CapabilityProfile:
    storage_report = build1_ref_factory("build1.storage.report")
    canonicalization_policy_ref = build1_ref_factory("build1.canonicalization.policy")
    return CapabilityProfile.model_validate(
        {
            "schema_version": "gptl.build1.capability-profile.v1",
            "profile_ref": build1_ref_factory("build1.capability.profile"),
            "canonicalization_policy_ref": canonicalization_policy_ref,
            "lifecycle_state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "expires_at": "2026-12-31T23:59:59.000Z",
            "owner_ref": build1_ref_factory("build1.owner.materials"),
            "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "instrument_tool_type_ids": ("tool.sem",),
            "source_systems": (
                {
                    "source_system_id": "source-system.lims",
                    "lifecycle_state": "ACTIVE",
                    "source_system_class_id": "source-system-class.lims",
                },
            ),
            "accepted_source_classes": (
                {
                    "source_class_id": "source-class.test-report",
                    "source_system_id": "source-system.lims",
                    "storage_policy_ref": storage_report,
                },
            ),
            "unsupported_source_classes": ("source-class.vendor-binary",),
            "measurement_class_ids": ("measurement.micrograph",),
            "calibration_msa_capability_label_ids": (),
            "storage_policies": (
                {
                    "storage_policy_ref": storage_report,
                    "canonicalization_policy_ref": canonicalization_policy_ref,
                    "lifecycle_state": "ACTIVE",
                    "max_bytes_per_source_record": max_source_bytes,
                    "allowed_evidence_locator_classes": ("evidence.byte-range",),
                },
            ),
            "evidence_refs": (build1_ref_factory("build1.evidence.capability-source-inventory"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


class _TrackingStream:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0
        self.bytes_returned = 0

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        self.bytes_returned += len(chunk)
        return chunk


def _insert_source_artifact_metadata(
    connection: psycopg.Connection[tuple[object, ...]],
    registration: SourceRegistrationAccepted,
    policy,
) -> None:
    record = registration.source_record
    payload = canonical_bytes(record, policy)
    connection.execute(
        """
        INSERT INTO gptl_source_artifacts (
            source_artifact_id, source_logical_id, source_version_id,
            source_version_number, source_content_hash, raw_byte_hash,
            byte_length, media_type, source_class_id, parser_status,
            payload_hash, payload, record_type, schema_version, hash_algorithm
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        """,
        (
            record.source_artifact_id,
            record.source_ref.logical_id,
            record.source_ref.version_id,
            record.source_ref.version_number,
            record.source_ref.content_hash,
            record.raw_byte_hash,
            record.byte_length,
            record.media_type,
            record.source_class_id,
            record.parser_eligibility.status,
            hashlib.sha256(payload).hexdigest(),
            payload,
            record.record_type,
            record.schema_version,
            record.hash_algorithm,
        ),
    )


def _insert_source_raw_bytes(
    connection: psycopg.Connection[tuple[object, ...]],
    registration: SourceRegistrationAccepted,
    *,
    raw_byte_hash: str,
    byte_length: int,
    raw_bytes: bytes,
) -> None:
    connection.execute(
        """
        INSERT INTO gptl_source_raw_bytes (
            source_artifact_id, raw_byte_hash, byte_length, raw_bytes,
            record_type, schema_version, hash_algorithm
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            registration.source_record.source_artifact_id,
            raw_byte_hash,
            byte_length,
            raw_bytes,
            "SOURCE_RAW_BYTES",
            "gptl.build1.source-artifact.v1",
            "SHA-256",
        ),
    )
