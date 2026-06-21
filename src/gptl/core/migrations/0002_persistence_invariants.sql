-- Constraint triggers are not retroactive; installing them over invalid history
-- would create false assurance that every persisted run satisfies the invariant.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM gptl_runs AS run
        LEFT JOIN gptl_audit_events AS event ON event.run_id = run.run_id
        GROUP BY run.run_id, run.audit_count
        HAVING count(event.event_id) <> run.audit_count
    ) THEN
        RAISE EXCEPTION 'existing GPTL run has an inconsistent audit count';
    END IF;
END;
$$;

ALTER FUNCTION gptl_reject_mutation() SET search_path FROM CURRENT;
ALTER FUNCTION gptl_reject_preflight_binding() SET search_path FROM CURRENT;

CREATE FUNCTION gptl_validate_audit_count() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
DECLARE
    expected_count integer;
    actual_count bigint;
BEGIN
    SELECT audit_count INTO expected_count
    FROM gptl_runs
    WHERE run_id = NEW.run_id;

    SELECT count(*) INTO actual_count
    FROM gptl_audit_events
    WHERE run_id = NEW.run_id;

    IF expected_count IS NULL OR actual_count <> expected_count THEN
        RAISE EXCEPTION 'GPTL run audit count does not match committed audit rows';
    END IF;
    RETURN NULL;
END;
$$;

-- Immediate validation would reject the required run-before-audit insert order;
-- deferral checks the invariant only after the transaction has the complete set.
CREATE CONSTRAINT TRIGGER gptl_runs_validate_audit_count
AFTER INSERT ON gptl_runs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_audit_count();

CREATE CONSTRAINT TRIGGER gptl_audit_events_validate_audit_count
AFTER INSERT ON gptl_audit_events
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_audit_count();

CREATE FUNCTION gptl_reject_truncate() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
BEGIN
    RAISE EXCEPTION 'GPTL committed records reject truncate';
END;
$$;

CREATE TRIGGER gptl_schema_migrations_reject_truncate
BEFORE TRUNCATE ON gptl_schema_migrations
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_runs_reject_truncate
BEFORE TRUNCATE ON gptl_runs
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_audit_events_reject_truncate
BEFORE TRUNCATE ON gptl_audit_events
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_snapshots_reject_truncate
BEFORE TRUNCATE ON gptl_snapshots
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_citations_reject_truncate
BEFORE TRUNCATE ON gptl_citations
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_bound_versions_reject_truncate
BEFORE TRUNCATE ON gptl_bound_versions
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();
