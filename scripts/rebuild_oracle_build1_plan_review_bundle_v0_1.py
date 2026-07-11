#!/usr/bin/env python3
"""
Module: Oracle Build 1 Plan-Review Bundle Builder (v0.1)
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
PLAN = ROOT / "docs" / "GPTL_BUILD1_PLAN_v0.1.md"
OUTPUT = ROOT / "docs" / "GPTL_ORACLE_BUILD1_PLAN_REVIEW_v0.1.md"


def _normalized(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    spec = _normalized(SPEC)
    plan = _normalized(PLAN)

    header = f"""# GPTL MIE Build 1 ORACLE Plan Review Bundle
## Single-Document Specification and Build Plan Packet - v0.1

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.20

**Build 1 plan:** GPTL MIE Build 1 Plan v0.1

**Spec SHA-256:** `{_sha256(spec)}`

**Build 1 plan SHA-256:** `{_sha256(plan)}`

---

## ORACLE Review Charter

This is the only input document for Build 1 plan review. It embeds the complete frozen governing specification and the proposed Build 1 plan. Do not request a second document or import any section as a separate rule pack.

Build 1 is not a new architecture. It is the implementation plan for the existing v0.4.20 Build 1 scope: capability-profiled capture, source registration, evidence-grounded typed proposals, human ratification, attributed observations, designed-validation protocols, and advisory bridge into the already-frozen Build 0 deterministic engine.

Build 1 is not a production qualification effort. It must not be reviewed as if it promises SpaceX-specific integration, production LIMS coverage, vendor parser fidelity, qualified MSA, production RBAC, QMS record-of-record semantics, distributed workers, or autonomous root-cause/disposition decisions.

### Questions ORACLE Must Answer

1. Does the Build 1 plan implement v0.4.20 §§2.3-2.7, §6, §11, and §18 without contradicting the frozen Build 0 spine?
2. Does the plan preserve the ratification firewall so no proposed value, model output, missing capability, unsupported source, or unvalidated observation can enter Tier 1?
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

<!-- BEGIN GPTL_BUILD1_PLAN_V0.1 -->
"""
    trailer = """<!-- END GPTL_BUILD1_PLAN_V0.1 -->
"""

    OUTPUT.write_text(header + spec + spec_end + plan + trailer, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
