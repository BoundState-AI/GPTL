# GPTL MIE Build 1 Plan
## Capability-Profiled Capture & Advisory Contract - v0.5

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20

**Status:** Draft after ORACLE sessions `20260623-040533`, `20260623-185534`, `20260623-192631`, and manual ORACLE review closeout `BUILD_1_PLAN_NOT_READY`; not an implementation freeze packet

**Build 0 dependency:** Build 0 is frozen by `GPTL_ORACLE_BUILD0_CLOSEOUT_REVIEW_v1.6.md`. Build 1 extends the frozen deterministic spine; it does not reopen Build 0 architecture, verdict semantics, replay, storage, canonicalization, or MSA/calibration gates.

**Operational boundary:** Build 1 remains `RESEARCH_ONLY`, non-dispositional, and not a QMS, quality, flight, or engineering record of record. It may create governed source, proposal, ratification, observation, and validation-protocol records. It does not qualify methods, instruments, MSA studies, vendor parsers, thresholds, process controls, or production actions.

**v0.2 review closeout:** resolves the Build 1 plan defects from ORACLE session `20260623-040533`. Direct instrument-emitted Tier 1 authority is deferred; Build 1 treats instrument/parser output as source-backed proposal material that still requires ratification before Tier 1. Active-value selection is defined by a target key and bind-time head resolution rather than an overclaimed database uniqueness constraint. Capability-profile scope checks, minimal authority policy, correction workflow, observation/protocol promotion through ratification, source-byte storage atomicity, raw-byte hashing, and fail-closed diagnostics are now explicit.

**v0.3 owner closeout:** resolves the remaining Build 1 plan defects from ORACLE session `20260623-185534`. The Build 1 `EvidenceScopeV1` dimension set and exact-match semantics are fixed. Source-derived record identity is limited to explicit existing references, caller-supplied identities, or a deterministic source-local identity recipe; fuzzy merge and entity reconciliation are deferred. Designed-validation acceptance criteria are limited to a small closed predicate-template set. Ratifiable evidence locations are byte/cell-stable only unless a parser/renderer/OCR toolchain is itself bound into the replay surface. Build 1 authority records represent claimed actor attribution against a governed local registry, not authenticated signatures. Active-value conflicts are resolved only by later correction/supersession events in later runs; historical conflicts replay as conflicts.

**v0.4 owner closeout:** resolves the blocked Build 1 plan findings from ORACLE session `20260623-192631` with conservative implementation choices. `SOURCE_LOCAL_RECORD_IDENTITY_V1` now requires an evidence-backed `source_local_record_key` so multiple records in one artifact do not collapse and value corrections do not mint new logical identities. Parser-derived proposals bind an exact `parse_attempt_ref`, and parser/decoder/identity/canonicalization algorithms resolve through governed executable registry entries rather than bare strings. Capability profiles no longer define calibration/MSA policy. The Build 0 bridge no longer assumes a shared transaction; it uses a deterministic narrowed-boundary bridge attempt when the frozen Build 0 engine owns its persistence boundary.

**v0.5 closeout:** resolves the manual `BUILD_1_PLAN_NOT_READY` bridge finding and closes the associated minor schema/replay gaps. Build 1 no longer describes any Build 0 retry/upsert semantic. Bridge retry is request-stable read-reconciliation against caller-supplied Build 0 IDs, because frozen Build 0 treats duplicate writes as integrity failures and allows recovery only by read-by-ID. `EvidenceScopeV1` is a governed Build 1 scope record whose `GovernedRef` must conform to the frozen Build 0 `BoundDecisionContext.evidence_scope_ref` surface before a bridge request exists. Numeric proposals bind Decimal canonicalization policy before hashing or ratification. Active-value resolution binds a governed resolver policy and active-state hash. Build 0 snapshots receive governed proposal-version refs and content hashes, never bare typed values.

---

## 1. Purpose

Build 1 turns the v0.4.20 Build 1 paragraph into executable vertical slices:

> Source registration and evidence-grounded proposals; human validation/ratification; governed designed-validation protocols; attributed-observation ingestion (`UNVALIDATED`, Tier-2-only); deterministic custom lexical Tier 2 retrieval; optional Bouncer and renderer adapters. Vendor-specific instrument adapters MAY begin here only from real, legally usable source files and MUST preserve the raw artifact and provenance.

Build 1 reuses the frozen Build 0 deterministic Tier 2 resolver. Build 1 supplies governed capture context, advisory gaps, and optional external rendered context; it does not rebuild or fork the Build 0 lexical resolver.

The core product question is:

**How do we take messy manufacturing/lab source artifacts that Build 1 can replay, preserve provenance, propose typed governed records, let a human validate or ratify them, and feed only governed values into the existing Build 0 engine?**

Build 1 is not new territory. It implements the original platform intent in §§2.3–2.7, §6, §11, and §18:

- Models translate or propose; they do not decide.
- Raw source artifacts are preserved and content-hashed.
- Proposed values are not authoritative.
- Ratification is explicit, claimed-actor-bound against a governed local registry, bitemporal, and append-only.
- Attributed observations preserve tribal knowledge without laundering it into fact.
- Missing capability, unsupported tools, and absent evidence produce explicit advisory gaps.
- The existing Build 0 engine remains the only Tier 1 MIE verdict path.

---

## 2. Build Rules

These are inherited from Build 0 and remain release-blocking:

- No FAISS, embeddings, vector database, similarity retrieval, or nearest-match fallback.
- No model output in candidate generation, applicability, scoring, confirmation, verdicts, or canonical payloads.
- No `float` in decision arithmetic or canonical decision data.
- No SQLite runtime or test fallback.
- No application default for domain policy, thresholds, units, evidence requirements, capability declarations, source precedence, parser behavior, or applicability.
- No authoritative free text. Human prose exists only in separate rendered artifacts or as unvalidated attributed observation text.
- No implicit latest-version lookup. Every governed input is an explicit immutable version.
- No missing value is converted to negative evidence.
- No unratified proposed value enters Tier 1.
- No direct instrument-emitted Tier 1 authority path exists in Build 1. Instrument, parser, import, model-assisted, and manual data all enter as source-backed proposals and require the same active ratification gate before Tier 1.
- No source artifact is overwritten by a parsed value; parsed values always cite the raw artifact and evidence location.
- No vendor-specific adapter is implemented without real, legally usable source files and expected-output fixtures.
- No authority check uses an application default. Ratification, rejection, correction requests, protocol execution, and protocol-derived value ratification all resolve through an explicit governed authority policy.
- No governed record identity is invented ad hoc. A proposal either targets an existing governed reference, uses a caller-supplied identity with evidence, or uses the published `SOURCE_LOCAL_RECORD_IDENTITY_V1` recipe.
- No source-local identity derives from proposed values, corrected values, extracted text, display labels, or mutable evidence wording. Source-local identity requires an evidence-backed `source_local_record_key`.
- No parser-derived proposal can become ratifiable without an exact `parse_attempt_ref`.
- No parser, decoder, identity, canonicalization, or locator-derivation behavior executes from a bare string. Each executable behavior resolves through a governed `AlgorithmRegistryEntry`.
- No module defines its own scope, identity, predicate, or evidence-location semantics. Build 1 uses the closed contracts in §§4.1, 6.1, 6.2, and 9.1.
- No PDF/OCR/image-region locator is ratifiable in Build 1 unless the exact parser/renderer/OCR algorithm ID, version, parameters, and derived artifact hash are bound into replay. Otherwise those locations may support proposals only.
- Build 1 source bytes are stored in PostgreSQL with their source record in the same transaction. External content-addressed storage is deferred until a production storage profile is specified.
- No unbounded buffering occurs before max-byte enforcement. Source registration enforces the governed byte limit while reading the payload.
- No Build 1 bridge path assumes Build 0 shares the caller's transaction. If the frozen Build 0 service cannot run inside a caller-supplied unit of work, Build 1 uses the narrowed-boundary bridge attempt contract in §10.
- No Build 1 bridge path treats a caller-supplied Build 0 identity as a retry token or upsert instruction. Request-stable retry uses read-by-ID reconciliation; duplicate Build 0 writes remain integrity failures under the frozen Build 0 contract.
- No Build 0 snapshot receives a bare typed value from Build 1. Decision-effective values enter only as governed proposal-version refs with content hashes and evidence locations.
- No Build 1 governed record relies on an application-default canonicalization policy. Source, parse-attempt, proposal, ratification, observation, validation, capture-gate, and bridge-attempt records bind the applicable `CanonicalizationPolicy`.
- Every synthetic/reference fixture identifies its fixture class and cannot claim vendor, lab, or production fidelity.
- Build 1 must pass with every model adapter disabled. Optional model-assisted proposal paths are convenience inputs only, never authority.
- Tests run locally. This plan adds no CI service or deployment automation.

Any implementation pressure to weaken one of these rules is a stop condition.

---

## 3. Target Repository Shape

Paths are introduced only when the slice first exercises them.

```text
src/gptl/
  core/
    capabilities.py         governed facility/tool capability profile contracts
    scope.py                closed EvidenceScopeV1 contract and match function
    algorithms.py           governed executable algorithm registry contracts
    source_artifacts.py     raw source registration and content-hash contracts
    parse_attempts.py       replay-bound parser/decoder attempt records
    proposals.py            typed proposed-value envelope, evidence locators, validation states
    identity.py             source-local proposed record identity recipes
    authority.py            minimal governed actor/role/action policy contracts
    validation.py           closed designed-validation predicate templates
    observations.py         attributed-observation contracts
    ratification.py         Build 1 ratification workflow over proposed values
    replay_build1.py        Build 1 exact replay capsule and verification contracts
    persistence.py          existing append-only PostgreSQL store, extended by migrations
  mie/
    capture_service.py      Build 1 source/proposal/ratification orchestration
    build1_bridge.py        snapshot assembly into existing Build 0 MIE service paths and bridge attempts
tests/
  build1/
    test_slice_01_capability_profile.py
    test_slice_02_source_registration.py
    test_slice_03_typed_proposals.py
    test_slice_04_ratification_workflow.py
    test_slice_05_attributed_observations.py
    test_slice_06_validation_protocols.py
    test_slice_07_build0_bridge.py
    test_slice_08_replay_closeout.py
docs/
  GPTL_BUILD1_PLAN_v0.5.md
```

The exact module names may change if implementation finds a cleaner local boundary, but the behavioral contracts and gates below are not optional.

---

## 4. Slice 1 — Capability Profile

### Goal

Create a governed facility/tool capability declaration so the system can represent what data sources and methods are available, unavailable, unknown, or unsupported without guessing.

### Scope

The capability profile is a versioned governed record. It declares:

- Facility/profile identity and evidence scope.
- Owning organization/actor and authority-policy reference.
- Instruments/tools available by governed type, not vendor folklore.
- Source systems such as LIMS, QMS, historian, file drop, manual upload, or unknown.
- Accepted source artifact classes such as CSV, PDF, image, vendor export, note, or log.
- Measurement classes supported by available tools.
- Non-authoritative calibration/MSA capability labels for routing and advisory diagnostics only.
- Explicit unsupported and unknown capabilities.
- Accepted source classes bind a governed `SourceStoragePolicy` that declares max bytes per source record and allowed evidence-locator classes.
- Effective and expiration timestamps.
- Owner and evidence references.

A Build 1 run binds exactly one capability-profile version by complete governed reference. The profile's evidence scope must match the run scope, source-artifact scope, proposal scope, and any Build 0 snapshot scope assembled from it. A wrong-but-explicit profile is still rejected if its scope, owner, or active lifecycle state is incompatible with the run.

### Evidence Scope Contract

`EvidenceScopeV1` is the only Build 1 scope schema. It is a governed immutable record with these exact dimensions:

- `scope_class`: `TEST_FIXTURE` or `RESEARCH_CORPUS`.
- `organization_id`: governed organization term.
- `site_id`: governed site term.
- `workspace_id`: governed workspace, lab, project, or data-room term.
- `data_boundary_id`: governed boundary term separating unrelated corpora.
- `context_id`: governed context term for the specific Build 1 exercise.

All dimensions are required. `UNSCOPED`, missing, empty, wildcard, inherited, or application-default dimensions are invalid in Build 1.

`scope_matches(candidate_scope, run_scope)` is `EVIDENCE_SCOPE_MATCH_V1`:

1. The candidate and run scopes must use `EvidenceScopeV1`.
2. All six dimensions must compare by exact governed term equality.
3. A lifecycle-inactive scope is not eligible.
4. A mismatch returns `SCOPE_INCOMPATIBLE` with the mismatched dimension IDs.

There is no containment, hierarchy, wildcard, or temporal-overlap operator in Build 1 scope matching. Effective/recorded time remains the existing bitemporal eligibility check on records and events; tool/source/method fit remains capability resolution. This is intentionally narrower than production scoping so no facility-level profile can silently match the wrong corpus.

For the Build 0 bridge, `EvidenceScopeV1` is published as a governed scope record and passed to frozen Build 0 only by complete `GovernedRef` through `BoundDecisionContext.evidence_scope_ref`. Build 1 does not pass a foreign scope object into Build 0. If the resolved `EvidenceScopeV1` record cannot be represented as a valid frozen Build 0 governed reference, or if its content hash does not verify, bridge assembly fails before Build 0 as `SCOPE_INCOMPATIBLE`.

`scope_class = TEST_FIXTURE` maps to the existing Build 0 test-fixture isolation rule. `scope_class = RESEARCH_CORPUS` is a Build 1 research-corpus scope for non-production capture and advisory work; it does not imply bench, vendor, company, or production-scoped MSA eligibility. Frozen Build 0 calibration/MSA gates still require their own exact scope match to a qualified study. If no such Build 0 scope-matched study exists, Build 0 produces its existing calibration/MSA refusal or advisory behavior.

### Exit Gate

- A profile with no declared capability cannot silently allow intake.
- Unknown and unsupported capabilities are distinct states.
- Missing capability produces a typed advisory gap, never a guessed source path.
- Calibration/MSA capability labels cannot satisfy, override, or redefine the frozen Build 0 calibration/MSA gates.
- Capability lists are canonical, unique, and order-independent.
- Scope mismatch, inactive lifecycle state, missing owner, or missing authority policy fails before source/proposal selection.
- A Build 1 scope ref used in a Build 0 request validates as a frozen Build 0 `GovernedRef` and has a byte-identical replay golden vector.
- Scope match/no-match golden vectors cover all six dimensions and lifecycle-inactive scopes.
- The profile has no domain constants in generic code.

### Deferred

Production RBAC, dynamic discovery from enterprise systems, vendor-specific identity resolution, and multi-site capability federation.

---

## 5. Slice 2 — Source Registration

### Goal

Register raw artifacts before any extraction or proposal occurs.

### Scope

`SourceArtifactRecord` captures:

- Source artifact ID, logical ID, version ID, schema version, lifecycle state.
- `version_number`, content hash, and bound `CanonicalizationPolicy` reference.
- Raw payload bytes stored in PostgreSQL and `raw_byte_hash`, the SHA-256 hash of the exact received bytes.
- `content_hash`, the canonical hash of the source record metadata, distinct from `raw_byte_hash`.
- Byte length, media type, and optional filename as metadata outside the raw-byte hash.
- Submitted filename or external identifier as non-authoritative metadata.
- Source class and claimed origin.
- Submitter, received time, asserted source time when available.
- Evidence scope and capability-profile reference.
- Parser eligibility state: `UNPARSED`, `PARSER_UNAVAILABLE`, `PARSER_UNSUPPORTED`, `PARSER_READY`, `PARSER_FAILED`.

Build 1 source registration is one PostgreSQL transaction: resolve the source class against the bound capability profile and `SourceStoragePolicy`, stream the payload while enforcing the governed max-byte limit, insert the source record, raw bytes, hash metadata, audit event, and any parser-eligibility record together, then verify the stored bytes against `raw_byte_hash` before commit visibility. A failure commits neither row nor bytes. The implementation must reject over-limit payloads before the full payload is buffered in application memory. Raw source bytes are not canonicalized before hashing; newline normalization, text decoding, OCR, and parser cleanup produce separate parse-attempt/proposal records that cite the raw artifact.

Parser eligibility records bind the applicable `AlgorithmRegistryEntry` references for decoders/parsers when a deterministic parser path exists. `PARSER_UNAVAILABLE`, `PARSER_UNSUPPORTED`, and `PARSER_FAILED` are recorded source states; they do not create inferred negative evidence or authority.

### Exit Gate

- Identical bytes produce identical `raw_byte_hash`.
- Different metadata over identical bytes does not change `raw_byte_hash` but does change source-record `content_hash`.
- Text and binary artifacts are hashed as exact bytes received, not as canonicalized text.
- Over-limit payloads fail before raw bytes or metadata become visible.
- A parsed/proposed record cannot exist without a registered raw source.
- Unsupported source class becomes explicit advisory gap.
- Failed parser does not mutate or delete the source artifact.
- Parser status binds the algorithm registry entry or the governed reason no parser was eligible.
- Raw source registration is append-only and replayable.

### Deferred

Large-object storage hardening, malware scanning, data retention policy, production access control, external system polling, and vendor-native binary parser fidelity.

---

## 6. Slice 3 — Typed Proposal Layer

### Goal

Represent extracted or translated values as typed proposals with evidence locations, never as authoritative facts.

### Scope

`TypedValueProposal` captures:

- Proposal identity and source artifact reference.
- `version_number`, content hash, and bound `CanonicalizationPolicy` reference.
- Claimed proposer/extractor actor reference when available, proposal method, and creation event reference.
- Proposed target descriptor: target record type, target logical ID, target schema version, semantic field path, and `context_key`.
- Proposed typed value with unit, Decimal policy, and canonical timestamp policy where applicable.
- Evidence location in the source artifact using the closed `ProposalEvidenceV1` locator set.
- Validation state: `PROPOSED`, `VALIDATION_FAILED`, `READY_FOR_RATIFICATION`, `REJECTED`, `SUPERSEDED`.
- Validation errors with governed reason IDs.

`context_key` is the canonical object containing every schema-declared dimension needed to distinguish multiple values for the same target field. Examples include sample side, measurement replicate, process step, parameter channel, specimen ID, or condition set. If the target schema declares no disambiguating dimensions, `context_key` is the explicit empty object. The target schema owns the allowed keys, value types, and canonical sort order. Unknown, missing, extra, or non-canonical context dimensions make the proposal invalid rather than being collapsed into the same target or split into ungoverned fragments.

`context_key` canonical bytes are computed before identity validation, active-value conflict detection, replay hashing, or bridge assembly. The same semantic context must serialize to the same bytes independent of input order. A non-canonical `context_key` is `CONFIGURATION_INVALID`, not a best-effort warning.

The active-value conflict key is target record type, target logical ID, semantic field path, and canonical `context_key`. Target schema version is retained for validation and wire compatibility, but it cannot split active heads for the same semantic target. If a future schema version changes field meaning, a governed schema-continuity map must either map it to the same semantic field path or declare it incompatible before publication.

For numeric proposed values, proposal validation binds the applicable Decimal precision, rounding mode, overflow behavior, and canonical string policy before proposal hashing, validation, ratification eligibility, replay, or bridge assembly. Numeric proposal payloads use canonical Decimal strings, never JSON numbers or `float`.

### Proposed Record Identity

Build 1 supports exactly three target-identity modes:

1. `EXISTING_GOVERNED_REF`: the proposal targets an already governed record reference.
2. `CALLER_SUPPLIED_IDENTITY`: the source provides a stable external identity, cited by evidence location. Build 1 normalizes only by Unicode NFC and the bound canonical timestamp/Decimal policies. It does not case-fold, strip punctuation, fuzzy-match, or merge near-duplicates.
3. `SOURCE_LOCAL_RECORD_IDENTITY_V1`: the proposal targets a new record local to one source artifact. The logical ID is derived from the SHA-256 of canonical bytes over `{scope_ref, source_artifact_ref, target_record_type, source_local_record_key}` under the bound canonicalization policy. The version identity is derived from the canonical proposal payload.

`source_local_record_key` is a canonical object, not a display string. It is a replay-stable discriminator for one logical record inside one source artifact and, when applicable, one parser attempt. The key object carries its key class, local discriminator, and `parse_attempt_ref` when parser-derived. It is evidence-backed and correction-stable; it cannot be derived from the proposed value, a corrected value, display text, or model-generated wording. Allowed Build 1 key sources are:

- A caller-supplied source record key cited by a ratifiable evidence locator.
- A CSV row identifier or row ordinal under a bound `parse_attempt_ref`.
- A JSON pointer to the containing object under a bound `parse_attempt_ref`.
- A UTF-8 line range under a bound `parse_attempt_ref`.
- A raw byte range under the registered source artifact's `raw_byte_hash`.

If a source artifact contains multiple records and no unique `source_local_record_key` can be proven from those allowed sources, the proposal is `IDENTITY_UNRESOLVED`. Build 1 does not invent row identities from values to make keyless data fit.

If the selected identity mode lacks required fields, the proposal is `IDENTITY_UNRESOLVED`. If a derived logical ID collides with different canonical identity inputs, publication and bridge execution fail closed as `IDENTITY_COLLISION`. Cross-source reconciliation, fuzzy entity resolution, and longitudinal merge workflows are deferred.

Submitting the identical governed proposal version a second time is not a successful duplicate-safe write. It is a duplicate insert integrity failure unless the caller is explicitly reading the already-persisted proposal by its governed reference. `version_number` is monotonic within one `logical_id`, caller-provided or allocated by a Build 1 publication service before canonical hashing, and preserved in the replay recipe; it is never inferred from query order or implicit latest lookup.

### Parse Attempt and Algorithm Registry Contracts

`ParseAttemptRecord` captures source artifact reference, parser or decoder `AlgorithmRegistryEntry` references, parser parameters, policy references, input hash, derived output hash, diagnostics, terminal status, and recorded time. Parser-derived proposals must cite a `parse_attempt_ref`; citing only a source artifact and algorithm ID is insufficient because two attempts may use the same parser version with different policies, parameters, or outcomes.

`AlgorithmRegistryEntry` captures governed algorithm ID, version ID, purpose, executable module/function reference, source digest, supported input class, output contract, parameter schema, canonicalization policy reference, lifecycle state, and evidence references. Build 1 cannot execute parser, decoder, identity, canonicalization, or locator-derivation behavior unless the registry entry resolves exactly and the executable source digest matches. An unresolved or lifecycle-inactive registry entry returns `CONFIGURATION_INVALID`.

### Proposal Evidence Locations

`ProposalEvidenceV1` is the only Build 1 evidence-location set:

- `RAW_BYTE_RANGE`: source artifact ref, start byte, end byte, and `raw_byte_hash`.
- `UTF8_LINE_RANGE`: source artifact ref, decoder algorithm registry ref, newline policy ID, start line, end line, and decoded-text hash.
- `CSV_CELL_RANGE`: source artifact ref, CSV parser algorithm registry ref, dialect policy ref, row range, column range, and parsed-table hash.
- `JSON_POINTER`: source artifact ref, JSON parser algorithm registry ref, pointer, and parsed-JSON hash.

These four locator classes are ratifiable in Build 1 when their parser/decoder policy references and derived hashes are bound. PDF page text, OCR text, image regions, screenshots, and rendered document coordinates are proposal-only in Build 1 unless a later plan revision binds the exact renderer/parser/OCR algorithm ID, version, parameters, derived artifact hash, and golden replay vectors. A proposal may cite such unstable locations for human convenience, but it cannot become `READY_FOR_RATIFICATION`.

### Exit Gate

- Unknown units, malformed timestamps, ambiguous terms, or unsupported field paths fail validation.
- Numeric proposed values without a bound Decimal policy fail validation.
- A proposal without evidence location cannot be ratified.
- A proposal without a valid target key cannot be ratified.
- A proposal whose identity mode is unresolved or collides cannot be ratified.
- A parser-derived proposal without a `parse_attempt_ref` cannot be ratified.
- A proposal using an unresolved algorithm registry entry cannot be ratified.
- A proposal whose evidence locator is not in the ratifiable `ProposalEvidenceV1` set cannot be ratified.
- Model-assisted and deterministic-parser proposals serialize to the same proposed-value schema.
- Model-assisted proposal can be disabled without changing any authoritative output.
- Proposed values cannot enter Build 0 Tier 1.

### Deferred

LLM UI, OCR quality, vendor parser qualification, automatic semantic reconciliation, and production data normalization.

---

## 7. Slice 4 — Human Ratification Workflow

### Goal

Promote a proposed value into a governed decision-effective input only through an explicit human event.

### Scope

`ProposalRatificationEvent` captures:

- Exact proposal reference and proposed value hash.
- `version_number`, content hash, and bound `CanonicalizationPolicy` reference.
- Claimed ratifying actor, role, authority-policy reference, and authorization-event reference.
- Decision: `RATIFIED`, `REJECTED`, `CORRECTION_REQUESTED`, or `SUPERSEDED`.
- Effective time and recorded time.
- Evidence references and optional reviewer note as non-authoritative prose.
- Optional superseded ratification-event reference.

`AuthorityPolicy` is the minimal Build 1 authority model. It declares actors or actor groups, roles, permitted actions, governed scope, target record classes, separation-of-duties requirements, effective/expiration times, and evidence references. `ActorRecord`, `RoleAssignmentEvent`, and `AuthorizationEvent` are governed, bitemporal, snapshot-bound records. Build 1 does not consult mutable external group membership during replay.

Build 1 records claimed actor attribution against the governed local registry. It does not claim authenticated signer identity, e-signature, identity-provider assurance, or QMS approval. Production authentication is deferred. A single-actor research lab may ratify only when the bound authority policy explicitly allows the same actor for the action and scope. In that case the ratification event records `same_actor_allowed = true`, `single_actor_policy_basis_ref`, and the claimed proposer/executor/ratifier actor references used for the policy decision. If the policy requires independence, the actor who authored the proposal, executed the protocol, or authored the observation cannot ratify the resulting value.

`ProposalRatificationEvent` is the only event that makes a value decision-effective for Tier 1 in Build 1. Protocol results and attributed observations may produce new typed proposals, but those proposals still require ratification. There is no separate promotion event with independent authority semantics.

Active-value resolution is computed at snapshot-bind time from the exact ratification event set in the snapshot. For each target key:

1. Select events whose proposal hash verifies, authority policy and authorization event are active, scope matches the run, `effective_at <= as_of_time`, and `recorded_at <= as_of_time`.
2. Remove events superseded by another eligible event.
3. `REJECTED`, `CORRECTION_REQUESTED`, and `SUPERSEDED` events cannot produce an active value.
4. Zero active `RATIFIED` heads means no Tier 1 value for that target key.
5. Exactly one active `RATIFIED` head is the decision-effective value.
6. More than one active `RATIFIED` head for the same target key is `ACTIVE_VALUE_CONFLICT` and fails closed before Build 0.

The resolver is a governed `ActiveValueResolverPolicy` with an explicit version ID. Snapshot binding stores the resolver policy ref and `active_value_state_hash`, computed from the exact eligible event refs, target keys, proposal refs, proposal content hashes, and active-value outcomes. Replay recomputes this hash before bridge assembly; a mismatch is `INTEGRITY_FAILURE`.

PostgreSQL enforces immutable event identity and duplicate primary keys; it does not claim to prove every bitemporal active-head uniqueness question with a static constraint. Build 1 write transactions use the single-writer persistence lane, and bind-time active-value resolution is the authoritative conflict check.

`CORRECTION_REQUESTED` is terminal for the proposal version it references. The corrected content is submitted as a new `TypedValueProposal` with `corrects_proposal_ref`; historical rejection/correction events remain visible and replayable.

`ACTIVE_VALUE_CONFLICT` is resolved in-band only by a later correction or supersession event that leaves exactly one active `RATIFIED` head for a later run. The conflicting historical run remains a fail-closed conflict under replay.

### Exit Gate

- Ratification verifies the proposal content hash before eligibility.
- Ratification verifies authority policy, authorization event, role assignment, and separation-of-duties records from the bound snapshot.
- Single-actor ratification records the explicit policy basis and cannot be reported as independent review.
- A later-recorded backdated ratification affects only later runs whose `as_of_time` includes it.
- Duplicate active ratification heads for the same target key fail closed with `ACTIVE_VALUE_CONFLICT`.
- `ACTIVE_VALUE_CONFLICT` diagnostics cite the exact colliding `ProposalRatificationEvent` refs by `version_id`.
- Active-value replay verifies the governed resolver policy version and active-value-state hash.
- Rejected proposals cannot enter snapshots.
- Correction-requested proposals cannot enter snapshots; only a newly submitted corrected proposal can be ratified.
- Protocol-derived and observation-derived values use the same ratification event and active-value resolver as parser/manual proposals.
- Historical replay uses the original active ratification state.

### Deferred

Enterprise identity provider integration, production RBAC, e-signatures, QMS record-of-record semantics, and delegated approval workflows.

---

## 8. Slice 5 — Attributed Observation Intake

### Goal

Capture tribal knowledge, technician observations, shift notes, and local heuristics without turning them into facts.

### Scope

`AttributedObservation` captures:

- Claim text as attributed prose.
- `version_number`, content hash, and bound `CanonicalizationPolicy` reference.
- Named source or role, recorded actor, timestamp, and production context reference when available.
- Validation state: `UNVALIDATED`, `UNDER_REVIEW`, `PROMOTED_BY_PROTOCOL`, `REJECTED`, `SUPERSEDED`.
- Evidence scope, source artifact reference when available, and confidence-free metadata.
- Tier 2 visibility policy.

Build 1 does not modify the frozen Build 0 `AdvisoryDecision` schema. Unvalidated observations are surfaced by governed reference in Build 1 capture context and may appear in a separate `RenderedArtifact` or review UI over the advisory hash. The structured Build 0 advisory output remains unchanged and carries no observation prose field.

### Exit Gate

- `UNVALIDATED` observations can appear only in Tier 2 advisory context.
- No observation text can satisfy a Tier 1 evidence requirement.
- Promotion requires a governed validation protocol result or corroborating governed evidence that creates a typed proposal; that proposal still requires a `ProposalRatificationEvent`.
- Advisory output must label the observation as attributed and unvalidated.
- Structured Build 0 `AdvisoryDecision` remains unchanged; observation prose is rendered only outside the authoritative/advisory payload.
- Observations are append-only and replayable.

### Deferred

Social trust scoring, anonymous tips, culture/process analytics, production corrective action workflows, and automated credibility inference.

---

## 9. Slice 6 — Designed Validation Protocols

### Goal

Define a deterministic path for converting a proposal or observation into validated governed evidence when direct ratification is insufficient.

### Scope

`DesignedValidationProtocol` captures:

- Hypothesis or claim under validation.
- Required data to collect.
- Required method/tool capability labels and required input record references. Build 1 protocols do not satisfy or redefine the frozen Build 0 calibration/MSA gates.
- Acceptance criteria as governed deterministic predicates.
- Required actor authority and separation-of-duties rule.
- Result schema and allowed terminal states.

`DesignedValidationResult` captures:

- Protocol reference.
- Claimed executor actor, role, authority-policy reference, and authorization-event reference.
- Collected source artifacts and typed values.
- Predicate evaluation results.
- Reviewer/authority event.
- Terminal state: `VALIDATED`, `NOT_VALIDATED`, `INCONCLUSIVE`, or `INVALID_PROTOCOL_EXECUTION`.

Designed-validation protocol and result records bind their `CanonicalizationPolicy` reference and governed version fields. A policy-free protocol or result is `CONFIGURATION_INVALID`.

A `VALIDATED` protocol result is not itself a Tier 1 fact. It may create a typed proposal referencing the protocol result and supporting source artifacts. That proposal becomes decision-effective only through the Slice 4 ratification workflow.

### Predicate Templates

`DesignedValidationProtocol` acceptance criteria may use only `VALIDATION_PREDICATE_TEMPLATES_V1`:

- `REQUIRED_PRESENT(field_ref)`.
- `TERM_EQUALS(field_ref, expected_term_ref)`.
- `DECIMAL_EQUALS(field_ref, expected_decimal, unit_ref)`.
- `DECIMAL_IN_CLOSED_RANGE(field_ref, lower_decimal, upper_decimal, unit_ref)`.
- `TIMESTAMP_IN_CLOSED_INTERVAL(field_ref, start_timestamp, end_timestamp)`.
- `UNIT_COMPATIBLE(field_ref, unit_ref)`.
- `ALL_OF(predicate_refs...)`.

Every predicate template declares typed operands, required unit registry reference when units are present, canonicalization policy reference, missing-data behavior, and result enum `TRUE | FALSE | MISSING_DATA | INVALID_OPERAND | CONFIGURATION_INVALID`. `MISSING_DATA`, `INVALID_OPERAND`, or `CONFIGURATION_INVALID` cannot validate a protocol. `OR`, negation, arbitrary expressions, code execution, model-evaluated predicates, and user-defined operators are outside Build 1.

`DesignedValidationResult` binds the predicate-template version, unit registry, canonicalization policy, operand proposal/source refs, and each predicate result. Replay recomputes the result from those bound records.

### Exit Gate

- A protocol with missing required data returns explicit non-validation.
- Acceptance criteria are governed predicates, not model judgment.
- Acceptance criteria outside `VALIDATION_PREDICATE_TEMPLATES_V1` are `CONFIGURATION_INVALID`.
- A validation result cannot create a proposal from an observation unless the protocol allows that target type.
- A validation result cannot bypass proposal ratification.
- Protocol execution is replayable from bound source/proposal/result records.
- No protocol result qualifies a method or production process; Build 2 owns qualification.

### Deferred

Bench qualification design, statistical validity claims, production MSA expansion, and operational-mode elevation.

---

## 10. Slice 7 — Build 0 Engine Bridge

### Goal

Feed ratified Build 1 records into the existing Build 0 MIE engine without creating a second decision path.

### Scope

The bridge:

- Selects an exact capability profile.
- Selects exact source/proposal/ratification/observation/protocol versions.
- Assembles a Build 0-compatible `KnowledgeSnapshot`.
- Binds only actively ratified governed proposal versions into Tier 1 input rows.
- Binds unvalidated observation references in the Build 1 capture context only. Observation prose may be rendered outside the frozen Build 0 structured advisory payload and may not alter Build 0 route selection except through governed advisory-gap/context references explicitly allowed by Build 1.
- Emits explicit capture/advisory gaps for unknown/unsupported capabilities, unsupported source artifacts, missing parser, or missing ratification.
- Defers calibration/MSA eligibility decisions to the frozen Build 0 engine once a valid Build 0 request exists.

Every bridge refusal/advisory gap carries a minimal diagnostic payload: governed reason ID, affected target key or capability reference when applicable, conflicting active ratification heads when applicable, missing source/proposal/profile reference when applicable, and the next required governed record type. Diagnostics explain the fail-closed state; they do not create authority.

`CaptureGateResult` is a closed Build 1 result object, not a new MIE verdict. It records all capture-stage findings for one bridge attempt: capability resolution, scope check, identity resolution, evidence-locator ratifiability, active-value resolution, authority eligibility, observation containment, validation-protocol status, parser status, and proposal lineage. It may carry multiple findings.

Capture gate classification is closed and deterministic:

- Integrity failures, scope incompatibility, authority ineligibility, identity collision, unresolved identity for a requested Tier 1 target, non-ratifiable evidence for a ratified proposal, and active-value conflict are fail-closed `CaptureGateResult` states. They produce no Build 0 request.
- Missing ratification, unsupported/unknown/ambiguous capability, parser unavailable/unsupported/failed, and advisory-only observations are capture/advisory gaps. They produce no Tier 1 Build 0 value and no negative evidence.
- Missing calibration or MSA after a valid Build 0 request exists is not decided by Build 1. It is reported only through the frozen Build 0 calibration/MSA decision path and replay capsule.

Precedence is deterministic: integrity failure, scope incompatibility, authority ineligible, identity unresolved/collision, evidence locator not ratifiable, active-value conflict, missing ratification, capability unsupported/unknown/ambiguous, parser unavailable/unsupported/failed, then advisory-only observations.

Each decision-effective Build 1 value enters the Build 0 `KnowledgeSnapshot` as a governed row reference: proposal `logical_id`, `version_id`, `version_number`, `content_hash`, target key, typed canonical value, and `ProposalEvidenceV1` locator reference. Build 1 never injects a bare typed value into Build 0 without the governed proposal-version binding that produced it.

`BridgeAttemptRecord` is the Build 1-to-Build 0 persistence contract. Its closed lifecycle states are `CAPTURE_BOUND`, `BUILD0_REQUEST_CREATED`, `BUILD0_PERSISTED`, `FINALIZED`, `BUILD0_FAILED`, and `INTEGRITY_FAILURE`. Build 1 does not require Build 0 to share the caller's database transaction. If the frozen Build 0 engine exposes a pure in-process call over a caller-supplied unit of work with no independent commit, the implementation may store the Build 1 capsule and Build 0 run atomically in that shared unit of work. Otherwise Build 1 uses the narrowed-boundary fallback:

1. Commit the Build 1 capture records, `CaptureGateResult`, generated Build 0 request, request hash, and exact caller-supplied Build 0 `run_id`, `decision_id`, `case_id`, `audit_event_id`, `snapshot_id`, and `replay_id` as `CAPTURE_BOUND`.
2. Mark the exact Build 0 request and caller-supplied IDs as `BUILD0_REQUEST_CREATED` before invocation.
3. Before invoking Build 0, read the Build 0 store by the bound `run_id`. If the run exists, verify its stored request hash, output hash, replay capsule hash, and caller-supplied IDs match the immutable bridge request; then record `BUILD0_PERSISTED` from the existing run and finalize. A mismatch is `INTEGRITY_FAILURE`.
4. If no Build 0 run exists for the bound `run_id`, invoke the frozen Build 0 engine with the identical request and identical caller-supplied IDs.
5. On Build 0 success, record the Build 0 run reference and replay capsule hash as `BUILD0_PERSISTED`, then finalize the bridge attempt as `FINALIZED`.
6. On Build 0 duplicate-insert failure, re-read by the bound `run_id` and apply the same byte/hash verification in step 3. If the read-back verifies, finalize; if it does not verify or no run can be read, record `INTEGRITY_FAILURE`.
7. On any other Build 0 failure, record `BUILD0_FAILED` with error reason and leave the original request hash and caller-supplied IDs immutable.
8. A retry must use the same bridge attempt, Build 0 request hash, and caller-supplied IDs. A different request or different ID set under the same attempt is `INTEGRITY_FAILURE`.

`Build1BridgeReplayCapsule` binds the upstream capture-to-engine chain: capability profile, scope, source records and raw byte hashes, parse attempts, algorithm registry entries, proposal records, proposal evidence locators and derived hashes, identity recipe inputs/results, authority policy and authorization events, ratification events, observations, validation protocols/results, capture gate result, bridge attempt state, generated Build 0 request, and the existing Build 0 replay capsule reference when one exists. Algorithm ID is `BUILD1_EXACT_REPLAY_V1`.

### Exit Gate

- A complete ratified fixture reaches the existing Build 0 path unchanged.
- An equivalent unratified fixture stops before Tier 1.
- Unsupported capability appears as an advisory gap and never as negative evidence.
- Wrong-scope capability profile, missing authority policy, undefined context key, and active-value conflict each fail before Build 0 with diagnostics.
- A bridge retry with a changed Build 0 request hash fails closed.
- A bridge retry first reconciles by reading existing Build 0 records by caller-supplied ID; duplicate writes are never treated as successful upserts.
- Removing all model adapters changes no structured output.
- Build 0 replay remains byte-identical for runs created through the bridge, and `BUILD1_EXACT_REPLAY_V1` proves which exact upstream records produced the Build 0 request.

### Deferred

New Tier 1 verdict types, production Problem Solver orchestration, graph-wide population scoping, and production adapter scheduling.

---

## 11. Slice 8 — Replay and Evidence Closeout

### Goal

Close Build 1 with the same evidence discipline used for Build 0.

### Scope

Build 1 completion evidence binds:

- Exact source commit and governing-document hashes.
- Dependency lockfile digest and package inventory.
- PostgreSQL migrations and source digests.
- Collected test inventory and gate map.
- Canonical samples for source registration, parse attempts, algorithm registry entries, proposal, ratification, observation, validation protocol, bridge attempt, and Build 0 bridge.
- Cross-minor canonical equality for the published fixture corpus.
- JSON validation schemas and canonical wire schemas.
- Replay recipes for Build 1 record lifecycle paths.
- Golden vectors for Build 1 scope refs in Build 0 `BoundDecisionContext`, duplicate BridgeAttempt retry/read-reconciliation, duplicate proposal submission failure, and conflict-resolution history replay.

`BUILD1_EXACT_REPLAY_V1` verifies canonical bytes for source records, raw byte hashes, parse attempts, algorithm registry entries, proposal records, evidence locator derived hashes, source-local identity recipe inputs/outputs, authority/authorization/ratification state, active-value resolver policy and state hash, observation records, validation protocol/result records, capture gate result, bridge attempt state, Build 0 request, Build 0 replay capsule reference when present, and rendered-artifact separation when present. Tampering, missing records, missing raw bytes, derived locator drift, authority drift, active-value drift, bridge-attempt drift, or Build 0 request drift returns `INTEGRITY_FAILURE` without producing or modifying a MIE verdict.

### Exit Gate

- Generated evidence derives readiness from executed gates only.
- Build 1 records replay byte-identically across process restart.
- Tampered source/parse-attempt/algorithm-registry/proposal/ratification/authority/authorization/observation/protocol/capture-gate/bridge-attempt records fail closed.
- Missing capability/profile/source/proposal records produce explicit non-verdict/advisory gaps.
- Fail-closed results include actionable diagnostics without introducing authority or prose-only facts.
- Completion evidence is self-audited and claims no external attestation.

### Deferred

External attestation, production backup/recovery, production concurrency, cryptographic multi-party governance, and qualified deployment.

---

## 12. Requirement Ownership Matrix

| Requirement | Primary Slice | Governing Spec |
|---|---:|---|
| Governed capability profile | 1 | §§2.7, 2.11, 6, 18 |
| Closed evidence scope contract | 1 | §§2.7, 2.11, 6 |
| Build 0 evidence scope ref conformance | 1, 7 | §§7.1, 9, 12 |
| Unknown/unsupported capability gaps | 1 | §§2.7, 2.9, 18 |
| Raw source preservation | 2 | §§2.5, 11 |
| Content-hashed source identity | 2 | §§2.12–2.13 |
| Parser eligibility without silent failure | 2 | §§2.7, 11 |
| Streaming source-size enforcement | 2 | §§2.5, 12 |
| Atomic source-byte storage | 2 | §§2.5, 12 |
| Governed executable algorithm registry | 3 | §§2.12–2.13, 11 |
| Replay-bound parse attempts | 3 | §§2.5, 2.12–2.13, 11 |
| Typed proposed-value envelope | 3 | §§2.3–2.5, 6, 11 |
| Target key and context key definition | 3, 4 | §§2.4, 2.12, 11 |
| Decimal/canonicalization policy binding | 3, 8 | §§2.12–2.13 |
| Proposed record identity recipes | 3 | §§2.12–2.13, 6 |
| Replay-stable evidence locators | 3, 8 | §§2.5, 2.12–2.13, 11 |
| Evidence-location requirement | 3 | §§2.5, 11 |
| Model-disabled equivalence | 3, 7 | §§2.3, 2.12 |
| Human ratification event | 4 | §§2.4, 6, 11 |
| Minimal authority policy | 4 | §§2.4, 6, 11 |
| Snapshot-bound authorization events | 4 | §§2.4, 2.12, 11 |
| Bitemporal ratification eligibility | 4 | §§2.4, 2.12 |
| Active-value resolver policy and state hash | 4, 8 | §§2.4, 2.11, 2.12 |
| Active-value conflict detection | 4, 7 | §§2.4, 2.7, 2.12 |
| Rejection/correction append-only history | 4 | §§2.4, 11, 12 |
| Attributed observation containment | 5 | §§2.6, 11 |
| Observation Tier 2 surface without schema change | 5, 7 | §§2.6, 9 |
| Observation promotion discipline | 5, 6 | §§2.4, 2.6, 11 |
| Designed validation protocols and predicate templates | 6 | §11 |
| Deterministic validation results | 6 | §§2.7, 2.11, 11 |
| Build 0 bridge over ratified values only | 7 | §§2.4, 5, 7, 18 |
| Capture gate output contract | 7 | §§2.7, 9 |
| Deterministic bridge attempt state | 7, 8 | §§2.12–2.13, 12 |
| Bridge read-reconciliation retry | 7, 8 | §§2.12, 12 |
| Advisory gaps for missing capability/evidence | 7 | §§2.7, 2.9, 9 |
| Build 1 replay and evidence closeout | 8 | §§2.12–2.13, 12, 17 |

---

## 13. Build 1 Completion Gate

Build 1 is complete only when:

1. Every slice gate passes locally against PostgreSQL.
2. All Build 0 tests still pass unchanged.
3. Every new Build 1 record has a closed schema, semantic scalar types, explicit lifecycle enum, canonical list sort keys, validation-input schema, canonical-wire schema, and published non-schema semantic invariants.
4. Every Build 1 governed record binds its `CanonicalizationPolicy`; no timestamp, Decimal, governed ref, context key, or canonical hash uses an application default.
5. Every raw source record preserves exact received bytes, raw content hash, and provenance in one PostgreSQL transaction.
6. Source registration enforces governed max-byte limits while reading and never buffers unbounded payloads before rejection.
7. Every parser-derived proposal binds an exact `parse_attempt_ref`, and every parser/decoder/identity/canonicalization behavior resolves through a governed executable algorithm registry entry.
8. Every typed proposal cites a ratifiable `ProposalEvidenceV1` locator or remains proposal-only.
9. Every new proposed target identity resolves through an existing governed reference, caller-supplied identity, or `SOURCE_LOCAL_RECORD_IDENTITY_V1` with an evidence-backed `source_local_record_key`; unresolved or colliding identity fails closed.
10. Numeric proposed values bind Decimal precision, rounding, overflow, and canonical string policy before hashing, ratification, replay, or bridge assembly.
11. No value enters Tier 1 without active ratification resolved through governed authority policy, snapshot-bound authorization records, governed resolver policy, and verified active-value-state hash.
12. Unvalidated attributed observations are Tier-2-only and never change the frozen `AdvisoryDecision` schema.
13. Unknown/unsupported/wrong-scope capability produces explicit advisory gap, not inferred support or inferred absence.
14. Designed validation protocols use only `VALIDATION_PREDICATE_TEMPLATES_V1` and cannot qualify a method, production process, or bypass ratification.
15. Bridge retries use read-by-ID reconciliation against frozen Build 0 records; duplicate writes are never accepted as retry-equivalent success or upsert.
16. Removing model adapters changes no structured output.
17. Static scans find no vector implementation, SQLite fallback, domain constants, module-local scope logic, module-local identity recipes, or user-defined predicate engines in generic modules.
18. Build 1 replay detects tampering and missing source/proposal/ratification/authority/authorization/observation/protocol/capture-gate/bridge-attempt records and detects locator-derived hash drift.
19. Generated Build 1 completion evidence binds exact source commit, governing-document hashes, dependency lockfile, migrations, test inventory, gate map, validation and canonical-wire schemas, replay recipes, canonical samples, and cross-minor fixture equality.

Passing Build 1 does not qualify a lab, instrument, source system, method, MSA study, vendor parser, or production decision. It proves the capture and advisory layer can preserve provenance, propose typed records, enforce ratification, contain observations, and feed the deterministic Build 0 engine without weakening the firewall.

---

## 14. Explicitly Deferred

- SpaceX-specific LIMS, QMS, historian, or vendor instrument integration.
- Vendor-native adapters without real lawful sample files and expected-output fixtures.
- Direct instrument-emitted Tier 1 authority without ratification.
- External content-addressed source storage and large-object production hardening.
- PDF/OCR/image-region ratification without a replay-bound parser/renderer/OCR toolchain.
- Fuzzy entity resolution, near-duplicate detection, and cross-source identity merge workflows.
- General user-defined predicate engines.
- Production RBAC, e-signature, QMS record-of-record semantics, retention, backup/recovery, and tamper-evidence policy.
- Production concurrency and distributed workers.
- Qualification of thresholds, MSA studies, methods, parsers, instruments, or operational mode.
- Material/lot genealogy, process drift, FRACAS, spec compliance, and Problem Solver orchestration.
- External attestation.

---

## 15. ORACLE Review Questions

ORACLE should answer these questions against this plan and v0.4.20:

1. Does Build 1 v0.5 implement the existing v0.4.20 Build 1 contract, or does it accidentally introduce new architecture?
2. Are any Build 1 slices attempting Build 2 qualification or Build 3 production concerns too early?
3. Does the plan preserve the Build 0 firewall: no unratified value, model output, missing capability, or unvalidated observation can enter Tier 1?
4. Are the proposed record types sufficient to preserve source provenance, typed proposals, target/context keys, proposed identity, ratification, authority policy, authorization events, observations, validation predicates, capture-gate results, and replay?
5. Does any gate rely on hidden defaults, magic values, vectors, model authority, SQLite fallback, or vendor assumptions?
6. Is the "choose your tools" capability profile deterministic enough to proceed before knowing a specific lab's equipment list?
7. What is the smallest correction that would make this plan implementation-ready without pulling Build 2/3 work into Build 1?

Findings should cite the exact plan section and governing spec section, classify severity as `BLOCKER|MAJOR|MINOR|NIT`, and distinguish true contradictions from preferences or deferred production work.
