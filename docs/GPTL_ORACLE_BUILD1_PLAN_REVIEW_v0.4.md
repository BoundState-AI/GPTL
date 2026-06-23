# GPTL MIE Build 1 ORACLE Plan Review Bundle
## Single-Document Specification and Build Plan Packet - v0.4

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20

**Build 1 plan:** GPTL MIE Build 1 Plan v0.4

**Spec SHA-256:** `4429dc720dd3bce327af63821f813fc6ee0496aa9817a9259f243fcf977e4dc6`

**Build 1 plan SHA-256:** `08b672cf49fe8aa26f3c45dabf569dc9b44f21a012a37d1cae96e0ffb1c19b7e`

---

## ORACLE Review Charter

This is the only input document for Build 1 plan review. It embeds the complete frozen governing specification and the proposed Build 1 plan. Do not request a second document or import any section as a separate rule pack.

Build 1 is not a new architecture. It is the implementation plan for the existing v0.4.20 Build 1 scope: capability-profiled capture, source registration, evidence-grounded typed proposals, human ratification, attributed observations, designed-validation protocols, and advisory bridge into the already-frozen Build 0 deterministic engine.

Build 1 is not a production qualification effort. It must not be reviewed as if it promises SpaceX-specific integration, production LIMS coverage, vendor parser fidelity, qualified MSA, production RBAC, QMS record-of-record semantics, distributed workers, or autonomous root-cause/disposition decisions.

This v0.4 packet carries forward the owner-direction decisions from ORACLE session `20260623-040533`:

1. Direct instrument-emitted Tier 1 authority is deferred. Build 1 captures instrument/parser/import/manual/model-assisted data only as source-backed proposals; every Tier 1 value requires active ratification.
2. Build 1 does not impose a universal dual-human rule. It defines a governed `AuthorityPolicy`; single-actor research ratification is allowed only when the bound policy explicitly allows it, while independence is enforced when the policy requires it.
3. Build 1 stores raw source bytes in PostgreSQL with the source record for atomic research-corpus registration. External content-addressed storage is deferred to a production storage profile.

It also resolves the material findings from ORACLE session `20260623-185534` with conservative owner decisions:

1. Build 1 uses the closed `EvidenceScopeV1` dimension set and exact-match `EVIDENCE_SCOPE_MATCH_V1`; there is no wildcard, hierarchy, containment, or temporal scope operator.
2. Source-derived identity is limited to existing governed references, caller-supplied identities with evidence, or `SOURCE_LOCAL_RECORD_IDENTITY_V1`; fuzzy merge and cross-source entity reconciliation are deferred.
3. Designed-validation criteria use only `VALIDATION_PREDICATE_TEMPLATES_V1`; arbitrary expressions and model-evaluated predicates are prohibited.
4. Ratifiable evidence locations are limited to replay-stable `ProposalEvidenceV1` locators. PDF/OCR/image-region evidence is proposal-only unless a replay-bound parser/renderer/OCR toolchain is later specified.
5. Build 1 authority records bind claimed actor attribution against a governed local registry; authenticated signer identity, e-signature, and production RBAC are deferred.
6. Active-value conflicts are resolved only by later correction/supersession events in later runs; historical conflicts replay as conflicts.

It resolves the blocked findings from ORACLE session `20260623-192631` with these owner-direction decisions:

1. `SOURCE_LOCAL_RECORD_IDENTITY_V1` uses an evidence-backed `source_local_record_key` rather than evidence text, proposed values, or corrected values. This is the intended source-local identity model for Build 1.
2. Parser-derived proposals bind an exact `parse_attempt_ref`; parser/decoder/identity/canonicalization algorithms resolve through governed executable `AlgorithmRegistryEntry` records.
3. Capability profiles may carry non-authoritative calibration/MSA labels for routing/advisory diagnostics, but Build 0 remains the only owner of calibration/MSA gates.
4. Build 1 does not require the frozen Build 0 engine to share the caller's transaction. If Build 0 cannot run inside a caller-supplied unit of work, Build 1 uses the narrowed-boundary bridge attempt state machine with immutable request hashes and idempotent retry.
5. Build 1 records single-actor research ratification as an explicit policy-allowed exception, not as independent separation-of-duties.
6. Source registration enforces governed max-byte limits while streaming the payload; it must not buffer an unbounded payload before rejection.
7. Build 1 covers messy source artifacts only within ratifiable replay-bound evidence classes. PDF/OCR/image evidence remains proposal-only unless a later replay-bound parser/renderer/OCR toolchain is specified.

### Questions ORACLE Must Answer

1. Does the Build 1 plan implement v0.4.20 §§2.3-2.7, §6, §11, and §18 without contradicting the frozen Build 0 spine?
2. Does the plan preserve the ratification firewall so no proposed value, model output, direct instrument/parser output, missing capability, unsupported source, or unvalidated observation can enter Tier 1?
3. Is the capability-profile/"choose your tools" model sufficient to proceed before knowing a specific lab's exact instruments and LIMS, while still failing closed for unknown or unsupported capabilities?
4. Are the slices ordered correctly for an incremental build, or is any Build 2 qualification or Build 3 production concern being pulled into Build 1 too early?
5. Are any required Build 1 record types, replay surfaces, or evidence gates missing?
6. Does any plan item rely on vectors, hidden defaults, magic values, model authority, SQLite fallback, vendor assumptions, or production claims?
7. What is the smallest correction set that makes this Build 1 plan implementation-ready?

### Evidence and Scope Rules

- Findings must cite exact sections in the embedded plan and governing specification.
- Do not relitigate Build 0 closeout unless the Build 1 plan contradicts a frozen Build 0 invariant.
- Do not classify explicitly deferred Build 2/3 work as a Build 1 defect.
- Do not treat absence of real SpaceX equipment, LIMS schemas, vendor files, or production MSA as a Build 1 blocker; Build 1 defines the deterministic intake and capability profile that lets those be added later without guessing.
- Treat preferences, alternate architectures, and production-hardening suggestions as nonblocking unless they expose a contradiction in the Build 1 plan.

### Required Finding Format

For every finding provide: finding ID; severity `BLOCKER|MAJOR|MINOR|NIT`; exact plan section; exact governing-spec section; contradiction or unsupported claim; minimum correction preserving ratified constraints; Build 1 impact; and whether the finding is established from this bundle.

### Required Final Disposition

Return exactly one:

- `BUILD_1_PLAN_READY_TO_IMPLEMENT`
- `BUILD_1_PLAN_READY_WITH_NONBLOCKING_FINDINGS`
- `BUILD_1_PLAN_NOT_READY`

`BUILD_1_PLAN_NOT_READY` requires at least one bundle-established `BLOCKER` or `MAJOR` contradiction that would let unratified/model/missing/unsupported evidence enter Tier 1, break deterministic replay/provenance, or move Build 2/3 production claims into Build 1.

---

# Embedded Governing Specification

<!-- BEGIN GPTL_SPEC_V0.4.20 -->
# GPTL Manufacturing Intelligence Platform
## Architecture Baseline and MIE Build 0 Contract — v0.4.20

**Author:** Joe Wilde, BoundState AI LLC
**Status:** **OWNER-RATIFIED ARCHITECTURE BASELINE; RESEARCH-ONLY BUILD CONTRACT.** This document is the governing architecture and the implementation contract **for the MIE Build 0 wedge only** (§§5–9, §18). All [HORIZON] modules and the domain-neutral GPTL contract *names* in this document are architecture-baseline intent, not field-level implementation contracts, and are explicitly marked as such. Build 0 is deterministic and audit-reconstructable but not qualified for production reliance. Supersedes v0.3, v0.4, the ORACLE-generated v0.4.1/v0.4.2 drafts, v0.4.3, v0.4.4, v0.4.5, v0.4.6, v0.4.7, v0.4.8, v0.4.9, v0.4.10, v0.4.11, v0.4.12, v0.4.13, v0.4.14, v0.4.15, v0.4.16, v0.4.17, v0.4.18, v0.4.19, and prior BoundState GPTL/MIE/SENTINEL architectural statements.
**Self-contained:** defines the system from first principles; requires no external context.

> **Change basis (v0.3 → v0.4):** closes ten adversarial-review findings. The load-bearing six: numeric determinism via `Decimal` (§2.12, §8, §9); **order-independent evidence aggregation** (§8.7 — scoring no longer depends on discriminator order); production-context-graph and core contracts re-scoped honestly as architecture baseline (§1.5, §3, §6); typed closed-schema outputs replacing open dicts/strings (§9); completeness language replaced with bounded-catalog language throughout (§2.9, §8.8, §9); and **the foundational architecture resolved — shared substrate, multiple reasoning engines; MIE is the first *diagnostic engine*, not an Authority Pack** (§1.3, §4). Plus: advisory penalties removed from Build 0 (§8.4); Problem Solver presents options, never declares action "justified" (§13.5); expanded permutation/edge-case test classes (§17).

> **Change basis (v0.4 → v0.4.2):** incorporates the accepted ORACLE findings: disjoint verdict/refusal/advisory output kinds; canonical serialization and hashing; immutable logical-record/version identity; snapshot-bound supersession; class-scoped MSA eligibility; governed applicability predicates and attestations; authoritative/display separation; a typed Tier 2 output; governed meta-approval records; and explicit `RESEARCH_ONLY` Build 0 operation.

> **Change basis (v0.4.2 → v0.4.3):** closes the final execution-level gaps found during human verification. Applicability now returns four states rather than `bool`; missing context cannot silently remove a candidate; precedence is restricted to an explicit selection group; the predicate AST can represent range bounds; candidates without sufficient evidence remain `OPEN_UNASSESSED` and cannot be ruled out; authoritative identifiers/references use constrained types rather than comments over open strings; the shared-substrate/bounded-engine amendment is owner-ratified; and synthetic fixtures, instrument adapters, and production qualification are separated explicitly.

> **Change basis (v0.4.3 → v0.4.4):** binds every MSA qualification and snapshot-bound decision to a governed evidence scope. Synthetic MSA can qualify only an isolated `TEST_FIXTURE` scope, always forces `RESEARCH_ONLY`, and can never satisfy a bench, vendor, company, or production-scoped run. This closes the test-fixture qualification gap without weakening the MSA gate.

> **Change basis (v0.4.4 → v0.4.5):** owner decision replaces the Build 0 SQLite profile with PostgreSQL. Build 0 now uses transactional PostgreSQL persistence, database-enforced append-only records, forward-only migrations, and deterministic custom lexical scoring. PostgreSQL text search may accelerate bounded lookup only behind an explicit parity gate that preserves canonical membership and ordering.

> **Change basis (v0.4.5 → v0.4.6):** closes the Slice 2 safe-refusal review without overloading valid candidate evidence states. Runtime-invalid applicability now emits typed candidate configuration issues carrying the exact evaluation, error code, and evidence. Ratification verifies value integrity before active-state resolution, is re-evaluated from the event set bound into the snapshot, and requires decision-effective events to be both effective and recorded by the run's explicit `as_of_time`; later-recorded backdated events affect later runs but cannot rewrite historical eligibility.

Snapshot-bound output records written under this revision use schema version `gptl.slice2.v2`. Readers MUST continue to verify and load immutable `gptl.slice2.v1` records; historical payloads are never rewritten to the new schema.

> **Change basis (v0.4.6 → v0.4.7):** implements the Slice 3 calibration and MSA hard gates. Ratified intake must pass governed calibration before MSA evaluation. Method/class/measurand identity is carried by a governed `MethodMeasurementContract`; MSA failure precedence is explicit in a snapshot-bound route policy; exact compared deviation and uncertainty values are retained in both terminal comparison decisions; and scope, qualification, implemented class, applicability, and selection are all fail-closed.

Snapshot-bound Slice 3 outputs use schema version `gptl.slice3.v1`. Readers retain verified compatibility with immutable Slice 2 v1/v2 records; no historical payload or migration is rewritten.

> **Change basis (v0.4.7 → v0.4.8):** implements Slice 4 artifact confirmation. Every signature weight, evidence threshold, discriminating power, confirmation threshold, verdict threshold, dominance margin, and high-power boundary resolves through a provenance-complete `GovernedNumericPolicy`; no domain numeric value enters generic engine code. Slice 3 exposes a typed outside-variation continuation so Slice 4 consumes the exact prior snapshot and gate evaluations. Discriminator results, role authorization, and attestations use explicit immutable supersession plus effective and recorded times. Structured and attested confirmation are both fail-closed, and `METHOD_ARTIFACT` retains the selected MSA comparison and exact candidate assessments.

Snapshot-bound Slice 4 outputs use schema version `gptl.slice4.v1`. Readers retain verified compatibility with immutable Slice 2 v1/v2 and Slice 3 v1 records; no historical payload or migration is rewritten.

> **Change basis (v0.4.8 → v0.4.9):** closes the Slice 4 safe-refusal review. `CONFIRMED` remains a candidate-level status; `METHOD_ARTIFACT` requires exactly one dominant named winner but does not erase a lower-support confirmed candidate. Closed-schema validation of an engine-generated decision is an engine invariant, so a failure returns governed `ENGINE_FAILURE` rather than escaping or being mislabeled as input configuration. Partial required signature evidence cannot enter support aggregation, multiple active authorities remain integrity failures, and renderer independence is regression-protected.

This clarification does not revise the `gptl.slice4.v1` payload schema or rewrite historical records.

> **Change basis (v0.4.9 → v0.4.10):** implements Slice 5 honest bounded-catalog negatives. Hard elimination is a governed predicate record evaluated before signature scoring. `RULED_OUT` requires an evaluable candidate, support at or below a governed `tau_ruleout`, and every discriminator named by the candidate's exact `RuleOutEvidenceRequirement` resolving `CONSISTENT_WITH_REAL`; support alone cannot exclude. `KNOWN_ARTIFACTS_EXCLUDED` is reachable only when every applicable published candidate is terminally eliminated or ruled out, the exact high-power discriminator denominator is known, and the governed minimum evaluated fraction is met. Positive artifact routing retains precedence, known unevaluated categories remain explicit, and every terminal exclusion carries ruling citations.

Snapshot-bound Slice 5 outputs use schema version `gptl.slice5.v1`. Readers retain verified compatibility with immutable Slice 2 v1/v2, Slice 3 v1, and Slice 4 v1 records; no historical payload or migration is rewritten.

> **Change basis (v0.4.10 → v0.4.11):** closes the Slice 5 adversarial review without changing verdict semantics or the `gptl.slice5.v1` payload schema. Regression gates now pin the absence of any real-material assertion, exact named-gap content, fail-closed uncited exclusions, and all registered directive classes. Citation intersections compare the complete immutable `GovernedRef`, not a partial lookup key. Governed record evidence references remain snapshot-bound unless they are independently citable records with their own type and evidence location; the engine never fabricates citation metadata to surface a bare reference.

This clarification does not rewrite historical payloads or migrations.

> **Change basis (v0.4.11 → v0.4.12):** implements Slice 6 deterministic Tier 2 advisory. Method resolution follows the fixed exact-ID/alias → controlled-term → relational → lexical lane order under a snapshot-bound resolver policy. NFKC/casefold/ASCII-alphanumeric normalization, every lane weight, the minimum lexical score, catalog membership, route rules, and stable full-reference tie-break are explicit and replayable. Eligibility gaps are derived from the actual Tier 1 attempt rather than reconstructed in advisory code. `AdvisoryDecision` carries no verdict, refusal, candidate support, retrieval score, or model-derived field; unknown and ambiguous methods cannot select a method. Optional acceleration must reproduce canonical membership and ordering exactly, and prose remains a separate `RenderedArtifact` over the advisory hash.

> **Change basis (v0.4.12 → v0.4.13):** closes the Slice 6 adversarial review. Lexical normalization now binds the frozen UCD 3.2.0 table explicitly rather than inheriting CPython's release-dependent default Unicode database; ASCII case folding after fixed-table NFKC makes replay stable across supported interpreter minors. A resolved advisory path rejects any Tier 1 non-refusal before route selection, so fixture content cannot silently convert a verdict into advisory output. Regression gates also recompute every ineligible fixture's advisory hash and pin the public Slice 6 contracts.

> **Change basis (v0.4.13 → v0.4.14):** implements Slice 7 replay and integrity closure. Each replay-qualified run atomically stores an append-only `gptl.replay-recipe.v1` capsule containing its exact typed request, runtime, policy, and query under `BUILD0_EXACT_REPLAY_V1`. Replay reconstructs Slices 1–6 without network access or implicit-latest resolution and requires byte identity across output, snapshot, audit, citation, and bound-version payloads. Missing, altered, non-canonical, or algorithm-incompatible replay material returns typed `INTEGRITY_FAILURE`. Explicit as-of pack lifecycle records govern new-run eligibility; upgrades, rollback, deprecation, revocation, supersession, and corrected input never mutate historical output.

Snapshot-bound Slice 6 outputs use schema version `gptl.slice6.v1`. Readers retain verified compatibility with every earlier snapshot-bound schema; no historical payload or migration is rewritten.

> **Change basis (v0.4.14 → v0.4.15):** closes the source-audited Build 0 contract review. Canonical timestamp width remains an explicit bound `CanonicalizationPolicy` value with no platform default; every timestamp comparison domain must validate all members under that one policy before lexical comparison. Run, decision, case, audit, snapshot, and replay identifiers are caller-supplied typed inputs preserved in the exact replay recipe, never engine-generated state. Tier 2 persists one advisory artifact per run after deterministically reproducing the Tier 1 eligibility attempt over the same bound inputs; it does not create an implicit paired refusal. The exact implemented calibration, refusal, replay-recipe, and replay-result schemas and replay byte surfaces are now stated explicitly. The Build 0 freeze additionally requires a repository-derived gate-to-test evidence manifest; narrative pass counts alone are not completion evidence.

> **Change basis (v0.4.15 → v0.4.16):** closes the completion-evidence audit. The gate map and generator now have independent conformance tests, every source anchor resolves to an actual heading, and readiness is derived only after those tests pass. The supported Build 0 execution profile is explicitly CPython 3.10, 3.11, and 3.12 on Linux x86-64 with PostgreSQL 14; the complete suite must pass on every minor. Full source-derived JSON Schemas, including every nested replay request/runtime/policy/query definition, are published in the machine evidence rather than represented only by opaque digests.

> **Change basis (v0.4.16 → v0.4.17):** closes the final freeze-evidence findings. Cross-minor determinism now compares canonical artifact bytes directly rather than inferring equality from separate passing suites. Every requirement-ownership row and completion criterion is enumerated in the evidence coverage map. Published schemas distinguish permissive Pydantic validation input from the canonical wire contract, whose decimals are strings only, and publish semantic invariants that JSON Schema cannot express. `diagnostic_state_hash` now has an exact byte-input definition. Repository-generated evidence is labeled self-audited unless an external attestation is actually present.

> **Change basis (v0.4.17 → v0.4.18):** closes ORACLE session `20260622-235816` without rewriting the bound v1.4 closeout. Caller-supplied authoritative identifiers now have explicit uniqueness and non-idempotency semantics; optional PostgreSQL text-search acceleration is framed as a bounded parity gate, not a mathematical proof from finite tests; `version_number` is bounded to the RFC 8785/JCS safe-integer ceiling; canonical wire Decimal strings are tied to `canonical_decimal(policy)` rather than to a permissive validation regex; and cross-minor byte evidence is stated as fixture-corpus evidence, not a universal proof over all possible inputs. The unresolved external-attestation question remains a governance choice, not a claimed repository capability.

> **Change basis (v0.4.18 → v0.4.19):** closes ORACLE session `20260623-003512`. The generated evidence gate now cites the active generator version, and completion evidence must self-check that generator identity. The replay-capsule persistence wrapper is published as its own source-derived schema artifact. `diagnostic_state_hash` now states recursive NFC normalization for nested `GovernedRef` fields rather than relying on local shorthand. Snapshot assembly names the Build 0 PostgreSQL transaction/isolation contract explicitly. The retrieval-time `STALE_EVIDENCE` marker remains an owner product decision under the existing [HORIZON] correction-propagation contract.

> **Change basis (v0.4.19 → v0.4.20):** closes ORACLE session `20260623-011909`. Build 0 single-writer persistence is now enforced by a transaction-scoped PostgreSQL advisory lock rather than accepted as a documented assumption, with a concurrent-writer rejection test. Completion evidence now binds the resolved `uv.lock` dependency inventory and digest so the freeze record names both source and dependency state.

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

Build 0 does not generate authoritative identifiers. `run_id`, `decision_id`, `case_id`, `audit_event_id`, `snapshot_id`, and `replay_id` are constrained caller-supplied inputs before execution and are preserved in the exact typed replay recipe or verification request. They may be opaque and need not be derivable from domain content; determinism requires that replay consume the identical bound identifiers, not that identity be a content hash. Random, sequence-allocated, or wall-clock-derived identity created *inside* the authoritative engine is prohibited.

Caller-supplied identity is not an idempotency key. Within the authoritative store, `run_id`, audit `event_id`, replay `run_id`, and each table's declared primary identity are unique under their table/context constraints. A duplicate insert is an integrity failure that aborts the transaction and commits no replacement or inferred equivalence, even if the submitted bytes match an existing record. Re-reading an existing record by ID is the only idempotent operation; writes are append-only creates, never upserts.

### 2.13 Canonical Serialization and Hashing Contract
RFC 8785 (JSON Canonicalization Scheme) is the locked normative standard for Build 0. Before serialization, every string MUST be normalized to Unicode NFC. Object keys follow RFC 8785 ordering. Decision-affecting numerics are emitted as canonical `Decimal` strings, never JSON numbers. A canonical Decimal string is the exact output of `canonical_decimal(value, bound_canonicalization_policy)`: fixed scale from the policy, no exponent, no plus sign, no negative zero, no leading zeros except the single digit `0`, and integer width within the policy's overflow limit. JSON Schema can publish the string-only wire surface, but policy-coupled Decimal lexeme uniqueness is a semantic invariant enforced by canonicalization tests, not by a generic regex alone. Timestamps use RFC 3339 UTC with `Z` and the exact fractional width declared by the bound `CanonicalizationPolicy`; that policy is mandatory for preflight, snapshot-bound execution, persistence, and replay and has no application default. Every timestamp in one comparison domain is validated under the same policy before comparison, so lexical and chronological order are equivalent; mixed-width or policy-free comparison is prohibited. Every authoritative list declares a semantic sort key in its schema; no list relies on insertion or query order. Absent optional fields are omitted unless the schema explicitly defines `null` as semantically distinct. SHA-256 is computed over the canonical UTF-8 bytes, and the hash algorithm identifier is stored with the snapshot. A self-hash field is never part of its own hash input: record `content_hash`, snapshot hash, and decision/advisory envelope hashes are computed over the explicitly named payload and then stored alongside it. Two conforming implementations MUST produce identical bytes and hashes for identical bound inputs.

### 2.14 Build 0 Execution Profile
The freeze-evidenced reference profile is CPython `3.10`, `3.11`, and `3.12` on Linux x86-64 with PostgreSQL `14`. The complete conformance and slice suite MUST pass independently on every supported Python minor, and the canonical fixture artifacts MUST match across those runs. Other interpreters, Python minors, operating systems, architectures, and PostgreSQL majors are not claimed unsupported, but they are outside the Build 0 freeze evidence until added by an owner-ratified profile revision and complete evidence run. The freeze evidence directly compares the published canonical fixture corpus across supported minors; it does not claim an exhaustive proof over every possible input value. Package metadata MUST encode the same Python-minor boundary.

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

Each Build 0 run persists exactly one `MIEOutput`: either `Tier1Output` or `Tier2Output`. A Tier 2 run deterministically executes the Tier 1 eligibility path over its exact request, runtime, policy, query, snapshot, and `as_of_time`; it may persist an advisory only when that attempt returns an eligible `RefusalDecision` or the method resolver is explicitly unknown/ambiguous. The eligibility attempt is internal evidence for route construction and is reproduced by exact replay; it is not persisted as a second implicit output. A consumer that requires both records must submit two explicit runs with distinct run/decision/audit identities. Build 0 defines no combined output kind and no hidden dual-artifact transaction.

### 5.2 Tier 2 Retrieval Without Vectors
Order: exact method ID/alias; controlled-vocabulary token match; relational joins (method/observable/instrument/failure-class); deterministic custom lexical scoring over normalized tokens with published weights and stable governed-ID tie-break; optional model explanation over the bounded rows. PostgreSQL `tsvector`/trigram MAY accelerate bounded lookup only behind a bounded parity gate that compares the accelerator result with the canonical resolver for the published corpus and the run's bounded query set; any mismatch disables the accelerator or returns `CONFIGURATION_INVALID`. Finite tests qualify the implemented gate and fixtures; they are not a mathematical proof that a database-native rank can never diverge. No match → `UNKNOWN_METHOD_OR_FAILURE_MODE`. All lexical policy is explicit governed records.

Build 0 implements this order as `BUILD0_LEXICAL_V1`. Text normalization is the versioned `NFKC_UCD_3_2_ASCII_CASEFOLD_ALNUM_V1` algorithm: NFKC normalization against the frozen UCD 3.2.0 table, ASCII uppercase-to-lowercase folding, then ASCII letter/digit token extraction. The resolver policy binds `unicode_data_version="3.2.0"`; an unavailable or mismatched table fails closed before retrieval. Non-ASCII source text may resolve only through the fixed table's NFKC ASCII compatibility form or separately governed controlled/relational fields; every unsupported character is a token separator, and no transliteration or fuzzy substitution occurs. The resolver policy also binds the exact lane order, positive `Decimal` weight for each lane, minimum non-exact score, evidence, and immutable policy identity. The exact typed `AdvisoryQuery` is itself an immutable governed input, snapshot-bound and cited before resolution, so replay never depends on an unrecorded search string.

The first lane with eligible rows controls membership. Within that lane, rows order by descending exact `Decimal` score then complete immutable method reference. A unique top score resolves the method; a tied top score is `AMBIGUOUS` and selects none; no eligible row is `UNKNOWN` and selects none. All rows admitted by the controlling lane remain visible to advisory candidate construction even when one method resolves. Retrieval scores are internal ordering evidence and never enter `AdvisoryDecision`.

Tier 2 eligibility state is taken from the deterministic Tier 1 attempt executed over the same bound inputs and snapshot. A resolved method may enter Tier 2 only from `RefusalDecision`; any Tier 1 verdict fails closed before route selection. Unknown and ambiguous method triggers are resolver outcomes and do not consume or replace the separate bound method runtime's Tier 1 result. A governed `AdvisoryRouteRule` maps the exact source route reason, or explicit unknown/ambiguous method trigger, to the advisory route reason, eligibility-gap term, proposed fields, required records/measurements, and registered next-step directive. Advisory code cannot infer or replace a gate outcome. PostgreSQL text-search acceleration receives no decision authority: a membership or ordering difference is `CONFIGURATION_INVALID` at the advisory boundary.

---

## 6. GPTL Core Data Contracts [HORIZON — names, not field-level; architecture baseline]

Domain-neutral records every GPTL implementation SHALL provide. **These are contract *names* at baseline fidelity; field-level schemas are specified per engine/pack as built.** `AuthorityPackVersion, SourceRecord, EvidenceRecord, ControlledTerm, ConstraintRule, EvidenceRequirement, TypedQueryProposal, RatificationEvent, DecisionRun, DecisionEvent, EvidenceCitation, RefusalRecord, PackReleaseRecord, AttributedObservation, AttestationEvent, GovernanceApprovalEvent.` Common properties: stable logical identity, immutable version identity, schema version, lifecycle state, provenance, content hash, created/validated actors, and effective timestamps. The MIE records (§7) and output (§9) are Build 0 implementation contracts.

### 6.1 Record Identity and Versioning Model
Every governed record uses one platform-wide model:

- `logical_id`: stable across revisions of the same logical record.
- `version_id`: immutable and unique per revision; never reused.
- `version_number`: monotonic JCS-safe integer within one `logical_id`, `0 <= value <= 9007199254740991`.
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
NonNegativeInt = Annotated[int, Field(strict=True, ge=0, le=9007199254740991)]
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

`validate_utc_timestamp_and_policy_precision` parses the timestamp strictly, rejects nonexistent calendar/time values, and verifies fractional precision against the explicitly supplied `CanonicalizationPolicy`. The same validation context is mandatory on the preflight path, where the policy is carried by `SafeRefusalPolicy`, and on every snapshot-bound path. Nested timestamp-bearing records in one runtime/catalog are validated under that same context before any lexical comparison. Missing context, mixed width, or a replay-policy/recipe-policy parameter mismatch fails closed; no platform or application default supplies precision. The concrete implementation MAY use Pydantic custom scalar classes instead of `NewType`, but it MUST preserve these semantic distinctions and reject malformed values. Authoritative free text is prohibited. Human-readable prose belongs only in `RenderedArtifact` (§9).

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

Build 0 represents the Slice 2 failure-mode identity and its Slice 4 diagnostic fields as two exact-bound governed records. `CandidateDiagnosticContract` binds one published failure mode to its complete ordered signature-feature set, required signature fields, discriminator set, confirm test, minimum-coverage policy, confirmation threshold, verdict threshold, author, approver, and provenance. The split preserves immutable historical Slice 2 records; it does not make any diagnostic field optional. Every published candidate in a Slice 4 pack MUST resolve exactly one contract.

Every decision-affecting diagnostic numeric is a `GovernedNumericPolicy` carrying policy kind, canonical `Decimal` value, unit, exact pack scope, derivation, governing sources, distinct owner and approver, qualification state, validation corpus and result, effective/expiration interval, evidence location, and governed evidence. The runtime policy set MUST equal the set referenced by the diagnostic contracts, features, discriminators, and route policy; missing, extra, expired, failed, mis-scoped, wrong-kind, or wrong-unit policies are `CONFIGURATION_INVALID`. Generic engine modules contain only the mathematical identities zero and one; fixture/domain values live in governed policy records.

### 7.4 Instruments and Runs
`InstrumentRecord` governs identity, supported methods, quirks, and calibration state. `RunContext` references the instrument, method, variant, operator, run parameters, calibration state at run, sample context, and canonical timestamp. These are immutable governed records bound by `version_id` into the snapshot. Vendor-native raw files are source artifacts referenced by these records; vendor parser/adapters are not part of Build 0 (§18).

Build 0 calibration eligibility is derived from an immutable `CalibrationRecord` and snapshot-bound `CalibrationValidityPolicy`. A calibrated record carries an inclusive `valid_from`/`valid_until` interval; a pre-interval run is `INVALID`, a post-interval run is `STALE`, and only an in-interval run is `VALID`. Explicit `INVALID` and `UNAVAILABLE` records carry no validity interval. Gate precedence is fixed: ratification/integrity → calibration → MSA → candidate loading/scoring. Stale or invalid calibration returns `STALE_OR_INVALID_CALIBRATION`; unavailable calibration returns `MISSING_REQUIRED_EVIDENCE`. No downstream MSA or candidate state may override an earlier gate.

The canonical evaluation embedded in Tier 1 decisions is the following closed schema:

```python
class CalibrationTruth(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"

class CalibrationEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: CalibrationTruth
    calibration_ref: GovernedRef
    policy_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]
```

`calibration_ref` always identifies the evaluated immutable `CalibrationRecord`, including an explicit `UNAVAILABLE` record; unavailable is evidence state, not absence of a record. `evidence_refs` is non-empty, unique, sorted by complete governed reference, and contains both `calibration_ref` and `policy_ref`. Validity bounds and the evaluation time are not duplicated in this object: they remain in the cited calibration record and decision header bound into the same snapshot.

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
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp

class RuleOutEvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requirement_ref: GovernedRef
    candidate_ref: GovernedRef
    required_discriminator_refs: list[GovernedRef]
    aggregation: Literal["ALL_CONSISTENT_WITH_REAL"]
    tau_ruleout_policy_ref: GovernedRef
    evidence_refs: list[GovernedRef]

class HardEliminationRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_ref: GovernedRef
    candidate_ref: GovernedRef
    predicate_ref: GovernedRef
    predicate: Predicate
    evidence_refs: list[GovernedRef]

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
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    supersedes_version_id: VersionId | None
```

Each failure mode resolves exactly one `RuleOutEvidenceRequirement`; Build 0 rule-out requires every named discriminator to resolve `CONSISTENT_WITH_REAL` and support to be at or below that requirement's governed `tau_ruleout`. The required list MUST be non-empty and a discriminator cannot be borrowed from another candidate. A low support score alone never satisfies rule-out.

A `HardEliminationRule` belongs to one published candidate and is evaluated before signature scoring. Only `TRUE` eliminates; `FALSE` leaves the candidate open, `UNKNOWN` supplies no negative evidence, and `INVALID` returns `CONFIGURATION_INVALID`. Every elimination retains the rule, predicate evaluation, exact input evidence, and governing citations.

For a discriminator observation, exactly one of `artifact_predicate` or `real_predicate` may evaluate `TRUE`. If neither is true, the result is `INCONCLUSIVE`. If either is `UNKNOWN`, the result is `INCONCLUSIVE` with missing fields recorded. If both are true, or either is `INVALID`, the pack/run returns `CONFIGURATION_INVALID`; overlapping outcome predicates are also a pack-publication error when statically detectable.

`CONFIRMED` is unreachable without a passing structured confirm test or an active governed attestation. The attester role MUST be allowed by the snapshot-bound role policy. The attester MUST NOT be the author or approver of the governing failure-mode record. Revoked or superseded attestations cannot satisfy a confirm test.

`AuthorizedRolePolicy` binds allowed governed roles to the exact method. `RoleAuthorizationEvent` binds actor, role, and policy with effective time, recorded time, state, and explicit supersession. Discriminator-result, role-authorization, and attestation chains have one root, monotonic version order, stable bound identity, and at most one successor per version. Eligibility uses only events with both timestamps at or before `as_of_time`; the unique unsuperseded head controls state. Missing supersession targets, forks, multiple active authorizations, multiple satisfying attestations, observation/result disagreement, or contradictory unsuperseded results are `INTEGRITY_FAILURE`.

### 7.6 MSA Hard Precondition [OWNER DECISION]
`MSAStudy` references method, measurand, range, conditions, study type, measured uncertainty, class-appropriate capability evidence, applicability predicate, optional selection group, precedence rank when grouped, qualification state, **qualification-scope reference**, effective time, and expiration time. One global Gage R&R rule is prohibited: `QUANT_NONDESTRUCTIVE` uses a governed Gage R&R contract; `DESTRUCTIVE` uses nested-design reproducibility; `QUALITATIVE` uses governed attribute agreement; `CONDITION_SENSITIVE` uses a per-condition uncertainty contract.

`MethodMeasurementContract` binds the exact method, implemented-MSA class, and deviation field used by the gate. `ImplementedMSAClassRegistry` is bound to the running engine ID/version. Runtime MSA failure-reason precedence is an explicit ordered field of the snapshot-bound route policy; application branch order is not policy. Measurement comparisons convert deviation and uncertainty through the snapshot unit registry into the contract measurand's canonical unit, use canonical `Decimal`, and retain both compared values and the selected study reference in the decision.

No qualified, applicable MSA study of a class implemented by the running engine **and valid for the run's bound evidence scope** means Tier 1 SHALL NOT issue an investigation verdict. It returns `RefusalDecision{verdict="REFUSED", refusal_type="MSA_UNCHARACTERIZED"}`; Tier 2 advisory MAY also run. Build 0 implements `QUANT_NONDESTRUCTIVE` only. Eligibility is earned per method; no application default bypass exists.

A synthetic MSA fixture MAY be qualified only inside an isolated governed `TEST_FIXTURE` evidence scope. That study can satisfy the gate only for a run bound to the identical scope and always forces `operational_mode = RESEARCH_ONLY`. It cannot satisfy a bench, vendor, company, or production-scoped run. Scope mismatch behaves as no applicable qualified study. This is test data isolation, not an MSA bypass.

### 7.7 Cases and Snapshots
`TriageCase` references intake, tier, run context, pack version, engine version, knowledge snapshot, MSA result, candidates, discriminator results, canonical result, actions, provenance, and non-dispositional state. `KnowledgeSnapshot` binds every exact governed `version_id` and `content_hash` used, plus engine policy, algorithms, unit registry, precision/rounding policy, serialization policy, lexical policy, and explicit `as_of_time`.

Governed records are immutable. Any correction creates a new `version_id` under the same `logical_id`; mutation of a published version is prohibited. The snapshot references specific versions only. A content-hash mismatch is tamper evidence and returns `INTEGRITY_FAILURE`. Replay never resolves an implicit latest version.

Build 0 exact replay uses a separately versioned replay capsule stored atomically beside the immutable run. The capsule preserves the complete typed executable request, runtime, policy, and query, including explicit null input fields required to reconstruct existing closed schemas; its metadata binds the complete governed replay-policy reference, recipe schema, and algorithm ID. It is reconstruction material, not a decision input: it does not enter the original snapshot, decision, advisory, or audit hash. `BUILD0_EXACT_REPLAY_V1` re-executes only that capsule and compares canonical output, snapshot, audit, citation, and bound-version bytes. It performs no network retrieval, accepts no latest-version resolver, and cannot substitute current pack or lifecycle state. Capsule absence, checksum failure, schema/algorithm/policy unavailability, missing bound content, or re-execution drift returns `INTEGRITY_FAILURE` without changing the original run.

`gptl.replay-recipe.v1` is a closed discriminated union selected by `recipe_kind`:

```python
class SafeRefusalReplayRecipe(BaseModel):
    recipe_kind: Literal["SAFE_REFUSAL"]
    request: SafeRefusalRequest
    pack_registry: ExactPackRegistry
    policy: SafeRefusalPolicy

class CandidatePreservationReplayRecipe(BaseModel):
    recipe_kind: Literal["CANDIDATE_PRESERVATION"]
    request: Slice2Request
    runtime: Slice2Runtime
    policy: Slice2Policy

class MSAGateReplayRecipe(BaseModel):
    recipe_kind: Literal["MSA_GATE"]
    request: Slice2Request
    runtime: Slice3Runtime
    policy: Slice3Policy

class ArtifactConfirmationReplayRecipe(BaseModel):
    recipe_kind: Literal["ARTIFACT_CONFIRMATION"]
    request: Slice2Request
    runtime: Slice4Runtime
    policy: Slice4Policy

class HonestNegativeReplayRecipe(BaseModel):
    recipe_kind: Literal["HONEST_NEGATIVE"]
    request: Slice2Request
    runtime: Slice5Runtime
    policy: Slice5Policy

class Tier2AdvisoryReplayRecipe(BaseModel):
    recipe_kind: Literal["TIER2_ADVISORY"]
    request: Slice2Request
    query: AdvisoryQuery
    runtime: Slice6Runtime
    policy: Slice6Policy
```

Every recipe and nested member is immutable and `extra="forbid"`. Explicit nulls are retained in recipe bytes because current closed request/runtime schemas distinguish a present no-value field from omission. Capsule metadata stores `run_id`, `algorithm_id`, `recipe_schema_version`, the complete `replay_policy_ref`, SHA-256 of the exact canonical recipe bytes, record type, run schema version, and hash algorithm. The recipe's canonicalization parameters must equal the replay policy's parameters except for policy identity; mismatch is invalid recipe material.

The Build 0 completion evidence publishes two full source-derived schemas for every recipe member above, including all `$defs` reachable through `SafeRefusalRequest`, `ExactPackRegistry`, `SafeRefusalPolicy`, `Slice2Request`, `Slice2Runtime` through `Slice6Runtime`, their policies, and `AdvisoryQuery`. It also publishes the persisted replay-capsule wrapper schema containing `run_id`, `algorithm_id`, `recipe_schema_version`, `replay_policy_ref`, canonical recipe-byte SHA-256, record type, run schema version, and hash algorithm. The **validation-input schema** documents values accepted by Pydantic before canonicalization. The distinct **canonical-wire schema** documents persisted/hashed bytes and replaces every Decimal `anyOf[number,string]` branch with the canonical string branch required by §2.13; JSON numbers are prohibited on that surface. Each artifact carries qualified model identity, both schema digests, and explicit semantic invariants that JSON Schema cannot express, including non-empty/unique/sorted reference sets, coupled optional-field presence, and cross-field evidence membership. A digest without its inspectable schema is insufficient freeze evidence. These schemas are executable evidence of this contract at the audited implementation commit; a schema change requires a new contract/evidence version and never rewrites historical recipes.

Replay compares these byte surfaces: output envelope in stored order; audit events in explicit sequence order; snapshot as one canonical object; citations as a sorted set of canonical citation bytes; and bound versions as a sorted set of canonical complete-`GovernedRef` bytes. Preflight requires snapshot/citation/bound-version surfaces to be absent. Each stored surface carries its own declared record type, schema version, hash algorithm, and SHA-256 digest, all verified before re-execution. The verification result is a separate closed union, never an MIE verdict:

```python
class ReplayVerified(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    replay_id: OpaqueId
    run_id: OpaqueId
    status: Literal["VERIFIED"]
    algorithm_id: Literal["BUILD0_EXACT_REPLAY_V1"]
    replay_policy_ref: GovernedRef
    recipe_schema_version: Literal["gptl.replay-recipe.v1"]
    source_run_schema_version: OpaqueId
    output_hash: Sha256Hex
    snapshot_hash: Sha256Hex | None
    bound_version_refs: tuple[GovernedRef, ...]

class ReplayIntegrityFailure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    replay_id: OpaqueId
    run_id: OpaqueId
    status: Literal["INTEGRITY_FAILURE"]
    algorithm_id: Literal["BUILD0_EXACT_REPLAY_V1"]
    replay_policy_ref: GovernedRef
    reason_id: TermId
```

For `ReplayVerified`, snapshot hash and non-empty sorted unique bound-version references appear together; both are absent for preflight. Audit, citation, and bound-version byte equality are verified before success even though their individual hashes are not duplicated into the result. Any failed metadata, digest, schema, canonical-form, availability, or byte comparison returns only `ReplayIntegrityFailure` and never reconstructs or modifies an engineering decision.

---

## 8. Deterministic MIE Pipeline (Diagnostic Engine)

### 8.0 Step 0 — Integrity and Tier Routing
Validate schema, actor, pack version, hashes, method identity, units, required fields, ratification status, calibration, and implemented MSA class; confirm a fully resolved pack with no missing policy; route in the fixed precedence order; no runtime default injection.

### 8.1 Step 1 — Snapshot
Create `DecisionRun`; bind the immutable content-hashed `KnowledgeSnapshot`, including exact `version_id` references, before evaluation.

### 8.1A Calibration Precondition (hard gate, §7.4)
After ratification and integrity succeed, evaluate the snapshot-bound calibration record under its governed validity policy. Only `VALID` proceeds. `STALE` or `INVALID` returns `REFUSED{STALE_OR_INVALID_CALIBRATION}`. `UNAVAILABLE` returns `REFUSED{MISSING_REQUIRED_EVIDENCE}` with the governed calibration-unavailable route reason. MSA is not evaluated on a failed calibration route.

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

For the bounded negative gate, `total_high_power` is enumerated from every applicable published candidate before considering which candidates reached discriminator execution. A hard-eliminated candidate therefore remains in the known denominator; its unevaluated discriminators count unanswered rather than disappearing. An empty or otherwise unenumerable denominator is `CONFIGURATION_INVALID`, never a fabricated zero or one.

- **`METHOD_ARTIFACT`**: a confirmed dominant candidate (support ≥ `tau_verdict`, dominance margin ≥ `delta_dom` over the next evaluable candidate), required coverage, satisfied confirm test, and no unresolved applicability that could change dominance.
- **`KNOWN_ARTIFACTS_EXCLUDED`** (cited coverage record, not a determination of real behavior): every candidate in the `published_candidate_set` is explicitly `ELIMINATED` or `RULED_OUT`; no candidate is `OPEN_UNASSESSED` or `APPLICABILITY_UNRESOLVED`; `evaluated_fraction_within_published_catalog` meets the governed minimum; and the mandatory boundary fields are present (§9). It asserts only that the published catalog did not explain the anomaly after the recorded investigation.
- Otherwise **`INDETERMINATE`** with open discriminators and the facts to continue.

`CONFIRMED` describes each candidate independently. A `METHOD_ARTIFACT` verdict names exactly one confirmed candidate that also satisfies the verdict threshold and dominance margin. Other candidates MAY remain `CONFIRMED` when they satisfy their own confirmation contracts but are not verdict-dominant; their assessments remain visible in the canonical result.

### 8.9 Step 9 — Canonical Result and Rendering
Build, canonically serialize, and persist the authoritative structured result first. Optional prose rendering occurs afterward into a separate non-authoritative `RenderedArtifact`; it cannot modify the decision.

Failure to construct a closed-schema authoritative result from otherwise accepted internal state is `REFUSED{ENGINE_FAILURE}` with a governed route reason and human action. It is not `CONFIGURATION_INVALID`, because no external configuration correction can repair an engine invariant violation. Rendering is outside this boundary and cannot be required to produce or validate the structured result.

---

## 9. Canonical Output Contract

All models use `extra="forbid"` and immutable values recursively. All numerics are `Decimal`. Authoritative maps are prohibited; governed keyed values use sorted typed arrays. Authoritative prose is prohibited.

```python
class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_type_id: TermId
    record_ref: GovernedRef
    evidence_location: EvidenceLocator

class RefusalType(str, Enum):
    MSA_UNCHARACTERIZED = "MSA_UNCHARACTERIZED"
    UNKNOWN_METHOD_OR_FAILURE_MODE = "UNKNOWN_METHOD_OR_FAILURE_MODE"
    MISSING_REQUIRED_EVIDENCE = "MISSING_REQUIRED_EVIDENCE"
    STALE_OR_INVALID_CALIBRATION = "STALE_OR_INVALID_CALIBRATION"
    PACK_VERSION_UNAVAILABLE = "PACK_VERSION_UNAVAILABLE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    ENGINE_FAILURE = "ENGINE_FAILURE"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"

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
    route_reason_id: TermId
    calibration_evaluation: CalibrationEvaluation
    msa_applicability_evaluations: list[ApplicabilityEvaluation]
    assessments: list[CandidateAssessment]
    citations: list[Citation]
    missing_field_ids: list[FieldId]
    required_human_action: DisplayDirective
    audit_event_ids: list[OpaqueId]

class MethodArtifactDecision(MIEDecisionBase):
    verdict: Literal["METHOD_ARTIFACT"]
    msa_study_ref: GovernedRef
    measured_deviation: Decimal
    measured_uncertainty: Decimal
    uncertainty_unit_id: UnitId
    diagnostic_state_hash: Sha256Hex
    confirmed_candidate_ref: GovernedRef
    evaluated_fraction_within_published_catalog: Decimal
    confirm_evidence: list[Citation]
    what_would_change_this: list[DisplayDirective]

class KnownArtifactsExcludedDecision(MIEDecisionBase):
    verdict: Literal["KNOWN_ARTIFACTS_EXCLUDED"]
    artifacts_evaluated: list[EvaluatedArtifact]
    known_unevaluated_gaps: list[KnownGap]
    catalog_boundary: DisplayDirective
    evaluated_fraction_within_published_catalog: Decimal

class IndeterminateDecision(MIEDecisionBase):
    verdict: Literal["INDETERMINATE"]
    msa_study_ref: GovernedRef
    measured_deviation: Decimal
    measured_uncertainty: Decimal
    uncertainty_unit_id: UnitId
    diagnostic_state_hash: Sha256Hex | None
    open_discriminator_refs: list[GovernedRef]

class WithinMeasurementVariationDecision(MIEDecisionBase):
    verdict: Literal["WITHIN_MEASUREMENT_VARIATION"]
    msa_study_ref: GovernedRef
    measured_deviation: Decimal
    measured_uncertainty: Decimal
    uncertainty_unit_id: UnitId

class RefusalDecision(DecisionHeader):
    verdict: Literal["REFUSED"]
    refusal_type: RefusalType
    context: RefusalContext
    method_ref: GovernedRef | None
    route_reason_id: TermId | None
    calibration_evaluation: CalibrationEvaluation | None
    msa_applicability_evaluations: list[ApplicabilityEvaluation] | None
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

`MIEOutput` is the complete persisted output envelope for one `DecisionRun`. Exactly one union member is stored under that run identity. A Tier 2 run's deterministic Tier 1 eligibility attempt (§5.1) is replay input to advisory construction, not a second output envelope and not an omitted member of a compound record.

Canonical list sort keys are normative: governed references by `(logical_id, version_id)`; citations by `(record_type_id, logical_id, version_id, evidence_location)`; candidate assessments by candidate reference; display parameters by `key_id`; directives by `(template_id, canonical params)`; IDs and terms lexicographically under §2.13. A schema may declare a different semantic order only when order itself carries domain meaning, in which case the order field is explicit and governed.

Sort keys are not identity substitutes. Any two governed references sharing `(logical_id, version_id)` but differing in `version_number` or `content_hash` are an integrity conflict, and evidence/citation intersections compare the complete `GovernedRef`. A governed record's `evidence_refs` are bound into the snapshot for replay and integrity. They become separate `Citation` rows only when each referenced item has its own governed record type and evidence location; inventing either field is prohibited.

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

Build 0 pack lifecycle selection is exact-version and bitemporal. A `PackLifecycleEvent` names one immutable pack reference, `PUBLISHED|DEPRECATED|REVOKED` state, effective and recorded times, and the exact predecessor event it supersedes. New-run eligibility evaluates only the explicitly requested `version_id` as of both timestamps. A newer published version never silently replaces an older explicitly requested published version; deprecation or revocation blocks new use according to governed reason IDs but cannot alter replay of a run that already bound that version.

---

## 12. Storage and Retrieval
**Build 0 and production storage:** PostgreSQL with migration-controlled schema versions, foreign keys, transactional snapshot binding, primary-key citations, immutable pack versions, and database-enforced append-only decision/audit/replay-capsule records. Snapshot assembly and persistence run in one PostgreSQL transaction on one connection under the connection's default `READ COMMITTED` isolation. Build 0 write transactions acquire a transaction-scoped PostgreSQL advisory lock for the Build 0 writer lane; a competing writer is rejected before any run record is inserted. That lock makes the single-writer profile an enforced repository behavior rather than an operator assumption. Decision-effective records are immutable/append-only, and every selected version is copied into the bound snapshot before commit; a multi-writer or production profile must be owner-ratified separately and may require stricter isolation. Replay capsule count is transactionally enforced, so a replay-qualified run and its exact recipe cannot commit separately. `Decimal` values are stored as canonical strings when part of canonical payloads and as constrained `numeric` only for explicitly non-payload query columns whose conversion is tested. Build 0 is single-writer but uses the same persistence semantics intended for production. **Allowed retrieval:** exact IDs/aliases; FK/relational; range/categorical; controlled-vocabulary joins; deterministic rule evaluation; custom versioned lexical scoring with stable tie-break; optional `tsvector`/trigram acceleration only behind the bounded parity gate in §5.2. **Prohibited:** SQLite/FTS5 in the runtime path; vector similarity/embedding indexes; model-memory assertions; uncited search in a decision path; nearest-match fallback; hidden reranking/unversioned weights; application-code defaults; mutation of a published governed version.

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

Slice 4 computes `diagnostic_state_hash = SHA-256(JCS_UTF8(payload))`, where `payload` is exactly the JSON object with keys `as_of_time`, `active_discriminator_result_refs`, `active_role_authorization_refs`, and `active_attestation_refs`; it contains no hash field. Each reference array contains the complete `GovernedRef` objects resolved from the snapshot-bound event set, unique and sorted by `(logical_id, version_id)`. Decimal normalization is irrelevant because this payload contains no Decimal. String normalization is recursive: every string value and object key inside the payload, including nested `GovernedRef` fields, is normalized to NFC under §2.13 before RFC 8785 serialization, and the timestamp has the bound canonical width. No envelope, model name, current-state value, or insertion order enters the bytes. Slice 3 `INDETERMINATE` records carry no diagnostic state and omit this optional field canonically. Slice 4 `METHOD_ARTIFACT` and diagnostic `INDETERMINATE` records retain the hash so replay proves the same decision-effective authority/evidence state without consulting current state.

Replay verification is a separate typed result, not a new MIE verdict: `VERIFIED` carries the exact source run schema, output hash, optional snapshot hash, and bound references; `INTEGRITY_FAILURE` carries only a governed reason. It never converts replay failure into a reconstructed engineering decision.

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

Build 0 freeze additionally requires a repository-derived evidence manifest bound to an exact source commit and governing-document hashes. It maps every slice gate and completion criterion to exact collected pytest node IDs, records the complete PostgreSQL-backed result and static-gate artifact digests, publishes representative canonical output/snapshot hashes, identifies migration/source/schema digests, and contains no manually asserted pass state. A narrative test count or undocumented local execution cannot close this gate.

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
<!-- END GPTL_SPEC_V0.4.20 -->
---

# Embedded Build 1 Plan

<!-- BEGIN GPTL_BUILD1_PLAN_V0.4 -->
# GPTL MIE Build 1 Plan
## Capability-Profiled Capture & Advisory Contract - v0.4

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20

**Status:** Draft after ORACLE sessions `20260623-040533`, `20260623-185534`, and `20260623-192631`; not an implementation freeze packet

**Build 0 dependency:** Build 0 is frozen by `GPTL_ORACLE_BUILD0_CLOSEOUT_REVIEW_v1.6.md`. Build 1 extends the frozen deterministic spine; it does not reopen Build 0 architecture, verdict semantics, replay, storage, canonicalization, or MSA/calibration gates.

**Operational boundary:** Build 1 remains `RESEARCH_ONLY`, non-dispositional, and not a QMS, quality, flight, or engineering record of record. It may create governed source, proposal, ratification, observation, and validation-protocol records. It does not qualify methods, instruments, MSA studies, vendor parsers, thresholds, process controls, or production actions.

**v0.2 review closeout:** resolves the Build 1 plan defects from ORACLE session `20260623-040533`. Direct instrument-emitted Tier 1 authority is deferred; Build 1 treats instrument/parser output as source-backed proposal material that still requires ratification before Tier 1. Active-value selection is defined by a target key and bind-time head resolution rather than an overclaimed database uniqueness constraint. Capability-profile scope checks, minimal authority policy, correction workflow, observation/protocol promotion through ratification, source-byte storage atomicity, raw-byte hashing, and fail-closed diagnostics are now explicit.

**v0.3 owner closeout:** resolves the remaining Build 1 plan defects from ORACLE session `20260623-185534`. The Build 1 `EvidenceScopeV1` dimension set and exact-match semantics are fixed. Source-derived record identity is limited to explicit existing references, caller-supplied identities, or a deterministic source-local identity recipe; fuzzy merge and entity reconciliation are deferred. Designed-validation acceptance criteria are limited to a small closed predicate-template set. Ratifiable evidence locations are byte/cell-stable only unless a parser/renderer/OCR toolchain is itself bound into the replay surface. Build 1 authority records represent claimed actor attribution against a governed local registry, not authenticated signatures. Active-value conflicts are resolved only by later correction/supersession events in later runs; historical conflicts replay as conflicts.

**v0.4 owner closeout:** resolves the blocked Build 1 plan findings from ORACLE session `20260623-192631` with conservative implementation choices. `SOURCE_LOCAL_RECORD_IDENTITY_V1` now requires an evidence-backed `source_local_record_key` so multiple records in one artifact do not collapse and value corrections do not mint new logical identities. Parser-derived proposals bind an exact `parse_attempt_ref`, and parser/decoder/identity/canonicalization algorithms resolve through governed executable registry entries rather than bare strings. Capability profiles no longer define calibration/MSA policy. The Build 0 bridge no longer assumes a shared transaction; it uses a deterministic narrowed-boundary bridge attempt when the frozen Build 0 engine owns its persistence boundary.

---

## 1. Purpose

Build 1 turns the v0.4.20 Build 1 paragraph into executable vertical slices:

> Source registration and evidence-grounded proposals; human validation/ratification; governed designed-validation protocols; attributed-observation ingestion (`UNVALIDATED`, Tier-2-only); deterministic custom lexical Tier 2 retrieval; optional Bouncer and renderer adapters. Vendor-specific instrument adapters MAY begin here only from real, legally usable source files and MUST preserve the raw artifact and provenance.

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
  GPTL_BUILD1_PLAN_v0.4.md
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

### Exit Gate

- A profile with no declared capability cannot silently allow intake.
- Unknown and unsupported capabilities are distinct states.
- Missing capability produces a typed advisory gap, never a guessed source path.
- Calibration/MSA capability labels cannot satisfy, override, or redefine the frozen Build 0 calibration/MSA gates.
- Capability lists are canonical, unique, and order-independent.
- Scope mismatch, inactive lifecycle state, missing owner, or missing authority policy fails before source/proposal selection.
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
- Claimed proposer/extractor actor reference when available, proposal method, and creation event reference.
- Proposed target descriptor: target record type, target logical ID, target schema version, semantic field path, and `context_key`.
- Proposed typed value with unit and canonical timestamp policy where applicable.
- Evidence location in the source artifact using the closed `ProposalEvidenceV1` locator set.
- Validation state: `PROPOSED`, `VALIDATION_FAILED`, `READY_FOR_RATIFICATION`, `REJECTED`, `SUPERSEDED`.
- Validation errors with governed reason IDs.

`context_key` is the canonical object containing every schema-declared dimension needed to distinguish multiple values for the same target field. Examples include sample side, measurement replicate, process step, parameter channel, specimen ID, or condition set. If the target schema declares no disambiguating dimensions, `context_key` is the explicit empty object. The target schema owns the allowed keys, value types, and canonical sort order. Unknown, missing, extra, or non-canonical context dimensions make the proposal invalid rather than being collapsed into the same target or split into ungoverned fragments.

`context_key` canonical bytes are computed before identity validation, active-value conflict detection, replay hashing, or bridge assembly. The same semantic context must serialize to the same bytes independent of input order. A non-canonical `context_key` is `CONFIGURATION_INVALID`, not a best-effort warning.

The active-value conflict key is target record type, target logical ID, semantic field path, and canonical `context_key`. Target schema version is retained for validation and wire compatibility, but it cannot split active heads for the same semantic target. If a future schema version changes field meaning, a governed schema-continuity map must either map it to the same semantic field path or declare it incompatible before publication.

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

PostgreSQL enforces immutable event identity and duplicate primary keys; it does not claim to prove every bitemporal active-head uniqueness question with a static constraint. Build 1 write transactions use the single-writer persistence lane, and bind-time active-value resolution is the authoritative conflict check.

`CORRECTION_REQUESTED` is terminal for the proposal version it references. The corrected content is submitted as a new `TypedValueProposal` with `corrects_proposal_ref`; historical rejection/correction events remain visible and replayable.

`ACTIVE_VALUE_CONFLICT` is resolved in-band only by a later correction or supersession event that leaves exactly one active `RATIFIED` head for a later run. The conflicting historical run remains a fail-closed conflict under replay.

### Exit Gate

- Ratification verifies the proposal content hash before eligibility.
- Ratification verifies authority policy, authorization event, role assignment, and separation-of-duties records from the bound snapshot.
- Single-actor ratification records the explicit policy basis and cannot be reported as independent review.
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
- Passes only actively ratified typed values into Tier 1.
- Passes unvalidated observations only to Tier 2 advisory context.
- Emits explicit capture/advisory gaps for unknown/unsupported capabilities, unsupported source artifacts, missing parser, or missing ratification.
- Defers calibration/MSA eligibility decisions to the frozen Build 0 engine once a valid Build 0 request exists.

Every bridge refusal/advisory gap carries a minimal diagnostic payload: governed reason ID, affected target key or capability reference when applicable, conflicting active ratification heads when applicable, missing source/proposal/profile reference when applicable, and the next required governed record type. Diagnostics explain the fail-closed state; they do not create authority.

`CaptureGateResult` is a closed Build 1 result object, not a new MIE verdict. It records all capture-stage findings for one bridge attempt: capability resolution, scope check, identity resolution, evidence-locator ratifiability, active-value resolution, authority eligibility, observation containment, validation-protocol status, parser status, and proposal lineage. It may carry multiple findings.

Capture gate classification is closed and deterministic:

- Integrity failures, scope incompatibility, authority ineligibility, identity collision, unresolved identity for a requested Tier 1 target, non-ratifiable evidence for a ratified proposal, and active-value conflict are fail-closed `CaptureGateResult` states. They produce no Build 0 request.
- Missing ratification, unsupported/unknown/ambiguous capability, parser unavailable/unsupported/failed, and advisory-only observations are capture/advisory gaps. They produce no Tier 1 Build 0 value and no negative evidence.
- Missing calibration or MSA after a valid Build 0 request exists is not decided by Build 1. It is reported only through the frozen Build 0 calibration/MSA decision path and replay capsule.

Precedence is deterministic: integrity failure, scope incompatibility, authority ineligible, identity unresolved/collision, evidence locator not ratifiable, active-value conflict, missing ratification, capability unsupported/unknown/ambiguous, parser unavailable/unsupported/failed, then advisory-only observations.

`BridgeAttemptRecord` is the Build 1-to-Build 0 persistence contract. Its closed lifecycle states are `CAPTURE_BOUND`, `BUILD0_REQUEST_CREATED`, `BUILD0_PERSISTED`, `FINALIZED`, and `BUILD0_FAILED`. Build 1 does not require Build 0 to share the caller's database transaction. If the frozen Build 0 engine exposes a pure in-process call over a caller-supplied unit of work with no independent commit, the implementation may store the Build 1 capsule and Build 0 run atomically in that shared unit of work. Otherwise Build 1 uses the narrowed-boundary fallback:

1. Commit the Build 1 capture records, `CaptureGateResult`, generated Build 0 request, and request hash as `CAPTURE_BOUND`.
2. Mark the exact Build 0 request and idempotency key as `BUILD0_REQUEST_CREATED` before invocation.
3. Invoke the frozen Build 0 engine with that exact request and idempotency key.
4. On Build 0 success, record the Build 0 run reference and replay capsule hash as `BUILD0_PERSISTED`, then finalize the bridge attempt as `FINALIZED`.
5. On Build 0 failure, record `BUILD0_FAILED` with error reason and leave the original request hash immutable.
6. A retry must use the same bridge attempt, Build 0 request hash, and idempotency key. A different request under the same attempt is `INTEGRITY_FAILURE`.

`Build1BridgeReplayCapsule` binds the upstream capture-to-engine chain: capability profile, scope, source records and raw byte hashes, parse attempts, algorithm registry entries, proposal records, proposal evidence locators and derived hashes, identity recipe inputs/results, authority policy and authorization events, ratification events, observations, validation protocols/results, capture gate result, bridge attempt state, generated Build 0 request, and the existing Build 0 replay capsule reference when one exists. Algorithm ID is `BUILD1_EXACT_REPLAY_V1`.

### Exit Gate

- A complete ratified fixture reaches the existing Build 0 path unchanged.
- An equivalent unratified fixture stops before Tier 1.
- Unsupported capability appears as an advisory gap and never as negative evidence.
- Wrong-scope capability profile, missing authority policy, undefined context key, and active-value conflict each fail before Build 0 with diagnostics.
- A bridge retry with a changed Build 0 request hash fails closed.
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

`BUILD1_EXACT_REPLAY_V1` verifies canonical bytes for source records, raw byte hashes, parse attempts, algorithm registry entries, proposal records, evidence locator derived hashes, source-local identity recipe inputs/outputs, authority/authorization/ratification state, observation records, validation protocol/result records, capture gate result, bridge attempt state, Build 0 request, Build 0 replay capsule reference when present, and rendered-artifact separation when present. Tampering, missing records, missing raw bytes, derived locator drift, authority drift, active-value drift, bridge-attempt drift, or Build 0 request drift returns `INTEGRITY_FAILURE` without producing or modifying a MIE verdict.

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
| Proposed record identity recipes | 3 | §§2.12–2.13, 6 |
| Replay-stable evidence locators | 3, 8 | §§2.5, 2.12–2.13, 11 |
| Evidence-location requirement | 3 | §§2.5, 11 |
| Model-disabled equivalence | 3, 7 | §§2.3, 2.12 |
| Human ratification event | 4 | §§2.4, 6, 11 |
| Minimal authority policy | 4 | §§2.4, 6, 11 |
| Snapshot-bound authorization events | 4 | §§2.4, 2.12, 11 |
| Bitemporal ratification eligibility | 4 | §§2.4, 2.12 |
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
| Advisory gaps for missing capability/evidence | 7 | §§2.7, 2.9, 9 |
| Build 1 replay and evidence closeout | 8 | §§2.12–2.13, 12, 17 |

---

## 13. Build 1 Completion Gate

Build 1 is complete only when:

1. Every slice gate passes locally against PostgreSQL.
2. All Build 0 tests still pass unchanged.
3. Every new Build 1 record has a closed schema, semantic scalar types, explicit lifecycle enum, canonical list sort keys, validation-input schema, canonical-wire schema, and published non-schema semantic invariants.
4. Every raw source record preserves exact received bytes, raw content hash, and provenance in one PostgreSQL transaction.
5. Source registration enforces governed max-byte limits while reading and never buffers unbounded payloads before rejection.
6. Every parser-derived proposal binds an exact `parse_attempt_ref`, and every parser/decoder/identity/canonicalization behavior resolves through a governed executable algorithm registry entry.
7. Every typed proposal cites a ratifiable `ProposalEvidenceV1` locator or remains proposal-only.
8. Every new proposed target identity resolves through an existing governed reference, caller-supplied identity, or `SOURCE_LOCAL_RECORD_IDENTITY_V1` with an evidence-backed `source_local_record_key`; unresolved or colliding identity fails closed.
9. No value enters Tier 1 without active ratification resolved through governed authority policy and snapshot-bound authorization records.
10. Unvalidated attributed observations are Tier-2-only and never change the frozen `AdvisoryDecision` schema.
11. Unknown/unsupported/wrong-scope capability produces explicit advisory gap, not inferred support or inferred absence.
12. Designed validation protocols use only `VALIDATION_PREDICATE_TEMPLATES_V1` and cannot qualify a method, production process, or bypass ratification.
13. Bridge retries are idempotent by immutable Build 0 request hash and cannot silently generate a different request under the same attempt.
14. Removing model adapters changes no structured output.
15. Static scans find no vector implementation, SQLite fallback, domain constants, module-local scope logic, module-local identity recipes, or user-defined predicate engines in generic modules.
16. Build 1 replay detects tampering and missing source/proposal/ratification/authority/authorization/observation/protocol/capture-gate/bridge-attempt records and detects locator-derived hash drift.
17. Generated Build 1 completion evidence binds exact source commit, governing-document hashes, dependency lockfile, migrations, test inventory, gate map, validation and canonical-wire schemas, replay recipes, canonical samples, and cross-minor fixture equality.

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

1. Does Build 1 v0.4 implement the existing v0.4.20 Build 1 contract, or does it accidentally introduce new architecture?
2. Are any Build 1 slices attempting Build 2 qualification or Build 3 production concerns too early?
3. Does the plan preserve the Build 0 firewall: no unratified value, model output, missing capability, or unvalidated observation can enter Tier 1?
4. Are the proposed record types sufficient to preserve source provenance, typed proposals, target/context keys, proposed identity, ratification, authority policy, authorization events, observations, validation predicates, capture-gate results, and replay?
5. Does any gate rely on hidden defaults, magic values, vectors, model authority, SQLite fallback, or vendor assumptions?
6. Is the "choose your tools" capability profile deterministic enough to proceed before knowing a specific lab's equipment list?
7. What is the smallest correction that would make this plan implementation-ready without pulling Build 2/3 work into Build 1?

Findings should cite the exact plan section and governing spec section, classify severity as `BLOCKER|MAJOR|MINOR|NIT`, and distinguish true contradictions from preferences or deferred production work.
<!-- END GPTL_BUILD1_PLAN_V0.4 -->
