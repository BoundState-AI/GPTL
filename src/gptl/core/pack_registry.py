"""
Module: Pack Registry
Purpose: Exact-identifier pack availability boundary.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.semantic_types import OpaqueId


class ExactPackRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    available_pack_ids: tuple[OpaqueId, ...]

    @model_validator(mode="after")
    def validate_order(self) -> "ExactPackRegistry":
        if len(self.available_pack_ids) != len(set(self.available_pack_ids)):
            raise ValueError("pack IDs must be unique")
        if self.available_pack_ids != tuple(sorted(self.available_pack_ids)):
            raise ValueError("pack IDs must be lexicographically sorted")
        return self

    def contains_exact(self, pack_id: str) -> bool:
        return pack_id in self.available_pack_ids
