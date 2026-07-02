CREATE FUNCTION gptl_validate_source_raw_byte_pair() RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $$
DECLARE
    artifact_count bigint;
    raw_count bigint;
BEGIN
    SELECT count(*) INTO artifact_count
    FROM gptl_source_artifacts
    WHERE source_artifact_id = NEW.source_artifact_id;

    SELECT count(*) INTO raw_count
    FROM gptl_source_raw_bytes
    WHERE source_artifact_id = NEW.source_artifact_id;

    IF artifact_count <> 1 OR raw_count <> 1 THEN
        RAISE EXCEPTION 'GPTL source artifact raw byte pair is incomplete';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM gptl_source_artifacts AS artifact
        JOIN gptl_source_raw_bytes AS raw
            ON raw.source_artifact_id = artifact.source_artifact_id
        WHERE artifact.source_artifact_id = NEW.source_artifact_id
            AND (
                artifact.raw_byte_hash <> raw.raw_byte_hash
                OR artifact.byte_length <> raw.byte_length
                OR raw.byte_length <> octet_length(raw.raw_bytes)
            )
    ) THEN
        RAISE EXCEPTION 'GPTL source artifact raw byte metadata mismatch';
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER gptl_source_artifacts_validate_raw_byte_pair
AFTER INSERT ON gptl_source_artifacts
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_source_raw_byte_pair();

CREATE CONSTRAINT TRIGGER gptl_source_raw_bytes_validate_pair
AFTER INSERT ON gptl_source_raw_bytes
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION gptl_validate_source_raw_byte_pair();
