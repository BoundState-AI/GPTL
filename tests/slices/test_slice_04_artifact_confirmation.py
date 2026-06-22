from __future__ import annotations

import inspect
import itertools
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes, canonical_sha256
from gptl.core.persistence import SLICE4_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.mie import slice4_service
from gptl.mie.candidates import load_candidate_set
from gptl.mie.diagnostics import (
    evaluate_discriminators,
    evaluate_signature,
    evaluate_support,
    resolve_diagnostic_active_state,
)
from gptl.mie.predicates import EnumValue, EqualityComparison, Predicate
from gptl.mie.schema import IndeterminateDecision, MethodArtifactDecision, Tier1Output
from gptl.mie.slice3_service import Slice3OutsideVariationReady, prepare_msa_calibration_gate
from gptl.mie.slice4_service import (
    Slice4Runtime,
    build_artifact_confirmation,
    execute_artifact_confirmation,
)
from gptl.slice2_fixture import governed_ref
from gptl.slice4_fixture import (
    AS_OF,
    FIELD_PEAK_SHAPE,
    FIELD_REFERENCE_RESCAN,
    LATER_AS_OF,
    PEAK_OVERLAP,
    RESCAN_ARTIFACT,
    RESCAN_REAL,
    slice4_policy,
    slice4_request,
    slice4_runtime,
)


def test_diagnostic_state_hash_has_one_exact_canonical_payload() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    request = slice4_request("diagnostic-state-hash", AS_OF)
    policy = slice4_policy().slice3_policy.slice2_policy.canonicalization_policy

    state = resolve_diagnostic_active_state(
        runtime.discriminator_results,
        runtime.role_authorization_events,
        runtime.attestation_events,
        request.as_of_time,
        policy,
    )
    payload = {
        "as_of_time": state.as_of_time,
        "active_discriminator_result_refs": state.active_discriminator_result_refs,
        "active_role_authorization_refs": state.active_role_authorization_refs,
        "active_attestation_refs": state.active_attestation_refs,
    }

    assert state.state_hash == canonical_sha256(payload, policy)
    assert state.state_hash != canonical_sha256({**payload, "state_hash": state.state_hash}, policy)


def test_structured_confirmation_returns_cited_method_artifact() -> None:
    policy = slice4_policy()
    result = build_artifact_confirmation(
        slice4_request("structured", AS_OF),
        slice4_runtime("STRUCTURED", "NONE", True, "NONE"),
        policy,
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, MethodArtifactDecision)
    assert decision.operational_mode == "RESEARCH_ONLY"
    assert decision.route_reason_id == policy.route_reasons.method_artifact
    assert decision.confirmed_candidate_ref.logical_id == "failure.peak-overlap"
    assert decision.evaluated_fraction_within_published_catalog == Decimal("1.0000")
    assert decision.confirm_evidence
    assert decision.diagnostic_state_hash
    assert decision.what_would_change_this == policy.what_would_change_artifact
    assert decision.measured_deviation == Decimal("0.0101")
    assert decision.measured_uncertainty == Decimal("0.0100")
    confirmed = tuple(item for item in decision.assessments if item.status == "CONFIRMED")
    assert len(confirmed) == 1
    assert confirmed[0].candidate_support_score == Decimal("1.0000")


def test_uniquely_dominant_winner_allows_a_second_confirmed_candidate() -> None:
    policy = slice4_policy()
    result = build_artifact_confirmation(
        slice4_request("two-confirmed", AS_OF),
        _runtime_with_two_confirmed_candidates(),
        policy,
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, MethodArtifactDecision)
    assert decision.confirmed_candidate_ref.logical_id == "failure.peak-overlap"
    confirmed = tuple(item for item in decision.assessments if item.status == "CONFIRMED")
    assert len(confirmed) == 2
    assert [item.candidate_support_score for item in confirmed] == [
        Decimal("0.8000"),
        Decimal("1.0000"),
    ]


def test_output_schema_failure_returns_governed_engine_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_output(*args: object, **kwargs: object) -> object:
        raise ValidationError.from_exception_data("MethodArtifactDecision", [])

    monkeypatch.setattr(MethodArtifactDecision, "model_validate", reject_output)
    policy = slice4_policy()

    result = build_artifact_confirmation(
        slice4_request("schema-engine-failure", AS_OF),
        slice4_runtime("STRUCTURED", "NONE", True, "NONE"),
        policy,
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert decision.verdict == "REFUSED"
    assert decision.refusal_type == "ENGINE_FAILURE"
    assert decision.route_reason_id == policy.route_reasons.diagnostic_engine_failure
    assert decision.required_human_action == policy.engine_failure_action


def test_zero_signature_observations_remain_open_unassessed() -> None:
    result = build_artifact_confirmation(
        slice4_request("zero-signature", AS_OF),
        slice4_runtime("STRUCTURED", "NONE", False, "NONE"),
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, IndeterminateDecision)
    assert decision.assessments
    assert all(item.evidence_state == "OPEN_UNASSESSED" for item in decision.assessments)
    assert all(item.signature_match_score is None for item in decision.assessments)
    assert all(item.signature_coverage == Decimal("0.0000") for item in decision.assessments)
    assert all(item.candidate_support_score is None for item in decision.assessments)


def test_partial_required_signature_evidence_never_aggregates_support() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    values = tuple(
        item
        for item in runtime.slice3_runtime.slice2_runtime.intake.values
        if item.field_id != FIELD_REFERENCE_RESCAN
    )
    intake = runtime.slice3_runtime.slice2_runtime.intake.model_copy(update={"values": values})
    slice2 = runtime.slice3_runtime.slice2_runtime.model_copy(update={"intake": intake})
    slice3 = runtime.slice3_runtime.model_copy(update={"slice2_runtime": slice2})
    partial = runtime.model_copy(update={"slice3_runtime": slice3})

    result = build_artifact_confirmation(
        slice4_request("partial-signature", AS_OF),
        partial,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, IndeterminateDecision)
    assert all(item.evidence_state == "OPEN_UNASSESSED" for item in decision.assessments)
    assert all(item.signature_match_score is not None for item in decision.assessments)
    assert all(item.signature_coverage == Decimal("0.6000") for item in decision.assessments)
    assert all(item.candidate_support_score is None for item in decision.assessments)


def test_slice4_authoritative_path_has_no_renderer_dependency() -> None:
    source = inspect.getsource(slice4_service).lower()

    assert "render" not in source


def test_missing_required_structured_evidence_blocks_confirmation() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE").model_copy(
        update={"evidence_type_assertions": ()}
    )

    result = build_artifact_confirmation(
        slice4_request("missing-confirm-evidence", AS_OF),
        runtime,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, IndeterminateDecision)
    assert all(item.status != "CONFIRMED" for item in result.output.decision.assessments)


@pytest.mark.parametrize(
    "scenario,expected_verdict",
    (
        ("VALID", "METHOD_ARTIFACT"),
        ("DISALLOWED_ROLE", "INDETERMINATE"),
        ("SEPARATION_AUTHOR", "INDETERMINATE"),
        ("SEPARATION_APPROVER", "INDETERMINATE"),
        ("ATTESTATION_REVOKED", "INDETERMINATE"),
        ("ROLE_REVOKED", "INDETERMINATE"),
        ("LATE_ATTESTATION_REVOCATION", "METHOD_ARTIFACT"),
        ("ATTESTATION_SUPERSEDED", "METHOD_ARTIFACT"),
    ),
)
def test_attested_confirmation_enforces_authority_and_lifecycle(
    scenario: str,
    expected_verdict: str,
) -> None:
    result = build_artifact_confirmation(
        slice4_request(f"attested-{scenario}", AS_OF),
        slice4_runtime("HUMAN_ATTESTED", scenario, True, "NONE"),
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == expected_verdict
    if expected_verdict != "METHOD_ARTIFACT":
        assert all(item.status != "CONFIRMED" for item in result.output.decision.assessments)


def test_multiple_active_role_authorizations_fail_integrity() -> None:
    runtime = slice4_runtime("HUMAN_ATTESTED", "VALID", True, "NONE")
    duplicate = runtime.role_authorization_events[0].model_copy(
        update={"event_ref": governed_ref("role-authorization.eds-reviewer-duplicate")}
    )
    changed = runtime.model_copy(
        update={
            "role_authorization_events": tuple(
                sorted(
                    (*runtime.role_authorization_events, duplicate),
                    key=lambda item: (
                        item.event_ref.logical_id,
                        item.event_ref.version_number,
                        item.event_ref.version_id,
                    ),
                )
            )
        }
    )
    changed = _bind_additional_refs(changed, (duplicate.event_ref,))

    result = build_artifact_confirmation(
        slice4_request("duplicate-role-authorization", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == "REFUSED"
    assert result.output.decision.refusal_type == "INTEGRITY_FAILURE"


def test_multiple_active_attestations_fail_integrity() -> None:
    runtime = slice4_runtime("HUMAN_ATTESTED", "VALID", True, "NONE")
    duplicate = runtime.attestation_events[0].model_copy(
        update={"attestation_ref": governed_ref("attestation.peak-overlap-duplicate")}
    )
    changed = runtime.model_copy(
        update={
            "attestation_events": tuple(
                sorted(
                    (*runtime.attestation_events, duplicate),
                    key=lambda item: (
                        item.attestation_ref.logical_id,
                        item.attestation_ref.version_number,
                        item.attestation_ref.version_id,
                    ),
                )
            )
        }
    )
    changed = _bind_additional_refs(changed, (duplicate.attestation_ref,))

    result = build_artifact_confirmation(
        slice4_request("duplicate-attestation", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == "REFUSED"
    assert result.output.decision.refusal_type == "INTEGRITY_FAILURE"


def test_later_recorded_revocation_changes_new_run_not_historical_replay() -> None:
    policy = slice4_policy()
    runtime = slice4_runtime(
        "HUMAN_ATTESTED",
        "LATE_ATTESTATION_REVOCATION",
        True,
        "NONE",
    )
    historical_request = slice4_request("revocation-historical", AS_OF)

    historical = build_artifact_confirmation(historical_request, runtime, policy)
    current = build_artifact_confirmation(
        slice4_request("revocation-current", LATER_AS_OF),
        runtime,
        policy,
    )
    replay = build_artifact_confirmation(historical_request, runtime, policy)

    assert historical.output.decision.verdict == "METHOD_ARTIFACT"
    assert current.output.decision.verdict == "INDETERMINATE"
    assert canonical_bytes(
        historical.output,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    ) == canonical_bytes(
        replay.output,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    assert historical.output.decision_hash == replay.output.decision_hash
    assert (
        historical.output.decision.diagnostic_state_hash
        != current.output.decision.diagnostic_state_hash
    )


def test_contradictory_unsuperseded_results_fail_integrity() -> None:
    policy = slice4_policy()
    result = build_artifact_confirmation(
        slice4_request("contradictory", AS_OF),
        slice4_runtime("STRUCTURED", "NONE", True, "CONTRADICTORY"),
        policy,
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert decision.verdict == "REFUSED"
    assert decision.refusal_type == "INTEGRITY_FAILURE"
    assert decision.route_reason_id == policy.route_reasons.diagnostic_integrity_failure


def test_explicit_discriminator_supersession_selects_one_active_result() -> None:
    result = build_artifact_confirmation(
        slice4_request("superseded-result", AS_OF),
        slice4_runtime("STRUCTURED", "NONE", True, "SUPERSEDED"),
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, MethodArtifactDecision)


def test_missing_supersession_target_fails_integrity() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "SUPERSEDED")
    malformed = runtime.discriminator_results[-1].model_copy(
        update={"supersedes_version_id": "discriminator-result.peak-overlap.absent"}
    )
    changed = runtime.model_copy(
        update={"discriminator_results": (*runtime.discriminator_results[:-1], malformed)}
    )

    result = build_artifact_confirmation(
        slice4_request("missing-supersession", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == "REFUSED"
    assert result.output.decision.refusal_type == "INTEGRITY_FAILURE"


def test_discriminator_result_must_bind_evaluated_observation() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "SUPERSEDED")
    mismatched = runtime.discriminator_results[-1].model_copy(
        update={"observed_value_ref": runtime.candidate_contracts[0].contract_ref}
    )
    changed = runtime.model_copy(
        update={"discriminator_results": (*runtime.discriminator_results[:-1], mismatched)}
    )

    result = build_artifact_confirmation(
        slice4_request("result-observation-mismatch", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == "REFUSED"
    assert result.output.decision.refusal_type == "INTEGRITY_FAILURE"


def test_missing_referenced_numeric_policy_fails_configuration() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    changed = runtime.model_copy(update={"numeric_policies": runtime.numeric_policies[1:]})

    result = build_artifact_confirmation(
        slice4_request("missing-numeric-policy", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == "REFUSED"
    assert result.output.decision.refusal_type == "CONFIGURATION_INVALID"


def test_failed_structured_confirm_predicate_blocks_confirmation() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    target = runtime.confirm_tests[-1]
    assert target.kind == "STRUCTURED"
    failed = target.model_copy(
        update={
            "predicate": Predicate(
                kind="comparison",
                comparison=EqualityComparison(
                    op="eq",
                    field_id=FIELD_REFERENCE_RESCAN,
                    operand=EnumValue(kind="ENUM", value=RESCAN_REAL),
                ),
            )
        }
    )
    changed = runtime.model_copy(update={"confirm_tests": (*runtime.confirm_tests[:-1], failed)})

    result = build_artifact_confirmation(
        slice4_request("failed-structured-confirm", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, IndeterminateDecision)
    assert all(item.status != "CONFIRMED" for item in result.output.decision.assessments)


def test_overlapping_discriminator_outcomes_fail_configuration() -> None:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    target = runtime.discriminators[-1]
    invalid = target.model_copy(update={"real_predicate": target.artifact_predicate})
    changed = runtime.model_copy(update={"discriminators": (*runtime.discriminators[:-1], invalid)})

    result = build_artifact_confirmation(
        slice4_request("overlapping-outcomes", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == "REFUSED"
    assert result.output.decision.refusal_type == "CONFIGURATION_INVALID"


@pytest.mark.parametrize(
    "threshold,expected_verdict",
    (
        (Decimal("0.9839"), "METHOD_ARTIFACT"),
        (Decimal("0.9840"), "METHOD_ARTIFACT"),
        (Decimal("0.9841"), "INDETERMINATE"),
    ),
)
def test_confirmation_threshold_uses_exact_decimal_boundary(
    threshold: Decimal,
    expected_verdict: str,
) -> None:
    changed = _runtime_with_peak_support_09840(
        (
            ("TAU_CONFIRM", threshold),
            ("TAU_VERDICT", threshold),
        )
    )

    result = build_artifact_confirmation(
        slice4_request(f"boundary-{threshold}", AS_OF),
        changed,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == expected_verdict
    peak = next(
        item
        for item in result.output.decision.assessments
        if item.candidate_ref.logical_id == "failure.peak-overlap"
    )
    assert peak.candidate_support_score == Decimal("0.9840")


@pytest.mark.parametrize(
    "delta,expected_verdict",
    (
        (Decimal("0.9839"), "METHOD_ARTIFACT"),
        (Decimal("0.9840"), "METHOD_ARTIFACT"),
        (Decimal("0.9841"), "INDETERMINATE"),
    ),
)
def test_dominance_margin_uses_exact_decimal_boundary(
    delta: Decimal,
    expected_verdict: str,
) -> None:
    runtime = _runtime_with_peak_support_09840((("DELTA_DOMINANCE", delta),))

    result = build_artifact_confirmation(
        slice4_request(f"dominance-{delta}", AS_OF),
        runtime,
        slice4_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.verdict == expected_verdict


def test_discriminator_aggregation_is_invariant_to_result_order() -> None:
    policy = slice4_policy()
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    request = slice4_request("permutations", AS_OF)
    prepared = prepare_msa_calibration_gate(
        request,
        runtime.slice3_runtime,
        policy.slice3_policy,
    )
    assert isinstance(prepared, Slice3OutsideVariationReady)
    candidate_set = load_candidate_set(
        runtime.slice3_runtime.slice2_runtime.pack,
        prepared.context_values,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    peak_ref = next(
        item
        for item in candidate_set.preserved_candidate_refs
        if item.logical_id == "failure.peak-overlap"
    )
    contract = next(
        item for item in runtime.candidate_contracts if item.failure_mode_ref == peak_ref
    )
    features = tuple(item for item in runtime.signature_features if item.candidate_ref == peak_ref)
    discriminators = tuple(
        item for item in runtime.discriminators if item.candidate_ref == peak_ref
    )
    signature = evaluate_signature(
        contract,
        features,
        prepared.context_values,
        runtime.numeric_policies,
        runtime.slice3_runtime.slice2_runtime.pack.field_registry,
        runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
        runtime.diagnostic_route_policy,
        request.as_of_time,
        policy.slice3_policy.slice2_policy.operational_mode,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    evaluations = evaluate_discriminators(
        contract,
        discriminators,
        (),
        prepared.context_values,
        runtime.slice3_runtime.slice2_runtime.pack.field_registry,
        runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
        request.as_of_time,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )

    scores = {
        evaluate_support(
            signature,
            tuple(permutation),
            discriminators,
            runtime.numeric_policies,
            runtime.diagnostic_route_policy,
            request.as_of_time,
            policy.slice3_policy.slice2_policy.operational_mode,
            policy.slice3_policy.slice2_policy.canonicalization_policy,
        ).support_score
        for permutation in itertools.permutations(evaluations)
    }

    assert scores == {Decimal("1.0000")}


def test_discriminator_aggregation_is_commutative_over_finite_outcome_domain() -> None:
    policy = slice4_policy()
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    request = slice4_request("commutative-domain", AS_OF)
    prepared = prepare_msa_calibration_gate(
        request,
        runtime.slice3_runtime,
        policy.slice3_policy,
    )
    assert isinstance(prepared, Slice3OutsideVariationReady)
    contract = runtime.candidate_contracts[-1]
    features = tuple(
        item
        for item in runtime.signature_features
        if item.candidate_ref == contract.failure_mode_ref
    )
    discriminators = tuple(
        item for item in runtime.discriminators if item.candidate_ref == contract.failure_mode_ref
    )
    signature = evaluate_signature(
        contract,
        features,
        prepared.context_values,
        runtime.numeric_policies,
        runtime.slice3_runtime.slice2_runtime.pack.field_registry,
        runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
        runtime.diagnostic_route_policy,
        request.as_of_time,
        policy.slice3_policy.slice2_policy.operational_mode,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    base_evaluations = evaluate_discriminators(
        contract,
        discriminators,
        (),
        prepared.context_values,
        runtime.slice3_runtime.slice2_runtime.pack.field_registry,
        runtime.slice3_runtime.slice2_runtime.pack.unit_registry,
        request.as_of_time,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    outcomes = (
        "CONSISTENT_WITH_ARTIFACT",
        "CONSISTENT_WITH_REAL",
        "INCONCLUSIVE",
    )

    for outcome_pair in itertools.product(outcomes, repeat=len(base_evaluations)):
        evaluations = tuple(
            item.model_copy(update={"outcome": outcome})
            for item, outcome in zip(base_evaluations, outcome_pair, strict=True)
        )
        scores = {
            evaluate_support(
                signature,
                tuple(permutation),
                discriminators,
                runtime.numeric_policies,
                runtime.diagnostic_route_policy,
                request.as_of_time,
                policy.slice3_policy.slice2_policy.operational_mode,
                policy.slice3_policy.slice2_policy.canonicalization_policy,
            ).support_score
            for permutation in itertools.permutations(evaluations)
        }
        assert len(scores) == 1


def test_slice4_snapshot_binds_numeric_policy_confirmation_and_authority() -> None:
    runtime = slice4_runtime("HUMAN_ATTESTED", "VALID", True, "NONE")
    policy = slice4_policy()
    result = build_artifact_confirmation(
        slice4_request("snapshot", AS_OF),
        runtime,
        policy,
    )

    bound = {(item.logical_id, item.version_id) for item in result.snapshot.bound_versions}
    expected = (
        runtime.diagnostic_route_policy.policy_ref,
        runtime.diagnostic_route_policy.combine_algorithm_ref,
        runtime.numeric_policies[0].policy_ref,
        runtime.candidate_contracts[-1].contract_ref,
        runtime.confirm_tests[-1].test_ref,
        runtime.role_policies[0].policy_ref,
        runtime.role_authorization_events[0].event_ref,
        runtime.attestation_events[0].attestation_ref,
        policy.route_policy_ref,
    )
    assert {(item.logical_id, item.version_id) for item in expected}.issubset(bound)


def test_slice4_persists_explicit_schema_and_complete_payload(postgres_url: str) -> None:
    policy = slice4_policy()
    request = slice4_request("persisted", AS_OF)
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    store = PostgresRunStore(
        postgres_url,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    store.initialize()

    result = execute_artifact_confirmation(request, runtime, policy, store)
    stored = store.load_run(request.run_id)

    assert stored is not None
    assert stored.schema_version == SLICE4_RUN_SCHEMA_VERSION
    assert stored.payload == canonical_bytes(
        result.output,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    assert stored.snapshot_payload == canonical_bytes(
        result.snapshot,
        policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    assert stored.citation_payloads
    assert stored.bound_version_payloads


def test_documented_slice4_demo_runs_against_postgres(postgres_url: str) -> None:
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "artifact-confirmation",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"verdict": "METHOD_ARTIFACT"' in completed.stdout
    assert '"schema_version": "gptl.snapshot.v1"' in completed.stdout


def _runtime_with_peak_support_09840(
    policy_updates: tuple[tuple[str, Decimal], ...],
) -> Slice4Runtime:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    secondary = next(
        item
        for item in runtime.signature_features
        if item.candidate_ref.logical_id == "failure.peak-overlap"
        and item.observable_id == FIELD_REFERENCE_RESCAN
    )
    changed_feature = secondary.model_copy(
        update={
            "match_predicate": Predicate(
                kind="comparison",
                comparison=EqualityComparison(
                    op="eq",
                    field_id=FIELD_REFERENCE_RESCAN,
                    operand=EnumValue(kind="ENUM", value=RESCAN_REAL),
                ),
            )
        }
    )
    features = tuple(
        changed_feature if item.feature_ref == secondary.feature_ref else item
        for item in runtime.signature_features
    )
    updates = dict(policy_updates)
    policies = tuple(
        item.model_copy(update={"value": updates[item.policy_kind]})
        if item.policy_kind in updates
        else item
        for item in runtime.numeric_policies
    )
    return runtime.model_copy(update={"signature_features": features, "numeric_policies": policies})


def _runtime_with_two_confirmed_candidates() -> Slice4Runtime:
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    drift = runtime.candidate_contracts[0]
    features = []
    for item in runtime.signature_features:
        if item.candidate_ref == drift.failure_mode_ref:
            expected = PEAK_OVERLAP if item.observable_id == FIELD_PEAK_SHAPE else RESCAN_ARTIFACT
            item = item.model_copy(
                update={
                    "match_predicate": Predicate(
                        kind="comparison",
                        comparison=EqualityComparison(
                            op="eq",
                            field_id=item.observable_id,
                            operand=EnumValue(kind="ENUM", value=expected),
                        ),
                    )
                }
            )
        features.append(item)
    policies = tuple(
        item.model_copy(update={"value": Decimal("0.20")})
        if item.policy_kind in {"DISCRIMINATING_POWER", "HIGH_POWER_THRESHOLD"}
        else item
        for item in runtime.numeric_policies
    )
    confirm_tests = tuple(
        item.model_copy(
            update={
                "predicate": Predicate(
                    kind="comparison",
                    comparison=EqualityComparison(
                        op="eq",
                        field_id=FIELD_PEAK_SHAPE,
                        operand=EnumValue(kind="ENUM", value=PEAK_OVERLAP),
                    ),
                )
            }
        )
        if item.test_ref == drift.confirm_test_ref
        else item
        for item in runtime.confirm_tests
    )
    return runtime.model_copy(
        update={
            "signature_features": tuple(features),
            "numeric_policies": policies,
            "confirm_tests": confirm_tests,
        }
    )


def _bind_additional_refs(
    runtime: Slice4Runtime,
    refs: tuple[GovernedRef, ...],
) -> Slice4Runtime:
    additional = sorted_unique_refs(
        (
            *runtime.slice3_runtime.slice2_runtime.additional_bound_refs,
            *refs,
        )
    )
    slice2 = runtime.slice3_runtime.slice2_runtime.model_copy(
        update={"additional_bound_refs": additional}
    )
    slice3 = runtime.slice3_runtime.model_copy(update={"slice2_runtime": slice2})
    return runtime.model_copy(update={"slice3_runtime": slice3})
