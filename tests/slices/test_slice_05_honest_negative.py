from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.core.directives import DisplayDirective
from gptl.core.persistence import SLICE5_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.semantic_types import TemplateId
from gptl.mie import slice5_service
from gptl.mie.diagnostics import DiagnosticEngineError
from gptl.mie.predicates import EnumValue, EqualityComparison, Predicate
from gptl.mie.schema import (
    Citation,
    IndeterminateDecision,
    KnownArtifactsExcludedDecision,
    MethodArtifactDecision,
    RefusalDecision,
    Tier1Output,
)
from gptl.mie.slice5_service import (
    Slice5Policy,
    Slice5Runtime,
    build_honest_negative,
    execute_honest_negative,
    negative_bound_refs,
)
from gptl.slice4_fixture import FIELD_PEAK_SHAPE, FIELD_REFERENCE_RESCAN, PEAK_ISOLATED, RESCAN_REAL
from gptl.slice5_fixture import (
    KNOWN_GAP_CATEGORY,
    slice5_policy,
    slice5_request,
    slice5_runtime,
)


def test_complete_terminal_catalog_returns_honest_bounded_negative() -> None:
    policy = slice5_policy()
    runtime = slice5_runtime("COMPLETE")
    result = build_honest_negative(
        slice5_request("complete"),
        runtime,
        policy,
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, KnownArtifactsExcludedDecision)
    assert decision.operational_mode == "RESEARCH_ONLY"
    assert decision.verdict == "KNOWN_ARTIFACTS_EXCLUDED"
    assert decision.dispositional is False
    assert decision.non_record_of_record is True
    assert not (
        set(KnownArtifactsExcludedDecision.model_fields)
        & {"is_real", "real_behavior", "material_is_real", "confirmed_real"}
    )
    assert decision.route_reason_id == policy.route_reasons.known_artifacts_excluded
    assert decision.evaluated_fraction_within_published_catalog == Decimal("0.6667")
    assert [item.status for item in decision.assessments] == ["ELIMINATED", "RULED_OUT"]
    assert [item.terminal_status for item in decision.artifacts_evaluated] == [
        "ELIMINATED",
        "RULED_OUT",
    ]
    assert [item.category_id for item in decision.known_unevaluated_gaps] == [KNOWN_GAP_CATEGORY]
    gap = decision.known_unevaluated_gaps[0]
    expected_gap = runtime.known_gaps[0]
    assert gap.why_unevaluated == expected_gap.why_unevaluated
    assert gap.what_would_enable == expected_gap.what_would_enable
    assert decision.catalog_boundary == policy.catalog_boundary
    assert decision.required_human_action == policy.known_artifacts_excluded_action
    assert all(item.ruling_citations for item in decision.artifacts_evaluated)
    ruling_record_ids = {
        citation.record_ref.logical_id
        for artifact in decision.artifacts_evaluated
        for citation in artifact.ruling_citations
    }
    assert "elimination-rule.detector-drift-humid" in ruling_record_ids
    assert "rule-out-requirement.peak-overlap" in ruling_record_ids


def test_missing_terminal_ruling_citation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = slice5_service._negative_citations

    def without_elimination_rule(runtime: Slice5Runtime) -> tuple[Citation, ...]:
        return tuple(
            item
            for item in original(runtime)
            if item.record_ref.logical_id != "elimination-rule.detector-drift-humid"
        )

    monkeypatch.setattr(slice5_service, "_negative_citations", without_elimination_rule)
    policy = slice5_policy()

    result = build_honest_negative(
        slice5_request("missing-ruling-citation"),
        slice5_runtime("COMPLETE"),
        policy,
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, RefusalDecision)
    assert decision.refusal_type == "ENGINE_FAILURE"
    assert decision.route_reason_id == policy.slice4_policy.route_reasons.diagnostic_engine_failure


def test_ruling_citation_intersection_requires_full_governed_identity() -> None:
    runtime = slice5_runtime("COMPLETE")
    citation = next(
        item
        for item in slice5_service._negative_citations(runtime)
        if item.record_ref.logical_id == "elimination-rule.detector-drift-humid"
    )
    divergent = citation.record_ref.model_copy(update={"content_hash": "0" * 64})

    with pytest.raises(DiagnosticEngineError, match="lost its governing citation"):
        slice5_service._citations_for_refs((citation,), (divergent,))


def test_zero_support_without_every_required_discriminator_never_rules_out() -> None:
    result = build_honest_negative(
        slice5_request("inconclusive"),
        slice5_runtime("LOW_SUPPORT_WITH_INCONCLUSIVE"),
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, IndeterminateDecision)
    peak = decision.assessments[-1]
    assert peak.candidate_support_score == Decimal("0.0000")
    assert peak.status == "CANDIDATE"


def test_hard_elimination_stops_before_candidate_scoring() -> None:
    runtime = slice5_runtime("COMPLETE")
    drift_feature = next(
        item
        for item in runtime.slice4_runtime.signature_features
        if item.candidate_ref.logical_id == "failure.detector-drift"
    )
    scoring_would_fail = drift_feature.model_copy(
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
        scoring_would_fail if item.feature_ref == drift_feature.feature_ref else item
        for item in runtime.slice4_runtime.signature_features
    )
    runtime4 = runtime.slice4_runtime.model_copy(update={"signature_features": features})
    changed = runtime.model_copy(update={"slice4_runtime": runtime4})

    result = build_honest_negative(
        slice5_request("elimination-before-scoring"),
        changed,
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, KnownArtifactsExcludedDecision)
    assert result.output.decision.assessments[0].status == "ELIMINATED"


def test_open_unassessed_candidate_blocks_negative_verdict() -> None:
    result = build_honest_negative(
        slice5_request("open"),
        slice5_runtime("OPEN_UNASSESSED"),
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, IndeterminateDecision)
    assert result.output.decision.assessments[-1].status == "OPEN_UNASSESSED"
    assert result.output.decision.assessments[-1].candidate_support_score is None


def test_unresolved_applicability_blocks_negative_verdict() -> None:
    result = build_honest_negative(
        slice5_request("unknown-applicability"),
        slice5_runtime("UNKNOWN_APPLICABILITY"),
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, RefusalDecision)
    assert decision.refusal_type == "MISSING_REQUIRED_EVIDENCE"
    assert all(item.status == "APPLICABILITY_UNRESOLVED" for item in decision.assessments)


def test_unknown_catalog_denominator_refuses_configuration() -> None:
    result = build_honest_negative(
        slice5_request("unknown-denominator"),
        slice5_runtime("UNKNOWN_DENOMINATOR"),
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, RefusalDecision)
    assert decision.refusal_type == "CONFIGURATION_INVALID"


def test_catalog_fraction_below_governed_minimum_remains_indeterminate() -> None:
    result = build_honest_negative(
        slice5_request("fraction-below-minimum"),
        slice5_runtime("FRACTION_BELOW_MINIMUM"),
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert isinstance(decision, IndeterminateDecision)
    assert [item.status for item in decision.assessments] == ["ELIMINATED", "RULED_OUT"]


def test_positive_artifact_verdict_has_precedence_over_bounded_negative() -> None:
    result = build_honest_negative(
        slice5_request("positive-precedence"),
        slice5_runtime("POSITIVE_PRECEDENCE"),
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, MethodArtifactDecision)


@pytest.mark.parametrize(
    "threshold,expected_type",
    (
        (Decimal("0.0239"), IndeterminateDecision),
        (Decimal("0.0240"), KnownArtifactsExcludedDecision),
        (Decimal("0.0241"), KnownArtifactsExcludedDecision),
    ),
)
def test_rule_out_threshold_uses_exact_decimal_boundary(
    threshold: Decimal,
    expected_type: type[IndeterminateDecision] | type[KnownArtifactsExcludedDecision],
) -> None:
    runtime = _runtime_with_peak_support_00240(threshold)
    result = build_honest_negative(
        slice5_request(f"ruleout-boundary-{threshold}"),
        runtime,
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, expected_type)
    peak = result.output.decision.assessments[-1]
    assert peak.candidate_support_score == Decimal("0.0240")


def test_unknown_gap_template_is_configuration_invalid() -> None:
    runtime = slice5_runtime("COMPLETE")
    invalid_gap = runtime.known_gaps[0].model_copy(
        update={
            "why_unevaluated": DisplayDirective(
                template_id=TemplateId("gap.unregistered"),
                params=(),
            )
        }
    )
    changed = runtime.model_copy(update={"known_gaps": (invalid_gap,)})

    result = build_honest_negative(
        slice5_request("invalid-gap-template"),
        changed,
        slice5_policy(),
    )

    assert isinstance(result.output, Tier1Output)
    assert isinstance(result.output.decision, RefusalDecision)
    assert result.output.decision.refusal_type == "CONFIGURATION_INVALID"


@pytest.mark.parametrize(
    "directive_field",
    ("known_artifacts_excluded_action", "catalog_boundary"),
)
def test_unregistered_policy_directive_is_rejected_at_construction(
    directive_field: str,
) -> None:
    policy = slice5_policy()
    invalid = DisplayDirective(
        template_id=TemplateId("directive.unregistered"),
        params=(),
    )

    with pytest.raises(ValidationError, match="unknown template"):
        Slice5Policy.model_validate(
            {
                **policy.model_dump(mode="python"),
                directive_field: invalid,
            }
        )


def test_rule_out_contract_must_cover_every_published_candidate() -> None:
    runtime = slice5_runtime("COMPLETE")
    canonicalization = (
        slice5_policy().slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    )

    with pytest.raises(ValidationError, match="every published candidate"):
        Slice5Runtime.model_validate(
            {
                **runtime.model_dump(mode="python"),
                "rule_out_requirements": runtime.rule_out_requirements[1:],
            },
            context={"canonicalization_policy": canonicalization},
        )


def test_identical_negative_run_replays_byte_identically() -> None:
    policy = slice5_policy()
    request = slice5_request("replay")
    runtime = slice5_runtime("COMPLETE")

    first = build_honest_negative(request, runtime, policy)
    second = build_honest_negative(request, runtime, policy)
    canonicalization = policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy

    assert canonical_bytes(first.output, canonicalization) == canonical_bytes(
        second.output,
        canonicalization,
    )
    assert first.output.decision_hash == second.output.decision_hash


def test_slice5_snapshot_binds_every_negative_contract() -> None:
    runtime = slice5_runtime("COMPLETE")
    policy = slice5_policy()
    result = build_honest_negative(slice5_request("snapshot"), runtime, policy)

    bound = {(item.logical_id, item.version_id) for item in result.snapshot.bound_versions}
    expected = (policy.route_policy_ref, *negative_bound_refs(runtime))
    assert {(item.logical_id, item.version_id) for item in expected}.issubset(bound)


def test_slice5_persists_explicit_schema_and_complete_payload(postgres_url: str) -> None:
    policy = slice5_policy()
    request = slice5_request("persisted")
    runtime = slice5_runtime("COMPLETE")
    canonicalization = policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    store = PostgresRunStore(postgres_url, canonicalization)
    store.initialize()

    result = execute_honest_negative(request, runtime, policy, store)
    stored = store.load_run(request.run_id)

    assert stored is not None
    assert stored.schema_version == SLICE5_RUN_SCHEMA_VERSION
    assert stored.payload == canonical_bytes(result.output, canonicalization)
    assert stored.snapshot_payload == canonical_bytes(result.snapshot, canonicalization)
    assert stored.citation_payloads
    assert stored.bound_version_payloads


def test_documented_slice5_demo_runs_against_postgres(postgres_url: str) -> None:
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "honest-negative",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"verdict": "KNOWN_ARTIFACTS_EXCLUDED"' in completed.stdout
    assert '"schema_version": "gptl.snapshot.v1"' in completed.stdout


def _runtime_with_peak_support_00240(threshold: Decimal) -> Slice5Runtime:
    runtime = slice5_runtime("COMPLETE")
    peak_feature = next(
        item
        for item in runtime.slice4_runtime.signature_features
        if item.candidate_ref.logical_id == "failure.peak-overlap"
        and item.observable_id == FIELD_PEAK_SHAPE
    )
    changed_feature = peak_feature.model_copy(
        update={
            "match_predicate": Predicate(
                kind="comparison",
                comparison=EqualityComparison(
                    op="eq",
                    field_id=FIELD_PEAK_SHAPE,
                    operand=EnumValue(kind="ENUM", value=PEAK_ISOLATED),
                ),
            )
        }
    )
    features = tuple(
        changed_feature if item.feature_ref == peak_feature.feature_ref else item
        for item in runtime.slice4_runtime.signature_features
    )
    runtime4 = runtime.slice4_runtime.model_copy(update={"signature_features": features})
    policies = tuple(
        item.model_copy(update={"value": threshold}) if item.policy_kind == "TAU_RULEOUT" else item
        for item in runtime.numeric_policies
    )
    return runtime.model_copy(
        update={
            "slice4_runtime": runtime4,
            "numeric_policies": policies,
        }
    )
