"""PostgreSQL-only atomic, append-only run persistence."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files
from typing import Final, Literal, Protocol, cast

import psycopg
from psycopg import sql
from pydantic import BaseModel, ConfigDict

from gptl.core.audit import PreflightRefusalAuditEvent, SnapshotDecisionAuditEvent
from gptl.core.canonical import canonical_bytes, canonical_sha256, verify_sha256
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    LogicalId,
    OpaqueId,
    Sha256Hex,
    VersionId,
)
from gptl.core.snapshot import KnowledgeSnapshot, snapshot_hash
from gptl.mie.schema import (
    AdvisoryDecision,
    Citation,
    MIEOutput,
    Tier1Decision,
    Tier1Output,
)

SCHEMA_VERSION: Final = "gptl.slice1.v1"
SNAPSHOT_RUN_SCHEMA_VERSION: Final = "gptl.slice2.v2"
SLICE3_RUN_SCHEMA_VERSION: Final = "gptl.slice3.v1"
SLICE4_RUN_SCHEMA_VERSION: Final = "gptl.slice4.v1"
SLICE5_RUN_SCHEMA_VERSION: Final = "gptl.slice5.v1"
SLICE6_RUN_SCHEMA_VERSION: Final = "gptl.slice6.v1"
WRITABLE_SNAPSHOT_RUN_SCHEMA_VERSIONS: Final = frozenset(
    {
        SNAPSHOT_RUN_SCHEMA_VERSION,
        SLICE3_RUN_SCHEMA_VERSION,
        SLICE4_RUN_SCHEMA_VERSION,
        SLICE5_RUN_SCHEMA_VERSION,
        SLICE6_RUN_SCHEMA_VERSION,
    }
)
SUPPORTED_SNAPSHOT_RUN_SCHEMA_VERSIONS: Final = frozenset(
    {
        "gptl.slice2.v1",
        *WRITABLE_SNAPSHOT_RUN_SCHEMA_VERSIONS,
    }
)
HASH_ALGORITHM: Final = "SHA-256"
TIER1_OUTPUT_RECORD_TYPE: Final = "TIER1_OUTPUT"
TIER2_OUTPUT_RECORD_TYPE: Final = "TIER2_OUTPUT"
PREFLIGHT_AUDIT_RECORD_TYPE: Final = "PREFLIGHT_REFUSAL_AUDIT_EVENT"
SNAPSHOT_AUDIT_RECORD_TYPE: Final = "SNAPSHOT_DECISION_AUDIT_EVENT"
SNAPSHOT_RECORD_TYPE: Final = "KNOWLEDGE_SNAPSHOT"
CITATION_RECORD_TYPE: Final = "EVIDENCE_CITATION"
BOUND_VERSION_RECORD_TYPE: Final = "BOUND_VERSION"
REPLAY_CAPSULE_RECORD_TYPE: Final = "REPLAY_CAPSULE"
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
class ReplayCapsulePayload:
    algorithm_id: str
    recipe_schema_version: str
    replay_policy_ref: GovernedRef
    payload: bytes


class ReplayCapsuleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: OpaqueId
    algorithm_id: Literal["BUILD0_EXACT_REPLAY_V1"]
    recipe_schema_version: Literal["gptl.replay-recipe.v1"]
    replay_policy_ref: GovernedRef
    payload_hash: Sha256Hex
    record_type: Literal["REPLAY_CAPSULE"]
    schema_version: OpaqueId
    hash_algorithm: Literal["SHA-256"]


@dataclass(frozen=True)
class StoredReplayCapsule:
    algorithm_id: str
    recipe_schema_version: str
    replay_policy_ref: GovernedRef
    payload: bytes
    payload_hash: str


@dataclass(frozen=True)
class StoredRun:
    run_id: str
    context_kind: str
    record_type: str
    schema_version: str
    hash_algorithm: str
    payload: bytes
    payload_hash: str
    audit_payloads: tuple[bytes, ...]
    snapshot_payload: bytes | None
    citation_payloads: tuple[bytes, ...]
    bound_version_payloads: tuple[bytes, ...]
    replay_capsule: StoredReplayCapsule | None


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
        expected_schema_version: str,
    ) -> None:
        if record_type != expected_record_type:
            raise PersistenceIntegrityError("persisted record type mismatch")
        if schema_version != expected_schema_version:
            raise PersistenceIntegrityError("persisted schema version mismatch")
        if hash_algorithm != HASH_ALGORITHM:
            raise PersistenceIntegrityError("persisted hash algorithm mismatch")

    def persist_preflight_run(
        self,
        run_id: str,
        output: Tier1Output,
        audit_events: Sequence[PreflightRefusalAuditEvent],
    ) -> None:
        self._persist_preflight_run(run_id, output, audit_events, None)

    def persist_replayable_preflight_run(
        self,
        run_id: str,
        output: Tier1Output,
        audit_events: Sequence[PreflightRefusalAuditEvent],
        replay_capsule: ReplayCapsulePayload,
    ) -> None:
        self._persist_preflight_run(run_id, output, audit_events, replay_capsule)

    def _persist_preflight_run(
        self,
        run_id: str,
        output: Tier1Output,
        audit_events: Sequence[PreflightRefusalAuditEvent],
        replay_capsule: ReplayCapsulePayload | None,
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
                            audit_count, snapshot_count, citation_count,
                            bound_version_count, replay_capsule_count
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
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
                            0,
                            0,
                            0,
                            1 if replay_capsule is not None else 0,
                        ),
                    )
                    self._insert_audit_events(cursor, audit_events, SCHEMA_VERSION)
                    if replay_capsule is not None:
                        self._insert_replay_capsule(
                            cursor,
                            run_id,
                            replay_capsule,
                            SCHEMA_VERSION,
                        )

    def persist_snapshot_run(
        self,
        run_id: str,
        output: MIEOutput,
        snapshot: KnowledgeSnapshot,
        audit_events: Sequence[SnapshotDecisionAuditEvent],
        bound_versions: Sequence[GovernedRef],
        schema_version: str,
    ) -> None:
        self._persist_snapshot_run(
            run_id,
            output,
            snapshot,
            audit_events,
            bound_versions,
            schema_version,
            None,
        )

    def persist_replayable_snapshot_run(
        self,
        run_id: str,
        output: MIEOutput,
        snapshot: KnowledgeSnapshot,
        audit_events: Sequence[SnapshotDecisionAuditEvent],
        bound_versions: Sequence[GovernedRef],
        schema_version: str,
        replay_capsule: ReplayCapsulePayload,
    ) -> None:
        self._persist_snapshot_run(
            run_id,
            output,
            snapshot,
            audit_events,
            bound_versions,
            schema_version,
            replay_capsule,
        )

    def _persist_snapshot_run(
        self,
        run_id: str,
        output: MIEOutput,
        snapshot: KnowledgeSnapshot,
        audit_events: Sequence[SnapshotDecisionAuditEvent],
        bound_versions: Sequence[GovernedRef],
        schema_version: str,
        replay_capsule: ReplayCapsulePayload | None,
    ) -> None:
        if schema_version not in WRITABLE_SNAPSHOT_RUN_SCHEMA_VERSIONS:
            raise ValueError("snapshot run schema is not writable")
        body: Tier1Decision | AdvisoryDecision
        if isinstance(output, Tier1Output):
            body = output.decision
            output_hash = output.decision_hash
            expected_hash = canonical_sha256(body, self._policy)
            record_type = TIER1_OUTPUT_RECORD_TYPE
        else:
            body = output.advisory
            output_hash = output.advisory_hash
            expected_hash = canonical_sha256(body, self._policy)
            record_type = TIER2_OUTPUT_RECORD_TYPE
        if body.context.context_kind != "SNAPSHOT_BOUND":
            raise ValueError("snapshot persistence requires a snapshot-bound output")
        if output_hash != expected_hash:
            raise PersistenceIntegrityError("snapshot-bound output checksum mismatch")
        snapshot_digest = snapshot_hash(snapshot, self._policy)
        if body.context.knowledge_snapshot_hash != snapshot_digest:
            raise PersistenceIntegrityError("output snapshot hash mismatch")
        if tuple(body.audit_event_ids) != tuple(sorted(event.event_id for event in audit_events)):
            raise ValueError("output audit IDs do not match supplied events")
        if tuple(event.sequence for event in audit_events) != tuple(range(len(audit_events))):
            raise ValueError("audit event sequence must be contiguous and zero-based")
        if any(
            event.run_id != run_id
            or event.output_hash != output_hash
            or event.snapshot_hash != snapshot_digest
            or event.as_of_time != body.as_of_time
            or event.output_kind != output.output_kind
            for event in audit_events
        ):
            raise ValueError("snapshot audit event does not match output")
        normalized_versions = sorted_unique_refs(tuple(bound_versions))
        if normalized_versions != snapshot.bound_versions:
            raise ValueError("persisted bound versions do not match snapshot")
        citations = body.citations
        output_payload = canonical_bytes(output, self._policy)
        output_payload_hash = hashlib.sha256(output_payload).hexdigest()
        snapshot_payload = canonical_bytes(snapshot, self._policy)
        with psycopg.connect(self._database_url) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    self._pin_search_path(cursor)
                    cursor.execute(
                        """
                        INSERT INTO gptl_runs (
                            run_id, case_id, context_kind, as_of_time, record_type,
                            schema_version, hash_algorithm, payload_hash, payload,
                            audit_count, snapshot_count, citation_count,
                            bound_version_count, replay_capsule_count
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            run_id,
                            body.case_id,
                            body.context.context_kind,
                            body.as_of_time,
                            record_type,
                            schema_version,
                            HASH_ALGORITHM,
                            output_payload_hash,
                            output_payload,
                            len(audit_events),
                            1,
                            len(citations),
                            len(normalized_versions),
                            1 if replay_capsule is not None else 0,
                        ),
                    )
                    self._insert_snapshot(
                        cursor,
                        run_id,
                        snapshot_payload,
                        snapshot_digest,
                        schema_version,
                    )
                    self._insert_citations(cursor, run_id, citations, schema_version)
                    self._insert_bound_versions(
                        cursor,
                        run_id,
                        normalized_versions,
                        schema_version,
                    )
                    self._insert_audit_events(
                        cursor,
                        audit_events,
                        schema_version,
                    )
                    if replay_capsule is not None:
                        self._insert_replay_capsule(
                            cursor,
                            run_id,
                            replay_capsule,
                            schema_version,
                        )

    def _insert_replay_capsule(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        run_id: str,
        replay_capsule: ReplayCapsulePayload,
        schema_version: str,
    ) -> None:
        if not replay_capsule.algorithm_id or not replay_capsule.recipe_schema_version:
            raise ValueError("replay capsule requires algorithm and recipe schema identities")
        payload_hash = hashlib.sha256(replay_capsule.payload).hexdigest()
        cursor.execute(
            """
            INSERT INTO gptl_replay_capsules (
                run_id, algorithm_id, recipe_schema_version,
                replay_policy_logical_id, replay_policy_version_id,
                replay_policy_version_number, replay_policy_content_hash,
                payload_hash, payload, record_type, schema_version, hash_algorithm
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                replay_capsule.algorithm_id,
                replay_capsule.recipe_schema_version,
                replay_capsule.replay_policy_ref.logical_id,
                replay_capsule.replay_policy_ref.version_id,
                replay_capsule.replay_policy_ref.version_number,
                replay_capsule.replay_policy_ref.content_hash,
                payload_hash,
                replay_capsule.payload,
                REPLAY_CAPSULE_RECORD_TYPE,
                schema_version,
                HASH_ALGORITHM,
            ),
        )

    def _insert_audit_events(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        audit_events: Sequence[PreflightRefusalAuditEvent | SnapshotDecisionAuditEvent],
        schema_version: str,
    ) -> None:
        for event in sorted(audit_events, key=lambda item: item.sequence):
            payload = canonical_bytes(event, self._policy)
            record_type = (
                PREFLIGHT_AUDIT_RECORD_TYPE
                if isinstance(event, PreflightRefusalAuditEvent)
                else SNAPSHOT_AUDIT_RECORD_TYPE
            )
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
                    record_type,
                    schema_version,
                    HASH_ALGORITHM,
                    canonical_sha256(event, self._policy),
                    payload,
                ),
            )

    def _insert_snapshot(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        run_id: str,
        payload: bytes,
        payload_hash: str,
        schema_version: str,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO gptl_snapshots (
                run_id, payload_hash, payload, record_type, schema_version,
                hash_algorithm
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                payload_hash,
                payload,
                SNAPSHOT_RECORD_TYPE,
                schema_version,
                HASH_ALGORITHM,
            ),
        )

    def _insert_citations(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        run_id: str,
        citations: Sequence[Citation],
        schema_version: str,
    ) -> None:
        for citation in citations:
            payload = canonical_bytes(citation, self._policy)
            payload_hash = hashlib.sha256(payload).hexdigest()
            cursor.execute(
                """
                INSERT INTO gptl_citations (
                    citation_id, run_id, payload_hash, payload, record_type,
                    schema_version, hash_algorithm
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payload_hash,
                    run_id,
                    payload_hash,
                    payload,
                    CITATION_RECORD_TYPE,
                    schema_version,
                    HASH_ALGORITHM,
                ),
            )

    def _insert_bound_versions(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        run_id: str,
        bound_versions: Sequence[GovernedRef],
        schema_version: str,
    ) -> None:
        for version in bound_versions:
            payload = canonical_bytes(version, self._policy)
            payload_hash = hashlib.sha256(payload).hexdigest()
            cursor.execute(
                """
                INSERT INTO gptl_bound_versions (
                    binding_id, run_id, payload_hash, payload, record_type,
                    schema_version, hash_algorithm
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    version.version_id,
                    run_id,
                    payload_hash,
                    payload,
                    BOUND_VERSION_RECORD_TYPE,
                    schema_version,
                    HASH_ALGORITHM,
                ),
            )

    def load_run(self, run_id: str) -> StoredRun | None:
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                self._pin_search_path(cursor)
                cursor.execute(
                    "SELECT payload, payload_hash, audit_count, record_type, "
                    "schema_version, hash_algorithm, context_kind, snapshot_count, "
                    "citation_count, bound_version_count, replay_capsule_count "
                    "FROM gptl_runs WHERE run_id = %s",
                    (run_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                payload, payload_hash, audit_count = bytes(row[0]), row[1].strip(), row[2]
                context_kind = row[6]
                if context_kind == "PREFLIGHT":
                    expected_schema = SCHEMA_VERSION
                    expected_record_type = TIER1_OUTPUT_RECORD_TYPE
                    expected_audit_type = PREFLIGHT_AUDIT_RECORD_TYPE
                elif (
                    context_kind == "SNAPSHOT_BOUND"
                    and row[3] in {TIER1_OUTPUT_RECORD_TYPE, TIER2_OUTPUT_RECORD_TYPE}
                    and row[4] in SUPPORTED_SNAPSHOT_RUN_SCHEMA_VERSIONS
                ):
                    expected_schema = cast(str, row[4])
                    expected_record_type = row[3]
                    expected_audit_type = SNAPSHOT_AUDIT_RECORD_TYPE
                else:
                    raise PersistenceIntegrityError("persisted run context is invalid")
                self._validate_record_metadata(
                    row[3],
                    row[4],
                    row[5],
                    expected_record_type,
                    expected_schema,
                )
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
                        expected_audit_type,
                        expected_schema,
                    )
                    immutable_payload = bytes(audit_row[0])
                    verify_sha256(immutable_payload, audit_row[1].strip())
                    audit_payloads.append(immutable_payload)
                snapshot_payload = self._load_snapshot_payload(
                    cursor,
                    run_id,
                    row[7],
                    expected_schema,
                )
                citation_payloads = self._load_related_payloads(
                    cursor,
                    "gptl_citations",
                    "citation_id",
                    run_id,
                    row[8],
                    CITATION_RECORD_TYPE,
                    expected_schema,
                )
                bound_version_payloads = self._load_related_payloads(
                    cursor,
                    "gptl_bound_versions",
                    "binding_id",
                    run_id,
                    row[9],
                    BOUND_VERSION_RECORD_TYPE,
                    expected_schema,
                )
                replay_capsule = self._load_replay_capsule(
                    cursor,
                    run_id,
                    row[10],
                    expected_schema,
                )
                return StoredRun(
                    run_id=run_id,
                    context_kind=context_kind,
                    record_type=expected_record_type,
                    schema_version=expected_schema,
                    hash_algorithm=HASH_ALGORITHM,
                    payload=payload,
                    payload_hash=payload_hash,
                    audit_payloads=tuple(audit_payloads),
                    snapshot_payload=snapshot_payload,
                    citation_payloads=citation_payloads,
                    bound_version_payloads=bound_version_payloads,
                    replay_capsule=replay_capsule,
                )

    def _load_replay_capsule(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        run_id: str,
        expected_count: object,
        expected_schema: str,
    ) -> StoredReplayCapsule | None:
        cursor.execute(
            "SELECT algorithm_id, recipe_schema_version, replay_policy_logical_id, "
            "replay_policy_version_id, replay_policy_version_number, "
            "replay_policy_content_hash, payload, payload_hash, "
            "record_type, schema_version, hash_algorithm "
            "FROM gptl_replay_capsules WHERE run_id = %s",
            (run_id,),
        )
        rows = cursor.fetchall()
        if len(rows) != expected_count:
            raise PersistenceIntegrityError("persisted replay capsule count mismatch")
        if not rows:
            return None
        row = cast(
            tuple[str, str, str, str, int, str, bytes, str, str, str, str],
            rows[0],
        )
        self._validate_record_metadata(
            row[8],
            row[9],
            row[10],
            REPLAY_CAPSULE_RECORD_TYPE,
            expected_schema,
        )
        payload = bytes(row[6])
        payload_hash = row[7].strip()
        verify_sha256(payload, payload_hash)
        return StoredReplayCapsule(
            algorithm_id=row[0],
            recipe_schema_version=row[1],
            replay_policy_ref=GovernedRef(
                logical_id=LogicalId(row[2]),
                version_id=VersionId(row[3]),
                version_number=row[4],
                content_hash=row[5].strip(),
            ),
            payload=payload,
            payload_hash=payload_hash,
        )

    def _load_snapshot_payload(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        run_id: str,
        expected_count: object,
        expected_schema: str,
    ) -> bytes | None:
        cursor.execute(
            "SELECT payload, payload_hash, record_type, schema_version, hash_algorithm "
            "FROM gptl_snapshots WHERE run_id = %s",
            (run_id,),
        )
        rows = cursor.fetchall()
        if len(rows) != expected_count:
            raise PersistenceIntegrityError("persisted snapshot count mismatch")
        if not rows:
            return None
        row = cast(tuple[bytes, str, str, str, str], rows[0])
        self._validate_record_metadata(
            row[2],
            row[3],
            row[4],
            SNAPSHOT_RECORD_TYPE,
            expected_schema,
        )
        payload = bytes(row[0])
        verify_sha256(payload, row[1].strip())
        return payload

    def _load_related_payloads(
        self,
        cursor: psycopg.Cursor[tuple[object, ...]],
        table_name: str,
        order_column: str,
        run_id: str,
        expected_count: object,
        expected_record_type: str,
        expected_schema: str,
    ) -> tuple[bytes, ...]:
        query = sql.SQL(
            "SELECT payload, payload_hash, record_type, schema_version, hash_algorithm "
            "FROM {} WHERE run_id = %s ORDER BY {}"
        ).format(sql.Identifier(table_name), sql.Identifier(order_column))
        cursor.execute(query, (run_id,))
        rows = cursor.fetchall()
        if len(rows) != expected_count:
            raise PersistenceIntegrityError(f"persisted {table_name} count mismatch")
        payloads = []
        for row in cast(list[tuple[bytes, str, str, str, str]], rows):
            self._validate_record_metadata(
                row[2],
                row[3],
                row[4],
                expected_record_type,
                expected_schema,
            )
            payload = bytes(row[0])
            verify_sha256(payload, row[1].strip())
            payloads.append(payload)
        return tuple(payloads)
