# GPTL Build 1 Slice 2 Owner Closeout v0.2

## Status

Slice 2 is closed for Build 1 progression.

This document records the owner decisions and implementation fixes made after the
single-round Oracle review of:

```text
docs/GPTL_BUILD1_SLICE2_ORACLE_CLOSEOUT_PACKET_v0.1.md
```

The closeout implementation target is:

```text
f078dcc46ebebbb436524c808af8481d4decbb5f
Resolve Slice 2 closeout owner calls
```

No additional Oracle pass is required before moving to Build 1 Slice 3.

## Latest Oracle Review Summary

Oracle reviewed the Slice 2 v0.1 closeout packet in one round and reported:

```text
Accepted critical defects: 0
Accepted high defects: 1
Total accepted defects: 4
Consensus: BLOCKED / not converged
```

The non-convergence was not treated as a request for another review loop. It was
caused by owner/domain questions that needed direct decisions:

1. Whether pre-`0008` source rows must be migrated or explicitly blocked.
2. Whether source loading uses each record's historical canonicalization policy.
3. What "bounded accepted payload" means without introducing a magic global size.
4. What Slice 2 promises about registration-time `PARSER_FAILED`.

## Owner Decisions

### 1. Pre-`0008` Upgrade Path

Decision:

Slice 2 source data is greenfield unless an explicit source-audit backfill is designed.

Rationale:

`0008` introduced required source registration audit events. A database containing
source rows written before `0008` cannot prove the new atomic audit invariant without
a deliberate backfill. Silently allowing those rows through would create exactly the
unloadable historical state Oracle flagged.

Implementation:

```text
src/gptl/core/migrations/0009_build1_source_registration_greenfield_guard.sql
```

`0009` fails migration if any source artifact lacks a registration audit event.
That preserves migration immutability for `0008` while making the upgrade precondition
executable.

Regression coverage:

```text
test_pre_0008_source_rows_require_explicit_backfill
```

### 2. Historical Canonicalization Policy Loading

Decision:

Source loading resolves the canonicalization policy from the record's own governed
`canonicalization_policy_ref`, not from a single global current policy.

Rationale:

Append-only historical records must remain loadable after a future policy version is
introduced. A store-level "current policy only" check would make valid old rows fail
for the wrong reason.

Implementation:

`PostgresRunStore` now accepts a source policy registry:

```python
PostgresRunStore(
    database_url,
    current_policy,
    current_policy_ref,
    source_policy_registry={historical_policy_ref: historical_policy},
)
```

On source load, the store extracts `canonicalization_policy_ref` from the canonical
payload, resolves that exact policy from the registry, then validates the full source
record and audit event with that policy.

If the historical policy is not registered, load fails loud.

Regression coverage:

```text
test_source_load_resolves_historical_record_policy_ref
```

### 3. Accepted Payload Bound

Decision:

There is no global accepted payload size constant in generic code.

The accepted byte limit is the governed per-source-class value:

```text
SourceStoragePolicy.max_bytes_per_source_record
```

Rationale:

A single product-wide number would be a hidden domain default. Different source classes
can have different governed storage policies. Slice 2's invariant is that the selected
governed limit is enforced while reading, before an over-limit payload is fully buffered.

Fixture values are test data, not production defaults:

```text
tests/build1/test_slice_02_source_registration.py: DEFAULT_MAX_SOURCE_BYTES = 16
tests/build1/test_slice_01_capability_profile.py: TEST_REPORT_MAX_SOURCE_BYTES = 1024
tests/build1/test_slice_01_capability_profile.py: MANUAL_UPLOAD_MAX_SOURCE_BYTES = 2048
```

Regression coverage:

```text
test_over_limit_payload_fails_before_full_buffer_read
```

### 4. Registration-Time `PARSER_FAILED`

Decision:

`PARSER_FAILED` remains representable because the approved Build 1 plan includes it,
but Slice 2 does not assign downstream lifecycle semantics to it.

Rationale:

Slice 2 registers sources and governed parser eligibility. Parser execution and parser
attempt lifecycle belong to the next parser/parse-attempt slice. `PARSER_FAILED` creates
no negative evidence and grants no Tier 1 authority in Slice 2.

Follow-on requirement:

Slice 3 must decide whether parser failures are represented as source eligibility state,
parse-attempt records, or both, with exact retry/retention/downstream behavior.

## Packet-Level Fixes

The Oracle review also found packet-level defects. They are resolved here rather than
through another Oracle round.

### Local-File Baseline

The v0.1 packet referenced local Windows download paths. This closeout treats the
in-repo closeout map and this owner decision file as the authoritative audit baseline.

### Severity Taxonomy

The review schema mapping is:

```text
BLOCKER -> critical
MAJOR   -> high
MINOR   -> medium
NIT     -> low
```

### Claimed Status Framing

Future review packets should say `claimed fixed`, `claimed clarified`, or
`claimed deferred` when presenting implementation status for external review.

## Files Changed By The Owner Closeout

Implementation:

```text
src/gptl/core/persistence.py
src/gptl/core/migrations/0009_build1_source_registration_greenfield_guard.sql
```

Tests:

```text
tests/build1/test_slice_02_source_registration.py
tests/conformance/test_migrations.py
tests/slices/test_slice_01_safe_refusal.py
```

Documentation:

```text
docs/GPTL_BUILD1_SLICE2_OWNER_CLOSEOUT_v0.2.md
```

## Verification

Focused verification:

```text
uv run pytest tests/build1/test_slice_02_source_registration.py \
  tests/conformance/test_migrations.py \
  tests/slices/test_slice_01_safe_refusal.py::test_migrations_are_ordered_checksummed_and_idempotent -q

32 passed in 3.49s
```

Full verification:

```text
uv run pytest -q
364 passed in 38.12s

uv run ruff check src tests scripts
All checks passed.

uv run mypy src
Success: no issues found in 40 source files

git diff --check
clean
```

## Move-On Criteria

Slice 2 can be treated as closed because:

- Oracle accepted zero critical implementation defects.
- The one high material concern was resolved in code by historical policy lookup.
- The pre-`0008` trap was resolved in migration behavior by a greenfield/backfill guard.
- Payload bounds remain governed policy, not a hardcoded default.
- `PARSER_FAILED` is explicitly deferred to parser-attempt lifecycle design.
- Full local verification is green.

Build 1 may proceed to Slice 3.
