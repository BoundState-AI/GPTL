from __future__ import annotations

import inspect
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes, canonical_sha256
from gptl.core.directives import DisplayDirective
from gptl.core.persistence import SLICE6_RUN_SCHEMA_VERSION, PostgresRunStore
from gptl.core.semantic_types import FieldId, TemplateId, TermId
from gptl.mie import advisory as advisory_module
from gptl.mie import slice6_service
from gptl.mie.advisory import (
    LEXICAL_UNICODE_DATA_VERSION,
    AdvisoryQuery,
    LexicalResolverPolicy,
    normalize_lexical_text,
    resolve_advisory_method,
)
from gptl.mie.schema import AdvisoryDecision, RenderedArtifact, Tier2Output
from gptl.mie.slice6_service import (
    AdvisoryConfigurationError,
    advisory_bound_refs,
    build_tier2_advisory,
    execute_tier2_advisory,
)
from gptl.slice4_fixture import FIELD_REFERENCE_RESCAN
from gptl.slice6_fixture import (
    MEASUREMENT_MSA,
    METHOD_PRIMARY_REF,
    METHOD_SECONDARY_REF,
    RECORD_CALIBRATION,
    RECORD_MSA,
    TERM_SPECTROSCOPY,
    slice6_policy,
    slice6_query,
    slice6_request,
    slice6_runtime,
)


def _resolver_query(
    *,
    method_text: str,
    controlled_term_ids: tuple[TermId, ...] = (),
    observable_ids: tuple[FieldId, ...] = (),
    instrument_type_ids: tuple[TermId, ...] = (),
    failure_class_ids: tuple[TermId, ...] = (),
) -> AdvisoryQuery:
    return slice6_query("MISSING_MSA").model_copy(
        update={
            "method_text": method_text,
            "controlled_term_ids": controlled_term_ids,
            "observable_ids": observable_ids,
            "instrument_type_ids": instrument_type_ids,
            "failure_class_ids": failure_class_ids,
        }
    )


@pytest.mark.parametrize(
    "scenario,resolution,gap,proposed,measurements,records",
    (
        (
            "UNRATIFIED_INTAKE",
            "RESOLVED",
            "gap.intake-unratified",
            ("field.mode",),
            (),
            (),
        ),
        ("AMBIGUOUS_METHOD", "AMBIGUOUS", "gap.method-ambiguous", (), (), ()),
        ("UNKNOWN_METHOD", "UNKNOWN", "gap.method-unknown", (), (), ()),
        (
            "MISSING_MSA",
            "RESOLVED",
            "gap.msa-missing",
            (),
            (MEASUREMENT_MSA,),
            (RECORD_MSA,),
        ),
        (
            "UNIMPLEMENTED_MSA",
            "RESOLVED",
            "gap.msa-unimplemented",
            (),
            (MEASUREMENT_MSA,),
            (RECORD_MSA,),
        ),
        (
            "STALE_CALIBRATION",
            "RESOLVED",
            "gap.calibration-stale",
            (),
            (),
            (RECORD_CALIBRATION,),
        ),
        (
            "UNAVAILABLE_CALIBRATION",
            "RESOLVED",
            "gap.calibration-unavailable",
            (),
            (),
            (RECORD_CALIBRATION,),
        ),
        (
            "UNKNOWN_APPLICABILITY",
            "RESOLVED",
            "gap.applicability-unknown",
            ("field.eds-peak-shape",),
            (),
            (),
        ),
    ),
)
def test_each_ineligible_case_returns_typed_nonverdict_advisory(
    scenario: str,
    resolution: str,
    gap: str,
    proposed: tuple[str, ...],
    measurements: tuple[str, ...],
    records: tuple[str, ...],
) -> None:
    policy = slice6_policy()
    result = build_tier2_advisory(
        slice6_request(scenario.lower()),
        slice6_query(scenario),
        slice6_runtime(scenario),
        policy,
    )

    assert isinstance(result.output, Tier2Output)
    assert result.output.output_kind == "TIER2_ADVISORY"
    advisory = result.output.advisory
    canonicalization = (
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    )
    assert result.output.advisory_hash == canonical_sha256(advisory, canonicalization)
    assert advisory.status == "ADVISORY_NO_VERDICT"
    assert advisory.method_resolution == resolution
    assert advisory.tier1_eligibility_gap_ids == (gap,)
    assert advisory.proposed_field_ids == proposed
    assert advisory.required_measurement_ids == measurements
    assert advisory.required_record_type_ids == records
    assert advisory.dispositional is False
    assert advisory.non_record_of_record is True
    assert advisory.next_steps
    assert advisory.citations


def test_advisory_schema_cannot_carry_verdict_refusal_or_support() -> None:
    forbidden = {
        "verdict",
        "refusal_type",
        "support_score",
        "candidate_support_score",
        "confidence",
        "probability",
    }

    assert not (set(AdvisoryDecision.model_fields) & forbidden)


def test_tier2_rejects_a_positive_tier1_verdict_before_route_selection() -> None:
    with pytest.raises(
        AdvisoryConfigurationError,
        match="cannot consume or replace a Tier 1 verdict",
    ):
        build_tier2_advisory(
            slice6_request("positive-verdict-rejected"),
            slice6_query("POSITIVE_PRECEDENCE"),
            slice6_runtime("POSITIVE_PRECEDENCE"),
            slice6_policy(),
        )


def test_lexical_normalization_uses_governed_fixed_unicode_data() -> None:
    policy = slice6_runtime("MISSING_MSA").resolver_policy

    assert policy.normalization_id == "NFKC_UCD_3_2_ASCII_CASEFOLD_ALNUM_V1"
    assert policy.unicode_data_version == LEXICAL_UNICODE_DATA_VERSION
    assert normalize_lexical_text("\uff25\uff24\uff33 \ufb00") == ("eds", "ff")


def test_unexpected_unicode_data_version_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnexpectedUnicodeData:
        unidata_version = "unexpected"

    monkeypatch.setattr(
        advisory_module,
        "_LEXICAL_UNICODE_DATABASE",
        UnexpectedUnicodeData(),
    )

    with pytest.raises(ValueError, match="does not match governed policy"):
        normalize_lexical_text("eds")


def test_resolver_policy_rejects_an_unimplemented_unicode_data_version() -> None:
    payload = slice6_runtime("MISSING_MSA").resolver_policy.model_dump(mode="python")
    payload["unicode_data_version"] = "15.1.0"

    with pytest.raises(ValidationError, match="unicode_data_version"):
        LexicalResolverPolicy.model_validate(payload)


@pytest.mark.parametrize(
    "public_function",
    (
        normalize_lexical_text,
        resolve_advisory_method,
        build_tier2_advisory,
        execute_tier2_advisory,
        advisory_bound_refs,
    ),
)
def test_slice6_public_functions_declare_their_contract(public_function: object) -> None:
    assert inspect.getdoc(public_function)


def test_ambiguous_alias_preserves_every_bounded_candidate_without_selecting_method() -> None:
    result = build_tier2_advisory(
        slice6_request("ambiguous-candidates"),
        slice6_query("AMBIGUOUS_METHOD"),
        slice6_runtime("AMBIGUOUS_METHOD"),
        slice6_policy(),
    )

    advisory = result.output.advisory
    assert advisory.method_ref is None
    assert [item.logical_id for item in advisory.candidate_failure_mode_refs] == [
        "failure.detector-drift",
        "failure.peak-overlap",
        "failure.secondary-spectrum",
    ]
    assert advisory.applicability_evaluations == ()
    assert advisory.open_discriminator_refs == ()


def test_unknown_method_remains_explicit_without_candidates() -> None:
    result = build_tier2_advisory(
        slice6_request("unknown-explicit"),
        slice6_query("UNKNOWN_METHOD"),
        slice6_runtime("UNKNOWN_METHOD"),
        slice6_policy(),
    )

    advisory = result.output.advisory
    assert advisory.method_resolution == "UNKNOWN"
    assert advisory.method_ref is None
    assert advisory.candidate_failure_mode_refs == ()
    assert advisory.applicability_evaluations == ()
    assert advisory.open_discriminator_refs == ()


def test_resolved_advisory_preserves_complete_published_candidate_set() -> None:
    result = build_tier2_advisory(
        slice6_request("resolved-candidates"),
        slice6_query("MISSING_MSA"),
        slice6_runtime("MISSING_MSA"),
        slice6_policy(),
    )

    assert [item.logical_id for item in result.output.advisory.candidate_failure_mode_refs] == [
        "failure.detector-drift",
        "failure.peak-overlap",
    ]


def test_unknown_applicability_evidence_remains_explicit() -> None:
    result = build_tier2_advisory(
        slice6_request("unknown-applicability-evidence"),
        slice6_query("UNKNOWN_APPLICABILITY"),
        slice6_runtime("UNKNOWN_APPLICABILITY"),
        slice6_policy(),
    )

    evaluations = result.output.advisory.applicability_evaluations
    assert evaluations
    assert all(item.truth == "UNKNOWN" for item in evaluations)
    assert all(item.missing_field_ids == ("field.eds-peak-shape",) for item in evaluations)


def test_exact_advisory_query_is_snapshot_bound_and_cited() -> None:
    query = slice6_query("MISSING_MSA")
    result = build_tier2_advisory(
        slice6_request("query-bound"),
        query,
        slice6_runtime("MISSING_MSA"),
        slice6_policy(),
    )

    bound = set(result.snapshot.bound_versions)
    cited = {item.record_ref for item in result.output.advisory.citations}
    assert query.query_ref in bound
    assert set(query.evidence_refs).issubset(bound)
    assert query.query_ref in cited


@pytest.mark.parametrize(
    "query,expected_lane,expected_resolution,expected_refs",
    (
        (
            _resolver_query(
                method_text=(
                    "\uff2d\uff25\uff34\uff28\uff2f\uff24\uff0e\uff25\uff24\uff33"
                    "\uff0d\uff32\uff25\uff26\uff25\uff32\uff25\uff2e\uff23\uff25"
                ),
                controlled_term_ids=(),
                observable_ids=(),
                instrument_type_ids=(),
                failure_class_ids=(),
            ),
            "EXACT",
            "RESOLVED",
            (METHOD_PRIMARY_REF,),
        ),
        (
            _resolver_query(
                method_text="",
                controlled_term_ids=(TERM_SPECTROSCOPY,),
                observable_ids=(),
                instrument_type_ids=(),
                failure_class_ids=(),
            ),
            "CONTROLLED_TERM",
            "AMBIGUOUS",
            (METHOD_PRIMARY_REF, METHOD_SECONDARY_REF),
        ),
        (
            _resolver_query(
                method_text="",
                controlled_term_ids=(),
                observable_ids=(FIELD_REFERENCE_RESCAN,),
                instrument_type_ids=(),
                failure_class_ids=(),
            ),
            "RELATIONAL",
            "RESOLVED",
            (METHOD_PRIMARY_REF,),
        ),
        (
            _resolver_query(
                method_text="energy dispersive spectrum",
                controlled_term_ids=(),
                observable_ids=(),
                instrument_type_ids=(),
                failure_class_ids=(),
            ),
            "LEXICAL",
            "RESOLVED",
            (METHOD_PRIMARY_REF,),
        ),
        (
            _resolver_query(
                method_text="spectral analysis",
                controlled_term_ids=(),
                observable_ids=(),
                instrument_type_ids=(),
                failure_class_ids=(),
            ),
            "LEXICAL",
            "AMBIGUOUS",
            (METHOD_PRIMARY_REF, METHOD_SECONDARY_REF),
        ),
    ),
)
def test_resolver_uses_declared_lane_order_and_stable_governed_tie_break(
    query: AdvisoryQuery,
    expected_lane: str,
    expected_resolution: str,
    expected_refs: tuple,
) -> None:
    runtime = slice6_runtime("MISSING_MSA")

    result = resolve_advisory_method(query, runtime.catalog, runtime.resolver_policy)

    assert result.resolved_by_lane == expected_lane
    assert result.resolution == expected_resolution
    assert result.ordered_method_refs == expected_refs


def test_lexical_tie_break_replays_across_process_hash_seeds() -> None:
    repository_root = Path(__file__).parents[2]
    program = """
from gptl.mie.advisory import resolve_advisory_method
from gptl.slice6_fixture import slice6_query, slice6_runtime
r = slice6_runtime('MISSING_MSA')
q = slice6_query('MISSING_MSA').model_copy(update={'method_text': 'spectral analysis'})
print('|'.join(x.logical_id for x in resolve_advisory_method(q, r.catalog, r.resolver_policy).ordered_method_refs))
"""
    outputs = []
    for seed in ("1", "8675309"):
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            [sys.executable, "-c", program],
            cwd=repository_root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        outputs.append(completed.stdout.strip())

    assert outputs == ["method.eds-reference|method.eds-secondary"] * 2


def test_equivalent_text_search_accelerator_cannot_change_output() -> None:
    policy = slice6_policy()
    request = slice6_request("accelerator-equivalent")
    query = slice6_query("MISSING_MSA")
    runtime = slice6_runtime("MISSING_MSA")
    canonicalization = (
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    )
    expected_refs = resolve_advisory_method(
        query,
        runtime.catalog,
        runtime.resolver_policy,
    ).ordered_method_refs

    without = build_tier2_advisory(request, query, runtime, policy)
    with_accelerator = build_tier2_advisory(
        request,
        query,
        runtime,
        policy,
        expected_refs,
    )

    assert canonical_bytes(without.output, canonicalization) == canonical_bytes(
        with_accelerator.output,
        canonicalization,
    )
    assert without.output.advisory_hash == with_accelerator.output.advisory_hash


def test_non_equivalent_text_search_accelerator_fails_configuration() -> None:
    with pytest.raises(AdvisoryConfigurationError, match="changed canonical"):
        build_tier2_advisory(
            slice6_request("accelerator-mismatch"),
            slice6_query("MISSING_MSA"),
            slice6_runtime("MISSING_MSA"),
            slice6_policy(),
            (METHOD_SECONDARY_REF,),
        )


def test_authoritative_advisory_path_has_no_model_adapter_surface() -> None:
    source = inspect.getsource(slice6_service).lower()
    parameters = inspect.signature(build_tier2_advisory).parameters

    assert not {"model", "llm", "adapter"} & set(parameters)
    for prohibited in ("openai", "anthropic", "embedding", "faiss"):
        assert prohibited not in source


def test_rendered_prose_is_separate_and_cannot_modify_advisory_hash() -> None:
    result = build_tier2_advisory(
        slice6_request("render-boundary"),
        slice6_query("MISSING_MSA"),
        slice6_runtime("MISSING_MSA"),
        slice6_policy(),
    )
    before = result.output.advisory_hash

    rendered = RenderedArtifact(
        decision_id=result.output.advisory.decision_id,
        renderer_id="renderer.test",
        renderer_version="renderer.test.v1",
        rendered_text="Non-authoritative explanation.",
        generated_from_decision_hash=before,
        non_record_of_record=True,
    )

    assert rendered.generated_from_decision_hash == before
    assert result.output.advisory_hash == before
    assert "rendered_text" not in AdvisoryDecision.model_fields


def test_unregistered_advisory_directive_is_rejected() -> None:
    runtime = slice6_runtime("MISSING_MSA")
    target = next(
        item
        for item in runtime.route_rules
        if item.source_route_reason_id
        == slice6_policy().slice5_policy.slice4_policy.slice3_policy.route_reasons.msa_missing
    )
    invalid = target.model_copy(
        update={
            "next_step": DisplayDirective(
                template_id=TemplateId("action.unregistered"),
                params=(),
            )
        }
    )
    changed = runtime.model_copy(
        update={
            "route_rules": tuple(
                invalid if item.rule_ref == target.rule_ref else item
                for item in runtime.route_rules
            )
        }
    )

    with pytest.raises(AdvisoryConfigurationError, match="unknown template"):
        build_tier2_advisory(
            slice6_request("bad-directive"),
            slice6_query("MISSING_MSA"),
            changed,
            slice6_policy(),
        )


def test_identical_advisory_replays_byte_identically() -> None:
    policy = slice6_policy()
    request = slice6_request("replay")
    query = slice6_query("UNKNOWN_APPLICABILITY")
    runtime = slice6_runtime("UNKNOWN_APPLICABILITY")
    canonicalization = (
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    )

    first = build_tier2_advisory(request, query, runtime, policy)
    second = build_tier2_advisory(request, query, runtime, policy)

    assert canonical_bytes(first.output, canonicalization) == canonical_bytes(
        second.output,
        canonicalization,
    )
    assert first.output.advisory_hash == second.output.advisory_hash


def test_slice6_persists_explicit_schema_and_complete_payload(postgres_url: str) -> None:
    policy = slice6_policy()
    request = slice6_request("persisted")
    query = slice6_query("MISSING_MSA")
    runtime = slice6_runtime("MISSING_MSA")
    canonicalization = (
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy
    )
    store = PostgresRunStore(postgres_url, canonicalization)
    store.initialize()

    result = execute_tier2_advisory(request, query, runtime, policy, store)
    stored = store.load_run(request.run_id)

    assert stored is not None
    assert stored.schema_version == SLICE6_RUN_SCHEMA_VERSION
    assert stored.payload == canonical_bytes(result.output, canonicalization)
    assert stored.snapshot_payload == canonical_bytes(result.snapshot, canonicalization)
    assert stored.citation_payloads
    assert stored.bound_version_payloads


def test_documented_slice6_demo_runs_against_postgres(postgres_url: str) -> None:
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "tier2-advisory",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"output_kind": "TIER2_ADVISORY"' in completed.stdout
    assert '"status": "ADVISORY_NO_VERDICT"' in completed.stdout
