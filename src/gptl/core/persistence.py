"""PostgreSQL-only atomic, append-only run persistence."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files
from typing import Final, Protocol, cast

import psycopg
from psycopg import sql

from gptl.core.audit import PreflightRefusalAuditEvent
from gptl.core.canonical import canonical_bytes, canonical_sha256, verify_sha256
from gptl.core.semantic_types import CanonicalizationPolicy
from gptl.mie.schema import Tier1Output

SCHEMA_VERSION: Final = "gptl.slice1.v1"
HASH_ALGORITHM: Final = "SHA-256"
TIER1_OUTPUT_RECORD_TYPE: Final = "TIER1_OUTPUT"
PREFLIGHT_AUDIT_RECORD_TYPE: Final = "PREFLIGHT_REFUSAL_AUDIT_EVENT"
MIGRATION_FILE_PATTERN = re.compile(r"^(?P<ordinal>\d{4})_[a-z0-9_]+\.sql$")


class PersistenceIntegrityError(RuntimeError):
    pass


class MigrationResource(Protocol):
    @property
    def name(self) -> str: ...

    def read_text(self, encoding: str | None = None) -> str: ...


@dataclass(frozen=True)
class Migration:
    ordinal: int
    migration_id: str
    payload: str
    payload_hash: str


@dataclass(frozen=True)
class StoredRun:
    run_id: str
    record_type: str
    schema_version: str
    hash_algorithm: str
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
        migrations = self._load_migrations()
        with psycopg.connect(self._database_url) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    self._pin_search_path(cursor)
                    cursor.execute(
                        """
                        SELECT to_regclass('gptl_schema_migrations')
                        """
                    )
                    existence_row = cursor.fetchone()
                    if existence_row is None:
                        raise PersistenceIntegrityError(
                            "PostgreSQL did not return schema existence state"
                        )
                    exists = existence_row[0] is not None
                    applied = self._load_applied_migrations(cursor) if exists else {}
                    if exists:
                        self._validate_migration_history(migrations, applied)

                    for migration in migrations:
                        applied_hash = applied.get(migration.migration_id)
                        if applied_hash is not None:
                            # A migration ID is historical identity. Accepting new SQL
                            # under it would make replay semantics installation-dependent.
                            if applied_hash != migration.payload_hash:
                                raise PersistenceIntegrityError(
                                    f"migration checksum mismatch: {migration.migration_id}"
                                )
                            continue
                        cursor.execute(migration.payload)
                        cursor.execute(
                            "INSERT INTO gptl_schema_migrations "
                            "(migration_id, migration_hash) VALUES (%s, %s)",
                            (migration.migration_id, migration.payload_hash),
                        )

    @staticmethod
    def _load_migrations() -> tuple[Migration, ...]:
        migration_root = files("gptl.core").joinpath("migrations")
        migration_files = sorted(
            (
                entry
                for entry in migration_root.iterdir()
                if entry.is_file() and MIGRATION_FILE_PATTERN.fullmatch(entry.name)
            ),
            key=lambda entry: entry.name,
        )
        if not migration_files:
            raise PersistenceIntegrityError("no PostgreSQL migrations are packaged")
        migrations = tuple(PostgresRunStore._read_migration(path) for path in migration_files)
        if tuple(migration.ordinal for migration in migrations) != tuple(
            range(1, len(migrations) + 1)
        ):
            raise PersistenceIntegrityError(
                "PostgreSQL migration ordinals must be contiguous and start at 0001"
            )
        return migrations

    @staticmethod
    def _read_migration(path: MigrationResource) -> Migration:
        payload = path.read_text(encoding="utf-8")
        match = MIGRATION_FILE_PATTERN.fullmatch(path.name)
        if match is None:
            raise PersistenceIntegrityError(f"invalid migration filename: {path.name}")
        return Migration(
            ordinal=int(match.group("ordinal")),
            migration_id=path.name.removesuffix(".sql"),
            payload=payload,
            payload_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        )

    @staticmethod
    def _load_applied_migrations(
        cursor: psycopg.Cursor[tuple[object, ...]],
    ) -> dict[str, str]:
        cursor.execute(
            "SELECT migration_id, migration_hash FROM gptl_schema_migrations ORDER BY migration_id"
        )
        rows = cast(list[tuple[str, str]], cursor.fetchall())
        return {migration_id: migration_hash.strip() for migration_id, migration_hash in rows}

    @staticmethod
    def _validate_migration_history(
        migrations: tuple[Migration, ...],
        applied: dict[str, str],
    ) -> None:
        packaged_ids = tuple(migration.migration_id for migration in migrations)
        applied_ids = tuple(applied)
        if not applied_ids or applied_ids != packaged_ids[: len(applied_ids)]:
            raise PersistenceIntegrityError(
                "applied migrations must be an exact prefix of packaged migrations"
            )

    @staticmethod
    def _pin_search_path(cursor: psycopg.Cursor[tuple[object, ...]]) -> None:
        cursor.execute("SELECT current_schema()")
        row = cursor.fetchone()
        if row is None or not isinstance(row[0], str):
            raise PersistenceIntegrityError("PostgreSQL connection has no active schema")
        # Later search-path entries must not be able to shadow GPTL relations or
        # change which objects a trigger function resolves after publication.
        cursor.execute(
            sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(row[0]))
        )

    @staticmethod
    def _validate_record_metadata(
        record_type: object,
        schema_version: object,
        hash_algorithm: object,
        expected_record_type: str,
    ) -> None:
        if record_type != expected_record_type:
            raise PersistenceIntegrityError("persisted record type mismatch")
        if schema_version != SCHEMA_VERSION:
            raise PersistenceIntegrityError("persisted schema version mismatch")
        if hash_algorithm != HASH_ALGORITHM:
            raise PersistenceIntegrityError("persisted hash algorithm mismatch")

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
        if tuple(event.sequence for event in audit_events) != tuple(range(len(audit_events))):
            raise ValueError("audit event sequence must be contiguous and zero-based")
        if canonical_sha256(output.decision, self._policy) != output.decision_hash:
            raise PersistenceIntegrityError("decision checksum mismatch")
        if any(event.decision_hash != output.decision_hash for event in audit_events):
            raise ValueError("audit event decision hash mismatch")
        if any(
            event.requested_pack_id != output.decision.context.requested_pack_id
            for event in audit_events
        ):
            raise ValueError("audit event requested pack mismatch")
        if any(event.as_of_time != output.decision.as_of_time for event in audit_events):
            raise ValueError("audit event as_of_time mismatch")

        output_payload = canonical_bytes(output, self._policy)
        output_hash = hashlib.sha256(output_payload).hexdigest()
        with psycopg.connect(self._database_url) as connection:
            # The FK requires the run first, but exposing it without its audit would
            # violate the record contract; one transaction makes either both durable
            # or neither visible.
            with connection.transaction():
                with connection.cursor() as cursor:
                    self._pin_search_path(cursor)
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
                            TIER1_OUTPUT_RECORD_TYPE,
                            SCHEMA_VERSION,
                            HASH_ALGORITHM,
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
                    PREFLIGHT_AUDIT_RECORD_TYPE,
                    SCHEMA_VERSION,
                    HASH_ALGORITHM,
                    canonical_sha256(event, self._policy),
                    payload,
                ),
            )

    def load_run(self, run_id: str) -> StoredRun | None:
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                self._pin_search_path(cursor)
                cursor.execute(
                    "SELECT payload, payload_hash, audit_count, record_type, "
                    "schema_version, hash_algorithm FROM gptl_runs WHERE run_id = %s",
                    (run_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                payload, payload_hash, audit_count = bytes(row[0]), row[1].strip(), row[2]
                self._validate_record_metadata(row[3], row[4], row[5], TIER1_OUTPUT_RECORD_TYPE)
                verify_sha256(payload, payload_hash)
                cursor.execute(
                    "SELECT payload, payload_hash, record_type, schema_version, "
                    "hash_algorithm FROM gptl_audit_events "
                    "WHERE run_id = %s ORDER BY sequence",
                    (run_id,),
                )
                audit_rows = cursor.fetchall()
                if len(audit_rows) != audit_count:
                    raise PersistenceIntegrityError("persisted audit count mismatch")
                audit_payloads = []
                for audit_row in audit_rows:
                    self._validate_record_metadata(
                        audit_row[2],
                        audit_row[3],
                        audit_row[4],
                        PREFLIGHT_AUDIT_RECORD_TYPE,
                    )
                    immutable_payload = bytes(audit_row[0])
                    verify_sha256(immutable_payload, audit_row[1].strip())
                    audit_payloads.append(immutable_payload)
                return StoredRun(
                    run_id=run_id,
                    record_type=TIER1_OUTPUT_RECORD_TYPE,
                    schema_version=SCHEMA_VERSION,
                    hash_algorithm=HASH_ALGORITHM,
                    payload=payload,
                    payload_hash=payload_hash,
                    audit_payloads=tuple(audit_payloads),
                )
