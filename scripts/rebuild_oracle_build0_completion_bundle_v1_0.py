#!/usr/bin/env python3
"""Rebuild the final Build 0 ORACLE completion bundle from active contracts."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "GPTL_Manufacturing_Platform_v0.4.14.md"
PLAN = ROOT / "docs" / "GPTL_BUILD_PLAN_v0.15.md"
OUTPUT = ROOT / "docs" / "GPTL_ORACLE_BUILD0_COMPLETION_REVIEW_v1.0.md"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    spec = SPEC.read_text(encoding="utf-8").rstrip() + "\n"
    plan = PLAN.read_text(encoding="utf-8").rstrip() + "\n"

    header = f"""# GPTL MIE Build 0 ORACLE Completion Review Bundle
## Final Specification, Build Plan, and Acceptance Evidence — v1.0

**Governing specification:** GPTL Manufacturing Intelligence Platform v0.4.14

**Build plan and acceptance record:** GPTL MIE Build 0 Plan v0.15

**Implementation baseline commit:** `9e919df4a932e1883e1668e9fbada8cbd15e45bc`

**Spec SHA-256:** `{sha256_text(spec)}`

**Plan SHA-256:** `{sha256_text(plan)}`

---

## ORACLE Review Charter

This is the single primary document for the final MIE Build 0 completion review. The complete governing specification and build plan are embedded verbatim below. The build plan includes the executed PostgreSQL acceptance evidence. **Do not import either source as a separate rule pack and do not require a second document.**

Review whether the completed Build 0 contract is internally coherent, safety-preserving, and ready to freeze as the deterministic research baseline before Build 1 begins. This is not permission to redesign ratified architecture, claim production qualification, or expand Build 0 scope.

### Questions ORACLE Must Answer

1. Do v0.4.14 and v0.15 agree on every Build 0 invariant, output boundary, slice owner, persistence contract, and completion gate?
2. Does the acceptance record objectively close all seven slice gates, including PostgreSQL atomicity, append-only enforcement, restart/cross-process replay, tamper detection, missing-content refusal, and pack evolution?
3. Can any missing input, unresolved applicability, missing MSA, unratified value, absent evidence, unknown catalog category, or replay failure still become a false negative or material-truth conclusion?
4. Does replay reconstruct only the exact stored typed recipe and bound snapshot, with no network retrieval, implicit latest version, mutable live state, model authority, or unversioned algorithm?
5. Are every decision-affecting threshold, weight, reason, route, policy, template, lifecycle state, and algorithm identity governed rather than supplied by an application default or unexplained domain constant?
6. Do the Tier 1, Tier 2, renderer, replay-verification, and record-of-record boundaries remain disjoint and fail closed?
7. Did any Slice 7 persistence or replay addition silently change an earlier canonical output, schema, fixture expectation, or historical record?
8. Are the remaining Build 1-3 activities correctly classified as capture/integration, empirical qualification, or production controls rather than hidden Build 0 defects?

### Ratified Constraints — Not Open for Redesign

- One shared safety substrate with a closed, bounded engine set by computation type; MIE uses the Diagnostic Engine.
- No vector retrieval, embedding index, or model authority in the authoritative decision path.
- PostgreSQL only for Build 0 persistence; no SQLite or embedded-database fallback.
- No probability, posterior, generic confidence, or confidence interval in authoritative output.
- No application defaults or unexplained domain numerics in decision logic.
- MSA is a hard Tier 1 precondition and must match method, class, measurand, scope, qualification, applicability, and implemented engine support.
- Applicability is `TRUE|FALSE|UNKNOWN|INVALID`; `UNKNOWN` never excludes.
- Missing evidence remains explicit and never becomes rule-out evidence.
- Negative results are bounded-catalog statements and never assert real material behavior.
- Every Build 0 Tier 1 output is non-dispositional `RESEARCH_ONLY` and not a QMS or engineering record of record.
- Synthetic/reference fixtures and `TEST_FIXTURE` evidence cannot claim vendor, production, or qualified-lab fidelity.
- Historical records are immutable; correction, supersession, deprecation, and revocation create new state/new runs without rewriting old output.

If ORACLE believes a ratified constraint creates a contradiction, it must identify the exact conflicting sections and the minimum correction. Preference for another architecture is not a finding.

### Review Evidence Boundary

This bundle contains the normative specification and build/acceptance record, not the repository source tree. ORACLE may verify claims that are evidenced inside these documents. Any claim requiring direct source inspection must be labeled `SOURCE_AUDIT_REQUIRED` rather than inferred or treated as a demonstrated defect.

### Required Finding Format

For every finding, provide:

- Finding ID
- Severity: `BLOCKER|MAJOR|MINOR|NIT`
- Governing specification section
- Build-plan section or completion gate
- Exact contradiction, omission, unsupported claim, or unsafe ambiguity
- Concrete minimum correction that preserves ratified constraints
- Whether it blocks Build 0 freeze, Build 1 start, later qualification only, or nothing
- Whether the finding is established from this bundle or requires direct source audit

Do not report preferences, optional enhancements, production features explicitly deferred to Build 1-3, or missing real-lab qualification as Build 0 defects.

### Required Final Disposition

Return exactly one overall disposition:

- `BUILD_0_COMPLETE_READY_TO_FREEZE`
- `BUILD_0_COMPLETE_WITH_NONBLOCKING_FINDINGS`
- `BUILD_0_NOT_COMPLETE`

`BUILD_0_NOT_COMPLETE` requires at least one cited `BLOCKER` or `MAJOR` contradiction that violates a Build 0 invariant or leaves a completion gate unsupported. Lack of production lab data does not qualify because Build 0 is explicitly synthetic/reference and `RESEARCH_ONLY`.

---

# Embedded Governing Specification

<!-- BEGIN GPTL_SPEC_V0.4.14 -->
"""

    separator = """<!-- END GPTL_SPEC_V0.4.14 -->
---

# Embedded Build Plan and Acceptance Record

<!-- BEGIN GPTL_BUILD_PLAN_V0.15 -->
"""

    trailer = "<!-- END GPTL_BUILD_PLAN_V0.15 -->\n"

    OUTPUT.write_text(
        header + spec + separator + plan + trailer,
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
