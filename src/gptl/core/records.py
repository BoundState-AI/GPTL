"""Core governed-record identities."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from gptl.core.canonical import canonical_sha256
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    LogicalId,
    NonNegativeInt,
    Sha256Hex,
    VersionId,
)


class GovernedRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    logical_id: LogicalId
    version_id: VersionId
    version_number: NonNegativeInt
    content_hash: Sha256Hex


class GovernedReferenceConflictError(ValueError):
    pass


def sorted_unique_refs(refs: tuple[GovernedRef, ...]) -> tuple[GovernedRef, ...]:
    unique: dict[tuple[str, str], GovernedRef] = {}
    for item in refs:
        key = (item.logical_id, item.version_id)
        existing = unique.get(key)
        if existing is not None and existing != item:
            raise GovernedReferenceConflictError(
                "one governed identity resolved to conflicting version metadata"
            )
        unique[key] = item
    return tuple(unique[key] for key in sorted(unique))


def governed_record_content_payload(record: BaseModel, self_ref_field: str) -> dict[str, Any]:
    if self_ref_field not in record.__class__.model_fields:
        raise ValueError("self reference field is not present on governed record")
    return record.model_dump(
        mode="python",
        exclude={self_ref_field: {"content_hash"}},
    )


def governed_record_content_hash(
    record: BaseModel,
    self_ref_field: str,
    policy: CanonicalizationPolicy,
) -> str:
    return canonical_sha256(governed_record_content_payload(record, self_ref_field), policy)
