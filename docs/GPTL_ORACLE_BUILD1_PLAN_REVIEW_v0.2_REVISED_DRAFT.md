# GPTL MIE Build 1 Plan
## Capability-Profiled Capture & Advisory Contract — v0.4 (Beth revision round 2 of v0.3)

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20 (frozen; unchanged by this revision)

**Status:** Draft after ORACLE session `20260623-040533` and Beth normalization round 2; not an implementation freeze packet. Three items remain owner-authority decisions (see §16 Open Owner Decisions).

**Build 0 dependency:** Build 0 is frozen by `GPTL_ORACLE_BUILD0_CLOSEOUT_REVIEW_v1.6.md`. Build 1 extends the frozen deterministic spine; it does not reopen Build 0 architecture, verdict semantics, replay, storage, canonicalization, or MSA/calibration gates.

**Operational boundary:** Build 1 remains `RESEARCH_ONLY`, non-dispositional, and not a QMS, quality, flight, or engineering record of record. It may create governed source, proposal, ratification, observation, capability-profile, authority-policy, and validation-protocol records. It does not qualify methods, instruments, MSA studies, vendor parsers, thresholds, process controls, or production actions.

**v0.4 closeout over v0.3:** retains all v0.3 contracts and owner-direction decisions and closes the round-2 review defects: (a) a closed `EvidenceScope` contract and deterministic scope-match semantics used by every scope gate (§4.2); (b) published `ContextKey`/`ContextKeyRegistry` schemas plus a cross-schema-version continuity rule (§6.1); (c) a closed `ProposalEvidence` set so protocol- and observation-derived proposals are representable and hashable (§6); (d) the model-output prohibition scoped to authoritative payloads so model-assisted proposals are unambiguous (§2); (e) pinned evaluator/unit-registry/canonicalization refs in validation results for reproducible replay (§9); (f) a multi-finding `CaptureGateResult` with published precedence (§10.1); (g) a global `max_bytes_per_transaction` hard ceiling on raw-byte storage (§2, §5); (h) closed capability-resolver match semantics (null/wildcard, overlap lint, frozen algorithm id) (§4.1); and (i) a minimum ratification trust anchor (§7).

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
- No model output in any authoritative or decision-effective payload: candidate generation, applicability, scoring, confirmation, verdicts, Tier 1 inputs, `CaptureGateResult`, Build 0 requests/snapshots/verdicts, or any canonical decision data. Model-assisted content MAY appear only inside a non-authoritative `TypedValueProposal` as captured proposal content carrying explicit `proposal_method` provenance; such content is never authoritative and never enters Tier 1 without a `ProposalRatificationEvent`.
- No `float` in decision arithmetic or canonical decision data.
- No SQLite runtime or test fallback.
- No application default for domain policy, thresholds, units, evidence requirements, capability declarations, source precedence, parser behavior, capability matching, or applicability.
- No authoritative free text. Human prose exists only in separate rendered artifacts or as unvalidated attributed observation text.
- No implicit latest-version lookup. Every governed input is an explicit immutable version.
- No missing value is converted to negative evidence.
- No unratified proposed value enters Tier 1.
- No direct instrument-emitted Tier 1 authority path exists in Build 1. Instrument, parser, import, model-assisted, and manual data all enter as source-backed proposals and require the same active ratification gate before Tier 1.
- No source artifact is overwritten by a parsed value; parsed values always cite the raw artifact and evidence location.
- No vendor-specific adapter is implemented without real, legally usable source files and expected-output fixtures.
- No authority check uses an application default. Ratification, rejection, correction requests, protocol execution, and protocol-derived value ratification all resolve through an explicit governed `AuthorityPolicy` whose lifecycle state is `PUBLISHED` and active at bind time, and whose scope matches the run under the §4.2 scope-match contract.
- No capability decision, source-class acceptance, or advisory-gap classification is made in generic code; it is resolved only through the governed capability resolver (§4.1).
- Build 1 source bytes are stored in PostgreSQL with their source record in the same transaction, and only within both the governed per-source-class size bound (§4, §5) and a global `max_bytes_per_transaction` hard ceiling tied to tested PostgreSQL limits (§5). External content-addressed storage is deferred until a production storage profile is specified.
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
    capabilities.py         governed facility/tool capability profile + resolver contracts
    scope.py                closed EvidenceScope contract + scope-match semantics
    source_artifacts.py     raw source registration and content-hash contracts
    proposals.py            typed proposed-value envelope, target-key, evidence set, validation states
    authority.py            governed actor/role/action policy contracts + lifecycle + principal binding
    validation.py           designed-validation protocol contracts (predicate-bound)
    observations.py         attributed-observation contracts
    ratification.py         Build 1 ratification workflow over proposed values
    persistence.py          existing append-only PostgreSQL store, extended by migrations
  mie/
    capture_service.py      Build 1 source/proposal/ratification orchestration
    build1_bridge.py        snapshot assembly + capture-gate output + bridge replay capsule
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

- Facility/profile identity and evidence scope (§4.2).
- Owning organization/actor and authority-policy reference.
- Instruments/tools available by governed type, not vendor folklore.
- Source systems such as LIMS, QMS, historian, file drop, manual upload, or unknown.
- Accepted source artifact classes such as CSV, PDF, image, vendor export, note, or log.
- Measurement classes supported by available tools.
- Required calibration/MSA evidence types for each declared tool/method class.
- Explicit unsupported and unknown capabilities.
- A governed `max_bytes_per_source_class` bound for every accepted source artifact class.
- A published dimension precedence consumed by the frozen capability resolver (§4.1).
- Effective and expiration timestamps.
- Owner, lifecycle state, and evidence references.

A Build 1 run binds exactly one capability-profile version by complete governed reference. The profile's evidence scope must match the run scope, source-artifact scope, proposal scope, and any Build 0 snapshot scope assembled from it, under the §4.2 scope-match contract. A wrong-but-explicit profile is still rejected if its scope, owner, or active lifecycle state is incompatible with the run.

### 4.1 Capability Resolver Contract (closed)

The capability profile is data; the resolver is the deterministic decision procedure that maps a concrete intake to a capability state. Capability decisions MUST NOT live in application code or operator judgment.

```python
class CapabilityRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requirement_ref: GovernedRef
    # ordered, closed set of match dimensions evaluated against the bound profile
    source_class_id: TermId | None
    source_system_id: TermId | None
    tool_type_id: TermId | None
    measurement_class_id: TermId | None

class CapabilityResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requirement_ref: GovernedRef
    profile_ref: GovernedRef
    resolver_algorithm_id: Literal["CAPABILITY_RESOLVER_V1"]
    state: Literal["SUPPORTED", "UNSUPPORTED", "UNKNOWN", "AMBIGUOUS"]
    reason_id: TermId
    matched_capability_refs: tuple[GovernedRef, ...]
    unmatched_dimension_ids: tuple[TermId, ...]
```

Normative resolver rules:

1. The resolver is frozen as `CAPABILITY_RESOLVER_V1`. It consumes the profile's published dimension precedence as governed data; the matching algorithm itself does not vary by profile.
2. A `None` dimension on a `CapabilityRequirement` means the requirement is not constrained on that dimension and that dimension does not participate in matching. Every non-null requirement dimension MUST resolve against the bound profile under the published precedence.
3. A `None` on a profile capability declaration is an explicit wildcard matching any value on that dimension; an explicit value matches only that value. Wildcards are governed declarations, never an application default.
4. A requirement fully matched by an explicitly available capability is `SUPPORTED`.
5. A requirement matched by an explicitly declared unsupported capability is `UNSUPPORTED`.
6. A requirement that matches no declared capability — available or unsupported — is `UNKNOWN`.
7. A requirement matching more than one declared capability without a governed precedence winner is `AMBIGUOUS`.
8. Any `UNSUPPORTED`, `UNKNOWN`, or `AMBIGUOUS` resolution becomes an explicit advisory/capture gate (§10.1) carrying its `reason_id`; it is never inferred support and never negative evidence.
9. Partial matches (some dimensions matched, some unmatched) resolve to `UNKNOWN` for the unmatched dimension set; the resolution records exactly which dimensions did not match in `unmatched_dimension_ids`.
10. Publication-time overlap lint: a profile fails publication if two available capabilities can both fully match any single requirement shape without a governed precedence winner (latent `AMBIGUOUS`). Profiles cannot ship a configuration whose resolution is non-deterministic.

### 4.2 Evidence Scope Contract (closed)

Scope is used as a binding/authorization gate by the capability profile, authority policy, source artifacts, proposals, protocols, and the bridge. It is a closed type with deterministic match semantics.

```python
class ScopeDimension(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dimension_id: TermId
    value: CanonicalScalar

class EvidenceScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scope_id: OpaqueId
    facility_id: TermId
    domain_id: TermId
    dimensions: tuple[ScopeDimension, ...]  # canonically sorted by dimension_id; may be empty
```

Normative scope rules:

1. Two scopes are **equal** iff `(facility_id, domain_id, dimensions)` are byte-equal under §2.13 canonicalization.
2. Scope A **contains** scope B iff `facility_id` and `domain_id` are equal and every dimension present in A is present and equal in B (A is the broader/run scope; B is the record scope). Dimensions absent from A are unconstrained.
3. Two scopes are **disjoint** iff `facility_id` or `domain_id` differ, or any shared dimension_id holds differing values.
4. A record binds to a run only if the run scope **contains** the record scope. Disjoint or wrong-facility/domain scope fails closed before source/proposal selection and produces a `PROFILE_INVALID` capture gate (§10.1) when the failing record is the capability profile, or the relevant gate state for other records.
5. Scope match is computed by a frozen procedure; no module may invent its own interpretation.

### Exit Gate

- A profile with no declared capability cannot silently allow intake.
- Unknown and unsupported capabilities are distinct states, produced only by the §4.1 resolver under `CAPABILITY_RESOLVER_V1`.
- Missing capability produces a typed advisory gap, never a guessed source path.
- Capability lists are canonical, unique, and order-independent.
- A profile with a latent-ambiguous overlap fails publication (§4.1 rule 10).
- `max_bytes_per_source_class` is present for every accepted source class; an absent bound fails publication.
- Scope mismatch (non-containment), inactive lifecycle state, missing owner, or missing authority policy fails before source/proposal selection using the §4.2 contract.
- The profile, resolver, and scope-match procedure have no domain constants in generic code.

### Deferred

Production RBAC, dynamic discovery from enterprise systems, vendor-specific identity resolution, multi-site capability federation, and automatic emergent-tool onboarding (a new tool is added only by publishing a new governed profile version).

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
- Evidence scope (§4.2) and capability-profile reference.
- Parser eligibility state: `UNPARSED`, `PARSER_UNAVAILABLE`, `PARSER_UNSUPPORTED`, `PARSER_READY`, `PARSER_FAILED`.

Build 1 source registration is one PostgreSQL transaction: resolve the source class against the bound capability profile (§4.1), enforce its `max_bytes_per_source_class` bound **and** the global `max_bytes_per_transaction` hard ceiling, then insert the source record, raw bytes, hash metadata, audit event, and any parser-eligibility record together, then verify the stored bytes against the recorded hash before commit visibility. A failure commits neither row nor bytes. An over-size (per-class or global) or unsupported-class artifact is rejected at the service boundary before any byte is persisted and produces an explicit capture gate (§10.1). Raw source bytes are not canonicalized before hashing; newline normalization, text decoding, OCR, and parser cleanup produce separate proposal records that cite the raw artifact.

The global `max_bytes_per_transaction` ceiling is a governed value set conservatively for Build 1 (initial guidance: small/text-class friendly, well below tested PostgreSQL single-transaction limits). It is independent of per-class limits and exists to protect the write-ahead log and transaction memory from a single in-bound large artifact. Raising it requires explicit governed justification.

### Exit Gate

- Identical bytes produce identical content hashes.
- Different metadata over identical bytes does not change raw content hash.
- Text and binary artifacts are hashed as exact bytes received, not as canonicalized text.
- An artifact exceeding `max_bytes_per_source_class` or the global `max_bytes_per_transaction` ceiling is rejected at the service boundary before persistence with a governed reason ID, proven by a dedicated oversize fixture.
- A parsed/proposed record cannot exist without a registered raw source.
- Unsupported source class becomes explicit capture gate.
- Failed parser does not mutate or delete the source artifact.
- Raw source registration is append-only and replayable.

### Deferred

External large-object storage, malware scanning, data retention policy, production access control, external system polling, and vendor-native binary parser fidelity.

---

## 6. Slice 3 — Typed Proposal Layer

### Goal

Represent extracted or translated values as typed proposals with evidence locations, never as authoritative facts.

### Scope

`TypedValueProposal` captures:

- Proposal identity.
- Proposed `TargetKey` (§6.1).
- Proposed typed value with unit and canonical timestamp policy where applicable.
- A closed `ProposalEvidence` set (below).
- Proposal method: deterministic parser, manual entry, model-assisted proposal, or external import.
- Optional `corrects_proposal_ref`.
- Validation state: `PROPOSED`, `VALIDATION_FAILED`, `READY_FOR_RATIFICATION`, `REJECTED`, `SUPERSEDED`.
- Validation errors with governed reason IDs.

The proposal evidence chain is a closed set so that parser/manual, protocol-derived, and observation-derived proposals share one authoritative schema and one hash:

```python
class EvidenceLocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    # exactly one location kind populated
    page: int | None
    row: int | None
    column: int | None
    cell: str | None
    byte_span: tuple[int, int] | None
    image_region: str | None
    line_range: tuple[int, int] | None

class ProposalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    primary_source_artifact_ref: GovernedRef
    supporting_refs: tuple[GovernedRef, ...]   # source artifacts, protocol results, observations; unique, canonically sorted by (logical_id, version_id)
    evidence_location: EvidenceLocation
```

The canonical ordering of `supporting_refs` is included in the proposal content hash. Protocol-derived proposals set the protocol result as a supporting ref; observation-derived proposals set the observation as a supporting ref; neither adds an ad hoc field.

### 6.1 TargetKey Contract (closed)

Active-value resolution and `ACTIVE_VALUE_CONFLICT` depend entirely on a stable, governed target key. The key is closed and its allocation and merge semantics are normative.

```python
class ContextKeyDimension(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dimension_id: TermId
    value: CanonicalScalar

class ContextKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dimensions: tuple[ContextKeyDimension, ...]  # canonically sorted by dimension_id; empty tuple = no disambiguating dimensions

class ContextKeyDimensionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dimension_id: TermId
    value_type: TermId
    required: bool

class ContextKeyRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target_record_type_id: TermId
    target_schema_version: OpaqueId
    allowed_dimensions: tuple[ContextKeyDimensionSpec, ...]  # unique by dimension_id; defines canonical sort order

class TargetKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target_domain_id: LogicalId        # stable cross-version domain identity
    target_record_type_id: TermId
    target_logical_id: LogicalId
    target_schema_version: OpaqueId
    field_path: FieldId
    context_key: ContextKey
```

Normative rules:

1. **Allocation.** `target_logical_id` is caller-supplied, consistent with §2.12 caller-supplied identity. It is not engine-generated. A proposal that names a `target_logical_id` not previously seen in scope is a **create**; a proposal that names an existing in-scope `target_logical_id` for the same `target_record_type_id` is an **amend**. Mixing record types under one `target_logical_id` is rejected.
2. **context_key.** `context_key` carries every schema-declared disambiguating dimension (e.g. sample side, replicate, process step, parameter channel, specimen ID, condition set), validated against the governed `ContextKeyRegistry` for `(target_record_type_id, target_schema_version)`. If the schema declares no disambiguating dimensions, `context_key.dimensions` is the explicit empty tuple. Unknown, missing-required, extra, or non-canonical dimensions make the proposal invalid; they are never collapsed into the same target or split into ungoverned fragments.
3. **Uniqueness scope.** Two proposals share a target key if and only if all of `(target_domain_id, target_record_type_id, target_logical_id, target_schema_version, field_path, context_key)` are byte-equal under §2.13 canonicalization. Active-value resolution (§7) groups strictly by this tuple.
4. **Correction/retarget.** A corrected proposal carries `corrects_proposal_ref` and MUST address the identical target key as the proposal it corrects; it cannot silently retarget. A genuine retarget is a new proposal under the new key with its own ratification.
5. **No cross-source merge in Build 1.** Build 1 does not reconcile two distinct `target_logical_id`s into one fact; that is deferred semantic reconciliation. Two sources asserting the same fact under different caller-supplied logical IDs remain distinct target keys until a human ratifies one and supersedes/rejects the other.
6. **Cross-schema-version continuity.** `target_domain_id` is the stable identity of a domain fact and is constant across schema versions; `target_schema_version` is the representation version. A schema migration does not by itself fork identity for grouping by `target_domain_id`, but a corrected/amended proposal that crosses a schema version MUST be expressed through a governed migration mapping record that binds the old and new `(target_schema_version, context_key)` pair. Absent a governed migration mapping, a cross-version correction is invalid. (Owner confirmation pending — see §16.)

### Exit Gate

- Unknown units, malformed timestamps, ambiguous terms, or unsupported field paths fail validation.
- A proposal without a `ProposalEvidence` set (primary ref + valid evidence location) cannot be ratified.
- A proposal without a valid `TargetKey` cannot be ratified.
- Unknown/missing-required/extra/non-canonical `context_key` dimensions fail validation against the bound `ContextKeyRegistry`.
- Model-assisted and deterministic-parser proposals serialize to the same proposed-value schema.
- Model-assisted proposal can be disabled without changing any authoritative output.
- Proposed values cannot enter Build 0 Tier 1.
- Dual-source, correction, and cross-schema-version migration fixtures prove no false key collision and no silent fork.

### Deferred

LLM UI, OCR quality, vendor parser qualification, automatic semantic reconciliation/cross-source merge, caller-supplied-ID dedup advisory (see §16), and production data normalization.

---

## 7. Slice 4 — Human Ratification Workflow

### Goal

Promote a proposed value into a governed decision-effective input only through an explicit human event.

### Scope

`ProposalRatificationEvent` captures:

- Exact proposal reference and proposed value hash.
- Ratifying actor (authenticated principal), role, and authority-policy reference.
- Decision: `RATIFIED`, `REJECTED`, `CORRECTION_REQUESTED`, or `SUPERSEDED`.
- Effective time and recorded time.
- Evidence references and optional reviewer note as non-authoritative prose.
- Optional superseded ratification-event reference.

**Minimum trust anchor.** Build 1 binds every ratification/authority write to an authenticated principal resolved against an immutable governed actor registry. The database-enforced principal on the write MUST equal the `ratifying actor`; an event whose principal does not resolve to a registered actor fails closed. Build 1 does not implement production identity providers, e-signature, or RBAC (§14); absent that production layer, Build 1 is limited to synthetic and non-sensitive evaluation data. This limitation is a stated operational boundary, not a defect.

`AuthorityPolicy` is the governed Build 1 authority model. It declares actors or actor groups, roles, permitted actions, governed scope (§4.2), target record classes, separation-of-duties requirements, lifecycle state, named approver, effective/expiration times, and evidence references. `AuthorityPolicy` has explicit lifecycle states `DRAFT|PUBLISHED|DEPRECATED|REVOKED`; **only a `PUBLISHED`, in-effect version whose scope contains the run scope may authorize any ratification, rejection, correction, protocol execution, or protocol-derived ratification.** A `DRAFT` or non-effective policy authorizes nothing and fails closed. Build 1 does not impose a universal dual-actor rule. A single-actor research lab may ratify only when the bound `PUBLISHED` policy explicitly allows the same actor for the action and scope. If the policy requires independence, the actor who authored the proposal, executed the protocol, or authored the observation cannot ratify the resulting value.

`ProposalRatificationEvent` is the only event that makes a value decision-effective for Tier 1 in Build 1. Protocol results and attributed observations may produce new typed proposals, but those proposals still require ratification. There is no separate promotion event with independent authority semantics.

Active-value resolution is computed at snapshot-bind time from the exact ratification event set in the snapshot. For each target key (§6.1):

1. Select events whose proposal hash verifies, authority policy is `PUBLISHED` and active, scope contains the run, `effective_at <= as_of_time`, and `recorded_at <= as_of_time`.
2. Remove events superseded by another eligible event.
3. `REJECTED`, `CORRECTION_REQUESTED`, and `SUPERSEDED` events cannot produce an active value.
4. Zero active `RATIFIED` heads means no Tier 1 value for that target key.
5. Exactly one active `RATIFIED` head is the decision-effective value.
6. More than one active `RATIFIED` head for the same target key is `ACTIVE_VALUE_CONFLICT` and fails closed before Build 0.

PostgreSQL enforces immutable event identity and duplicate primary keys; it does not claim to prove every bitemporal active-head uniqueness question with a static constraint. Build 1 write transactions use the single-writer persistence lane, and bind-time active-value resolution is the authoritative conflict check.

`CORRECTION_REQUESTED` is terminal for the proposal version it references. The corrected content is submitted as a new `TypedValueProposal` with `corrects_proposal_ref` addressing the identical target key; historical rejection/correction events remain visible and replayable.

### Exit Gate

- Ratification verifies the proposal content hash before eligibility.
- A ratification write whose authenticated principal does not equal the registered ratifying actor fails closed.
- An unpublished, non-effective, or wrong-scope authority policy authorizes nothing.
- A later-recorded backdated ratification affects only later runs whose `as_of_time` includes it.
- Duplicate active ratification heads for the same target key fail closed with `ACTIVE_VALUE_CONFLICT`.
- Rejected proposals cannot enter snapshots.
- Correction-requested proposals cannot enter snapshots; only a newly submitted corrected proposal can be ratified.
- Protocol-derived and observation-derived values use the same ratification event and active-value resolver as parser/manual proposals.
- Historical replay uses the original active ratification state.

### Deferred

Enterprise identity provider integration, production RBAC, e-signatures, QMS record-of-record semantics, delegated approval workflows, and correction-pending work-queue tooling.

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

`DesignedValidationProtocol` is a governed versioned record with explicit lifecycle states `DRAFT|PUBLISHED|DEPRECATED|REVOKED`, named approver, effective/expiration times, and evidence references. **Only a `PUBLISHED`, in-effect protocol version may be executed or produce bridge-eligible results.** It captures:

- Hypothesis or claim under validation.
- Required data to collect.
- Required method/tool capability and calibration/MSA prerequisites.
- Acceptance criteria as governed deterministic predicates.
- Required actor authority and separation-of-duties rule.
- Result schema and allowed terminal states.

**Acceptance criteria reuse the frozen §7.2 `Predicate` AST and its evaluation semantics.** Acceptance predicates are evaluated under the four-state (`TRUE|FALSE|UNKNOWN|INVALID`) Kleene logic of §7.2, convert numeric operands through a pinned unit registry, treat missing context as `UNKNOWN` (not `FALSE`), and treat `INVALID` as `INVALID_PROTOCOL_EXECUTION`. No new predicate language is introduced.

`DesignedValidationResult` captures:

```python
class DesignedValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    protocol_ref: GovernedRef
    collected_source_artifact_refs: tuple[GovernedRef, ...]
    collected_value_refs: tuple[GovernedRef, ...]
    predicate_evaluations: tuple["ApplicabilityEvaluation", ...]  # §7.2-shaped, with evidence refs
    unit_registry_ref: GovernedRef                # pinned, not snapshot-deferred
    evaluator_algorithm_id: Literal["PREDICATE_EVAL_V1"]   # frozen §7.2 evaluator version
    canonicalization_policy_ref: GovernedRef
    authority_event_ref: GovernedRef              # under a PUBLISHED authority policy
    terminal_state: Literal["VALIDATED", "NOT_VALIDATED", "INCONCLUSIVE", "INVALID_PROTOCOL_EXECUTION"]
    result_hash: Sha256Hex
```

The result pins the exact unit registry, evaluator algorithm/version, and canonicalization policy used; these are part of the result, not a deferred dependency on later bridge context. Replay re-evaluates against the pinned artifacts only.

Terminal state mapping: all required acceptance predicates `TRUE` → `VALIDATED`; any required predicate `FALSE` → `NOT_VALIDATED`; any required predicate `UNKNOWN` → `INCONCLUSIVE`; any `INVALID` → `INVALID_PROTOCOL_EXECUTION`.

A `VALIDATED` protocol result is not itself a Tier 1 fact. It may create a typed proposal whose `ProposalEvidence.supporting_refs` include the protocol result and supporting source artifacts. That proposal becomes decision-effective only through the Slice 4 ratification workflow.

### Exit Gate

- A protocol with missing required data returns `INCONCLUSIVE`, not a guessed pass.
- Acceptance criteria are §7.2 governed predicates, not model judgment, with explicit unit/missing/INVALID semantics.
- Results pin `unit_registry_ref`, `evaluator_algorithm_id`, and `canonicalization_policy_ref`; replay against changed registries/evaluators is rejected, not silently re-derived.
- A draft or non-effective protocol cannot be executed or produce bridge-eligible results.
- A validation result cannot create a proposal from an observation unless the protocol allows that target type.
- A validation result cannot bypass proposal ratification.
- Protocol execution is replayable from bound source/proposal/result records and pinned evaluator artifacts.
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
- Emits explicit, closed capture-gate results for unknown/unsupported capabilities, unsupported source artifacts, missing parser, missing ratification, active-value conflict, missing calibration, or missing MSA (§10.1).

### 10.1 Capture-Gate Output Contract (closed)

Build 1 capture-stage failures and advisory gaps MUST serialize as a closed, hashed, replayable contract. The frozen §9 `MIEOutput` union is unchanged. Capture-gate results are classified as follows:

1. **Post-snapshot, method-resolution gaps that already fit the frozen contract** (e.g. missing ratified evidence after a valid snapshot binds, missing MSA, stale calibration) are produced by the Build 0 engine itself as the existing `RefusalDecision`/`AdvisoryDecision` with governed reason IDs. Build 1 introduces no new field on these.
2. **Pre-snapshot capture-stage failures** (missing/wrong-scope capability profile, unsupported/unknown/ambiguous capability, over-size or unsupported source class, undefined `TargetKey`/`context_key`, `ACTIVE_VALUE_CONFLICT`, unpublished authority policy, missing ratification) cannot bind a Build 0 snapshot and so MUST NOT fabricate pack/policy/snapshot references. They serialize as a closed `CaptureGateResult` union carrying one or more findings:

```python
class CaptureGateFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    gate_state: Literal[
        "PROFILE_INVALID", "CAPABILITY_UNSUPPORTED", "CAPABILITY_UNKNOWN",
        "CAPABILITY_AMBIGUOUS", "SOURCE_CLASS_UNSUPPORTED", "SOURCE_OVERSIZE",
        "TARGET_KEY_INVALID", "ACTIVE_VALUE_CONFLICT", "AUTHORITY_NOT_PUBLISHED",
        "MISSING_RATIFICATION"
    ]
    reason_id: TermId
    affected_target_key: TargetKey | None
    affected_capability_ref: GovernedRef | None
    conflicting_ratification_refs: tuple[GovernedRef, ...]
    missing_record_refs: tuple[GovernedRef, ...]

class CaptureGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_kind: Literal["CAPTURE_GATE"]
    case_id: OpaqueId
    dispositional: Literal[False]
    non_record_of_record: Literal[True]
    operational_mode: Literal["RESEARCH_ONLY"]
    gate_findings: tuple[CaptureGateFinding, ...]   # non-empty; canonically ordered by precedence then (gate_state, reason_id)
    primary_gate_state: str                          # = highest-precedence finding's gate_state
    next_required_record_type_id: TermId
    audit_event_ids: tuple[OpaqueId, ...]
    capture_gate_hash: Sha256Hex   # SHA-256 over the canonical result minus this field
```

A run may surface multiple independent capture failures. `gate_findings` is the complete closed set; `primary_gate_state` is derived deterministically from a published precedence (most-blocking first):

```text
PROFILE_INVALID > AUTHORITY_NOT_PUBLISHED > CAPABILITY_UNSUPPORTED >
CAPABILITY_AMBIGUOUS > CAPABILITY_UNKNOWN > SOURCE_CLASS_UNSUPPORTED >
SOURCE_OVERSIZE > TARGET_KEY_INVALID > ACTIVE_VALUE_CONFLICT > MISSING_RATIFICATION
```

A single Build 1 run persists exactly one of: a Build 0 `MIEOutput` (when a snapshot binds), or one `CaptureGateResult` (when capture fails before binding) carrying all findings. Diagnostics explain the fail-closed state; they create no authority and emit no prose-only fact. Every `gate_state` and the multi-finding aggregation each have a dedicated fixture.

### 10.2 Bridge Replay Capsule (closed)

Build 0 downstream replay alone does not close Build 1 audit. A `Build1BridgeReplayCapsule` is stored atomically beside each bridge run and binds the upstream capture-to-input chain:

```python
class Build1BridgeReplayCapsule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    capsule_kind: Literal["BUILD1_BRIDGE"]
    run_id: OpaqueId
    capability_profile_ref: GovernedRef
    source_artifact_refs: tuple[GovernedRef, ...]
    proposal_refs: tuple[GovernedRef, ...]
    ratification_event_refs: tuple[GovernedRef, ...]
    observation_refs: tuple[GovernedRef, ...]
    protocol_result_refs: tuple[GovernedRef, ...]
    active_value_resolution: tuple["ActiveValueBinding", ...]  # (TargetKey -> RATIFIED head ref)
    produced_build0_request_hash: Sha256Hex
    produced_snapshot_hash: Sha256Hex | None     # null for capture-gate results
    capture_gate_hash: Sha256Hex | None          # null when a snapshot bound
    algorithm_id: Literal["BUILD1_BRIDGE_REPLAY_V1"]
    capsule_hash: Sha256Hex
```

Replay re-derives the active-value resolution by target key from the bound ratification set and requires byte identity of the produced Build 0 request/snapshot hash (or the capture-gate hash). Missing, altered, or non-canonical capsule material returns `INTEGRITY_FAILURE` without reconstructing a decision. All reference sets are unique and sorted by `(logical_id, version_id)`.

### Exit Gate

- A complete ratified fixture reaches the existing Build 0 path unchanged.
- An equivalent unratified fixture stops before Tier 1 with a `MISSING_RATIFICATION` `CaptureGateResult`.
- Unsupported capability appears as a closed `CaptureGateResult`, never as negative evidence.
- Wrong-scope capability profile, missing/unpublished authority policy, undefined context key, and active-value conflict each fail before Build 0 with a closed diagnostic.
- A run with multiple independent failures returns one `CaptureGateResult` with all findings and a deterministic `primary_gate_state`.
- Every `gate_state` and the bridge replay capsule round-trip byte-identically.
- Removing all model adapters changes no structured output.
- Build 0 replay remains byte-identical for runs created through the bridge, and the §10.2 capsule proves which exact upstream records produced the snapshot.

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
- Canonical samples for source registration, proposal, ratification, observation, validation protocol, capture-gate result, bridge replay capsule, and Build 0 bridge.
- Cross-minor canonical equality for the published fixture corpus.
- JSON validation schemas and canonical wire schemas, including `EvidenceScope`, `TargetKey`, `ContextKey`, `ContextKeyRegistry`, `ProposalEvidence`, `CapabilityResolution`, `DesignedValidationResult`, `CaptureGateResult`, and `Build1BridgeReplayCapsule`.
- Replay recipes for Build 1 record lifecycle paths and the §10.2 bridge replay capsule.

### Exit Gate

- Generated evidence derives readiness from executed gates only.
- Build 1 records replay byte-identically across process restart.
- The §10.2 bridge replay capsule replays byte-identically and proves the upstream chain.
- Tampered source/proposal/ratification/observation/protocol/capsule records fail closed.
- Missing capability/profile/source/proposal records produce explicit `CaptureGateResult` outputs.
- Fail-closed results include actionable diagnostics without introducing authority or prose-only facts.
- Completion evidence is self-audited and claims no external attestation.

### Deferred

External attestation, production backup/recovery, production concurrency, cryptographic multi-party governance, and qualified deployment.

---

## 12. Requirement Ownership Matrix

| Requirement | Primary Slice | Governing Spec |
|---|---:|---|
| Governed capability profile | 1 | §§2.7, 2.11, 6, 18 |
| Capability resolver (matching procedure) | 1 | §§2.7, 2.9, 2.11, 18 |
| Evidence-scope contract + match semantics | 1 | §§2.7, 2.11, 2.12 |
| Unknown/unsupported capability gaps | 1, 7 | §§2.7, 2.9, 18 |
| Per-source-class + global max-byte guard | 1, 2 | §§2.7, 12 |
| Raw source preservation | 2 | §§2.5, 11 |
| Content-hashed source identity | 2 | §§2.12–2.13 |
| Parser eligibility without silent failure | 2 | §§2.7, 11 |
| Atomic source-byte storage | 2 | §§2.5, 12 |
| Typed proposed-value envelope + evidence set | 3 | §§2.3–2.5, 6, 11 |
| TargetKey identity/allocation/merge/version | 3, 4 | §§2.4, 2.12, 6.1, 11 |
| Evidence-location requirement | 3 | §§2.5, 11 |
| Model-disabled equivalence | 3, 7 | §§2.3, 2.12 |
| Human ratification event + trust anchor | 4 | §§2.4, 6, 11 |
| Authority policy + publication lifecycle | 4 | §§2.4, 6, 11 |
| Bitemporal ratification eligibility | 4 | §§2.4, 2.12 |
| Active-value conflict detection | 4, 7 | §§2.4, 2.7, 2.12 |
| Rejection/correction append-only history | 4 | §§2.4, 11, 12 |
| Attributed observation containment | 5 | §§2.6, 11 |
| Observation promotion discipline | 5, 6 | §§2.4, 2.6, 11 |
| Designed validation protocols (predicate-bound, lifecycle, pinned evaluator) | 6 | §§7.2, 11 |
| Deterministic validation results | 6 | §§2.7, 2.11, 7.2, 11 |
| Build 0 bridge over ratified values only | 7 | §§2.4, 5, 7, 18 |
| Capture-gate output contract (multi-finding) | 7 | §§2.7, 9 |
| Bridge replay capsule (upstream provenance) | 7, 8 | §§2.12, 7.7, 12 |
| Advisory gaps for missing capability/evidence | 7 | §§2.7, 2.9, 9 |
| Build 1 replay and evidence closeout | 8 | §§2.12–2.13, 12, 17 |

---

## 13. Build 1 Completion Gate

Build 1 is complete only when:

1. Every slice gate passes locally against PostgreSQL.
2. All Build 0 tests still pass unchanged.
3. Every new authoritative record has a closed schema and canonical wire contract, including `EvidenceScope`, `TargetKey`, `ContextKey`, `ContextKeyRegistry`, `ProposalEvidence`, `CapabilityResolution`, `DesignedValidationResult`, `CaptureGateResult`, and `Build1BridgeReplayCapsule`.
4. Every raw source record preserves exact received bytes, raw content hash, and provenance in one PostgreSQL transaction within both the per-source-class and global size bounds.
5. Every typed proposal cites a closed `ProposalEvidence` set with exact source evidence location and a valid `TargetKey`.
6. No value enters Tier 1 without active ratification resolved through a `PUBLISHED`, scope-matching governed authority policy bound to an authenticated principal.
7. Unvalidated attributed observations are Tier-2-only.
8. Unknown/unsupported/wrong-scope capability produces an explicit `CaptureGateResult`, not inferred support or inferred absence, via the §4.1 resolver and §4.2 scope-match.
9. Designed validation protocols are governed deterministic predicate-bound records with pinned evaluator/registry refs that cannot qualify a method, production process, or bypass ratification.
10. Removing model adapters changes no structured output.
11. Static scans find no vector implementation, SQLite fallback, capability/authority/scope logic in generic modules, or domain constants in generic modules.
12. Build 1 replay detects tampering and missing source/proposal/ratification/authority/observation/protocol records, and the §10.2 bridge capsule replays byte-identically.
13. Generated Build 1 completion evidence binds exact source commit, governing-document hashes, dependency lockfile, migrations, test inventory, gate map, schemas, canonical samples, and cross-minor fixture equality.

Passing Build 1 does not qualify a lab, instrument, source system, method, MSA study, vendor parser, or production decision. It proves the capture and advisory layer can preserve provenance, propose typed records, enforce ratification, contain observations, and feed the deterministic Build 0 engine without weakening the firewall.

---

## 14. Explicitly Deferred

- SpaceX-specific LIMS, QMS, historian, or vendor instrument integration.
- Vendor-native adapters without real lawful sample files and expected-output fixtures.
- Direct instrument-emitted Tier 1 authority without ratification.
- External content-addressed source storage and large-object production hardening (async/external blob ingest explicitly out of Build 1).
- Cross-source semantic reconciliation / logical-fact merge.
- Caller-supplied-ID dedup advisory (see §16 for the open product decision).
- Provisional or risk-downgraded Tier 1 (rejected: contradicts the §2.4 firewall and §2.7 fail-closed).
- Production RBAC, e-signature, QMS record-of-record semantics, retention, backup/recovery, and tamper-evidence policy.
- Correction-pending work-queue tooling.
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
4. Are the proposed record types and closed contracts (scope, capability profile + resolver, source artifact, typed proposal + evidence set + TargetKey/ContextKey, ratification + authority lifecycle + trust anchor, observations, validation protocols + pinned evaluator, capture-gate output, bridge replay capsule) sufficient to preserve provenance and replay?
5. Does any gate rely on hidden defaults, magic values, vectors, model authority, SQLite fallback, or vendor assumptions?
6. Is the capability profile plus §4.1 resolver and §4.2 scope contract deterministic enough to proceed before knowing a specific lab's equipment list?
7. What is the smallest correction that would make this plan implementation-ready without pulling Build 2/3 work into Build 1?

Findings should cite the exact plan section and governing spec section, classify severity as `BLOCKER|MAJOR|MINOR|NIT`, and distinguish true contradictions from preferences or deferred production work.

---

## 16. Open Owner Decisions

These require owner/domain authority before freeze; they are not blind-review items:

1. **Schema-version identity model (§6.1 rule 6).** Confirm the drafted split between stable `target_domain_id` and representation `target_schema_version`, and the governed migration-mapping requirement for cross-version corrections. This affects longitudinal continuity and active-value resolution.
2. **Caller-supplied logical-ID fragmentation.** Decide whether Build 1 adds a non-authoritative Tier-2 dedup advisory on new logical IDs (raised by review), given the §2 ban on similarity retrieval and the deferral of cross-source reconciliation. Currently deferred (§14).
3. **Trust-anchor scope (§7).** Confirm the authenticated-principal/actor-registry baseline and the synthetic/non-sensitive-data limitation are acceptable for the research phase, or specify a different boundary.