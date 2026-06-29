from __future__ import annotations

from pathlib import Path

from gptl.core.records import GovernedRef


def test_build1_ref_factory_creates_complete_governed_refs(build1_ref_factory) -> None:
    ref = build1_ref_factory("build1.harness.ref")

    assert isinstance(ref, GovernedRef)
    assert ref.logical_id == "build1.harness.ref"
    assert ref.version_id == "build1.harness.ref.v1"
    assert ref.version_number == 1
    assert len(ref.content_hash) == 64


def test_runtime_source_guard_is_exercised(runtime_source_guard) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard(
        (
            repository_root / "src" / "gptl" / "core" / "canonical.py",
            repository_root / "src" / "gptl" / "core" / "records.py",
        )
    )
