-- Slice 1 forbade these rows for every existing PREFLIGHT run. Refusing a
-- nonempty table prevents a schema rewrite from silently reinterpreting history.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM gptl_snapshots)
        OR EXISTS (SELECT 1 FROM gptl_citations)
        OR EXISTS (SELECT 1 FROM gptl_bound_versions) THEN
        RAISE EXCEPTION 'snapshot-bound tables must be empty before Slice 2 migration';
    END IF;
END;
$$;

ALTER TABLE gptl_runs
    ADD COLUMN snapshot_count integer NOT NULL DEFAULT 0 CHECK (snapshot_count >= 0),
    ADD COLUMN citation_count integer NOT NULL DEFAULT 0 CHECK (citation_count >= 0),
    ADD COLUMN bound_version_count integer NOT NULL DEFAULT 0 CHECK (bound_version_count >= 0);

ALTER TABLE gptl_runs
    ALTER COLUMN snapshot_count DROP DEFAULT,
    ALTER COLUMN citation_count DROP DEFAULT,
    ALTER COLUMN bound_version_count DROP DEFAULT,
    ADD CONSTRAINT gptl_runs_context_record_counts CHECK (
        (context_kind = 'PREFLIGHT'
            AND snapshot_count = 0
            AND citation_count = 0
            AND bound_version_count = 0)
        OR
        (context_kind = 'SNAPSHOT_BOUND'
            AND snapshot_count = 1
            AND bound_version_count > 0)
    );

ALTER TABLE gptl_snapshots
    ADD COLUMN record_type text NOT NULL,
    ADD COLUMN schema_version text NOT NULL,
    ADD COLUMN hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256');

ALTER TABLE gptl_citations
    DROP CONSTRAINT gptl_citations_pkey,
    ADD PRIMARY KEY (run_id, citation_id),
    ADD COLUMN record_type text NOT NULL,
    ADD COLUMN schema_version text NOT NULL,
    ADD COLUMN hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256');

ALTER TABLE gptl_bound_versions
    DROP CONSTRAINT gptl_bound_versions_pkey,
    ADD PRIMARY KEY (run_id, binding_id),
    ADD COLUMN record_type text NOT NULL,
    ADD COLUMN schema_version text NOT NULL,
    ADD COLUMN hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256');

CREATE FUNCTION gptl_validate_snapshot_bound_counts() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
DECLARE
    run_context text;
    expected_snapshots integer;
    expected_citations integer;
    expected_versions integer;
    actual_snapshots bigint;
    actual_citations bigint;
    actual_versions bigint;
BEGIN
    SELECT context_kind, snapshot_count, citation_count, bound_version_count
    INTO run_context, expected_snapshots, expected_citations, expected_versions
    FROM gptl_runs
    WHERE run_id = NEW.run_id;

    SELECT count(*) INTO actual_snapshots FROM gptl_snapshots WHERE run_id = NEW.run_id;
    SELECT count(*) INTO actual_citations FROM gptl_citations WHERE run_id = NEW.run_id;
    SELECT count(*) INTO actual_versions FROM gptl_bound_versions WHERE run_id = NEW.run_id;

    IF run_context IS NULL
        OR actual_snapshots <> expected_snapshots
        OR actual_citations <> expected_citations
        OR actual_versions <> expected_versions THEN
        RAISE EXCEPTION 'GPTL snapshot-bound record counts do not match committed rows';
    END IF;
    RETURN NULL;
END;
$$;

-- Every dependent row requires the run FK first. Immediate checks would reject
-- that valid insertion order before the transaction can assemble the full record.
CREATE CONSTRAINT TRIGGER gptl_runs_validate_snapshot_bound_counts
AFTER INSERT ON gptl_runs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_snapshot_bound_counts();

CREATE CONSTRAINT TRIGGER gptl_snapshots_validate_snapshot_bound_counts
AFTER INSERT ON gptl_snapshots
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_snapshot_bound_counts();

CREATE CONSTRAINT TRIGGER gptl_citations_validate_snapshot_bound_counts
AFTER INSERT ON gptl_citations
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_snapshot_bound_counts();

CREATE CONSTRAINT TRIGGER gptl_bound_versions_validate_snapshot_bound_counts
AFTER INSERT ON gptl_bound_versions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_snapshot_bound_counts();
