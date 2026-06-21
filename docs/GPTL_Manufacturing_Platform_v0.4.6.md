# GPTL Manufacturing Intelligence Platform
## Architecture Baseline and MIE Build 0 Contract — v0.4.6

**Author:** Joe Wilde, BoundState AI LLC
**Status:** **OWNER-RATIFIED ARCHITECTURE BASELINE; RESEARCH-ONLY BUILD CONTRACT.** This document is the governing architecture and the implementation contract **for the MIE Build 0 wedge only** (§§5–9, §18). All [HORIZON] modules and the domain-neutral GPTL contract *names* in this document are architecture-baseline intent, not field-level implementation contracts, and are explicitly marked as such. Build 0 is deterministic and audit-reconstructable but not qualified for production reliance. Supersedes v0.3, v0.4, the ORACLE-generated v0.4.1/v0.4.2 drafts, v0.4.3, v0.4.4, v0.4.5, and prior BoundState GPTL/MIE/SENTINEL architectural statements.
**Self-contained:** defines the system from first principles; requires no external context.

> **Change basis (v0.3 → v0.4):** closes ten adversarial-review findings. The load-bearing six: numeric determinism via `Decimal` (§2.12, §8, §9); **order-independent evidence aggregation** (§8.7 — scoring no longer depends on discriminator order); production-context-graph and core contracts re-scoped honestly as architecture baseline (§1.5, §3, §6); typed closed-schema outputs replacing open dicts/strings (§9); completeness language replaced with bounded-catalog language throughout (§2.9, §8.8, §9); and **the foundational architecture resolved — shared substrate, multiple reasoning engines; MIE is the first *diagnostic engine*, not an Authority Pack** (§1.3, §4). Plus: advisory penalties removed from Build 0 (§8.4); Problem Solver presents options, never declares action "justified" (§13.5); expanded permutation/edge-case test classes (§17).

> **Change basis (v0.4 → v0.4.2):** incorporates the accepted ORACLE findings: disjoint verdict/refusal/advisory output kinds; canonical serialization and hashing; immutable logical-record/version identity; snapshot-bound supersession; class-scoped MSA eligibility; governed applicability predicates and attestations; authoritative/display separation; a typed Tier 2 output; governed meta-approval records; and explicit `RESEARCH_ONLY` Build 0 operation.

> **Change basis (v0.4.2 → v0.4.3):** closes the final execution-level gaps found during human verification. Applicability now returns four states rather than `bool`; missing context cannot silently remove a candidate; precedence is restricted to an explicit selection group; the predicate AST can represent range bounds; candidates without sufficient evidence remain `OPEN_UNASSESSED` and cannot be ruled out; authoritative identifiers/references use constrained types rather than comments over open strings; the shared-substrate/bounded-engine amendment is owner-ratified; and synthetic fixtures, instrument adapters, and production qualification are separated explicitly.

> **Change basis (v0.4.3 → v0.4.4):** binds every MSA qualification and snapshot-bound decision to a governed evidence scope. Synthetic MSA can qualify only an isolated `TEST_FIXTURE` scope, always forces `RESEARCH_ONLY`, and can never satisfy a bench, vendor, company, or production-scoped run. This closes the test-fixture qualification gap without weakening the MSA gate.

> **Change basis (v0.4.4 → v0.4.5):** owner decision replaces the Build 0 SQLite profile with PostgreSQL. Build 0 now uses transactional PostgreSQL persistence, database-enforced append-only records, forward-only migrations, and deterministic custom lexical scoring. PostgreSQL text search may accelerate bounded lookup only when equivalence tests prove it cannot change canonical membership or ordering.

> **Change basis (v0.4.5 → v0.4.6):** closes the Slice 2 safe-refusal review without overloading valid candidate evidence states. Runtime-invalid applicability now emits typed candidate configuration issues carrying the exact evaluation, error code, and evidence. Ratification verifies value integrity before active-state resolution, is re-evaluated from the event set bound into the snapshot, and requires decision-effective events to be both effective and recorded by the run's explicit `as_of_time`; later-recorded backdated events affect later runs but cannot rewrite historical eligibility.

Snapshot-bound output records written under this revision use schema version `gptl.slice2.v2`. Readers MUST continue to verify and load immutable `gptl.slice2.v1` records; historical payloads are never rewritten to the new schema.

---

## 0. Normative Language and Scope

**MUST / MUST NOT / SHALL / SHALL NOT / SHOULD / MAY** are normative. **[OWNER DECISION]** = author-ratified. **[BENCH-OPEN]** = requires empirical data; cannot be closed by specification. **[HORIZON]** = architecture-baseline intent, not near-term build, not claimed buildable now.

This document does not certify any part of the platform for laboratory, QMS, regulatory, or flight use. The platform is a **non-dispositional advisory system**; a responsible human owns every engineering determination. Exports of any decision or rendered artifact MUST carry a non-record-of-record marker. The platform implements no e-signature or QMS record-of-record semantics; those controls are outside Build 0.

---

## 1. What This Platform Is

### 1.1 The Problem
A serious materials/production operation generates a large, fragmented data pile — lab results, instrument outputs, continuous process/sensor streams, material-lot genealogy, part/serial records, equipment logs, operator/environment records, nonconformance histories, specifications, and a large body of undocumented experiential knowledge ("vibes," tribal knowledge). The data and decent tools exist. **What does not exist is a system that turns the pile into evidence-backed action for solving production problems** — without fabricating, without laundering tribal knowledge into false fact, and without making the engineering decision for the human.

### 1.2 GPTL and the Eight Questions
**GPTL — General Purpose Translation Layer.** No other expansion is valid. The reusable architecture and contract set for translating human questions and governed domain knowledge into bounded, evidence-linked, auditable intelligence. Not a chatbot, model, vector index, or database product. Central method — **negative selection**:

> Define the valid domain and eliminate what cannot satisfy it. Reason only over what remains. Refuse when the governed evidence cannot support a conclusion. Where a negative result is reported, prove knowledge of the negatives that could exist — never claim their absence.

For any production problem the platform answers eight questions: (1) what changed; (2) what population is affected; (3) what explanations are impossible; (4) which hypotheses remain; (5) what evidence supports each (cited to governed rows); (6) what to check next; (7) what containment/corrective action the evidence *supports for human approval* (and what is not yet supported); (8) what remains unknown (the surfaced dark space).

### 1.3 Architecture: Shared Substrate, Bounded Reasoning Engines [OWNER DECISION — RATIFIED]

The prior "single engine + Authority Packs" framing was a simplification that does not survive contact with what different domains actually *compute*. There are three layers:

```
                         GPTL PLATFORM
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1 — SHARED SAFETY SUBSTRATE                                    │
│   invariants (§2) · governed relational store · BSMS retrieval       │
│   primitives · provenance · content-hashed snapshots · production    │
│   context graph · Authority Pack contract format · refusal taxonomy  │
│   (ONE substrate. ONE bouncer framework. ONE citation format.        │
│    ONE provenance model. This is the anti-sprawl core.)              │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 2 — REASONING ENGINES (a small, bounded set, by COMPUTATION)   │
│   • Retrieval Engine   — BSMS retrieve-and-cite, or refuse           │
│       (for lookup/compliance domains: materials compatibility,        │
│        PFAS liability, clause review, Spec Compliance)               │
│   • Diagnostic Engine  — abductive hypothesis-elimination            │
│       (for diagnosis domains: Method Integrity [MIE], FRACAS)        │
│   Each engine is a generic, versioned algorithm. Engine count is     │
│   bounded by COMPUTATION TYPE, never by domain count.                │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 3 — AUTHORITY PACKS (domain knowledge; declare their engine)   │
│   Method Integrity Pack → Diagnostic Engine                          │
│   Spec Compliance Pack  → Retrieval Engine                           │
│   (a pack is data: schemas, rules, vocabularies, thresholds,         │
│    evidence — never code)                                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Why this and not "one engine":** an Authority Pack is *data*. MIE's diagnostic core — the hypothesis-elimination loop, the bounded support aggregation, the discriminator interrogation, the verdict gates — is *compute*, a different *algorithm* than retrieve-and-cite. A retrieval domain (Spec Compliance: find the governing clause, cite it, or refuse) and a diagnostic domain (MIE: reason abductively over competing failure modes) cannot run the same algorithm. They share the *substrate*, not the *engine*. **MIE is the first Diagnostic Engine; it consumes the Method Integrity Authority Pack.** That dissolves the pack-vs-sibling question: MIE is a diagnostic *engine* consuming a method-integrity *pack* — both, at different layers.

**This is not sprawl.** Anti-sprawl means *not* building five retrieval architectures, five bouncer frameworks, five citation formats. The multi-engine model has exactly one of each of those. It has a *minimal* set of reasoning engines distinguished by *what they compute* (retrieve vs diagnose), with every domain that retrieves sharing the retrieval engine and every domain that diagnoses sharing the diagnostic engine. Engine count grows with computation types (a small, bounded number), never with domains.

**Relationship to the locked BoundState Platform Principles ("Single Engine"):** that principle was written for retrieval domains (materials compatibility, PFAS, clause review), all of which correctly share the Retrieval Engine. MIE is the specific real-world case where "single engine" fails because diagnosis is not retrieval. This document satisfies the principles' amendment requirement and ratifies the replacement principle:

> **One shared safety substrate supports a closed, bounded set of reasoning engines selected by computation type. MIE uses the Diagnostic Engine. Adding an engine type requires an owner-ratified architecture revision.**

Code-sharing percentage does not determine engine boundaries; computation semantics and output contracts do. Shared mechanisms remain in the substrate. Engine-specific decision procedures remain isolated behind a common versioned engine contract.

### 1.4 The Module Roadmap
Packs/engines over the shared substrate and production context graph: **Method Integrity (MIE)** [Diagnostic Engine, first build, Parts 5–9]; Material/Lot Genealogy, Process Integrity & Drift, Nonconformance/FRACAS, Specification Compliance, and the Production Problem Solver orchestrator — all **[HORIZON]** (§13).

### 1.5 Scope Discipline (read before judging scope)
This document describes the **complete platform** as the architectural destination, so the foundation is laid with the whole structure in view. **It does not claim the whole platform is buildable in the near term.** The near-term buildable artifact is **MIE Build 0 only** (§18) — and *that* is specified at implementation-contract fidelity. Everything marked [HORIZON], and the domain-neutral GPTL contract *names* in §6, are architecture baseline. A reviewer MUST evaluate Build 0 for buildability and [HORIZON] items for architectural coherence only.

---

## 2. Non-Negotiable Invariants (govern every engine and pack)

### 2.1 Deterministic Decision Core
Given identical ratified input, pack version, knowledge snapshot, threshold table, engine policy version, engine version, and explicit `as_of_time`, an authoritative (Tier 1) decision MUST produce a **byte-identical canonical decision payload under §2.13.** Natural-language rendering need not be byte-identical and is never authoritative; it is a separate `RenderedArtifact` (§9).

### 2.2 No Vector Retrieval
FAISS, pgvector, Pinecone, Weaviate, Chroma, embedding similarity, nearest-neighbor search, hybrid vector ranking SHALL NOT participate in runtime candidate generation, evidence retrieval, record resolution, scoring, verdicts, discriminator selection, or pack publication/validation. Temperature zero does not make a model deterministic and does not make vector proximity evidence. Embeddings MAY be used only in a segregated research sandbox; sandbox output is untrusted and enters the governed system only through the same human validation/provenance process as any external suggestion. **Rationale:** vector retrieval fails open (returns the nearest thing, confidently, when nothing matches) — fabrication with a score. The platform fails closed: the governed row exists or it does not; absence is a first-class signal.

### 2.3 Models Are Translators, Not Decision-Makers
An LLM SHALL NOT create/remove an authoritative candidate, narrow the mandatory candidate universe, supply an unratified scoring field, set/modify any deterministic score, mark a discriminator result, satisfy a confirm test, issue/suppress/overturn a verdict, invent evidence/citations/identifiers/records, or publish/validate a pack. LLM roles: **translation** and **scoped tool-calling** with typed, validated, deterministic-effect tools.

### 2.4 Ratification Firewall
Only instrument-emitted or explicitly human-ratified typed values may enter an authoritative decision. Model output is a *proposal* until a named human ratifies it (append-only event linked to value, source text, actor, timestamp, pack version). An `LLM_PROPOSED` value is never silently promoted by timeout, reuse, navigation, or model agreement.

Value content hashes MUST verify before ratification eligibility or active-state hashing. A decision-effective event participates only when both `effective_at <= as_of_time` and `recorded_at <= as_of_time`. Eligibility MUST be resolved from the exact event set bound into the knowledge snapshot and MUST reproduce that snapshot's active-state hash. A later-recorded backdated event can affect a later run whose `as_of_time` includes it, but cannot alter historical eligibility.

### 2.5 Governed Evidence
Every authoritative factual input MUST resolve to a governed row with a stable primary key, source record, version, and evidence location. Free-text prose is not a fact store.

### 2.6 Attributed Observation vs Governed Fact [OWNER DECISION — tribal-knowledge discipline]
Experiential knowledge enters as an **`AttributedObservation`, not a fact**: the claim, named source, timestamp, attached production context, and `validation_state = UNVALIDATED`. It MAY inform Tier 2 advisory and MAY be surfaced as "a technician observed X (unvalidated, attributed to …)". It SHALL NOT enter an authoritative decision as fact until it passes the same validation/ratification process as any governed record and is promoted to a governed row. This lets the system ingest tribal knowledge without laundering it into false ground truth.

### 2.7 Fail Closed
Missing inputs/evidence, unresolved candidates, stale calibration, ambiguous identity, version mismatch, failed validation, unavailable storage, or engine errors MUST produce an explicit non-verdict or refusal — never a best guess.

### 2.8 No Probabilistic Theater
No model confidence, generic confidence, confidence intervals, pseudo-posteriors, or probability-like transforms of deterministic scores. Permitted deterministic quantities: scores, coverage, counts, measured uncertainty from a governed study — labeled as such, never as probabilities. No confidence interval in authoritative output. A probability field requires an owner-approved revision plus a separate statistical validity case.

### 2.9 Surface the Boundary, Never Claim Completeness [OWNER DECISION — dark-space discipline]
A product MUST NOT assert the absence of a condition it cannot enumerate. *"You can't prove a negative; you can prove you know about the negatives that could exist and bite you."* A negative result SHALL emit: (a) the falsifiable record of what was evaluated, with citations; (b) the named categories known to apply but not evaluated (the dark space); (c) an explicit non-exhaustiveness boundary. **No fraction over an unknown denominator.** A fraction whose denominator is a *known bounded set* (e.g., the published catalog) is permitted and MUST be named to make the denominator explicit (e.g. `evaluated_fraction_within_published_catalog`); a fraction implying coverage of *all possible* conditions is prohibited. All "completeness/complete" language referring to candidate sets is replaced platform-wide by "published/bounded" language (e.g. `published_candidate_set`).

### 2.10 Human Authority and Non-Disposition
Every output MUST set `dispositional = false`. The platform informs a human determination; it is not the determination, a quality record of record, or a substitute for organizational approval.

### 2.11 Zero Magic Values, Zero Hardcoded Domain Policy
Engine code is generic, versioned algorithms only. All domain behavior — thresholds, weights, required fields, vocabularies, failure classes, trust-model ordering, units/conversions, MSA criteria, refusal triggers, applicability predicates, selection groups, and evidence-sufficiency gates — MUST be explicit in a fully resolved, versioned pack or engine-policy artifact. Each decision-affecting numeric policy carries value, units, scope, derivation, governing source IDs, owner/approver, qualification state, validation-corpus version, validation result, and effective/expiration dates. Missing/ambiguous policy → pack publication fails, or runtime `CONFIGURATION_INVALID`. An unqualified numeric policy is exercisable only in `RESEARCH_ONLY` mode.

### 2.12 Determinism Contract (with numeric representation) [closes finding 1]
The authoritative engine is a pure deterministic function of (ratified_input, run_context, pack_version, knowledge_snapshot, engine_policy_version, engine_version, explicit_as_of_time). **All decision-affecting numeric values — scores, masses, thresholds, coverage, measured uncertainty — MUST use `Decimal` with a pack-declared precision (scale), rounding mode, overflow behavior, and canonical string serialization.** Floating-point (`float`/IEEE-754) SHALL NOT be used anywhere a value can affect a boundary decision or appear in the canonical payload. Boundary comparisons MUST be tested at the exact value and at the nearest representable values on both sides under the declared `Decimal` scale. Also prohibited in the authoritative path: random/unseeded algorithms; model output; wall-clock time not supplied as input; unordered query results or collection iteration; locale-dependent parsing; network retrieval outside the bound snapshot; result-changing retry; policy-altering environment variables; implicit latest-version resolution after a run begins. Canonical serialization is governed by §2.13.

### 2.13 Canonical Serialization and Hashing Contract
RFC 8785 (JSON Canonicalization Scheme) is the locked normative standard for Build 0. Before serialization, every string MUST be normalized to Unicode NFC. Object keys follow RFC 8785 ordering. Decision-affecting numerics are emitted as canonical `Decimal` strings, never JSON numbers. Timestamps use RFC 3339 UTC with `Z` and engine-policy-declared fixed fractional precision. Every authoritative list declares a semantic sort key in its schema; no list relies on insertion or query order. Absent optional fields are omitted unless the schema explicitly defines `null` as semantically distinct. SHA-256 is computed over the canonical UTF-8 bytes, and the hash algorithm identifier is stored with the snapshot. A self-hash field is never part of its own hash input: record `content_hash`, snapshot hash, and decision/advisory envelope hashes are computed over the explicitly named payload and then stored alongside it. Two conforming implementations MUST produce identical bytes and hashes for identical bound inputs.

---

## 3. The Production Context Graph (platform spine) [HORIZON contracts; schema-baseline]

The abstraction connecting the fragmented data. Every node/edge is a governed record with provenance. **[HORIZON]:** governing factory data deterministically requires temporal and identity contracts not yet specified at field level here — canonical identity/dedup, source precedence, units, **valid-time vs ingestion-time**, late-arriving events, corrections and supersession, sampling windows, missingness semantics, lineage, and decision invalidation. These are required before any graph-dependent pack can claim deterministic answers to "what changed?" or "what population is affected?" The graph here is a schema baseline, not an implementation contract. **MIE Build 0 does not depend on these deferred contracts; it operates only over explicit snapshot-bound record versions (§6.1, §7.7, §18).**

**Correction propagation and decision invalidation [HORIZON].** Source systems publish correction/supersession events against a `logical_id`; a lineage service identifies every `DecisionRun` that bound a superseded `version_id`; those runs receive an external lifecycle state `STALE_EVIDENCE` and are routed for re-evaluation. The original decision and snapshot remain immutable and replay unchanged. Build 0 handles a corrected input by creating a new record version and a new run over a new snapshot; it does not implement platform-wide propagation.

```
MaterialLot → Part/Serial → ProcessStep → Machine/Tool → Parameters+TimeSeries
  → Operator/Environment → Inspection/TestMethod(→MIE) → Result/Deviation
  → Disposition/Outcome → InstitutionalMemory(governed, post-validation)
```

Nodes: `MaterialLot, PartSerial, ProcessStepRecord, MachineToolRecord, ParameterSeries, OperatorEnvRecord, InspectionRecord, DispositionRecord, AttributedObservation`. Edges are typed, directional, governed; genealogy queries are FK/relational traversals, never vector similarity. Each node/edge record MUST carry (when implemented) canonical ID, source precedence, valid-time and ingestion-time, supersession pointer, and lineage — per the deferred contracts above.

---

## 4. GPTL Runtime: BSMS, and Engine Selection

**BSMS = Bouncer → Sonnet 1 → MAPTIS-equivalent store + reasoning engine → Sonnet 2.** GPTL is the architecture; BSMS the runtime pattern; Authority Packs the knowledge; the **reasoning engine** (Retrieval or Diagnostic, §1.3) is selected by the pack's declared computation type.

1. **Bouncer** — authn/authz; scope/injection detection; identity resolution against governed records; required-field completeness; typed-intake proposal; deterministic Tier 1/Tier 2 routing; **selects the reasoning engine from the pack's declared type.** NL input → `PROPOSED` typed query, cannot enter Tier 1 until ratified.
2. **Sonnet 1 (optional, non-authoritative)** — explain missing fields, propose a typed query plan, propose source-text→vocabulary mappings, order already-governed open discriminators for convenience, summarize bounded governed rows. For Tier 1 the engine independently constructs/executes the mandatory plan; Sonnet 1 cannot narrow the mandatory candidate/evidence set.
3. **MAPTIS-equivalent store + reasoning engine** — authoritative. Shared: relational store, published pack, exact/controlled-vocabulary resolver, candidate/evidence loader, citation + canonical-decision builder, append-only audit. Engine-specific: Retrieval Engine (retrieve-and-cite or refuse) **or** Diagnostic Engine (negative selection → signature match → bounded support aggregation → discrimination → verdict gates).
4. **Sonnet 2 (optional, non-authoritative)** — renders a persisted structured result as prose into a separate `RenderedArtifact` (§9), without modifying the authoritative payload.

The authoritative core has **no model dependency** and runs with all model adapters disabled.

---

## 5. Method Integrity (MIE) — the First Diagnostic Engine

MIE captures why lab methods work, how their data becomes trustworthy, and how their measurement chains fail; it investigates anomalous results and determines whether a known method artifact is supported, ruled out, or open. **MIE does not model material truth** and SHALL NOT convert "no known artifact found" into "real material behavior confirmed" (§2.9). In platform terms MIE is the `InspectionRecord → Result/Deviation` reasoning that lets the Problem Solver trust a test result as evidence at all.

### 5.1 Two Tiers
- **Tier 1 — Deterministic Investigation Verdict.** Available only when method identity resolves uniquely; required typed intake is complete and ratified; the pack version is published; calibration/run context is available or explicitly marked unavailable; the engine can load the **published candidate set** without an unresolved applicability result; **a qualified MSA study of an implemented method class applies (§7.6, hard gate)**; and no integrity/version check fails. Build 0 implements `QUANT_NONDESTRUCTIVE` only. Returns `METHOD_ARTIFACT`, `KNOWN_ARTIFACTS_EXCLUDED`, `INDETERMINATE`, `WITHIN_MEASUREMENT_VARIATION`, or `REFUSED`.
- **Tier 2 — Advisory Guided Investigation.** Applies when typed input is incomplete/unratified, applicability is `UNKNOWN`, no qualified MSA study exists, or the method's MSA class is not implemented by the running build. No verdict and no candidate support score. Emits a typed `AdvisoryDecision` (§9) with status `ADVISORY_NO_VERDICT`.

### 5.2 Tier 2 Retrieval Without Vectors
Order: exact method ID/alias; controlled-vocabulary token match; relational joins (method/observable/instrument/failure-class); deterministic custom lexical scoring over normalized tokens with published weights and stable governed-ID tie-break; optional model explanation over the bounded rows. PostgreSQL `tsvector`/trigram MAY accelerate bounded lookup only when equivalence tests prove that enabling or disabling the accelerator cannot change canonical membership or ordering. No match → `UNKNOWN_METHOD_OR_FAILURE_MODE`. All lexical policy is explicit governed records.

---

## 6. GPTL Core Data Contracts [HORIZON — names, not field-level; architecture baseline]

Domain-neutral records every GPTL implementation SHALL provide. **These are contract *names* at baseline fidelity; field-level schemas are specified per engine/pack as built.** `AuthorityPackVersion, SourceRecord, EvidenceRecord, ControlledTerm, ConstraintRule, EvidenceRequirement, TypedQueryProposal, RatificationEvent, DecisionRun, DecisionEvent, EvidenceCitation, RefusalRecord, PackReleaseRecord, AttributedObservation, AttestationEvent, GovernanceApprovalEvent.` Common properties: stable logical identity, immutable version identity, schema version, lifecycle state, provenance, content hash, created/validated actors, and effective timestamps. The MIE records (§7) and output (§9) are Build 0 implementation contracts.

### 6.1 Record Identity and Versioning Model
Every governed record uses one platform-wide model:

- `logical_id`: stable across revisions of the same logical record.
- `version_id`: immutable and unique per revision; never reused.
- `version_number`: monotonic integer within one `logical_id`.
- `content_hash`: SHA-256 over canonical record content (§2.13).
- `supersedes_version_id`: prior revision's `version_id`, absent for the first revision.

A revision creates a new `version_id` and increments `version_number` under the same `logical_id`; the prior version is never mutated. Citations carry `logical_id` plus `version_number`; snapshots additionally bind the exact `version_id` and `content_hash`. Supersession, deduplication, foreign-key references, and rollback operate on explicit identifiers, never timestamps or an implicit "latest" query.

---

## 7. MIE Records and the MSA Hard Gate

### 7.1 Common Executable Types
Build 0 schemas MUST use constrained semantic types. A comment describing a plain `str` as an ID, controlled term, canonical timestamp, decimal, or governed reference is not sufficient. The implementation SHALL define and validate at least these distinct types:

```python
OpaqueId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
NonNegativeInt = Annotated[int, Field(ge=0)]
LogicalId = NewType("LogicalId", OpaqueId)
VersionId = NewType("VersionId", OpaqueId)
FieldId = NewType("FieldId", OpaqueId)
TermId = NewType("TermId", OpaqueId)
UnitId = NewType("UnitId", OpaqueId)
TemplateId = NewType("TemplateId", OpaqueId)
EvidenceLocator = NewType("EvidenceLocator", OpaqueId)
CanonicalTimestamp = Annotated[
    str,
    StringConstraints(
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
    ),
    AfterValidator(validate_utc_timestamp_and_policy_precision),
]

class GovernedRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    logical_id: LogicalId
    version_id: VersionId
    version_number: NonNegativeInt
    content_hash: Sha256Hex
```

`validate_utc_timestamp_and_policy_precision` parses the timestamp strictly, rejects nonexistent calendar/time values, and verifies the fractional precision against the snapshot-bound engine policy supplied through validation context. The concrete implementation MAY use Pydantic custom scalar classes instead of `NewType`, but it MUST preserve these semantic distinctions and reject malformed values. Authoritative free text is prohibited. Human-readable prose belongs only in `RenderedArtifact` (§9).

### 7.2 Method, Variant, and Applicability
`MethodRecord` governs identity, aliases, category, measurement principle, calibration requirements, signal chain, preparation requirements, validity criteria, standards, method class, MSA class, owner, lifecycle, and revalidation interval. `MethodVariant` contains explicit field-level overrides; unspecified fields inherit. Failure modes merge by union unless a governed suppression record explicitly names the suppressed failure-mode version and supporting evidence.

Every `MethodFailureMode` and `MSAStudy` carries an `applicability_predicate`. Applicability is not executable code, SQL, or an open DSL. It is the following closed, JSON-serializable AST:

```python
class NumericOperand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["NUMERIC"]
    value: Decimal
    unit_id: UnitId

class EnumOperand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["ENUM"]
    value: TermId

ScalarOperand = Annotated[
    Union[NumericOperand, EnumOperand], Field(discriminator="kind")
]

class RangeOperand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    low: Decimal
    high: Decimal
    unit_id: UnitId
    low_bound: Literal["INCLUSIVE", "EXCLUSIVE"]
    high_bound: Literal["INCLUSIVE", "EXCLUSIVE"]

class EqualityComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["eq", "neq"]
    field_id: FieldId
    operand: ScalarOperand

class OrderedComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["lt", "lte", "gt", "gte"]
    field_id: FieldId
    operand: NumericOperand

class MembershipComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["in"]
    field_id: FieldId
    allowed_terms: list[TermId]

class RangeComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["range"]
    field_id: FieldId
    operand: RangeOperand

class PresenceComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    op: Literal["present", "absent"]
    field_id: FieldId

Comparison = Annotated[Union[
    EqualityComparison, OrderedComparison, MembershipComparison,
    RangeComparison, PresenceComparison,
], Field(discriminator="op")]

class ComparisonPredicate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["comparison"]
    comparison: Comparison

class AllPredicate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["all"]
    terms: list["Predicate"]

class AnyPredicate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["any"]
    terms: list["Predicate"]

class NotPredicate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["not"]
    term: "Predicate"

Predicate = Annotated[Union[
    ComparisonPredicate, AllPredicate, AnyPredicate, NotPredicate,
], Field(discriminator="kind")]

class ApplicabilityTruth(StrEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"

class ApplicabilityEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    truth: ApplicabilityTruth
    predicate_ref: GovernedRef
    missing_field_ids: list[FieldId]
    error_code: Literal[
        "TYPE_MISMATCH", "UNIT_MISMATCH", "UNKNOWN_FIELD",
        "INVALID_AST", "INVALID_RANGE",
    ] | None
    evidence_refs: list[GovernedRef]

class SelectionBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    selection_group_ref: GovernedRef
    precedence_rank: Decimal
```

Normative evaluation rules:

1. Context fields come from a closed governed registry. Numeric comparison converts both values through the snapshot-bound unit registry before comparison. Incompatible units are `INVALID`.
2. Missing context produces `UNKNOWN`, not `FALSE`. `all`, `any`, and `not` use Kleene three-valued logic; `INVALID` dominates and terminates evaluation.
3. `TRUE` includes the record. `FALSE` excludes it and records the predicate evaluation as evidence.
4. For a failure mode, `UNKNOWN` MUST NOT remove the candidate. It records the candidate as `APPLICABILITY_UNRESOLVED`, blocks `KNOWN_ARTIFACTS_EXCLUDED`, and routes the case to Tier 2 or `REFUSED{MISSING_REQUIRED_EVIDENCE}` according to the ratified intake state.
5. For an MSA study, `UNKNOWN` means no applicable study has been established and routes to `REFUSED{MSA_UNCHARACTERIZED}`; Tier 2 MAY also be emitted.
6. `INVALID` always returns `REFUSED{CONFIGURATION_INVALID}`. A runtime-invalid candidate is retained as a typed `CandidateConfigurationIssue` containing its candidate reference, complete applicability evaluation and error code, and governed evidence references; it is never mislabeled as a valid candidate evidence state. Publication-time type, unit, registry, or AST errors prevent pack publication.
7. `all.terms`, `any.terms`, and `allowed_terms` MUST be non-empty; membership terms MUST be unique; range `low` MUST NOT exceed `high`; and every recursive model MUST be rebuilt/resolved before pack validation. Empty or unresolved AST structures are publication errors.
8. `ApplicabilityEvaluation.error_code` is present if and only if `truth == INVALID`. `missing_field_ids` is non-empty if `truth == UNKNOWN` and empty otherwise. These invariants are schema-validated.

Applicability overlap is resolved only inside an explicit `SelectionBinding`. Records with different groups, or no binding, do not compete and all `TRUE` records remain applicable. Within one group, lower governed `precedence_rank` wins; a rank tie is a pack-publication error. The referenced selection-group record MUST include a governed rationale and evidence for why its members are alternatives. Precedence MUST NOT choose between distinct failure mechanisms merely because both apply.

Multiple failure modes may legitimately apply and remain separate candidates. Multiple MSA studies that could simultaneously apply to the same method/measurand/range/conditions MUST either share one explicit selection group or declare a governed combination contract. Build 0 supports selection, not MSA-study combination; overlapping ungrouped MSA studies are a pack-publication error.

### 7.3 Failure Modes, Signatures, and Observables
`MethodFailureMode` contains a governed mechanism term, failure class, typed signature features, discriminator references, confirm-test reference, rule-out-evidence-requirement reference, severity term, known-mask references, evidence, provenance, applicability predicate, optional selection group, and precedence rank when grouped. `SignatureFeature` references exactly one registered observable and declares expected typed value/range, unit, weight, and match operator. `ObservableRegistry` is the closed vocabulary shared by intake and signatures; unknown observables cannot enter Tier 1. `material_class` is a governed enumerated field, ratifiable and never model-inferred into scoring.

### 7.4 Instruments and Runs
`InstrumentRecord` governs identity, supported methods, quirks, and calibration state. `RunContext` references the instrument, method, variant, operator, run parameters, calibration state at run, sample context, and canonical timestamp. These are immutable governed records bound by `version_id` into the snapshot. Vendor-native raw files are source artifacts referenced by these records; vendor parser/adapters are not part of Build 0 (§18).

### 7.5 Discriminators and Confirm Tests
```python
class Discriminator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    discriminator_ref: GovernedRef
    observable_id: FieldId
    artifact_predicate: Predicate
    real_predicate: Predicate
    discriminating_power: Decimal

class DiscriminatorResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    result_ref: GovernedRef
    discriminator_ref: GovernedRef
    supersedes_version_id: VersionId | None
    outcome: Literal[
        "CONSISTENT_WITH_ARTIFACT", "CONSISTENT_WITH_REAL", "INCONCLUSIVE"
    ]
    observed_value_ref: GovernedRef | None
    answered_by_actor_id: OpaqueId
    answered_at: CanonicalTimestamp

class RuleOutEvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requirement_ref: GovernedRef
    required_discriminator_refs: list[GovernedRef]
    aggregation: Literal["ALL_CONSISTENT_WITH_REAL"]

class StructuredConfirmTest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["STRUCTURED"]
    predicate: Predicate
    required_evidence_types: list[TermId]

class HumanAttestedConfirmTest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["HUMAN_ATTESTED"]
    authorized_role_policy_ref: GovernedRef
    required_evidence_types: list[TermId]

ConfirmTest = Annotated[
    Union[StructuredConfirmTest, HumanAttestedConfirmTest],
    Field(discriminator="kind"),
]

class AttestationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    attestation_ref: GovernedRef
    failure_mode_ref: GovernedRef
    method_ref: GovernedRef
    attester_id: OpaqueId
    attester_role_id: TermId
    supporting_evidence: list[GovernedRef]
    attested_at: CanonicalTimestamp
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    supersedes_version_id: VersionId | None
```

Each failure mode references a `RuleOutEvidenceRequirement`; Build 0 rule-out requires every named discriminator to resolve `CONSISTENT_WITH_REAL`. The required list MUST be non-empty. A low support score alone never satisfies rule-out.

For a discriminator observation, exactly one of `artifact_predicate` or `real_predicate` may evaluate `TRUE`. If neither is true, the result is `INCONCLUSIVE`. If either is `UNKNOWN`, the result is `INCONCLUSIVE` with missing fields recorded. If both are true, or either is `INVALID`, the pack/run returns `CONFIGURATION_INVALID`; overlapping outcome predicates are also a pack-publication error when statically detectable.

`CONFIRMED` is unreachable without a passing structured confirm test or an active governed attestation. The attester role MUST be allowed by the snapshot-bound role policy. The attester MUST NOT be the author or approver of the governing failure-mode record. Revoked or superseded attestations cannot satisfy a confirm test.

### 7.6 MSA Hard Precondition [OWNER DECISION]
`MSAStudy` references method, measurand, range, conditions, study type, measured uncertainty, class-appropriate capability evidence, applicability predicate, optional selection group, precedence rank when grouped, qualification state, **qualification-scope reference**, effective time, and expiration time. One global Gage R&R rule is prohibited: `QUANT_NONDESTRUCTIVE` uses a governed Gage R&R contract; `DESTRUCTIVE` uses nested-design reproducibility; `QUALITATIVE` uses governed attribute agreement; `CONDITION_SENSITIVE` uses a per-condition uncertainty contract.

No qualified, applicable MSA study of a class implemented by the running engine **and valid for the run's bound evidence scope** means Tier 1 SHALL NOT issue an investigation verdict. It returns `RefusalDecision{verdict="REFUSED", refusal_type="MSA_UNCHARACTERIZED"}`; Tier 2 advisory MAY also run. Build 0 implements `QUANT_NONDESTRUCTIVE` only. Eligibility is earned per method; no application default bypass exists.

A synthetic MSA fixture MAY be qualified only inside an isolated governed `TEST_FIXTURE` evidence scope. That study can satisfy the gate only for a run bound to the identical scope and always forces `operational_mode = RESEARCH_ONLY`. It cannot satisfy a bench, vendor, company, or production-scoped run. Scope mismatch behaves as no applicable qualified study. This is test data isolation, not an MSA bypass.

### 7.7 Cases and Snapshots
`TriageCase` references intake, tier, run context, pack version, engine version, knowledge snapshot, MSA result, candidates, discriminator results, canonical result, actions, provenance, and non-dispositional state. `KnowledgeSnapshot` binds every exact governed `version_id` and `content_hash` used, plus engine policy, algorithms, unit registry, precision/rounding policy, serialization policy, lexical policy, and explicit `as_of_time`.

Governed records are immutable. Any correction creates a new `version_id` under the same `logical_id`; mutation of a published version is prohibited. The snapshot references specific versions only. A content-hash mismatch is tamper evidence and returns `INTEGRITY_FAILURE`. Replay never resolves an implicit latest version.

---

## 8. Deterministic MIE Pipeline (Diagnostic Engine)

### 8.0 Step 0 — Integrity and Tier Routing
Validate schema, actor, pack version, hashes, method identity, units, required fields, ratification status, and implemented MSA class; confirm a fully resolved pack with no missing policy; route deterministically; no runtime default injection.

### 8.1 Step 1 — Snapshot
Create `DecisionRun`; bind the immutable content-hashed `KnowledgeSnapshot`, including exact `version_id` references, before evaluation.

### 8.2 Step 2 — MSA Precondition (hard gate, §7.6)
Evaluate every potentially applicable study through §7.2. No qualified `TRUE` study, an `UNKNOWN` study with no established applicable alternative, or an unimplemented MSA class → `REFUSED{MSA_UNCHARACTERIZED}`; Tier 2 may run. `INVALID` → `REFUSED{CONFIGURATION_INVALID}`. A study applies and deviation is within its governed uncertainty → `WITHIN_MEASUREMENT_VARIATION`. A study applies and deviation exceeds uncertainty → proceed.

### 8.3 Step 3 — Published Candidate Set
Load every published failure mode in scope for the method and evaluate its applicability predicate (§7.2). Every `TRUE` candidate enters the `published_candidate_set`, subject only to scoped `SelectionBinding` resolution. Every `FALSE` exclusion records its governed predicate evaluation. An `UNKNOWN` candidate is recorded as `APPLICABILITY_UNRESOLVED`, remains inside the evaluated boundary, and blocks Tier 1 negative conclusions; it is never silently dropped. `INVALID` returns `CONFIGURATION_INVALID`. The set is bounded and named, never described as complete or all possible. Models cannot change it.

### 8.4 Step 4 — Deterministic Negative Selection
Apply hard impossibility rules; each elimination records the rule reference, exact input facts, evaluation, and evidence. Hard elimination is distinct from low support. Advisory penalties are not part of Build 0. Ordering of open candidates for display uses the schema-declared stable candidate key only.

### 8.5 Step 5 — Signature Match (`Decimal`)
```text
signature_match_score(m) = Σ_observed weight(f)·match(f) / Σ_observed weight(f)
signature_coverage(m)    = Σ_observed weight(f) / Σ_all-features weight(f)
```
All values are `Decimal`. Missing data lowers coverage and never creates a match or mismatch. Zero observed features means `signature_match_score = UNDEFINED`; unless a hard impossibility rule eliminates it, the candidate remains `OPEN_UNASSESSED` until the pack-required signature evidence is present. Discriminator observations are retained but do not manufacture a base score. The engine MUST NOT substitute an application default or configurable "neutral floor."

### 8.6 Step 6 — Evidence State and Initial Support
Each candidate receives one evidence state before aggregation:

```text
ELIMINATED          = a hard impossibility rule evaluated TRUE
OPEN_UNASSESSED     = signature score is undefined
EVALUABLE           = signature score is defined and required evidence policy is satisfied
APPLICABILITY_UNRESOLVED = applicability evaluated UNKNOWN
```

Only `EVALUABLE` candidates receive `candidate_support_0 = signature_match_score`. Build 0 has no expert prior, context modifier, or undefined-signature substitute. `OPEN_UNASSESSED` and `APPLICABILITY_UNRESOLVED` candidates cannot become `RULED_OUT` and block `KNOWN_ARTIFACTS_EXCLUDED`.

### 8.7 Step 7 — Discrimination: Order-Independent Aggregation

The v0.3 sequential update (`support += d·(1−support)` / `support −= d·support`) was **order-dependent** and is replaced. Discriminator results are aggregated **set-wise**, so the score is a function of *what evidence exists*, not *what order it arrived*:

```text
Collect ALL DiscriminatorResults for candidate m, then compute once:

  # commutative product over a SET → order-independent by construction
  artifact_mass(m) = 1 − Π over {results CONSISTENT_WITH_ARTIFACT} of (1 − d_k)
  real_mass(m)     = 1 − Π over {results CONSISTENT_WITH_REAL}     of (1 − d_k)
  # INCONCLUSIVE results contribute to neither mass; they affect coverage only

  candidate_support_score(m) = COMBINE(candidate_support_0(m),
                                       artifact_mass(m),
                                       real_mass(m))
```

- Each mass is a **commutative product over a set**, so it is independent of the order results were obtained — order independence is **structural**, not a consequence of stable sorting.
- `COMBINE` is evaluated **exactly once** over the aggregated masses (never incrementally), is a versioned/qualified deterministic `Decimal` function, and MUST be bounded to `[0,1]`.
- **Build 0 `COMBINE` candidate (RESEARCH_ONLY until qualified, §2.11):**
  `support = clamp01( candidate_support_0·(1 − real_mass) + artifact_mass·(1 − candidate_support_0) )`.
  This is bounded, deterministic, a pure function of the aggregated masses, and **invariant to discriminator order** by construction. The exact `COMBINE` form is `[BENCH-OPEN]`; the order-independence property is **normative and permanent**.
- Discriminator aggregation runs only for an `EVALUABLE` candidate. Discriminator evidence for an `OPEN_UNASSESSED` candidate is retained and cited but does not manufacture a base score; the case remains open until the pack's required signature evidence is present.
- Duplicate discriminator results are reduced by the explicit snapshot-bound supersession chain (`result_ref.version_id` / `supersedes_version_id`), never by timestamp or an implicit latest query. Contradictory results without a supersession relationship return an explicit integrity error. Results arriving after a run create a new run and snapshot; they never mutate replay.

### 8.8 Step 8 — Status and Verdict Gates
```text
ELIMINATED      = hard impossibility rule satisfied
OPEN_UNASSESSED = evidence state is not EVALUABLE
CONFIRMED       = EVALUABLE AND support ≥ tau_confirm
                  AND required coverage satisfied AND confirm test satisfied
RULED_OUT       = EVALUABLE AND support ≤ tau_ruleout
                  AND governed rule-out evidence requirement satisfied
CANDIDATE       = EVALUABLE and no terminal candidate status above applies
```
`evaluated_fraction_within_published_catalog = answered_high_power / total_high_power`; the denominator is the governed high-power discriminator set on applicable candidates, and "answered" excludes `INCONCLUSIVE`. The exact high-power threshold and rule-out evidence requirement are qualified pack policy. A score below a floor, by itself, is never rule-out evidence.

- **`METHOD_ARTIFACT`**: a confirmed dominant candidate (support ≥ `tau_verdict`, dominance margin ≥ `delta_dom` over the next evaluable candidate), required coverage, satisfied confirm test, and no unresolved applicability that could change dominance.
- **`KNOWN_ARTIFACTS_EXCLUDED`** (cited coverage record, not a determination of real behavior): every candidate in the `published_candidate_set` is explicitly `ELIMINATED` or `RULED_OUT`; no candidate is `OPEN_UNASSESSED` or `APPLICABILITY_UNRESOLVED`; `evaluated_fraction_within_published_catalog` meets the governed minimum; and the mandatory boundary fields are present (§9). It asserts only that the published catalog did not explain the anomaly after the recorded investigation.
- Otherwise **`INDETERMINATE`** with open discriminators and the facts to continue.

### 8.9 Step 9 — Canonical Result and Rendering
Build, canonically serialize, and persist the authoritative structured result first. Optional prose rendering occurs afterward into a separate non-authoritative `RenderedArtifact`; it cannot modify the decision.

---

## 9. Canonical Output Contract

All models use `extra="forbid"` and immutable values recursively. All numerics are `Decimal`. Authoritative maps are prohibited; governed keyed values use sorted typed arrays. Authoritative prose is prohibited.

```python
class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_type_id: TermId
    record_ref: GovernedRef
    evidence_location: EvidenceLocator

class GovernedDisplayValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["GOVERNED_REF"]
    value: GovernedRef

class TermDisplayValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["TERM_REF"]
    value: TermId

class DecimalDisplayValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["DECIMAL"]
    value: Decimal
    unit_id: UnitId | None

DisplayValue = Annotated[Union[
    GovernedDisplayValue, TermDisplayValue, DecimalDisplayValue,
], Field(discriminator="kind")]

class DisplayParam(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    key_id: TermId
    value: DisplayValue

class DisplayDirective(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    template_id: TemplateId
    params: list[DisplayParam]

class RenderedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: OpaqueId
    renderer_id: OpaqueId
    renderer_version: OpaqueId
    rendered_text: str                         # non-authoritative prose allowed here only
    generated_from_decision_hash: Sha256Hex
    non_record_of_record: Literal[True]

class CandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    applicability: ApplicabilityTruth
    evidence_state: Literal[
        "ELIMINATED", "OPEN_UNASSESSED", "EVALUABLE", "APPLICABILITY_UNRESOLVED"
    ]
    status: Literal[
        "ELIMINATED", "OPEN_UNASSESSED", "CANDIDATE", "CONFIRMED",
        "RULED_OUT", "APPLICABILITY_UNRESOLVED"
    ]
    signature_match_score: Decimal | None
    signature_coverage: Decimal
    candidate_support_score: Decimal | None
    evidence_refs: list[GovernedRef]
    rule_refs: list[GovernedRef]

class CandidateConfigurationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    applicability_evaluation: ApplicabilityEvaluation
    evidence_refs: list[GovernedRef]

class EvaluatedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    failure_mode_ref: GovernedRef
    terminal_status: Literal["ELIMINATED", "RULED_OUT"]
    discriminator_refs: list[GovernedRef]
    ruling_citations: list[Citation]

class KnownGap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    category_id: TermId
    why_unevaluated: DisplayDirective
    what_would_enable: DisplayDirective

class DecisionHeader(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: OpaqueId
    case_id: OpaqueId
    tier: Literal[1]
    dispositional: Literal[False]
    non_record_of_record: Literal[True]
    operational_mode: Literal["RESEARCH_ONLY", "QUALIFIED"]
    engine_id: OpaqueId
    engine_version: OpaqueId
    as_of_time: CanonicalTimestamp

class BoundDecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    context_kind: Literal["SNAPSHOT_BOUND"]
    pack_ref: GovernedRef
    engine_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    knowledge_snapshot_hash: Sha256Hex

class PreflightRefusalContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    context_kind: Literal["PREFLIGHT"]
    requested_pack_id: OpaqueId | None
    failure_stage_id: TermId

RefusalContext = Annotated[
    Union[BoundDecisionContext, PreflightRefusalContext],
    Field(discriminator="context_kind"),
]

class MIEDecisionBase(DecisionHeader):
    context: BoundDecisionContext
    method_ref: GovernedRef | None
    assessments: list[CandidateAssessment]
    citations: list[Citation]
    missing_field_ids: list[FieldId]
    what_would_change_this: list[DisplayDirective]
    required_human_action: DisplayDirective
    audit_event_ids: list[OpaqueId]

class MethodArtifactDecision(MIEDecisionBase):
    verdict: Literal["METHOD_ARTIFACT"]
    confirmed_candidate_ref: GovernedRef
    evaluated_fraction_within_published_catalog: Decimal
    confirm_evidence: list[Citation]

class KnownArtifactsExcludedDecision(MIEDecisionBase):
    verdict: Literal["KNOWN_ARTIFACTS_EXCLUDED"]
    artifacts_evaluated: list[EvaluatedArtifact]
    known_unevaluated_gaps: list[KnownGap]
    catalog_boundary: DisplayDirective
    evaluated_fraction_within_published_catalog: Decimal

class IndeterminateDecision(MIEDecisionBase):
    verdict: Literal["INDETERMINATE"]
    open_discriminator_refs: list[GovernedRef]

class WithinMeasurementVariationDecision(MIEDecisionBase):
    verdict: Literal["WITHIN_MEASUREMENT_VARIATION"]
    msa_study_ref: GovernedRef
    measured_uncertainty: Decimal
    uncertainty_unit_id: UnitId

class RefusalDecision(DecisionHeader):
    verdict: Literal["REFUSED"]
    refusal_type: RefusalType
    context: RefusalContext
    method_ref: GovernedRef | None
    assessments: list[CandidateAssessment]
    configuration_issues: list[CandidateConfigurationIssue] | None
    citations: list[Citation]
    missing_field_ids: list[FieldId]
    required_human_action: DisplayDirective
    audit_event_ids: list[OpaqueId]

MIEDecision = Annotated[Union[
    MethodArtifactDecision, KnownArtifactsExcludedDecision, IndeterminateDecision,
    WithinMeasurementVariationDecision, RefusalDecision,
], Field(discriminator="verdict")]

class AdvisoryDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: OpaqueId
    case_id: OpaqueId
    tier: Literal[2]
    status: Literal["ADVISORY_NO_VERDICT"]
    dispositional: Literal[False]
    non_record_of_record: Literal[True]
    operational_mode: Literal["RESEARCH_ONLY", "QUALIFIED"]
    engine_id: OpaqueId
    engine_version: OpaqueId
    context: BoundDecisionContext
    as_of_time: CanonicalTimestamp
    method_resolution: Literal["RESOLVED", "AMBIGUOUS", "UNKNOWN"]
    method_ref: GovernedRef | None
    proposed_field_ids: list[FieldId]
    candidate_failure_mode_refs: list[GovernedRef]
    applicability_evaluations: list[ApplicabilityEvaluation]
    open_discriminator_refs: list[GovernedRef]
    required_measurement_ids: list[TermId]
    required_record_type_ids: list[TermId]
    tier1_eligibility_gap_ids: list[TermId]
    next_steps: list[DisplayDirective]
    citations: list[Citation]
    audit_event_ids: list[OpaqueId]

class Tier1Output(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_kind: Literal["TIER1_DECISION"]
    decision: MIEDecision
    decision_hash: Sha256Hex                    # hash of canonical `decision` only

class Tier2Output(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_kind: Literal["TIER2_ADVISORY"]
    advisory: AdvisoryDecision
    advisory_hash: Sha256Hex                    # hash of canonical `advisory` only

MIEOutput = Annotated[
    Union[Tier1Output, Tier2Output], Field(discriminator="output_kind")
]
```

Canonical list sort keys are normative: governed references by `(logical_id, version_id)`; citations by `(record_type_id, logical_id, version_id, evidence_location)`; candidate assessments by candidate reference; display parameters by `key_id`; directives by `(template_id, canonical params)`; IDs and terms lexicographically under §2.13. A schema may declare a different semantic order only when order itself carries domain meaning, in which case the order field is explicit and governed.

`decision_hash` is SHA-256 over the canonical `decision` object only; `advisory_hash` is over the canonical `advisory` object only. The enclosing transport object and its hash field are not inputs to their own hashes.

`MSA_UNCHARACTERIZED` is emitted only as `RefusalDecision{verdict="REFUSED", refusal_type="MSA_UNCHARACTERIZED"}`. A refusal after snapshot binding uses `BoundDecisionContext`. A refusal that prevents snapshot binding, such as `PACK_VERSION_UNAVAILABLE`, uses `PreflightRefusalContext` and MUST NOT fabricate pack, policy, or snapshot references. Tier 2 emits `AdvisoryDecision`, never a Tier 1 verdict or refusal. Build 0 emits `RESEARCH_ONLY`; later qualified deployments may still emit non-dispositional Tier 2 advisory outputs. No generic `confidence`, `confidence_interval`, or `posterior` field exists anywhere.

---

## 10. MIE Trust Models (pack content, not engine branches)
Qualitative optical: imaging→prep→induced change→geometry. Quantitative optical: imaging/prep→scale calibration→projection→segmentation/thresholding→measured geometry. Spectral: calibration→conversion assumptions→interference→geometry/sampling→reported property. Mechanical: fixturing/alignment→measurement chain→specimen→conditions→reported behavior. Thermal: baseline/calibration→rate/kinetics→coupling/mass→history→reported behavior. Order guides investigation; it does not establish material truth.

---

## 11. Capture, Attributed Observations, Pack Publication
Capture: register source → hash/preserve → deterministic extraction where available → LLM-assisted typed proposal where useful → evidence-location verification → domain-expert validation → rule/record tests → pack candidate → independent release review → immutable published pack version. Attributed observations (§2.6) enter `UNVALIDATED`, Tier-2-only, always shown with attribution. Promotion requires corroborating governed evidence or a governed designed-validation protocol, expert validation, and a recorded promotion event.

A designed-validation protocol is itself a governed versioned record declaring the hypothesis, data to collect, acceptance criteria, required authority, and result contract. Governance artifacts are governed too: authorized-role sets, pack approvals, qualification events, and operational-mode elevation records carry immutable versions, named approvers, effective times, evidence, and content hashes. Attestation separation of duties (§7.5) is a publication gate.

Lifecycle is `DRAFT→VALIDATED→PUBLISHED→DEPRECATED→REVOKED`; only `PUBLISHED` records enter Tier 1. Release gates include schema and referential integrity; predicate-AST and unit validation; selection-group validation with no rank ties; rules linked to evidence and owner; golden/regression suites; no unresolved critical findings; deterministic hashes; named approver; fully resolved policy manifest proving no application defaults; and source scans proving no domain constants in generic engine code. Threshold status is `UNVALIDATED|BENCH_TUNED|QUALIFIED`; `UNVALIDATED` or `BENCH_TUNED` decision policy forces `RESEARCH_ONLY`. Elevation to `QUALIFIED` requires a governed qualification event.

---

## 12. Storage and Retrieval
**Build 0 and production storage:** PostgreSQL with migration-controlled schema versions, foreign keys, transactional snapshot binding, primary-key citations, immutable pack versions, and database-enforced append-only decision/audit records. `Decimal` values are stored as canonical strings when part of canonical payloads and as constrained `numeric` only for explicitly non-payload query columns whose conversion is tested. Build 0 is single-writer but uses the same persistence semantics intended for production. **Allowed retrieval:** exact IDs/aliases; FK/relational; range/categorical; controlled-vocabulary joins; deterministic rule evaluation; custom versioned lexical scoring with stable tie-break; optional `tsvector`/trigram acceleration proven equivalent to the canonical scorer. **Prohibited:** SQLite/FTS5 in the runtime path; vector similarity/embedding indexes; model-memory assertions; uncited search in a decision path; nearest-match fallback; hidden reranking/unversioned weights; application-code defaults; mutation of a published governed version.

---

## 13. The Other Modules [HORIZON — architectural intent, not near-term build]
Each is an Authority Pack on the shared substrate over the production context graph, on whichever reasoning engine matches its computation, governed by §2, surfacing its dark space (§2.9), failing closed.

**13.1 Material/Lot Genealogy** [Retrieval Engine] — governs lot/serial nodes and genealogy edges; population answers by relational traversal; eliminate lots/serials that cannot be in the affected population; genealogy is governed record or unknown. Requires the §3 temporal/identity contracts first.

**13.2 Process Integrity & Drift** [Retrieval Engine + governed-rule SPC] — SPC/drift over **governed** parameters with **governed** control limits; a drift flag is a deterministic rule over governed series, not a model judgment; cites the series; never asserts causation. [HORIZON: historian-scale time-series governance is a real subsystem.]

**13.3 Nonconformance/FRACAS** [Diagnostic Engine] — failure-mode/corrective-action precedents as governed records; investigation memory; the dark-space rule is load-bearing ("these modes checked and excluded; these known modes not evaluated").

**13.4 Specification Compliance** [Retrieval Engine] — specs/procedures/acceptance criteria as `ConstraintRule`s with evidence links; deterministic rule evaluation with row-level citation; refuses when the governing spec/evidence is absent.

**13.5 Production Problem Solver (Orchestrator)** [HORIZON — the hardest; non-dispositional boundary tightened, closes finding 8] — composes packs over the graph to answer the eight questions: detect what changed, scope population, eliminate impossible causes, enumerate surviving hypotheses with cited evidence, propose next-best checks, **present evidence-supported containment/corrective options for human approval — it does NOT declare any action "justified."** A declaration that an action is justified requires a formal authority/approval contract outside this system; the orchestrator presents options and the evidence for each, and the human (with authority) decides. Conservative cross-pack aggregation = present what each pack supports, never average dissent into false consensus. **The antigravity step, pulled back:** the orchestrator is an evidence-assembly and hypothesis-scoping aid for a human investigator, never an autonomous root-cause decider.

---

## 14. Outcome Taxonomy
The output kinds are disjoint. Consumers branch first on `output_kind`, then on the relevant enum.

- Tier 1 `verdict`: `METHOD_ARTIFACT` · `KNOWN_ARTIFACTS_EXCLUDED` · `INDETERMINATE` · `WITHIN_MEASUREMENT_VARIATION` · `REFUSED`.
- `RefusalType`, valid only when `verdict == REFUSED`: `MSA_UNCHARACTERIZED` · `UNKNOWN_METHOD_OR_FAILURE_MODE` · `MISSING_REQUIRED_EVIDENCE` · `STALE_OR_INVALID_CALIBRATION` · `PACK_VERSION_UNAVAILABLE` · `INTEGRITY_FAILURE` · `ENGINE_FAILURE` · `CONFIGURATION_INVALID`.
- Tier 2 `status`: `ADVISORY_NO_VERDICT`.

`INDETERMINATE` and `WITHIN_MEASUREMENT_VARIATION` are verdicts, not refusal types. `MSA_UNCHARACTERIZED` is a refusal type, never a verdict.

---

## 15. Related Systems (not in the runtime decision path)
**FORGE** compiles schemas/contracts/tools/packs from governed data. **ORACLE** performs adversarial design/review governance; not a runtime verdict stage. **SENTINEL** is a domain product/vertical, not the generic name for GPTL as a service.

---

## 16. Acceptance Statement
Successful when an engineer can inspect a canonical authoritative result and answer, **without trusting a model:** exact input used; who/what supplied and ratified each value; which pack/engine/rules/thresholds/records were active; the published candidate set considered; why each candidate was retained/supported/ruled out; what evidence confirmed it; what remains unknown (the dark space); what would change it; whether it reproduces with every LLM disabled; whether every decision-affecting value traces to the bound snapshot rather than application code. If any answer is unavailable, the system has not earned the right to an authoritative verdict.

---

## 17. Test and Release Gates
**Required test classes:** LLM-off equivalence; deterministic stable ordering; `Decimal` boundary tests at the exact threshold and nearest representable values; RFC 8785/NFC/timestamp/list-order/hash conformance; property-based commutativity plus representative discriminator permutations; zero-observed-features → `OPEN_UNASSESSED`; missing applicability field → `UNKNOWN`, never exclusion; `UNKNOWN` candidate blocks negative verdict; invalid/empty predicate → `CONFIGURATION_INVALID`; range-bound inclusion/exclusion; unit incompatibility; selection-group isolation, precedence, and tie rejection; distinct applicable failure modes never compete without a shared group; overlapping ungrouped MSA studies fail publication; MSA evidence-scope mismatch fails the gate; a `TEST_FIXTURE` MSA cannot satisfy any non-test run; insufficient rule-out evidence never yields `RULED_OUT`; overlapping discriminator outcome predicates fail; contradictory discriminator results; explicit supersession-chain dedup; immutable historical replay; tamper → `INTEGRITY_FAILURE`; preflight refusal carries no fabricated pack/snapshot references; citation/evidence-location validation; renderer claim-diff; pack upgrade/rollback/revocation; no-default deletion tests; source scans rejecting domain constants and vector/model dependencies; verdict/advisory schema validation; attestation authority, revocation, supersession, and separation of duties; attributed-observation containment; MSA gate; and negative-result boundary fields.

**Build 0 gold fixtures:** synthetic/reference EDS peak overlap, SEM charging, and XRD missing-minor-phase cases for `QUANT_NONDESTRUCTIVE`; tensile and DSC Tier-2-only cases for unimplemented MSA classes; within-measurement-variation; `KNOWN_ARTIFACTS_EXCLUDED` with every candidate explicitly eliminated or ruled out; incomplete typed intake; conflicting confirmed candidates; unknown method; missing MSA; identical-input replay; and permuted-evidence identical verdict. Every non-production fixture MUST declare `fixture_class = SYNTHETIC` or `REFERENCE` and MUST NOT claim fidelity to a vendor instrument, company lab, or qualified production process.

**Release-blocking:** any golden regression; any unratified value entering Tier 1; any model-dependent difference in canonical Tier 1 output; any uncited authoritative claim; any vector dependency; any non-reconstructable historical decision; any rule without evidence/version/owner; any probability/confidence interval; any silent failure-to-result conversion; any decision value from application code rather than the bound snapshot; any nondeterministic order/time/locale/numeric/retry behavior; any non-canonical authoritative serialization; any authoritative free text; any open string used where a governed semantic type is required; any `float` in a boundary decision or canonical payload; any order-dependent score; any implicit-latest dedup; any applicability `UNKNOWN` treated as `FALSE`; precedence across unrelated candidates; any missing-evidence candidate becoming `RULED_OUT`; any confirmation without a valid structured test or attestation; any Tier 1 verdict for an unimplemented MSA class; any unvalidated observation in Tier 1; any artifact verdict without qualified scope-matched MSA; any `TEST_FIXTURE` evidence satisfying a non-test run; any negative result asserting real behavior or a fraction over unknowns; mutation of a published record version; or any Build 0 Tier 1 output not labeled `RESEARCH_ONLY`.

---

## 18. Build Sequence

### Build 0 — Deterministic Spine (near-term wedge; MIE Diagnostic Engine; IMPLEMENTATION CONTRACT)
Build the shared identity/version, canonical serialization, snapshot, policy-manifest, citation, and append-only audit substrate; the MIE schemas and four-state applicability evaluator; scoped selection-group resolution; exact method resolution; signature match; evidence-state gating; order-independent aggregation; structured/attested confirm tests; `QUANT_NONDESTRUCTIVE` MSA hard gate; typed Tier 1/Tier 2 outputs; and the §17 local conformance suite. The implementation runs with every LLM adapter disabled and has no vector dependency.

Build 0 uses synthetic/reference SEM, EDS, and XRD fixtures to prove engine behavior. Synthetic MSA data and diagnostic inputs are isolated in a governed `TEST_FIXTURE` evidence scope and cannot satisfy any non-test run. Tensile and DSC remain Tier-2-only until their method-class MSA contracts exist. Build 0 does **not** contain vendor-specific raw-file adapters and does not claim fidelity to any company's instruments or lab schema. Manually ratified typed inputs are sufficient for the engine vertical slice; vendor adapters are later integration work.

Every Build 0 Tier 1 decision carries `operational_mode = RESEARCH_ONLY`. It is deterministic and replayable but MUST NOT be consumed as qualified input to quality, disposition, compliance, or flight decisions. Elevation to `QUALIFIED` requires Build 2 qualification evidence and a governed elevation event.

Acceptance: synthetic EDS peak-overlap → `METHOD_ARTIFACT` in `RESEARCH_ONLY` for the recorded reason; no-MSA/unimplemented-class → `REFUSED{MSA_UNCHARACTERIZED}` plus optional Tier 2; catalog exhausted only through explicit elimination/rule-out → `KNOWN_ARTIFACTS_EXCLUDED` with correct boundary; missing applicability → no negative verdict; zero observations → `OPEN_UNASSESSED`; identical input → byte-identical replay; permuted discriminator order → identical verdict.

> **Knowledge acquisition is separate from the engine scaffold.** Public/reference knowledge and synthetic fixtures can exercise Build 0 without pretending to describe a specific lab. Vendor-native schemas, validated method records, failure modes, discriminators, confirm tests, and qualified MSA studies require real source material and domain validation. A method is production-eligible only when its knowledge and measurement system are qualified.

### Build 1 — Capture & Advisory
Source registration and evidence-grounded proposals; human validation/ratification; governed designed-validation protocols; attributed-observation ingestion (`UNVALIDATED`, Tier-2-only); deterministic custom lexical Tier 2 retrieval; optional Bouncer and renderer adapters. Vendor-specific instrument adapters MAY begin here only from real, legally usable source files and MUST preserve the raw artifact and provenance.

### Build 2 — Qualification
Qualify `tau_*`, `delta_dom`, evidence sufficiency, rule-out requirements, minimum coverage, and the `COMBINE` form against named bench cases; implement method-class-specific MSA; promote eligible methods from research-only; add fatigue crack growth and TGA; complete security/replay/adversarial suites.

### Build 3 — Governed Production Profile
Durable workers and production concurrency; RBAC, retention, tamper evidence, backup/recovery; qualified pack-release workflow; controlled integration APIs; non-QMS segregation and export controls; production vendor adapters; cryptographic/multi-party governance where required.

### [HORIZON] Beyond Build 3 — Platform Expansion
Genealogy → Process/Drift → FRACAS → Spec Compliance → Problem Solver, each its own pack/engine with its own build and qualification (and, for the graph packs, the §3 temporal/identity contracts first). The Retrieval Engine is introduced when the first retrieval pack (Spec Compliance) is built. Multi-pack orchestration is the destination, not the sprint.

---

## 19. Open Questions

**19.1 Owner-Decided (closed):** missing/unimplemented MSA → `REFUSED{MSA_UNCHARACTERIZED}`, Tier 2 may run · negative class → `KNOWN_ARTIFACTS_EXCLUDED`, cited bounded-catalog record, no fraction over unknowns · tribal knowledge → attributed observation, fact only after governed validation · missing applicability never excludes a candidate · missing evidence never rules out a candidate · **architecture → one shared safety substrate with a closed, bounded set of reasoning engines by computation type; MIE uses the Diagnostic Engine; adding an engine type requires owner-ratified revision (§1.3).**

**19.2 Bench-Open (need data):** `tau_*`, `delta_dom`, evidence-sufficiency and rule-out requirements, minimum coverage, and the `COMBINE` form (order-independence and fail-closed evidence states are fixed) · per-method qualification evidence/acceptance per §2.11 without pseudo-statistics · enumeration/currency of `known_unevaluated_gaps` per method class.

**19.3 Architecture-Open:** the §3 production-context-graph temporal/identity and correction-propagation contracts — required before any graph pack is deterministic, not before MIE Build 0 · whether the Problem Solver's conservative cross-pack aggregation needs its own formal contract before any module beyond MIE [HORIZON].

---

## 20. One-Sentence Product Definition
The GPTL Manufacturing Intelligence Platform is a non-dispositional, deterministic, fail-closed system — a shared safety substrate with a bounded set of reasoning engines (retrieval and diagnostic) over governed data — that turns fragmented materials, process, production, test, continuous, and experiential data into cited, evidence-backed hypotheses and next-best actions for human decision, ruling out what the governed evidence makes impossible, proving what it can, surfacing the named boundary of what it cannot, and never letting a model make or disguise the engineering decision — with Method Integrity as its first diagnostic engine and the full manufacturing-intelligence platform as its destination.

---

## Appendix A — Merge Disposition
| Source concept | Disposition |
|---|---|
| GPTL = General Purpose Translation Layer | Retained; only valid expansion |
| Negative selection | Retained as core method |
| BSMS runtime pattern | Retained; defined (§4) |
| **Single engine + packs** | **Owner-ratified amendment → one shared safety substrate plus a closed, bounded engine set by computation type (§1.3)** |
| SENTINEL as generic GPTL service | Superseded; a vertical |
| FAISS/vector retrieval (incl. MIE Tier 2) | Prohibited; lexical/relational/FTS only |
| Model confidence interval | Removed (§2.8) |
| L5 autonomous Finding/Implication/Action/Timeline | Superseded by cited-result-or-refusal |
| Generic `IntelligenceOutput` | Replaced by typed discriminated-union decisions (§9) |
| Authority Pack as YAML/prompt | Governed versioned domain payload (data, not code) |
| MIE `candidate confidence`/posterior | `candidate_support_score`, `Decimal`, order-independent |
| MIE `MATERIAL_BEHAVIOR` | Removed (no material-physics model) |
| MIE `NO_KNOWN_ARTIFACT` | `KNOWN_ARTIFACTS_EXCLUDED`; cited coverage record, not real-behavior |
| MIE as outer boundary | First diagnostic engine; platform is the boundary |
| Tribal knowledge/"vibes" | Attributed observation; governed fact only after validation |
| Production context graph | Platform spine; temporal/identity contracts deferred (§3) |
| float scoring | Replaced by `Decimal` (§2.12) |
| Sequential support update | Replaced by order-independent set aggregation (§8.7) |
| Boolean applicability | Replaced by `TRUE|FALSE|UNKNOWN|INVALID`; `UNKNOWN` never excludes (§7.2) |
| Global precedence rank | Restricted to an explicit governed selection group (§7.2) |
| Missing evidence as low support | Replaced by `OPEN_UNASSESSED`; cannot become `RULED_OUT` (§8.6–8.8) |
| Open authoritative strings/maps | Replaced by semantic scalar types, governed references, directives, and sorted arrays (§7.1, §9) |
| Vendor-native file assumptions in Build 0 | Excluded; synthetic/reference typed fixtures only (§17–18) |
| Temporal derivatives | Deferred to Process/Drift; governed-rule form only |
| Multi-pack switchboard | [HORIZON] beyond Build 3 |

---

## Appendix B — The Antigravity Line
**Buildable now (Build 0):** the shared deterministic substrate, MIE Diagnostic Engine, four-state applicability, evidence-state gates, PostgreSQL persistence, canonical serialization, immutable replay, and synthetic/reference research fixtures. **Requires real lab/source access:** vendor adapters, production method packs, and qualification. **Buildable with program effort (Build 3 + packs):** the governed production profile and additional engines/packs, qualified individually. **The antigravity step, pulled back:** the Production Problem Solver assembles cited evidence, scopes populations, eliminates only what governed evidence makes impossible, presents surviving hypotheses and explicit dark space, and recommends checks for a human. It never autonomously concludes causation or disposition.
