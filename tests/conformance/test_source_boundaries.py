from pathlib import Path


def test_authoritative_source_has_no_prohibited_runtime_dependencies() -> None:
    source_root = Path(__file__).parents[2] / "src"
    source = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in sorted(source_root.rglob("*.py"))
    )
    for prohibited in ("sqlite", "faiss", "pgvector", "embedding", "openai"):
        assert prohibited not in source
