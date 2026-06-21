from decimal import Decimal

import pytest

from gptl.core.canonical import (
    CanonicalizationError,
    canonical_bytes,
    canonical_sha256,
)
from gptl.slice1_fixture import canonicalization_policy


def test_unicode_nfc_variants_have_identical_bytes_and_hashes() -> None:
    policy = canonicalization_policy()
    composed = {"label": "caf\u00e9"}
    decomposed = {"label": "cafe\u0301"}

    assert canonical_bytes(composed, policy) == canonical_bytes(decomposed, policy)
    assert canonical_sha256(composed, policy) == canonical_sha256(decomposed, policy)


def test_duplicate_keys_after_nfc_normalization_are_rejected() -> None:
    with pytest.raises(CanonicalizationError, match="duplicate object key"):
        canonical_bytes({"\u00e9": 1, "e\u0301": 2}, canonicalization_policy())


def test_float_is_rejected_at_any_depth() -> None:
    with pytest.raises(CanonicalizationError, match="float is prohibited"):
        canonical_bytes({"outer": [{"value": 0.1}]}, canonicalization_policy())


def test_decimal_uses_explicit_fixed_scale_policy() -> None:
    payload = canonical_bytes({"value": Decimal("1.2")}, canonicalization_policy())
    assert payload == b'{"value":"1.2000"}'


def test_decimal_overflow_is_rejected_by_explicit_policy() -> None:
    with pytest.raises(CanonicalizationError, match="overflow limit"):
        canonical_bytes(
            {"value": Decimal("1000000000000000000")},
            canonicalization_policy(),
        )
