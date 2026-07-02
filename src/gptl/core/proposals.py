"""Build 1 typed proposal contracts."""

from __future__ import annotations

from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gptl.core.canonical import canonical_sha256
from gptl.core.records import GovernedRef, governed_record_content_hash, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    LogicalId,
    NonNegativeInt,
    OpaqueId,
    PositiveInt,
    Sha256Hex,
    TermId,
    UnitId,
)
from gptl.mie.predicates import EnumValue, NumericValue, ScalarValue

TYPED_VALUE_PROPOSAL_SCHEMA_VERSION: Final = "gptl.build1.typed-value-proposal.v1"
TYPED_VALUE_PROPOSAL_RECORD_TYPE: Final = "TYPED_VALUE_PROPOSAL"
ALGORITHM_REGISTRY_ENTRY_SCHEMA_VERSION: Final = "gptl.build1.algorithm-registry-entry.v1"
ALGORITHM_REGISTRY_ENTRY_RECORD_TYPE: Final = "ALGORITHM_REGISTRY_ENTRY"
PARSE_ATTEMPT_SCHEMA_VERSION: Final = "gptl.build1.parse-attempt.v1"
PARSE_ATTEMPT_RECORD_TYPE: Final = "PARSE_ATTEMPT"
HASH_ALGORITHM: Final = "SHA-256"
SOURCE_LOCAL_LOGICAL_ID_PREFIX: Final = "build1.source-local"

PROPOSAL_READY_REASON_ID: Final = TermId("build1.proposal.ready-for-ratification")
PROPOSAL_VALIDATION_FAILED_REASON_ID: Final = TermId("build1.proposal.validation-failed")
PROPOSAL_CONFIGURATION_INVALID_REASON_ID: Final = TermId(
    "build1.proposal.configuration-invalid"
)
PROPOSAL_CONTEXT_KEY_INVALID_REASON_ID: Final = TermId(
    "build1.proposal.context-key-invalid"
)
PROPOSAL_TARGET_SCHEMA_MISMATCH_REASON_ID: Final = TermId(
    "build1.proposal.target-schema-mismatch"
)
PROPOSAL_VALUE_KIND_INVALID_REASON_ID: Final = TermId("build1.proposal.value-kind-invalid")
PROPOSAL_UNIT_UNKNOWN_REASON_ID: Final = TermId("build1.proposal.unit-unknown")
PROPOSAL_ENUM_TERM_UNKNOWN_REASON_ID: Final = TermId("build1.proposal.enum-term-unknown")
PROPOSAL_SOURCE_MISMATCH_REASON_ID: Final = TermId("build1.proposal.source-mismatch")
PROPOSAL_EVIDENCE_UNSUPPORTED_REASON_ID: Final = TermId(
    "build1.proposal.evidence-unsupported"
)
PROPOSAL_EVIDENCE_BOUNDS_INVALID_REASON_ID: Final = TermId(
    "build1.proposal.evidence-bounds-invalid"
)
PROPOSAL_ALGORITHM_UNRESOLVED_REASON_ID: Final = TermId(
    "build1.proposal.algorithm-unresolved"
)
PROPOSAL_PARSE_ATTEMPT_REQUIRED_REASON_ID: Final = TermId(
    "build1.proposal.parse-attempt-required"
)
PROPOSAL_PARSE_ATTEMPT_INVALID_REASON_ID: Final = TermId(
    "build1.proposal.parse-attempt-invalid"
)
PROPOSAL_IDENTITY_UNRESOLVED_REASON_ID: Final = TermId(
    "build1.proposal.identity-unresolved"
)
PROPOSAL_IDENTITY_COLLISION_REASON_ID: Final = TermId(
    "build1.proposal.identity-collision"
)
PROPOSAL_DUPLICATE_VERSION_NUMBER_REASON_ID: Final = TermId(
    "build1.proposal.duplicate-version-number"
)
PROPOSAL_NON_MONOTONIC_VERSION_NUMBER_REASON_ID: Final = TermId(
    "build1.proposal.non-monotonic-version-number"
)

ContextValue = str | int | bool


class ContextDimensionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: OpaqueId
    value_kind: Literal["TERM", "TEXT", "INTEGER", "BOOLEAN"]


class TargetFieldSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_schema_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    target_record_type: TermId
    target_schema_version: OpaqueId
    semantic_field_path: OpaqueId
    value_kind: Literal["NUMERIC", "ENUM"]
    canonical_unit_id: UnitId | None = None
    allowed_terms: tuple[TermId, ...] = ()
    context_dimensions: tuple[ContextDimensionDefinition, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def sort_schema_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "allowed_terms" in normalized:
            normalized["allowed_terms"] = tuple(sorted(normalized["allowed_terms"]))
        if "context_dimensions" in normalized:
            normalized["context_dimensions"] = tuple(
                sorted(
                    normalized["context_dimensions"],
                    key=lambda item: str(_field_value(item, "key")),
                )
            )
        return normalized

    @model_validator(mode="after")
    def validate_schema(self) -> TargetFieldSchema:
        if self.value_kind == "NUMERIC":
            if self.canonical_unit_id is None or self.allowed_terms:
                raise ValueError("numeric proposal field schema is inconsistent")
        elif self.canonical_unit_id is not None or not self.allowed_terms:
            raise ValueError("enum proposal field schema is inconsistent")
        if self.allowed_terms != tuple(sorted(set(self.allowed_terms))):
            raise ValueError("proposal allowed terms must be unique and sorted")
        context_keys = tuple(item.key for item in self.context_dimensions)
        if context_keys != tuple(sorted(set(context_keys))):
            raise ValueError("proposal context dimensions must be unique and sorted")
        return self


class ProposalTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target_record_type: TermId
    target_logical_id: LogicalId
    target_schema_version: OpaqueId
    semantic_field_path: OpaqueId
    context_key: dict[str, ContextValue]


class AlgorithmRegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.algorithm-registry-entry.v1"]
    record_type: Literal["ALGORITHM_REGISTRY_ENTRY"]
    hash_algorithm: Literal["SHA-256"]
    algorithm_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    purpose: Literal["PARSER", "DECODER", "IDENTITY", "LOCATOR_DERIVATION"]
    executable_module: OpaqueId
    executable_name: OpaqueId
    source_digest: Sha256Hex
    supported_input_class_id: TermId
    output_contract_id: TermId
    parameter_schema_hash: Sha256Hex
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_evidence_refs(cls, value: object) -> object:
        if not isinstance(value, dict) or "evidence_refs" not in value:
            return value
        normalized = dict(value)
        normalized["evidence_refs"] = sorted_unique_refs(tuple(normalized["evidence_refs"]))
        return normalized

    @model_validator(mode="after")
    def validate_entry(self) -> AlgorithmRegistryEntry:
        if not self.evidence_refs:
            raise ValueError("algorithm registry entry requires evidence references")
        return self


class AlgorithmRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_ref: GovernedRef
    entries: tuple[AlgorithmRegistryEntry, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_entries(cls, value: object) -> object:
        if not isinstance(value, dict) or "entries" not in value:
            return value
        normalized = dict(value)
        normalized["entries"] = tuple(
            sorted(normalized["entries"], key=lambda item: _ref_value_key(item, "algorithm_ref"))
        )
        return normalized

    @model_validator(mode="after")
    def validate_entries(self) -> AlgorithmRegistry:
        keys = tuple(_ref_key(item.algorithm_ref) for item in self.entries)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("algorithm registry entries must be unique and sorted")
        return self


class ParseAttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.parse-attempt.v1"]
    record_type: Literal["PARSE_ATTEMPT"]
    hash_algorithm: Literal["SHA-256"]
    parse_attempt_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    source_artifact_ref: GovernedRef
    algorithm_refs: tuple[GovernedRef, ...]
    parser_parameters_hash: Sha256Hex
    policy_refs: tuple[GovernedRef, ...]
    input_hash: Sha256Hex
    derived_output_hash: Sha256Hex | None
    diagnostics: tuple[TermId, ...]
    terminal_status: Literal["SUCCEEDED", "FAILED"]
    recorded_at: CanonicalTimestamp

    @model_validator(mode="before")
    @classmethod
    def sort_parse_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "algorithm_refs" in normalized:
            normalized["algorithm_refs"] = sorted_unique_refs(tuple(normalized["algorithm_refs"]))
        if "policy_refs" in normalized:
            normalized["policy_refs"] = sorted_unique_refs(tuple(normalized["policy_refs"]))
        if "diagnostics" in normalized:
            normalized["diagnostics"] = tuple(sorted(normalized["diagnostics"]))
        return normalized

    @model_validator(mode="after")
    def validate_attempt(self) -> ParseAttemptRecord:
        if not self.algorithm_refs:
            raise ValueError("parse attempt requires at least one algorithm reference")
        if self.terminal_status == "SUCCEEDED" and self.derived_output_hash is None:
            raise ValueError("successful parse attempt requires derived output hash")
        return self


class RawByteRangeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    locator_class: Literal["RAW_BYTE_RANGE"]
    source_artifact_ref: GovernedRef
    start_byte: NonNegativeInt
    end_byte: PositiveInt
    raw_byte_hash: Sha256Hex

    @model_validator(mode="after")
    def validate_range(self) -> RawByteRangeEvidence:
        if self.end_byte <= self.start_byte:
            raise ValueError("raw byte range end must exceed start")
        return self


class Utf8LineRangeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    locator_class: Literal["UTF8_LINE_RANGE"]
    source_artifact_ref: GovernedRef
    decoder_algorithm_ref: GovernedRef
    newline_policy_id: TermId
    start_line: PositiveInt
    end_line: PositiveInt
    decoded_text_hash: Sha256Hex

    @model_validator(mode="after")
    def validate_range(self) -> Utf8LineRangeEvidence:
        if self.end_line < self.start_line:
            raise ValueError("UTF-8 line range end cannot precede start")
        return self


class CsvCellRangeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    locator_class: Literal["CSV_CELL_RANGE"]
    source_artifact_ref: GovernedRef
    csv_parser_algorithm_ref: GovernedRef
    dialect_policy_ref: GovernedRef
    start_row: PositiveInt
    end_row: PositiveInt
    start_column: PositiveInt
    end_column: PositiveInt
    parsed_table_hash: Sha256Hex

    @model_validator(mode="after")
    def validate_range(self) -> CsvCellRangeEvidence:
        if self.end_row < self.start_row or self.end_column < self.start_column:
            raise ValueError("CSV cell range end cannot precede start")
        return self


class JsonPointerEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    locator_class: Literal["JSON_POINTER"]
    source_artifact_ref: GovernedRef
    json_parser_algorithm_ref: GovernedRef
    pointer: str
    parsed_json_hash: Sha256Hex

    @model_validator(mode="after")
    def validate_pointer(self) -> JsonPointerEvidence:
        if not self.pointer.startswith("/"):
            raise ValueError("JSON pointer evidence must use an absolute pointer")
        return self


class ProposalOnlyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    locator_class: Literal["PROPOSAL_ONLY_RENDERED_REGION"]
    source_artifact_ref: GovernedRef
    reason_id: TermId


ProposalEvidenceLocation = Annotated[
    RawByteRangeEvidence
    | Utf8LineRangeEvidence
    | CsvCellRangeEvidence
    | JsonPointerEvidence
    | ProposalOnlyEvidence,
    Field(discriminator="locator_class"),
]


class ExistingGovernedIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_mode: Literal["EXISTING_GOVERNED_REF"]
    target_ref: GovernedRef


class CallerSuppliedIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_mode: Literal["CALLER_SUPPLIED_IDENTITY"]
    source_identity_key: OpaqueId


class SourceLocalRecordKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key_class: Literal[
        "CALLER_SUPPLIED_SOURCE_KEY",
        "CSV_ROW",
        "JSON_POINTER",
        "UTF8_LINE_RANGE",
        "RAW_BYTE_RANGE",
    ]
    source_artifact_ref: GovernedRef
    local_discriminator: OpaqueId
    parse_attempt_ref: GovernedRef | None = None

    @model_validator(mode="after")
    def validate_key_source(self) -> SourceLocalRecordKey:
        if self.key_class in {"CSV_ROW", "JSON_POINTER", "UTF8_LINE_RANGE"}:
            if self.parse_attempt_ref is None:
                raise ValueError("parser-derived source-local key requires parse attempt")
        elif self.parse_attempt_ref is not None:
            raise ValueError("raw/caller source-local key cannot bind parse attempt")
        return self


class SourceLocalIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_mode: Literal["SOURCE_LOCAL_RECORD_IDENTITY_V1"]
    source_local_record_key: SourceLocalRecordKey


ProposalIdentity = Annotated[
    ExistingGovernedIdentity | CallerSuppliedIdentity | SourceLocalIdentity,
    Field(discriminator="identity_mode"),
]


class TypedValueProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.typed-value-proposal.v1"]
    record_type: Literal["TYPED_VALUE_PROPOSAL"]
    hash_algorithm: Literal["SHA-256"]
    proposal_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    source_artifact_ref: GovernedRef
    source_raw_byte_hash: Sha256Hex
    identity: ProposalIdentity
    claimed_proposer_ref: GovernedRef | None = None
    proposal_method: Literal["DETERMINISTIC_PARSER", "MODEL_ASSISTED", "MANUAL_TRANSLATION"]
    creation_event_ref: GovernedRef
    parse_attempt_ref: GovernedRef | None = None
    target: ProposalTarget
    proposed_value: ScalarValue
    evidence_location: ProposalEvidenceLocation
    validation_state: Literal[
        "PROPOSED",
        "VALIDATION_FAILED",
        "READY_FOR_RATIFICATION",
        "REJECTED",
        "SUPERSEDED",
    ]
    validation_errors: tuple[TermId, ...] = ()
    corrects_proposal_ref: GovernedRef | None = None

    @model_validator(mode="before")
    @classmethod
    def sort_validation_errors(cls, value: object) -> object:
        if not isinstance(value, dict) or "validation_errors" not in value:
            return value
        normalized = dict(value)
        normalized["validation_errors"] = tuple(sorted(normalized["validation_errors"]))
        return normalized

    @model_validator(mode="after")
    def validate_state_shape(self) -> TypedValueProposal:
        if self.validation_state == "READY_FOR_RATIFICATION" and self.validation_errors:
            raise ValueError("ready proposal cannot carry validation errors")
        if self.validation_state == "VALIDATION_FAILED" and not self.validation_errors:
            raise ValueError("failed proposal requires validation errors")
        if self.proposal_method != "DETERMINISTIC_PARSER" and self.parse_attempt_ref is not None:
            raise ValueError("non-parser proposal cannot bind parse attempt")
        return self


class ProposalValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["READY_FOR_RATIFICATION", "VALIDATION_FAILED"]
    reason_id: TermId
    proposal_ref: GovernedRef
    validation_errors: tuple[TermId, ...]
    active_value_key_hash: Sha256Hex | None


class ProposalVersionSequenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ACCEPTED", "CONFIGURATION_INVALID", "INTEGRITY_FAILURE"]
    reason_id: TermId
    proposal_ref: GovernedRef | None = None


class ProposalIdentitySetResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ACCEPTED", "INTEGRITY_FAILURE"]
    reason_id: TermId
    proposal_ref: GovernedRef | None = None


def context_key_hash(
    target: ProposalTarget,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(target.context_key, canonicalization_policy)


def active_value_key_hash(
    target: ProposalTarget,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return canonical_sha256(
        active_value_key_payload(target, canonicalization_policy),
        canonicalization_policy,
    )


def active_value_key_payload(
    target: ProposalTarget,
    canonicalization_policy: CanonicalizationPolicy,
) -> dict[str, object]:
    return {
        "target_record_type": target.target_record_type,
        "target_logical_id": target.target_logical_id,
        "semantic_field_path": target.semantic_field_path,
        "context_key_hash": context_key_hash(target, canonicalization_policy),
    }


def source_local_target_logical_id(
    scope_ref: GovernedRef,
    source_artifact_ref: GovernedRef,
    target_record_type: TermId,
    source_local_record_key: SourceLocalRecordKey,
    canonicalization_policy: CanonicalizationPolicy,
) -> LogicalId:
    digest = canonical_sha256(
        {
            "algorithm_id": "SOURCE_LOCAL_RECORD_IDENTITY_V1",
            "scope_ref": scope_ref,
            "source_artifact_ref": source_artifact_ref,
            "target_record_type": target_record_type,
            "source_local_record_key": source_local_record_key,
        },
        canonicalization_policy,
    )
    return LogicalId(f"{SOURCE_LOCAL_LOGICAL_ID_PREFIX}.{digest}")


def typed_value_proposal_content_hash(
    proposal: TypedValueProposal,
    canonicalization_policy: CanonicalizationPolicy,
) -> Sha256Hex:
    return governed_record_content_hash(proposal, "proposal_ref", canonicalization_policy)


def finalize_typed_value_proposal(
    proposal: TypedValueProposal,
    canonicalization_policy: CanonicalizationPolicy,
) -> TypedValueProposal:
    content_hash = typed_value_proposal_content_hash(proposal, canonicalization_policy)
    updated_ref = proposal.proposal_ref.model_copy(update={"content_hash": content_hash})
    return proposal.model_copy(update={"proposal_ref": updated_ref})


def evaluate_typed_value_proposal(
    proposal: TypedValueProposal,
    source_artifact_ref: GovernedRef,
    source_raw_byte_hash: Sha256Hex,
    source_byte_length: NonNegativeInt,
    target_schema: TargetFieldSchema,
    algorithm_registry: AlgorithmRegistry,
    parse_attempts: tuple[ParseAttemptRecord, ...],
    canonicalization_policy: CanonicalizationPolicy,
) -> ProposalValidationResult:
    issues: set[TermId] = set()
    if proposal.source_artifact_ref != source_artifact_ref:
        issues.add(PROPOSAL_SOURCE_MISMATCH_REASON_ID)
    if proposal.source_raw_byte_hash != source_raw_byte_hash:
        issues.add(PROPOSAL_SOURCE_MISMATCH_REASON_ID)
    if proposal.canonicalization_policy_ref != target_schema.canonicalization_policy_ref:
        issues.add(PROPOSAL_TARGET_SCHEMA_MISMATCH_REASON_ID)
    issues.update(_target_issues(proposal.target, target_schema))
    issues.update(_value_issues(proposal.proposed_value, target_schema))
    issues.update(
        _evidence_issues(
            proposal.evidence_location,
            source_artifact_ref,
            source_raw_byte_hash,
            source_byte_length,
            algorithm_registry,
        )
    )
    issues.update(_parse_issues(proposal, source_artifact_ref, algorithm_registry, parse_attempts))
    issues.update(_identity_issues(proposal, canonicalization_policy))

    ordered_issues = tuple(sorted(issues))
    if ordered_issues:
        return ProposalValidationResult(
            status="VALIDATION_FAILED",
            reason_id=PROPOSAL_VALIDATION_FAILED_REASON_ID,
            proposal_ref=proposal.proposal_ref,
            validation_errors=ordered_issues,
            active_value_key_hash=None,
        )
    return ProposalValidationResult(
        status="READY_FOR_RATIFICATION",
        reason_id=PROPOSAL_READY_REASON_ID,
        proposal_ref=proposal.proposal_ref,
        validation_errors=(),
        active_value_key_hash=active_value_key_hash(proposal.target, canonicalization_policy),
    )


def validate_proposal_version_sequence(
    proposals: tuple[TypedValueProposal, ...],
) -> ProposalVersionSequenceResult:
    latest_by_logical_id: dict[str, int] = {}
    seen_versions: set[tuple[str, int]] = set()
    for proposal in proposals:
        logical_id = proposal.proposal_ref.logical_id
        version_number = proposal.proposal_ref.version_number
        key = (logical_id, version_number)
        if key in seen_versions:
            return ProposalVersionSequenceResult(
                status="INTEGRITY_FAILURE",
                reason_id=PROPOSAL_DUPLICATE_VERSION_NUMBER_REASON_ID,
                proposal_ref=proposal.proposal_ref,
            )
        seen_versions.add(key)
        latest = latest_by_logical_id.get(logical_id)
        if latest is not None and version_number <= latest:
            return ProposalVersionSequenceResult(
                status="CONFIGURATION_INVALID",
                reason_id=PROPOSAL_NON_MONOTONIC_VERSION_NUMBER_REASON_ID,
                proposal_ref=proposal.proposal_ref,
            )
        latest_by_logical_id[logical_id] = version_number
    return ProposalVersionSequenceResult(
        status="ACCEPTED",
        reason_id=PROPOSAL_READY_REASON_ID,
    )


def validate_source_local_identity_set(
    proposals: tuple[TypedValueProposal, ...],
    canonicalization_policy: CanonicalizationPolicy,
) -> ProposalIdentitySetResult:
    inputs_by_logical_id: dict[str, str] = {}
    for proposal in proposals:
        identity = proposal.identity
        if not isinstance(identity, SourceLocalIdentity):
            continue
        identity_hash = canonical_sha256(
            {
                "algorithm_id": "SOURCE_LOCAL_RECORD_IDENTITY_V1",
                "scope_ref": proposal.evidence_scope_ref,
                "source_artifact_ref": proposal.source_artifact_ref,
                "target_record_type": proposal.target.target_record_type,
                "source_local_record_key": identity.source_local_record_key,
            },
            canonicalization_policy,
        )
        existing_hash = inputs_by_logical_id.get(proposal.target.target_logical_id)
        if existing_hash is not None and existing_hash != identity_hash:
            return ProposalIdentitySetResult(
                status="INTEGRITY_FAILURE",
                reason_id=PROPOSAL_IDENTITY_COLLISION_REASON_ID,
                proposal_ref=proposal.proposal_ref,
            )
        inputs_by_logical_id[proposal.target.target_logical_id] = identity_hash
    return ProposalIdentitySetResult(status="ACCEPTED", reason_id=PROPOSAL_READY_REASON_ID)


def _target_issues(target: ProposalTarget, schema: TargetFieldSchema) -> set[TermId]:
    issues: set[TermId] = set()
    if (
        target.target_record_type != schema.target_record_type
        or target.target_schema_version != schema.target_schema_version
        or target.semantic_field_path != schema.semantic_field_path
    ):
        issues.add(PROPOSAL_TARGET_SCHEMA_MISMATCH_REASON_ID)
    expected_keys = tuple(item.key for item in schema.context_dimensions)
    if tuple(sorted(target.context_key)) != expected_keys:
        issues.add(PROPOSAL_CONTEXT_KEY_INVALID_REASON_ID)
        return issues
    definitions = {item.key: item for item in schema.context_dimensions}
    for key, value in target.context_key.items():
        if not _context_value_matches(value, definitions[key].value_kind):
            issues.add(PROPOSAL_CONTEXT_KEY_INVALID_REASON_ID)
    return issues


def _value_issues(value: ScalarValue, schema: TargetFieldSchema) -> set[TermId]:
    if isinstance(value, NumericValue):
        if schema.value_kind != "NUMERIC":
            return {PROPOSAL_VALUE_KIND_INVALID_REASON_ID}
        if value.unit_id != schema.canonical_unit_id:
            return {PROPOSAL_UNIT_UNKNOWN_REASON_ID}
        return set()
    if schema.value_kind != "ENUM":
        return {PROPOSAL_VALUE_KIND_INVALID_REASON_ID}
    enum_value = value
    if isinstance(enum_value, EnumValue) and enum_value.value not in schema.allowed_terms:
        return {PROPOSAL_ENUM_TERM_UNKNOWN_REASON_ID}
    return set()


def _evidence_issues(
    evidence: ProposalEvidenceLocation,
    source_artifact_ref: GovernedRef,
    source_raw_byte_hash: Sha256Hex,
    source_byte_length: NonNegativeInt,
    algorithm_registry: AlgorithmRegistry,
) -> set[TermId]:
    issues: set[TermId] = set()
    if evidence.source_artifact_ref != source_artifact_ref:
        issues.add(PROPOSAL_SOURCE_MISMATCH_REASON_ID)
    if isinstance(evidence, ProposalOnlyEvidence):
        issues.add(PROPOSAL_EVIDENCE_UNSUPPORTED_REASON_ID)
        return issues
    if isinstance(evidence, RawByteRangeEvidence):
        if evidence.raw_byte_hash != source_raw_byte_hash:
            issues.add(PROPOSAL_SOURCE_MISMATCH_REASON_ID)
        if evidence.end_byte > source_byte_length:
            issues.add(PROPOSAL_EVIDENCE_BOUNDS_INVALID_REASON_ID)
        return issues
    algorithm_ref = _evidence_algorithm_ref(evidence)
    if algorithm_ref is not None and _active_algorithm(algorithm_registry, algorithm_ref) is None:
        issues.add(PROPOSAL_ALGORITHM_UNRESOLVED_REASON_ID)
    return issues


def _parse_issues(
    proposal: TypedValueProposal,
    source_artifact_ref: GovernedRef,
    algorithm_registry: AlgorithmRegistry,
    parse_attempts: tuple[ParseAttemptRecord, ...],
) -> set[TermId]:
    if proposal.parse_attempt_ref is None:
        if _requires_parse_attempt(proposal):
            return {PROPOSAL_PARSE_ATTEMPT_REQUIRED_REASON_ID}
        return set()
    attempt = _parse_attempt_by_ref(parse_attempts, proposal.parse_attempt_ref)
    if (
        attempt is None
        or attempt.source_artifact_ref != source_artifact_ref
        or attempt.input_hash != proposal.source_raw_byte_hash
        or attempt.terminal_status != "SUCCEEDED"
    ):
        return {PROPOSAL_PARSE_ATTEMPT_INVALID_REASON_ID}
    evidence_algorithm_ref = _evidence_algorithm_ref(proposal.evidence_location)
    if evidence_algorithm_ref is not None and evidence_algorithm_ref not in attempt.algorithm_refs:
        return {PROPOSAL_PARSE_ATTEMPT_INVALID_REASON_ID}
    for algorithm_ref in attempt.algorithm_refs:
        if _active_algorithm(algorithm_registry, algorithm_ref) is None:
            return {PROPOSAL_ALGORITHM_UNRESOLVED_REASON_ID}
    return set()


def _identity_issues(
    proposal: TypedValueProposal,
    canonicalization_policy: CanonicalizationPolicy,
) -> set[TermId]:
    identity = proposal.identity
    if isinstance(identity, ExistingGovernedIdentity):
        if proposal.target.target_logical_id != identity.target_ref.logical_id:
            return {PROPOSAL_IDENTITY_UNRESOLVED_REASON_ID}
        return set()
    if isinstance(identity, CallerSuppliedIdentity):
        return set()
    if identity.source_local_record_key.source_artifact_ref != proposal.source_artifact_ref:
        return {PROPOSAL_IDENTITY_UNRESOLVED_REASON_ID}
    if (
        identity.source_local_record_key.parse_attempt_ref is not None
        and identity.source_local_record_key.parse_attempt_ref != proposal.parse_attempt_ref
    ):
        return {PROPOSAL_PARSE_ATTEMPT_INVALID_REASON_ID}
    expected_logical_id = source_local_target_logical_id(
        proposal.evidence_scope_ref,
        proposal.source_artifact_ref,
        proposal.target.target_record_type,
        identity.source_local_record_key,
        canonicalization_policy,
    )
    if proposal.target.target_logical_id != expected_logical_id:
        return {PROPOSAL_IDENTITY_UNRESOLVED_REASON_ID}
    return set()


def _requires_parse_attempt(proposal: TypedValueProposal) -> bool:
    if proposal.proposal_method == "DETERMINISTIC_PARSER":
        return True
    identity = proposal.identity
    if isinstance(identity, SourceLocalIdentity):
        if identity.source_local_record_key.parse_attempt_ref is not None:
            return True
    return isinstance(
        proposal.evidence_location,
        (Utf8LineRangeEvidence, CsvCellRangeEvidence, JsonPointerEvidence),
    )


def _parse_attempt_by_ref(
    attempts: tuple[ParseAttemptRecord, ...],
    parse_attempt_ref: GovernedRef,
) -> ParseAttemptRecord | None:
    for attempt in attempts:
        if attempt.parse_attempt_ref == parse_attempt_ref:
            return attempt
    return None


def _active_algorithm(
    registry: AlgorithmRegistry,
    algorithm_ref: GovernedRef,
) -> AlgorithmRegistryEntry | None:
    for entry in registry.entries:
        if entry.algorithm_ref == algorithm_ref and entry.lifecycle_state == "ACTIVE":
            return entry
    return None


def _evidence_algorithm_ref(evidence: ProposalEvidenceLocation) -> GovernedRef | None:
    if isinstance(evidence, Utf8LineRangeEvidence):
        return evidence.decoder_algorithm_ref
    if isinstance(evidence, CsvCellRangeEvidence):
        return evidence.csv_parser_algorithm_ref
    if isinstance(evidence, JsonPointerEvidence):
        return evidence.json_parser_algorithm_ref
    return None


def _context_value_matches(value: ContextValue, value_kind: str) -> bool:
    if value_kind in {"TERM", "TEXT"}:
        return isinstance(value, str)
    if value_kind == "INTEGER":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_kind == "BOOLEAN":
        return isinstance(value, bool)
    return False


def _ref_key(ref: GovernedRef) -> tuple[str, str]:
    return (ref.logical_id, ref.version_id)


def _ref_value_key(value: object, field_name: str) -> tuple[str, str]:
    ref = _field_value(value, field_name)
    if isinstance(ref, GovernedRef):
        return _ref_key(ref)
    if isinstance(ref, dict):
        return (str(ref["logical_id"]), str(ref["version_id"]))
    raise ValueError("governed reference values must be model or mapping values")


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, BaseModel):
        return getattr(value, field_name)
    if isinstance(value, dict):
        return value[field_name]
    raise ValueError("proposal values must be model or mapping values")
