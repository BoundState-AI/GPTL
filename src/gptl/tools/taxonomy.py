"""
Module: Analytical Tool Taxonomy
Purpose: Build 2 analytical tool taxonomy: governed tool definitions and fail-closed registry.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True

An ``AnalyticalToolDefinition`` describes one analytical technique (XRD, SEM, ICP-MS,
...) as governed data: the measurement classes it may propose, the qualitative
observation classes it may attribute, the raw source classes it emits, and the
calibration/MSA capability labels a facility must hold before capture from that tool is
eligible. Engine code carries no tool-specific constants; techniques are records, and a
facility's Slice 1 ``CapabilityProfile`` decides which of them are live at a site.
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.capabilities import (
    CAPABILITY_PROFILE_EXPIRED_REASON_ID,
    CAPABILITY_PROFILE_INACTIVE_REASON_ID,
    CAPABILITY_PROFILE_NOT_EFFECTIVE_REASON_ID,
    CapabilityProfile,
)
from gptl.core.records import (
    GovernedRef,
    governed_record_content_hash,
    sorted_unique_refs,
)
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    CanonicalTimestamp,
    TermId,
)

ANALYTICAL_TOOL_SCHEMA_VERSION: Final = "gptl.build2.analytical-tool.v1"
ANALYTICAL_TOOL_RECORD_TYPE: Final = "ANALYTICAL_TOOL_DEFINITION"
HASH_ALGORITHM: Final = "SHA-256"

TOOL_RESOLVED_REASON_ID: Final = TermId("build2.tool.resolved")
TOOL_UNKNOWN_REASON_ID: Final = TermId("build2.tool.unknown")
TOOL_INACTIVE_REASON_ID: Final = TermId("build2.tool.inactive")
TOOL_FACILITY_READY_REASON_ID: Final = TermId("build2.tool.facility-ready")
TOOL_NOT_IN_FACILITY_PROFILE_REASON_ID: Final = TermId("build2.tool.not-in-facility-profile")
TOOL_CALIBRATION_LABEL_MISSING_REASON_ID: Final = TermId(
    "build2.tool.calibration-label-missing"
)
TOOL_MEASUREMENT_CLASS_UNDECLARED_REASON_ID: Final = TermId(
    "build2.tool.measurement-class-undeclared"
)
TOOL_SOURCE_CLASS_UNDECLARED_REASON_ID: Final = TermId(
    "build2.tool.source-class-undeclared"
)

ToolModality = Literal["SPECTRAL", "VISUAL"]
ProposalMethodId = Literal["DETERMINISTIC_PARSER", "MODEL_ASSISTED", "MANUAL_TRANSLATION"]


class AnalyticalToolDefinition(BaseModel):
    """Governed description of one analytical technique."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build2.analytical-tool.v1"]
    record_type: Literal["ANALYTICAL_TOOL_DEFINITION"]
    hash_algorithm: Literal["SHA-256"]
    tool_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    tool_type_id: TermId
    modality: ToolModality
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    display_label_id: TermId
    measurement_class_ids: tuple[TermId, ...]
    observation_class_ids: tuple[TermId, ...]
    emitted_source_class_ids: tuple[TermId, ...]
    required_calibration_label_ids: tuple[TermId, ...]
    allowed_proposal_methods: tuple[ProposalMethodId, ...]
    agent_role_id: TermId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_definition_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        for field_name in (
            "measurement_class_ids",
            "observation_class_ids",
            "emitted_source_class_ids",
            "required_calibration_label_ids",
            "allowed_proposal_methods",
        ):
            if field_name in normalized:
                normalized[field_name] = tuple(sorted(normalized[field_name]))
        if "evidence_refs" in normalized:
            refs = normalized["evidence_refs"]
            if isinstance(refs, tuple) and all(isinstance(item, GovernedRef) for item in refs):
                normalized["evidence_refs"] = sorted_unique_refs(refs)
        return normalized

    @model_validator(mode="after")
    def validate_definition(self) -> AnalyticalToolDefinition:
        for values, label in (
            (self.measurement_class_ids, "measurement classes"),
            (self.observation_class_ids, "observation classes"),
            (self.emitted_source_class_ids, "emitted source classes"),
            (self.required_calibration_label_ids, "calibration labels"),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"tool {label} must be unique and sorted")
        if not self.measurement_class_ids and not self.observation_class_ids:
            raise ValueError("tool must declare at least one measurement or observation class")
        overlap = set(self.measurement_class_ids) & set(self.observation_class_ids)
        if overlap:
            raise ValueError("a class cannot be both a measurement and an observation class")
        if not self.emitted_source_class_ids:
            raise ValueError("tool must declare at least one emitted source class")
        if not self.required_calibration_label_ids:
            raise ValueError("tool must declare its required calibration labels")
        if not self.allowed_proposal_methods:
            raise ValueError("tool must declare its allowed proposal methods")
        if len(set(self.allowed_proposal_methods)) != len(self.allowed_proposal_methods):
            raise ValueError("tool proposal methods must be unique")
        if not self.evidence_refs:
            raise ValueError("tool definition requires evidence references")
        if sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("tool evidence references must be unique and sorted")
        return self


def analytical_tool_content_hash(
    tool: AnalyticalToolDefinition,
    canonicalization_policy: CanonicalizationPolicy,
) -> str:
    return governed_record_content_hash(tool, "tool_ref", canonicalization_policy)


def finalize_analytical_tool_definition(
    tool: AnalyticalToolDefinition,
    canonicalization_policy: CanonicalizationPolicy,
) -> AnalyticalToolDefinition:
    content_hash = analytical_tool_content_hash(tool, canonicalization_policy)
    updated_ref = tool.tool_ref.model_copy(update={"content_hash": content_hash})
    return tool.model_copy(update={"tool_ref": updated_ref})


class ToolResolved(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["RESOLVED"]
    reason_id: TermId
    tool: AnalyticalToolDefinition


class ToolUnknown(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["UNKNOWN"]
    reason_id: TermId
    tool_type_id: TermId
    registry_ref: GovernedRef


class ToolInactive(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["INACTIVE"]
    reason_id: TermId
    tool_type_id: TermId
    tool_ref: GovernedRef


ToolResolution = ToolResolved | ToolUnknown | ToolInactive


class AnalyticalToolRegistry(BaseModel):
    """Exact, fail-closed lookup of governed tool definitions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_ref: GovernedRef
    canonicalization_policy_ref: GovernedRef
    tools: tuple[AnalyticalToolDefinition, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_tools(cls, value: object) -> object:
        if not isinstance(value, dict) or "tools" not in value:
            return value
        normalized = dict(value)
        tools = normalized["tools"]
        if isinstance(tools, tuple) and all(
            isinstance(item, AnalyticalToolDefinition) for item in tools
        ):
            normalized["tools"] = tuple(sorted(tools, key=lambda item: item.tool_type_id))
        return normalized

    @model_validator(mode="after")
    def validate_registry(self) -> AnalyticalToolRegistry:
        if not self.tools:
            raise ValueError("tool registry requires at least one tool definition")
        type_ids = tuple(tool.tool_type_id for tool in self.tools)
        if type_ids != tuple(sorted(set(type_ids))):
            raise ValueError("tool type ids must be unique and sorted")
        for tool in self.tools:
            if tool.canonicalization_policy_ref != self.canonicalization_policy_ref:
                raise ValueError("tool definitions must share the registry canonicalization policy")
        return self

    def resolve(self, tool_type_id: TermId) -> ToolResolution:
        tool = next(
            (candidate for candidate in self.tools if candidate.tool_type_id == tool_type_id),
            None,
        )
        if tool is None:
            return ToolUnknown(
                status="UNKNOWN",
                reason_id=TOOL_UNKNOWN_REASON_ID,
                tool_type_id=tool_type_id,
                registry_ref=self.registry_ref,
            )
        if tool.lifecycle_state != "ACTIVE":
            return ToolInactive(
                status="INACTIVE",
                reason_id=TOOL_INACTIVE_REASON_ID,
                tool_type_id=tool_type_id,
                tool_ref=tool.tool_ref,
            )
        return ToolResolved(status="RESOLVED", reason_id=TOOL_RESOLVED_REASON_ID, tool=tool)

    def tools_for_modality(self, modality: ToolModality) -> tuple[AnalyticalToolDefinition, ...]:
        return tuple(tool for tool in self.tools if tool.modality == modality)


class ToolFacilityReady(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["FACILITY_READY"]
    reason_id: TermId
    tool_ref: GovernedRef
    profile_ref: GovernedRef


class ToolFacilityRefused(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["FACILITY_REFUSED"]
    reason_id: TermId
    tool_type_id: TermId
    profile_ref: GovernedRef
    missing_term_ids: tuple[TermId, ...] = ()

    @model_validator(mode="after")
    def validate_missing_terms(self) -> ToolFacilityRefused:
        if self.missing_term_ids != tuple(sorted(set(self.missing_term_ids))):
            raise ValueError("missing term ids must be unique and sorted")
        return self


ToolFacilityResolution = ToolFacilityReady | ToolFacilityRefused | ToolUnknown | ToolInactive


def resolve_tool_for_facility(
    registry: AnalyticalToolRegistry,
    tool_type_id: TermId,
    profile: CapabilityProfile,
    as_of_time: CanonicalTimestamp,
) -> ToolFacilityResolution:
    """Fail-closed check that a facility profile actually supports a tool.

    A tool is facility-ready only when the profile is live at ``as_of_time``, declares
    the tool type, holds every calibration/MSA label the tool requires, declares every
    measurement class the tool may propose, and accepts every source class the tool
    emits. Anything less refuses with the missing governed terms named.
    """
    resolution = registry.resolve(tool_type_id)
    if not isinstance(resolution, ToolResolved):
        return resolution
    tool = resolution.tool

    if profile.lifecycle_state != "ACTIVE":
        return _facility_refused(tool, profile, CAPABILITY_PROFILE_INACTIVE_REASON_ID)
    if as_of_time < profile.effective_at:
        return _facility_refused(tool, profile, CAPABILITY_PROFILE_NOT_EFFECTIVE_REASON_ID)
    if profile.expires_at is not None and as_of_time > profile.expires_at:
        return _facility_refused(tool, profile, CAPABILITY_PROFILE_EXPIRED_REASON_ID)

    if tool.tool_type_id not in profile.instrument_tool_type_ids:
        return _facility_refused(tool, profile, TOOL_NOT_IN_FACILITY_PROFILE_REASON_ID)

    missing_labels = tuple(
        sorted(
            set(tool.required_calibration_label_ids)
            - set(profile.calibration_msa_capability_label_ids)
        )
    )
    if missing_labels:
        return _facility_refused(
            tool,
            profile,
            TOOL_CALIBRATION_LABEL_MISSING_REASON_ID,
            missing_labels,
        )

    missing_measurements = tuple(
        sorted(set(tool.measurement_class_ids) - set(profile.measurement_class_ids))
    )
    if missing_measurements:
        return _facility_refused(
            tool,
            profile,
            TOOL_MEASUREMENT_CLASS_UNDECLARED_REASON_ID,
            missing_measurements,
        )

    accepted_source_classes = {item.source_class_id for item in profile.accepted_source_classes}
    missing_sources = tuple(
        sorted(set(tool.emitted_source_class_ids) - accepted_source_classes)
    )
    if missing_sources:
        return _facility_refused(
            tool,
            profile,
            TOOL_SOURCE_CLASS_UNDECLARED_REASON_ID,
            missing_sources,
        )

    return ToolFacilityReady(
        status="FACILITY_READY",
        reason_id=TOOL_FACILITY_READY_REASON_ID,
        tool_ref=tool.tool_ref,
        profile_ref=profile.profile_ref,
    )


def _facility_refused(
    tool: AnalyticalToolDefinition,
    profile: CapabilityProfile,
    reason_id: TermId,
    missing_term_ids: tuple[TermId, ...] = (),
) -> ToolFacilityRefused:
    return ToolFacilityRefused(
        status="FACILITY_REFUSED",
        reason_id=reason_id,
        tool_type_id=tool.tool_type_id,
        profile_ref=profile.profile_ref,
        missing_term_ids=missing_term_ids,
    )
