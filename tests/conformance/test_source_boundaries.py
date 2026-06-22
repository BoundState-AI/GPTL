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


def test_diagnostic_engine_has_no_domain_numeric_constants_through_slice5() -> None:
    source_root = Path(__file__).parents[2] / "src" / "gptl" / "mie"
    source = "\n".join(
        (source_root / name).read_text(encoding="utf-8")
        for name in (
            "diagnostics.py",
            "advisory.py",
            "negative.py",
            "slice4_service.py",
            "slice5_service.py",
            "slice6_service.py",
        )
    )
    decimal_literals = {
        value
        for marker in ('Decimal("', "Decimal('")
        for fragment in source.split(marker)[1:]
        for value in (fragment.split(marker[-1], 1)[0],)
    }

    assert decimal_literals <= {"0", "1"}
