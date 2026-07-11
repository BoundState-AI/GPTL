"""
Module: MSA Hard Gate
Purpose: Qualified measurement-system analysis hard gate.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    EvidenceLocator,
    FieldId,
    OpaqueId,
    TermId,
)
from gptl.mie.predicates import (
    ApplicabilityEvaluation,
    ApplicabilityTruth,
    ContextValue,
    FieldRegistry,
    NumericValue,
    Predicate,
    PredicateConfigurationError,
    UnitRegistry,
    convert_numeric_value,
    evaluate_applicability,
    validate_predicate_configuration,
)
from gptl.mie.selection import (
    SelectableRecord,
    SelectionBinding,
    SelectionConfigurationError,
    SelectionGroupRecord,
    selected_record_refs,
    validate_selection_configuration,
)


class MSAGateOutcome(str, Enum):
    WITHIN_VARIATION = "WITHIN_VARIATION"
    OUTSIDE_VARIATION = "OUTSIDE_VARIATION"
    UNCHARACTERIZED = "UNCHARACTERIZED"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"


class MSAGateReason(str, Enum):
    WITHIN_VARIATION = "WITHIN_VARIATION"
    OUTSIDE_VARIATION = "OUTSIDE_VARIATION"
    MISSING_STUDY = "MISSING_STUDY"
    UNQUALIFIED_STUDY = "UNQUALIFIED_STUDY"
    UNKNOWN_APPLICABILITY = "UNKNOWN_APPLICABILITY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    UNIMPLEMENTED_CLASS = "UNIMPLEMENTED_CLASS"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"


class EvidenceScopeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scope_ref: GovernedRef
    scope_kind: Literal["TEST_FIXTURE", "BENCH", "VENDOR", "COMPANY", "PRODUCTION"]


class ImplementedMSAClassRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    registry_ref: GovernedRef
    engine_id: OpaqueId
    engine_version: OpaqueId
    implemented_class_ids: tuple[TermId, ...]

    @model_validator(mode="after")
    def validate_classes(self) -> ImplementedMSAClassRegistry:
        if not self.implemented_class_ids or self.implemented_class_ids != tuple(
            sorted(set(self.implemented_class_ids))
        ):
            raise ValueError("implemented MSA classes must be nonempty, unique, and sorted")
        return self


class MethodMeasurementContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_ref: GovernedRef
    method_ref: GovernedRef
    msa_class_id: TermId
    deviation_field_id: FieldId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> MethodMeasurementContract:
        if sorted_unique_refs(self.evidence_refs) != self.evidence_refs or not self.evidence_refs:
            raise ValueError("method measurement contract requires governed evidence")
        return self


class MSAStudy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    study_ref: GovernedRef
    study_record_type_id: TermId
    study_evidence_location: EvidenceLocator
    method_ref: GovernedRef
    msa_class_id: TermId
    measurand_field_id: FieldId
    overlap_scope_id: TermId
    predicate_ref: GovernedRef
    predicate_record_type_id: TermId
    predicate_evidence_location: EvidenceLocator
    applicability_predicate: Predicate
    selection_binding: SelectionBinding | None
    measured_uncertainty: NumericValue
    qualification_state: Literal["QUALIFIED", "UNQUALIFIED"]
    qualification_scope_ref: GovernedRef
    fixture_class: Literal["SYNTHETIC", "REFERENCE", "PRODUCTION"]
    effective_at: CanonicalTimestamp
    expires_at: CanonicalTimestamp
    capability_evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_study(self) -> MSAStudy:
        if self.measured_uncertainty.value < 0:
            raise ValueError("measured uncertainty cannot be negative")
        if self.effective_at > self.expires_at:
            raise ValueError("MSA qualification interval is inverted")
        if (
            not self.capability_evidence_refs
            or sorted_unique_refs(self.capability_evidence_refs) != self.capability_evidence_refs
        ):
            raise ValueError("MSA capability evidence must be nonempty, unique, and sorted")
        return self


class MSAGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: MSAGateOutcome
    reason: MSAGateReason
    selected_study_ref: GovernedRef | None
    measured_deviation: NumericValue
    measured_uncertainty: NumericValue | None
    applicability_evaluations: tuple[ApplicabilityEvaluation, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_outcome(self) -> MSAGateResult:
        selected = self.selected_study_ref is not None
        compared = self.measured_uncertainty is not None
        terminal_comparison = self.outcome in {
            MSAGateOutcome.WITHIN_VARIATION,
            MSAGateOutcome.OUTSIDE_VARIATION,
        }
        if terminal_comparison != selected or terminal_comparison != compared:
            raise ValueError("MSA comparison outcome requires one selected study")
        return self


class MSAConfigurationError(ValueError):
    pass


def validate_msa_configuration(
    studies: tuple[MSAStudy, ...],
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
    known_scopes: tuple[EvidenceScopeRecord, ...],
    selection_groups: tuple[SelectionGroupRecord, ...],
    measurement_contract: MethodMeasurementContract,
    policy: CanonicalizationPolicy,
) -> None:
    study_keys = tuple((item.study_ref.logical_id, item.study_ref.version_id) for item in studies)
    if study_keys != tuple(sorted(set(study_keys))):
        raise MSAConfigurationError("MSA studies must be unique and sorted")
    scope_refs = tuple(item.scope_ref for item in known_scopes)
    if sorted_unique_refs(scope_refs) != scope_refs:
        raise MSAConfigurationError("evidence scopes must be unique and sorted")
    scope_by_ref = {
        (item.scope_ref.logical_id, item.scope_ref.version_id): item for item in known_scopes
    }
    group_refs = tuple(item.group_ref for item in selection_groups)
    if sorted_unique_refs(group_refs) != group_refs:
        raise MSAConfigurationError("MSA selection groups must be unique and sorted")
    group_by_key = {
        (item.group_ref.logical_id, item.group_ref.version_id): item for item in selection_groups
    }
    selectables = tuple(
        SelectableRecord(
            record_ref=study.study_ref,
            record_kind="MSA_STUDY",
            overlap_scope_id=study.overlap_scope_id,
            selection_binding=study.selection_binding,
        )
        for study in studies
    )
    try:
        validate_selection_configuration(selectables)
        fields = {item.field_id: item for item in field_registry.fields}
        for study in studies:
            if (
                study.method_ref == measurement_contract.method_ref
                and study.msa_class_id == measurement_contract.msa_class_id
                and study.measurand_field_id != measurement_contract.deviation_field_id
            ):
                raise MSAConfigurationError(
                    "MSA measurand does not match the method measurement contract"
                )
            if study.selection_binding is not None:
                binding_key = (
                    study.selection_binding.selection_group_ref.logical_id,
                    study.selection_binding.selection_group_ref.version_id,
                )
                selection_group = group_by_key.get(binding_key)
                if selection_group is None:
                    raise MSAConfigurationError("MSA study references an unknown selection group")
                if selection_group.group_ref != study.selection_binding.selection_group_ref:
                    raise MSAConfigurationError(
                        "MSA selection-group reference conflicts with record"
                    )
            validate_predicate_configuration(
                study.applicability_predicate,
                field_registry,
                unit_registry,
            )
            measurand = fields.get(study.measurand_field_id)
            if measurand is None or measurand.value_kind != "NUMERIC":
                raise MSAConfigurationError("MSA measurand must be a registered numeric field")
            if measurand.canonical_unit_id is None:
                raise MSAConfigurationError("MSA measurand has no canonical unit")
            converted_uncertainty = convert_numeric_value(
                study.measured_uncertainty,
                measurand.canonical_unit_id,
                unit_registry,
                policy,
            )
            if not isinstance(converted_uncertainty, NumericValue):
                raise MSAConfigurationError("MSA uncertainty unit is incompatible with measurand")
            scope = scope_by_ref.get(
                (
                    study.qualification_scope_ref.logical_id,
                    study.qualification_scope_ref.version_id,
                )
            )
            if scope is None:
                raise MSAConfigurationError("MSA qualification scope is unknown")
            if scope.scope_ref != study.qualification_scope_ref:
                raise MSAConfigurationError(
                    "MSA qualification-scope reference conflicts with record"
                )
            if (
                study.fixture_class in {"SYNTHETIC", "REFERENCE"}
                and scope.scope_kind != "TEST_FIXTURE"
            ):
                raise MSAConfigurationError(
                    "non-production MSA can qualify only a TEST_FIXTURE scope"
                )
    except (PredicateConfigurationError, SelectionConfigurationError) as exc:
        raise MSAConfigurationError(str(exc)) from exc


def evaluate_msa_gate(
    studies: tuple[MSAStudy, ...],
    registry: ImplementedMSAClassRegistry,
    known_scopes: tuple[EvidenceScopeRecord, ...],
    selection_groups: tuple[SelectionGroupRecord, ...],
    run_scope_ref: GovernedRef,
    measurement_contract: MethodMeasurementContract,
    measured_deviation: NumericValue,
    context_values: tuple[ContextValue, ...],
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
    as_of_time: CanonicalTimestamp,
    policy: CanonicalizationPolicy,
    uncharacterized_precedence: tuple[MSAGateReason, ...],
) -> MSAGateResult:
    required_precedence = {
        MSAGateReason.UNKNOWN_APPLICABILITY,
        MSAGateReason.SCOPE_MISMATCH,
        MSAGateReason.UNQUALIFIED_STUDY,
        MSAGateReason.NOT_APPLICABLE,
    }
    if (
        measured_deviation.value < 0
        or len(uncharacterized_precedence) != len(set(uncharacterized_precedence))
        or set(uncharacterized_precedence) != required_precedence
    ):
        return _terminal_result(
            MSAGateOutcome.CONFIGURATION_INVALID,
            MSAGateReason.INVALID_CONFIGURATION,
            measured_deviation,
            (),
            sorted_unique_refs(
                (
                    registry.registry_ref,
                    measurement_contract.contract_ref,
                    *measurement_contract.evidence_refs,
                )
            ),
        )
    try:
        validate_msa_configuration(
            studies,
            field_registry,
            unit_registry,
            known_scopes,
            selection_groups,
            measurement_contract,
            policy,
        )
    except MSAConfigurationError:
        return _terminal_result(
            MSAGateOutcome.CONFIGURATION_INVALID,
            MSAGateReason.INVALID_CONFIGURATION,
            measured_deviation,
            (),
            _study_evidence(studies),
        )
    if measurement_contract.msa_class_id not in registry.implemented_class_ids:
        return _terminal_result(
            MSAGateOutcome.UNCHARACTERIZED,
            MSAGateReason.UNIMPLEMENTED_CLASS,
            measured_deviation,
            (),
            (registry.registry_ref,),
        )
    in_method = tuple(
        study
        for study in studies
        if study.method_ref == measurement_contract.method_ref
        and study.msa_class_id == measurement_contract.msa_class_id
    )
    if not in_method:
        return _terminal_result(
            MSAGateOutcome.UNCHARACTERIZED,
            MSAGateReason.MISSING_STUDY,
            measured_deviation,
            (),
            (registry.registry_ref,),
        )
    evaluations = tuple(
        evaluate_applicability(
            study.applicability_predicate,
            study.predicate_ref,
            context_values,
            field_registry,
            unit_registry,
            policy,
        )
        for study in in_method
    )
    if any(item.truth == ApplicabilityTruth.INVALID for item in evaluations):
        return _terminal_result(
            MSAGateOutcome.CONFIGURATION_INVALID,
            MSAGateReason.INVALID_CONFIGURATION,
            measured_deviation,
            evaluations,
            _study_evidence(in_method),
        )
    eligible = tuple(
        study
        for study, evaluation in zip(in_method, evaluations, strict=True)
        if evaluation.truth == ApplicabilityTruth.TRUE
        and study.qualification_state == "QUALIFIED"
        and study.qualification_scope_ref == run_scope_ref
        and study.effective_at <= as_of_time <= study.expires_at
    )
    if not eligible:
        reason = _uncharacterized_reason(
            in_method,
            evaluations,
            run_scope_ref,
            as_of_time,
            uncharacterized_precedence,
        )
        return _terminal_result(
            MSAGateOutcome.UNCHARACTERIZED,
            reason,
            measured_deviation,
            evaluations,
            _study_evidence(in_method),
        )
    selected_refs = selected_record_refs(
        tuple(
            SelectableRecord(
                record_ref=study.study_ref,
                record_kind="MSA_STUDY",
                overlap_scope_id=study.overlap_scope_id,
                selection_binding=study.selection_binding,
            )
            for study in eligible
        )
    )
    if len(selected_refs) != 1:
        return _terminal_result(
            MSAGateOutcome.CONFIGURATION_INVALID,
            MSAGateReason.INVALID_CONFIGURATION,
            measured_deviation,
            evaluations,
            _study_evidence(eligible),
        )
    selected_ref = selected_refs[0]
    selected = next(study for study in eligible if study.study_ref == selected_ref)
    field_definition = next(
        (item for item in field_registry.fields if item.field_id == selected.measurand_field_id),
        None,
    )
    if field_definition is None or field_definition.canonical_unit_id is None:
        return _terminal_result(
            MSAGateOutcome.CONFIGURATION_INVALID,
            MSAGateReason.INVALID_CONFIGURATION,
            measured_deviation,
            evaluations,
            _study_evidence((selected,)),
        )
    normalized_deviation = convert_numeric_value(
        measured_deviation,
        field_definition.canonical_unit_id,
        unit_registry,
        policy,
    )
    normalized_uncertainty = convert_numeric_value(
        selected.measured_uncertainty,
        field_definition.canonical_unit_id,
        unit_registry,
        policy,
    )
    if not isinstance(normalized_deviation, NumericValue) or not isinstance(
        normalized_uncertainty, NumericValue
    ):
        return _terminal_result(
            MSAGateOutcome.CONFIGURATION_INVALID,
            MSAGateReason.INVALID_CONFIGURATION,
            measured_deviation,
            evaluations,
            _study_evidence((selected,)),
        )
    within = normalized_deviation.value <= normalized_uncertainty.value
    return MSAGateResult(
        outcome=(MSAGateOutcome.WITHIN_VARIATION if within else MSAGateOutcome.OUTSIDE_VARIATION),
        reason=(MSAGateReason.WITHIN_VARIATION if within else MSAGateReason.OUTSIDE_VARIATION),
        selected_study_ref=selected.study_ref,
        measured_deviation=normalized_deviation,
        measured_uncertainty=normalized_uncertainty,
        applicability_evaluations=tuple(
            sorted(
                evaluations,
                key=lambda item: (item.predicate_ref.logical_id, item.predicate_ref.version_id),
            )
        ),
        evidence_refs=sorted_unique_refs(
            (selected.study_ref, selected.predicate_ref, *selected.capability_evidence_refs)
        ),
    )


def _uncharacterized_reason(
    studies: tuple[MSAStudy, ...],
    evaluations: tuple[ApplicabilityEvaluation, ...],
    run_scope_ref: GovernedRef,
    as_of_time: CanonicalTimestamp,
    precedence: tuple[MSAGateReason, ...],
) -> MSAGateReason:
    available = {MSAGateReason.NOT_APPLICABLE}
    if any(item.truth == ApplicabilityTruth.UNKNOWN for item in evaluations):
        available.add(MSAGateReason.UNKNOWN_APPLICABILITY)
    true_studies = tuple(
        study
        for study, evaluation in zip(studies, evaluations, strict=True)
        if evaluation.truth == ApplicabilityTruth.TRUE
    )
    if any(study.qualification_scope_ref != run_scope_ref for study in true_studies):
        available.add(MSAGateReason.SCOPE_MISMATCH)
    if any(
        study.qualification_state != "QUALIFIED"
        or not (study.effective_at <= as_of_time <= study.expires_at)
        for study in true_studies
    ):
        available.add(MSAGateReason.UNQUALIFIED_STUDY)
    return next(reason for reason in precedence if reason in available)


def _terminal_result(
    outcome: MSAGateOutcome,
    reason: MSAGateReason,
    measured_deviation: NumericValue,
    evaluations: tuple[ApplicabilityEvaluation, ...],
    evidence_refs: tuple[GovernedRef, ...],
) -> MSAGateResult:
    return MSAGateResult(
        outcome=outcome,
        reason=reason,
        selected_study_ref=None,
        measured_deviation=measured_deviation,
        measured_uncertainty=None,
        applicability_evaluations=tuple(
            sorted(
                evaluations,
                key=lambda item: (item.predicate_ref.logical_id, item.predicate_ref.version_id),
            )
        ),
        evidence_refs=sorted_unique_refs(evidence_refs),
    )


def _study_evidence(studies: tuple[MSAStudy, ...]) -> tuple[GovernedRef, ...]:
    return sorted_unique_refs(
        tuple(
            ref
            for study in studies
            for ref in (study.study_ref, study.predicate_ref, *study.capability_evidence_refs)
        )
    )
