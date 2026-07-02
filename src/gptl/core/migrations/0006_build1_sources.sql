CREATE TABLE gptl_source_artifacts (
    source_artifact_id text PRIMARY KEY,
    source_logical_id text NOT NULL,
    source_version_id text NOT NULL,
    source_version_number integer NOT NULL CHECK (source_version_number >= 0),
    source_content_hash char(64) NOT NULL CHECK (source_content_hash ~ '^[0-9a-f]{64}$'),
    raw_byte_hash char(64) NOT NULL CHECK (raw_byte_hash ~ '^[0-9a-f]{64}$'),
    byte_length bigint NOT NULL CHECK (byte_length >= 0),
    media_type text NOT NULL,
    source_class_id text NOT NULL,
    parser_status text NOT NULL CHECK (
        parser_status IN (
            'UNPARSED',
            'PARSER_UNAVAILABLE',
            'PARSER_UNSUPPORTED',
            'PARSER_READY',
            'PARSER_FAILED'
        )
    ),
    payload_hash char(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    record_type text NOT NULL CHECK (record_type = 'SOURCE_ARTIFACT'),
    schema_version text NOT NULL CHECK (schema_version = 'gptl.build1.source-artifact.v1'),
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256'),
    UNIQUE (source_logical_id, source_version_id)
);

CREATE TABLE gptl_source_raw_bytes (
    source_artifact_id text PRIMARY KEY REFERENCES gptl_source_artifacts(source_artifact_id),
    raw_byte_hash char(64) NOT NULL CHECK (raw_byte_hash ~ '^[0-9a-f]{64}$'),
    byte_length bigint NOT NULL CHECK (byte_length >= 0),
    raw_bytes bytea NOT NULL,
    record_type text NOT NULL CHECK (record_type = 'SOURCE_RAW_BYTES'),
    schema_version text NOT NULL CHECK (schema_version = 'gptl.build1.source-artifact.v1'),
    hash_algorithm text NOT NULL CHECK (hash_algorithm = 'SHA-256')
);

CREATE TRIGGER gptl_source_artifacts_append_only
BEFORE UPDATE OR DELETE ON gptl_source_artifacts
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_source_raw_bytes_append_only
BEFORE UPDATE OR DELETE ON gptl_source_raw_bytes
FOR EACH ROW EXECUTE FUNCTION gptl_reject_mutation();

CREATE TRIGGER gptl_source_artifacts_reject_truncate
BEFORE TRUNCATE ON gptl_source_artifacts
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();

CREATE TRIGGER gptl_source_raw_bytes_reject_truncate
BEFORE TRUNCATE ON gptl_source_raw_bytes
FOR EACH STATEMENT EXECUTE FUNCTION gptl_reject_truncate();
