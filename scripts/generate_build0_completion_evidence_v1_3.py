#!/usr/bin/env python3
"""
Module: Build 0 Completion Evidence Generator (v1.3)
Purpose: Execute and record the source-audited MIE Build 0 completion gates.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from gptl.core.audit import PreflightRefusalAuditEvent, SnapshotDecisionAuditEvent
from gptl.core.canonical import canonical_bytes
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import CanonicalizationPolicy
from gptl.core.snapshot import KnowledgeSnapshot, snapshot_hash
from gptl.mie.calibration import CalibrationEvaluation
from gptl.mie.replay import (
    ArtifactConfirmationReplayRecipe,
    CandidatePreservationReplayRecipe,
    HonestNegativeReplayRecipe,
    MSAGateReplayRecipe,
    ReplayIntegrityFailure,
    ReplayPolicy,
    ReplayVerified,
    SafeRefusalReplayRecipe,
    Tier2AdvisoryReplayRecipe,
    _execute_recipe,
)
from gptl.mie.schema import RefusalDecision, Tier1Output, Tier2Output
from gptl.slice7_fixture import replay_policy, replay_recipes

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "GPTL_Manufacturing_Platform_v0.4.18.md"
PLAN = ROOT / "docs" / "GPTL_BUILD_PLAN_v0.19.md"
GATE_MAP = ROOT / "docs" / "evidence" / "BUILD0_GATE_MAP_v1.3.json"
JSON_OUTPUT = ROOT / "docs" / "evidence" / "GPTL_BUILD0_COMPLETION_EVIDENCE_v1.3.json"
MARKDOWN_OUTPUT = ROOT / "docs" / "evidence" / "GPTL_BUILD0_COMPLETION_EVIDENCE_v1.3.md"
SUPPORTED_PYTHON_MINORS = ("3.10", "3.11", "3.12")
SUPPORTED_PLATFORM = "Linux-x86_64"
SUPPORTED_POSTGRESQL_MAJOR = "14"
PYDANTIC_DECIMAL_PATTERN = r"^(?!^[-+.]*$)[+-]?0*\d*\.?\d*$"
CANONICAL_DECIMAL_PATTERN = r"^(?:0|[1-9][0-9]*|-(?:[1-9][0-9]*))(?:\.[0-9]+)?$"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256(path.read_bytes())


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "0"},
        check=False,
    )
    output = _normalize_command_output(completed.stdout + completed.stderr)
    result = {
        "command": _normalize_command(command),
        "exit_code": completed.returncode,
        "output": output,
        "output_sha256": _sha256(output.encode("utf-8")),
    }
    if completed.returncode != 0:
        raise RuntimeError(json.dumps(result, indent=2))
    return result


def _normalize_command_output(value: str) -> str:
    normalized = value.replace(str(ROOT), "<REPOSITORY_ROOT>")
    normalized = re.sub(r"\bin \d+(?:\.\d+)?(?:ms|s)\b", "in <elapsed>", normalized)
    return normalized.rstrip() + "\n"


def _normalize_command(command: list[str]) -> list[str]:
    executable_names = {
        str(Path(sys.executable).resolve()): "python",
    }
    for name in ("uv", "pg_config"):
        executable = shutil.which(name)
        if executable is not None:
            executable_names[str(Path(executable).resolve())] = name
    normalized = []
    for argument in command:
        resolved = str(Path(argument).resolve()) if Path(argument).is_absolute() else argument
        normalized.append(
            executable_names.get(resolved, argument.replace(str(ROOT), "<REPOSITORY_ROOT>"))
        )
    return normalized


def _git_value(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _require_clean_baseline() -> None:
    allowed = {
        str(JSON_OUTPUT.relative_to(ROOT)),
        str(MARKDOWN_OUTPUT.relative_to(ROOT)),
    }
    status = _git_value("status", "--porcelain", "--untracked-files=all")
    unexpected = []
    for line in status.splitlines():
        path = line[3:]
        if path not in allowed:
            unexpected.append(line)
    if unexpected:
        raise RuntimeError("evidence requires a clean baseline:\n" + "\n".join(unexpected))


def _collect_tests() -> tuple[list[str], dict[str, Any]]:
    result = _run([sys.executable, "-m", "pytest", "--collect-only", "-q"])
    node_ids = sorted(
        line for line in result["output"].splitlines() if line.startswith("tests/") and "::" in line
    )
    if not node_ids:
        raise RuntimeError("pytest collection produced no exact test node IDs")
    return node_ids, result


def _expand_gate_map(node_ids: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gate_map = json.loads(GATE_MAP.read_text(encoding="utf-8"))
    if gate_map.get("schema_version") != "gptl.build0-gate-map.v1.3":
        raise RuntimeError("unsupported Build 0 gate-map schema")
    gates = gate_map.get("gates")
    if not isinstance(gates, list) or not gates:
        raise RuntimeError("Build 0 gate map has no gates")
    expanded: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for gate in gates:
        gate_id = gate["gate_id"]
        if gate_id in seen_ids:
            raise RuntimeError(f"duplicate gate ID: {gate_id}")
        seen_ids.add(gate_id)
        selectors = gate["test_selectors"]
        matches = sorted(
            {
                node_id
                for selector in selectors
                for node_id in node_ids
                if fnmatch.fnmatchcase(node_id, selector)
            }
        )
        if not matches:
            raise RuntimeError(f"gate selector matched no tests: {gate_id}")
        for source_ref in gate["source_refs"]:
            path_text, _, anchor = source_ref.partition("#")
            source_path = ROOT / path_text
            if not source_path.exists():
                raise RuntimeError(f"gate source does not exist: {source_ref}")
            if anchor and anchor not in _heading_anchors(source_path):
                raise RuntimeError(f"gate source anchor does not exist: {source_ref}")
        expanded.append(
            {**gate, "matched_test_count": len(matches), "exact_test_node_ids": matches}
        )
    return gate_map, expanded


def _heading_anchors(path: Path) -> set[str]:
    anchors = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip().lower()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        anchors.add(slug)
    return anchors


def _schema_artifact(model: type[BaseModel]) -> dict[str, Any]:
    validation_schema = model.model_json_schema()
    wire_schema = _canonical_wire_schema(validation_schema)
    validation_payload = json.dumps(
        validation_schema,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    wire_payload = json.dumps(
        wire_schema,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    model_name = f"{model.__module__}.{model.__name__}"
    return {
        "model": model_name,
        "validation_input_schema_sha256": _sha256(validation_payload),
        "validation_input_schema": validation_schema,
        "canonical_wire_schema_sha256": _sha256(wire_payload),
        "canonical_wire_schema": wire_schema,
        "semantic_invariants": _semantic_invariants(model_name, wire_schema),
    }


def _canonical_wire_schema(schema: dict[str, Any]) -> dict[str, Any]:
    wire = copy.deepcopy(schema)

    def rewrite(value: Any) -> None:
        if isinstance(value, dict):
            branches = value.get("anyOf")
            if isinstance(branches, list):
                string_branches = [
                    branch
                    for branch in branches
                    if isinstance(branch, dict)
                    and branch.get("type") == "string"
                    and "pattern" in branch
                ]
                if string_branches and any(
                    isinstance(branch, dict) and branch.get("type") == "number"
                    for branch in branches
                ):
                    canonical_string_branches = [
                        {
                            **branch,
                            "pattern": CANONICAL_DECIMAL_PATTERN,
                            "description": (
                                "Canonical Decimal wire string; exact scale and overflow "
                                "are enforced by the bound CanonicalizationPolicy."
                            ),
                        }
                        for branch in string_branches
                    ]
                    null_branches = [
                        branch
                        for branch in branches
                        if isinstance(branch, dict) and branch.get("type") == "null"
                    ]
                    value["anyOf"] = [*canonical_string_branches, *null_branches]
            for child in value.values():
                rewrite(child)
        elif isinstance(value, list):
            for child in value:
                rewrite(child)

    rewrite(wire)
    return wire


def _schema_contains_canonical_decimal(schema: Any) -> bool:
    if isinstance(schema, dict):
        if schema.get("pattern") == CANONICAL_DECIMAL_PATTERN:
            return True
        return any(_schema_contains_canonical_decimal(value) for value in schema.values())
    if isinstance(schema, list):
        return any(_schema_contains_canonical_decimal(value) for value in schema)
    return False


def _schema_contains_pydantic_decimal_pattern(schema: Any) -> bool:
    if isinstance(schema, dict):
        if schema.get("pattern") == PYDANTIC_DECIMAL_PATTERN:
            return True
        return any(_schema_contains_pydantic_decimal_pattern(value) for value in schema.values())
    if isinstance(schema, list):
        return any(_schema_contains_pydantic_decimal_pattern(value) for value in schema)
    return False


def _semantic_invariants(model_name: str, wire_schema: dict[str, Any]) -> list[str]:
    common = ["extra fields prohibited; model immutable after validation"]
    if _schema_contains_canonical_decimal(wire_schema):
        common.append(
            "Decimal wire strings are generated only by canonical_decimal(value, "
            "bound CanonicalizationPolicy); exact scale, unsigned zero, no exponent, "
            "and overflow rejection are semantic invariants beyond JSON Schema"
        )
    specific = {
        "gptl.mie.calibration.CalibrationEvaluation": [
            "evidence_refs nonempty, unique, sorted, and contains calibration_ref and policy_ref"
        ],
        "gptl.mie.replay.ReplayVerified": [
            "snapshot_hash is present iff bound_version_refs is nonempty",
            "bound_version_refs unique and sorted by complete governed reference",
        ],
        "gptl.mie.schema.Tier1Output": [
            "decision_hash equals SHA-256 of canonical decision bytes only"
        ],
        "gptl.mie.schema.Tier2Output": [
            "advisory_hash equals SHA-256 of canonical advisory bytes only"
        ],
    }
    return [*common, *specific.get(model_name, [])]


def _schema_artifacts() -> list[dict[str, Any]]:
    models: tuple[type[BaseModel], ...] = (
        CanonicalizationPolicy,
        GovernedRef,
        CalibrationEvaluation,
        RefusalDecision,
        Tier1Output,
        Tier2Output,
        KnowledgeSnapshot,
        PreflightRefusalAuditEvent,
        SnapshotDecisionAuditEvent,
        ReplayPolicy,
        SafeRefusalReplayRecipe,
        CandidatePreservationReplayRecipe,
        MSAGateReplayRecipe,
        ArtifactConfirmationReplayRecipe,
        HonestNegativeReplayRecipe,
        Tier2AdvisoryReplayRecipe,
        ReplayVerified,
        ReplayIntegrityFailure,
    )
    return [_schema_artifact(model) for model in models]


def _canonical_samples() -> list[dict[str, Any]]:
    policy = replay_policy().canonicalization_policy
    samples = []
    for recipe in replay_recipes():
        execution = _execute_recipe(recipe)
        output_bytes = canonical_bytes(execution.output, policy)
        body = (
            execution.output.decision
            if isinstance(execution.output, Tier1Output)
            else execution.output.advisory
        )
        sample = {
            "recipe_kind": recipe.recipe_kind,
            "run_id": recipe.request.run_id,
            "output_kind": execution.output.output_kind,
            "output_payload_sha256": _sha256(output_bytes),
            "decision_or_advisory_hash": (
                execution.output.decision_hash
                if isinstance(execution.output, Tier1Output)
                else execution.output.advisory_hash
            ),
            "snapshot_sha256": (
                snapshot_hash(execution.snapshot, policy)
                if execution.snapshot is not None
                else None
            ),
            "audit_payload_sha256": [
                _sha256(canonical_bytes(item, policy)) for item in execution.audit_events
            ],
            "citation_payload_sha256": sorted(
                _sha256(canonical_bytes(item, policy)) for item in body.citations
            ),
            "bound_version_payload_sha256": sorted(
                _sha256(canonical_bytes(item, policy)) for item in execution.bound_versions
            ),
        }
        samples.append(sample)
    return samples


def _tree_evidence(root: Path, pattern: str) -> dict[str, Any]:
    rows = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": _file_sha256(path),
        }
        for path in sorted(root.rglob(pattern))
        if path.is_file()
    ]
    payload = "".join(f"{row['path']}\0{row['sha256']}\n" for row in rows).encode("utf-8")
    return {"aggregate_sha256": _sha256(payload), "files": rows}


def _commands() -> list[list[str]]:
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required for Build 0 completion evidence")
    commands = [
        [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"],
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts"],
        [sys.executable, "-m", "mypy", "src"],
        [uv, "build"],
    ]
    commands.extend(
        [
            uv,
            "run",
            "--isolated",
            "--python",
            minor,
            "--group",
            "dev",
            "pytest",
            "-q",
        ]
        for minor in SUPPORTED_PYTHON_MINORS
    )
    return commands


def _environment() -> dict[str, str]:
    pg_config = shutil.which("pg_config")
    if pg_config is None:
        raise RuntimeError("pg_config is required for PostgreSQL evidence")
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "postgresql": _run([pg_config, "--version"])["output"].strip(),
        "uv": _run(["uv", "--version"])["output"].strip(),
    }


def _requirement_coverage(gates: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {gate["gate_id"]: gate for gate in gates}
    plan_lines = PLAN.read_text(encoding="utf-8").splitlines()
    requirements = []
    in_matrix = False
    for line in plan_lines:
        if line == "## 12. Requirement Ownership Matrix":
            in_matrix = True
            continue
        if in_matrix and line.startswith("## "):
            break
        if not in_matrix or not line.startswith("|") or line.startswith("|---"):
            continue
        columns = [item.strip() for item in line.strip("|").split("|")]
        if columns[0] == "Requirement" or len(columns) != 3 or not columns[1].isdigit():
            continue
        slice_number = columns[1]
        gate = next(
            item for gate_id, item in by_id.items() if gate_id.startswith(f"SLICE_{slice_number}_")
        )
        requirements.append(
            {
                "requirement": columns[0],
                "primary_slice": int(slice_number),
                "governing_spec": columns[2],
                "evidence_gate_id": gate["gate_id"],
                "exact_test_node_ids": gate["exact_test_node_ids"],
            }
        )
    criteria = []
    in_completion = False
    for line in plan_lines:
        if line == "## 13. Build 0 Completion Gate":
            in_completion = True
            continue
        if in_completion and line.startswith("## "):
            break
        match = re.match(r"^(\d+)\. (.+)$", line) if in_completion else None
        if match:
            number = int(match.group(1))
            gate = by_id[
                f"COMPLETION_{number}_"
                + next(
                    gate_id.split(f"COMPLETION_{number}_", 1)[1]
                    for gate_id in by_id
                    if gate_id.startswith(f"COMPLETION_{number}_")
                )
            ]
            criteria.append(
                {
                    "criterion": number,
                    "text": match.group(2),
                    "evidence_gate_id": gate["gate_id"],
                    "exact_test_node_ids": gate["exact_test_node_ids"],
                }
            )
    return {"requirement_rows": requirements, "completion_criteria": criteria}


def _cross_minor_artifacts(uv: str) -> dict[str, Any]:
    outputs = {}
    script = str(Path(__file__).resolve().relative_to(ROOT))
    for minor in SUPPORTED_PYTHON_MINORS:
        command = [
            uv,
            "run",
            "--isolated",
            "--python",
            minor,
            "--group",
            "dev",
            "python",
            script,
            "--emit-canonical-samples",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            env={**os.environ, "PYTHONHASHSEED": "0"},
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"canonical sample emission failed for Python {minor}")
        outputs[minor] = {
            "command": _normalize_command(command),
            "exit_code": completed.returncode,
            "canonical_bytes_sha256": _sha256(completed.stdout),
            "canonical_bytes_utf8": completed.stdout.decode("utf-8").rstrip() + "\n",
            "diagnostic_output": _normalize_command_output(completed.stderr.decode("utf-8")),
        }
    payloads = {result["canonical_bytes_utf8"] for result in outputs.values()}
    if len(payloads) != 1:
        raise RuntimeError("canonical artifacts differ across supported Python minors")
    return {
        "identical": True,
        "canonical_samples_sha256": _sha256(next(iter(payloads)).encode("utf-8")),
        "minor_results": outputs,
    }


def _schema_contains_numeric_decimal(schema: Any) -> bool:
    if isinstance(schema, dict):
        branches = schema.get("anyOf")
        if isinstance(branches, list) and any(
            isinstance(branch, dict) and branch.get("type") == "string" and "pattern" in branch
            for branch in branches
        ):
            if any(
                isinstance(branch, dict) and branch.get("type") == "number" for branch in branches
            ):
                return True
        return any(_schema_contains_numeric_decimal(value) for value in schema.values())
    if isinstance(schema, list):
        return any(_schema_contains_numeric_decimal(value) for value in schema)
    return False


def _derive_disposition(evidence: dict[str, Any]) -> str:
    if any(result["exit_code"] != 0 for result in evidence["command_results"]):
        raise RuntimeError("a completion command failed")
    gates = {gate["gate_id"]: gate for gate in evidence["gates"]}
    criterion = gates.get("COMPLETION_13_EVIDENCE_MANIFEST")
    if criterion is None or not criterion["exact_test_node_ids"]:
        raise RuntimeError("criterion 13 has no independent tests")
    if any(
        not node.startswith("tests/conformance/test_completion_evidence.py::")
        for node in criterion["exact_test_node_ids"]
    ):
        raise RuntimeError("criterion 13 cites unrelated tests")
    command_lines = [" ".join(result["command"]) for result in evidence["command_results"]]
    for minor in SUPPORTED_PYTHON_MINORS:
        if not any(
            f"--python {minor}" in command and "pytest -q" in command for command in command_lines
        ):
            raise RuntimeError(f"supported Python {minor} lacks a full-suite gate")
    recipe_artifacts = [
        item for item in evidence["schema_artifacts"] if item["model"].endswith("ReplayRecipe")
    ]
    if len(recipe_artifacts) != 6 or any(
        not item["canonical_wire_schema"].get("$defs") for item in recipe_artifacts
    ):
        raise RuntimeError("nested replay schemas are incomplete")
    if any(
        _schema_contains_numeric_decimal(item["canonical_wire_schema"])
        for item in evidence["schema_artifacts"]
    ):
        raise RuntimeError("canonical wire schema accepts numeric Decimal")
    if any(
        _schema_contains_pydantic_decimal_pattern(item["canonical_wire_schema"])
        for item in evidence["schema_artifacts"]
    ):
        raise RuntimeError("canonical wire schema exposes validation Decimal regex")
    if any(not item["semantic_invariants"] for item in evidence["schema_artifacts"]):
        raise RuntimeError("schema semantic invariants are missing")
    if any(
        _schema_contains_canonical_decimal(item["canonical_wire_schema"])
        and not any("canonical_decimal" in invariant for invariant in item["semantic_invariants"])
        for item in evidence["schema_artifacts"]
    ):
        raise RuntimeError("canonical Decimal semantic invariants are missing")
    coverage = evidence["requirement_coverage"]
    if len(coverage["completion_criteria"]) != 13 or not coverage["requirement_rows"]:
        raise RuntimeError("requirement coverage is incomplete")
    if not evidence["cross_minor_canonical_artifacts"]["identical"]:
        raise RuntimeError("cross-minor canonical artifacts differ")
    return "BUILD_0_COMPLETE_READY_TO_FREEZE"


def _render_markdown(evidence: dict[str, Any]) -> str:
    lines = [
        "# GPTL MIE Build 0 Completion Evidence",
        "## Repository Self-Audit Freeze Record - v1.3",
        "",
        f"**Implementation commit:** `{evidence['implementation_commit']}`",
        "",
        f"**Git tree:** `{evidence['git_tree']}`",
        "",
        f"**Governing spec SHA-256:** `{evidence['governing_documents']['spec_sha256']}`",
        "",
        f"**Build plan SHA-256:** `{evidence['governing_documents']['plan_sha256']}`",
        "",
        f"**Collected tests:** `{evidence['test_inventory']['count']}`",
        "",
        f"**Test inventory SHA-256:** `{evidence['test_inventory']['sha256']}`",
        "",
        f"**Disposition:** `{evidence['disposition']}`",
        "",
        "This disposition is derived only because every recorded command exited zero and every governed gate mapped to at least one exact collected test. It does not qualify a method, lab, instrument, or production process.",
        "",
        "## Executed Gates",
        "",
    ]
    for result in evidence["command_results"]:
        lines.extend(
            [
                f"### `{result['command_id']}`",
                "",
                f"- Command: `{' '.join(result['command'])}`",
                f"- Exit code: `{result['exit_code']}`",
                f"- Output SHA-256: `{result['output_sha256']}`",
                "- Normalized output:",
                "",
                "```text",
                result["output"].rstrip(),
                "```",
                "",
            ]
        )
    lines.extend(["## Requirement-to-Test Traceability", ""])
    for gate in evidence["gates"]:
        lines.extend(
            [
                f"### `{gate['gate_id']}`",
                "",
                gate["requirement"],
                "",
                f"Matched tests: `{gate['matched_test_count']}`",
                "",
                "Source references:",
                *[f"- `{item}`" for item in gate["source_refs"]],
                "",
                "Exact passed node IDs:",
                *[f"- `{item}`" for item in gate["exact_test_node_ids"]],
                "",
            ]
        )
    coverage = evidence["requirement_coverage"]
    cross_minor = evidence["cross_minor_canonical_artifacts"]
    lines.extend(
        [
            "## Coverage and Cross-Minor Equality",
            "",
            f"- Requirement ownership rows covered: `{len(coverage['requirement_rows'])}`",
            f"- Completion criteria covered: `{len(coverage['completion_criteria'])}`",
            f"- Cross-minor canonical fixture corpus identical: `{cross_minor['identical']}`",
            f"- Cross-minor canonical fixture corpus SHA-256: `{cross_minor['canonical_samples_sha256']}`",
            "",
            "## Canonical Artifact Samples",
            "",
        ]
    )
    for sample in evidence["canonical_samples"]:
        lines.extend(
            [
                f"### `{sample['recipe_kind']}`",
                "",
                f"- Run ID: `{sample['run_id']}`",
                f"- Output kind: `{sample['output_kind']}`",
                f"- Output payload SHA-256: `{sample['output_payload_sha256']}`",
                f"- Decision/advisory hash: `{sample['decision_or_advisory_hash']}`",
                f"- Snapshot SHA-256: `{sample['snapshot_sha256']}`",
                f"- Audit payload hashes: `{json.dumps(sample['audit_payload_sha256'])}`",
                f"- Citation payload hashes: `{json.dumps(sample['citation_payload_sha256'])}`",
                f"- Bound-version payload hashes: `{json.dumps(sample['bound_version_payload_sha256'])}`",
                "",
            ]
        )
    lines.extend(["## Closed Schema Digests", ""])
    lines.extend(
        f"- `{item['model']}` validation: `{item['validation_input_schema_sha256']}`; wire: `{item['canonical_wire_schema_sha256']}`"
        for item in evidence["schema_artifacts"]
    )
    lines.extend(
        [
            "",
            "## Source and Migration Digests",
            "",
            f"- Source tree: `{evidence['source_tree']['aggregate_sha256']}`",
            f"- Migration tree: `{evidence['migration_tree']['aggregate_sha256']}`",
            f"- Gate map: `{evidence['governing_documents']['gate_map_sha256']}`",
            f"- Generator: `{evidence['governing_documents']['generator_sha256']}`",
            "",
            "The companion JSON contains the complete per-file source and migration digest inventories.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-canonical-samples", action="store_true")
    arguments = parser.parse_args()
    if arguments.emit_canonical_samples:
        print(
            json.dumps(
                _canonical_samples(), ensure_ascii=False, separators=(",", ":"), sort_keys=True
            )
        )
        return
    _require_clean_baseline()
    node_ids, collection_result = _collect_tests()
    _, gates = _expand_gate_map(node_ids)
    command_results = []
    for index, command in enumerate(_commands(), start=1):
        result = _run(command)
        command_results.append({"command_id": f"GATE-{index:02d}", **result})
    inventory_payload = "\n".join(node_ids).encode("utf-8") + b"\n"
    evidence: dict[str, Any] = {
        "schema_version": "gptl.build0-completion-evidence.v1.3",
        "implementation_commit": _git_value("rev-parse", "HEAD"),
        "git_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "governing_documents": {
            "spec_path": str(SPEC.relative_to(ROOT)),
            "spec_sha256": _file_sha256(SPEC),
            "plan_path": str(PLAN.relative_to(ROOT)),
            "plan_sha256": _file_sha256(PLAN),
            "gate_map_path": str(GATE_MAP.relative_to(ROOT)),
            "gate_map_sha256": _file_sha256(GATE_MAP),
            "generator_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "generator_sha256": _file_sha256(Path(__file__).resolve()),
        },
        "environment": _environment(),
        "supported_execution_profile": {
            "python_minors": list(SUPPORTED_PYTHON_MINORS),
            "platform": SUPPORTED_PLATFORM,
            "postgresql_major": SUPPORTED_POSTGRESQL_MAJOR,
        },
        "test_inventory": {
            "count": len(node_ids),
            "sha256": _sha256(inventory_payload),
            "collection_command": collection_result,
            "exact_node_ids": node_ids,
        },
        "command_results": command_results,
        "gates": gates,
        "canonical_samples": _canonical_samples(),
        "schema_artifacts": _schema_artifacts(),
        "source_tree": _tree_evidence(ROOT / "src" / "gptl", "*.py"),
        "migration_tree": _tree_evidence(ROOT / "src" / "gptl" / "core" / "migrations", "*.sql"),
    }
    evidence["requirement_coverage"] = _requirement_coverage(gates)
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required for cross-minor evidence")
    evidence["cross_minor_canonical_artifacts"] = _cross_minor_artifacts(uv)
    evidence["disposition"] = _derive_disposition(evidence)
    encoded = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    JSON_OUTPUT.write_text(encoded, encoding="utf-8", newline="\n")
    MARKDOWN_OUTPUT.write_text(
        _render_markdown(evidence),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
