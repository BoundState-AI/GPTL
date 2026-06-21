"""Governed calibration eligibility."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import CanonicalTimestamp, EvidenceLocator, TermId


class CalibrationTruth(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


class CalibrationValidityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    interval_rule: Literal["VALID_FROM_INCLUSIVE_VALID_UNTIL_INCLUSIVE"]
    before_valid_from_result: Literal["INVALID"]
    after_valid_until_result: Literal["STALE"]


class CalibrationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    calibration_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    instrument_ref: GovernedRef
    status: Literal["CALIBRATED", "INVALID", "UNAVAILABLE"]
    valid_from: CanonicalTimestamp | None
    valid_until: CanonicalTimestamp | None
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_state(self) -> CalibrationRecord:
        if self.status == "CALIBRATED":
            if self.valid_from is None or self.valid_until is None:
                raise ValueError("calibrated record requires a validity interval")
            if self.valid_from > self.valid_until:
                raise ValueError("calibration validity interval is inverted")
        elif self.valid_from is not None or self.valid_until is not None:
            raise ValueError("non-calibrated state cannot claim a validity interval")
        if sorted_unique_refs(self.evidence_refs) != self.evidence_refs or not self.evidence_refs:
            raise ValueError("calibration evidence must be nonempty, unique, and sorted")
        return self


class MeasurementRunContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_context_ref: GovernedRef
    instrument_ref: GovernedRef
    calibration_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> MeasurementRunContext:
        if sorted_unique_refs(self.evidence_refs) != self.evidence_refs or not self.evidence_refs:
            raise ValueError("run-context evidence must be nonempty, unique, and sorted")
        return self


class CalibrationEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: CalibrationTruth
    calibration_ref: GovernedRef
    policy_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> CalibrationEvaluation:
        if sorted_unique_refs(self.evidence_refs) != self.evidence_refs or not self.evidence_refs:
            raise ValueError("calibration evaluation requires governed evidence")
        if (
            self.calibration_ref not in self.evidence_refs
            or self.policy_ref not in self.evidence_refs
        ):
            raise ValueError("calibration evaluation must cite its record and policy")
        return self


def evaluate_calibration(
    record: CalibrationRecord,
    policy: CalibrationValidityPolicy,
    as_of_time: CanonicalTimestamp,
) -> CalibrationEvaluation:
    if record.status == "INVALID":
        state = CalibrationTruth.INVALID
    elif record.status == "UNAVAILABLE":
        state = CalibrationTruth.UNAVAILABLE
    elif record.valid_from is None or record.valid_until is None:
        state = CalibrationTruth.INVALID
    elif as_of_time < record.valid_from:
        state = CalibrationTruth(policy.before_valid_from_result)
    elif as_of_time > record.valid_until:
        state = CalibrationTruth(policy.after_valid_until_result)
    else:
        state = CalibrationTruth.VALID
    return CalibrationEvaluation(
        state=state,
        calibration_ref=record.calibration_ref,
        policy_ref=policy.policy_ref,
        evidence_refs=sorted_unique_refs(
            (record.calibration_ref, policy.policy_ref, *record.evidence_refs)
        ),
    )
