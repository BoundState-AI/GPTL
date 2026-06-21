from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import PersistenceIntegrityError, PostgresRunStore
from gptl.core.pack_registry import ExactPackRegistry
from gptl.mie.service import (
    PackAvailableForLaterSlice,
    build_safe_refusal,
    execute_safe_refusal,
)
from gptl.slice1_fixture import (
    empty_pack_registry,
    safe_refusal_policy,
    safe_refusal_request,
)


def test_absent_pack_produces_deterministic_preflight_refusal() -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()

    first = build_safe_refusal(request, empty_pack_registry(), policy)
    second = build_safe_refusal(request, empty_pack_registry(), policy)

    assert canonical_bytes(first.output, policy.canonicalization_policy) == canonical_bytes(
        second.output, policy.canonicalization_policy
    )
    assert first.output.decision_hash == second.output.decision_hash
    assert first.output.decision.verdict == "REFUSED"
    assert first.output.decision.refusal_type == "PACK_VERSION_UNAVAILABLE"
    assert first.output.decision.context.context_kind == "PREFLIGHT"
    assert first.output.decision.operational_mode == "RESEARCH_ONLY"
    assert first.output.decision.method_ref is None
    assert first.output.decision.assessments == ()
    assert first.output.decision.citations == ()
    serialized = canonical_bytes(first.output, policy.canonicalization_policy)
    assert b"pack_ref" not in serialized
    assert b"engine_policy_ref" not in serialized
    assert b"snapshot" not in serialized


def test_available_exact_pack_stops_at_later_slice_boundary() -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    registry = ExactPackRegistry(
        available_pack_ids=(request.requested_pack_id,)
    )

    with pytest.raises(PackAvailableForLaterSlice):
        build_safe_refusal(request, registry, policy)


def test_store_has_no_non_postgres_fallback() -> None:
    with pytest.raises(ValueError, match="must select PostgreSQL"):
        PostgresRunStore("file:embedded.db", safe_refusal_policy().canonicalization_policy)


def test_postgres_persists_atomic_run_and_audit_across_connections(
    postgres_url: str,
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    result = execute_safe_refusal(request, empty_pack_registry(), policy, store)
    reopened = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    persisted = reopened.load_run(request.run_id)

    assert persisted is not None
    expected = canonical_bytes(result.output, policy.canonicalization_policy)
    assert persisted.payload == expected
    assert persisted.payload_hash == hashlib.sha256(expected).hexdigest()
    assert len(persisted.audit_payloads) == 1


def test_documented_demo_runs_against_postgres(postgres_url: str) -> None:
    repository_root = Path(__file__).parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "run_slice.py"),
            "safe-refusal",
            "--database-url",
            postgres_url,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"verdict": "REFUSED"' in completed.stdout
    assert '"context_kind": "PREFLIGHT"' in completed.stdout


def test_failure_between_run_and_audit_insert_rolls_back(
    postgres_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    result = build_safe_refusal(request, empty_pack_registry(), policy)

    def fail_after_run_insert(*_: object) -> None:
        raise RuntimeError("simulated audit write failure")

    monkeypatch.setattr(store, "_insert_audit_events", fail_after_run_insert)
    with pytest.raises(RuntimeError, match="simulated"):
        store.persist_preflight_run(request.run_id, result.output, result.audit_events)

    assert store.load_run(request.run_id) is None
    with psycopg.connect(postgres_url) as connection:
        assert connection.execute("SELECT count(*) FROM gptl_audit_events").fetchone()[0] == 0


def test_store_rejects_a_well_formed_but_incorrect_decision_hash(
    postgres_url: str,
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    result = build_safe_refusal(request, empty_pack_registry(), policy)
    invalid_output = result.output.model_copy(update={"decision_hash": "f" * 64})

    with pytest.raises(PersistenceIntegrityError, match="decision checksum"):
        store.persist_preflight_run(
            request.run_id, invalid_output, result.audit_events
        )
    assert store.load_run(request.run_id) is None


def test_database_rejects_update_and_delete_of_committed_rows(
    postgres_url: str,
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_safe_refusal(request, empty_pack_registry(), policy, store)

    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute(
                "UPDATE gptl_runs SET case_id = %s WHERE run_id = %s",
                ("case.changed", request.run_id),
            )
    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute(
                "DELETE FROM gptl_audit_events WHERE run_id = %s", (request.run_id,)
            )
    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute("DELETE FROM gptl_schema_migrations")


@pytest.mark.parametrize(
    "table,id_column,id_value",
    (
        ("gptl_snapshots", None, None),
        ("gptl_citations", "citation_id", "citation.fabricated"),
        ("gptl_bound_versions", "binding_id", "binding.fabricated"),
    ),
)
def test_database_rejects_fabricated_preflight_bindings(
    postgres_url: str, table: str, id_column: str | None, id_value: str | None
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_safe_refusal(request, empty_pack_registry(), policy, store)

    payload = b"{}"
    payload_hash = hashlib.sha256(payload).hexdigest()
    columns = "run_id, payload_hash, payload"
    values: tuple[object, ...] = (request.run_id, payload_hash, payload)
    if id_column is not None:
        columns = f"{id_column}, " + columns
        values = (id_value,) + values
    placeholders = ", ".join(("%s",) * len(values))
    statement = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="PREFLIGHT run cannot bind"):
            connection.execute(statement, values)
