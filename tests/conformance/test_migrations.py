import hashlib
from pathlib import Path

import pytest

from gptl.core.persistence import PersistenceIntegrityError, PostgresRunStore

PUBLISHED_MIGRATION_SHA256 = {
    "0001_slice_1.sql": "6e8ef39c2a75c2d1b8b5c1d3887af5d8158a7845b3647444c3c85da235b7cdf9",
    "0002_persistence_invariants.sql": (
        "d613491e11bcfb65915636e59c198c9c9bb1834b57bcf2b9f093aaffc05f9799"
    ),
    "0003_snapshot_bound_runs.sql": (
        "6d0a4fcf74c0699285249a6e7b713c8f77d39c343e32c3f977ecaa114b08ae86"
    ),
    "0004_replay_capsules.sql": (
        "a21fb28046652ce2e40d3b0de9836bb758d2f85839e8ed766b4dee43bb825ad0"
    ),
    "0005_build1_capability_scope.sql": (
        "3cdb13ca80d88f7e089517a63645d6484391f57f85469bdc2b13b1cdedca2af2"
    ),
    "0006_build1_sources.sql": (
        "55dc0616e780e5a4a8b61f121d369a5d28dd50dfe52ca2fe840ac6b822562bdd"
    ),
    "0007_build1_source_integrity.sql": (
        "2244e9204718c985d7462f65cf0d377f1ff3aefed052281731b857bc17e654a7"
    ),
    "0008_build1_source_registration_audit.sql": (
        "9902a715d3af0279a733c36d860b50deb86ca42a2a06be4c48feb9cd627c4ec7"
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
