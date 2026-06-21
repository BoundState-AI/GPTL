"""Core governed-record identities."""

from pydantic import BaseModel, ConfigDict

from gptl.core.semantic_types import LogicalId, NonNegativeInt, Sha256Hex, VersionId


class GovernedRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    logical_id: LogicalId
    version_id: VersionId
    version_number: NonNegativeInt
    content_hash: Sha256Hex
