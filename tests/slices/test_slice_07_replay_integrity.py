from __future__ import annotations

import hashlib
import inspect
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import PostgresRunStore
from gptl.core.semantic_types import VersionId
from gptl.mie import replay as replay_module
from gptl.mie.replay import (
    ArtifactConfirmationReplayRecipe,
    ReplayIntegrityFailure,
    ReplayVerified,
    evaluate_pack_eligibility,
    execute_replayable_run,
    verify_persisted_replay,
)
from gptl.mie.schema import Tier1Output
from gptl.mie.slice2_service import execute_candidate_preservation
from gptl.slice2_fixture import ORIGINAL_AS_OF, ratified_runtime, slice2_policy, slice2_request
from gptl.slice4_fixture import (
    AS_OF,
    LATER_AS_OF,
    slice4_policy,
    slice4_request,
    slice4_runtime,
)
from gptl.slice7_fixture import (
    PACK_ROLLBACK_AS_OF,
    PACK_V1,
    PACK_V1_DEPRECATED_AT,
    PACK_V1_REVOKED_AT,
    PACK_V2,
    corrected_candidate_recipe,
    pack_lifecycle_catalog,
    pack_lifecycle_policy,
    replay_policy,
    replay_recipes,
)


def test_every_prior_slice_replays_exactly_after_store_reopen(postgres_url: str) -> None:
    policy = replay_policy()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    for recipe in replay_recipes():
        execution = execute_replayable_run(recipe, policy, store)
        reopened = PostgresRunStore(postgres_url, policy.canonicalization_policy)
        result = verify_persisted_replay(
            f"replay.slice7.{recipe.recipe_kind.lower()}",
            recipe.request.run_id,
            reopened,
            policy,
        )

        assert isinstance(result, ReplayVerified)
        assert result.status == "VERIFIED"
        assert result.source_run_schema_version == execution.schema_version
        assert result.bound_version_refs == execution.bound_versions
        assert result.output_hash == (
            execution.output.decision_hash
            if isinstance(execution.output, Tier1Output)
            else execution.output.advisory_hash
        )
        persisted = reopened.load_run(recipe.request.run_id)
        assert persisted is not None
        assert persisted.replay_capsule is not None


def test_identical_replay_is_byte_identical(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[5]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)

    first = verify_persisted_replay(
        "replay.slice7.determinism",
        recipe.request.run_id,
        store,
        policy,
    )
    second = verify_persisted_replay(
        "replay.slice7.determinism",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(first, ReplayVerified)
    assert isinstance(second, ReplayVerified)
    assert canonical_bytes(first, policy.canonicalization_policy) == canonical_bytes(
        second,
        policy.canonicalization_policy,
    )


def test_replay_has_no_network_or_implicit_latest_surface() -> None:
    source = inspect.getsource(replay_module).lower()
    parameters = inspect.signature(verify_persisted_replay).parameters

    assert not {"resolver", "network", "latest", "client"} & set(parameters)
    for prohibited in ("requests", "httpx", "urllib", "socket", "resolve_latest"):
        assert prohibited not in source


def test_missing_run_returns_governed_integrity_failure(postgres_url: str) -> None:
    policy = replay_policy()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    result = verify_persisted_replay(
        "replay.slice7.missing-run",
        "run.slice7.missing-run",
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.run_missing_reason_id


def test_run_without_exact_recipe_fails_closed(postgres_url: str) -> None:
    policy = replay_policy()
    slice_policy = slice2_policy()
    request = slice2_request("slice7-no-capsule", ORIGINAL_AS_OF)
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_candidate_preservation(request, ratified_runtime(), slice_policy, store)

    result = verify_persisted_replay(
        "replay.slice7.no-capsule",
        request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.capsule_missing_reason_id


def test_replay_capsule_and_run_commit_atomically(
    postgres_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[1]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    def fail_capsule_insert(*_: object) -> None:
        raise RuntimeError("simulated replay-capsule write failure")

    monkeypatch.setattr(store, "_insert_replay_capsule", fail_capsule_insert)
    with pytest.raises(RuntimeError, match="replay-capsule write failure"):
        execute_replayable_run(recipe, policy, store)

    assert store.load_run(recipe.request.run_id) is None


def test_database_rejects_replay_capsule_mutation(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[0]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)

    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute(
                "UPDATE gptl_replay_capsules SET payload = %s WHERE run_id = %s",
                (b"{}", recipe.request.run_id),
            )
    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="reject truncate"):
            connection.execute("TRUNCATE gptl_replay_capsules")


def test_tampered_replay_capsule_returns_integrity_failure(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[2]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    _bypass_update(
        postgres_url,
        "gptl_replay_capsules",
        "payload = %s",
        (b"{}",),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.tampered-capsule",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.stored_content_invalid_reason_id


def test_stale_run_payload_checksum_returns_stored_content_invalid(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[4]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    _bypass_update(
        postgres_url,
        "gptl_runs",
        "payload = %s",
        (b"{}",),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.stale-run-checksum",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.stored_content_invalid_reason_id


def test_unavailable_bound_content_returns_integrity_failure(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[3]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execution = execute_replayable_run(recipe, policy, store)
    missing = execution.bound_versions[0]
    with psycopg.connect(postgres_url) as connection:
        connection.execute("ALTER TABLE gptl_bound_versions DISABLE TRIGGER USER")
        connection.execute(
            "DELETE FROM gptl_bound_versions WHERE run_id = %s AND binding_id = %s",
            (recipe.request.run_id, missing.version_id),
        )
        connection.execute("ALTER TABLE gptl_bound_versions ENABLE TRIGGER USER")

    result = verify_persisted_replay(
        "replay.slice7.missing-bound-content",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.stored_content_invalid_reason_id


def test_validly_rehashed_output_tamper_is_caught_by_reexecution(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[4]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    tampered = b"{}"
    _bypass_update(
        postgres_url,
        "gptl_runs",
        "payload = %s, payload_hash = %s",
        (tampered, hashlib.sha256(tampered).hexdigest()),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.rehashed-output",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.replay_mismatch_reason_id


def test_unavailable_replay_algorithm_fails_closed(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[5]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    _bypass_update(
        postgres_url,
        "gptl_replay_capsules",
        "algorithm_id = %s",
        ("BUILD0_EXACT_REPLAY_REMOVED",),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.algorithm-unavailable",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.algorithm_unavailable_reason_id


def test_replay_policy_reference_mismatch_fails_closed(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[1]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    _bypass_update(
        postgres_url,
        "gptl_replay_capsules",
        "replay_policy_version_id = %s",
        ("policy.replay.replaced.v1",),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.policy-mismatch",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.recipe_invalid_reason_id


def test_replay_recipe_schema_mismatch_fails_closed(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[1]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    _bypass_update(
        postgres_url,
        "gptl_replay_capsules",
        "recipe_schema_version = %s",
        ("gptl.replay-recipe.removed",),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.recipe-schema-mismatch",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.recipe_invalid_reason_id


def test_cross_run_capsule_substitution_fails_closed(postgres_url: str) -> None:
    policy = replay_policy()
    target, source = replay_recipes()[2:4]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(target, policy, store)
    execute_replayable_run(source, policy, store)
    source_run = store.load_run(source.request.run_id)
    assert source_run is not None
    assert source_run.replay_capsule is not None
    source_capsule = source_run.replay_capsule
    _bypass_update(
        postgres_url,
        "gptl_replay_capsules",
        "payload = %s, payload_hash = %s",
        (source_capsule.payload, source_capsule.payload_hash),
        target.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.cross-run-capsule",
        target.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.recipe_invalid_reason_id


def test_noncanonical_replay_recipe_fails_closed(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[5]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    stored = store.load_run(recipe.request.run_id)
    assert stored is not None
    assert stored.replay_capsule is not None
    noncanonical = b" " + stored.replay_capsule.payload
    _bypass_update(
        postgres_url,
        "gptl_replay_capsules",
        "payload = %s, payload_hash = %s",
        (noncanonical, hashlib.sha256(noncanonical).hexdigest()),
        recipe.request.run_id,
    )

    result = verify_persisted_replay(
        "replay.slice7.noncanonical-recipe",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.recipe_invalid_reason_id


def test_reexecution_exception_returns_integrity_failure(
    postgres_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[2]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)

    def fail_reexecution(_: object) -> None:
        raise RuntimeError("simulated unavailable historical implementation")

    monkeypatch.setattr(replay_module, "_execute_recipe", fail_reexecution)
    result = verify_persisted_replay(
        "replay.slice7.execution-failure",
        recipe.request.run_id,
        store,
        policy,
    )

    assert isinstance(result, ReplayIntegrityFailure)
    assert result.reason_id == policy.replay_mismatch_reason_id


def test_explicit_pack_evolution_never_resolves_latest() -> None:
    catalog = pack_lifecycle_catalog()
    policy = pack_lifecycle_policy()

    rollback = evaluate_pack_eligibility(
        PACK_V1.version_id,
        PACK_ROLLBACK_AS_OF,
        catalog,
        policy,
    )
    current = evaluate_pack_eligibility(
        PACK_V2.version_id,
        PACK_ROLLBACK_AS_OF,
        catalog,
        policy,
    )
    deprecated = evaluate_pack_eligibility(
        PACK_V1.version_id,
        PACK_V1_DEPRECATED_AT,
        catalog,
        policy,
    )
    revoked = evaluate_pack_eligibility(
        PACK_V1.version_id,
        PACK_V1_REVOKED_AT,
        catalog,
        policy,
    )
    unknown = evaluate_pack_eligibility(
        VersionId("pack.lifecycle-reference.v999"),
        PACK_ROLLBACK_AS_OF,
        catalog,
        policy,
    )

    assert rollback.status == "ELIGIBLE"
    assert rollback.pack_ref == PACK_V1
    assert current.status == "ELIGIBLE"
    assert current.pack_ref == PACK_V2
    assert deprecated.status == "INELIGIBLE"
    assert deprecated.reason_id == policy.deprecated_reason_id
    assert revoked.status == "INELIGIBLE"
    assert revoked.reason_id == policy.revoked_reason_id
    assert unknown.pack_ref is None
    assert unknown.reason_id == policy.unavailable_reason_id


def test_correction_creates_new_version_and_run_without_rewriting_history(
    postgres_url: str,
) -> None:
    policy = replay_policy()
    original = replay_recipes()[1]
    corrected = corrected_candidate_recipe()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    original_execution = execute_replayable_run(original, policy, store)
    before = store.load_run(original.request.run_id)
    corrected_execution = execute_replayable_run(corrected, policy, store)
    after = store.load_run(original.request.run_id)

    assert before is not None
    assert after is not None
    assert before.payload == after.payload
    assert before.snapshot_payload == after.snapshot_payload
    assert original.runtime.intake.intake_ref in original_execution.bound_versions
    assert corrected.runtime.intake.intake_ref in corrected_execution.bound_versions
    assert (
        original.runtime.intake.intake_ref.version_id
        != corrected.runtime.intake.intake_ref.version_id
    )
    assert before.payload != canonical_bytes(
        corrected_execution.output,
        policy.canonicalization_policy,
    )
    assert isinstance(
        verify_persisted_replay(
            "replay.slice7.original-after-correction",
            original.request.run_id,
            store,
            policy,
        ),
        ReplayVerified,
    )


def test_later_attestation_revocation_changes_new_run_not_historical_replay(
    postgres_url: str,
) -> None:
    replay_contract = replay_policy()
    policy = slice4_policy()
    runtime = slice4_runtime(
        "HUMAN_ATTESTED",
        "LATE_ATTESTATION_REVOCATION",
        True,
        "NONE",
    )
    historical = ArtifactConfirmationReplayRecipe(
        recipe_kind="ARTIFACT_CONFIRMATION",
        request=slice4_request("slice7-revocation-historical", AS_OF),
        runtime=runtime,
        policy=policy,
    )
    current = historical.model_copy(
        update={"request": slice4_request("slice7-revocation-current", LATER_AS_OF)}
    )
    store = PostgresRunStore(postgres_url, replay_contract.canonicalization_policy)
    store.initialize()

    historical_execution = execute_replayable_run(historical, replay_contract, store)
    current_execution = execute_replayable_run(current, replay_contract, store)
    historical_replay = verify_persisted_replay(
        "replay.slice7.revocation-historical",
        historical.request.run_id,
        store,
        replay_contract,
    )

    assert isinstance(historical_execution.output, Tier1Output)
    assert historical_execution.output.decision.verdict == "METHOD_ARTIFACT"
    assert isinstance(current_execution.output, Tier1Output)
    assert current_execution.output.decision.verdict == "INDETERMINATE"
    assert isinstance(historical_replay, ReplayVerified)
    assert historical_replay.output_hash == historical_execution.output.decision_hash


def test_snapshot_bound_discriminator_supersession_replays_exactly(postgres_url: str) -> None:
    replay_contract = replay_policy()
    recipe = ArtifactConfirmationReplayRecipe(
        recipe_kind="ARTIFACT_CONFIRMATION",
        request=slice4_request("slice7-discriminator-supersession", AS_OF),
        runtime=slice4_runtime("STRUCTURED", "NONE", True, "SUPERSEDED"),
        policy=slice4_policy(),
    )
    store = PostgresRunStore(postgres_url, replay_contract.canonicalization_policy)
    store.initialize()

    execution = execute_replayable_run(recipe, replay_contract, store)
    result = verify_persisted_replay(
        "replay.slice7.discriminator-supersession",
        recipe.request.run_id,
        store,
        replay_contract,
    )

    assert isinstance(execution.output, Tier1Output)
    assert execution.output.decision.diagnostic_state_hash is not None
    assert isinstance(result, ReplayVerified)
    assert result.output_hash == execution.output.decision_hash


def test_cross_process_replay_uses_only_persisted_capsule(postgres_url: str) -> None:
    policy = replay_policy()
    recipe = replay_recipes()[3]
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_replayable_run(recipe, policy, store)
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "replay-integrity",
            "--database-url",
            postgres_url,
            "--run-id",
            recipe.request.run_id,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"status": "VERIFIED"' in completed.stdout


def test_documented_slice7_demo_replays_all_prior_slices(postgres_url: str) -> None:
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "replay-integrity",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.count('"status": "VERIFIED"') == len(replay_recipes())


def test_every_documented_demo_requires_an_explicit_database_url() -> None:
    repository_root = Path(__file__).parents[2]
    build_plan = (repository_root / "docs" / "GPTL_BUILD_PLAN_v0.15.md").read_text(encoding="utf-8")
    demo_rows = tuple(
        line
        for line in build_plan.splitlines()
        if line.startswith(tuple(f"| {n} |" for n in range(1, 8)))
    )

    assert len(demo_rows) == len(range(1, 8))
    assert all('--database-url "$GPTL_DATABASE_URL"' in row for row in demo_rows)


def _bypass_update(
    database_url: str,
    table_name: str,
    assignment_sql: str,
    assignment_values: tuple[object, ...],
    run_id: str,
) -> None:
    if table_name not in {"gptl_replay_capsules", "gptl_runs"}:
        raise ValueError("test tamper helper received an unapproved table")
    with psycopg.connect(database_url) as connection:
        connection.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER USER")
        connection.execute(
            f"UPDATE {table_name} SET {assignment_sql} WHERE run_id = %s",
            (*assignment_values, run_id),
        )
        connection.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER USER")
