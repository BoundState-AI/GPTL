from __future__ import annotations

import copy
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[2]
evidence = SimpleNamespace(
    **runpy.run_path(str(ROOT / "scripts" / "generate_build0_completion_evidence_v1_4.py"))
)
PRIOR_EVIDENCE = ROOT / "docs" / "evidence" / "GPTL_BUILD0_COMPLETION_EVIDENCE_v1.3.json"


def _criterion_test_ids() -> list[str]:
    return [
        f"tests/conformance/test_completion_evidence.py::{name}"
        for name in (
            "test_gate_map_selectors_and_markdown_anchors_resolve",
            "test_ready_disposition_is_derived_from_self_audit_evidence",
            "test_ready_disposition_rejects_failed_or_incomplete_evidence",
            "test_replay_schema_artifacts_publish_nested_definitions",
            "test_replay_capsule_wrapper_schema_is_published",
            "test_generator_identity_is_self_checked",
            "test_canonical_wire_schemas_reject_numeric_decimals",
            "test_canonical_wire_schemas_publish_canonical_decimal_semantics",
            "test_requirement_coverage_includes_every_matrix_row_and_criterion",
            "test_cross_minor_divergence_blocks_ready_disposition",
            "test_package_and_evidence_support_matrices_agree",
        )
    ]


def _valid_disposition_input() -> dict[str, object]:
    commands = [
        {
            "command": ["uv", "run", "--python", minor, "pytest", "-q"],
            "exit_code": 0,
        }
        for minor in evidence.SUPPORTED_PYTHON_MINORS
    ]
    schemas = [
        {
            "model": f"gptl.mie.replay.Recipe{index}ReplayRecipe",
            "canonical_wire_schema": {"$defs": {"NestedRuntime": {"type": "object"}}},
            "semantic_invariants": ["extra fields prohibited"],
        }
        for index in range(6)
    ]
    schemas.append(
        {
            "model": "gptl.core.persistence.ReplayCapsuleRecord",
            "canonical_wire_schema": {"type": "object"},
            "semantic_invariants": ["payload_hash equals canonical recipe bytes"],
        }
    )
    return {
        "governing_documents": {
            "generator_path": "scripts/generate_build0_completion_evidence_v1_4.py"
        },
        "command_results": commands,
        "gates": [
            {
                "gate_id": "COMPLETION_13_EVIDENCE_MANIFEST",
                "exact_test_node_ids": _criterion_test_ids(),
                "source_refs": ["scripts/generate_build0_completion_evidence_v1_4.py"],
            }
        ],
        "schema_artifacts": schemas,
        "requirement_coverage": {
            "requirement_rows": [{"requirement": "covered"}],
            "completion_criteria": [{"criterion": number} for number in range(1, 14)],
        },
        "cross_minor_canonical_artifacts": {"identical": True},
    }


def test_gate_map_selectors_and_markdown_anchors_resolve() -> None:
    prior = json.loads(PRIOR_EVIDENCE.read_text(encoding="utf-8"))
    node_ids = sorted({*prior["test_inventory"]["exact_node_ids"], *_criterion_test_ids()})

    _, gates = evidence._expand_gate_map(node_ids)

    assert gates
    assert all(gate["exact_test_node_ids"] for gate in gates)


def test_ready_disposition_is_derived_from_self_audit_evidence() -> None:
    assert evidence._derive_disposition(_valid_disposition_input()) == (
        "BUILD_0_COMPLETE_READY_TO_FREEZE"
    )


def test_ready_disposition_rejects_failed_or_incomplete_evidence() -> None:
    failed = _valid_disposition_input()
    failed["command_results"][0]["exit_code"] = 1  # type: ignore[index]
    with pytest.raises(RuntimeError, match="command failed"):
        evidence._derive_disposition(failed)

    missing_minor = _valid_disposition_input()
    missing_minor["command_results"] = missing_minor["command_results"][:-1]  # type: ignore[index]
    with pytest.raises(RuntimeError, match="lacks a full-suite gate"):
        evidence._derive_disposition(missing_minor)

    unrelated = _valid_disposition_input()
    unrelated["gates"][0]["exact_test_node_ids"] = ["tests/conformance/test_schema.py::test_x"]  # type: ignore[index]
    with pytest.raises(RuntimeError, match="unrelated tests"):
        evidence._derive_disposition(unrelated)

    missing_schema = copy.deepcopy(_valid_disposition_input())
    missing_schema["schema_artifacts"][0]["canonical_wire_schema"] = {}  # type: ignore[index]
    with pytest.raises(RuntimeError, match="nested replay schemas"):
        evidence._derive_disposition(missing_schema)


def test_replay_schema_artifacts_publish_nested_definitions() -> None:
    artifacts = [
        item for item in evidence._schema_artifacts() if item["model"].endswith("ReplayRecipe")
    ]

    assert len(artifacts) == 6
    assert all(item["canonical_wire_schema"].get("$defs") for item in artifacts)
    serialized = json.dumps(artifacts, sort_keys=True)
    for nested_model in (
        "SafeRefusalRequest",
        "Slice2Request",
        "Slice6Runtime",
        "AdvisoryQuery",
    ):
        assert nested_model in serialized


def test_replay_capsule_wrapper_schema_is_published() -> None:
    artifacts = evidence._schema_artifacts()
    wrapper = next(
        item for item in artifacts if item["model"] == "gptl.core.persistence.ReplayCapsuleRecord"
    )
    serialized = json.dumps(wrapper, sort_keys=True)

    for field in (
        "run_id",
        "algorithm_id",
        "recipe_schema_version",
        "replay_policy_ref",
        "payload_hash",
        "record_type",
        "schema_version",
        "hash_algorithm",
    ):
        assert field in serialized
    assert any("payload_hash" in invariant for invariant in wrapper["semantic_invariants"])

    missing_wrapper = _valid_disposition_input()
    missing_wrapper["schema_artifacts"] = [  # type: ignore[index]
        item
        for item in missing_wrapper["schema_artifacts"]  # type: ignore[union-attr]
        if item["model"] != "gptl.core.persistence.ReplayCapsuleRecord"
    ]
    with pytest.raises(RuntimeError, match="replay capsule wrapper schema is missing"):
        evidence._derive_disposition(missing_wrapper)


def test_generator_identity_is_self_checked() -> None:
    prior = json.loads(PRIOR_EVIDENCE.read_text(encoding="utf-8"))
    node_ids = sorted({*prior["test_inventory"]["exact_node_ids"], *_criterion_test_ids()})
    _, gates = evidence._expand_gate_map(node_ids)
    completion_gate = next(
        gate for gate in gates if gate["gate_id"] == "COMPLETION_13_EVIDENCE_MANIFEST"
    )

    assert completion_gate["source_refs"] == [
        "scripts/generate_build0_completion_evidence_v1_4.py",
        "docs/evidence/BUILD0_GATE_MAP_v1.4.json",
    ]

    stale = _valid_disposition_input()
    stale["gates"][0]["source_refs"] = [  # type: ignore[index]
        "scripts/generate_build0_completion_evidence_v1_3.py"
    ]
    with pytest.raises(RuntimeError, match="stale generator identity"):
        evidence._derive_disposition(stale)


def test_canonical_wire_schemas_reject_numeric_decimals() -> None:
    artifacts = evidence._schema_artifacts()

    assert all(
        not evidence._schema_contains_numeric_decimal(item["canonical_wire_schema"])
        for item in artifacts
    )
    validation_text = json.dumps(artifacts, sort_keys=True)
    assert '"type": "number"' in validation_text


def test_canonical_wire_schemas_publish_canonical_decimal_semantics() -> None:
    artifacts = evidence._schema_artifacts()

    assert any(
        evidence._schema_contains_canonical_decimal(item["canonical_wire_schema"])
        and any("canonical_decimal" in invariant for invariant in item["semantic_invariants"])
        for item in artifacts
    )
    assert all(
        not evidence._schema_contains_pydantic_decimal_pattern(item["canonical_wire_schema"])
        for item in artifacts
    )

    invalid = _valid_disposition_input()
    invalid["schema_artifacts"].append(  # type: ignore[union-attr]
        {
            "model": "gptl.test.DecimalWire",
            "canonical_wire_schema": {
                "type": "string",
                "pattern": evidence.PYDANTIC_DECIMAL_PATTERN,
            },
            "semantic_invariants": ["extra fields prohibited"],
        }
    )
    with pytest.raises(RuntimeError, match="validation Decimal regex"):
        evidence._derive_disposition(invalid)

    missing_invariant = _valid_disposition_input()
    missing_invariant["schema_artifacts"].append(  # type: ignore[union-attr]
        {
            "model": "gptl.test.DecimalWire",
            "canonical_wire_schema": {
                "type": "string",
                "pattern": evidence.CANONICAL_DECIMAL_PATTERN,
            },
            "semantic_invariants": ["extra fields prohibited"],
        }
    )
    with pytest.raises(RuntimeError, match="canonical Decimal semantic invariants"):
        evidence._derive_disposition(missing_invariant)


def test_requirement_coverage_includes_every_matrix_row_and_criterion() -> None:
    prior = json.loads(PRIOR_EVIDENCE.read_text(encoding="utf-8"))
    node_ids = sorted({*prior["test_inventory"]["exact_node_ids"], *_criterion_test_ids()})
    _, gates = evidence._expand_gate_map(node_ids)

    coverage = evidence._requirement_coverage(gates)

    assert len(coverage["requirement_rows"]) == 28
    assert [item["criterion"] for item in coverage["completion_criteria"]] == list(range(1, 14))
    assert all(item["exact_test_node_ids"] for item in coverage["requirement_rows"])


def test_cross_minor_divergence_blocks_ready_disposition() -> None:
    divergent = _valid_disposition_input()
    divergent["cross_minor_canonical_artifacts"] = {"identical": False}

    with pytest.raises(RuntimeError, match="cross-minor canonical artifacts differ"):
        evidence._derive_disposition(divergent)


def test_package_and_evidence_support_matrices_agree() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    commands = [" ".join(command) for command in evidence._commands()]

    assert 'requires-python = ">=3.10,<3.13"' in project
    assert evidence.SUPPORTED_PYTHON_MINORS == ("3.10", "3.11", "3.12")
    for minor in evidence.SUPPORTED_PYTHON_MINORS:
        assert any(
            f"--python {minor}" in command and command.endswith("pytest -q") for command in commands
        )
