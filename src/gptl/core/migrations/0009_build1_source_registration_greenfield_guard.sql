DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM gptl_source_artifacts AS artifact
        LEFT JOIN gptl_source_registration_audit_events AS audit
            ON audit.source_artifact_id = artifact.source_artifact_id
        WHERE audit.source_artifact_id IS NULL
    ) THEN
        RAISE EXCEPTION 'GPTL source registration audit migration requires greenfield source artifacts or explicit backfill';
    END IF;
END;
$$;
