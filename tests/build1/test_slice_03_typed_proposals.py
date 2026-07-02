from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.core.proposals import (
    ALGORITHM_REGISTRY_ENTRY_RECORD_TYPE,
    ALGORITHM_REGISTRY_ENTRY_SCHEMA_VERSION,
    HASH_ALGORITHM,
    PARSE_ATTEMPT_RECORD_TYPE,
    PARSE_ATTEMPT_SCHEMA_VERSION,
    PROPOSAL_ALGORITHM_UNRESOLVED_REASON_ID,
    PROPOSAL_CONTEXT_KEY_INVALID_REASON_ID,
    PROPOSAL_EVIDENCE_UNSUPPORTED_REASON_ID,
    PROPOSAL_IDENTITY_COLLISION_REASON_ID,
    PROPOSAL_IDENTITY_UNRESOLVED_REASON_ID,
    PROPOSAL_NON_MONOTONIC_VERSION_NUMBER_REASON_ID,
    PROPOSAL_PARSE_ATTEMPT_INVALID_REASON_ID,
    PROPOSAL_PARSE_ATTEMPT_REQUIRED_REASON_ID,
    PROPOSAL_UNIT_UNKNOWN_REASON_ID,
    PROPOSAL_VALIDATION_FAILED_REASON_ID,
    TYPED_VALUE_PROPOSAL_RECORD_TYPE,
    TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
    AlgorithmRegistry,
    AlgorithmRegistryEntry,
    ParseAttemptRecord,
    ProposalTarget,
    SourceLocalIdentity,
    SourceLocalRecordKey,
    TargetFieldSchema,
    TypedValueProposal,
    active_value_key_hash,
    context_key_hash,
    evaluate_typed_value_proposal,
    finalize_typed_value_proposal,
    source_local_target_logical_id,
    validate_proposal_version_sequence,
    validate_source_local_identity_set,
)
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import LogicalId, TermId, VersionId
from gptl.mie.predicates import NumericValue
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-06-30T12:00:00.000Z"
SOURCE_RAW_HASH = "a" * 64
SOURCE_BYTE_LENGTH = 128
DERIVED_OUTPUT_HASH = "b" * 64
PARAMETER_SCHEMA_HASH = "c" * 64
PARSER_SOURCE_DIGEST = "d" * 64
PARSE_PARAMETERS_HASH = "e" * 64
PARSED_TABLE_HASH = "f" * 64


def test_context_key_hash_is_order_independent_and_active_key_ignores_schema_version(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    first = _target(build1_ref_factory, context_key={"side": "side.left", "replicate": 1})
    second = _target(build1_ref_factory, context_key={"replicate": 1, "side": "side.left"})
    schema_v2 = first.model_copy(update={"target_schema_version": "schema.specimen.v2"})

    assert context_key_hash(first, policy) == context_key_hash(second, policy)
    assert active_value_key_hash(first, policy) == active_value_key_hash(schema_v2, policy)


def test_ready_proposal_requires_valid_source_target_evidence_and_value(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    proposal = _proposal(build1_ref_factory)

    result = _evaluate(build1_ref_factory, proposal)
    finalized = finalize_typed_value_proposal(proposal, policy)

    assert result.status == "READY_FOR_RATIFICATION"
    assert result.validation_errors == ()
    assert result.active_value_key_hash == active_value_key_hash(proposal.target, policy)
    assert finalized.proposal_ref.content_hash != proposal.proposal_ref.content_hash


@pytest.mark.parametrize(
    "context_key",
    (
        {"side": "side.left"},
        {"side": "side.left", "replicate": 1, "extra": "x"},
        {"side": "side.left", "replicate": True},
    ),
)
def test_context_key_must_match_target_schema_exactly(
    build1_ref_factory: Callable[[str], GovernedRef],
    context_key: dict[str, object],
) -> None:
    proposal = _proposal(
        build1_ref_factory,
        target=_target(build1_ref_factory, context_key=context_key),
    )

    result = _evaluate(build1_ref_factory, proposal)

    assert result.status == "VALIDATION_FAILED"
    assert PROPOSAL_CONTEXT_KEY_INVALID_REASON_ID in result.validation_errors


def test_numeric_proposal_requires_bound_decimal_policy_and_canonical_unit(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(
        build1_ref_factory,
        proposed_value={"kind": "NUMERIC", "value": Decimal("41.2500"), "unit_id": "unit.mpa"},
    )

    result = _evaluate(build1_ref_factory, proposal)

    assert result.reason_id == PROPOSAL_VALIDATION_FAILED_REASON_ID
    assert result.validation_errors == (PROPOSAL_UNIT_UNKNOWN_REASON_ID,)
    with pytest.raises(ValidationError):
        _proposal(
            build1_ref_factory,
            proposed_value={"kind": "NUMERIC", "value": 41.25, "unit_id": "unit.hrc"},
        )


def test_parser_derived_proposal_requires_exact_successful_parse_attempt(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    missing_attempt = _proposal(
        build1_ref_factory,
        proposal_method="DETERMINISTIC_PARSER",
        evidence_location=_csv_evidence(build1_ref_factory),
    )
    failed_attempt = missing_attempt.model_copy(
        update={"parse_attempt_ref": build1_ref_factory("build1.parse.csv.failed")}
    )

    missing_result = _evaluate(build1_ref_factory, missing_attempt)
    failed_result = _evaluate(
        build1_ref_factory,
        failed_attempt,
        parse_attempts=(
            _parse_attempt(
                build1_ref_factory,
                parse_attempt_ref=build1_ref_factory("build1.parse.csv.failed"),
                terminal_status="FAILED",
            ),
        ),
    )

    assert missing_result.validation_errors == (PROPOSAL_PARSE_ATTEMPT_REQUIRED_REASON_ID,)
    assert failed_result.validation_errors == (PROPOSAL_PARSE_ATTEMPT_INVALID_REASON_ID,)


def test_parser_and_locator_algorithms_must_resolve_to_active_registry_entries(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    parse_ref = build1_ref_factory("build1.parse.csv.1")
    proposal = _proposal(
        build1_ref_factory,
        proposal_method="DETERMINISTIC_PARSER",
        parse_attempt_ref=parse_ref,
        evidence_location=_csv_evidence(build1_ref_factory),
    )

    unresolved = _evaluate(
        build1_ref_factory,
        proposal,
        registry=_algorithm_registry(build1_ref_factory, entries=()),
        parse_attempts=(_parse_attempt(build1_ref_factory, parse_attempt_ref=parse_ref),),
    )
    inactive = _evaluate(
        build1_ref_factory,
        proposal,
        registry=_algorithm_registry(
            build1_ref_factory,
            entries=(_algorithm_entry(build1_ref_factory, lifecycle_state="INACTIVE"),),
        ),
        parse_attempts=(_parse_attempt(build1_ref_factory, parse_attempt_ref=parse_ref),),
    )

    assert unresolved.validation_errors == (PROPOSAL_ALGORITHM_UNRESOLVED_REASON_ID,)
    assert inactive.validation_errors == (PROPOSAL_ALGORITHM_UNRESOLVED_REASON_ID,)


def test_proposal_only_evidence_location_cannot_be_ready_for_ratification(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(
        build1_ref_factory,
        evidence_location={
            "locator_class": "PROPOSAL_ONLY_RENDERED_REGION",
            "source_artifact_ref": _source_ref(build1_ref_factory),
            "reason_id": "build1.proposal.ocr-not-bound",
        },
    )

    result = _evaluate(build1_ref_factory, proposal)

    assert result.status == "VALIDATION_FAILED"
    assert result.validation_errors == (PROPOSAL_EVIDENCE_UNSUPPORTED_REASON_ID,)


def test_source_local_identity_is_stable_across_value_corrections(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    source_key = _source_local_key(build1_ref_factory)
    target_logical_id = source_local_target_logical_id(
        build1_ref_factory("build1.scope.candidate"),
        _source_ref(build1_ref_factory),
        TermId("record.material-specimen"),
        source_key,
        policy,
    )
    first = _proposal(
        build1_ref_factory,
        target=_target(build1_ref_factory, target_logical_id=target_logical_id),
        identity=SourceLocalIdentity(
            identity_mode="SOURCE_LOCAL_RECORD_IDENTITY_V1",
            source_local_record_key=source_key,
        ),
        proposed_value={"kind": "NUMERIC", "value": Decimal("41.2500"), "unit_id": "unit.hrc"},
    )
    corrected = _proposal(
        build1_ref_factory,
        target=_target(build1_ref_factory, target_logical_id=target_logical_id),
        identity=SourceLocalIdentity(
            identity_mode="SOURCE_LOCAL_RECORD_IDENTITY_V1",
            source_local_record_key=source_key,
        ),
        proposed_value={"kind": "NUMERIC", "value": Decimal("42.0000"), "unit_id": "unit.hrc"},
    )

    assert _evaluate(build1_ref_factory, first).status == "READY_FOR_RATIFICATION"
    assert _evaluate(build1_ref_factory, corrected).status == "READY_FOR_RATIFICATION"
    assert first.target.target_logical_id == corrected.target.target_logical_id


def test_source_local_identity_mismatch_fails_closed(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    proposal = _proposal(
        build1_ref_factory,
        identity=SourceLocalIdentity(
            identity_mode="SOURCE_LOCAL_RECORD_IDENTITY_V1",
            source_local_record_key=_source_local_key(build1_ref_factory),
        ),
    )

    result = _evaluate(build1_ref_factory, proposal)

    assert result.validation_errors == (PROPOSAL_IDENTITY_UNRESOLVED_REASON_ID,)


def test_source_local_identity_collision_fails_closed(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    first_key = _source_local_key(build1_ref_factory)
    second_key = first_key.model_copy(update={"local_discriminator": "bytes.16-32"})
    target_logical_id = source_local_target_logical_id(
        build1_ref_factory("build1.scope.candidate"),
        _source_ref(build1_ref_factory),
        TermId("record.material-specimen"),
        first_key,
        policy,
    )
    first = _proposal(
        build1_ref_factory,
        target=_target(build1_ref_factory, target_logical_id=target_logical_id),
        identity=SourceLocalIdentity(
            identity_mode="SOURCE_LOCAL_RECORD_IDENTITY_V1",
            source_local_record_key=first_key,
        ),
    )
    collision = _proposal(
        build1_ref_factory,
        target=_target(build1_ref_factory, target_logical_id=target_logical_id),
        identity=SourceLocalIdentity(
            identity_mode="SOURCE_LOCAL_RECORD_IDENTITY_V1",
            source_local_record_key=second_key,
        ),
    )

    result = validate_source_local_identity_set((first, collision), policy)

    assert result.status == "INTEGRITY_FAILURE"
    assert result.reason_id == PROPOSAL_IDENTITY_COLLISION_REASON_ID


def test_version_sequence_rejects_duplicate_and_non_monotonic_versions(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    first = _proposal(build1_ref_factory, proposal_ref=_proposal_ref("build1.proposal.seq", 1))
    duplicate = _proposal(build1_ref_factory, proposal_ref=_proposal_ref("build1.proposal.seq", 1))
    second = _proposal(build1_ref_factory, proposal_ref=_proposal_ref("build1.proposal.seq", 2))

    duplicate_result = validate_proposal_version_sequence((first, duplicate))
    non_monotonic_result = validate_proposal_version_sequence((second, first))

    assert duplicate_result.status == "INTEGRITY_FAILURE"
    assert duplicate_result.reason_id != PROPOSAL_NON_MONOTONIC_VERSION_NUMBER_REASON_ID
    assert non_monotonic_result.status == "CONFIGURATION_INVALID"
    assert non_monotonic_result.reason_id == PROPOSAL_NON_MONOTONIC_VERSION_NUMBER_REASON_ID


def test_model_assisted_and_parser_proposals_share_the_same_value_schema(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    value = NumericValue(kind="NUMERIC", value=Decimal("41.2500"), unit_id="unit.hrc")
    manual = _proposal(
        build1_ref_factory,
        proposal_method="MODEL_ASSISTED",
        proposed_value=value,
    )
    parser = _proposal(
        build1_ref_factory,
        proposal_method="DETERMINISTIC_PARSER",
        parse_attempt_ref=build1_ref_factory("build1.parse.csv.1"),
        proposed_value=value,
        evidence_location=_csv_evidence(build1_ref_factory),
    )

    assert canonical_bytes(manual.proposed_value, canonicalization_policy()) == canonical_bytes(
        parser.proposed_value,
        canonicalization_policy(),
    )


def test_slice_3_runtime_source_guard(runtime_source_guard) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard((repository_root / "src" / "gptl" / "core" / "proposals.py",))


def _evaluate(
    build1_ref_factory: Callable[[str], GovernedRef],
    proposal: TypedValueProposal,
    *,
    registry: AlgorithmRegistry | None = None,
    parse_attempts: tuple[ParseAttemptRecord, ...] = (),
):
    return evaluate_typed_value_proposal(
        proposal,
        _source_ref(build1_ref_factory),
        SOURCE_RAW_HASH,
        SOURCE_BYTE_LENGTH,
        _target_schema(build1_ref_factory),
        registry or _algorithm_registry(build1_ref_factory),
        parse_attempts,
        canonicalization_policy(),
    )


def _proposal(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    proposal_ref: GovernedRef | None = None,
    target: ProposalTarget | None = None,
    identity: object | None = None,
    proposal_method: str = "MANUAL_TRANSLATION",
    parse_attempt_ref: GovernedRef | None = None,
    proposed_value: object | None = None,
    evidence_location: object | None = None,
) -> TypedValueProposal:
    return TypedValueProposal.model_validate(
        {
            "schema_version": TYPED_VALUE_PROPOSAL_SCHEMA_VERSION,
            "record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "proposal_ref": proposal_ref or build1_ref_factory("build1.proposal.fixture"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "source_artifact_ref": _source_ref(build1_ref_factory),
            "source_raw_byte_hash": SOURCE_RAW_HASH,
            "identity": identity
            or {
                "identity_mode": "EXISTING_GOVERNED_REF",
                "target_ref": _target_ref(build1_ref_factory),
            },
            "proposal_method": proposal_method,
            "creation_event_ref": build1_ref_factory("build1.proposal.creation-event"),
            "parse_attempt_ref": parse_attempt_ref,
            "target": target or _target(build1_ref_factory),
            "proposed_value": proposed_value
            or {"kind": "NUMERIC", "value": Decimal("41.2500"), "unit_id": "unit.hrc"},
            "evidence_location": evidence_location
            or {
                "locator_class": "RAW_BYTE_RANGE",
                "source_artifact_ref": _source_ref(build1_ref_factory),
                "start_byte": 0,
                "end_byte": 5,
                "raw_byte_hash": SOURCE_RAW_HASH,
            },
            "validation_state": "PROPOSED",
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _target(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    target_logical_id: LogicalId | None = None,
    context_key: dict[str, object] | None = None,
) -> ProposalTarget:
    return ProposalTarget.model_validate(
        {
            "target_record_type": "record.material-specimen",
            "target_logical_id": target_logical_id or _target_ref(build1_ref_factory).logical_id,
            "target_schema_version": "schema.specimen.v1",
            "semantic_field_path": "field.hardness",
            "context_key": context_key or {"side": "side.left", "replicate": 1},
        }
    )


def _target_schema(build1_ref_factory: Callable[[str], GovernedRef]) -> TargetFieldSchema:
    return TargetFieldSchema.model_validate(
        {
            "field_schema_ref": build1_ref_factory("build1.schema.specimen.hardness"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "target_record_type": "record.material-specimen",
            "target_schema_version": "schema.specimen.v1",
            "semantic_field_path": "field.hardness",
            "value_kind": "NUMERIC",
            "canonical_unit_id": "unit.hrc",
            "context_dimensions": (
                {"key": "replicate", "value_kind": "INTEGER"},
                {"key": "side", "value_kind": "TERM"},
            ),
        }
    )


def _algorithm_registry(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    entries: tuple[AlgorithmRegistryEntry, ...] | None = None,
) -> AlgorithmRegistry:
    return AlgorithmRegistry.model_validate(
        {
            "registry_ref": build1_ref_factory("build1.algorithm-registry"),
            "entries": entries
            if entries is not None
            else (_algorithm_entry(build1_ref_factory),),
        }
    )


def _algorithm_entry(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    lifecycle_state: str = "ACTIVE",
) -> AlgorithmRegistryEntry:
    return AlgorithmRegistryEntry.model_validate(
        {
            "schema_version": ALGORITHM_REGISTRY_ENTRY_SCHEMA_VERSION,
            "record_type": ALGORITHM_REGISTRY_ENTRY_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "algorithm_ref": build1_ref_factory("build1.parser.csv"),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "lifecycle_state": lifecycle_state,
            "purpose": "PARSER",
            "executable_module": "gptl.parsers.csv",
            "executable_name": "parse_csv",
            "source_digest": PARSER_SOURCE_DIGEST,
            "supported_input_class_id": "source-class.test-report",
            "output_contract_id": "contract.parsed-table.v1",
            "parameter_schema_hash": PARAMETER_SCHEMA_HASH,
            "evidence_refs": (build1_ref_factory("build1.evidence.parser-source"),),
        }
    )


def _parse_attempt(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    parse_attempt_ref: GovernedRef,
    terminal_status: str = "SUCCEEDED",
) -> ParseAttemptRecord:
    return ParseAttemptRecord.model_validate(
        {
            "schema_version": PARSE_ATTEMPT_SCHEMA_VERSION,
            "record_type": PARSE_ATTEMPT_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "parse_attempt_ref": parse_attempt_ref,
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "source_artifact_ref": _source_ref(build1_ref_factory),
            "algorithm_refs": (build1_ref_factory("build1.parser.csv"),),
            "parser_parameters_hash": PARSE_PARAMETERS_HASH,
            "policy_refs": (build1_ref_factory("build1.csv-dialect.policy"),),
            "input_hash": SOURCE_RAW_HASH,
            "derived_output_hash": DERIVED_OUTPUT_HASH
            if terminal_status == "SUCCEEDED"
            else None,
            "diagnostics": (),
            "terminal_status": terminal_status,
            "recorded_at": AS_OF,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _csv_evidence(build1_ref_factory: Callable[[str], GovernedRef]) -> dict[str, object]:
    return {
        "locator_class": "CSV_CELL_RANGE",
        "source_artifact_ref": _source_ref(build1_ref_factory),
        "csv_parser_algorithm_ref": build1_ref_factory("build1.parser.csv"),
        "dialect_policy_ref": build1_ref_factory("build1.csv-dialect.policy"),
        "start_row": 2,
        "end_row": 2,
        "start_column": 3,
        "end_column": 3,
        "parsed_table_hash": PARSED_TABLE_HASH,
    }


def _source_local_key(build1_ref_factory: Callable[[str], GovernedRef]) -> SourceLocalRecordKey:
    return SourceLocalRecordKey(
        key_class="RAW_BYTE_RANGE",
        source_artifact_ref=_source_ref(build1_ref_factory),
        local_discriminator="bytes.0-16",
    )


def _source_ref(build1_ref_factory: Callable[[str], GovernedRef]) -> GovernedRef:
    return build1_ref_factory("build1.source.fixture-1")


def _target_ref(build1_ref_factory: Callable[[str], GovernedRef]) -> GovernedRef:
    return build1_ref_factory("build1.target.specimen-1")


def _proposal_ref(logical_id: str, version_number: int) -> GovernedRef:
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v{version_number}"),
        version_number=version_number,
        content_hash="0" * 64,
    )
