"""
Module: Semantic Types
Purpose: Constrained scalar types shared by deterministic GPTL records.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Final, Literal, NewType

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
)

OpaqueId = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$"),
]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
JCS_MAX_SAFE_INTEGER: Final = 9_007_199_254_740_991
NonNegativeInt = Annotated[
    int,
    Field(strict=True, ge=0, le=JCS_MAX_SAFE_INTEGER),
]
PositiveInt = Annotated[
    int,
    Field(strict=True, ge=1, le=JCS_MAX_SAFE_INTEGER),
]
CanonicalDecimal = Annotated[Decimal, Field(strict=True)]

LogicalId = NewType("LogicalId", OpaqueId)
VersionId = NewType("VersionId", OpaqueId)
FieldId = NewType("FieldId", OpaqueId)
TermId = NewType("TermId", OpaqueId)
UnitId = NewType("UnitId", OpaqueId)
TemplateId = NewType("TemplateId", OpaqueId)
EvidenceLocator = NewType("EvidenceLocator", OpaqueId)


class CanonicalizationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_id: OpaqueId
    policy_version: OpaqueId
    timestamp_fraction_digits: PositiveInt
    decimal_scale: NonNegativeInt
    decimal_rounding: Literal["ROUND_HALF_EVEN"]
    decimal_max_integer_digits: PositiveInt
    decimal_overflow: Literal["REJECT"]


def _validate_canonical_timestamp(value: str, info: ValidationInfo) -> str:
    context = info.context
    if not isinstance(context, dict):
        raise ValueError("canonicalization policy validation context is required")
    policy = context.get("canonicalization_policy")
    if not isinstance(policy, CanonicalizationPolicy):
        raise ValueError("canonicalization_policy is required")

    fraction = value.rsplit(".", 1)[1][:-1]
    if len(fraction) != policy.timestamp_fraction_digits:
        raise ValueError("timestamp fractional precision does not match policy")
    try:
        date_part, time_part = value[:-1].split("T", 1)
        year, month, day = (int(part) for part in date_part.split("-"))
        hour_text, minute_text, seconds_and_fraction = time_part.split(":")
        second_text, _ = seconds_and_fraction.split(".", 1)
        datetime(
            year,
            month,
            day,
            int(hour_text),
            int(minute_text),
            int(second_text),
        )
    except ValueError as exc:
        raise ValueError("timestamp is not a valid RFC 3339 UTC value") from exc
    return value


CanonicalTimestamp = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"),
    AfterValidator(_validate_canonical_timestamp),
]
