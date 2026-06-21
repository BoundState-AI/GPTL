# GPTL MIE Build 0 Plan
## Vertical-Slice Implementation Contract — v0.1

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.4

**Status:** Proposed implementation sequence for adversarial review

**Operational boundary:** Every Build 0 output is `RESEARCH_ONLY`, non-dispositional, and not a QMS or engineering record of record.

---

## 1. Purpose

This plan translates the MIE Build 0 contract into independently verifiable vertical slices. It does not amend v0.4.4, create domain policy, qualify a method, or define vendor instrument formats. When this plan and v0.4.4 conflict, v0.4.4 governs and implementation stops until the conflict is resolved explicitly.

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
    snapshot.py             immutable snapshot binding
    audit.py                append-only events and decision envelopes
  mie/
    schema.py               MIE records and output unions
    predicates.py           four-state applicability AST evaluator
    selection.py            selection-group resolution and candidate loading
    msa.py                  MSA applicability and hard gate
    signatures.py           signature match and evidence-state calculation
    aggregation.py          order-independent evidence aggregation
    verdicts.py             candidate status and verdict gates
    service.py              deterministic MIE pipeline orchestration
packs/reference/mie/        governed synthetic/reference pack data
tests/
  conformance/              cross-cutting invariant tests
  slices/                   slice acceptance tests
  fixtures/                 typed inputs and expected canonical outputs
scripts/                    local demonstration entry points only
```

Domain facts, thresholds, method records, failure modes, discriminators, and MSA evidence belong in packs/fixtures, never generic engine modules.

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

The implementation may refactor code across completed slices only when all prior slice acceptance fixtures remain byte-identical or the governing specification explicitly requires a payload revision.

The local demonstration runner is introduced by Slice 1 and remains model-free. Each scenario prints the canonical structured output and decision trace, then exits nonzero on contract failure:

| Slice | Demonstration command |
|---:|---|
| 1 | `python scripts/run_slice.py safe-refusal` |
| 2 | `python scripts/run_slice.py candidate-preservation` |
| 3 | `python scripts/run_slice.py msa-gate` |
| 4 | `python scripts/run_slice.py artifact-confirmation` |
| 5 | `python scripts/run_slice.py honest-negative` |
| 6 | `python scripts/run_slice.py tier2-advisory` |
| 7 | `python scripts/run_slice.py replay-integrity` |

The acceptance-test command for slice `NN` is `python -m pytest tests/slices/test_slice_NN_*.py tests/conformance -q`. Shell wildcard expansion affects file selection only and cannot alter engine behavior.

---

## 5. Slice 1 — Safe Refusal

### Objective

Prove that GPTL can reject an unexecutable request deterministically without fabricating unavailable pack, policy, or snapshot references.

### Governing References

v0.4.4 §§2.1, 2.7, 2.10–2.13, 6.1, 9, 12, 14, 17.

### Scope

- Python package and local test harness.
- Constrained semantic scalar types.
- RFC 8785/NFC/UTC canonical serialization and SHA-256 envelope hashing.
- `DecisionHeader`, `PreflightRefusalContext`, `RefusalDecision`, and `Tier1Output`.
- Minimal append-only SQLite audit event for the refusal.
- Requested pack lookup by exact identifier only.

### Fixture

A fixed request names a pack identifier absent from an empty pack registry.

### Expected Result

`Tier1Output{decision.verdict="REFUSED", refusal_type="PACK_VERSION_UNAVAILABLE", context.context_kind="PREFLIGHT"}` with `operational_mode="RESEARCH_ONLY"`, no pack/snapshot references, a canonical decision hash, and one persisted audit event.

### Acceptance Gate

- Identical request produces identical decision bytes and hash.
- Unicode normalization variants canonicalize identically.
- Invalid timestamp, identifier, or hash is rejected by schema validation.
- No fake `pack_ref`, `engine_policy_ref`, or snapshot hash appears.
- Restarting the process does not erase the audit event.

### Non-Goals

Published packs, snapshots, MSA, candidates, scoring, advisory output, rendering.

### Stop Conditions

Canonical serialization cannot be made RFC 8785-conformant with the selected library; an output field requires unspecified free text; audit persistence cannot be atomic with the refusal envelope.

---

## 6. Slice 2 — Candidate Preservation

### Objective

Load a bounded published candidate set while proving that missing context cannot silently remove a candidate.

### Governing References

v0.4.4 §§2.4–2.7, 2.9, 2.11–2.13, 6.1, 7.1–7.4, 7.7, 8.0–8.4, 9, 17.

### Scope

- Immutable governed records and explicit version references.
- Pack and engine-policy manifests with no runtime defaults.
- Knowledge snapshot creation and transactional binding.
- Closed applicability AST and four-state evaluator.
- Snapshot-bound unit conversion.
- Scoped `SelectionBinding` resolution.
- Candidate assessments without signature/support scores.

### Fixtures

One reference method pack contains distinct failure modes producing `TRUE`, `FALSE`, and `UNKNOWN` applicability results. A separate invalid-pack fixture contains an incompatible unit or malformed AST. Two applicable candidates intentionally have no shared selection group. A grouped alternative pair exercises precedence and tie rejection.

### Expected Results

- `TRUE` candidates remain in the bounded set.
- `FALSE` exclusions carry predicate evidence.
- `UNKNOWN` remains `APPLICABILITY_UNRESOLVED` and returns `REFUSED{MISSING_REQUIRED_EVIDENCE}` rather than a negative conclusion.
- `INVALID` returns `REFUSED{CONFIGURATION_INVALID}`.
- Distinct ungrouped candidates both survive.

### Acceptance Gate

- Kleene `all`, `any`, and `not` truth tables are exhaustive.
- Missing field never evaluates `FALSE`.
- Range bounds, membership uniqueness, empty expressions, and unit failures are tested.
- Selection precedence applies only inside one explicit group.
- Rank ties and overlapping ungrouped MSA records fail pack publication.
- Snapshot contains every exact record and policy version used.

### Non-Goals

MSA execution, signature matching, discriminator aggregation, artifact verdicts, Tier 2 advisory.

### Stop Conditions

A context field or unit lacks a governed registry definition; applicability requires an operator outside the closed AST; selection requires choosing between unrelated failure mechanisms.

---

## 7. Slice 3 — MSA Gate

### Objective

Prove that Tier 1 eligibility is earned through a qualified, applicable measurement-system study and cannot be bypassed.

### Governing References

v0.4.4 §§2.7, 2.11, 5.1, 7.2, 7.6–7.7, 8.0–8.3, 9, 14, 17–18.

### Scope

- `MSAStudy` schema, qualification metadata, and qualification-scope binding.
- `QUANT_NONDESTRUCTIVE` MSA applicability and selection.
- Implemented-MSA-class registry bound to engine version.
- Hard-gate routing before scoring.
- `WithinMeasurementVariationDecision`.

### Fixtures

- No MSA study.
- Applicable but unqualified study.
- Synthetic study qualified only for the governed `TEST_FIXTURE` scope whose uncertainty contains the deviation.
- Synthetic study qualified only for the governed `TEST_FIXTURE` scope whose uncertainty does not contain the deviation.
- Method with an unimplemented MSA class.
- Test-qualified study presented to a non-test evidence scope.

### Expected Results

Missing, unqualified, unknown-applicability, stale, out-of-range, or unimplemented-class MSA cannot proceed to scoring. A within-variation case returns `WITHIN_MEASUREMENT_VARIATION`. The outside-variation fixture deliberately omits the signature observations introduced in Slice 4, so it proceeds through the already implemented candidate-preservation path and returns `INDETERMINATE` with `OPEN_UNASSESSED` candidates. No output is justified merely by an unimplemented code path.

### Acceptance Gate

- No artifact or negative verdict is reachable without a qualified applicable MSA.
- A qualification-scope mismatch behaves as no applicable qualified MSA; `TEST_FIXTURE` qualification never satisfies another scope.
- Overlapping studies resolve only through a valid selection group.
- MSA version and capability evidence are in the snapshot.
- Boundary comparisons use exact `Decimal` behavior.

### Non-Goals

Other MSA classes, support aggregation, confirmation, known-artifacts-excluded.

### Stop Conditions

The fixture lacks defensible reference capability evidence; method class is ambiguous; a numeric MSA rule is not present in governed policy.

---

## 8. Slice 4 — Artifact Confirmation

### Objective

Run the first complete positive diagnostic path from a synthetic typed EDS case to a cited `METHOD_ARTIFACT` research verdict.

### Governing References

v0.4.4 §§2, 7.3, 7.5–7.7, 8.3–8.9, 9–10, 16–18.

### Scope

- Signature features and coverage.
- Evidence states, including `OPEN_UNASSESSED`.
- Discriminator result evaluation and explicit supersession.
- Order-independent artifact/real masses.
- Versioned Build 0 `COMBINE` implementation.
- Structured confirm test.
- Candidate status and dominance gates.
- `MethodArtifactDecision` and complete citations.

### Fixture

A fixture explicitly labeled `SYNTHETIC` represents an EDS peak-overlap investigation using typed observables. Its diagnostic records and synthetic MSA study share one isolated governed `TEST_FIXTURE` evidence scope. It claims no vendor file format, lab configuration, or production qualification. Every domain value, weight, threshold, discriminator, and required evidence item is contained in the reference pack with provenance and `RESEARCH_ONLY` status.

### Expected Result

`METHOD_ARTIFACT` for the peak-overlap candidate, for the recorded signature/discriminator/confirm-test reasons, with every alternative candidate visible and the output labeled `RESEARCH_ONLY`.

### Acceptance Gate

- Missing all signature observations produces `OPEN_UNASSESSED`, never support zero.
- Missing required signature evidence prevents aggregation.
- Every permutation of representative discriminator ordering yields identical support and verdict; property tests establish commutativity over generated result sets.
- Contradictory unsuperseded results produce an integrity error.
- A failed confirm test makes `CONFIRMED` unreachable.
- Renderer-disabled execution produces the same canonical result.

### Non-Goals

Vendor-native ingestion, production EDS fidelity, qualified thresholds, negative catalog verdict, human attestation.

### Stop Conditions

A fixture value lacks explicit reference provenance; code requires a hidden default; the scoring function consumes missing data as evidence; the expected verdict depends on tuning not declared `RESEARCH_ONLY`.

---

## 9. Slice 5 — Honest Negative

### Objective

Prove that the engine issues `KNOWN_ARTIFACTS_EXCLUDED` only after every applicable published candidate has explicit elimination or sufficient governed rule-out evidence.

### Governing References

v0.4.4 §§2.7–2.11, 7.5, 8.3–8.9, 9, 14, 16–18.

### Scope

- Hard-impossibility elimination records.
- `RuleOutEvidenceRequirement` with `ALL_CONSISTENT_WITH_REAL`.
- Rule-out status gates.
- Bounded-catalog evaluated fraction.
- Evaluated-artifact record, named known gaps, and catalog-boundary directive.
- `KnownArtifactsExcludedDecision`.

### Fixtures

- Every candidate explicitly eliminated or ruled out.
- One candidate `OPEN_UNASSESSED`.
- One candidate `APPLICABILITY_UNRESOLVED`.
- Low support without required rule-out evidence.
- Catalog with a named unevaluated category.

### Expected Results

Only the fully evaluated fixture returns `KNOWN_ARTIFACTS_EXCLUDED`. Every incomplete fixture returns `INDETERMINATE` or a refusal and names what would enable continuation.

### Acceptance Gate

- Low support alone never produces `RULED_OUT`.
- `UNKNOWN`, `OPEN_UNASSESSED`, or `INCONCLUSIVE` blocks the negative verdict.
- Every elimination/rule-out has governed citations.
- Output states only what was excluded within the published catalog and never asserts real material behavior.
- No fraction uses an unknown denominator.

### Non-Goals

Proof that no unknown artifact exists, material-truth verdict, causal root-cause determination.

### Stop Conditions

The catalog boundary cannot be represented without free authoritative prose; a rule-out requirement lacks evidence; catalog denominator cannot be enumerated exactly.

---

## 10. Slice 6 — Tier 2 Advisory

### Objective

Provide useful deterministic continuation guidance without issuing a verdict or support score when Tier 1 eligibility is absent.

### Governing References

v0.4.4 §§2.3–2.7, 4, 5.1–5.2, 9, 12, 14, 17–18.

### Scope

- `AdvisoryDecision` and `Tier2Output`.
- Exact alias, controlled-term, relational, and FTS5 retrieval in declared order.
- Published lexical policy and stable tie-break.
- Proposed field IDs, eligibility gaps, required records/measurements, open discriminators, and display directives.
- Optional renderer boundary test with all model adapters disabled.

### Fixtures

Incomplete ratified intake, ambiguous method alias, unknown method, missing MSA, unimplemented MSA class, and applicability `UNKNOWN`.

### Expected Result

Typed `ADVISORY_NO_VERDICT` output with no support score, no hidden candidate narrowing, and exact steps required for Tier 1 eligibility. Unknown method with no lexical/relational match remains explicit.

### Acceptance Gate

- No advisory path emits a Tier 1 verdict.
- FTS/lexical order and tie-break are reproducible.
- Removing every model adapter changes no advisory structured data.
- Optional prose is separate from and cannot modify the advisory hash.

### Non-Goals

LLM translation, automated ratification, vendor parsers, qualified daily-use claims.

### Stop Conditions

Lexical ranking requires an unpublished weight; a model is required to produce a structured field; advisory output invents a method or failure mode.

---

## 11. Slice 7 — Replay and Integrity

### Objective

Close Build 0 by proving historical decisions are reconstructable, immutable, and detect tampering across process restarts and pack evolution.

### Governing References

v0.4.4 §§2.1, 2.4–2.5, 2.12–2.13, 3, 6.1, 7.7, 8.1, 8.7, 8.9, 9, 11–12, 16–18.

### Scope

- Full append-only decision, snapshot, citation, and audit persistence.
- Historical replay by exact bound versions.
- Pack upgrade, deprecation, revocation, and rollback fixtures.
- Corrected input as a new version/new run.
- Tamper and missing-content detection.
- Local Build 0 demonstration script covering all prior slices.

### Fixtures

Persisted outputs from Slices 1–6, a new pack version, an explicitly superseded discriminator result, a corrected governed observation, modified stored content, and missing referenced content.

### Expected Results

Historical runs replay byte-identically from their original snapshots. New versions create new runs without changing old output. Modified or unavailable bound content returns `INTEGRITY_FAILURE`. Deprecation/revocation affects new eligibility according to policy but does not rewrite history.

### Acceptance Gate

- Restart and cross-process replay is byte-identical.
- Every canonical decision field traces to the snapshot or fixed algorithm version.
- No replay performs network retrieval or resolves "latest."
- Tampering and missing bound content fail closed.
- All prior slice fixtures still pass unchanged.

### Non-Goals

Platform-wide correction propagation, production RBAC, durable distributed workers, Postgres, backup/recovery qualification, QMS integration.

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
| Minimal append-only refusal audit | 1 | §§9, 12 |
| Governed identity/version records | 2 | §6.1 |
| Snapshot binding | 2 | §7.7, §8.1 |
| Four-state applicability | 2 | §7.2 |
| Scoped selection groups | 2 | §7.2 |
| Published candidate-set construction | 2 | §8.3 |
| `QUANT_NONDESTRUCTIVE` MSA hard gate | 3 | §7.6, §8.2 |
| MSA qualification/evidence-scope isolation | 3 | §§7.6, 9, 17 |
| Measurement-variation verdict | 3 | §§8.2, 9 |
| Signature and evidence-state calculation | 4 | §§8.5–8.6 |
| Order-independent aggregation | 4 | §8.7 |
| Confirm-test and artifact verdict | 4 | §§7.5, 8.8, 9 |
| Explicit elimination and rule-out evidence | 5 | §§7.5, 8.4, 8.8 |
| Honest bounded-catalog negative verdict | 5 | §§2.9, 8.8, 9 |
| Typed Tier 2 advisory and lexical retrieval | 6 | §§5.1–5.2, 9, 12 |
| Complete immutable audit and replay | 7 | §§6.1, 7.7, 8.9, 12 |
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
9. The final local demonstration exercises safe refusal, candidate preservation, MSA gating, positive artifact, honest negative, advisory, and replay paths.

Passing Build 0 does not qualify a method or authorize production reliance. It proves that the deterministic engine scaffold honors the governing contracts.

---

## 14. Change Control

Implementation discoveries are classified before action:

- **Implementation detail:** does not alter a schema, invariant, decision boundary, or observable output; resolve in code and tests.
- **Build-plan correction:** changes sequencing or ownership without changing v0.4.4 semantics; revise this plan.
- **Specification amendment:** changes a schema contract, decision state, policy source, evidence requirement, or invariant; stop the affected slice and revise the governing specification before implementation.
- **Bench-open result:** supplies qualification evidence for an explicitly bench-open item; record the evidence and qualification event without rewriting historical Build 0 outputs.

Code is executable evidence that the contract can be implemented. It is not permission to silently replace the governing specification.
