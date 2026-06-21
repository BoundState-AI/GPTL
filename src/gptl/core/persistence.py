"""PostgreSQL-only atomic, append-only run persistence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.resources import files
from typing import Sequence

import psycopg

from gptl.core.audit import PreflightRefusalAuditEvent
from gptl.core.canonical import canonical_bytes, canonical_sha256, verify_sha256
from gptl.core.semantic_types import CanonicalizationPolicy
from gptl.mie.schema import Tier1Output


SCHEMA_VERSION = "gptl.slice1.v1"
MIGRATION_ID = "0001_slice_1"


class PersistenceIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredRun:
    run_id: str
    payload: bytes
    payload_hash: str
    audit_payloads: tuple[bytes, ...]


class PostgresRunStore:
    def __init__(self, database_url: str, policy: CanonicalizationPolicy) -> None:
        if not database_url:
            raise ValueError("an explicit PostgreSQL database URL is required")
        if not database_url.startswith(("postgresql://", "postgres://")):
            raise ValueError("database URL must select PostgreSQL")
        self._database_url = database_url
        self._policy = policy

    def initialize(self) -> None:
        migration_path = files("gptl.core").joinpath("migrations/0001_slice_1.sql")
        migration_sql = migration_path.read_text(encoding="utf-8")
        migration_hash = hashlib.sha256(migration_sql.encode("utf-8")).hexdigest()
        with psycopg.connect(self._database_url) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT to_regclass('public.gptl_schema_migrations')
                        """
                    )
                    exists = cursor.fetchone()[0] is not None
                    if exists:
                        cursor.execute(
                            "SELECT migration_hash FROM gptl_schema_migrations "
                            "WHERE migration_id = %s",
                            (MIGRATION_ID,),
                        )
                        row = cursor.fetchone()
                        if row is None:
                            raise PersistenceIntegrityError(
                                "database schema exists without required migration"
                            )
                        if row[0].strip() != migration_hash:
                            raise PersistenceIntegrityError("migration checksum mismatch")
                        return
                    cursor.execute(migration_sql)
                    cursor.execute(
                        "INSERT INTO gptl_schema_migrations "
                        "(migration_id, migration_hash) VALUES (%s, %s)",
                        (MIGRATION_ID, migration_hash),
                    )

    def persist_preflight_run(
        self,
        run_id: str,
        output: Tier1Output,
        audit_events: Sequence[PreflightRefusalAuditEvent],
    ) -> None:
        if output.decision.context.context_kind != "PREFLIGHT":
            raise ValueError("persist_preflight_run accepts PREFLIGHT decisions only")
        if tuple(output.decision.audit_event_ids) != tuple(
            sorted(event.event_id for event in audit_events)
        ):
            raise ValueError("decision audit IDs do not match supplied events")
        if any(event.run_id != run_id for event in audit_events):
            raise ValueError("audit event run ID mismatch")
        if canonical_sha256(output.decision, self._policy) != output.decision_hash:
            raise PersistenceIntegrityError("decision checksum mismatch")

        output_payload = canonical_bytes(output, self._policy)
        output_hash = hashlib.sha256(output_payload).hexdigest()
        with psycopg.connect(self._database_url) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO gptl_runs (
                            run_id, case_id, context_kind, as_of_time, record_type,
                            schema_version, hash_algorithm, payload_hash, payload,
                            audit_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            run_id,
                            output.decision.case_id,
                            output.decision.context.context_kind,
                            output.decision.as_of_time,
                            "TIER1_OUTPUT",
                            SCHEMA_VERSION,
                            "SHA-256",
                            output_hash,
                            output_payload,
                            len(audit_events),
                        ),
                    )
                    self._insert_audit_events(cursor, audit_events)

    def _insert_audit_events(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        audit_events: Sequence[PreflightRefusalAuditEvent],
    ) -> None:
        for event in sorted(audit_events, key=lambda item: item.sequence):
            payload = canonical_bytes(event, self._policy)
            cursor.execute(
                """
                INSERT INTO gptl_audit_events (
                    event_id, run_id, sequence, record_type, schema_version,
                    hash_algorithm, payload_hash, payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.sequence,
                    "PREFLIGHT_REFUSAL_AUDIT_EVENT",
                    SCHEMA_VERSION,
                    "SHA-256",
                    canonical_sha256(event, self._policy),
                    payload,
                ),
            )

    def load_run(self, run_id: str) -> StoredRun | None:
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT payload, payload_hash, audit_count FROM gptl_runs "
                    "WHERE run_id = %s",
                    (run_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                payload, payload_hash, audit_count = bytes(row[0]), row[1].strip(), row[2]
                verify_sha256(payload, payload_hash)
                cursor.execute(
                    "SELECT payload, payload_hash FROM gptl_audit_events "
                    "WHERE run_id = %s ORDER BY sequence",
                    (run_id,),
                )
                audit_rows = cursor.fetchall()
                if len(audit_rows) != audit_count:
                    raise PersistenceIntegrityError("persisted audit count mismatch")
                audit_payloads = []
                for audit_payload, audit_hash in audit_rows:
                    immutable_payload = bytes(audit_payload)
                    verify_sha256(immutable_payload, audit_hash.strip())
                    audit_payloads.append(immutable_payload)
                return StoredRun(run_id, payload, payload_hash, tuple(audit_payloads))
