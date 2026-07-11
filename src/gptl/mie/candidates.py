"""
Module: Candidate Loading
Purpose: Published candidate loading with fail-open applicability preservation.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import CanonicalizationPolicy
from gptl.mie.predicates import (
    ApplicabilityEvaluation,
    ApplicabilityTruth,
    ContextValue,
    PredicateConfigurationError,
    evaluate_applicability,
    validate_predicate_configuration,
)
from gptl.mie.records import CandidatePack
from gptl.mie.schema import CandidateAssessment, CandidateConfigurationIssue, Citation
from gptl.mie.selection import (
    SelectableRecord,
    SelectionConfigurationError,
    selected_record_refs,
    validate_selection_configuration,
)


class CandidatePackConfigurationError(ValueError):
    pass


class CandidateSetResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    preserved_candidate_refs: tuple[GovernedRef, ...]
    assessments: tuple[CandidateAssessment, ...]
    configuration_issues: tuple[CandidateConfigurationIssue, ...]
    applicability_evaluations: tuple[ApplicabilityEvaluation, ...]
    citations: tuple[Citation, ...]
    has_unknown: bool
    has_invalid: bool

    @model_validator(mode="after")
    def validate_order(self) -> CandidateSetResult:
        _validate_refs(self.preserved_candidate_refs, "preserved candidates")
        assessment_keys = tuple(
            (item.candidate_ref.logical_id, item.candidate_ref.version_id)
            for item in self.assessments
        )
        if assessment_keys != tuple(sorted(set(assessment_keys))):
            raise ValueError("candidate assessments must be unique and sorted")
        issue_keys = tuple(
            (item.candidate_ref.logical_id, item.candidate_ref.version_id)
            for item in self.configuration_issues
        )
        if issue_keys != tuple(sorted(set(issue_keys))):
            raise ValueError("candidate configuration issues must be unique and sorted")
        evaluation_keys = tuple(
            (item.predicate_ref.logical_id, item.predicate_ref.version_id)
            for item in self.applicability_evaluations
        )
        if evaluation_keys != tuple(sorted(set(evaluation_keys))):
            raise ValueError("applicability evaluations must be unique and sorted")
        return self


def validate_candidate_pack(pack: CandidatePack) -> None:
    selectables = tuple(
        SelectableRecord(
            record_ref=candidate.failure_mode_ref,
            record_kind="FAILURE_MODE",
            overlap_scope_id=candidate.overlap_scope_id,
            selection_binding=candidate.selection_binding,
        )
        for candidate in pack.candidates
    )
    try:
        validate_selection_configuration(selectables)
        for candidate in pack.candidates:
            validate_predicate_configuration(
                candidate.applicability_predicate,
                pack.field_registry,
                pack.unit_registry,
            )
    except (SelectionConfigurationError, PredicateConfigurationError) as exc:
        raise CandidatePackConfigurationError(str(exc)) from exc


def load_candidate_set(
    pack: CandidatePack,
    context_values: tuple[ContextValue, ...],
    policy: CanonicalizationPolicy,
) -> CandidateSetResult:
    validate_candidate_pack(pack)
    evaluations = tuple(
        evaluate_applicability(
            candidate.applicability_predicate,
            candidate.predicate_ref,
            context_values,
            pack.field_registry,
            pack.unit_registry,
            policy,
        )
        for candidate in pack.candidates
    )
    true_selectables = tuple(
        SelectableRecord(
            record_ref=candidate.failure_mode_ref,
            record_kind="FAILURE_MODE",
            overlap_scope_id=candidate.overlap_scope_id,
            selection_binding=candidate.selection_binding,
        )
        for candidate, evaluation in zip(pack.candidates, evaluations, strict=True)
        if evaluation.truth == ApplicabilityTruth.TRUE
    )
    selected = selected_record_refs(true_selectables)
    selected_keys = {(item.logical_id, item.version_id) for item in selected}
    preserved = list(selected)
    assessments: list[CandidateAssessment] = []
    configuration_issues: list[CandidateConfigurationIssue] = []
    citations: list[Citation] = []
    for candidate, evaluation in zip(pack.candidates, evaluations, strict=True):
        candidate_key = (
            candidate.failure_mode_ref.logical_id,
            candidate.failure_mode_ref.version_id,
        )
        evidence_refs = _merged_refs(
            candidate.evidence_refs,
            evaluation.evidence_refs,
            (candidate.predicate_ref,),
        )
        if evaluation.truth == ApplicabilityTruth.INVALID:
            configuration_issues.append(
                CandidateConfigurationIssue(
                    candidate_ref=candidate.failure_mode_ref,
                    applicability_evaluation=evaluation,
                    evidence_refs=evidence_refs,
                )
            )
            citations.append(
                Citation(
                    record_type_id=candidate.predicate_record_type_id,
                    record_ref=candidate.predicate_ref,
                    evidence_location=candidate.predicate_evidence_location,
                )
            )
            continue
        if evaluation.truth == ApplicabilityTruth.UNKNOWN:
            preserved.append(candidate.failure_mode_ref)
            assessments.append(
                _assessment(
                    candidate.failure_mode_ref,
                    evaluation,
                    "APPLICABILITY_UNRESOLVED",
                    "APPLICABILITY_UNRESOLVED",
                    evidence_refs,
                    (),
                )
            )
            continue
        if evaluation.truth == ApplicabilityTruth.FALSE:
            assessments.append(
                _assessment(
                    candidate.failure_mode_ref,
                    evaluation,
                    "ELIMINATED",
                    "ELIMINATED",
                    evidence_refs,
                    (candidate.predicate_ref,),
                )
            )
            citations.append(
                Citation(
                    record_type_id=candidate.predicate_record_type_id,
                    record_ref=candidate.predicate_ref,
                    evidence_location=candidate.predicate_evidence_location,
                )
            )
            continue
        if candidate_key in selected_keys:
            assessments.append(
                _assessment(
                    candidate.failure_mode_ref,
                    evaluation,
                    "OPEN_UNASSESSED",
                    "OPEN_UNASSESSED",
                    evidence_refs,
                    (),
                )
            )
            continue
        binding = candidate.selection_binding
        if binding is None:
            raise CandidatePackConfigurationError(
                "unselected candidate is missing a selection binding"
            )
        group_ref = binding.selection_group_ref
        assessments.append(
            _assessment(
                candidate.failure_mode_ref,
                evaluation,
                "ELIMINATED",
                "ELIMINATED",
                evidence_refs,
                (group_ref,),
            )
        )
    assessments.sort(
        key=lambda item: (item.candidate_ref.logical_id, item.candidate_ref.version_id)
    )
    configuration_issues.sort(
        key=lambda item: (item.candidate_ref.logical_id, item.candidate_ref.version_id)
    )
    evaluations = tuple(
        sorted(
            evaluations,
            key=lambda item: (item.predicate_ref.logical_id, item.predicate_ref.version_id),
        )
    )
    citations.sort(
        key=lambda item: (
            item.record_type_id,
            item.record_ref.logical_id,
            item.record_ref.version_id,
            item.evidence_location,
        )
    )
    return CandidateSetResult(
        preserved_candidate_refs=sorted_unique_refs(tuple(preserved)),
        assessments=tuple(assessments),
        configuration_issues=tuple(configuration_issues),
        applicability_evaluations=evaluations,
        citations=tuple(citations),
        has_unknown=any(item.truth == ApplicabilityTruth.UNKNOWN for item in evaluations),
        has_invalid=any(item.truth == ApplicabilityTruth.INVALID for item in evaluations),
    )


def _assessment(
    candidate_ref: GovernedRef,
    evaluation: ApplicabilityEvaluation,
    evidence_state: str,
    status: str,
    evidence_refs: tuple[GovernedRef, ...],
    rule_refs: tuple[GovernedRef, ...],
) -> CandidateAssessment:
    return CandidateAssessment.model_validate(
        {
            "candidate_ref": candidate_ref,
            "applicability": evaluation.truth,
            "evidence_state": evidence_state,
            "status": status,
            "signature_match_score": None,
            "signature_coverage": Decimal(0),
            "candidate_support_score": None,
            "evidence_refs": evidence_refs,
            "rule_refs": _merged_refs(rule_refs),
        }
    )


def _merged_refs(*groups: tuple[GovernedRef, ...]) -> tuple[GovernedRef, ...]:
    return sorted_unique_refs(tuple(item for group in groups for item in group))


def _validate_refs(refs: tuple[GovernedRef, ...], label: str) -> None:
    keys = tuple((item.logical_id, item.version_id) for item in refs)
    if len(keys) != len(set(keys)) or keys != tuple(sorted(keys)):
        raise ValueError(f"{label} must be unique and sorted")
