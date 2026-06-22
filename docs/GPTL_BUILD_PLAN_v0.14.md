# GPTL MIE Build 0 Plan
## Vertical-Slice Implementation Contract — v0.14

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.14

**Status:** Post-ORACLE Build 0 baseline; Slices 1–7 implemented

**Operational boundary:** Every Build 0 output is `RESEARCH_ONLY`, non-dispositional, and not a QMS or engineering record of record.

**Review basis:** ORACLE session `20260621-192749`; eight accepted build-plan defects incorporated. v0.4 closed the remaining preflight-persistence, routing-matrix, requirement-ownership, and lexical-determinism ambiguities. **v0.5 owner decision:** PostgreSQL replaces SQLite for Build 0; no SQLite/FTS5 runtime or test fallback is permitted. **v0.6 Slice 2 review closeout:** runtime-invalid applicability is retained as typed evidence, integrity precedes ratification-state resolution, and event eligibility is bitemporal.

Snapshot-bound outputs introduced by this revision are stored as `gptl.slice2.v2`. Persistence readers retain verified read compatibility with immutable `gptl.slice2.v1` records; no migration rewrites historical payloads.

**v0.7 Slice 3 closeout:** calibration eligibility, method measurement contracts, MSA class support, scope/qualification/applicability selection, and exact uncertainty comparison are implemented as deterministic snapshot-bound gates. Slice 3 writes `gptl.slice3.v1`; readers retain verified compatibility with Slice 2 v1/v2.

**v0.8 Slice 4 closeout:** exact signature coverage, set-wise discriminator aggregation, explicit supersession, structured and human-attested confirmation, bitemporal role authority, separation of duties, exact confirmation/dominance gates, and cited `METHOD_ARTIFACT` output are implemented. All domain numerics resolve through provenance-complete snapshot-bound policies. Slice 4 writes `gptl.slice4.v1`; readers retain verified compatibility with Slice 2 v1/v2 and Slice 3 v1.

**v0.9 Slice 4 review closeout:** candidate confirmation and verdict dominance are explicitly separate gates. One dominant confirmed winner may coexist with lower-support confirmed candidates, all assessments remain canonical evidence, and engine-generated schema failures return governed `ENGINE_FAILURE`. Adversarial coverage now pins the two-confirmed path, partial required evidence, duplicate active authorities, and renderer independence.

**v0.10 Slice 5 closeout:** governed hard-elimination rules execute before scoring; exact rule-out contracts require low-enough support plus all named real-consistent discriminators; catalog coverage uses a known published denominator; positive artifact routing retains precedence; and cited `KNOWN_ARTIFACTS_EXCLUDED` outputs retain named dark-space gaps and governed boundary/action directives. Slice 5 writes `gptl.slice5.v1`; readers retain verified compatibility with every prior snapshot-bound schema.

**v0.11 Slice 5 review closeout:** tests explicitly prohibit real-material claims, pin exact gap categories and continuation directives, exercise uncited terminal exclusions through governed `ENGINE_FAILURE`, and reject unregistered boundary, gap, and action directives. Citation intersections use complete governed-reference equality across Slices 3–5. Bare evidence references remain snapshot-bound and are not promoted into citations without independently governed citation metadata.

**v0.13 Slice 6 review closeout:** Tier 2 retains the implemented model-free retrieval and eligibility behavior while making two hidden assumptions fail closed. Lexical policy now binds frozen UCD 3.2.0 normalization, independent of the running CPython minor. A resolved advisory accepts only a Tier 1 refusal; a positive Tier 1 verdict cannot be consumed or replaced by an advisory route. Regression tests recompute every ineligible fixture's canonical advisory hash and pin public Slice 6 contracts. Slice 6 remains `gptl.slice6.v1`; no historical payload is rewritten.

**v0.14 Slice 7 closeout:** exact typed replay recipes for Slices 1–6 are stored atomically with replay-qualified runs in append-only PostgreSQL capsules. `BUILD0_EXACT_REPLAY_V1` re-executes without network or latest-version lookup and compares every persisted output, snapshot, audit, citation, and bound-version byte. Tampering, missing content, missing recipes, unavailable algorithms, and drift return governed integrity failures. Explicit pack lifecycle and correction fixtures prove new versions and later events affect new runs without rewriting history.

---

## 1. Purpose

This plan translates the MIE Build 0 contract into independently verifiable vertical slices. It does not amend v0.4.14, create domain policy, qualify a method, or define vendor instrument formats. When this plan and v0.4.14 conflict, v0.4.14 governs and implementation stops until the conflict is resolved explicitly.

A vertical slice begins with a typed request or governed fixture and ends with:

1. A closed-schema output or explicit refusal.
2. Canonical serialization and a recorded hash.
3. Append-only audit evidence sufficient to explain the path.
4. Local deterministic acceptance tests.
5. A runnable demonstration command.

No slice is complete because its internal classes exist. It is complete only when its external behavior and failure paths satisfy the slice exit gate.

---

## 2. Build Rules

These rules apply to every slice and are not deferred:

- No FAISS, embeddings, vector database, similarity retrieval, or nearest-match fallback.
- No model output in candidate generation, applicability, scoring, confirmation, verdicts, or canonical payloads.
- No `float` in decision arithmetic or canonical decision data.
- No application default for domain policy, thresholds, units, evidence requirements, or applicability.
- No authoritative free text. Human prose exists only in a separate `RenderedArtifact`.
- No implicit latest-version lookup. Every governed input is an explicit immutable version.
- No missing value is converted to negative evidence.
- Applicability `UNKNOWN` never becomes `FALSE`.
- A candidate without required evidence remains `OPEN_UNASSESSED`.
- No authoritative value enters Tier 1 unless it is instrument-emitted or has a snapshot-bound active `RatificationEvent`.
- Every run binds a fixed `as_of_time`. Ratification, attestation, role authorization, calibration, revocation, and supersession are evaluated against the exact event/policy versions in that run's snapshot.
- A later event never changes historical replay. It affects new runs and may mark an old run stale through a separate lifecycle record without mutating the old decision.
- Every synthetic/reference fixture identifies its fixture class and cannot claim vendor or production fidelity.
- Synthetic MSA and diagnostic data are bound to an isolated governed `TEST_FIXTURE` evidence scope and cannot satisfy any non-test run.
- Tests run locally. This plan adds no CI service or deployment automation.

Any implementation pressure to weaken one of these rules is a stop condition, not an engineering tradeoff to resolve inside code.

---

## 3. Target Repository Shape

The structure is directional, not permission to create empty placeholder modules. A path is introduced only by the slice that first exercises it.

```text
src/gptl/
  core/
    semantic_types.py       constrained IDs, hashes, timestamps, Decimal policy
    canonical.py            RFC 8785 normalization, serialization, hashing
    records.py              identity/version and governed references
    ratification.py         ratification events and Tier 1 input gating
    directives.py           governed display-template registry
    snapshot.py             immutable snapshot binding
    persistence.py          atomic append-only PostgreSQL run store
    audit.py                append-only events and decision envelopes
  mie/
    schema.py               MIE records and output unions
    predicates.py           four-state applicability AST evaluator
    selection.py            selection-group resolution and candidate loading
    candidates.py           published candidate-set construction
    calibration.py          calibration-state validation and routing
    msa.py                  MSA applicability and hard gate
    advisory.py             deterministic Tier 2 catalog and resolver contracts
    diagnostics.py          signature, aggregation, authority, and confirmation contracts
    negative.py             elimination and bounded-catalog rule-out contracts
    service.py              safe-refusal orchestration
    slice2_service.py       candidate preservation and snapshot-bound intake
    slice3_service.py       calibration and MSA orchestration
    slice4_service.py       diagnostic evaluation and positive routing
    slice5_service.py       honest bounded-negative routing
    slice6_service.py       model-free advisory retrieval and eligibility guidance
    replay.py               exact-input re-execution and pack-lifecycle integrity
packs/reference/mie/        governed synthetic/reference pack data
tests/
  conformance/              cross-cutting invariant tests
  slices/                   slice acceptance tests
  fixtures/                 typed inputs and expected canonical outputs
scripts/                    local demonstration entry points only
```

Domain facts, thresholds, method records, failure modes, discriminators, MSA evidence, calibration policy, role policy, lexical policy, and display templates belong in packs/fixtures, never generic engine modules.

---

## 4. Slice Exit Protocol

Each slice change must include:

- **Scope:** the exact requirements owned by the slice.
- **Input:** a committed typed fixture or generated request with fixed `as_of_time`.
- **Expected output:** committed canonical JSON or an exact schema assertion.
- **Decision trace:** governed references and audit events explaining the outcome.
- **Tests:** happy path, required refusal path, boundary path, deterministic replay within the slice.
- **Demonstration:** one local command documented in the slice README or test.
- **Non-goals:** behavior deliberately deferred to a named later slice.
- **Stop conditions:** ambiguity that requires a spec amendment or governed policy not yet available.

Persistence is substrate, not Slice 7 polish. Slice 1 establishes decision/audit durability; Slice 2 adds transactional snapshot binding. The minimum storage contract is:

1. Every run has immutable `run_id` and fixed `as_of_time`.
2. Every run atomically persists its canonical output envelope, envelope hash, and audit events.
3. A `PREFLIGHT` refusal persists **no** fabricated snapshot, citation, pack/policy reference, or bound-version set. Their absence is represented by the refusal context and database constraints.
4. A `SNAPSHOT_BOUND` run atomically persists the output envelope, knowledge snapshot, citations, resolved bound-version set, and audit events.
5. A partial transaction is never readable or replayable. PostgreSQL transaction abort/restart rolls it back.
6. Committed run, output, snapshot, citation, and audit rows are insert-only. Database triggers reject update/delete, in addition to repository API restrictions.
7. Build 0 is single-writer over PostgreSQL. Concurrent-writer qualification and distributed work are outside Build 0.
8. Each persisted payload stores its schema version, canonical SHA-256 checksum, and record type.
9. PostgreSQL migrations are forward-only and never rewrite committed historical rows.

Tests receive a PostgreSQL connection URL explicitly. There is no application database URL default and no SQLite fallback. Local acceptance tests MAY create an ephemeral user-owned PostgreSQL cluster, but the resulting URL is still passed explicitly to the store.

Decision-effective events (`RatificationEvent`, `DiscriminatorResult`, `AttestationEvent`, role authorization, revocation, supersession, calibration state) carry immutable identity, `effective_at`, `recorded_at`, state where applicable, and explicit supersession. Evaluation uses events present in the bound snapshot only when both `effective_at <= as_of_time` and `recorded_at <= as_of_time`. Ratification eligibility is replayed against the snapshot's ratification-state hash; Slice 4 resolves discriminator/authority heads into the canonical `diagnostic_state_hash` carried by its decision. Historical replay uses the original event set and both applicable state hashes; a later-recorded or backdated event creates a new run/lifecycle warning and never rewrites the original result.

The implementation may refactor code across completed slices only when all prior slice acceptance fixtures remain byte-identical or the governing specification explicitly requires a payload revision.

The local demonstration runner is introduced by Slice 1 and remains model-free. Each scenario prints the canonical structured output and decision trace, then exits nonzero on contract failure:

| Slice | Demonstration command |
|---:|---|
| 1 | `python scripts/run_slice.py safe-refusal --database-url "$GPTL_DATABASE_URL"` |
| 2 | `python scripts/run_slice.py candidate-preservation --database-url "$GPTL_DATABASE_URL"` |
| 3 | `python scripts/run_slice.py msa-gate --database-url "$GPTL_DATABASE_URL"` |
| 4 | `python scripts/run_slice.py artifact-confirmation --database-url "$GPTL_DATABASE_URL"` |
| 5 | `python scripts/run_slice.py honest-negative --database-url "$GPTL_DATABASE_URL"` |
| 6 | `python scripts/run_slice.py tier2-advisory --database-url "$GPTL_DATABASE_URL"` |
| 7 | `python scripts/run_slice.py replay-integrity --database-url "$GPTL_DATABASE_URL"` |

The acceptance-test command for slice `NN` is `python -m pytest tests/slices/test_slice_NN_*.py tests/conformance -q`. Shell wildcard expansion affects file selection only and cannot alter engine behavior.

---

## 5. Slice 1 — Safe Refusal

### Objective

Prove that GPTL can reject an unexecutable request deterministically without fabricating unavailable pack, policy, or snapshot references.

### Governing References

v0.4.14 §§2.1, 2.7, 2.10–2.13, 6.1, 9, 12, 14, 17.

### Scope

- Python package and local test harness.
- Constrained semantic scalar types.
- RFC 8785/NFC/UTC canonical serialization and SHA-256 envelope hashing.
- `DecisionHeader`, `PreflightRefusalContext`, `RefusalDecision`, and `Tier1Output`.
- Governed display-template registry sufficient for refusal directives: versioned template ID, allowed parameter keys, parameter types/order, and registry binding. No template meaning is hardcoded in engine code.
- Slice 1 portion of the §4 PostgreSQL persistence contract: atomic preflight decision envelope and audit persistence, database-trigger insert-only enforcement, schema version, checksums, and transaction rollback.
- Requested pack lookup by exact identifier only.

### Fixture

A fixed request names a pack identifier absent from an empty pack registry.

### Expected Result

`Tier1Output{decision.verdict="REFUSED", refusal_type="PACK_VERSION_UNAVAILABLE", context.context_kind="PREFLIGHT"}` with `operational_mode="RESEARCH_ONLY"`, no pack/snapshot/citation/version-set references, a governed `required_human_action` directive, a canonical decision hash, and one persisted audit event.

### Acceptance Gate

- Identical request produces identical decision bytes and hash.
- Unicode normalization variants canonicalize identically.
- Invalid timestamp, identifier, or hash is rejected by schema validation.
- No fake `pack_ref`, `engine_policy_ref`, or snapshot hash appears.
- `required_human_action` uses a registered template with validated parameters; an unknown template or parameter fails validation.
- Restarting the process does not erase the audit event.
- A simulated failure between envelope and audit writes leaves no readable partial run after PostgreSQL transaction rollback.
- Direct update/delete of committed rows is rejected by the database.

### Non-Goals

Published packs, snapshots, MSA, candidates, scoring, advisory output, rendering, and rich decision/advisory templates implemented by later slices.

### Stop Conditions

Canonical serialization cannot be made RFC 8785-conformant with the selected library; a refusal directive requires authoritative free text; PostgreSQL cannot enforce the context-specific atomic write contract.

---

## 6. Slice 2 — Candidate Preservation

### Objective

Load a bounded published candidate set while proving that missing context cannot silently remove a candidate and unratified authoritative input cannot enter Tier 1.

### Governing References

v0.4.14 §§2.4–2.7, 2.9, 2.11–2.13, 5.1, 6.1, 7.1–7.4, 7.7, 8.0–8.4, 9, 17.

### Scope

- Immutable governed records and explicit version references.
- Pack and engine-policy manifests with no runtime defaults.
- `RatificationEvent` representation and Tier 1 ratified-input gate. Instrument-emitted values carry their governed source linkage; human values reference an active event naming the value, source, actor, effective/recorded times, and governing pack version.
- Knowledge snapshot creation and the `SNAPSHOT_BOUND` atomic persistence contract from §4.
- Closed applicability AST and four-state evaluator.
- Snapshot-bound unit conversion.
- Scoped `SelectionBinding` resolution.
- Candidate assessments without signature/support scores.

### Fixtures

One reference method pack contains distinct failure modes producing `TRUE`, `FALSE`, and `UNKNOWN` applicability results. A separate invalid-pack fixture contains an incompatible unit or malformed AST. Two applicable candidates intentionally have no shared selection group. A grouped alternative pair exercises precedence and tie rejection. Paired intake fixtures differ only in ratification state. Another pair proves that a ratification revoked after the original run changes new runs but not replay of the original snapshot.

### Expected Results

- `TRUE` candidates remain in the bounded set.
- `FALSE` exclusions carry predicate evidence.
- `UNKNOWN` remains `APPLICABILITY_UNRESOLVED` and returns `REFUSED{MISSING_REQUIRED_EVIDENCE}` rather than a negative conclusion.
- `INVALID` returns `REFUSED{CONFIGURATION_INVALID}` and identifies every runtime-invalid candidate through a typed configuration issue containing its evaluation, error code, and evidence.
- Distinct ungrouped candidates both survive.
- Fully ratified input proceeds. Unratified/incomplete input deterministically returns Tier 2 `ADVISORY_NO_VERDICT`; it never enters Tier 1.
- Ratification active at the original `as_of_time` remains active for historical replay even when a later event revokes it.

### Acceptance Gate

- Kleene `all`, `any`, and `not` truth tables are exhaustive.
- Missing field never evaluates `FALSE`.
- Range bounds, membership uniqueness, empty expressions, and unit failures are tested.
- Selection precedence applies only inside one explicit group.
- Rank ties and overlapping ungrouped MSA records fail pack publication.
- Snapshot contains every exact record and policy version used.
- Every admitted human value traces to an active snapshot-bound ratification event and actor.
- Value hashes are verified before ratification eligibility or active-state hashing.
- A backdated event is ineligible until its immutable `recorded_at` is at or before the run's `as_of_time`.
- A later revocation cannot alter persisted/replayed output; it affects only new runs or lifecycle warnings.
- Snapshot, citations, output, and audit events commit atomically.

### Non-Goals

MSA execution, calibration gating, signature matching, discriminator aggregation, artifact verdicts, and full Tier 2 retrieval/advisory behavior. Slice 2 implements only the deterministic advisory envelope needed for the unratified-input route.

### Stop Conditions

A context field or unit lacks a governed registry definition; applicability requires an operator outside the closed AST; selection requires choosing between unrelated failure mechanisms; ratification state cannot be resolved from immutable typed events.

---

## 7. Slice 3 — MSA and Calibration Gate

### Objective

Prove that Tier 1 eligibility requires ratified intake, valid calibration, and a qualified applicable measurement-system study, with deterministic routing precedence.

### Governing References

v0.4.14 §§2.7, 2.11, 5.1, 7.2, 7.4, 7.6–7.7, 8.0–8.3, 9, 14, 17–18.

### Scope

- `MSAStudy` schema, qualification metadata, and qualification-scope binding.
- Governed `MethodMeasurementContract` binding method, MSA class, and deviation field.
- `QUANT_NONDESTRUCTIVE` MSA applicability and selection.
- Implemented-MSA-class registry bound to engine version.
- Governed calibration state and validity/freshness policy; no engine constants.
- Fixed gate precedence: ratification → calibration → MSA → scoring.
- Snapshot-bound precedence for competing MSA failure reasons; application branch order is not policy.
- Hard-gate routing before scoring.
- `WithinMeasurementVariationDecision`.
- `IndeterminateDecision` records the exact outside-variation comparison before Slice 4.

### Fixtures

- No MSA study.
- Applicable but unqualified study.
- Synthetic study qualified only for the governed `TEST_FIXTURE` scope whose uncertainty contains the deviation.
- Synthetic study qualified only for the governed `TEST_FIXTURE` scope whose uncertainty does not contain the deviation.
- Method with an unimplemented MSA class.
- Test-qualified study presented to a non-test evidence scope.
- Ratified intake crossed with `VALID`, `STALE`, `INVALID`, and `UNAVAILABLE` calibration.
- Unratified/incomplete intake crossed with the same four calibration states.

### Expected Results

Routing is fixed by this matrix; every route records a governed `route_reason_id`:

| Intake | Calibration | Result |
|---|---|---|
| unratified/incomplete | any state | Tier 2 `ADVISORY_NO_VERDICT` through the Slice 2 intake gate |
| ratified | `VALID` | proceed to MSA |
| ratified | `STALE` or `INVALID` | `REFUSED{STALE_OR_INVALID_CALIBRATION}` |
| ratified | `UNAVAILABLE` | `REFUSED{MISSING_REQUIRED_EVIDENCE}` with calibration-unavailable reason |

After valid calibration, missing, unqualified, unknown-applicability, out-of-range, scope-mismatched, or unimplemented-class MSA cannot proceed to scoring. A within-variation case returns `WITHIN_MEASUREMENT_VARIATION`. The outside-variation fixture deliberately omits Slice 4 signature observations and returns `INDETERMINATE` with `OPEN_UNASSESSED` candidates.

### Acceptance Gate

- No artifact or negative verdict is reachable without ratified intake, valid calibration, and qualified applicable MSA.
- A qualification-scope mismatch behaves as no applicable qualified MSA; `TEST_FIXTURE` qualification never satisfies another scope.
- Every intake/calibration matrix cell has exactly one result; no "refusal or Tier 2" alternative remains.
- Stale/invalid calibration returns `STALE_OR_INVALID_CALIBRATION`; unavailable calibration never silently passes.
- Overlapping studies resolve only through a valid selection group.
- MSA version and capability evidence are in the snapshot.
- Calibration/MSA routes retain typed evaluations, governed route reasons, and exact compared values.
- Boundary comparisons use exact `Decimal` behavior.

### Non-Goals

Other MSA classes, support aggregation, confirmation, known-artifacts-excluded, and partial continuation across independently calibrated multi-source evidence.

### Stop Conditions

The fixture lacks defensible reference capability evidence; method class is ambiguous; an MSA/calibration rule is absent from governed policy; routing requires an outcome not represented in the fixed matrix.

---

## 8. Slice 4 — Artifact Confirmation

### Objective

Run complete structured and human-attested positive diagnostic paths from synthetic typed EDS cases to cited `METHOD_ARTIFACT` research verdicts.

### Governing References

v0.4.14 §§2, 7.3, 7.5–7.7, 8.3–8.9, 9–10, 16–18.

### Scope

- Signature features and coverage.
- `CandidateDiagnosticContract` as the exact, mandatory Slice 4 extension of each immutable published failure-mode identity.
- Provenance-complete `GovernedNumericPolicy` records for every weight, power, threshold, coverage gate, and dominance margin; the resolved set is exact and pack-scoped.
- Evidence states, including `OPEN_UNASSESSED`.
- Discriminator result evaluation and explicit supersession.
- Order-independent artifact/real masses.
- Versioned Build 0 `COMBINE` implementation.
- Typed Slice 3 outside-variation continuation; Slice 4 never reconstructs a prior gate result.
- Structured confirm test.
- `HumanAttestedConfirmTest`, `AttestationEvent`, snapshot-bound role-policy evaluation, revocation/supersession, and separation of duties.
- Candidate status and dominance gates.
- `MethodArtifactDecision` and complete citations.

### Fixture

A fixture explicitly labeled `SYNTHETIC` represents an EDS peak-overlap investigation using typed observables. Its diagnostic records and synthetic MSA study share one isolated governed `TEST_FIXTURE` evidence scope. Every domain value, weight, threshold, discriminator, required evidence item, role policy, and attestation is in the reference pack with provenance and `RESEARCH_ONLY` status. Companion cases cover allowed role, disallowed role, attester equal to pack author/approver, revoked/superseded attestation, and revocation recorded after the original run.

### Expected Result

`METHOD_ARTIFACT` for the peak-overlap candidate only when its structured or attested confirmation contract is satisfied. Attested confirmation requires active as-of-time authorization and separation of duties. Post-run revocation changes new runs but not historical replay.

The canonical decision retains the selected MSA study and exact deviation/uncertainty comparison, exactly one named winner with a matching `CONFIRMED` assessment, every other candidate assessment without status rewriting, the exact bounded published-catalog evaluation fraction, confirmation citations, governed route reason, required human action, and governed `what_would_change_this` directive. Slice 4 persistence uses `gptl.slice4.v1` without rewriting earlier schema records.

### Acceptance Gate

- Missing all signature observations produces `OPEN_UNASSESSED`, never support zero.
- Missing required signature evidence prevents aggregation.
- Every permutation of representative discriminator ordering yields identical support and verdict; property tests establish commutativity over generated result sets.
- Exact `Decimal` tests pin confirmation and dominance at the boundary and at the nearest representable values on both sides.
- Two candidates may be `CONFIRMED`; exactly one verdict-dominant candidate still yields `METHOD_ARTIFACT`, and both assessments remain in the result.
- Contradictory unsuperseded results produce an integrity error.
- Missing, forked, identity-changing, or unavailable supersession links produce an integrity error; one explicit active successor is selected deterministically.
- Multiple active authorizations or satisfying attestations for one confirmation contract produce an integrity error.
- A failed structured confirm test makes `CONFIRMED` unreachable.
- Disallowed role, separation-of-duties violation, or inactive attestation makes `CONFIRMED` unreachable.
- Role policy and attestation state are resolved at `as_of_time`, persisted in the active-state hash, and replay without consulting current state.
- Every score and boundary value cites the governed numeric policy and provenance bound into the snapshot; source scans permit no domain numeric constant in generic Slice 4 modules.
- Failure to construct a valid authoritative output returns governed `ENGINE_FAILURE`, never an uncaught schema exception or configuration refusal.
- Renderer-disabled execution produces the same canonical result.

### Non-Goals

Vendor-native ingestion, production EDS fidelity, qualified thresholds, negative catalog verdict, production RBAC, and live identity-provider authorization.

### Stop Conditions

A fixture value lacks explicit reference provenance; code requires a hidden default; scoring consumes missing data as evidence; the expected verdict depends on tuning not declared `RESEARCH_ONLY`; role/attestation linkage cannot be represented as immutable governed records.

---

## 9. Slice 5 — Honest Negative

### Objective

Prove that the engine issues `KNOWN_ARTIFACTS_EXCLUDED` only after every applicable published candidate has explicit elimination or sufficient governed rule-out evidence.

### Governing References

v0.4.14 §§2.7–2.11, 7.5, 8.3–8.9, 9, 14, 16–18.

### Scope

- Hard-impossibility elimination records.
- `RuleOutEvidenceRequirement` with `ALL_CONSISTENT_WITH_REAL`.
- Rule-out status gates.
- Bounded-catalog evaluated fraction.
- Evaluated-artifact record, named known gaps, and catalog-boundary directive.
- Governed rich decision templates for catalog boundary, known gaps, `what_would_change_this`, and human action; extends the Slice 1 registry without hardcoded template semantics.
- `KnownArtifactsExcludedDecision`.

### Fixtures

- Every candidate explicitly eliminated or ruled out.
- One candidate `OPEN_UNASSESSED`.
- One candidate `APPLICABILITY_UNRESOLVED`.
- Low support without required rule-out evidence.
- Catalog with a named unevaluated category.

### Expected Results

Only the fully terminal fixture meeting the governed published-catalog fraction returns `KNOWN_ARTIFACTS_EXCLUDED`. The output reports the exact known denominator fraction, preserves named unevaluated categories outside the published set, and asserts no real material behavior. Every incomplete fixture returns `INDETERMINATE` or a refusal and names what would enable continuation. Slice 5 persistence uses `gptl.slice5.v1` without rewriting earlier records.

### Acceptance Gate

- Low support alone never produces `RULED_OUT`.
- Exact `Decimal` tests pin `tau_ruleout` at the boundary and nearest representable values on both sides.
- `UNKNOWN`, `OPEN_UNASSESSED`, or `INCONCLUSIVE` blocks the negative verdict.
- A valid dominant positive candidate retains `METHOD_ARTIFACT` precedence over negative routing.
- Every elimination/rule-out has governed citations.
- Output states only what was excluded within the published catalog and never asserts real material behavior.
- No fraction uses an unknown denominator; an empty governed high-power set returns `CONFIGURATION_INVALID`.
- Every boundary/gap/action directive references a snapshot-bound registered template with validated parameters.

### Non-Goals

Proof that no unknown artifact exists, material-truth verdict, causal root-cause determination.

### Stop Conditions

The catalog boundary cannot be represented without free authoritative prose; a rule-out requirement lacks evidence; catalog denominator cannot be enumerated exactly.

---

## 10. Slice 6 — Tier 2 Advisory

### Objective

Provide useful deterministic continuation guidance without issuing a verdict or support score when Tier 1 eligibility is absent.

### Governing References

v0.4.14 §§2.3–2.7, 4, 5.1–5.2, 9, 12, 14, 17–18.

### Scope

- `AdvisoryDecision` and `Tier2Output`.
- Exact alias, controlled-term, and relational retrieval in declared order.
- Custom deterministic lexical scorer over normalized tokens with published weights and stable governed-ID tie-break. The normalization algorithm and frozen Unicode data version, scorer version, weights, and vocabulary are snapshot-bound.
- PostgreSQL `tsvector`/trigram MAY accelerate candidate lookup only when an equivalence check proves it returns the same bounded rows; database-native rank never affects canonical membership or ordering.
- Proposed field IDs, eligibility gaps, required records/measurements, open discriminators, and display directives.
- Governed advisory templates for next steps and ratification/calibration/MSA eligibility gaps.
- Optional renderer boundary test with all model adapters disabled.

### Fixtures

Incomplete/unratified intake, ambiguous method alias, unknown method, missing MSA, unimplemented MSA class, stale/unavailable calibration, applicability `UNKNOWN`, and a resolved method whose Tier 1 attempt returns a positive verdict.

### Expected Result

Typed `ADVISORY_NO_VERDICT` output with no support score, no hidden candidate narrowing, and exact steps required for Tier 1 eligibility as derived from the actual Tier 1 attempt. Unknown and ambiguous methods select no method; all bounded matches remain represented. Slice 6 persists as `gptl.slice6.v1` without rewriting earlier records.

### Acceptance Gate

- No advisory path emits a Tier 1 verdict; a resolved Tier 1 non-refusal fails before advisory route selection.
- Lexical membership/order and tie-break replay identically across processes and supported platforms from the bound scorer policy; a Unicode table mismatch fails closed.
- Exact ID/alias, controlled-term, relational, and lexical lanes execute only in declared order; a tied top score remains ambiguous.
- Enabling/disabling the optional PostgreSQL text-search accelerator cannot change canonical rows or ordering.
- Removing every model adapter changes no advisory structured data.
- Optional prose is separate from and cannot modify the advisory hash.
- Advisory schemas contain no verdict, refusal, support score, confidence, or probability field.
- Advisory directives reference snapshot-bound registered templates.

### Non-Goals

LLM translation, automated ratification, operator-facing ratification/attestation tooling, vendor parsers, qualified daily-use claims.

### Stop Conditions

Lexical ranking requires an unpublished weight; deterministic normalization/scoring cannot be reproduced; a model is required to produce a structured field; advisory output invents a method or failure mode.

---

## 11. Slice 7 — Replay and Integrity

### Objective

Close Build 0 by proving historical decisions are reconstructable, immutable, and detect tampering across process restarts and pack evolution over the persistence substrate established in Slices 1–2.

### Governing References

v0.4.14 §§2.1, 2.4–2.5, 2.12–2.13, 3, 6.1, 7.7, 8.1, 8.7, 8.9, 9, 11–12, 16–18.

### Scope

- Replay/integrity regression over the already durable append-only decision, snapshot, citation, and audit substrate; Slice 7 does not introduce first-time persistence.
- Atomic append-only replay capsules containing the exact typed request, runtime, policy, and query under a bound governed replay-policy reference, versioned algorithm, and recipe schema.
- Historical replay by exact bound versions.
- Replay ratification, attestation, role authorization, calibration, revocation, and supersession from the original snapshot and active-state hash, never current state.
- Pack upgrade, deprecation, revocation, and rollback fixtures.
- Corrected input as a new version/new run.
- Tamper and missing-content detection.
- Local Build 0 demonstration script covering all prior slices.

### Fixtures

Persisted outputs and exact replay capsules from Slices 1–6, a new pack version, explicitly superseded discriminator/ratification/attestation events, a corrected governed observation, modified stored content, a missing capsule, and missing referenced content.

### Expected Results

Historical runs reconstruct and replay byte-identically from their stored exact recipes and original snapshots. New versions create new runs without changing old output. Modified, unavailable, non-canonical, or algorithm-incompatible replay material returns `INTEGRITY_FAILURE`. Deprecation/revocation affects new eligibility according to exact-version as-of policy but does not rewrite history.

### Acceptance Gate

- Restart and cross-process replay is byte-identical.
- A replay-qualified run and its capsule commit atomically; capsule update, delete, and truncate are database-rejected.
- Every canonical decision field traces to the snapshot or fixed algorithm version.
- No replay performs network retrieval or resolves "latest."
- Post-run revocation/supersession cannot change historical replay; backdated events create new runs/lifecycle warnings rather than rewriting history.
- Tampering and missing bound content fail closed.
- Slices 1–6 all reconstruct from persisted typed recipes; replay compares output, snapshot, audit, citation, and bound-version bytes.
- All prior slice fixtures still pass unchanged.

### Non-Goals

Platform-wide correction propagation, production RBAC, durable distributed workers, backup/recovery qualification, QMS integration.

### Stop Conditions

A historical decision cannot be reconstructed from stored versions; an algorithm version is unavailable; replay requires mutable external state.

---

## 12. Requirement Ownership Matrix

Each requirement has one primary implementation slice. Later slices may add regression coverage but do not redefine ownership.

| Requirement | Primary Slice | Governing Spec |
|---|---:|---|
| Semantic scalar validation | 1 | §7.1 |
| Canonical serialization and envelope hashing | 1 | §§2.12–2.13, 9 |
| Preflight refusal without fabricated references | 1 | §§9, 14 |
| Governed refusal display-template registry | 1 | §9 |
| Atomic append-only preflight decision/audit store | 1 | §§9, 12 |
| Governed identity/version records | 2 | §6.1 |
| Atomic snapshot/citation/version-set binding | 2 | §7.7, §8.1 |
| Four-state applicability | 2 | §7.2 |
| Scoped selection groups | 2 | §7.2 |
| Published candidate-set construction | 2 | §8.3 |
| Ratification events and Tier 1 ratified-input gate | 2 | §§2.4, 5.1, 8.0 |
| As-of ratification resolution | 2 | §§2.4, 7.7 |
| `QUANT_NONDESTRUCTIVE` MSA hard gate | 3 | §7.6, §8.2 |
| MSA qualification/evidence-scope isolation | 3 | §§7.6, 9, 17 |
| Calibration validation and exact routing matrix | 3 | §§5.1, 7.4, 8.0, 14 |
| Measurement-variation verdict | 3 | §§8.2, 9 |
| Signature and evidence-state calculation | 4 | §§8.5–8.6 |
| Order-independent aggregation | 4 | §8.7 |
| Structured confirm test and artifact verdict | 4 | §§7.5, 8.8, 9 |
| Attested confirmation, role policy, and separation of duties | 4 | §§7.5, 8.8, 17 |
| As-of attestation and role-authorization resolution | 4 | §§2.5, 7.5, 7.7 |
| Explicit elimination and rule-out evidence | 5 | §§7.5, 8.4, 8.8 |
| Honest bounded-catalog negative verdict | 5 | §§2.9, 8.8, 9 |
| Governed decision/gap display templates | 5 | §9 |
| Typed Tier 2 advisory | 6 | §§5.1–5.2, 9 |
| Deterministic lexical scorer and advisory templates | 6 | §§5.2, 9, 12 |
| Immutable replay/tamper regression | 7 | §§6.1, 7.7, 8.9, 12 |
| Pack evolution and correction-as-new-run | 7 | §§3, 6.1, 8.7, 11 |

Cross-cutting invariants in §2 and release blockers in §17 apply to every slice even though their first executable coverage is owned by the earliest relevant slice.

---

## 13. Build 0 Completion Gate

Build 0 is complete only when:

1. Every slice acceptance gate passes locally.
2. Every requirement in §12 has an implementation and test owner.
3. All committed expected canonical outputs reproduce byte-identically.
4. All model adapters can be absent without affecting structured output.
5. Static dependency/source scans find no vector implementation or domain constants in generic modules.
6. Every Tier 1 output is `RESEARCH_ONLY`, non-dispositional, and non-record-of-record.
7. Synthetic/reference fixtures are labeled honestly.
8. Test-fixture MSA/data cannot satisfy a differently scoped run.
9. Both structured and attested confirmation paths, ratification gating, calibration routing, and display-template validation pass their acceptance fixtures.
10. The persistence contract passes atomicity, append-only, crash-recovery, checksum, schema-version, and context-specific record-set tests.
11. Historical replay resolves decision-effective events from the original snapshot and active-state hash, never live state.
12. The final local demonstration exercises safe refusal, candidate preservation, MSA/calibration gating, positive artifact, honest negative, advisory, and replay paths.

Passing Build 0 does not qualify a method or authorize production reliance. It proves that the deterministic engine scaffold honors the governing contracts.

---

## 14. Change Control

Implementation discoveries are classified before action:

- **Implementation detail:** does not alter a schema, invariant, decision boundary, or observable output; resolve in code and tests.
- **Build-plan correction:** changes sequencing or ownership without changing v0.4.14 semantics; revise this plan.
- **Specification amendment:** changes a schema contract, decision state, policy source, evidence requirement, or invariant; stop the affected slice and revise the governing specification before implementation.
- **Bench-open result:** supplies qualification evidence for an explicitly bench-open item; record the evidence and qualification event without rewriting historical Build 0 outputs.

Code is executable evidence that the contract can be implemented. It is not permission to silently replace the governing specification.
