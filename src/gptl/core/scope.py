"""
Module: Evidence Scope
Purpose: Closed Build 1 evidence-scope contract.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import TermId

EVIDENCE_SCOPE_MATCH_ALGORITHM_ID: Final = "EVIDENCE_SCOPE_MATCH_V1"
SCOPE_INCOMPATIBLE_REASON_ID: Final = TermId("build1.scope.incompatible")
SCOPE_TERM_UNKNOWN_REASON_ID: Final = TermId("build1.scope.term-unknown")

SCOPE_CLASS_DIMENSION_ID: Final = TermId("scope.scope_class")
ORGANIZATION_DIMENSION_ID: Final = TermId("scope.organization_id")
SITE_DIMENSION_ID: Final = TermId("scope.site_id")
WORKSPACE_DIMENSION_ID: Final = TermId("scope.workspace_id")
DATA_BOUNDARY_DIMENSION_ID: Final = TermId("scope.data_boundary_id")
CONTEXT_DIMENSION_ID: Final = TermId("scope.context_id")
LIFECYCLE_DIMENSION_ID: Final = TermId("scope.lifecycle_state")

SCOPE_DIMENSION_IDS: Final = (
    SCOPE_CLASS_DIMENSION_ID,
    ORGANIZATION_DIMENSION_ID,
    SITE_DIMENSION_ID,
    WORKSPACE_DIMENSION_ID,
    DATA_BOUNDARY_DIMENSION_ID,
    CONTEXT_DIMENSION_ID,
)
_PROHIBITED_SCOPE_TERM_IDS: Final = frozenset(
    {
        "*",
        "APPLICATION_DEFAULT",
        "DEFAULT",
        "UNSCOPED",
        "WILDCARD",
        "application-default",
        "default",
        "unscoped",
        "wildcard",
    }
)


class EvidenceScopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.evidence-scope.v1"]
    scope_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    scope_class: Literal["TEST_FIXTURE", "RESEARCH_CORPUS"]
    organization_id: TermId
    site_id: TermId
    workspace_id: TermId
    data_boundary_id: TermId
    context_id: TermId

    @model_validator(mode="after")
    def validate_dimensions(self) -> EvidenceScopeV1:
        for dimension_id, value in _dimension_values(self):
            if value in _PROHIBITED_SCOPE_TERM_IDS:
                raise ValueError(f"{dimension_id} cannot use an unscoped or default sentinel")
        return self


class ScopeTermSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension_id: TermId
    allowed_term_ids: tuple[TermId, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_allowed_terms(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "allowed_term_ids" in normalized:
            normalized["allowed_term_ids"] = tuple(sorted(normalized["allowed_term_ids"]))
        return normalized

    @model_validator(mode="after")
    def validate_allowed_terms(self) -> ScopeTermSet:
        if not self.allowed_term_ids:
            raise ValueError("scope term set requires allowed terms")
        if self.allowed_term_ids != tuple(sorted(set(self.allowed_term_ids))):
            raise ValueError("scope term IDs must be unique and sorted")
        return self


class ScopeTermRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_ref: GovernedRef
    term_sets: tuple[ScopeTermSet, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_term_sets(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "term_sets" in normalized:
            normalized["term_sets"] = tuple(
                sorted(normalized["term_sets"], key=_term_set_sort_key)
            )
        return normalized

    @model_validator(mode="after")
    def validate_term_sets(self) -> ScopeTermRegistry:
        dimensions = tuple(item.dimension_id for item in self.term_sets)
        if dimensions != tuple(sorted(SCOPE_DIMENSION_IDS)):
            raise ValueError("scope term registry must cover the closed Build 1 dimensions")
        return self


class ScopeTermsResolved(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["TERMS_RESOLVED"]
    registry_ref: GovernedRef
    scope_ref: GovernedRef


class ScopeTermUnknown(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["SCOPE_TERM_UNKNOWN"]
    reason_id: TermId
    registry_ref: GovernedRef
    scope_ref: GovernedRef
    unknown_dimension_ids: tuple[TermId, ...]

    @model_validator(mode="after")
    def validate_unknown_dimensions(self) -> ScopeTermUnknown:
        if not self.unknown_dimension_ids:
            raise ValueError("unknown scope term result requires dimensions")
        if self.unknown_dimension_ids != tuple(sorted(set(self.unknown_dimension_ids))):
            raise ValueError("unknown scope dimensions must be unique and sorted")
        return self


ScopeTermResolution = ScopeTermsResolved | ScopeTermUnknown


class EvidenceScopeMatched(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["MATCHED"]
    algorithm_id: Literal["EVIDENCE_SCOPE_MATCH_V1"]
    candidate_scope_ref: GovernedRef
    run_scope_ref: GovernedRef


class ScopeIncompatible(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["SCOPE_INCOMPATIBLE"]
    algorithm_id: Literal["EVIDENCE_SCOPE_MATCH_V1"]
    reason_id: TermId
    candidate_scope_ref: GovernedRef
    run_scope_ref: GovernedRef
    mismatched_dimension_ids: tuple[TermId, ...]

    @model_validator(mode="after")
    def validate_mismatches(self) -> ScopeIncompatible:
        if not self.mismatched_dimension_ids:
            raise ValueError("scope incompatibility requires at least one mismatched dimension")
        if self.mismatched_dimension_ids != tuple(sorted(set(self.mismatched_dimension_ids))):
            raise ValueError("mismatched dimensions must be unique and sorted")
        return self


EvidenceScopeMatchResult = EvidenceScopeMatched | ScopeIncompatible


def validate_scope_terms(
    scope: EvidenceScopeV1,
    registry: ScopeTermRegistry,
) -> ScopeTermResolution:
    allowed_by_dimension = {
        term_set.dimension_id: set(term_set.allowed_term_ids) for term_set in registry.term_sets
    }
    unknown_dimensions = tuple(
        sorted(
            dimension_id
            for dimension_id, term_id in _dimension_values(scope)
            if term_id not in allowed_by_dimension.get(dimension_id, set())
        )
    )
    if unknown_dimensions:
        return ScopeTermUnknown(
            status="SCOPE_TERM_UNKNOWN",
            reason_id=SCOPE_TERM_UNKNOWN_REASON_ID,
            registry_ref=registry.registry_ref,
            scope_ref=scope.scope_ref,
            unknown_dimension_ids=unknown_dimensions,
        )

    return ScopeTermsResolved(
        status="TERMS_RESOLVED",
        registry_ref=registry.registry_ref,
        scope_ref=scope.scope_ref,
    )


def scope_matches(
    candidate_scope: EvidenceScopeV1,
    run_scope: EvidenceScopeV1,
) -> EvidenceScopeMatchResult:
    mismatches: list[TermId] = []
    if candidate_scope.lifecycle_state != "ACTIVE" or run_scope.lifecycle_state != "ACTIVE":
        mismatches.append(LIFECYCLE_DIMENSION_ID)
    for dimension_id, candidate_value, run_value in _paired_dimension_values(
        candidate_scope,
        run_scope,
    ):
        if candidate_value != run_value:
            mismatches.append(dimension_id)

    if mismatches:
        return ScopeIncompatible(
            status="SCOPE_INCOMPATIBLE",
            algorithm_id=EVIDENCE_SCOPE_MATCH_ALGORITHM_ID,
            reason_id=SCOPE_INCOMPATIBLE_REASON_ID,
            candidate_scope_ref=candidate_scope.scope_ref,
            run_scope_ref=run_scope.scope_ref,
            mismatched_dimension_ids=tuple(sorted(set(mismatches))),
        )

    return EvidenceScopeMatched(
        status="MATCHED",
        algorithm_id=EVIDENCE_SCOPE_MATCH_ALGORITHM_ID,
        candidate_scope_ref=candidate_scope.scope_ref,
        run_scope_ref=run_scope.scope_ref,
    )


def scope_ref_for_build0(scope: EvidenceScopeV1) -> GovernedRef:
    return scope.scope_ref


def _dimension_values(scope: EvidenceScopeV1) -> tuple[tuple[TermId, object], ...]:
    return (
        (SCOPE_CLASS_DIMENSION_ID, scope.scope_class),
        (ORGANIZATION_DIMENSION_ID, scope.organization_id),
        (SITE_DIMENSION_ID, scope.site_id),
        (WORKSPACE_DIMENSION_ID, scope.workspace_id),
        (DATA_BOUNDARY_DIMENSION_ID, scope.data_boundary_id),
        (CONTEXT_DIMENSION_ID, scope.context_id),
    )


def _paired_dimension_values(
    candidate_scope: EvidenceScopeV1,
    run_scope: EvidenceScopeV1,
) -> tuple[tuple[TermId, object, object], ...]:
    return (
        (SCOPE_CLASS_DIMENSION_ID, candidate_scope.scope_class, run_scope.scope_class),
        (ORGANIZATION_DIMENSION_ID, candidate_scope.organization_id, run_scope.organization_id),
        (SITE_DIMENSION_ID, candidate_scope.site_id, run_scope.site_id),
        (WORKSPACE_DIMENSION_ID, candidate_scope.workspace_id, run_scope.workspace_id),
        (
            DATA_BOUNDARY_DIMENSION_ID,
            candidate_scope.data_boundary_id,
            run_scope.data_boundary_id,
        ),
        (CONTEXT_DIMENSION_ID, candidate_scope.context_id, run_scope.context_id),
    )


def _term_set_sort_key(value: object) -> str:
    if isinstance(value, ScopeTermSet):
        return str(value.dimension_id)
    if isinstance(value, dict):
        return str(value["dimension_id"])
    raise ValueError("scope term set must be a model or mapping value")
