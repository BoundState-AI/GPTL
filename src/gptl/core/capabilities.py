"""Build 1 facility/tool capability profile contracts."""

from __future__ import annotations

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from gptl.core.records import GovernedRef
from gptl.core.scope import EvidenceScopeV1, ScopeIncompatible, scope_matches
from gptl.core.semantic_types import PositiveInt, TermId

SOURCE_CLASS_SUPPORTED_REASON_ID: Final = TermId("build1.capability.source-class-supported")
SOURCE_CLASS_UNSUPPORTED_REASON_ID: Final = TermId("build1.capability.source-class-unsupported")
CAPABILITY_PROFILE_INACTIVE_REASON_ID: Final = TermId("build1.capability.profile-inactive")
SOURCE_SYSTEM_INACTIVE_REASON_ID: Final = TermId("build1.capability.source-system-inactive")
SOURCE_STORAGE_POLICY_INACTIVE_REASON_ID: Final = TermId(
    "build1.capability.source-storage-policy-inactive"
)
CAPABILITY_CONFIGURATION_INVALID_REASON_ID: Final = TermId(
    "build1.capability.configuration-invalid"
)


class SourceStoragePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    storage_policy_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    max_bytes_per_source_record: PositiveInt
    allowed_evidence_locator_classes: tuple[TermId, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_locator_classes(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "allowed_evidence_locator_classes" in normalized:
            normalized["allowed_evidence_locator_classes"] = tuple(
                sorted(normalized["allowed_evidence_locator_classes"])
            )
        return normalized

    @model_validator(mode="after")
    def validate_locator_classes(self) -> SourceStoragePolicy:
        if not self.allowed_evidence_locator_classes:
            raise ValueError("source storage policy requires evidence locator classes")
        if self.allowed_evidence_locator_classes != tuple(
            sorted(set(self.allowed_evidence_locator_classes))
        ):
            raise ValueError("evidence locator classes must be unique and sorted")
        return self


class SourceSystemCapability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_system_id: TermId
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    source_system_class_id: TermId


class AcceptedSourceClass(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_class_id: TermId
    source_system_id: TermId
    storage_policy_ref: GovernedRef


class CapabilityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gptl.build1.capability-profile.v1"]
    profile_ref: GovernedRef
    lifecycle_state: Literal["ACTIVE", "INACTIVE"]
    owner_ref: GovernedRef
    authority_policy_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    source_systems: tuple[SourceSystemCapability, ...]
    accepted_source_classes: tuple[AcceptedSourceClass, ...]
    storage_policies: tuple[SourceStoragePolicy, ...]

    @model_validator(mode="before")
    @classmethod
    def sort_profile_lists(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "source_systems" in normalized:
            normalized["source_systems"] = tuple(
                sorted(normalized["source_systems"], key=_source_system_sort_key)
            )
        if "accepted_source_classes" in normalized:
            normalized["accepted_source_classes"] = tuple(
                sorted(normalized["accepted_source_classes"], key=_accepted_source_class_sort_key)
            )
        if "storage_policies" in normalized:
            normalized["storage_policies"] = tuple(
                sorted(normalized["storage_policies"], key=_storage_policy_sort_key)
            )
        return normalized

    @model_validator(mode="after")
    def validate_profile(self) -> CapabilityProfile:
        if not self.source_systems:
            raise ValueError("capability profile requires at least one source system")
        if not self.storage_policies:
            raise ValueError("capability profile requires at least one source storage policy")

        source_ids = tuple(item.source_system_id for item in self.source_systems)
        if source_ids != tuple(sorted(set(source_ids))):
            raise ValueError("source systems must be unique and sorted")

        policy_keys = tuple(_ref_key(item.storage_policy_ref) for item in self.storage_policies)
        if policy_keys != tuple(sorted(set(policy_keys))):
            raise ValueError("source storage policies must be unique and sorted")

        source_class_ids = tuple(item.source_class_id for item in self.accepted_source_classes)
        if source_class_ids != tuple(sorted(set(source_class_ids))):
            raise ValueError("accepted source classes must be unique and sorted")

        known_source_ids = set(source_ids)
        known_policy_keys = set(policy_keys)
        for accepted in self.accepted_source_classes:
            if accepted.source_system_id not in known_source_ids:
                raise ValueError("accepted source class references an unknown source system")
            if _ref_key(accepted.storage_policy_ref) not in known_policy_keys:
                raise ValueError("accepted source class references an unknown storage policy")
        return self


class SourceClassSupported(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["SUPPORTED"]
    reason_id: TermId
    source_class_id: TermId
    source_system_id: TermId
    storage_policy_ref: GovernedRef


class CapabilityGap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["CAPABILITY_GAP", "CONFIGURATION_INVALID"]
    reason_id: TermId
    source_class_id: TermId
    profile_ref: GovernedRef


SourceClassSupportResult = SourceClassSupported | CapabilityGap


class CaptureProfileReady(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["READY"]
    profile_ref: GovernedRef
    evidence_scope_ref: GovernedRef
    source_class_id: TermId
    source_system_id: TermId
    storage_policy_ref: GovernedRef


class CaptureProfileNotReady(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["NOT_READY"]
    reason_id: TermId
    profile_ref: GovernedRef
    source_class_id: TermId
    scope_result: ScopeIncompatible | None
    capability_gap: CapabilityGap | None

    @model_validator(mode="after")
    def validate_cause(self) -> CaptureProfileNotReady:
        if (self.scope_result is None) == (self.capability_gap is None):
            raise ValueError("capture-profile failure requires exactly one cause")
        return self


CaptureProfileReadiness = CaptureProfileReady | CaptureProfileNotReady


def resolve_source_class_support(
    profile: CapabilityProfile,
    source_class_id: TermId,
) -> SourceClassSupportResult:
    if profile.lifecycle_state != "ACTIVE":
        return _capability_gap(profile, source_class_id, CAPABILITY_PROFILE_INACTIVE_REASON_ID)

    accepted = next(
        (
            candidate
            for candidate in profile.accepted_source_classes
            if candidate.source_class_id == source_class_id
        ),
        None,
    )
    if accepted is None:
        return _capability_gap(profile, source_class_id, SOURCE_CLASS_UNSUPPORTED_REASON_ID)

    source_system = next(
        (
            candidate
            for candidate in profile.source_systems
            if candidate.source_system_id == accepted.source_system_id
        ),
        None,
    )
    if source_system is None:
        return _configuration_gap(profile, source_class_id)
    if source_system.lifecycle_state != "ACTIVE":
        return _capability_gap(profile, source_class_id, SOURCE_SYSTEM_INACTIVE_REASON_ID)

    storage_policy = next(
        (
            candidate
            for candidate in profile.storage_policies
            if _ref_key(candidate.storage_policy_ref) == _ref_key(accepted.storage_policy_ref)
        ),
        None,
    )
    if storage_policy is None:
        return _configuration_gap(profile, source_class_id)
    if storage_policy.lifecycle_state != "ACTIVE":
        return _capability_gap(
            profile,
            source_class_id,
            SOURCE_STORAGE_POLICY_INACTIVE_REASON_ID,
        )

    return SourceClassSupported(
        status="SUPPORTED",
        reason_id=SOURCE_CLASS_SUPPORTED_REASON_ID,
        source_class_id=accepted.source_class_id,
        source_system_id=accepted.source_system_id,
        storage_policy_ref=accepted.storage_policy_ref,
    )


def evaluate_capture_profile(
    profile: CapabilityProfile,
    candidate_scope: EvidenceScopeV1,
    run_scope: EvidenceScopeV1,
    source_class_id: TermId,
) -> CaptureProfileReadiness:
    scope_result = scope_matches(candidate_scope, run_scope)
    if isinstance(scope_result, ScopeIncompatible):
        return CaptureProfileNotReady(
            status="NOT_READY",
            reason_id=scope_result.reason_id,
            profile_ref=profile.profile_ref,
            source_class_id=source_class_id,
            scope_result=scope_result,
            capability_gap=None,
        )

    support = resolve_source_class_support(profile, source_class_id)
    if isinstance(support, CapabilityGap):
        return CaptureProfileNotReady(
            status="NOT_READY",
            reason_id=support.reason_id,
            profile_ref=profile.profile_ref,
            source_class_id=source_class_id,
            scope_result=None,
            capability_gap=support,
        )

    return CaptureProfileReady(
        status="READY",
        profile_ref=profile.profile_ref,
        evidence_scope_ref=run_scope.scope_ref,
        source_class_id=support.source_class_id,
        source_system_id=support.source_system_id,
        storage_policy_ref=support.storage_policy_ref,
    )


def _capability_gap(
    profile: CapabilityProfile,
    source_class_id: TermId,
    reason_id: TermId,
) -> CapabilityGap:
    return CapabilityGap(
        status="CAPABILITY_GAP",
        reason_id=reason_id,
        source_class_id=source_class_id,
        profile_ref=profile.profile_ref,
    )


def _configuration_gap(profile: CapabilityProfile, source_class_id: TermId) -> CapabilityGap:
    return CapabilityGap(
        status="CONFIGURATION_INVALID",
        reason_id=CAPABILITY_CONFIGURATION_INVALID_REASON_ID,
        source_class_id=source_class_id,
        profile_ref=profile.profile_ref,
    )


def _source_system_sort_key(value: Any) -> str:
    return str(_field_value(value, "source_system_id"))


def _accepted_source_class_sort_key(value: Any) -> tuple[str, str]:
    return (
        str(_field_value(value, "source_class_id")),
        str(_field_value(value, "source_system_id")),
    )


def _storage_policy_sort_key(value: Any) -> tuple[str, str]:
    return _ref_key(_field_value(value, "storage_policy_ref"))


def _field_value(value: Any, field_name: str) -> Any:
    if isinstance(value, BaseModel):
        return getattr(value, field_name)
    if isinstance(value, dict):
        return value[field_name]
    raise ValueError("capability profile lists must contain model or mapping values")


def _ref_key(ref: Any) -> tuple[str, str]:
    if isinstance(ref, GovernedRef):
        return (str(ref.logical_id), str(ref.version_id))
    if isinstance(ref, dict):
        return (str(ref["logical_id"]), str(ref["version_id"]))
    raise ValueError("governed reference is required")
