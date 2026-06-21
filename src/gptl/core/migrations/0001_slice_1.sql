CREATE TABLE gptl_schema_migrations (
    migration_id text PRIMARY KEY,
    migration_hash char(64) NOT NULL CHECK (migration_hash ~ '^[0-9a-f]{64}$')
);

CREATE TABLE gptl_runs (
    run_id text PRIMARY KEY,
    case_id text NOT NULL,
    context_kind text NOT NULL CHECK (context_kind IN ('PREFLIGHT', 'SNAPSHOT_BOUND')),
    as_of_time text NOT NULL,
    record_type text NOT NULL,
    schema_version text NOT NULL,
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256'),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    audit_count integer NOT NULL CHECK (audit_count > 0)
);

CREATE TABLE gptl_audit_events (
    event_id text PRIMARY KEY,
    run_id text NOT NULL REFERENCES gptl_runs(run_id),
    sequence integer NOT NULL CHECK (sequence >= 0),
    record_type text NOT NULL,
    schema_version text NOT NULL,
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256'),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    UNIQUE (run_id, sequence)
);

CREATE TABLE gptl_snapshots (
    run_id text PRIMARY KEY REFERENCES gptl_runs(run_id),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL
);

CREATE TABLE gptl_citations (
    citation_id text PRIMARY KEY,
    run_id text NOT NULL REFERENCES gptl_runs(run_id),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL
);

CREATE TABLE gptl_bound_versions (
    binding_id text PRIMARY KEY,
    run_id text NOT NULL REFERENCES gptl_runs(run_id),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL
);

CREATE FUNCTION gptl_reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'GPTL committed records are append-only';
END;
$$;

CREATE FUNCTION gptl_reject_preflight_binding() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM gptl_runs
        WHERE run_id = NEW.run_id AND context_kind = 'PREFLIGHT'
    ) THEN
        RAISE EXCEPTION 'PREFLIGHT run cannot bind snapshot, citation, or version records';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER gptl_runs_append_only
BEFORE UPDATE OR DELETE ON gptl_runs
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_schema_migrations_append_only
BEFORE UPDATE OR DELETE ON gptl_schema_migrations
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_audit_events_append_only
BEFORE UPDATE OR DELETE ON gptl_audit_events
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_snapshots_append_only
BEFORE UPDATE OR DELETE ON gptl_snapshots
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_citations_append_only
BEFORE UPDATE OR DELETE ON gptl_citations
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_bound_versions_append_only
BEFORE UPDATE OR DELETE ON gptl_bound_versions
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_snapshots_no_preflight
BEFORE INSERT ON gptl_snapshots
FOR EACH ROW EXECUTE FUNCTION gptl_reject_preflight_binding();

CREATE TRIGGER gptl_citations_no_preflight
BEFORE INSERT ON gptl_citations
FOR EACH ROW EXECUTE FUNCTION gptl_reject_preflight_binding();

CREATE TRIGGER gptl_bound_versions_no_preflight
BEFORE INSERT ON gptl_bound_versions
FOR EACH ROW EXECUTE FUNCTION gptl_reject_preflight_binding();
