# GPTL MIE Build 1 Plan
## Capability-Profiled Capture & Advisory Contract — v0.2

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20

**Status:** Draft after ORACLE session `20260623-040533`; not an implementation freeze packet

**Build 0 dependency:** Build 0 is frozen by `GPTL_ORACLE_BUILD0_CLOSEOUT_REVIEW_v1.6.md`. Build 1 extends the frozen deterministic spine; it does not reopen Build 0 architecture, verdict semantics, replay, storage, canonicalization, or MSA/calibration gates.

**Operational boundary:** Build 1 remains `RESEARCH_ONLY`, non-dispositional, and not a QMS, quality, flight, or engineering record of record. It may create governed source, proposal, ratification, observation, and validation-protocol records. It does not qualify methods, instruments, MSA studies, vendor parsers, thresholds, process controls, or production actions.

**v0.2 review closeout:** resolves the Build 1 plan defects from ORACLE session `20260623-040533`. Direct instrument-emitted Tier 1 authority is deferred; Build 1 treats instrument/parser output as source-backed proposal material that still requires ratification before Tier 1. Active-value selection is defined by a target key and bind-time head resolution rather than an overclaimed database uniqueness constraint. Capability-profile scope checks, minimal authority policy, correction workflow, observation/protocol promotion through ratification, source-byte storage atomicity, raw-byte hashing, and fail-closed diagnostics are now explicit.

---

## 1. Purpose

Build 1 turns the v0.4.20 Build 1 paragraph into executable vertical slices:

> Source registration and evidence-grounded proposals; human validation/ratification; governed designed-validation protocols; attributed-observation ingestion (`UNVALIDATED`, Tier-2-only); deterministic custom lexical Tier 2 retrieval; optional Bouncer and renderer adapters. Vendor-specific instrument adapters MAY begin here only from real, legally usable source files and MUST preserve the raw artifact and provenance.

The core product question is:

**How do we take messy real-world manufacturing/lab data, preserve provenance, propose typed governed records, let a human validate or ratify them, and feed only governed values into the existing Build 0 engine?**

Build 1 is not new territory. It implements the original platform intent in §§2.3–2.7, §6, §11, and §18:

- Models translate or propose; they do not decide.
- Raw source artifacts are preserved and content-hashed.
- Proposed values are not authoritative.
- Ratification is explicit, actor-bound, bitemporal, and append-only.
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
- Build 1 source bytes are stored in PostgreSQL with their source record in the same transaction. External content-addressed storage is deferred until a production storage profile is specified.
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
    source_artifacts.py     raw source registration and content-hash contracts
    proposals.py            typed proposed-value envelope and validation states
    authority.py            minimal governed actor/role/action policy contracts
    validation.py           designed-validation protocol contracts
    observations.py         attributed-observation contracts
    ratification.py         Build 1 ratification workflow over proposed values
    persistence.py          existing append-only PostgreSQL store, extended by migrations
  mie/
    capture_service.py      Build 1 source/proposal/ratification orchestration
    build1_bridge.py        snapshot assembly into existing Build 0 MIE service paths
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
  GPTL_BUILD1_PLAN_v0.2.md
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
- Required calibration/MSA evidence types for each declared tool/method class.
- Explicit unsupported and unknown capabilities.
- Effective and expiration timestamps.
- Owner and evidence references.

A Build 1 run binds exactly one capability-profile version by complete governed reference. The profile's evidence scope must match the run scope, source-artifact scope, proposal scope, and any Build 0 snapshot scope assembled from it. A wrong-but-explicit profile is still rejected if its scope, owner, or active lifecycle state is incompatible with the run.

### Exit Gate

- A profile with no declared capability cannot silently allow intake.
- Unknown and unsupported capabilities are distinct states.
- Missing capability produces a typed advisory gap, never a guessed source path.
- Capability lists are canonical, unique, and order-independent.
- Scope mismatch, inactive lifecycle state, missing owner, or missing authority policy fails before source/proposal selection.
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
- Raw payload bytes stored in PostgreSQL and the SHA-256 hash of the exact received bytes.
- Byte length, media type, and optional filename as metadata outside the raw-byte hash.
- Submitted filename or external identifier as non-authoritative metadata.
- Source class and claimed origin.
- Submitter, received time, asserted source time when available.
- Evidence scope and capability-profile reference.
- Parser eligibility state: `UNPARSED`, `PARSER_UNAVAILABLE`, `PARSER_UNSUPPORTED`, `PARSER_READY`, `PARSER_FAILED`.

Build 1 source registration is one PostgreSQL transaction: insert the source record, raw bytes, hash metadata, audit event, and any parser-eligibility record together, then verify the stored bytes against the recorded hash before commit visibility. A failure commits neither row nor bytes. Raw source bytes are not canonicalized before hashing; newline normalization, text decoding, OCR, and parser cleanup produce separate proposal records that cite the raw artifact.

### Exit Gate

- Identical bytes produce identical content hashes.
- Different metadata over identical bytes does not change raw content hash.
- Text and binary artifacts are hashed as exact bytes received, not as canonicalized text.
- A parsed/proposed record cannot exist without a registered raw source.
- Unsupported source class becomes explicit advisory gap.
- Failed parser does not mutate or delete the source artifact.
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
- Proposed target key: target record type, target logical ID, target schema version, field path, and `context_key`.
- Proposed typed value with unit and canonical timestamp policy where applicable.
- Evidence location in the source artifact: page, row, column, cell, byte span, image region, or line range.
- Proposal method: deterministic parser, manual entry, model-assisted proposal, or external import.
- Validation state: `PROPOSED`, `VALIDATION_FAILED`, `READY_FOR_RATIFICATION`, `REJECTED`, `SUPERSEDED`.
- Validation errors with governed reason IDs.

`context_key` is the canonical object containing every schema-declared dimension needed to distinguish multiple values for the same target field. Examples include sample side, measurement replicate, process step, parameter channel, specimen ID, or condition set. If the target schema declares no disambiguating dimensions, `context_key` is the explicit empty object. The target schema owns the allowed keys, value types, and canonical sort order. Unknown, missing, extra, or non-canonical context dimensions make the proposal invalid rather than being collapsed into the same target or split into ungoverned fragments.

### Exit Gate

- Unknown units, malformed timestamps, ambiguous terms, or unsupported field paths fail validation.
- A proposal without evidence location cannot be ratified.
- A proposal without a valid target key cannot be ratified.
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
- Ratifying actor, role, and authority-policy reference.
- Decision: `RATIFIED`, `REJECTED`, `CORRECTION_REQUESTED`, or `SUPERSEDED`.
- Effective time and recorded time.
- Evidence references and optional reviewer note as non-authoritative prose.
- Optional superseded ratification-event reference.

`AuthorityPolicy` is the minimal Build 1 authority model. It declares actors or actor groups, roles, permitted actions, governed scope, target record classes, separation-of-duties requirements, effective/expiration times, and evidence references. Build 1 does not impose a universal dual-actor rule. A single-actor research lab may ratify only when the bound authority policy explicitly allows the same actor for the action and scope. If the policy requires independence, the actor who authored the proposal, executed the protocol, or authored the observation cannot ratify the resulting value.

`ProposalRatificationEvent` is the only event that makes a value decision-effective for Tier 1 in Build 1. Protocol results and attributed observations may produce new typed proposals, but those proposals still require ratification. There is no separate promotion event with independent authority semantics.

Active-value resolution is computed at snapshot-bind time from the exact ratification event set in the snapshot. For each target key:

1. Select events whose proposal hash verifies, authority policy is active, scope matches the run, `effective_at <= as_of_time`, and `recorded_at <= as_of_time`.
2. Remove events superseded by another eligible event.
3. `REJECTED`, `CORRECTION_REQUESTED`, and `SUPERSEDED` events cannot produce an active value.
4. Zero active `RATIFIED` heads means no Tier 1 value for that target key.
5. Exactly one active `RATIFIED` head is the decision-effective value.
6. More than one active `RATIFIED` head for the same target key is `ACTIVE_VALUE_CONFLICT` and fails closed before Build 0.

PostgreSQL enforces immutable event identity and duplicate primary keys; it does not claim to prove every bitemporal active-head uniqueness question with a static constraint. Build 1 write transactions use the single-writer persistence lane, and bind-time active-value resolution is the authoritative conflict check.

`CORRECTION_REQUESTED` is terminal for the proposal version it references. The corrected content is submitted as a new `TypedValueProposal` with `corrects_proposal_ref`; historical rejection/correction events remain visible and replayable.

### Exit Gate

- Ratification verifies the proposal content hash before eligibility.
- A later-recorded backdated ratification affects only later runs whose `as_of_time` includes it.
- Duplicate active ratification heads for the same target key fail closed with `ACTIVE_VALUE_CONFLICT`.
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
- Named source or role, recorded actor, timestamp, and production context reference when available.
- Validation state: `UNVALIDATED`, `UNDER_REVIEW`, `PROMOTED_BY_PROTOCOL`, `REJECTED`, `SUPERSEDED`.
- Evidence scope, source artifact reference when available, and confidence-free metadata.
- Tier 2 visibility policy.

### Exit Gate

- `UNVALIDATED` observations can appear only in Tier 2 advisory context.
- No observation text can satisfy a Tier 1 evidence requirement.
- Promotion requires a governed validation protocol result or corroborating governed evidence that creates a typed proposal; that proposal still requires a `ProposalRatificationEvent`.
- Advisory output must label the observation as attributed and unvalidated.
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
- Required method/tool capability and calibration/MSA prerequisites.
- Acceptance criteria as governed deterministic predicates.
- Required actor authority and separation-of-duties rule.
- Result schema and allowed terminal states.

`DesignedValidationResult` captures:

- Protocol reference.
- Collected source artifacts and typed values.
- Predicate evaluation results.
- Reviewer/authority event.
- Terminal state: `VALIDATED`, `NOT_VALIDATED`, `INCONCLUSIVE`, or `INVALID_PROTOCOL_EXECUTION`.

A `VALIDATED` protocol result is not itself a Tier 1 fact. It may create a typed proposal referencing the protocol result and supporting source artifacts. That proposal becomes decision-effective only through the Slice 4 ratification workflow.

### Exit Gate

- A protocol with missing required data returns explicit non-validation.
- Acceptance criteria are governed predicates, not model judgment.
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
- Passes only actively ratified typed values into Tier 1.
- Passes unvalidated observations only to Tier 2 advisory context.
- Emits explicit advisory gaps for unknown/unsupported capabilities, unsupported source artifacts, missing parser, missing ratification, missing calibration, or missing MSA.

Every bridge refusal/advisory gap carries a minimal diagnostic payload: governed reason ID, affected target key or capability reference when applicable, conflicting active ratification heads when applicable, missing source/proposal/profile reference when applicable, and the next required governed record type. Diagnostics explain the fail-closed state; they do not create authority.

### Exit Gate

- A complete ratified fixture reaches the existing Build 0 path unchanged.
- An equivalent unratified fixture stops before Tier 1.
- Unsupported capability appears as an advisory gap and never as negative evidence.
- Wrong-scope capability profile, missing authority policy, undefined context key, and active-value conflict each fail before Build 0 with diagnostics.
- Removing all model adapters changes no structured output.
- Build 0 replay remains byte-identical for runs created through the bridge.

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
- Canonical samples for source registration, proposal, ratification, observation, validation protocol, and Build 0 bridge.
- Cross-minor canonical equality for the published fixture corpus.
- JSON validation schemas and canonical wire schemas.
- Replay recipes for Build 1 record lifecycle paths.

### Exit Gate

- Generated evidence derives readiness from executed gates only.
- Build 1 records replay byte-identically across process restart.
- Tampered source/proposal/ratification/observation/protocol records fail closed.
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
| Unknown/unsupported capability gaps | 1 | §§2.7, 2.9, 18 |
| Raw source preservation | 2 | §§2.5, 11 |
| Content-hashed source identity | 2 | §§2.12–2.13 |
| Parser eligibility without silent failure | 2 | §§2.7, 11 |
| Atomic source-byte storage | 2 | §§2.5, 12 |
| Typed proposed-value envelope | 3 | §§2.3–2.5, 6, 11 |
| Target key and context key definition | 3, 4 | §§2.4, 2.12, 11 |
| Evidence-location requirement | 3 | §§2.5, 11 |
| Model-disabled equivalence | 3, 7 | §§2.3, 2.12 |
| Human ratification event | 4 | §§2.4, 6, 11 |
| Minimal authority policy | 4 | §§2.4, 6, 11 |
| Bitemporal ratification eligibility | 4 | §§2.4, 2.12 |
| Active-value conflict detection | 4, 7 | §§2.4, 2.7, 2.12 |
| Rejection/correction append-only history | 4 | §§2.4, 11, 12 |
| Attributed observation containment | 5 | §§2.6, 11 |
| Observation promotion discipline | 5, 6 | §§2.4, 2.6, 11 |
| Designed validation protocols | 6 | §11 |
| Deterministic validation results | 6 | §§2.7, 2.11, 11 |
| Build 0 bridge over ratified values only | 7 | §§2.4, 5, 7, 18 |
| Advisory gaps for missing capability/evidence | 7 | §§2.7, 2.9, 9 |
| Build 1 replay and evidence closeout | 8 | §§2.12–2.13, 12, 17 |

---

## 13. Build 1 Completion Gate

Build 1 is complete only when:

1. Every slice gate passes locally against PostgreSQL.
2. All Build 0 tests still pass unchanged.
3. Every new authoritative record has a closed schema and canonical wire contract.
4. Every raw source record preserves exact received bytes, raw content hash, and provenance in one PostgreSQL transaction.
5. Every typed proposal cites exact source evidence location.
6. No value enters Tier 1 without active ratification resolved through a governed authority policy.
7. Unvalidated attributed observations are Tier-2-only.
8. Unknown/unsupported/wrong-scope capability produces explicit advisory gap, not inferred support or inferred absence.
9. Designed validation protocols are governed deterministic records and cannot qualify a method, production process, or bypass ratification.
10. Removing model adapters changes no structured output.
11. Static scans find no vector implementation, SQLite fallback, or domain constants in generic modules.
12. Build 1 replay detects tampering and missing source/proposal/ratification/authority/observation/protocol records.
13. Generated Build 1 completion evidence binds exact source commit, governing-document hashes, dependency lockfile, migrations, test inventory, gate map, schemas, canonical samples, and cross-minor fixture equality.

Passing Build 1 does not qualify a lab, instrument, source system, method, MSA study, vendor parser, or production decision. It proves the capture and advisory layer can preserve provenance, propose typed records, enforce ratification, contain observations, and feed the deterministic Build 0 engine without weakening the firewall.

---

## 14. Explicitly Deferred

- SpaceX-specific LIMS, QMS, historian, or vendor instrument integration.
- Vendor-native adapters without real lawful sample files and expected-output fixtures.
- Direct instrument-emitted Tier 1 authority without ratification.
- External content-addressed source storage and large-object production hardening.
- Production RBAC, e-signature, QMS record-of-record semantics, retention, backup/recovery, and tamper-evidence policy.
- Production concurrency and distributed workers.
- Qualification of thresholds, MSA studies, methods, parsers, instruments, or operational mode.
- Material/lot genealogy, process drift, FRACAS, spec compliance, and Problem Solver orchestration.
- External attestation.

---

## 15. ORACLE Review Questions

ORACLE should answer these questions against this plan and v0.4.20:

1. Does Build 1 v0.2 implement the existing v0.4.20 Build 1 contract, or does it accidentally introduce new architecture?
2. Are any Build 1 slices attempting Build 2 qualification or Build 3 production concerns too early?
3. Does the plan preserve the Build 0 firewall: no unratified value, model output, missing capability, or unvalidated observation can enter Tier 1?
4. Are the proposed record types sufficient to preserve source provenance, typed proposals, target/context keys, ratification, authority policy, observations, validation protocols, and replay?
5. Does any gate rely on hidden defaults, magic values, vectors, model authority, SQLite fallback, or vendor assumptions?
6. Is the "choose your tools" capability profile deterministic enough to proceed before knowing a specific lab's equipment list?
7. What is the smallest correction that would make this plan implementation-ready without pulling Build 2/3 work into Build 1?

Findings should cite the exact plan section and governing spec section, classify severity as `BLOCKER|MAJOR|MINOR|NIT`, and distinguish true contradictions from preferences or deferred production work.
