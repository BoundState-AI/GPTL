from pathlib import Path


def test_authoritative_source_has_no_prohibited_runtime_dependencies() -> None:
    source_root = Path(__file__).parents[2] / "src"
    source = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in sorted(source_root.rglob("*.py"))
    )
    for prohibited in (
        "sqlite",
        "faiss",
        "pgvector",
        "embedding",
        "openai",
        "anthropic",
        "confidence_interval",
        "posterior",
        "probability",
    ):
        assert prohibited not in source


def test_diagnostic_engine_has_no_domain_numeric_constants_through_slice7() -> None:
    gptl_root = Path(__file__).parents[2] / "src" / "gptl"
    mie_root = gptl_root / "mie"
    mie_sources = [
        (mie_root / name).read_text(encoding="utf-8")
        for name in (
            "diagnostics.py",
            "advisory.py",
            "negative.py",
            "replay.py",
            "slice4_service.py",
            "slice5_service.py",
            "slice6_service.py",
        )
    ]
    # Build 1 governed-record engines (src/gptl/core) and the Build 2 analytical tool
    # layer (src/gptl/tools) must likewise carry no hardcoded domain numeric constants:
    # all bounds live in governed protocol/proposal/policy data, never in engine code.
    # rglob so new modules are covered automatically — the guard, not manual inspection,
    # enforces the no-magic-numbers invariant.
    governed_sources = [
        path.read_text(encoding="utf-8")
        for package in ("core", "tools")
        for path in sorted((gptl_root / package).rglob("*.py"))
    ]
    source = "\n".join([*mie_sources, *governed_sources])
    decimal_literals = {
        value
        for marker in ('Decimal("', "Decimal('")
        for fragment in source.split(marker)[1:]
        for value in (fragment.split(marker[-1], 1)[0],)
    }

    assert decimal_literals <= {"0", "1"}
