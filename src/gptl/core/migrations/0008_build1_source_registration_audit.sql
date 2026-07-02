CREATE TABLE gptl_source_registration_audit_events (
    event_id text PRIMARY KEY,
    source_artifact_id text NOT NULL REFERENCES gptl_source_artifacts(source_artifact_id),
    sequence integer NOT NULL CHECK (sequence = 0),
    reason_id text NOT NULL,
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    record_type text NOT NULL CHECK (record_type = 'SOURCE_REGISTRATION_AUDIT_EVENT'),
    schema_version text NOT NULL CHECK (schema_version = 'gptl.build1.source-registration-audit.v1'),
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256'),
    UNIQUE (source_artifact_id, sequence)
);

CREATE TRIGGER gptl_source_registration_audit_events_append_only
BEFORE UPDATE OR DELETE ON gptl_source_registration_audit_events
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_source_registration_audit_events_reject_truncate
BEFORE TRUNCATE ON gptl_source_registration_audit_events
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE FUNCTION gptl_validate_source_registration_audit_count() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
DECLARE
    artifact_count bigint;
    audit_count bigint;
BEGIN
    SELECT count(*) INTO artifact_count
    FROM gptl_source_artifacts
    WHERE source_artifact_id = NEW.source_artifact_id;

    SELECT count(*) INTO audit_count
    FROM gptl_source_registration_audit_events
    WHERE source_artifact_id = NEW.source_artifact_id;

    IF artifact_count <> 1 OR audit_count <> 1 THEN
        RAISE EXCEPTION 'GPTL source registration audit count does not match committed source artifact';
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER gptl_source_artifacts_validate_audit_count
AFTER INSERT ON gptl_source_artifacts
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_source_registration_audit_count();

CREATE CONSTRAINT TRIGGER gptl_source_registration_audit_events_validate_count
AFTER INSERT ON gptl_source_registration_audit_events
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_source_registration_audit_count();
