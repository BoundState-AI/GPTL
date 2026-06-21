import hashlib
from pathlib import Path

import pytest

from gptl.core.persistence import PersistenceIntegrityError, PostgresRunStore

PUBLISHED_MIGRATION_SHA256 = {
    "0001_slice_1.sql": "6e8ef39c2a75c2d1b8b5c1d3887af5d8158a7845b3647444c3c85da235b7cdf9",
    "0002_persistence_invariants.sql": (
        "d613491e11bcfb65915636e59c198c9c9bb1834b57bcf2b9f093aaffc05f9799"
    ),
}


def test_published_migrations_are_byte_immutable() -> None:
    repository_root = Path(__file__).parents[2]
    migration_root = repository_root / "src/gptl/core/migrations"
    actual = {
        migration.name: hashlib.sha256(migration.read_bytes()).hexdigest()
        for migration in sorted(migration_root.glob("*.sql"))
    }
    assert actual == PUBLISHED_MIGRATION_SHA256


@pytest.mark.parametrize(
    "applied_ids",
    (
        (),
        ("0002_persistence_invariants",),
        ("0001_slice_1", "0003_unknown"),
    ),
)
def test_migration_history_must_be_an_exact_packaged_prefix(
    applied_ids: tuple[str, ...],
) -> None:
    migrations = PostgresRunStore._load_migrations()
    applied = {migration_id: "0" * 64 for migration_id in applied_ids}
    with pytest.raises(PersistenceIntegrityError, match="exact prefix"):
        PostgresRunStore._validate_migration_history(migrations, applied)
