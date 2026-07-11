#!/usr/bin/env python3
"""
Module: Oracle Build 0 Closeout Bundle Builder (v1.3)
Purpose: Rebuild the single-file ORACLE Build 0 freeze-review bundle.

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
SPEC = ROOT / "docs" / "GPTL_Manufacturing_Platform_v0.4.17.md"
PLAN = ROOT / "docs" / "GPTL_BUILD_PLAN_v0.18.md"
EVIDENCE_MD = ROOT / "docs" / "evidence" / "GPTL_BUILD0_COMPLETION_EVIDENCE_v1.2.md"
EVIDENCE_JSON = ROOT / "docs" / "evidence" / "GPTL_BUILD0_COMPLETION_EVIDENCE_v1.2.json"
OUTPUT = ROOT / "docs" / "GPTL_ORACLE_BUILD0_CLOSEOUT_REVIEW_v1.3.md"


def _normalized(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    spec = _normalized(SPEC)
    plan = _normalized(PLAN)
    evidence_md = _normalized(EVIDENCE_MD)
    evidence_json = _normalized(EVIDENCE_JSON)

    header = f"""# GPTL MIE Build 0 ORACLE Freeze Closeout Bundle
## Repository Self-Audited Specification, Plan, and Executed Evidence - v1.3

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.17

**Build plan:** GPTL MIE Build 0 Plan v0.18

**Audited implementation commit:** `f2ce17932dabfea9dd8035c0edb3ab309f6945c3`

**Evidence commit:** `038154062ad17980d06f7c494b30c76b18b78625`

**Spec SHA-256:** `{_sha256(spec)}`

**Plan SHA-256:** `{_sha256(plan)}`

**Evidence Markdown SHA-256:** `{_sha256(evidence_md)}`

**Evidence JSON SHA-256:** `{_sha256(evidence_json)}`

---

## ORACLE Closeout Charter

This is the only input document for the final MIE Build 0 freeze review. It embeds the complete governing specification, build plan, human-readable executed evidence, and machine-readable evidence record. Do not request a second document or import any section as a separate rule pack.

The prior ORACLE sessions did not reject the architecture. Session `20260622-233237` found final evidence-contract gaps. This bundle resolves them as follows:

1. Timestamp width is mandatory bound `CanonicalizationPolicy` input on preflight, snapshot, persistence, and replay paths. Every lexical comparison domain validates one width; no global or application default was introduced.
2. Authoritative identifiers are typed caller inputs retained in the exact replay recipe. The engine does not generate identity.
3. Calibration, refusal, replay-recipe, and replay-result contracts now state the exact implemented closed schemas. An unavailable calibration still cites its explicit immutable calibration record.
4. One run persists exactly one `Tier1Output` or `Tier2Output`. Tier 2 deterministically reproduces the Tier 1 eligibility attempt but does not invent an implicit paired refusal transaction.
5. Replay byte surfaces, ordering, metadata validation, and success/failure result boundaries are explicit.
6. Canonical sample bytes are emitted under CPython 3.10, 3.11, and 3.12 and compared directly; all three produce SHA-256 `b4db3ed4d3ebedfc275c505d4abeb1279c38df850c0eeb0dedc9b26b7f1eba51`.
7. All 28 requirement-ownership rows and all 13 completion criteria have explicit evidence coverage.
8. Published validation-input schemas are distinct from canonical-wire schemas; wire Decimal branches are string-only and semantic invariants are explicit.
9. `diagnostic_state_hash` has an exact RFC 8785 byte-input contract and a regression test.
10. The complete 297-test suite passes on every supported Python minor.
11. The bundle is honestly labeled repository self-audited; it claims no external attestation.

Review the revised contract and the evidence as a freeze closeout, not as permission to redesign ratified architecture or demand production qualification. Production method packs, real-lab MSA, vendor adapters, cryptographic production governance, distributed performance, and SpaceX-specific integration remain Build 1-3 or qualification work and are not Build 0 defects.

### Questions ORACLE Must Answer

1. Do v0.4.17 and v0.18 now state one coherent contract matching the source-audited boundaries above?
2. Does the evidence record bind the exact source commit, governing-document hashes, test inventory, gate mappings, executed command results, canonical artifacts, closed schemas, source files, and migrations without narrative-only assertions?
3. Are PostgreSQL atomicity, append-only enforcement, restart/cross-process replay, tamper/missing-content refusal, and pack lifecycle evolution each supported by exact named passing tests?
4. Does any remaining bundle-established contradiction permit missing or ambiguous evidence to become a false negative, material-truth conclusion, silent default, or unreconstructable decision?
5. Is any remaining issue genuinely Build 0 release-blocking rather than deferred production integration, qualification, performance, or security work?

### Evidence Rules

- A finding must cite the exact specification section, plan gate, and evidence/test item that conflict.
- Source behavior established by the source-audited evidence must not be replaced with a preferred architecture.
- Do not treat lack of real SpaceX equipment, LIMS schemas, vendor files, production MSA, or lab qualification as a Build 0 defect; Build 0 is explicitly synthetic/reference and `RESEARCH_ONLY`.
- If direct repository inspection beyond the embedded source/schema/migration digests is still desired, label it `OPTIONAL_SOURCE_CONFIRMATION`; do not call the existing executed evidence absent.
- Rejected prior proposals remain out of scope: magic constants, uncertainty bands, weakened replay integrity, vector/model authority, arbitrary performance gates, and Build 3 cryptography.

### Required Finding Format

For every finding provide: finding ID; severity `BLOCKER|MAJOR|MINOR|NIT`; exact specification section; exact plan/evidence reference; contradiction or unsupported claim; minimum correction preserving ratified constraints; freeze impact; and whether it is established from this bundle.

Do not report preferences, optional enhancements, or explicitly deferred work as defects.

### Required Final Disposition

Return exactly one:

- `BUILD_0_COMPLETE_READY_TO_FREEZE`
- `BUILD_0_COMPLETE_WITH_NONBLOCKING_FINDINGS`
- `BUILD_0_NOT_COMPLETE`

`BUILD_0_NOT_COMPLETE` requires at least one bundle-established `BLOCKER` or `MAJOR` contradiction that violates a Build 0 invariant or leaves a completion gate unsupported.

---

# Embedded Governing Specification

<!-- BEGIN GPTL_SPEC_V0.4.17 -->
"""
    spec_end = """<!-- END GPTL_SPEC_V0.4.17 -->
---

# Embedded Build Plan

<!-- BEGIN GPTL_BUILD_PLAN_V0.18 -->
"""
    plan_end = """<!-- END GPTL_BUILD_PLAN_V0.18 -->
---

# Embedded Human-Readable Completion Evidence

<!-- BEGIN GPTL_BUILD0_EVIDENCE_MD_V1.2 -->
"""
    evidence_md_end = """<!-- END GPTL_BUILD0_EVIDENCE_MD_V1.2 -->
---

# Embedded Machine-Readable Completion Evidence

<!-- BEGIN GPTL_BUILD0_EVIDENCE_JSON_V1.2 -->

```json
"""
    trailer = """```

<!-- END GPTL_BUILD0_EVIDENCE_JSON_V1.2 -->
"""

    OUTPUT.write_text(
        header
        + spec
        + spec_end
        + plan
        + plan_end
        + evidence_md
        + evidence_md_end
        + evidence_json
        + trailer,
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
