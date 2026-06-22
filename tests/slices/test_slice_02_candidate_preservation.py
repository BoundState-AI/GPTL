from __future__ import annotations

import hashlib
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import (
    BOUND_VERSION_RECORD_TYPE,
    HASH_ALGORITHM,
    SNAPSHOT_AUDIT_RECORD_TYPE,
    SNAPSHOT_RECORD_TYPE,
    SNAPSHOT_RUN_SCHEMA_VERSION,
    TIER1_OUTPUT_RECORD_TYPE,
    PersistenceIntegrityError,
    PostgresRunStore,
)
from gptl.core.ratification import (
    IntakeRecord,
    evaluate_ratification_gate,
    intake_value_hash,
)
from gptl.mie.candidates import CandidatePackConfigurationError, load_candidate_set
from gptl.mie.predicates import NumericValue
from gptl.mie.schema import RefusalDecision, Tier1Output, Tier2Output
from gptl.mie.service import build_safe_refusal
from gptl.mie.slice2_service import (
    CandidateSetReadyForLaterSlice,
    PackVersionBindingError,
    Slice2Runtime,
    build_candidate_preservation,
    execute_candidate_preservation,
)
from gptl.slice1_fixture import empty_pack_registry, safe_refusal_policy, safe_refusal_request
from gptl.slice2_fixture import (
    FIELD_ENVIRONMENT,
    FIELD_MODE,
    FIELD_TEMPERATURE,
    ORIGINAL_AS_OF,
    REVOKED_AS_OF,
    UNIT_CELSIUS,
    UNIT_MM,
    canonicalization_policy,
    invalid_unit_pack,
    ratified_runtime,
    revoked_runtime,
    slice2_policy,
    slice2_request,
    tied_selection_pack,
    unratified_runtime,
)


def _runtime_with_temperature(
    value: str,
    update_hash: bool,
    unit_id: str = UNIT_CELSIUS,
) -> Slice2Runtime:
    runtime = ratified_runtime()
    replacement_value = NumericValue(
        kind="NUMERIC",
        value=Decimal(value),
        unit_id=unit_id,
    )
    values = []
    for intake_value in runtime.intake.values:
        if intake_value.field_id != FIELD_TEMPERATURE:
            values.append(intake_value)
            continue
        replacement_hash = intake_value.value_hash
        if update_hash:
            replacement_hash = intake_value_hash(
                intake_value.field_id,
                replacement_value,
                canonicalization_policy(),
            )
        values.append(
            intake_value.model_copy(
                update={
                    "value": replacement_value,
                    "value_hash": replacement_hash,
                }
            )
        )
    intake = IntakeRecord(intake_ref=runtime.intake.intake_ref, values=tuple(values))
    return runtime.model_copy(update={"intake": intake})


def test_unknown_applicability_is_preserved_and_blocks_negative_conclusion() -> None:
    policy = slice2_policy()
    runtime = ratified_runtime()

    result = build_candidate_preservation(slice2_request(), runtime, policy)

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert decision.context.context_kind == "SNAPSHOT_BOUND"
    assert decision.refusal_type == "MISSING_REQUIRED_EVIDENCE"
    assert decision.missing_field_ids == (FIELD_ENVIRONMENT,)
    assessments = {item.candidate_ref.logical_id: item for item in decision.assessments}
    assert set(assessments) == {
        item.failure_mode_ref.logical_id for item in runtime.pack.candidates
    }
    assert assessments["failure.unknown"].applicability == "UNKNOWN"
    assert assessments["failure.unknown"].status == "APPLICABILITY_UNRESOLVED"
    assert assessments["failure.false"].status == "ELIMINATED"
    assert assessments["failure.group-low"].status == "OPEN_UNASSESSED"
    assert assessments["failure.group-high"].status == "ELIMINATED"
    assert assessments["failure.true-a"].status == "OPEN_UNASSESSED"
    assert assessments["failure.true-b"].status == "OPEN_UNASSESSED"
    assert all(item.signature_match_score is None for item in decision.assessments)
    assert all(item.candidate_support_score is None for item in decision.assessments)
    assert tuple(item.record_ref.logical_id for item in decision.citations) == (
        "predicate.failure.false",
    )


def test_invalid_pack_returns_configuration_refusal() -> None:
    policy = slice2_policy()
    runtime = ratified_runtime(pack=invalid_unit_pack())

    result = build_candidate_preservation(slice2_request("invalid"), runtime, policy)

    assert isinstance(result.output, Tier1Output)
    assert result.output.decision.refusal_type == "CONFIGURATION_INVALID"
    assert result.output.decision.assessments == ()
    assert result.output.decision.configuration_issues is None


def test_runtime_invalid_applicability_surfaces_candidate_error_and_evidence(
    postgres_url: str,
) -> None:
    policy = slice2_policy()
    runtime = _runtime_with_temperature("25", update_hash=True, unit_id=UNIT_MM)
    request = slice2_request("runtime-invalid")
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    result = execute_candidate_preservation(request, runtime, policy, store)
    persisted = store.load_run(request.run_id)

    assert isinstance(result.output, Tier1Output)
    decision = result.output.decision
    assert decision.refusal_type == "CONFIGURATION_INVALID"
    assert decision.configuration_issues is not None
    issues = {item.candidate_ref.logical_id: item for item in decision.configuration_issues}
    assert set(issues) == {"failure.false", "failure.true-a"}
    assert all(item.applicability_evaluation.truth == "INVALID" for item in issues.values())
    assert all(
        item.applicability_evaluation.error_code == "UNIT_MISMATCH" for item in issues.values()
    )
    assert all(
        item.applicability_evaluation.predicate_ref in item.evidence_refs
        for item in issues.values()
    )
    assert {item.record_ref.logical_id for item in decision.citations} >= {
        "predicate.failure.false",
        "predicate.failure.true-a",
    }
    assert persisted is not None
    assert b'"configuration_issues"' in persisted.payload
    assert b'"error_code":"UNIT_MISMATCH"' in persisted.payload


def test_integrity_failure_precedes_ratification_state_and_candidate_loading() -> None:
    policy = slice2_policy()
    invalid_runtime = _runtime_with_temperature("9999999999999999999", update_hash=False)
    valid = build_candidate_preservation(
        slice2_request("integrity-valid"), ratified_runtime(), policy
    )

    invalid = build_candidate_preservation(
        slice2_request("integrity-invalid"),
        invalid_runtime,
        policy,
    )

    assert isinstance(invalid.output, Tier1Output)
    assert invalid.output.decision.refusal_type == "INTEGRITY_FAILURE"
    assert invalid.output.decision.assessments == ()
    assert invalid.output.decision.configuration_issues is None
    assert invalid.snapshot.ratification_state_hash != valid.snapshot.ratification_state_hash


def test_selection_rank_tie_fails_pack_validation() -> None:
    pack = tied_selection_pack()

    with pytest.raises(CandidatePackConfigurationError, match="precedence-rank tie"):
        load_candidate_set(pack, (), canonicalization_policy())


def test_unratified_human_input_returns_non_dispositional_advisory() -> None:
    policy = slice2_policy()
    runtime = unratified_runtime()

    result = build_candidate_preservation(slice2_request("unratified"), runtime, policy)

    assert isinstance(result.output, Tier2Output)
    advisory = result.output.advisory
    assert advisory.status == "ADVISORY_NO_VERDICT"
    assert advisory.proposed_field_ids == (FIELD_MODE,)
    assert advisory.candidate_failure_mode_refs == runtime.pack.manifest.candidate_refs
    assert advisory.applicability_evaluations == ()
    assert advisory.non_record_of_record is True
    assert advisory.dispositional is False


def test_scalar_intake_rejects_multiple_values_for_one_field() -> None:
    runtime = ratified_runtime()
    mode = next(item for item in runtime.intake.values if item.field_id == FIELD_MODE)
    duplicate = mode.model_copy(update={"value_id": "value.mode.duplicate"})
    values = tuple(
        sorted(
            (*runtime.intake.values, duplicate),
            key=lambda item: (item.field_id, item.value_id),
        )
    )

    with pytest.raises(ValidationError, match="cannot have multiple values"):
        IntakeRecord(intake_ref=runtime.intake.intake_ref, values=values)


def test_ratification_lookup_requires_the_exact_governed_event_identity() -> None:
    runtime = ratified_runtime()
    active = runtime.ratification_events[0]
    conflicting_ref = active.event_ref.model_copy(
        update={
            "logical_id": "ratification.unrelated",
            "content_hash": "f" * 64,
        }
    )
    unrelated = active.model_copy(update={"event_ref": conflicting_ref})

    result = evaluate_ratification_gate(
        runtime.intake,
        (active, unrelated),
        runtime.pack.manifest.pack_ref,
        slice2_request().as_of_time,
        canonicalization_policy(),
    )

    assert result.eligible is True
    assert result.unratified_field_ids == ()


def test_backdated_revocation_applies_only_after_its_recorded_time() -> None:
    runtime = revoked_runtime()
    active, revocation = runtime.ratification_events
    backdated = revocation.model_copy(update={"effective_at": ORIGINAL_AS_OF})
    backdated_runtime = runtime.model_copy(update={"ratification_events": (active, backdated)})

    historical = build_candidate_preservation(
        slice2_request("backdated-historical", ORIGINAL_AS_OF),
        backdated_runtime,
        slice2_policy(),
    )
    current = build_candidate_preservation(
        slice2_request("backdated-current", REVOKED_AS_OF),
        backdated_runtime,
        slice2_policy(),
    )

    assert isinstance(historical.output, Tier1Output)
    assert historical.output.decision.refusal_type == "MISSING_REQUIRED_EVIDENCE"
    assert isinstance(current.output, Tier2Output)
    assert current.output.advisory.proposed_field_ids == (FIELD_MODE,)


def test_pack_version_mismatch_raises_named_binding_error() -> None:
    request = slice2_request("pack-mismatch").model_copy(
        update={"requested_pack_version_id": "pack.other.v1"}
    )

    with pytest.raises(PackVersionBindingError, match="exact loaded pack version"):
        build_candidate_preservation(request, ratified_runtime(), slice2_policy())


def test_refusal_context_scoping_rejects_cross_boundary_records() -> None:
    preflight_policy = safe_refusal_policy()
    preflight = build_safe_refusal(
        safe_refusal_request(),
        empty_pack_registry(),
        preflight_policy,
    ).output.decision
    bound = build_candidate_preservation(
        slice2_request("context-bound"),
        ratified_runtime(),
        slice2_policy(),
    ).output
    runtime_invalid = build_candidate_preservation(
        slice2_request("context-issue"),
        _runtime_with_temperature("25", update_hash=True, unit_id=UNIT_MM),
        slice2_policy(),
    ).output
    assert isinstance(bound, Tier1Output)
    assert isinstance(runtime_invalid, Tier1Output)
    assert runtime_invalid.decision.configuration_issues is not None
    invalid_preflight_values = (
        ("method_ref", bound.decision.method_ref),
        ("assessments", bound.decision.assessments),
        ("citations", bound.decision.citations),
        ("configuration_issues", runtime_invalid.decision.configuration_issues),
    )
    for field, value in invalid_preflight_values:
        payload = preflight.model_dump(mode="python")
        payload[field] = value
        with pytest.raises(ValidationError, match="preflight refusal"):
            RefusalDecision.model_validate(
                payload,
                context={"canonicalization_policy": preflight_policy.canonicalization_policy},
            )

    missing_method = bound.decision.model_dump(mode="python")
    missing_method["method_ref"] = None
    with pytest.raises(ValidationError, match="snapshot-bound refusal requires"):
        RefusalDecision.model_validate(
            missing_method,
            context={"canonicalization_policy": canonicalization_policy()},
        )

    wrong_refusal = bound.decision.model_dump(mode="python")
    wrong_refusal["configuration_issues"] = runtime_invalid.decision.configuration_issues
    with pytest.raises(ValidationError, match="require CONFIGURATION_INVALID"):
        RefusalDecision.model_validate(
            wrong_refusal,
            context={"canonicalization_policy": canonicalization_policy()},
        )


def test_fully_ratified_candidate_set_reaches_slice_3_boundary() -> None:
    policy = slice2_policy()
    runtime = ratified_runtime(include_environment=True)

    with pytest.raises(CandidateSetReadyForLaterSlice) as raised:
        build_candidate_preservation(slice2_request("resolved"), runtime, policy)

    candidate_set = raised.value.candidate_set
    assert candidate_set.has_unknown is False
    assert candidate_set.has_invalid is False
    assert tuple(item.logical_id for item in candidate_set.preserved_candidate_refs) == (
        "failure.group-low",
        "failure.true-a",
        "failure.true-b",
        "failure.unknown",
    )


def test_snapshot_binds_every_decision_effective_version() -> None:
    policy = slice2_policy()
    runtime = ratified_runtime()

    result = build_candidate_preservation(slice2_request("snapshot"), runtime, policy)

    bound = {
        (item.logical_id, item.version_id, item.content_hash)
        for item in result.snapshot.bound_versions
    }
    expected = {
        (runtime.pack.manifest.pack_ref.logical_id, runtime.pack.manifest.pack_ref.version_id),
        (
            runtime.pack.engine_policy.policy_ref.logical_id,
            runtime.pack.engine_policy.policy_ref.version_id,
        ),
        (runtime.pack.manifest.method_ref.logical_id, runtime.pack.manifest.method_ref.version_id),
        (
            runtime.pack.field_registry.registry_ref.logical_id,
            runtime.pack.field_registry.registry_ref.version_id,
        ),
        (
            runtime.pack.unit_registry.registry_ref.logical_id,
            runtime.pack.unit_registry.registry_ref.version_id,
        ),
        (runtime.intake.intake_ref.logical_id, runtime.intake.intake_ref.version_id),
        *(
            (candidate.failure_mode_ref.logical_id, candidate.failure_mode_ref.version_id)
            for candidate in runtime.pack.candidates
        ),
        *(
            (candidate.predicate_ref.logical_id, candidate.predicate_ref.version_id)
            for candidate in runtime.pack.candidates
        ),
        *(
            (event.event_ref.logical_id, event.event_ref.version_id)
            for event in runtime.ratification_events
        ),
    }
    assert expected.issubset({(logical_id, version_id) for logical_id, version_id, _ in bound})
    assert result.snapshot.ratification_events == runtime.ratification_events
    assert result.bound_versions == result.snapshot.bound_versions


def test_revocation_changes_new_run_without_rewriting_historical_run(
    postgres_url: str,
) -> None:
    policy = slice2_policy()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    original_request = slice2_request("historical", ORIGINAL_AS_OF)
    original = execute_candidate_preservation(
        original_request,
        ratified_runtime(),
        policy,
        store,
    )
    persisted_before = store.load_run(original_request.run_id)

    revoked = build_candidate_preservation(
        slice2_request("revoked", REVOKED_AS_OF),
        revoked_runtime(),
        policy,
    )
    historical_as_of = build_candidate_preservation(
        slice2_request("historical-replay", ORIGINAL_AS_OF),
        revoked_runtime(),
        policy,
    )
    persisted_after = store.load_run(original_request.run_id)

    assert isinstance(original.output, Tier1Output)
    assert isinstance(revoked.output, Tier2Output)
    assert revoked.output.advisory.proposed_field_ids == (FIELD_MODE,)
    assert isinstance(historical_as_of.output, Tier1Output)
    assert historical_as_of.output.decision.refusal_type == "MISSING_REQUIRED_EVIDENCE"
    assert (
        historical_as_of.snapshot.ratification_state_hash
        == original.snapshot.ratification_state_hash
    )
    assert revoked.snapshot.ratification_state_hash != original.snapshot.ratification_state_hash
    assert persisted_before is not None
    assert persisted_after is not None
    assert persisted_after.payload == persisted_before.payload
    assert persisted_after.snapshot_payload == persisted_before.snapshot_payload


def test_snapshot_bound_run_persists_and_reloads_complete_record(
    postgres_url: str,
) -> None:
    policy = slice2_policy()
    request = slice2_request("persisted")
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    result = execute_candidate_preservation(request, ratified_runtime(), policy, store)
    reopened = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    stored = reopened.load_run(request.run_id)

    assert stored is not None
    assert stored.context_kind == "SNAPSHOT_BOUND"
    assert stored.record_type == TIER1_OUTPUT_RECORD_TYPE
    assert stored.schema_version == SNAPSHOT_RUN_SCHEMA_VERSION
    assert stored.hash_algorithm == HASH_ALGORITHM
    assert stored.payload == canonical_bytes(result.output, policy.canonicalization_policy)
    assert stored.snapshot_payload == canonical_bytes(
        result.snapshot,
        policy.canonicalization_policy,
    )
    assert len(stored.audit_payloads) == 1
    assert len(stored.citation_payloads) == len(result.output.decision.citations)
    assert len(stored.bound_version_payloads) == len(result.bound_versions)


def test_store_retains_verified_read_compatibility_with_slice2_v1(
    postgres_url: str,
) -> None:
    policy = slice2_policy()
    request = slice2_request("legacy-v1")
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    payload = b"{}"
    payload_hash = hashlib.sha256(payload).hexdigest()
    legacy_schema = "gptl.slice2.v1"

    with psycopg.connect(postgres_url) as connection:
        connection.execute(
            """
            INSERT INTO gptl_runs (
                run_id, case_id, context_kind, as_of_time, record_type,
                schema_version, hash_algorithm, payload_hash, payload,
                audit_count, snapshot_count, citation_count, bound_version_count,
                replay_capsule_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request.run_id,
                request.case_id,
                "SNAPSHOT_BOUND",
                request.as_of_time,
                TIER1_OUTPUT_RECORD_TYPE,
                legacy_schema,
                HASH_ALGORITHM,
                payload_hash,
                payload,
                1,
                1,
                0,
                1,
                0,
            ),
        )
        connection.execute(
            """
            INSERT INTO gptl_snapshots (
                run_id, payload_hash, payload, record_type, schema_version, hash_algorithm
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                request.run_id,
                payload_hash,
                payload,
                SNAPSHOT_RECORD_TYPE,
                legacy_schema,
                HASH_ALGORITHM,
            ),
        )
        connection.execute(
            """
            INSERT INTO gptl_bound_versions (
                binding_id, run_id, payload_hash, payload, record_type,
                schema_version, hash_algorithm
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "binding.legacy-v1",
                request.run_id,
                payload_hash,
                payload,
                BOUND_VERSION_RECORD_TYPE,
                legacy_schema,
                HASH_ALGORITHM,
            ),
        )
        connection.execute(
            """
            INSERT INTO gptl_audit_events (
                event_id, run_id, sequence, record_type, schema_version,
                hash_algorithm, payload_hash, payload
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request.audit_event_id,
                request.run_id,
                0,
                SNAPSHOT_AUDIT_RECORD_TYPE,
                legacy_schema,
                HASH_ALGORITHM,
                payload_hash,
                payload,
            ),
        )

    stored = store.load_run(request.run_id)

    assert stored is not None
    assert stored.schema_version == legacy_schema
    assert stored.snapshot_payload == payload
    assert stored.bound_version_payloads == (payload,)


def test_documented_candidate_preservation_demo_runs_against_postgres(
    postgres_url: str,
) -> None:
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "candidate-preservation",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"refusal_type": "MISSING_REQUIRED_EVIDENCE"' in completed.stdout
    assert '"context_kind": "SNAPSHOT_BOUND"' in completed.stdout


def test_snapshot_write_failure_rolls_back_every_dependent_record(
    postgres_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = slice2_policy()
    request = slice2_request("rollback")
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    result = build_candidate_preservation(request, ratified_runtime(), policy)

    def fail_after_snapshot_and_citations(*_: object) -> None:
        raise RuntimeError("simulated bound-version write failure")

    monkeypatch.setattr(store, "_insert_bound_versions", fail_after_snapshot_and_citations)
    with pytest.raises(RuntimeError, match="simulated"):
        store.persist_snapshot_run(
            request.run_id,
            result.output,
            result.snapshot,
            result.audit_events,
            result.bound_versions,
            SNAPSHOT_RUN_SCHEMA_VERSION,
        )

    with psycopg.connect(postgres_url) as connection:
        for table_name in (
            "gptl_runs",
            "gptl_snapshots",
            "gptl_citations",
            "gptl_bound_versions",
            "gptl_audit_events",
        ):
            count = connection.execute(f"SELECT count(*) FROM {table_name}").fetchone()
            assert count == (0,)


def test_database_rejects_incomplete_snapshot_bound_commit(postgres_url: str) -> None:
    policy = slice2_policy()
    request = slice2_request("incomplete")
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    payload = b"{}"
    payload_hash = hashlib.sha256(payload).hexdigest()

    connection = psycopg.connect(postgres_url)
    try:
        with pytest.raises(psycopg.Error, match="snapshot-bound record counts"):
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO gptl_runs (
                        run_id, case_id, context_kind, as_of_time, record_type,
                        schema_version, hash_algorithm, payload_hash, payload,
                        audit_count, snapshot_count, citation_count,
                        bound_version_count, replay_capsule_count
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        request.run_id,
                        request.case_id,
                        "SNAPSHOT_BOUND",
                        request.as_of_time,
                        TIER1_OUTPUT_RECORD_TYPE,
                        SNAPSHOT_RUN_SCHEMA_VERSION,
                        HASH_ALGORITHM,
                        payload_hash,
                        payload,
                        1,
                        1,
                        0,
                        1,
                        0,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO gptl_audit_events (
                        event_id, run_id, sequence, record_type, schema_version,
                        hash_algorithm, payload_hash, payload
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        request.audit_event_id,
                        request.run_id,
                        0,
                        "SNAPSHOT_DECISION_AUDIT_EVENT",
                        SNAPSHOT_RUN_SCHEMA_VERSION,
                        HASH_ALGORITHM,
                        payload_hash,
                        payload,
                    ),
                )
    finally:
        connection.close()


def test_store_rejects_output_snapshot_hash_mismatch(postgres_url: str) -> None:
    policy = slice2_policy()
    request = slice2_request("hash-mismatch")
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    result = build_candidate_preservation(request, ratified_runtime(), policy)
    assert isinstance(result.output, Tier1Output)
    invalid_context = result.output.decision.context.model_copy(
        update={"knowledge_snapshot_hash": "f" * 64}
    )
    invalid_decision = result.output.decision.model_copy(update={"context": invalid_context})
    invalid_output = result.output.model_copy(
        update={
            "decision": invalid_decision,
            "decision_hash": "f" * 64,
        }
    )

    with pytest.raises(PersistenceIntegrityError, match="output checksum"):
        store.persist_snapshot_run(
            request.run_id,
            invalid_output,
            result.snapshot,
            result.audit_events,
            result.bound_versions,
            SNAPSHOT_RUN_SCHEMA_VERSION,
        )
