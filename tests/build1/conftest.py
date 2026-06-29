from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable
from pathlib import Path

import pytest

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import LogicalId, VersionId

RuntimeSourceGuard = Callable[[Iterable[Path]], None]


@pytest.fixture
def build1_ref_factory() -> Callable[[str], GovernedRef]:
    def create_ref(logical_id: str) -> GovernedRef:
        return GovernedRef(
            logical_id=LogicalId(logical_id),
            version_id=VersionId(f"{logical_id}.v1"),
            version_number=1,
            content_hash=hashlib.sha256(f"fixture:{logical_id}:v1".encode()).hexdigest(),
        )

    return create_ref


@pytest.fixture
def runtime_source_guard() -> RuntimeSourceGuard:
    prohibited = (
        "fai" + "ss",
        "pg" + "vector",
        "pinecone",
        "weaviate",
        "chroma",
        "embed" + "ding",
        "nearest" + "_neighbor",
        "nearest" + "-neighbor",
        "sql" + "ite",
        "sql" + "ite3",
    )
    pattern = re.compile(
        r"\b("
        + "|".join(re.escape(token) for token in prohibited)
        + r")\b|nearest[-_]neighbor",
        re.IGNORECASE,
    )

    def assert_clean(paths: Iterable[Path]) -> None:
        for path in paths:
            source = path.read_text(encoding="utf-8")
            assert pattern.search(source) is None, path

    return assert_clean
