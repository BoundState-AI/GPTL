from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import psycopg
import pytest
from psycopg import sql

from gptl.core.canonical import canonical_bytes, canonical_sha256
from gptl.core.pack_registry import ExactPackRegistry
from gptl.core.persistence import (
    BUILD0_WRITER_LOCK_NAME,
    BUILD0_WRITER_LOCK_NAMESPACE,
    HASH_ALGORITHM,
    PREFLIGHT_AUDIT_RECORD_TYPE,
    SCHEMA_VERSION,
    TIER1_OUTPUT_RECORD_TYPE,
    PersistenceIntegrityError,
    PostgresRunStore,
)
from gptl.mie.service import (
    PackAvailableForLaterSlice,
    SafeRefusalRequest,
    build_safe_refusal,
    execute_safe_refusal,
)
from gptl.slice1_fixture import (
    empty_pack_registry,
    safe_refusal_policy,
    safe_refusal_request,
)


def _insert_direct_complete_run(
    postgres_url: str,
    request: SafeRefusalRequest,
    run_metadata: tuple[str, str, str],
    audit_metadata: tuple[str, str, str],
) -> None:
    payload = b"{}"
    payload_hash = hashlib.sha256(payload).hexdigest()
    with psycopg.connect(postgres_url) as connection:
        connection.execute(
            """
            INSERT INTO gptl_runs (
                run_id, case_id, context_kind, as_of_time, record_type,
                schema_version, hash_algorithm, payload_hash, payload, audit_count,
                snapshot_count, citation_count, bound_version_count,
                replay_capsule_count
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                request.run_id,
                request.case_id,
                "PREFLIGHT",
                request.as_of_time,
                *run_metadata,
                payload_hash,
                payload,
                1,
                0,
                0,
                0,
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
                *audit_metadata,
                payload_hash,
                payload,
            ),
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
    assert (
        canonical_sha256(first.output.decision, policy.canonicalization_policy)
        == "41a41a3d3e171f65dd509de228dee114b2e2375282388392fe51330f3666c995"
    )


def test_available_exact_pack_stops_at_later_slice_boundary() -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    registry = ExactPackRegistry(available_pack_ids=(request.requested_pack_id,))

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
    assert persisted.record_type == TIER1_OUTPUT_RECORD_TYPE
    assert persisted.schema_version == SCHEMA_VERSION
    assert persisted.hash_algorithm == HASH_ALGORITHM
    assert len(persisted.audit_payloads) == 1


def test_duplicate_run_id_is_not_an_idempotent_write(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    result = execute_safe_refusal(request, empty_pack_registry(), policy, store)
    with pytest.raises(psycopg.errors.UniqueViolation):
        execute_safe_refusal(request, empty_pack_registry(), policy, store)

    persisted = store.load_run(request.run_id)
    assert persisted is not None
    assert persisted.payload == canonical_bytes(result.output, policy.canonicalization_policy)


def test_store_rejects_a_concurrent_build0_writer(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()

    with psycopg.connect(postgres_url) as connection:
        with connection.transaction():
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s), hashtext(%s))",
                (BUILD0_WRITER_LOCK_NAMESPACE, BUILD0_WRITER_LOCK_NAME),
            )
            with pytest.raises(PersistenceIntegrityError, match="concurrent Build 0 writer"):
                execute_safe_refusal(request, empty_pack_registry(), policy, store)

    assert store.load_run(request.run_id) is None


def test_migrations_are_ordered_checksummed_and_idempotent(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)

    store.initialize()
    store.initialize()

    with psycopg.connect(postgres_url) as connection:
        rows = connection.execute(
            "SELECT migration_id, migration_hash FROM gptl_schema_migrations ORDER BY migration_id"
        ).fetchall()
    assert [migration_id for migration_id, _ in rows] == [
        "0001_slice_1",
        "0002_persistence_invariants",
        "0003_snapshot_bound_runs",
        "0004_replay_capsules",
        "0005_build1_capability_scope",
        "0006_build1_sources",
    ]
    assert all(len(payload_hash.strip()) == 64 for _, payload_hash in rows)


def test_initialize_rejects_empty_migration_history(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    with psycopg.connect(postgres_url) as connection:
        connection.execute(
            """
            CREATE TABLE gptl_schema_migrations (
                migration_id text PRIMARY KEY,
                migration_hash char(64) NOT NULL
            )
            """
        )

    with pytest.raises(PersistenceIntegrityError, match="exact prefix"):
        store.initialize()


def test_initialize_rejects_migration_checksum_drift(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    bootstrap = store._load_migrations()[0]
    with psycopg.connect(postgres_url) as connection:
        connection.execute(bootstrap.payload)
        connection.execute(
            "INSERT INTO gptl_schema_migrations (migration_id, migration_hash) VALUES (%s, %s)",
            (bootstrap.migration_id, "0" * 64),
        )

    with pytest.raises(PersistenceIntegrityError, match="checksum mismatch: 0001"):
        store.initialize()


def test_store_honors_connection_selected_schema(postgres_url: str) -> None:
    schema = "gptl_isolated"
    with psycopg.connect(postgres_url) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    schema_option = quote(f"-csearch_path={schema}")
    isolated_url = f"{postgres_url}?options={schema_option}"
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(isolated_url, policy.canonicalization_policy)

    store.initialize()
    execute_safe_refusal(request, empty_pack_registry(), policy, store)

    assert store.load_run(request.run_id) is not None
    with psycopg.connect(postgres_url) as connection:
        assert connection.execute(
            "SELECT to_regclass(%s)", (f"{schema}.gptl_runs",)
        ).fetchone() == (f"{schema}.gptl_runs",)


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


def test_persisted_run_is_readable_from_a_fresh_process(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_safe_refusal(request, empty_pack_registry(), policy, store)
    program = """
import sys
from gptl.core.persistence import PostgresRunStore
from gptl.slice1_fixture import safe_refusal_policy

policy = safe_refusal_policy()
store = PostgresRunStore(sys.argv[1], policy.canonicalization_policy)
run = store.load_run(sys.argv[2])
raise SystemExit(0 if run is not None and len(run.audit_payloads) == 1 else 1)
"""
    subprocess.run(
        [sys.executable, "-c", program, postgres_url, request.run_id],
        check=True,
        capture_output=True,
        text=True,
    )


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
        store.persist_preflight_run(request.run_id, invalid_output, result.audit_events)
    assert store.load_run(request.run_id) is None


@pytest.mark.parametrize(
    "field,value,error",
    (
        ("run_id", "run.other", "run ID mismatch"),
        ("sequence", 1, "sequence must be contiguous"),
        ("decision_hash", "f" * 64, "decision hash mismatch"),
        ("requested_pack_id", "pack.other", "requested pack mismatch"),
        ("as_of_time", "2026-06-21T12:00:00.001Z", "as_of_time mismatch"),
    ),
)
def test_store_rejects_audit_records_not_bound_to_the_decision(
    postgres_url: str, field: str, value: object, error: str
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    result = build_safe_refusal(request, empty_pack_registry(), policy)
    invalid_event = result.audit_events[0].model_copy(update={field: value})

    with pytest.raises(ValueError, match=error):
        store.persist_preflight_run(request.run_id, result.output, (invalid_event,))
    assert store.load_run(request.run_id) is None


def test_database_rejects_run_without_declared_audit_rows(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    payload = b"{}"

    connection = psycopg.connect(postgres_url)
    try:
        with pytest.raises(psycopg.Error, match="audit count"), connection.transaction():
            connection.execute(
                """
                INSERT INTO gptl_runs (
                    run_id, case_id, context_kind, as_of_time, record_type,
                    schema_version, hash_algorithm, payload_hash, payload, audit_count,
                    snapshot_count, citation_count, bound_version_count,
                    replay_capsule_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    request.run_id,
                    request.case_id,
                    "PREFLIGHT",
                    request.as_of_time,
                    TIER1_OUTPUT_RECORD_TYPE,
                    SCHEMA_VERSION,
                    HASH_ALGORITHM,
                    hashlib.sha256(payload).hexdigest(),
                    payload,
                    1,
                    0,
                    0,
                    0,
                    0,
                ),
            )
    finally:
        connection.close()


def test_database_rejects_zero_audit_count(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    payload = b"{}"

    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO gptl_runs (
                    run_id, case_id, context_kind, as_of_time, record_type,
                    schema_version, hash_algorithm, payload_hash, payload, audit_count,
                    snapshot_count, citation_count, bound_version_count,
                    replay_capsule_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    request.run_id,
                    request.case_id,
                    "PREFLIGHT",
                    request.as_of_time,
                    TIER1_OUTPUT_RECORD_TYPE,
                    SCHEMA_VERSION,
                    HASH_ALGORITHM,
                    hashlib.sha256(payload).hexdigest(),
                    payload,
                    0,
                    0,
                    0,
                    0,
                    0,
                ),
            )


def test_database_rejects_late_audit_row_that_exceeds_declared_count(
    postgres_url: str,
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_safe_refusal(request, empty_pack_registry(), policy, store)
    payload = b"{}"

    connection = psycopg.connect(postgres_url)
    try:
        with pytest.raises(psycopg.Error, match="audit count"), connection.transaction():
            connection.execute(
                """
                INSERT INTO gptl_audit_events (
                    event_id, run_id, sequence, record_type, schema_version,
                    hash_algorithm, payload_hash, payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "audit.late.1",
                    request.run_id,
                    1,
                    PREFLIGHT_AUDIT_RECORD_TYPE,
                    SCHEMA_VERSION,
                    HASH_ALGORITHM,
                    hashlib.sha256(payload).hexdigest(),
                    payload,
                ),
            )
    finally:
        connection.close()


@pytest.mark.parametrize(
    "target,index,value,error",
    (
        ("run", 0, "WRONG_RUN_TYPE", "record type mismatch"),
        ("run", 1, "wrong.schema", "schema version mismatch"),
        ("audit", 0, "WRONG_AUDIT_TYPE", "record type mismatch"),
        ("audit", 1, "wrong.schema", "schema version mismatch"),
    ),
)
def test_load_rejects_incorrect_persisted_metadata(
    postgres_url: str,
    target: str,
    index: int,
    value: str,
    error: str,
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    run_metadata = [TIER1_OUTPUT_RECORD_TYPE, SCHEMA_VERSION, HASH_ALGORITHM]
    audit_metadata = [PREFLIGHT_AUDIT_RECORD_TYPE, SCHEMA_VERSION, HASH_ALGORITHM]
    metadata = run_metadata if target == "run" else audit_metadata
    metadata[index] = value
    _insert_direct_complete_run(
        postgres_url,
        request,
        tuple(run_metadata),
        tuple(audit_metadata),
    )

    with pytest.raises(PersistenceIntegrityError, match=error):
        store.load_run(request.run_id)


@pytest.mark.parametrize("target", ("run", "audit"))
def test_database_rejects_unknown_hash_algorithm(
    postgres_url: str,
    target: str,
) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    run_metadata = [TIER1_OUTPUT_RECORD_TYPE, SCHEMA_VERSION, HASH_ALGORITHM]
    audit_metadata = [PREFLIGHT_AUDIT_RECORD_TYPE, SCHEMA_VERSION, HASH_ALGORITHM]
    metadata = run_metadata if target == "run" else audit_metadata
    metadata[2] = "SHA-512"

    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_direct_complete_run(
            postgres_url,
            request,
            tuple(run_metadata),
            tuple(audit_metadata),
        )


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
            connection.execute("DELETE FROM gptl_audit_events WHERE run_id = %s", (request.run_id,))
    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="append-only"):
            connection.execute("DELETE FROM gptl_schema_migrations")


def test_database_rejects_truncate_of_committed_rows(postgres_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(postgres_url, policy.canonicalization_policy)
    store.initialize()
    execute_safe_refusal(request, empty_pack_registry(), policy, store)

    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="reject truncate"):
            connection.execute("TRUNCATE gptl_runs CASCADE")


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
        values = (id_value, *values)
    placeholders = ", ".join(("%s",) * len(values))
    statement = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with psycopg.connect(postgres_url) as connection:
        with pytest.raises(psycopg.Error, match="PREFLIGHT run cannot bind"):
            connection.execute(statement, values)
