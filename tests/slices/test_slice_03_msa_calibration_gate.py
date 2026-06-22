from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import SLICE3_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.records import sorted_unique_refs
from gptl.core.semantic_types import TermId
from gptl.mie.calibration import CalibrationTruth, evaluate_calibration
from gptl.mie.msa import MSAGateReason
from gptl.mie.schema import (
    IndeterminateDecision,
    Tier1Output,
    Tier2Output,
    WithinMeasurementVariationDecision,
)
from gptl.mie.slice3_service import (
    build_msa_calibration_gate,
    execute_msa_calibration_gate,
)
from gptl.slice3_fixture import (
    VALID_FROM,
    VALID_UNTIL,
    slice3_policy,
    slice3_request,
    slice3_runtime,
)


@pytest.mark.parametrize(
    "calibration,ratified,expected_kind,expected_result,reason_field",
    (
        (
            "VALID",
            False,
            "TIER2_ADVISORY",
            "ADVISORY_NO_VERDICT",
            "intake_unratified",
        ),
        (
            "STALE",
            False,
            "TIER2_ADVISORY",
            "ADVISORY_NO_VERDICT",
            "intake_unratified",
        ),
        (
            "INVALID",
            False,
            "TIER2_ADVISORY",
            "ADVISORY_NO_VERDICT",
            "intake_unratified",
        ),
        (
            "UNAVAILABLE",
            False,
            "TIER2_ADVISORY",
            "ADVISORY_NO_VERDICT",
            "intake_unratified",
        ),
        (
            "VALID",
            True,
            "TIER1_DECISION",
            "WITHIN_MEASUREMENT_VARIATION",
            "within_variation",
        ),
        (
            "STALE",
            True,
            "TIER1_DECISION",
            "STALE_OR_INVALID_CALIBRATION",
            "calibration_stale",
        ),
        (
            "INVALID",
            True,
            "TIER1_DECISION",
            "STALE_OR_INVALID_CALIBRATION",
            "calibration_invalid",
        ),
        (
            "UNAVAILABLE",
            True,
            "TIER1_DECISION",
            "MISSING_REQUIRED_EVIDENCE",
            "calibration_unavailable",
        ),
    ),
)
def test_intake_calibration_matrix_has_one_deterministic_route(
    calibration: str,
    ratified: bool,
    expected_kind: str,
    expected_result: str,
    reason_field: str,
) -> None:
    policy = slice3_policy()
    runtime = slice3_runtime(calibration, "QUALIFIED", Decimal("0.0100"), ratified)

    result = build_msa_calibration_gate(
        slice3_request(f"matrix-{calibration}-{ratified}"),
        runtime,
        policy,
    )

    assert result.output.output_kind == expected_kind
    if isinstance(result.output, Tier2Output):
        body = result.output.advisory
        assert body.status == expected_result
        expected_reason = policy.slice2_policy.unratified_route_reason_id
    else:
        body = result.output.decision
        actual_result = getattr(body, "refusal_type", body.verdict)
        assert actual_result == expected_result
        expected_reason = getattr(policy.route_reasons, reason_field)
    assert body.route_reason_id == expected_reason


def test_calibration_validity_boundaries_are_inclusive_and_policy_bound() -> None:
    runtime = slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True)
    record = runtime.calibration
    policy = runtime.calibration_policy

    at_start = evaluate_calibration(record, policy, VALID_FROM)
    at_end = evaluate_calibration(record, policy, VALID_UNTIL)
    before = evaluate_calibration(record, policy, "2026-06-20T11:59:59.999Z")
    after = evaluate_calibration(record, policy, "2026-06-22T12:00:00.001Z")

    assert at_start.state == CalibrationTruth.VALID
    assert at_end.state == CalibrationTruth.VALID
    assert before.state == CalibrationTruth.INVALID
    assert after.state == CalibrationTruth.STALE


@pytest.mark.parametrize(
    "scenario,refusal_type,route_field",
    (
        ("MISSING", "MSA_UNCHARACTERIZED", "msa_missing"),
        ("UNQUALIFIED", "MSA_UNCHARACTERIZED", "msa_unqualified"),
        ("UNKNOWN", "MSA_UNCHARACTERIZED", "msa_unknown_applicability"),
        ("NOT_APPLICABLE", "MSA_UNCHARACTERIZED", "msa_not_applicable"),
        ("UNIMPLEMENTED", "MSA_UNCHARACTERIZED", "msa_unimplemented_class"),
        ("SCOPE_MISMATCH", "MSA_UNCHARACTERIZED", "msa_scope_mismatch"),
        ("NON_TEST_SCOPE", "MSA_UNCHARACTERIZED", "msa_scope_mismatch"),
        ("INVALID_UNIT", "CONFIGURATION_INVALID", "msa_configuration_invalid"),
        ("GROUPED_TIE", "CONFIGURATION_INVALID", "msa_configuration_invalid"),
    ),
)
def test_msa_failure_routes_are_explicit_and_stop_before_candidates(
    scenario: str,
    refusal_type: str,
    route_field: str,
) -> None:
    policy = slice3_policy()
    runtime = slice3_runtime("VALID", scenario, Decimal("0.0100"), True)

    result = build_msa_calibration_gate(slice3_request(f"msa-{scenario}"), runtime, policy)

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert decision.verdict == "REFUSED"
    assert decision.refusal_type == refusal_type
    assert decision.route_reason_id == getattr(policy.route_reasons, route_field)
    assert decision.assessments == ()
    assert decision.calibration_evaluation is not None
    if scenario == "INVALID_UNIT":
        assert {item.record_ref for item in decision.citations} >= {
            runtime.msa_studies[0].study_ref
        }


def test_invalid_deviation_and_contract_mismatch_fail_closed() -> None:
    policy = slice3_policy()
    negative = slice3_runtime("VALID", "QUALIFIED", Decimal("-0.0001"), True)
    mismatch_base = slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True)
    mismatch_contract = mismatch_base.measurement_contract.model_copy(
        update={"deviation_field_id": "field.temperature"}
    )
    mismatch = mismatch_base.model_copy(update={"measurement_contract": mismatch_contract})

    negative_result = build_msa_calibration_gate(
        slice3_request("negative-deviation"),
        negative,
        policy,
    )
    mismatch_result = build_msa_calibration_gate(
        slice3_request("contract-mismatch"),
        mismatch,
        policy,
    )

    for result in (negative_result, mismatch_result):
        assert isinstance(result.output, Tier1Output)
        assert result.output.decision.verdict == "REFUSED"
        assert result.output.decision.refusal_type == "CONFIGURATION_INVALID"
        assert (
            result.output.decision.route_reason_id == policy.route_reasons.msa_configuration_invalid
        )


def test_test_fixture_msa_cannot_satisfy_a_non_test_scope() -> None:
    policy = slice3_policy()
    runtime = slice3_runtime("VALID", "NON_TEST_SCOPE", Decimal("0.0100"), True)

    result = build_msa_calibration_gate(slice3_request("non-test-isolation"), runtime, policy)

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert decision.verdict == "REFUSED"
    assert decision.refusal_type == "MSA_UNCHARACTERIZED"
    assert decision.context.evidence_scope_ref == runtime.run_context.evidence_scope_ref
    assert decision.route_reason_id == policy.route_reasons.msa_scope_mismatch


def test_msa_boundary_uses_snapshot_bound_unit_conversion() -> None:
    policy = slice3_policy()
    exact = build_msa_calibration_gate(
        slice3_request("boundary-exact"),
        slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True),
        policy,
    )
    above = build_msa_calibration_gate(
        slice3_request("boundary-above"),
        slice3_runtime("VALID", "QUALIFIED", Decimal("0.0101"), True),
        policy,
    )

    assert isinstance(exact.output, Tier1Output)
    assert isinstance(exact.output.decision, WithinMeasurementVariationDecision)
    assert exact.output.decision.measured_deviation == Decimal("0.0100")
    assert exact.output.decision.measured_uncertainty == Decimal("0.0100")
    assert exact.output.decision.uncertainty_unit_id == "unit.mm"
    assert exact.output.decision.assessments == ()
    assert exact.output.decision.required_human_action == policy.within_variation_action
    assert exact.output.decision.route_reason_id == policy.route_reasons.within_variation
    assert isinstance(above.output, Tier1Output)
    assert isinstance(above.output.decision, IndeterminateDecision)
    assert above.output.decision.route_reason_id == policy.route_reasons.outside_variation
    assert above.output.decision.measured_deviation == Decimal("0.0101")
    assert above.output.decision.measured_uncertainty == Decimal("0.0100")
    assert above.output.decision.uncertainty_unit_id == "unit.mm"


@pytest.mark.parametrize(
    "calibration,msa_scenario,deviation",
    (
        ("VALID", "QUALIFIED", Decimal("0.0100")),
        ("UNAVAILABLE", "INVALID_UNIT", Decimal("0.0100")),
    ),
)
def test_slice3_replay_is_byte_identical(
    calibration: str,
    msa_scenario: str,
    deviation: Decimal,
) -> None:
    policy = slice3_policy()
    request = slice3_request(f"replay-{calibration}")
    runtime = slice3_runtime(calibration, msa_scenario, deviation, True)

    first = build_msa_calibration_gate(request, runtime, policy)
    second = build_msa_calibration_gate(request, runtime, policy)

    assert isinstance(first.output, Tier1Output)
    assert isinstance(second.output, Tier1Output)
    assert canonical_bytes(
        first.output,
        policy.slice2_policy.canonicalization_policy,
    ) == canonical_bytes(
        second.output,
        policy.slice2_policy.canonicalization_policy,
    )
    assert first.output.decision_hash == second.output.decision_hash


def test_outside_variation_returns_open_unassessed_candidates() -> None:
    result = build_msa_calibration_gate(
        slice3_request("outside-open"),
        slice3_runtime("VALID", "QUALIFIED", Decimal("0.0101"), True),
        slice3_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, IndeterminateDecision)
    assert decision.open_discriminator_refs
    assert decision.assessments
    assert all(item.signature_match_score is None for item in decision.assessments)
    assert all(item.candidate_support_score is None for item in decision.assessments)
    assert any(item.status == "OPEN_UNASSESSED" for item in decision.assessments)
    assert decision.calibration_evaluation.state == CalibrationTruth.VALID
    assert decision.msa_applicability_evaluations


def test_grouped_msa_precedence_applies_and_ungrouped_overlap_is_invalid() -> None:
    policy = slice3_policy()
    grouped = slice3_runtime("VALID", "GROUPED_PRECEDENCE", Decimal("0.0100"), True)

    selected = build_msa_calibration_gate(slice3_request("group-selected"), grouped, policy)

    assert isinstance(selected.output, Tier1Output)
    assert isinstance(selected.output.decision, WithinMeasurementVariationDecision)
    assert selected.output.decision.msa_study_ref.logical_id.endswith("-1")

    ungrouped_studies = tuple(
        study.model_copy(update={"selection_binding": None}) for study in grouped.msa_studies
    )
    ungrouped = grouped.model_copy(
        update={"msa_studies": ungrouped_studies, "msa_selection_groups": ()}
    )
    invalid = build_msa_calibration_gate(slice3_request("group-removed"), ungrouped, policy)

    assert isinstance(invalid.output, Tier1Output)
    assert invalid.output.decision.verdict == "REFUSED"
    assert invalid.output.decision.refusal_type == "CONFIGURATION_INVALID"


def test_gate_precedence_stops_before_invalid_downstream_state() -> None:
    policy = slice3_policy()
    unratified = slice3_runtime("INVALID", "INVALID_UNIT", Decimal("0.0100"), False)
    invalid_calibration = slice3_runtime("INVALID", "INVALID_UNIT", Decimal("0.0100"), True)
    unavailable_calibration = slice3_runtime(
        "UNAVAILABLE",
        "INVALID_UNIT",
        Decimal("0.0100"),
        True,
    )

    intake_result = build_msa_calibration_gate(
        slice3_request("precedence-intake"),
        unratified,
        policy,
    )
    calibration_result = build_msa_calibration_gate(
        slice3_request("precedence-calibration"),
        invalid_calibration,
        policy,
    )
    unavailable_result = build_msa_calibration_gate(
        slice3_request("precedence-unavailable"),
        unavailable_calibration,
        policy,
    )

    assert isinstance(intake_result.output, Tier2Output)
    assert (
        intake_result.output.advisory.route_reason_id
        == policy.slice2_policy.unratified_route_reason_id
    )
    assert isinstance(calibration_result.output, Tier1Output)
    assert calibration_result.output.decision.refusal_type == "STALE_OR_INVALID_CALIBRATION"
    assert calibration_result.output.decision.msa_applicability_evaluations is None
    assert isinstance(unavailable_result.output, Tier1Output)
    assert unavailable_result.output.decision.refusal_type == "MISSING_REQUIRED_EVIDENCE"
    assert (
        unavailable_result.output.decision.route_reason_id
        == policy.route_reasons.calibration_unavailable
    )
    assert unavailable_result.output.decision.msa_applicability_evaluations is None


def test_msa_failure_reason_precedence_is_governed_policy() -> None:
    default_policy = slice3_policy()
    unknown_runtime = slice3_runtime("VALID", "UNKNOWN", Decimal("0.0100"), True)
    scope_runtime = slice3_runtime("VALID", "SCOPE_MISMATCH", Decimal("0.0100"), True)
    unknown_study = unknown_runtime.msa_studies[0].model_copy(
        update={"overlap_scope_id": TermId("msa-overlap.unknown-condition")}
    )
    scope_study = scope_runtime.msa_studies[0]
    studies = tuple(
        sorted((unknown_study, scope_study), key=lambda item: item.study_ref.logical_id)
    )
    extra_refs = sorted_unique_refs(
        (
            *unknown_runtime.slice2_runtime.additional_bound_refs,
            scope_study.study_ref,
            scope_study.predicate_ref,
            scope_study.qualification_scope_ref,
            *scope_study.capability_evidence_refs,
        )
    )
    combined_slice2 = unknown_runtime.slice2_runtime.model_copy(
        update={"additional_bound_refs": extra_refs}
    )
    combined = unknown_runtime.model_copy(
        update={"slice2_runtime": combined_slice2, "msa_studies": studies}
    )

    unknown_first = build_msa_calibration_gate(
        slice3_request("reason-unknown-first"),
        combined,
        default_policy,
    )
    scope_first = default_policy.model_copy(
        update={
            "msa_uncharacterized_precedence": (
                MSAGateReason.SCOPE_MISMATCH,
                MSAGateReason.UNKNOWN_APPLICABILITY,
                MSAGateReason.UNQUALIFIED_STUDY,
                MSAGateReason.NOT_APPLICABLE,
            )
        }
    )
    scope_selected = build_msa_calibration_gate(
        slice3_request("reason-scope-first"),
        combined,
        scope_first,
    )

    assert isinstance(unknown_first.output, Tier1Output)
    assert (
        unknown_first.output.decision.route_reason_id
        == default_policy.route_reasons.msa_unknown_applicability
    )
    assert isinstance(scope_selected.output, Tier1Output)
    assert (
        scope_selected.output.decision.route_reason_id
        == scope_first.route_reasons.msa_scope_mismatch
    )


def test_snapshot_binds_calibration_msa_scope_capability_and_route_policy() -> None:
    runtime = slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True)
    policy = slice3_policy()

    result = build_msa_calibration_gate(slice3_request("snapshot-complete"), runtime, policy)

    bound = {(item.logical_id, item.version_id) for item in result.snapshot.bound_versions}
    study = runtime.msa_studies[0]
    expected = (
        runtime.run_context.run_context_ref,
        runtime.calibration.calibration_ref,
        runtime.calibration_policy.policy_ref,
        runtime.implemented_msa_classes.registry_ref,
        runtime.measurement_contract.contract_ref,
        *runtime.measurement_contract.evidence_refs,
        runtime.run_context.evidence_scope_ref,
        study.study_ref,
        study.predicate_ref,
        *study.capability_evidence_refs,
        policy.route_policy_ref,
    )
    assert {(item.logical_id, item.version_id) for item in expected}.issubset(bound)


def test_snapshot_binding_rejects_conflicting_runtime_reference() -> None:
    runtime = slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True)
    target = runtime.calibration.calibration_ref
    conflicting = target.model_copy(update={"content_hash": "f" * 64})
    refs = tuple(
        conflicting if item == target else item
        for item in runtime.slice2_runtime.additional_bound_refs
    )
    invalid_slice2 = runtime.slice2_runtime.model_copy(update={"additional_bound_refs": refs})
    invalid = runtime.model_copy(update={"slice2_runtime": invalid_slice2})

    with pytest.raises(ValueError, match="omit or conflict"):
        build_msa_calibration_gate(
            slice3_request("binding-conflict"),
            invalid,
            slice3_policy(),
        )


def test_slice3_persists_with_explicit_schema_and_reloads_complete_record(
    postgres_url: str,
) -> None:
    policy = slice3_policy()
    request = slice3_request("persisted")
    runtime = slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True)
    store = PostgresRunStore(postgres_url, policy.slice2_policy.canonicalization_policy)
    store.initialize()

    result = execute_msa_calibration_gate(request, runtime, policy, store)
    stored = store.load_run(request.run_id)

    assert stored is not None
    assert stored.schema_version == SLICE3_RUN_SCHEMA_VERSION
    assert stored.payload == canonical_bytes(
        result.output,
        policy.slice2_policy.canonicalization_policy,
    )
    assert stored.snapshot_payload == canonical_bytes(
        result.snapshot,
        policy.slice2_policy.canonicalization_policy,
    )
    assert len(stored.audit_payloads) == 1
    assert stored.bound_version_payloads


def test_documented_slice3_demo_runs_against_postgres(postgres_url: str) -> None:
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "msa-gate",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"verdict": "WITHIN_MEASUREMENT_VARIATION"' in completed.stdout
    assert '"schema_version": "gptl.snapshot.v1"' in completed.stdout
