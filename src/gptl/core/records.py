"""Core governed-record identities."""

from pydantic import BaseModel, ConfigDict

from gptl.core.semantic_types import LogicalId, NonNegativeInt, Sha256Hex, VersionId


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
