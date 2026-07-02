# GPTL Build 1 Slice 2 Oracle Review Packet

## Review Target

Review **Build 1 Slice 2 — Source Registration** at commit:

```text
98c482ada6d95cdb17de55ecedabff7c888f87d4
```

Latest relevant commits:

```text
98c482a Harden Build 1 source registration integrity
5f69857 Implement Build 1 source registration slice
41a9359 Harden Build 1 capability review edges
b1f4b79 Close Build 1 capability review gaps
bbf8f50 Implement Build 1 capability scope slice
```

Repository state when this packet was prepared:

```text
main...origin/main
```

Known untracked files at preparation time are unrelated Build 1 Oracle plan artifacts:

```text
docs/GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.2_FINDINGS.md
docs/GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.2_REVISED_DRAFT.md
docs/GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.2_polished.docx
```

## Requested Oracle Task

Review Build 1 Slice 2 for correctness, safety, determinism, replayability, and conformance to the approved Build 1 plan.

Classify findings as:

```text
BLOCKER / MAJOR / MINOR / NIT
```

Focus especially on:

1. Raw-byte preservation and exact SHA-256 hashing.
2. Streaming max-byte enforcement before full buffering.
3. Capability-profile and source-class gating.
4. Parser eligibility state invariants.
5. PostgreSQL atomicity and append-only behavior.
6. Artifact/raw-bytes 1:1 integrity, including migration `0007`.
7. Replayability and separation of canonical source-record `content_hash` from raw-byte `raw_byte_hash`.
8. Hidden hardcoded policy, magic numbers, hardcoded paths, SQLite/vector/embedding/similarity leakage, fabricated confidence, or application defaults.

Do **not** propose architecture outside the approved Build 1 plan unless an actual defect requires it.

## Standing Build Constraints

The implementation inherits the Build 0 and Build 1 constraints:

- PostgreSQL only. No SQLite runtime or test fallback.
- No FAISS, embeddings, vector store, nearest-neighbor lookup, or model authority.
- No hardcoded domain policy.
- No magic numbers. Numeric bounds are governed policy values or named structural constants.
- Fail closed on missing, unsupported, wrong-scope, ambiguous, stale, unauthorized, non-canonical, or tampered input.
- No raw source artifact is overwritten by parsed or normalized values.
- No unratified parser output enters Tier 1.
- Every governed Build 1 record binds the relevant canonicalization policy.
- Source bytes and source record commit atomically in PostgreSQL.
- Tests run locally. No CI or deployment automation is part of this build.

## Slice 2 Governing Contract

From `docs/GPTL_BUILD1_PLAN_v0.7.md`, Slice 2 is:

```text
## 5. Slice 2 — Source Registration

Goal:
Register raw artifacts before any extraction or proposal occurs.

SourceArtifactRecord captures:
- Source artifact ID, logical ID, version ID, schema version, lifecycle state.
- version_number, content hash, and bound CanonicalizationPolicy reference.
- Raw payload bytes stored in PostgreSQL and raw_byte_hash, the SHA-256 hash of the exact received bytes.
- content_hash, the canonical hash of the source record metadata, distinct from raw_byte_hash.
- Byte length, media type, and optional filename as metadata outside the raw-byte hash.
- Submitted filename or external identifier as non-authoritative metadata.
- Source class and claimed origin.
- Submitter, received time, asserted source time when available.
- Evidence scope and capability-profile reference.
- Parser eligibility state: UNPARSED, PARSER_UNAVAILABLE, PARSER_UNSUPPORTED, PARSER_READY, PARSER_FAILED.

Build 1 source registration is one PostgreSQL transaction:
- resolve the source class against the bound capability profile and SourceStoragePolicy,
- stream the payload while enforcing the governed max-byte limit,
- insert the source record, raw bytes, hash metadata, audit event, and any parser-eligibility record together,
- verify the stored bytes against raw_byte_hash before commit visibility.

A failure commits neither row nor bytes.

The implementation must reject over-limit payloads before the full payload is buffered in application memory.

Raw source bytes are not canonicalized before hashing.
Newline normalization, text decoding, OCR, and parser cleanup produce separate parse-attempt/proposal records that cite the raw artifact.

Parser eligibility records bind applicable AlgorithmRegistryEntry references for decoders/parsers when a deterministic parser path exists.
PARSER_UNAVAILABLE, PARSER_UNSUPPORTED, and PARSER_FAILED are recorded source states; they do not create inferred negative evidence or authority.
```

Slice 2 exit gate:

```text
- Identical bytes produce identical raw_byte_hash.
- Different metadata over identical bytes does not change raw_byte_hash but does change source-record content_hash.
- Text and binary artifacts are hashed as exact bytes received, not as canonicalized text.
- Over-limit payloads fail before raw bytes or metadata become visible.
- A parsed/proposed record cannot exist without a registered raw source.
- Unsupported source class becomes explicit advisory gap.
- Failed parser does not mutate or delete the source artifact.
- Parser status binds the algorithm registry entry or the governed reason no parser was eligible.
- Raw source registration is append-only and replayable.
```

## Files In Scope

Implementation:

```text
src/gptl/core/source_artifacts.py
src/gptl/core/persistence.py
src/gptl/core/migrations/0005_build1_capability_scope.sql
src/gptl/core/migrations/0006_build1_sources.sql
src/gptl/core/migrations/0007_build1_source_integrity.sql
```

Tests:

```text
tests/build1/test_slice_02_source_registration.py
tests/conformance/test_migrations.py
tests/slices/test_slice_01_safe_refusal.py
```

Build 1 Slice 1 dependency:

```text
src/gptl/core/capabilities.py
src/gptl/core/scope.py
tests/build1/test_slice_01_capability_profile.py
```

## Verification Result

Last full verification before this packet:

```text
uv run pytest -q
352 passed in 39.16s

uv run ruff check src tests scripts
All checks passed.

uv run mypy src
Success: no issues found in 40 source files

git diff --check
clean
```

Policy scans:

```text
rg -n "faiss|pgvector|Pinecone|Weaviate|Chroma|embedding|nearest[-_ ]neighbor|similarity|sqlite|sqlite3" src tests/build1
no hits

rg -n "TODO|FIXME|HACK|magic number|temporary" src/gptl/core src/gptl/mie tests/build1
no hits
```

## Implementation Summary

Slice 2 introduces:

- `SourceArtifactRegistrationRequest`
- `SourceArtifactRecord`
- `ParserEligibility`
- `SourceRegistrationAccepted`
- `SourceRegistrationRejected`
- `SourcePayloadTooLarge`
- raw-byte hashing over exact received bytes
- streaming governed max-byte enforcement
- content hash over canonical source metadata, excluding the embedded self-ref `content_hash`
- PostgreSQL source artifact and raw-byte persistence
- deferred DB validation that every artifact has exactly one raw-byte row
- loud load-time integrity failures for missing/tampered raw bytes

## Core Contract Excerpts

### Source Artifact Constants and Parser Eligibility

From `src/gptl/core/source_artifacts.py`:

```python
SOURCE_ARTIFACT_SCHEMA_VERSION: Final = "gptl.build1.source-artifact.v1"
SOURCE_ARTIFACT_RECORD_TYPE: Final = "SOURCE_ARTIFACT"
SOURCE_RAW_BYTES_RECORD_TYPE: Final = "SOURCE_RAW_BYTES"
SOURCE_REGISTRATION_ACCEPTED_REASON_ID: Final = TermId("build1.source.registration-accepted")
SOURCE_PAYLOAD_TOO_LARGE_REASON_ID: Final = TermId("build1.source.payload-too-large")
HASH_ALGORITHM: Final = "SHA-256"
SOURCE_STREAM_CHUNK_BYTES: Final = io.DEFAULT_BUFFER_SIZE
OVER_LIMIT_PROBE_BYTES: Final = 1

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
```

### Source Artifact Records

```python
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
```

### Raw-Byte Hashing and Streaming Limit

```python
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
```

Review point: `max_bytes_per_source_record` comes from `SourceStoragePolicy`, not from a hidden constant. The named `OVER_LIMIT_PROBE_BYTES` detects the first byte over the governed limit without reading the full stream.

### Registration Preparation

```python
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
```

### Source Record Content Hash vs Raw Byte Hash

```python
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
```

Review point: `raw_byte_hash` is SHA-256 over exact received bytes. `content_hash` is canonical metadata hash of `SourceArtifactRecord`, excluding the embedded self-ref `content_hash`.

## Persistence Excerpts

From `src/gptl/core/persistence.py`.

### Stored Source Artifact

```python
@dataclass(frozen=True)
class StoredSourceArtifact:
    source_artifact_id: str
    source_logical_id: str
    source_version_id: str
    raw_byte_hash: str
    byte_length: int
    parser_status: str
    payload: bytes
    raw_bytes: bytes
```

### Persist Source Registration

```python
def persist_source_registration(self, registration: SourceRegistrationAccepted) -> None:
    record = registration.source_record
    payload = canonical_bytes(record, self._policy)
    payload_hash = hashlib.sha256(payload).hexdigest()
    with psycopg.connect(self._database_url) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                self._pin_search_path(cursor)
                cursor.execute(
                    """
                    INSERT INTO gptl_source_artifacts (
                        source_artifact_id, source_logical_id, source_version_id,
                        source_version_number, source_content_hash, raw_byte_hash,
                        byte_length, media_type, source_class_id, parser_status,
                        payload_hash, payload, record_type, schema_version,
                        hash_algorithm
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
                        payload_hash,
                        payload,
                        SOURCE_ARTIFACT_RECORD_TYPE,
                        SOURCE_ARTIFACT_SCHEMA_VERSION,
                        SOURCE_HASH_ALGORITHM,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO gptl_source_raw_bytes (
                        source_artifact_id, raw_byte_hash, byte_length, raw_bytes,
                        record_type, schema_version, hash_algorithm
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.source_artifact_id,
                        record.raw_byte_hash,
                        record.byte_length,
                        registration.raw_bytes,
                        SOURCE_RAW_BYTES_RECORD_TYPE,
                        SOURCE_ARTIFACT_SCHEMA_VERSION,
                        SOURCE_HASH_ALGORITHM,
                    ),
                )
                cursor.execute(
                    """
                    SELECT raw_bytes, raw_byte_hash, byte_length
                    FROM gptl_source_raw_bytes
                    WHERE source_artifact_id = %s
                    """,
                    (record.source_artifact_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise PersistenceIntegrityError("source raw bytes were not persisted")
                stored_raw_bytes = bytes(row[0])
                if (
                    hashlib.sha256(stored_raw_bytes).hexdigest() != row[1].strip()
                    or row[1].strip() != record.raw_byte_hash
                    or row[2] != len(stored_raw_bytes)
                ):
                    raise PersistenceIntegrityError("source raw byte verification failed")
                verify_source_registration(registration, self._policy)
```

### Load Source Artifact

```python
def load_source_artifact(self, source_artifact_id: str) -> StoredSourceArtifact | None:
    with psycopg.connect(self._database_url) as connection:
        with connection.cursor() as cursor:
            self._pin_search_path(cursor)
            cursor.execute(
                """
                SELECT
                    source.source_artifact_id,
                    source.source_logical_id,
                    source.source_version_id,
                    source.raw_byte_hash,
                    source.byte_length,
                    source.parser_status,
                    source.payload,
                    source.payload_hash,
                    source.record_type,
                    source.schema_version,
                    source.hash_algorithm,
                    raw.raw_bytes,
                    raw.raw_byte_hash,
                    raw.byte_length,
                    raw.record_type,
                    raw.schema_version,
                    raw.hash_algorithm
                FROM gptl_source_artifacts AS source
                LEFT JOIN gptl_source_raw_bytes AS raw
                    ON raw.source_artifact_id = source.source_artifact_id
                WHERE source.source_artifact_id = %s
                """,
                (source_artifact_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            if row[11] is None:
                raise PersistenceIntegrityError("source artifact raw bytes are missing")
            typed_row = cast(...)
            self._validate_record_metadata(...)
            payload = bytes(typed_row[6])
            raw_bytes = bytes(typed_row[11])
            verify_sha256(payload, typed_row[7].strip())
            verify_sha256(raw_bytes, typed_row[12].strip())
            if (
                typed_row[3].strip() != typed_row[12].strip()
                or typed_row[4] != typed_row[13]
                or typed_row[13] != len(raw_bytes)
            ):
                raise PersistenceIntegrityError("source artifact row is inconsistent")
            return StoredSourceArtifact(...)
```

Review point: loader uses `LEFT JOIN` and explicitly raises on artifact metadata without raw bytes. It does not silently return `None` for corrupt/orphan metadata.

## Migrations

### `0005_build1_capability_scope.sql`

```sql
-- Slice 1 introduced governed capability/scope contracts without a persisted
-- relation. This migration preserves the owner-ratified Build 1 ordinal map so
-- later source/proposal migrations do not renumber after publication.
SELECT 1;
```

### `0006_build1_sources.sql`

```sql
CREATE TABLE gptl_source_artifacts (
    source_artifact_id text PRIMARY KEY,
    source_logical_id text NOT NULL,
    source_version_id text NOT NULL,
    source_version_number integer NOT NULL CHECK (source_version_number >= 0),
    source_content_hash char(64) NOT NULL CHECK (source_content_hash ~ '^[0-9a-f]{64}$'),
    raw_byte_hash char(64) NOT NULL CHECK (raw_byte_hash ~ '^[0-9a-f]{64}$'),
    byte_length bigint NOT NULL CHECK (byte_length >= 0),
    media_type text NOT NULL,
    source_class_id text NOT NULL,
    parser_status text NOT NULL CHECK (
        parser_status IN (
            'UNPARSED',
            'PARSER_UNAVAILABLE',
            'PARSER_UNSUPPORTED',
            'PARSER_READY',
            'PARSER_FAILED'
        )
    ),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    record_type text NOT NULL CHECK (record_type = 'SOURCE_ARTIFACT'),
    schema_version text NOT NULL CHECK (schema_version = 'gptl.build1.source-artifact.v1'),
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256'),
    UNIQUE (source_logical_id, source_version_id)
);

CREATE TABLE gptl_source_raw_bytes (
    source_artifact_id text PRIMARY KEY REFERENCES gptl_source_artifacts(source_artifact_id),
    raw_byte_hash char(64) NOT NULL CHECK (raw_byte_hash ~ '^[0-9a-f]{64}$'),
    byte_length bigint NOT NULL CHECK (byte_length >= 0),
    raw_bytes bytea NOT NULL,
    record_type text NOT NULL CHECK (record_type = 'SOURCE_RAW_BYTES'),
    schema_version text NOT NULL CHECK (schema_version = 'gptl.build1.source-artifact.v1'),
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256')
);

CREATE TRIGGER gptl_source_artifacts_append_only
BEFORE UPDATE OR DELETE ON gptl_source_artifacts
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_source_raw_bytes_append_only
BEFORE UPDATE OR DELETE ON gptl_source_raw_bytes
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_source_artifacts_reject_truncate
BEFORE TRUNCATE ON gptl_source_artifacts
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_source_raw_bytes_reject_truncate
BEFORE TRUNCATE ON gptl_source_raw_bytes
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();
```

### `0007_build1_source_integrity.sql`

```sql
CREATE FUNCTION gptl_validate_source_raw_byte_pair() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
DECLARE
    artifact_count bigint;
    raw_count bigint;
BEGIN
    SELECT count(*) INTO artifact_count
    FROM gptl_source_artifacts
    WHERE source_artifact_id = NEW.source_artifact_id;

    SELECT count(*) INTO raw_count
    FROM gptl_source_raw_bytes
    WHERE source_artifact_id = NEW.source_artifact_id;

    IF artifact_count <> 1 OR raw_count <> 1 THEN
        RAISE EXCEPTION 'GPTL source artifact raw byte pair is incomplete';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM gptl_source_artifacts AS artifact
        JOIN gptl_source_raw_bytes AS raw
            ON raw.source_artifact_id = artifact.source_artifact_id
        WHERE artifact.source_artifact_id = NEW.source_artifact_id
            AND (
                artifact.raw_byte_hash <> raw.raw_byte_hash
                OR artifact.byte_length <> raw.byte_length
                OR raw.byte_length <> octet_length(raw.raw_bytes)
            )
    ) THEN
        RAISE EXCEPTION 'GPTL source artifact raw byte metadata mismatch';
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER gptl_source_artifacts_validate_raw_byte_pair
AFTER INSERT ON gptl_source_artifacts
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_source_raw_byte_pair();

CREATE CONSTRAINT TRIGGER gptl_source_raw_bytes_validate_pair
AFTER INSERT ON gptl_source_raw_bytes
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_source_raw_byte_pair();
```

Review point: `0007` was added as a forward-only hardening migration after review identified that `0006` had app-enforced atomicity but not DB-defended 1:1 artifact/raw-byte integrity. Published migrations are immutable, so `0006` was not edited.

## Test Coverage Map

From `tests/build1/test_slice_02_source_registration.py`.

### Raw Byte Hashing

```python
def test_identical_bytes_produce_identical_raw_hash() -> None
def test_metadata_changes_content_hash_not_raw_hash(...)
def test_text_and_binary_artifacts_are_hashed_as_exact_received_bytes(...)
```

Coverage:

- identical bytes produce identical `raw_byte_hash`
- metadata changes do not change `raw_byte_hash`
- metadata changes do change source-record `content_hash`
- LF and CRLF text bytes hash differently
- binary bytes hash as exact received bytes

### Streaming Limit Enforcement

```python
def test_over_limit_payload_fails_before_full_buffer_read(...):
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
```

Coverage:

- over-limit payload rejected after `max + 1`
- stream is not fully read
- max comes from the governed source storage policy fixture

### Capability Source-Class Gating

```python
def test_unsupported_source_class_returns_governed_capture_gap(...):
    result = _prepare_registration(
        build1_ref_factory,
        source_class_id=TermId("source-class.vendor-binary"),
    )

    assert isinstance(result, SourceRegistrationRejected)
    assert result.capture_result.capability_failure is not None
    assert result.capture_result.capability_failure.status == "UNSUPPORTED"
```

Coverage:

- unsupported source class does not produce source artifact
- rejection is governed through capability profile result

### Parser Eligibility

```python
def test_parser_eligibility_state_is_deterministic_and_replayable(...)
def test_parser_eligibility_requires_algorithm_or_reason_by_state(...)
```

Coverage:

- parser refs sort deterministically
- `PARSER_READY` requires algorithms and no reason
- `PARSER_FAILED` requires algorithms and reason
- `PARSER_UNAVAILABLE` / `PARSER_UNSUPPORTED` require reason and no algorithms
- `UNPARSED` carries neither algorithms nor reason

### Postgres Persistence and Atomicity

```python
def test_raw_bytes_round_trip_exactly_from_postgres(...)
def test_failed_source_registration_leaves_no_rows_or_raw_bytes(...)
def test_database_rejects_source_artifact_without_raw_bytes(...)
def test_database_rejects_source_raw_byte_metadata_mismatch(...)
def test_load_source_artifact_fails_loud_for_historical_orphan_metadata(...)
def test_load_source_artifact_fails_loud_for_tampered_raw_bytes(...)
```

Coverage:

- raw bytes round-trip exactly
- persisted canonical payload matches source record
- failed registration leaves zero artifact rows and zero raw-byte rows
- DB rejects source artifact row without matching raw-byte row
- DB rejects raw-byte metadata mismatch
- historical/corrupt orphan metadata fails loud at load
- tampered raw bytes fail loud at load

## Migration Conformance

`tests/conformance/test_migrations.py` pins migration hashes:

```python
PUBLISHED_MIGRATION_SHA256 = {
    "0001_slice_1.sql": "6e8ef39c2a75c2d1b8b5c1d3887af5d8158a7845b3647444c3c85da235b7cdf9",
    "0002_persistence_invariants.sql": "d613491e11bcfb65915636e59c198c9c9bb1834b57bcf2b9f093aaffc05f9799",
    "0003_snapshot_bound_runs.sql": "6d0a4fcf74c0699285249a6e7b713c8f77d39c343e32c3f977ecaa114b08ae86",
    "0004_replay_capsules.sql": "a21fb28046652ce2e40d3b0de9836bb758d2f85839e8ed766b4dee43bb825ad0",
    "0005_build1_capability_scope.sql": "3cdb13ca80d88f7e089517a63645d6484391f57f85469bdc2b13b1cdedca2af2",
    "0006_build1_sources.sql": "55dc0616e780e5a4a8b61f121d369a5d28dd50dfe52ca2fe840ac6b822562bdd",
    "0007_build1_source_integrity.sql": "2244e9204718c985d7462f65cf0d377f1ff3aefed052281731b857bc17e654a7",
}
```

`tests/slices/test_slice_01_safe_refusal.py` checks migration ordering/idempotence includes:

```text
0001_slice_1
0002_persistence_invariants
0003_snapshot_bound_runs
0004_replay_capsules
0005_build1_capability_scope
0006_build1_sources
0007_build1_source_integrity
```

## Known Deliberate Design Choices

1. `0005_build1_capability_scope.sql` is `SELECT 1;` by design. Slice 1 introduced governed capability/scope contracts in code but no persisted relation. The migration preserves the owner-ratified Build 1 ordinal map so later migrations do not need renumbering.

2. `SOURCE_STREAM_CHUNK_BYTES = io.DEFAULT_BUFFER_SIZE` and `OVER_LIMIT_PROBE_BYTES = 1` are named structural I/O constants, not domain policy. The domain limit is `SourceStoragePolicy.max_bytes_per_source_record`.

3. Raw bytes are never canonicalized. Metadata is canonicalized for `SourceArtifactRecord.content_hash`; exact received bytes are hashed separately as `raw_byte_hash`.

4. Parser states are recorded source states. Parser failure or unsupported parser does not mutate/delete the raw artifact and does not create negative evidence.

5. The source/raw-byte DB hardening was added as forward-only migration `0007`, not by editing published migration `0006`.

## Specific Questions For Oracle

Please answer:

1. Does the implementation fully satisfy Slice 2’s raw source registration contract?
2. Does `read_raw_payload_with_limit` reject over-limit streams without full buffering in all boundary cases?
3. Is `SourceArtifactRecord.content_hash` properly separated from `raw_byte_hash`?
4. Are parser eligibility state invariants complete and contradiction-free?
5. Is capability/source-class gating correct and fail-closed?
6. Do migrations `0006` and `0007` provide sufficient DB-level append-only and artifact/raw-byte integrity?
7. Does `load_source_artifact` fail loudly for corrupt persisted source state?
8. Is any hidden policy, hardcoded domain assumption, magic number, path dependency, SQLite/vector/similarity leakage, model authority, or fabricated confidence present?
9. Are tests sufficient for Slice 2 closeout, or should any additional fixtures be added before Slice 3?

Return findings in this shape:

```text
Verdict: CLOSEABLE / CLOSEABLE WITH MINOR FIXES / NOT CLOSEABLE

Findings:
- [SEVERITY] [ID] [file/path:line or section] Title
  Evidence:
  Impact:
  Recommended fix:

Residual risk:

Suggested next step:
```
