#!/usr/bin/env python3
"""
Module: Oracle Review Bundle Builder (v0.1)
Purpose: Rebuild the immutable v0.1 ORACLE review bundle from its historical inputs.

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
SPEC = ROOT / "docs" / "GPTL_Manufacturing_Platform_v0.4.4.md"
PLAN = ROOT / "docs" / "GPTL_BUILD_PLAN_v0.1.md"
OUTPUT = ROOT / "docs" / "GPTL_ORACLE_BUILD_REVIEW_v0.1.md"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    spec = SPEC.read_text(encoding="utf-8").rstrip() + "\n"
    plan = PLAN.read_text(encoding="utf-8").rstrip() + "\n"

    header = f"""# GPTL MIE Build 0 ORACLE Review Bundle
## Specification-to-Build Review — v0.1

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.4

**Build plan:** GPTL MIE Build 0 Plan v0.1

**Spec SHA-256:** `{sha256_text(spec)}`

**Plan SHA-256:** `{sha256_text(plan)}`

---

## ORACLE Review Charter

This is a single-document review bundle because ORACLE accepts one primary document per review. The complete governing specification and build plan are embedded verbatim below. **No rule pack is required or desired for this review.**

Review the mapping from the ratified specification to the proposed implementation slices. Do not perform another general product rewrite.

### Questions ORACLE Must Answer

1. Does every MIE Build 0 requirement have exactly one primary implementation slice?
2. Are the slices ordered so each depends only on capabilities established by an earlier slice or explicitly introduced in that slice?
3. Does every slice have objective, machine-testable exit criteria and explicit failure/stop conditions?
4. Does any slice introduce a decision rule, threshold, default, data assumption, or authority not present in v0.4.4?
5. Can any missing input, unresolved applicability result, low-information score, or unavailable record still become a false negative conclusion?
6. Does the plan preserve deterministic replay, evidence citation, MSA gating, non-disposition, and the `RESEARCH_ONLY` boundary end to end?
7. Are synthetic/reference fixtures kept separate from vendor-specific ingestion and production qualification?
8. Is any requirement assigned too late to protect an earlier slice?

### Ratified Constraints — Not Open for Redesign

- One shared safety substrate with a closed, bounded engine set by computation type.
- MIE uses the Diagnostic Engine.
- No vector retrieval or model authority in the decision path.
- MSA is a hard Tier 1 precondition.
- Applicability is `TRUE|FALSE|UNKNOWN|INVALID`; `UNKNOWN` never excludes.
- Missing evidence produces `OPEN_UNASSESSED`, never rule-out evidence.
- All Build 0 Tier 1 outputs are non-dispositional `RESEARCH_ONLY` artifacts.
- Build 0 uses typed synthetic/reference fixtures; vendor adapters and production qualification are later work.
- Synthetic MSA/data are isolated to a governed `TEST_FIXTURE` evidence scope and cannot satisfy non-test runs.

If ORACLE believes a ratified constraint creates an implementation contradiction, it may report the exact contradiction with cited sections. Preference for another architecture is not a defect.

### Required Finding Format

For every finding, provide:

- Severity: `CRITICAL|HIGH|MEDIUM|LOW`
- Governing specification section
- Build-plan section/slice
- Exact contradiction, omission, or unsafe sequence
- Concrete correction that does not reopen a ratified constraint
- Whether the finding blocks Slice 1, a later named slice, or Build 0 completion only

### Required Final Disposition

Return exactly one overall disposition:

- `READY_TO_BUILD_SLICE_1`
- `READY_WITH_NONBLOCKING_FINDINGS`
- `BLOCKED_BY_SPEC_PLAN_CONTRADICTION`

`BLOCKED_BY_SPEC_PLAN_CONTRADICTION` requires at least one cited critical/high defect that makes the proposed implementation unsafe or non-deterministic. Lack of production lab data is not a Build 0 blocker because Build 0 is explicitly synthetic/reference and `RESEARCH_ONLY`.

---

# Embedded Governing Specification

<!-- BEGIN GPTL_SPEC_V0.4.4 -->
"""

    separator = """<!-- END GPTL_SPEC_V0.4.4 -->
---

# Embedded Build Plan

<!-- BEGIN GPTL_BUILD_PLAN_V0.1 -->
"""

    trailer = "<!-- END GPTL_BUILD_PLAN_V0.1 -->\n"

    OUTPUT.write_text(
        header + spec + separator + plan + trailer,
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
