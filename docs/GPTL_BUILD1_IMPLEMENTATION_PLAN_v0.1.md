# GPTL Build 1 Implementation Plan
## Capability-Profiled Capture and Ratified Evidence

**Version:** v0.1
**Status:** implementation plan
**Build basis:** `GPTL_BUILD1_PLAN_v0.7.md` and `GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.7.md`
**Governing baseline:** GPTL MIE Build 0 freeze, frozen Build 0 tests, and the v0.4.20 platform specification embedded in the v0.7 ORACLE bundle

---

## 1. Decision

Build 1 is ready to implement from the v0.7 plan. This plan does not reopen the architecture. It converts the approved Build 1 contract into ordered implementation slices, file targets, migrations, tests, and release gates.

Build 1 remains on the original GPTL path:

- Register real source artifacts and preserve exact bytes.
- Convert source-backed material into typed proposals, not facts.
- Require explicit human ratification before any value becomes Tier 1 decision-effective.
- Keep attributed observations as Tier-2-only context until promoted through governed validation and ratification.
- Bridge only ratified, scope-compatible, policy-compatible values into the frozen Build 0 MIE engine.
- Preserve replay and canonical-byte evidence across the entire capture-to-engine chain.

This is not new territory. It is Build 1 from the original roadmap: capture and advisory over the deterministic Build 0 spine.

---

## 2. Non-Negotiables During Implementation

These are build constraints, not preferences:

1. **PostgreSQL only.** Runtime and persistence tests must not introduce SQLite fallback.
2. **No FAISS, embeddings, vector store, nearest-neighbor lookup, or model authority.** A model may help translate text into proposed records only outside authority. Structured decisions must be deterministic.
3. **No hardcoded domain policy.** Source types, limits, authority roles, validation predicates, route reasons, storage policy, and facility/tool capability are governed records or fixtures, never hidden literals.
4. **No magic numbers.** Numeric bounds must be named, spec-cited constants or governed policy values. Local literal values are allowed only in tests when the fixture explicitly defines the governed policy under test.
5. **Fail closed.** Missing, unsupported, wrong-scope, ambiguous, stale, unauthorized, non-canonical, or tampered input returns a typed non-verdict or advisory gap, not an inferred pass.
6. **No bare values into Build 0.** Build 0 receives governed proposal-version references, content hashes, typed canonical values, and evidence locator refs.
7. **No unratified Tier 1 influence.** Parser output, observations, protocol results, and manual proposals are not facts until ratified.
8. **No application defaults for authority or canonicalization.** Every governed Build 1 record binds the relevant policy.
9. **Comments explain why, never what.** Comments should document domain judgment, fail-closed reasoning, or a constraint a maintainer might otherwise remove.
10. **Build 0 remains frozen.** Build 1 may bridge into Build 0 through existing contracts, but it must not rewrite Build 0 behavior to make Build 1 easier.

---

## 3. Repository Targets

Use the target shape from `GPTL_BUILD1_PLAN_v0.7.md`. Module names may move only if the behavioral boundary stays identical and the move is documented in the slice closeout.

```text
src/gptl/core/
  capabilities.py
  scope.py
  algorithms.py
  source_artifacts.py
  parse_attempts.py
  proposals.py
  identity.py
  authority.py
  validation.py
  observations.py
  ratification.py
  replay_build1.py
  persistence.py

src/gptl/mie/
  capture_service.py
  build1_bridge.py

tests/build1/
  test_slice_01_capability_profile.py
  test_slice_02_source_registration.py
  test_slice_03_typed_proposals.py
  test_slice_04_ratification_workflow.py
  test_slice_05_attributed_observations.py
  test_slice_06_validation_protocols.py
  test_slice_07_build0_bridge.py
  test_slice_08_replay_closeout.py
```

The existing Build 0 tests under `tests/conformance/` and `tests/slices/` are part of every Build 1 regression gate.

---

## 4. Migration Plan

Add forward-only PostgreSQL migrations under `src/gptl/core/migrations/`. Keep them small enough that failures point to the slice that introduced them.

```text
0005_build1_capability_scope.sql
0006_build1_sources.sql
0007_build1_proposals.sql
0008_build1_ratification_authority.sql
0009_build1_observations_validation.sql
0010_build1_bridge_replay.sql
```

Migration rules:

- Append-only governed records get immutable identity, explicit lifecycle, schema version, content hash, canonicalization policy ref, provenance, valid time, and recorded time.
- Raw source bytes and their source record commit atomically in PostgreSQL.
- Database constraints enforce local integrity, but application replay remains the authority for semantic validity and active-value conflict diagnosis.
- No migration may encode facility-specific tool assumptions, SpaceX-specific system names, or production deployment claims.

---

## 5. Slice 0 - Implementation Harness

**Goal:** create the build harness without changing behavior.

Implement:

- `tests/build1/conftest.py` with reusable governed fixture builders.
- Test helpers for canonical-byte assertions, content-hash assertions, complete `GovernedRef` construction, and PostgreSQL fixture setup.
- Static scan helper for prohibited runtime concepts: vector implementations, SQLite fallback, hidden local scope logic, hidden identity recipes, and module-local predicate engines.

Exit gate:

- Existing Build 0 tests pass unchanged.
- Empty Build 1 test package collects cleanly.
- Static scan helper is exercised by at least one test.

No product behavior lands in Slice 0.

---

## 6. Slice 1 - Capability Profile and Evidence Scope

**Goal:** Build 1 can say what corpus/tool profile a run is allowed to use, and can reject wrong-scope data before source selection.

Implement:

- `core/capabilities.py`
  - `CapabilityProfile`
  - source-system capability records
  - source-class support records
  - `SourceStoragePolicy` reference surface
- `core/scope.py`
  - `EvidenceScopeV1`
  - `EVIDENCE_SCOPE_MATCH_V1`
  - `SCOPE_INCOMPATIBLE` diagnostics with mismatched dimension IDs

Scope dimensions are exactly:

```text
scope_class
organization_id
site_id
workspace_id
data_boundary_id
context_id
```

Tests:

- Exact match passes.
- One mismatch in each of the six dimensions fails with the correct dimension ID.
- Inactive scope fails.
- Missing, empty, wildcard, inherited, and application-default scope fields are invalid.
- Capability lists canonicalize order-independently.
- Unknown source class produces an advisory/capture gap, not inferred support or absence.
- Build 0 bridge scope publication can produce a complete `GovernedRef`, but does not call Build 0 yet.

Exit gate:

- No source/proposal selection path can run without a valid capability profile and exact `EvidenceScopeV1` match.

---

## 7. Slice 2 - Source Registration

**Goal:** preserve real source artifacts with exact byte provenance before parsing or interpretation.

Implement:

- `core/source_artifacts.py`
  - `SourceArtifactRecord`
  - raw byte hash contract
  - source class and claimed origin
  - parser eligibility state
  - governed max-byte enforcement
- migration `0006_build1_sources.sql`
- persistence extension for source record plus raw bytes in one transaction

Rules:

- `raw_byte_hash` is SHA-256 over exact received bytes.
- Text decoding, newline normalization, OCR, CSV parsing, and cleanup are later parse attempts, never raw-byte mutation.
- Over-limit payloads must be rejected while streaming, before the full payload is buffered in application memory.
- Failed source registration leaves neither visible source row nor visible raw bytes.

Tests:

- Identical bytes produce identical raw hashes.
- Metadata changes do not change raw byte hash.
- Raw bytes round-trip exactly from PostgreSQL.
- Over-limit stream fails before full-buffer read.
- Unsupported source class returns governed capture gap.
- Parser-eligible and parser-ineligible states are deterministic and replayable.
- Transaction rollback leaves no partial source rows or byte rows.

Exit gate:

- No parser/proposal code can consume a source unless the source record and raw bytes are committed and hash-verified.

---

## 8. Slice 3 - Algorithms, Parse Attempts, Typed Proposals, and Identity

**Goal:** convert source material into evidence-linked proposed values without making them authoritative.

Implement:

- `core/algorithms.py`
  - governed executable algorithm registry entries
  - algorithm identity, version, source hash, and replay compatibility
- `core/parse_attempts.py`
  - `ParseAttemptRecord`
  - parser/decoder/OCR attempt records
  - parse success, partial, unsupported, and failure states
- `core/proposals.py`
  - typed proposed-value envelope
  - `ProposalEvidenceV1`
  - canonical value policy binding
  - proposal validation state
- `core/identity.py`
  - existing governed reference identity
  - caller-supplied identity with evidence
  - `SOURCE_LOCAL_RECORD_IDENTITY_V1`
- migration `0007_build1_proposals.sql`

Rules:

- Parser-derived proposal must bind exact `parse_attempt_ref`.
- Parser, decoder, identity, and canonicalization behavior resolves through governed algorithm registry entries.
- `SOURCE_LOCAL_RECORD_IDENTITY_V1` requires an evidence-backed `source_local_record_key`.
- Proposed values, corrected values, extracted text, display labels, and mutable wording cannot define source-local identity.
- `version_number` is unique and strictly monotonic within `logical_id` before publication.
- Duplicate `version_number` returns `INTEGRITY_FAILURE` with `DUPLICATE_VERSION_NUMBER`.
- Non-monotonic, out-of-range, missing, policy-free, or non-integer `version_number` returns `CONFIGURATION_INVALID`.

Tests:

- Parser-derived proposal without `parse_attempt_ref` fails.
- Proposal evidence locator must be byte/cell-stable unless the renderer/OCR chain is bound.
- Multiple records in one source artifact do not collapse.
- Correcting a value preserves logical identity when the source-local record key is unchanged.
- Changing only extracted value text does not mint a new source-local identity.
- Duplicate, non-monotonic, out-of-range, missing, policy-free, and non-integer version numbers map to the governed result classes above.
- Decimal proposals bind canonicalization policy before content hash.
- Duplicate proposal submission is not accepted as idempotent success.

Exit gate:

- Build 1 can store typed proposals and evidence locators, but none are decision-effective.

---

## 9. Slice 4 - Authority, Ratification, and Active Values

**Goal:** make proposed values decision-effective only through governed human ratification.

Implement:

- `core/authority.py`
  - local actor registry
  - role assignment records
  - action authorization records
  - authority policy refs
  - separation-of-duties checks
- `core/ratification.py`
  - `ProposalRatificationEvent`
  - correction/supersession event handling
  - active-value resolver policy binding
  - `ACTIVE_VALUE_STATE_HASH_V1`
- migration `0008_build1_ratification_authority.sql`

Rules:

- Ratification verifies proposal content hash before eligibility.
- Claimed actor attribution is local-governed, not cryptographic external identity.
- Authority is explicit; no action uses an application default policy.
- Historical conflicts replay as conflicts. Later correction/supersession resolves future runs only.
- `active_value_state_hash` uses the exact `ACTIVE_VALUE_STATE_HASH_V1` JCS payload from v0.7.

Tests:

- Unauthorized actor cannot ratify.
- Missing authority policy fails closed.
- Same actor cannot satisfy prohibited separation-of-duties.
- Backdated events do not rewrite prior run eligibility.
- Active-value conflict cites exact colliding `ProposalRatificationEvent` refs.
- `ACTIVE_VALUE_STATE_HASH_V1` canonical bytes are byte-stable across process restart.
- Hash changes when any eligible event ref, target key, proposal ref, proposal content hash, or active outcome changes.
- Recursive NFC normalization and timestamp policy are exercised by fixtures.

Exit gate:

- Ratified values can be selected as active Build 1 values, but they still have not entered Build 0.

---

## 10. Slice 5 - Attributed Observations

**Goal:** capture tribal knowledge and continuous context without letting unvalidated statements become facts.

Implement:

- `core/observations.py`
  - `AttributedObservation`
  - observation source attribution
  - uncertainty/status fields
  - Tier-2-only eligibility surface
- observation capture paths in `mie/capture_service.py`
- migration portion in `0009_build1_observations_validation.sql`

Rules:

- Attributed observations are never Tier 1 evidence.
- Observations never change Build 0 route selection.
- Observations never change the frozen `AdvisoryDecision` schema.
- Promotion creates a typed proposal through governed validation/corroborating evidence; that proposal still requires ratification.

Tests:

- Unvalidated observation cannot appear in Tier 1 candidate evidence.
- Unvalidated observation cannot affect Build 0 route reason.
- Promotion creates proposal-only material, not a fact.
- Observation replay preserves attribution and status.
- Removing observations from a run cannot change structured Tier 1 output.

Exit gate:

- Build 1 can ingest "vibes" and tribal knowledge honestly, with zero authority leakage.

---

## 11. Slice 6 - Designed Validation Protocols

**Goal:** allow governed validation protocols to produce evidence-backed proposals without opening a custom rule-engine escape hatch.

Implement:

- `core/validation.py`
  - `DesignedValidationProtocol`
  - `DesignedValidationResult`
  - `VALIDATION_PREDICATE_TEMPLATES_V1`
- predicate templates:
  - `REQUIRED_PRESENT`
  - `TERM_EQUALS`
  - `DECIMAL_EQUALS`
  - `DECIMAL_IN_CLOSED_RANGE`
  - `TIMESTAMP_IN_CLOSED_INTERVAL`
  - `UNIT_COMPATIBLE`
  - `ALL_OF`
- migration portion in `0009_build1_observations_validation.sql`

Rules:

- Predicate operands bind canonicalization policy before truth evaluation.
- Designed validation cannot qualify a method, qualify production process, or bypass ratification.
- Protocol result may create typed proposal material only.
- Missing operands, invalid operands, unknown predicates, and policy mismatch fail closed.

Tests:

- Every predicate template has pass, fail, missing-input, invalid-input, and replay fixtures.
- Decimal operand canonicalization happens before comparison.
- Unknown predicate template is `CONFIGURATION_INVALID`.
- Protocol result cannot enter Build 0 directly.
- Protocol-derived proposal still requires Slice 4 ratification.

Exit gate:

- Validation protocols can improve proposal quality, but authority still comes only from ratification.

---

## 12. Slice 7 - Build 0 Bridge

**Goal:** assemble a deterministic, replayable Build 0 request from ratified Build 1 values without changing Build 0.

Implement:

- `mie/capture_service.py`
  - capture gate orchestration
  - proposal and ratification workflow entry points
- `mie/build1_bridge.py`
  - `CaptureGateResult`
  - `BridgeAttemptRecord`
  - Build 0 request assembly
  - read-by-ID reconciliation
  - bridge integrity diagnostics
- migration `0010_build1_bridge_replay.sql`

Rules:

- Bridge accepts only ratified, active, scope-compatible, canonicalization-compatible values.
- Build 0 snapshots receive proposal `logical_id`, `version_id`, `version_number`, `content_hash`, target key, typed canonical value, and `ProposalEvidenceV1` locator ref.
- Duplicate Build 0 writes are never accepted as retry-equivalent success or upsert.
- Retry uses request-stable read-by-ID reconciliation against caller-supplied Build 0 IDs.
- Output and Build 0 replay-capsule hashes are adopted only after Build 0 produces them.
- Shared-unit-of-work bridge execution preserves the frozen Build 0 PostgreSQL writer advisory lock.

Tests:

- Unratified proposal stops before Build 0.
- Wrong scope stops before Build 0.
- Missing active-value state hash stops before Build 0.
- Decimal/canonicalization incompatibility stops before Build 0.
- Bare typed value injection is impossible through public bridge API.
- Successful bridge produces a Build 0 request that cites governed proposal-version refs and content hashes.
- Duplicate bridge retry performs read-by-ID reconciliation.
- Mismatched read result becomes `BRIDGE_INTEGRITY_FAILURE`.
- Existing Build 0 tests pass unchanged.

Exit gate:

- Build 1 can safely feed the frozen Build 0 engine with ratified capture data.

---

## 13. Slice 8 - Replay and Completion Evidence

**Goal:** close Build 1 with self-audited evidence rather than narrative confidence.

Implement:

- `core/replay_build1.py`
  - `Build1BridgeReplayCapsule`
  - `BUILD1_EXACT_REPLAY_V1`
  - replay verification result union
- completion evidence generator for Build 1
- gate map tying completion claims to exact test node IDs and artifact hashes

Replay capsule binds:

- capability profile
- evidence scope
- source records and raw byte hashes
- parse attempts
- algorithm registry entries
- proposal records
- evidence locators and derived hashes
- identity recipe inputs/results
- authority policies and authorization events
- ratification events
- active-value resolver policy and state hash
- observations
- validation protocols/results
- capture gate result
- bridge attempt state
- generated Build 0 request
- Build 0 replay capsule reference when present

Tests:

- Replay is byte-identical across process restart.
- Tampered source record fails.
- Missing raw bytes fail.
- Tampered parse attempt fails.
- Tampered algorithm registry entry fails.
- Tampered proposal, evidence locator, identity recipe, authority event, ratification event, observation, protocol, capture gate, or bridge attempt fails.
- Build 0 request drift fails.
- Generated completion evidence derives readiness only from executed gates.
- Cross-minor canonical fixtures match on supported Python minors.

Exit gate:

- Build 1 completion evidence binds exact source commit, governing document hashes, dependency lockfile, migrations, test inventory, gate map, validation schemas, canonical wire schemas, replay recipes, canonical samples, and fixture equality.

---

## 14. Work Order

Implement in this order:

1. Slice 0: harness.
2. Slice 1: capability profile and scope.
3. Slice 2: source registration.
4. Slice 3: parse attempts, proposals, and identity.
5. Slice 4: ratification and active values.
6. Slice 5: attributed observations.
7. Slice 6: validation protocols.
8. Slice 7: Build 0 bridge.
9. Slice 8: replay and completion evidence.

Do not start the next slice until:

- the slice tests pass,
- existing Build 0 tests still pass,
- the slice has no unresolved correctness findings,
- static scans still pass,
- the slice closeout names any implementation deviations from v0.7.

Small drift is not deferred. If a slice exposes a mismatch between implementation and v0.7, fix the implementation or explicitly rev the governing spec before proceeding.

---

## 15. Local Gate Commands

Use local gates, not a new CI service.

```bash
uv run pytest tests/conformance tests/slices
uv run pytest tests/build1
uv run ruff check src tests scripts
uv run mypy src
git diff --check
```

PostgreSQL-backed tests should use the repository's existing database fixture pattern. If local PostgreSQL is unavailable, tests may skip with an explicit skip reason, but a slice is not closed until its PostgreSQL gate has passed in an environment with PostgreSQL.

Static scan minimum:

```bash
rg -n "faiss|pgvector|Pinecone|Weaviate|Chroma|embedding|nearest[-_ ]neighbor|similarity" src tests
rg -n "sqlite|sqlite3" src tests
rg -n "TODO|FIXME|HACK|magic number|temporary" src/gptl/core src/gptl/mie tests/build1
```

The scan can flag quoted prohibitions in docs. Runtime code and Build 1 tests must not introduce the prohibited implementations.

---

## 16. Tool-Profile Entry Screen

The eventual "choose your tools" entry screen should be a thin UI over Slice 1 capability profiles.

It must not define policy. It should:

- create or select a governed capability profile,
- bind an `EvidenceScopeV1`,
- list declared source systems, source classes, and storage policies,
- show unsupported/unknown tools as explicit gaps,
- let the operator upload/register source artifacts only after scope and capability are valid.

This can be built after Slice 1 and Slice 2 are stable. It should not block backend implementation.

---

## 17. What We Can Build Without Knowing a Specific Lab

We can build the deterministic platform contracts now:

- governed scope,
- capability profile schema,
- source artifact preservation,
- parser/proposal contracts,
- authority and ratification,
- observation intake,
- validation protocols,
- Build 0 bridge,
- replay and evidence closeout.

We cannot honestly build production vendor adapters or facility-specific packs until we have legal, real sample artifacts and the lab's actual systems. Build 1 handles that by making tool support configured and evidence-bound instead of hardcoded. Unknown equipment becomes an explicit capability gap, not a reason to stop building the substrate.

---

## 18. Build 1 Definition of Done

Build 1 is done when:

- all eight implementation slices are complete,
- all v0.7 Build 1 completion gates are satisfied,
- Build 0 tests pass unchanged,
- PostgreSQL migrations are forward-only and source-audited,
- completion evidence is generated from executed gates,
- replay detects tampering and missing records across the capture-to-engine chain,
- no structured output changes when model adapters are removed,
- no prohibited vector, SQLite, hidden-default, or hardcoded domain-policy path exists,
- the final closeout doc cites the exact commit, dependency lockfile digest, governing document hashes, test inventory, migration digests, canonical samples, replay fixtures, and known deferred items.

At that point Build 1 is not a production lab deployment. It is a deterministic, source-audited capture and advisory substrate ready for real source adapters and facility packs.
