from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import ValidationError

from gptl.core.capabilities import CapabilityProfile
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import PositiveInt, TermId
from gptl.slice1_fixture import canonicalization_policy
from gptl.tools.standard_pack import (
    CAL_MAGNIFICATION,
    CAL_RECORDS_PRESENT,
    standard_tool_registry,
)
from gptl.tools.taxonomy import (
    TOOL_CALIBRATION_LABEL_MISSING_REASON_ID,
    TOOL_INACTIVE_REASON_ID,
    TOOL_MEASUREMENT_CLASS_UNDECLARED_REASON_ID,
    TOOL_NOT_IN_FACILITY_PROFILE_REASON_ID,
    TOOL_SOURCE_CLASS_UNDECLARED_REASON_ID,
    TOOL_UNKNOWN_REASON_ID,
    AnalyticalToolDefinition,
    AnalyticalToolRegistry,
    ToolFacilityReady,
    ToolFacilityRefused,
    ToolInactive,
    ToolResolved,
    ToolUnknown,
    analytical_tool_content_hash,
    resolve_tool_for_facility,
)

AS_OF = "2026-07-01T12:00:00.000Z"
SEM_MAX_SOURCE_BYTES: PositiveInt = 50_000_000

EXPECTED_SPECTRAL = (
    "tool.dsc",
    "tool.eds",
    "tool.ftir",
    "tool.gc-ms",
    "tool.icp-ms",
    "tool.icp-oes",
    "tool.oes",
    "tool.raman",
    "tool.tga",
    "tool.xrd",
    "tool.xrf",
)
EXPECTED_VISUAL = (
    "tool.fib",
    "tool.optical-microscopy",
    "tool.sem",
    "tool.tem",
)


def test_standard_pack_covers_both_modalities_with_real_content_hashes() -> None:
    registry = standard_tool_registry(canonicalization_policy())

    spectral = tuple(tool.tool_type_id for tool in registry.tools_for_modality("SPECTRAL"))
    visual = tuple(tool.tool_type_id for tool in registry.tools_for_modality("VISUAL"))

    assert spectral == EXPECTED_SPECTRAL
    assert visual == EXPECTED_VISUAL
    assert len(registry.tools) == len(EXPECTED_SPECTRAL) + len(EXPECTED_VISUAL)
    for tool in registry.tools:
        assert tool.lifecycle_state == "ACTIVE"
        assert tool.tool_ref.content_hash == analytical_tool_content_hash(
            tool, canonicalization_policy()
        )
        assert "MODEL_ASSISTED" in tool.allowed_proposal_methods


def test_registry_resolution_fails_closed_for_unknown_and_inactive() -> None:
    registry = standard_tool_registry(canonicalization_policy())

    unknown = registry.resolve(TermId("tool.does-not-exist"))
    assert isinstance(unknown, ToolUnknown)
    assert unknown.reason_id == TOOL_UNKNOWN_REASON_ID

    retired = registry.tools[0].model_copy(update={"lifecycle_state": "INACTIVE"})
    amended = AnalyticalToolRegistry(
        registry_ref=registry.registry_ref,
        canonicalization_policy_ref=registry.canonicalization_policy_ref,
        tools=(retired, *registry.tools[1:]),
    )
    inactive = amended.resolve(retired.tool_type_id)
    assert isinstance(inactive, ToolInactive)
    assert inactive.reason_id == TOOL_INACTIVE_REASON_ID


def test_definition_rejects_overlapping_measurement_and_observation_classes() -> None:
    registry = standard_tool_registry(canonicalization_policy())
    sem = next(tool for tool in registry.tools if tool.tool_type_id == "tool.sem")

    payload = sem.model_dump(mode="python")
    payload["observation_class_ids"] = ("measurement.grain-size",)
    with pytest.raises(ValidationError, match="both a measurement and an observation"):
        AnalyticalToolDefinition.model_validate(payload)


def test_facility_resolution_ready_when_profile_declares_everything(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    registry = standard_tool_registry(canonicalization_policy())
    profile = _facility_profile(build2_ref_factory)

    result = resolve_tool_for_facility(registry, TermId("tool.sem"), profile, AS_OF)

    assert isinstance(result, ToolFacilityReady)
    assert result.profile_ref == profile.profile_ref


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    (
        ("drop_tool_type", TOOL_NOT_IN_FACILITY_PROFILE_REASON_ID),
        ("drop_calibration_label", TOOL_CALIBRATION_LABEL_MISSING_REASON_ID),
        ("drop_measurement_class", TOOL_MEASUREMENT_CLASS_UNDECLARED_REASON_ID),
        ("drop_source_class", TOOL_SOURCE_CLASS_UNDECLARED_REASON_ID),
    ),
)
def test_facility_resolution_fails_closed_naming_missing_terms(
    build2_ref_factory: Callable[[str], GovernedRef],
    mutation: str,
    expected_reason: TermId,
) -> None:
    registry = standard_tool_registry(canonicalization_policy())
    profile = _facility_profile(build2_ref_factory, mutation=mutation)

    result = resolve_tool_for_facility(registry, TermId("tool.sem"), profile, AS_OF)

    assert isinstance(result, ToolFacilityRefused)
    assert result.reason_id == expected_reason
    if mutation == "drop_calibration_label":
        assert result.missing_term_ids == (CAL_MAGNIFICATION,)
    if mutation == "drop_measurement_class":
        assert result.missing_term_ids == (TermId("measurement.particle-size"),)
    if mutation == "drop_source_class":
        assert result.missing_term_ids == (TermId("source-class.sem-micrograph"),)


def test_facility_resolution_passes_through_unknown_tool(
    build2_ref_factory: Callable[[str], GovernedRef],
) -> None:
    registry = standard_tool_registry(canonicalization_policy())
    profile = _facility_profile(build2_ref_factory)

    result = resolve_tool_for_facility(registry, TermId("tool.nope"), profile, AS_OF)

    assert isinstance(result, ToolUnknown)


def _facility_profile(
    build2_ref_factory: Callable[[str], GovernedRef],
    *,
    mutation: str | None = None,
) -> CapabilityProfile:
    resolved = standard_tool_registry(canonicalization_policy()).resolve(TermId("tool.sem"))
    assert isinstance(resolved, ToolResolved)
    sem = resolved.tool

    tool_type_ids: tuple[str, ...] = ("tool.sem",)
    calibration_labels: tuple[str, ...] = (CAL_RECORDS_PRESENT, CAL_MAGNIFICATION)
    measurement_classes: tuple[str, ...] = sem.measurement_class_ids
    accepted_classes: tuple[str, ...] = ("source-class.sem-micrograph",)

    if mutation == "drop_tool_type":
        tool_type_ids = ("tool.microhardness",)
    if mutation == "drop_calibration_label":
        calibration_labels = (CAL_RECORDS_PRESENT,)
    if mutation == "drop_measurement_class":
        measurement_classes = tuple(
            item for item in measurement_classes if item != "measurement.particle-size"
        )
    if mutation == "drop_source_class":
        accepted_classes = ("source-class.other-report",)

    storage_policy_ref = build2_ref_factory("build2.storage.micrograph")
    policy_ref = build2_ref_factory("build2.canonicalization.policy")
    return CapabilityProfile.model_validate(
        {
            "schema_version": "gptl.build1.capability-profile.v1",
            "profile_ref": build2_ref_factory("build2.capability.profile"),
            "canonicalization_policy_ref": policy_ref,
            "lifecycle_state": "ACTIVE",
            "effective_at": "2026-06-01T00:00:00.000Z",
            "expires_at": "2026-12-31T23:59:59.000Z",
            "owner_ref": build2_ref_factory("build2.owner.materials-lab"),
            "authority_policy_ref": build2_ref_factory("build2.authority.policy"),
            "evidence_scope_ref": build2_ref_factory("build2.scope.candidate"),
            "instrument_tool_type_ids": tool_type_ids,
            "source_systems": (
                {
                    "source_system_id": "source-system.microscopy-suite",
                    "lifecycle_state": "ACTIVE",
                    "source_system_class_id": "source-system-class.instrument-pc",
                },
            ),
            "accepted_source_classes": tuple(
                {
                    "source_class_id": source_class,
                    "source_system_id": "source-system.microscopy-suite",
                    "storage_policy_ref": storage_policy_ref,
                }
                for source_class in accepted_classes
            ),
            "unsupported_source_classes": ("source-class.vendor-binary",),
            "measurement_class_ids": measurement_classes,
            "calibration_msa_capability_label_ids": calibration_labels,
            "storage_policies": (
                {
                    "storage_policy_ref": storage_policy_ref,
                    "canonicalization_policy_ref": policy_ref,
                    "lifecycle_state": "ACTIVE",
                    "max_bytes_per_source_record": SEM_MAX_SOURCE_BYTES,
                    "allowed_evidence_locator_classes": ("evidence.byte-range",),
                },
            ),
            "evidence_refs": (build2_ref_factory("build2.evidence.capability-owner"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
