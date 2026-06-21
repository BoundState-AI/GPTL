"""RFC 8785 canonical serialization with GPTL pre-serialization rules."""

from __future__ import annotations

import hashlib
import unicodedata
from decimal import Decimal, InvalidOperation, localcontext
from enum import Enum
from typing import Any

import rfc8785
from pydantic import BaseModel

from gptl.core.semantic_types import CanonicalizationPolicy


class CanonicalizationError(ValueError):
    """Raised when a value cannot enter an authoritative canonical payload."""


def _canonical_decimal(value: Decimal, policy: CanonicalizationPolicy) -> str:
    if not value.is_finite():
        raise CanonicalizationError("non-finite Decimal is prohibited")
    quantum = Decimal(1).scaleb(-policy.decimal_scale)
    try:
        with localcontext() as context:
            context.prec = max(len(value.as_tuple().digits) + policy.decimal_scale + 2, 28)
            quantized = value.quantize(quantum, rounding=policy.decimal_rounding)
    except InvalidOperation as exc:
        raise CanonicalizationError("Decimal exceeds canonical policy capacity") from exc
    integer_digits = max(quantized.copy_abs().adjusted() + 1, 1)
    if integer_digits > policy.decimal_max_integer_digits:
        raise CanonicalizationError("Decimal exceeds declared overflow limit")
    return format(quantized, f".{policy.decimal_scale}f")


def _normalize(value: Any, policy: CanonicalizationPolicy) -> Any:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python", exclude_none=True)
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise CanonicalizationError("float is prohibited in authoritative payloads")
    if isinstance(value, Decimal):
        return _canonical_decimal(value, policy)
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize(item, policy) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("authoritative object keys must be strings")
            canonical_key = unicodedata.normalize("NFC", key)
            # NFC may collapse visually equivalent source keys. Reject instead of
            # allowing iteration order to decide which authoritative value survives.
            if canonical_key in normalized:
                raise CanonicalizationError("duplicate object key after NFC normalization")
            normalized[canonical_key] = _normalize(item, policy)
        return normalized
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


def canonical_bytes(value: Any, policy: CanonicalizationPolicy) -> bytes:
    """Return RFC 8785 bytes after GPTL NFC and Decimal normalization."""

    try:
        return rfc8785.dumps(_normalize(value, policy))
    except (rfc8785.CanonicalizationError, UnicodeError) as exc:
        raise CanonicalizationError("RFC 8785 serialization failed") from exc


def canonical_sha256(value: Any, policy: CanonicalizationPolicy) -> str:
    return hashlib.sha256(canonical_bytes(value, policy)).hexdigest()


def verify_sha256(payload: bytes, expected_hash: str) -> None:
    actual_hash = hashlib.sha256(payload).hexdigest()
    if actual_hash != expected_hash:
        raise CanonicalizationError("persisted payload checksum mismatch")
