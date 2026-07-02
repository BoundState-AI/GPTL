# GPTL Build 1 Slice 2 Oracle Closeout Packet v0.1

## Review Target

Review the Slice 2 closeout at commit:

```text
d212bf0953d2fa5dbd36a8206e6b3bb4a2ce67a7
```

Commit summary:

```text
d212bf0 Close Slice 2 Oracle implementation gaps
```

This closeout supersedes the stale pre-fix packet:

```text
docs/GPTL_BUILD1_SLICE2_ORACLE_REVIEW_PACKET.md
```

That packet targeted commit `98c482ada6d95cdb17de55ecedabff7c888f87d4` and quoted the old implementation.

## Requested Oracle Task

Review whether commit `d212bf0953d2fa5dbd36a8206e6b3bb4a2ce67a7` closes the accepted implementation findings from the real Slice 2 Oracle review:

```text
C:\Users\Jnwil\Downloads\report (24).md
C:\Users\Jnwil\Downloads\metrics (23).json
C:\Users\Jnwil\Downloads\docx (32).docx
```

Classify any remaining findings as:

```text
BLOCKER / MAJOR / MINOR / NIT
```

Do not re-propose rejected architecture unless an actual remaining defect requires it.

Rejected or deferred scope remains rejected/deferred:

- No SQLite.
- No FAISS, embeddings, vector stores, similarity search, or model authority.
- No external blob/temp-file redesign for Slice 2.
- No concurrency/backpressure architecture expansion for Slice 2.
- No pgcrypto dependency unless the owner explicitly chooses DB-side SHA-256 enforcement.
- Parser lifecycle semantics for registration-time `PARSER_FAILED` remain an owner/product decision.

## Files Changed

Implementation:

```text
src/gptl/core/source_artifacts.py
src/gptl/core/persistence.py
src/gptl/core/migrations/0008_build1_source_registration_audit.sql
```

Tests:

```text
tests/build1/test_slice_02_source_registration.py
tests/conformance/test_migrations.py
tests/slices/test_slice_01_safe_refusal.py
```

## Closeout Map

### R1-001 / R2-002: Governance Refs And Ambient Policy Binding

Status: fixed.

Changes:

- `SourceArtifactRegistrationRequest` no longer accepts caller-asserted parser eligibility.
- Requests now bind `parser_eligibility_policy_ref`.
- `prepare_source_registration(...)` validates these actual gate inputs before registration:
  - capability profile ref,
  - evidence scope ref,
  - parser eligibility policy ref,
  - canonicalization policy ref.
- `PostgresRunStore` now accepts a governed canonicalization `policy_ref` for source persistence.
- Source persistence fails closed if the record's `canonicalization_policy_ref` does not match the store's governed policy ref.
- Source load parses canonical payloads and validates persisted query columns against the payload.

Regression coverage:

```text
test_registration_governance_refs_must_bind_to_actual_gate_inputs
test_load_source_artifact_fails_loud_for_query_column_payload_mismatch
```

### R1-002 / R2-006: Parser Eligibility Is Governed, Not Caller Asserted

Status: fixed for Slice 2 mechanics.

Changes:

- Added `ParserEligibilityPolicy`.
- Added deterministic `ParserEligibilityRule` sorting and uniqueness validation.
- Added `govern_parser_eligibility(...)`.
- Unknown `(source_class_id, media_type)` combinations fail closed with `CONFIGURATION_INVALID`.

Regression coverage:

```text
test_parser_eligibility_is_derived_from_governed_policy
test_missing_parser_eligibility_rule_fails_closed
```

Remaining owner/domain work:

- Production parser policy contents are a governed domain artifact, not a hardcoded code default.

### R1-003 / R2-001: Atomic Registration Audit Event

Status: fixed.

Changes:

- Added `SourceRegistrationAuditEvent`.
- `SourceRegistrationAccepted` now includes the audit event.
- Added migration `0008_build1_source_registration_audit.sql`.
- Added `gptl_source_registration_audit_events`.
- Added deferred source/audit count triggers.
- `persist_source_registration(...)` inserts source metadata, raw bytes, and audit event in one transaction.
- `load_source_artifact(...)` fails loud if the audit event is missing.

Regression coverage:

```text
test_raw_bytes_round_trip_exactly_from_postgres
test_failed_source_registration_leaves_no_rows_or_raw_bytes
test_database_rejects_source_artifact_without_audit_event
```

### R1-004: Accepted Payload Buffering Scope

Status: clarified, not redesigned.

The implemented safety requirement is:

```text
Over-limit payloads fail before the full payload is buffered in application memory.
```

That remains true. In-limit accepted payloads are still held in memory as bounded raw bytes for hashing and insertion. Oracle rejected the external blob/temp-file redesign; this closeout does not introduce one.

Regression coverage:

```text
test_over_limit_payload_fails_before_full_buffer_read
```

### R1-005 / R2-005: RawByteStream `read(n)` Contract

Status: fixed.

Changes:

- `read_raw_payload_with_limit(...)` now detects streams that return more than the requested byte count.
- Non-conforming streams return a typed `SourceStreamContractViolation` result instead of falling into generic failure.

Regression coverage:

```text
test_nonconforming_stream_is_a_typed_fail_closed_result
```

### R1-006 / R2-004: Load-Time Column/Payload Validation

Status: fixed.

Changes:

- Source load now validates:
  - source table metadata,
  - raw-byte table metadata,
  - audit table metadata,
  - payload SHA-256,
  - raw byte SHA-256,
  - audit payload SHA-256,
  - queryable source columns against `SourceArtifactRecord`,
  - audit columns against `SourceRegistrationAuditEvent`,
  - source/audit/raw cross-consistency through `verify_source_registration(...)`.

Regression coverage:

```text
test_load_source_artifact_fails_loud_for_historical_orphan_metadata
test_load_source_artifact_fails_loud_for_tampered_raw_bytes
test_load_source_artifact_fails_loud_for_query_column_payload_mismatch
```

### R1-007: DB-Side SHA-256 / pgcrypto

Status: owner decision remains deferred.

The current boundary is:

- PostgreSQL stores payload/raw/audit bytes append-only.
- Python computes and verifies SHA-256 deterministically.
- Load fails loud on mismatched bytes or duplicated metadata.
- No pgcrypto dependency has been introduced.

If the owner wants commit-time database hashing, that should be a separate explicit dependency decision.

### R2-003: Registration-Time `PARSER_FAILED`

Status: unresolved owner/product decision.

The implementation still permits `PARSER_FAILED` as a parser eligibility state because the approved Slice 2 plan includes it. This closeout does not reinterpret lifecycle semantics.

### Additional Guard: Registration Audit Reason

Status: fixed.

`verify_source_registration(...)` now pins both the accepted result reason and audit event reason to:

```text
build1.source.registration-accepted
```

Regression coverage:

```text
test_registration_audit_reason_is_pinned_to_accepted_reason
```

## Migration Evidence

New migration:

```text
src/gptl/core/migrations/0008_build1_source_registration_audit.sql
```

Pinned checksum:

```text
9902a715d3af0279a733c36d860b50deb86ca42a2a06be4c48feb9cd627c4ec7
```

Migration-order and checksum tests were updated in:

```text
tests/conformance/test_migrations.py
tests/slices/test_slice_01_safe_refusal.py
```

## Verification

Focused regression suite:

```text
uv run pytest tests/build1/test_slice_02_source_registration.py -q
25 passed
```

Full verification:

```text
uv run pytest -q
362 passed in 36.49s

uv run ruff check src tests scripts
All checks passed.

uv run mypy src
Success: no issues found in 40 source files

git diff --check
clean
```

## Standing Constraints Rechecked By Design

- PostgreSQL only.
- No SQLite fallback.
- No vector search, FAISS, embeddings, similarity search, or model authority.
- No hardcoded parser eligibility defaults in source registration.
- No ungoverned source registration gate.
- Raw bytes are hashed exactly as received.
- Parsed/normalized output remains outside Slice 2 source registration.
- Source metadata, raw bytes, and audit event are append-only durable rows.
- Missing raw bytes, missing audit events, tampered bytes, and duplicated-column drift fail loud.
