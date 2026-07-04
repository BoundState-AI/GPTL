# ORACLE Review Report

**Document:** /data/sessions/247194a76c64/GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.2.md
**Session:** 20260623-055209
**Rounds:** 2
**Converged:** No

**Consensus:** BLOCKED — stopped without consensus

**Convergence Reason:** Round 2 surfaced a coherent, non-duplicative set of genuinely material completeness defects (undefined scope contract, unpublished ContextKey/registry, proposal-evidence contradiction, model-output ambiguity, unpinned validation evaluator, single-state capture gate) that I have revised into closed contracts. Reviewers are converging on real spec-completeness, not drifting into taste. However, we are at the hard 2-round cap and three remaining items require owner/domain authority rather than further blind review: the schema-version identity model (a TargetKey change with replay implications), the trust-anchor scope, and the logical-ID fragmentation/dedup product direction. Per final-round policy I recommend HUMAN_REVIEW rather than another round; firewall-weakening proposals (provisional profiles, dropping the replay capsule, mandatory external CAS) were rejected as owner-ratified invariants.

**Reviewer pool:** 4 oracles across 3 vendors (Codex, Fran share openai)

## Metrics

- Accepted critical defects: 2
- Accepted high defects: 7
- Total accepted defects: 16
- Total rejected claims: 5
- Preference-only findings: 2
- Duplicate rate: n/a (not measured in this workflow)
- Rounds to stability: 2
- Converged: False

- Issue-ID continuity across rounds: 0%

## Data Integrity Warnings

> 8 coordinator decision(s) reference issue IDs with no matching normalized issue: BETH-R1-ISSUE-008, BETH-R1-ISSUE-009, BETH-R1-ISSUE-010, BETH-R2-ISSUE-010, BETH-R2-ISSUE-011, BETH-R2-ISSUE-012, BETH-R2-ISSUE-013, BETH-R2-ISSUE-014. Severity counts above may be incomplete for these decisions.

## Reviewer Verdicts (final round)

- **Codex**: revise
- **Fran**: major_revision
- **Gemini**: approve_with_minor_changes
- **Grok**: major_revision

## Dissent Summary

> The findings below were raised by reviewer oracles and NOT accepted into the revised draft. The coordinator's reasoning is recorded in full. A rejection is the coordinator's judgment, not a consensus verdict — readers should weigh the reviewer's position themselves.

### [REJECTED BY COORDINATOR] BETH-R1-ISSUE-008 (BETH-R1-ISSUE-008, round 1)
**Coordinator reasoning (full):** Grok's 'provisional Tier-1 under explicit risk policy with provenance downgrade' (0.85) directly contradicts the ratification firewall (§2.4) and fail-closed (§2.7), which are owner-ratified invariants. A constant-refusal complaint about human non-compliance is a product/operations concern, not a Build 1 plan defect; the correct answer is governed authority policy plus advisory routing, both already present.

### [REJECTED BY COORDINATOR] BETH-R1-ISSUE-009 (BETH-R1-ISSUE-009, round 1)
**Coordinator reasoning (full):** Grok's 'treat capability profile as best-effort heuristic rather than hard gate' (0.75) contradicts fail-closed and the owner's capability-profile model. Emergent lab tools are handled by issuing a new governed profile version and surfacing advisory gaps in the meantime — exactly the designed behavior. No defect.

### [UNRESOLVED QUESTION] BETH-R2-ISSUE-010 (BETH-R2-ISSUE-010, round 2)
**Coordinator reasoning (full):** Gemini (0.98) and Grok (0.8) want a non-blocking Tier-2 advisory lexical-similarity check on new logical IDs to surface probable duplicates. The concern (silent fragmentation) is legitimate, but the proposed fix introduces lexical similarity matching that brushes the §2 build rule against similarity retrieval/nearest-match and expands scope into deferred cross-source reconciliation. This is a product-direction decision, not a clear defect. Flagged as an open question for the owner rather than revised.

### [REJECTED BY COORDINATOR] BETH-R2-ISSUE-012 (BETH-R2-ISSUE-012, round 2)
**Coordinator reasoning (full):** Grok (0.85) again proposes a provisional/risk-flagged profile binding and removing AMBIGUOUS as terminal. This is the same firewall/fail-closed weakening rejected in R1 (ISSUE-008/009) and explicitly listed in §14 as rejected. Owner-ratified invariant; no new evidence.

### [REJECTED BY COORDINATOR] BETH-R2-ISSUE-013 (BETH-R2-ISSUE-013, round 2)
**Coordinator reasoning (full):** Grok (0.75) calls the replay capsule 'integrity theater' and would drop per-run capsule verification. The capsule is the accepted R1 resolution to a real audit gap (ISSUE-003) and the insider/DB-admin threat is exactly what §14 defers to cryptographic multi-party governance. Dropping it regresses the audited capture-to-input chain. Model taste, not a defect.

### [REJECTED BY COORDINATOR] BETH-R2-ISSUE-014 (BETH-R2-ISSUE-014, round 2)
**Coordinator reasoning (full):** Grok (0.9) and part of Gemini/Fran want mandatory external CAS or async blob ingest now. Raw bytes in PostgreSQL is an owner-direction decision; external content-addressed storage is explicitly deferred (§2, §14). The legitimate sub-point (a hard size envelope) is accepted under ISSUE-007. The architecture change itself is rejected as owner-deferred.

## Round 1

> **Degraded quorum:** 3/4 reviewers — Gemini failed this round and submitted no review. Absence of findings from a failed reviewer is not agreement.

### [HIGH] Bridge gap/refusal/advisory states have no closed persisted output contract (BETH-R1-ISSUE-001)
**Confidence (as reported):** 0.95
**Sources:** Codex

### [HIGH] Target-key identity, allocation, and merge semantics underspecified (BETH-R1-ISSUE-002)
**Confidence (as reported):** 0.93
**Sources:** Codex, Fran
**Corroboration:** same-vendor — all corroborating reviewers share provider 'openai'; same-model agreement is weaker evidence than cross-vendor agreement

### [HIGH] Bridge upstream provenance/replay not specified (BETH-R1-ISSUE-003)
**Confidence (as reported):** 0.90
**Sources:** Fran

### [HIGH] Capability resolver (matching procedure) undefined, only the data is defined (BETH-R1-ISSUE-004)
**Confidence (as reported):** 0.90
**Sources:** Fran

### [MEDIUM] Designed-validation acceptance predicates not bound to an executable contract (BETH-R1-ISSUE-005)
**Confidence (as reported):** 0.88
**Sources:** Codex

### [MEDIUM] AuthorityPolicy and DesignedValidationProtocol lack publication/lifecycle gate (BETH-R1-ISSUE-006)
**Confidence (as reported):** 0.85
**Sources:** Fran

### [LOW] No governed max-size guard on raw-byte source registration (BETH-R1-ISSUE-007)
**Confidence (as reported):** 0.80
**Sources:** Grok

### Coordinator Decisions
- **BETH-R1-ISSUE-001**: accepted_defect — Codex (0.97) is correct that the plan introduces pre-Build-0 capture-stage gap/refusal/advisory states but never binds them to a closed persisted/hashed/replayable output. §9 of the frozen spec only d
- **BETH-R1-ISSUE-002**: accepted_defect — Codex (0.95) and Fran (0.91) both expose that target-key identity, allocation, create-vs-amend, context_key uniqueness scope, and correction/retarget semantics are undefined, yet active-value resoluti
- **BETH-R1-ISSUE-003**: accepted_defect — Fran (0.91) is correct that Build 0 replay alone does not close audit on the capture-to-ratified-input chain. The bridge assembles a snapshot but nothing binds which exact source/proposal/ratification
- **BETH-R1-ISSUE-004**: accepted_defect — Fran (0.94) correctly distinguishes capability-profile DATA from the deterministic resolver that maps a concrete artifact/parser path to a capability state. Without a closed matching contract, support
- **BETH-R1-ISSUE-005**: accepted_defect — Codex (0.91) correctly notes designed-validation acceptance predicates are described but not bound to an executable evaluation contract; §7.2 AST exists only for applicability. Bound protocol acceptan
- **BETH-R1-ISSUE-006**: accepted_defect — Fran (0.88) correctly notes AuthorityPolicy and DesignedValidationProtocol gate Tier 1 input but lack explicit publication/lifecycle rules; 'active' is not 'published/approved'. Spec §11 already requi
- **BETH-R1-ISSUE-007**: accepted_defect — Grok's scalability finding (0.9) is mostly an owner-decided deferral (raw bytes in PostgreSQL is owner-direction decision #3), but the narrow sub-point — declare a governed max byte size per source cl
- **BETH-R1-ISSUE-008**: rejected_claim — Grok's 'provisional Tier-1 under explicit risk policy with provenance downgrade' (0.85) directly contradicts the ratification firewall (§2.4) and fail-closed (§2.7), which are owner-ratified invariant
- **BETH-R1-ISSUE-009**: rejected_claim — Grok's 'treat capability profile as best-effort heuristic rather than hard gate' (0.75) contradicts fail-closed and the owner's capability-profile model. Emergent lab tools are handled by issuing a ne
- **BETH-R1-ISSUE-010**: preference_only — Grok's 'bound the maximum event-set cardinality for active-value computation' is a performance hint, not a correctness defect; active-value resolution is already deterministic over the snapshot-bound 

## Round 2

### [CRITICAL] Scope is a gate everywhere but the scope contract is undefined (BETH-R2-ISSUE-001)
**Confidence (as reported):** 0.97
**Sources:** Codex

### [CRITICAL] TargetKey not actually closed: ContextKey/registry unpublished and schema-version identity undefined (BETH-R2-ISSUE-002)
**Confidence (as reported):** 0.90
**Sources:** Codex, Fran
**Corroboration:** same-vendor — all corroborating reviewers share provider 'openai'; same-model agreement is weaker evidence than cross-vendor agreement

### [HIGH] Proposal evidence schema cannot represent protocol-/observation-derived chains (BETH-R2-ISSUE-003)
**Confidence (as reported):** 0.95
**Sources:** Codex

### [HIGH] No-model-output rule contradicts model-assisted proposal path (BETH-R2-ISSUE-004)
**Confidence (as reported):** 0.95
**Sources:** Fran

### [HIGH] Validation-protocol replay not reproducible (unpinned evaluator/unit registry) (BETH-R2-ISSUE-005)
**Confidence (as reported):** 0.92
**Sources:** Fran

### [MEDIUM] CaptureGateResult cannot represent multiple concurrent capture failures (BETH-R2-ISSUE-006)
**Confidence (as reported):** 0.90
**Sources:** Codex

### [MEDIUM] Raw-byte storage lacks a global transaction size ceiling (BETH-R2-ISSUE-007)
**Confidence (as reported):** 0.90
**Sources:** Gemini, Fran, Grok
**Corroboration:** cross-vendor (3 independent providers)

### [MEDIUM] Capability resolver match semantics still incomplete (BETH-R2-ISSUE-008)
**Confidence (as reported):** 0.85
**Sources:** Fran

### [MEDIUM] Ratification authority has no stated trust anchor (BETH-R2-ISSUE-009)
**Confidence (as reported):** 0.85
**Sources:** Fran

### Coordinator Decisions
- **BETH-R2-ISSUE-001**: accepted_defect — Codex (0.99) is correct: 'scope match' is used as a binding/authorization gate in §4, §5, §7, §9, §10 but no scope schema, canonicalization, or equality/containment semantics exist. This makes profile
- **BETH-R2-ISSUE-002**: accepted_defect — Codex (0.98) and Fran (0.88) converge: the R1 TargetKey fix referenced `ContextKey` and a `ContextKeyRegistry` narratively but never published either wire contract, and `target_schema_version` inside 
- **BETH-R2-ISSUE-003**: accepted_defect — Codex (0.97) found a true internal contradiction: §6 gives a proposal a singular source-artifact reference, but §9 (protocol-derived) and §7 (observation-derived) require multiple supporting evidence 
- **BETH-R2-ISSUE-004**: accepted_defect — Fran (0.98) is correct that 'no model output in canonical payloads' and 'model-assisted TypedValueProposal' are both defensible from the text, since a stored proposal is a canonical record. Narrowed t
- **BETH-R2-ISSUE-005**: accepted_defect — Fran (0.94) correctly notes DesignedValidationResult omits the exact unit-registry ref, evaluator algorithm/version, and canonicalization policy, while predicate outcomes depend on them. 'Snapshot-bou
- **BETH-R2-ISSUE-006**: accepted_defect — Codex (0.95) is right that a run can have multiple independent capture failures but CaptureGateResult allowed exactly one gate_state, with no precedence or aggregation rule, forcing arbitrary first-er
- **BETH-R2-ISSUE-007**: accepted_defect — Gemini (0.95), Fran (0.9), and Grok (0.9) independently raise that the R1 per-source-class bound is necessary but insufficient: a single in-bound binary still risks WAL/transaction destabilization. Ad
- **BETH-R2-ISSUE-008**: accepted_defect — Fran (0.93) correctly notes the R1 resolver still lacks null/wildcard match semantics, publication-time overlap linting, and a frozen algorithm id (profile-local precedence alone does not guarantee de
- **BETH-R2-ISSUE-009**: accepted_defect — Fran (0.95): the core Build 1 control is human ratification, but no principal-binding mechanism was stated, so policy fields are spoofable. Production identity is correctly deferred (§14), but the abs
- **BETH-R2-ISSUE-010**: unresolved_question — Gemini (0.98) and Grok (0.8) want a non-blocking Tier-2 advisory lexical-similarity check on new logical IDs to surface probable duplicates. The concern (silent fragmentation) is legitimate, but the p
- **BETH-R2-ISSUE-011**: preference_only — Gemini (0.9) wants a CorrectionState tracking record / work queue. The authoritative event log is already transactionally sound, append-only, and replayable; correction events remain visible. A pendin
- **BETH-R2-ISSUE-012**: rejected_claim — Grok (0.85) again proposes a provisional/risk-flagged profile binding and removing AMBIGUOUS as terminal. This is the same firewall/fail-closed weakening rejected in R1 (ISSUE-008/009) and explicitly 
- **BETH-R2-ISSUE-013**: rejected_claim — Grok (0.75) calls the replay capsule 'integrity theater' and would drop per-run capsule verification. The capsule is the accepted R1 resolution to a real audit gap (ISSUE-003) and the insider/DB-admin
- **BETH-R2-ISSUE-014**: rejected_claim — Grok (0.9) and part of Gemini/Fran want mandatory external CAS or async blob ingest now. Raw bytes in PostgreSQL is an owner-direction decision; external content-addressed storage is explicitly deferr

## Open Questions

- Schema-version identity: confirm whether TargetKey should carry a stable target_domain_id separate from target_schema_version, and how active-value resolution spans migrations. Drafted as a governed migration mapping; owner authority needed.
- Caller-supplied logical-ID fragmentation: should Build 1 add a non-authoritative Tier-2 dedup advisory, given the §2 ban on similarity retrieval and the deferral of cross-source reconciliation? Product-direction decision.
- Trust-anchor scope: is the stated authenticated-principal/actor-registry baseline acceptable, or does the owner want it elevated/deferred differently for the research phase?
