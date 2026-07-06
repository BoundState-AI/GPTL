from __future__ import annotations

import hashlib
from collections.abc import Callable

import pytest

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import LogicalId, VersionId


@pytest.fixture
def build2_ref_factory() -> Callable[[str], GovernedRef]:
    def create_ref(logical_id: str) -> GovernedRef:
        return GovernedRef(
            logical_id=LogicalId(logical_id),
            version_id=VersionId(f"{logical_id}.v1"),
            version_number=1,
            content_hash=hashlib.sha256(f"fixture:{logical_id}:v1".encode()).hexdigest(),
        )

    return create_ref
