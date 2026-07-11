#!/usr/bin/env python3
"""
Module: Oracle Build 1 Plan-Review Bundle Builder (v0.7)
Purpose: Rebuild the single-file ORACLE Build 1 plan-review bundle.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "GPTL_Manufacturing_Platform_v0.4.20.md"
PLAN = ROOT / "docs" / "GPTL_BUILD1_PLAN_v0.7.md"
OUTPUT = ROOT / "docs" / "GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.7.md"


def _normalized(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    spec = _normalized(SPEC)
    plan = _normalized(PLAN)

    header = f"""# GPTL MIE Build 1 ORACLE Plan Review Bundle
## Single-Document Specification and Build Plan Packet - v0.7

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20

**Build 1 plan:** GPTL MIE Build 1 Plan v0.7

**Spec SHA-256:** `{_sha256(spec)}`

**Build 1 plan SHA-256:** `{_sha256(plan)}`

---

## ORACLE Review Charter

This is the only input document for Build 1 plan review. It embeds the complete frozen governing specification and the proposed Build 1 plan. Do not request a second document or import any section as a separate rule pack.

Build 1 is not a new architecture. It is the implementation plan for the existing v0.4.20 Build 1 scope: capability-profiled capture, source registration, evidence-grounded typed proposals, human ratification, attributed observations, designed-validation protocols, and advisory bridge into the already-frozen Build 0 deterministic engine.

Build 1 is not a production qualification effort. It must not be reviewed as if it promises SpaceX-specific integration, production LIMS coverage, vendor parser fidelity, qualified MSA, production RBAC, QMS record-of-record semantics, distributed workers, or autonomous root-cause/disposition decisions.

This v0.7 packet carries forward the owner-direction decisions from ORACLE session `20260623-040533`:

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
4. Build 1 does not require the frozen Build 0 engine to share the caller's transaction. If Build 0 cannot run inside a caller-supplied unit of work, Build 1 uses the narrowed-boundary bridge attempt state machine with immutable request hashes and read-by-ID reconciliation.
5. Build 1 records single-actor research ratification as an explicit policy-allowed exception, not as independent separation-of-duties.
6. Source registration enforces governed max-byte limits while streaming the payload; it must not buffer an unbounded payload before rejection.
7. Build 1 covers messy source artifacts only within ratifiable replay-bound evidence classes. PDF/OCR/image evidence remains proposal-only unless a later replay-bound parser/renderer/OCR toolchain is specified.

It resolves the manual `BUILD_1_PLAN_NOT_READY` review with these owner-direction decisions:

1. Build 1 does not add any Build 0 retry/upsert semantic. Bridge retry uses request-stable read-reconciliation by caller-supplied Build 0 IDs; duplicate Build 0 writes remain integrity failures.
2. `EvidenceScopeV1` is published as a governed Build 1 scope record and enters Build 0 only as a frozen-schema `GovernedRef` through `BoundDecisionContext.evidence_scope_ref`.
3. Numeric proposed values bind Decimal precision, rounding, overflow, and canonical string policy before proposal hashing, validation, ratification eligibility, replay, or bridge assembly.
4. Active-value resolution binds a governed resolver policy version and `active_value_state_hash`.
5. Build 0 snapshots receive governed proposal-version refs, content hashes, target keys, typed canonical values, and `ProposalEvidenceV1` locator refs. They do not receive bare typed values.
6. Unvalidated observation prose remains outside the frozen Build 0 structured advisory payload.
7. Every Build 1 governed record binds the applicable `CanonicalizationPolicy`; no application default supplies timestamp, Decimal, governed-ref, context-key, or hash canonicalization.

It resolves the manual v0.5 reviews from Gemini, Fran, Grok, and Beth with these owner-direction decisions:

1. Bridge reconciliation distinguishes first adoption of an existing Build 0 run from later verification after `BUILD0_PERSISTED`; output and replay-capsule hashes are adopted only after Build 0 has produced them.
2. Unvalidated observations have zero effect on Build 0 route selection, Tier 1 eligibility, or the frozen structured advisory payload.
3. Numeric proposal policy must be identical to the Build 0 snapshot policy or re-canonicalize to byte-identical Decimal output under that policy before bridge binding.
4. Caller-provided `version_number` values are checked for strict monotonicity and uniqueness under the governed `logical_id` before publication.
5. Shared-unit-of-work bridge execution must still acquire and respect the frozen Build 0 transaction-scoped PostgreSQL advisory lock for the Build 0 writer lane.
6. Numeric validation predicate templates enforce the bound canonicalization policy on every numeric operand before truth evaluation.
7. Bridge integrity failure is namespaced as `BRIDGE_INTEGRITY_FAILURE`; test wording uses replay fixtures/canonical samples rather than overloaded vector language.

It resolves the manual v0.6 reviews with these owner-direction decisions:

1. `active_value_state_hash` has an exact `ACTIVE_VALUE_STATE_HASH_V1` canonical payload contract using RFC 8785/JCS bytes, complete `GovernedRef` objects, declared sort keys, recursive NFC normalization, bound timestamp width, and omission rules.
2. Caller-provided `version_number` failures map to one governed result class: duplicate version number is `INTEGRITY_FAILURE`; non-monotonic, out-of-range, missing, policy-free, or non-integer version numbers are `CONFIGURATION_INVALID`.
3. Overloaded replay-test wording is replaced with replay fixtures.

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
"""
    spec_end = """<!-- END GPTL_SPEC_V0.4.20 -->
---

# Embedded Build 1 Plan

<!-- BEGIN GPTL_BUILD1_PLAN_V0.7 -->
"""
    trailer = """<!-- END GPTL_BUILD1_PLAN_V0.7 -->
"""

    OUTPUT.write_text(header + spec + spec_end + plan + trailer, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
