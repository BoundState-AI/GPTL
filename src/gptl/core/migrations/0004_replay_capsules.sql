ALTER TABLE gptl_runs
    ADD COLUMN replay_capsule_count integer NOT NULL DEFAULT 0
        CHECK (replay_capsule_count IN (0, 1));

ALTER TABLE gptl_runs
    ALTER COLUMN replay_capsule_count DROP DEFAULT;

CREATE TABLE gptl_replay_capsules (
    run_id text PRIMARY KEY REFERENCES gptl_runs(run_id),
    algorithm_id text NOT NULL,
    recipe_schema_version text NOT NULL,
    replay_policy_logical_id text NOT NULL,
    replay_policy_version_id text NOT NULL,
    replay_policy_version_number integer NOT NULL CHECK (replay_policy_version_number >= 0),
    replay_policy_content_hash char(64) NOT NULL
        CHECK (replay_policy_content_hash ~ '^[0-9a-f]{64}$'),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    record_type text NOT NULL CHECK (record_type = 'REPLAY_CAPSULE'),
    schema_version text NOT NULL,
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256')
);

CREATE TRIGGER gptl_replay_capsules_append_only
BEFORE UPDATE OR DELETE ON gptl_replay_capsules
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_replay_capsules_reject_truncate
BEFORE TRUNCATE ON gptl_replay_capsules
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE FUNCTION gptl_validate_replay_capsule_count() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
DECLARE
    expected_capsules integer;
    actual_capsules bigint;
BEGIN
    SELECT replay_capsule_count INTO expected_capsules
    FROM gptl_runs
    WHERE run_id = NEW.run_id;

    SELECT count(*) INTO actual_capsules
    FROM gptl_replay_capsules
    WHERE run_id = NEW.run_id;

    IF expected_capsules IS NULL OR actual_capsules <> expected_capsules THEN
        RAISE EXCEPTION 'GPTL replay capsule count does not match committed rows';
    END IF;
    RETURN NULL;
END;
$$;

-- The run row must exist before its capsule FK can be inserted; the deferred
-- count gate prevents either half of that valid transaction from committing alone.
CREATE CONSTRAINT TRIGGER gptl_runs_validate_replay_capsule_count
AFTER INSERT ON gptl_runs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_replay_capsule_count();

CREATE CONSTRAINT TRIGGER gptl_replay_capsules_validate_count
AFTER INSERT ON gptl_replay_capsules
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_replay_capsule_count();
