"""Governed elimination and bounded-catalog rule-out contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.directives import DisplayDirective
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import EvidenceLocator, TermId
from gptl.mie.predicates import Predicate


class HardEliminationRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    candidate_ref: GovernedRef
    predicate_ref: GovernedRef
    predicate: Predicate
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> HardEliminationRule:
        if not self.evidence_refs or sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("hard-elimination evidence must be nonempty, unique, and sorted")
        return self


class RuleOutEvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requirement_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    candidate_ref: GovernedRef
    required_discriminator_refs: tuple[GovernedRef, ...]
    aggregation: Literal["ALL_CONSISTENT_WITH_REAL"]
    tau_ruleout_policy_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> RuleOutEvidenceRequirement:
        if (
            not self.required_discriminator_refs
            or sorted_unique_refs(self.required_discriminator_refs)
            != self.required_discriminator_refs
        ):
            raise ValueError("rule-out discriminators must be nonempty, unique, and sorted")
        if not self.evidence_refs or sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("rule-out evidence must be nonempty, unique, and sorted")
        return self


class CatalogKnownGap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    gap_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    category_id: TermId
    why_unevaluated: DisplayDirective
    what_would_enable: DisplayDirective
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> CatalogKnownGap:
        if not self.evidence_refs or sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("known-gap evidence must be nonempty, unique, and sorted")
        return self


class NegativeRoutePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    min_evaluated_fraction_policy_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> NegativeRoutePolicy:
        if not self.evidence_refs or sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("negative route-policy evidence must be nonempty, unique, and sorted")
        return self
