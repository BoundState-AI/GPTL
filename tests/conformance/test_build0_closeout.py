from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.mie.calibration import CalibrationTruth
from gptl.mie.replay import ReplayIntegrityFailure, ReplayVerified
from gptl.mie.schema import RefusalDecision, RefusalType, Tier2Output
from gptl.mie.service import SafeRefusalRequest
from gptl.mie.slice3_service import build_msa_calibration_gate
from gptl.mie.slice6_service import build_tier2_advisory
from gptl.slice1_fixture import canonicalization_policy, safe_refusal_request
from gptl.slice3_fixture import slice3_policy, slice3_request, slice3_runtime
from gptl.slice6_fixture import slice6_policy, slice6_query, slice6_request, slice6_runtime
from gptl.slice7_fixture import replay_policy, replay_recipes


def test_authoritative_identifiers_are_caller_bound_replay_inputs() -> None:
    recipe = replay_recipes()[0]
    request = recipe.request
    payload = json.loads(canonical_bytes(recipe, replay_policy().canonicalization_policy))

    for field in ("run_id", "decision_id", "case_id", "audit_event_id"):
        assert payload["request"][field] == getattr(request, field)


def test_authoritative_source_does_not_generate_identity() -> None:
    source_root = Path(__file__).parents[2] / "src" / "gptl"
    prohibited = ("uuid4(", "random.", "secrets.", "datetime.now(", "utcnow(", "time.time(")

    for path in source_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert not any(token in source for token in prohibited), path


def test_authoritative_writes_do_not_upsert_identity() -> None:
    source = (Path(__file__).parents[2] / "src" / "gptl" / "core" / "persistence.py").read_text(
        encoding="utf-8"
    )

    assert "ON CONFLICT" not in source
    assert "DO NOTHING" not in source
    assert "DO UPDATE" not in source


def test_preflight_timestamp_width_is_explicitly_policy_bound() -> None:
    request = safe_refusal_request().model_dump(mode="python")
    request["as_of_time"] = "2026-06-21T12:00:00.00Z"

    with pytest.raises(ValidationError, match="fractional precision"):
        SafeRefusalRequest.model_validate(
            request,
            context={"canonicalization_policy": canonicalization_policy()},
        )


def test_unavailable_calibration_remains_an_explicit_cited_record() -> None:
    result = build_msa_calibration_gate(
        slice3_request("closeout-unavailable"),
        slice3_runtime("UNAVAILABLE", "QUALIFIED", Decimal("0.0100"), True),
        slice3_policy(),
    )

    assert isinstance(result.output.decision, RefusalDecision)
    evaluation = result.output.decision.calibration_evaluation
    assert evaluation is not None
    assert evaluation.state == CalibrationTruth.UNAVAILABLE
    assert evaluation.calibration_ref in evaluation.evidence_refs
    assert evaluation.policy_ref in evaluation.evidence_refs


def test_tier2_execution_has_one_output_envelope() -> None:
    result = build_tier2_advisory(
        slice6_request("closeout-one-output"),
        slice6_query("MISSING_MSA"),
        slice6_runtime("MISSING_MSA"),
        slice6_policy(),
    )

    assert isinstance(result.output, Tier2Output)
    assert set(Tier2Output.model_fields) == {"output_kind", "advisory", "advisory_hash"}


def test_refusal_and_replay_result_unions_are_closed() -> None:
    assert {item.value for item in RefusalType} == {
        "MSA_UNCHARACTERIZED",
        "UNKNOWN_METHOD_OR_FAILURE_MODE",
        "MISSING_REQUIRED_EVIDENCE",
        "STALE_OR_INVALID_CALIBRATION",
        "PACK_VERSION_UNAVAILABLE",
        "INTEGRITY_FAILURE",
        "ENGINE_FAILURE",
        "CONFIGURATION_INVALID",
    }
    assert ReplayVerified.model_config["extra"] == "forbid"
    assert ReplayIntegrityFailure.model_config["extra"] == "forbid"
    assert set(ReplayVerified.model_fields) == {
        "replay_id",
        "run_id",
        "status",
        "algorithm_id",
        "replay_policy_ref",
        "recipe_schema_version",
        "source_run_schema_version",
        "output_hash",
        "snapshot_hash",
        "bound_version_refs",
    }
    assert set(ReplayIntegrityFailure.model_fields) == {
        "replay_id",
        "run_id",
        "status",
        "algorithm_id",
        "replay_policy_ref",
        "reason_id",
    }
