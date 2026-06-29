from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.core.capabilities import (
    CAPABILITY_PROFILE_EXPIRED_REASON_ID,
    CAPABILITY_PROFILE_INACTIVE_REASON_ID,
    SOURCE_CLASS_UNKNOWN_REASON_ID,
    SOURCE_CLASS_UNSUPPORTED_REASON_ID,
    CapabilityProfile,
    CaptureProfileNotReady,
    CaptureProfileReady,
    SourceStoragePolicy,
    evaluate_capture_profile,
)
from gptl.core.records import GovernedRef, governed_record_content_hash
from gptl.core.scope import (
    CONTEXT_DIMENSION_ID,
    DATA_BOUNDARY_DIMENSION_ID,
    LIFECYCLE_DIMENSION_ID,
    ORGANIZATION_DIMENSION_ID,
    SCOPE_CLASS_DIMENSION_ID,
    SITE_DIMENSION_ID,
    WORKSPACE_DIMENSION_ID,
    EvidenceScopeV1,
    ScopeIncompatible,
    ScopeTermRegistry,
    ScopeTermUnknown,
    scope_matches,
    scope_ref_for_build0,
)
from gptl.core.semantic_types import TermId
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-06-29T12:00:00.000Z"
DEFAULT_ORGANIZATION_ID = TermId("org.boundstate")
DEFAULT_SITE_ID = TermId("site.materials-lab")
DEFAULT_WORKSPACE_ID = TermId("workspace.gptl-build1")
DEFAULT_DATA_BOUNDARY_ID = TermId("boundary.synthetic-build1")
DEFAULT_CONTEXT_ID = TermId("context.slice1")
TEST_REPORT_MAX_SOURCE_BYTES = 1024
MANUAL_UPLOAD_MAX_SOURCE_BYTES = 2048


def test_scope_exact_match_is_replay_stable(build1_ref_factory: Callable[[str], GovernedRef]) -> None:
    policy = canonicalization_policy()
    candidate_scope = _scope(build1_ref_factory)
    run_scope = _scope(build1_ref_factory, ref_id="build1.scope.run")

    first = scope_matches(candidate_scope, run_scope)
    second = scope_matches(candidate_scope, run_scope)

    assert first.status == "MATCHED"
    assert canonical_bytes(first, policy) == canonical_bytes(second, policy)


@pytest.mark.parametrize(
    "field,value,dimension_id",
    (
        ("scope_class", "RESEARCH_CORPUS", SCOPE_CLASS_DIMENSION_ID),
        ("organization_id", TermId("org.other"), ORGANIZATION_DIMENSION_ID),
        ("site_id", TermId("site.other"), SITE_DIMENSION_ID),
        ("workspace_id", TermId("workspace.other"), WORKSPACE_DIMENSION_ID),
        ("data_boundary_id", TermId("boundary.other"), DATA_BOUNDARY_DIMENSION_ID),
        ("context_id", TermId("context.other"), CONTEXT_DIMENSION_ID),
    ),
)
def test_scope_mismatch_reports_exact_dimension(
    build1_ref_factory: Callable[[str], GovernedRef],
    field: str,
    value: object,
    dimension_id: TermId,
) -> None:
    candidate_scope = _scope(build1_ref_factory)
    run_scope = _scope(build1_ref_factory, ref_id="build1.scope.run").model_copy(
        update={field: value}
    )

    result = scope_matches(candidate_scope, run_scope)

    assert isinstance(result, ScopeIncompatible)
    assert result.status == "SCOPE_INCOMPATIBLE"
    assert result.mismatched_dimension_ids == (dimension_id,)


def test_inactive_scope_is_not_eligible(build1_ref_factory: Callable[[str], GovernedRef]) -> None:
    candidate_scope = _scope(build1_ref_factory, lifecycle_state="INACTIVE")
    run_scope = _scope(build1_ref_factory, ref_id="build1.scope.run")

    result = scope_matches(candidate_scope, run_scope)

    assert isinstance(result, ScopeIncompatible)
    assert result.mismatched_dimension_ids == (LIFECYCLE_DIMENSION_ID,)


@pytest.mark.parametrize("sentinel", ("UNSCOPED", "WILDCARD", "application-default"))
def test_unscoped_default_or_wildcard_terms_are_invalid(
    build1_ref_factory: Callable[[str], GovernedRef],
    sentinel: str,
) -> None:
    with pytest.raises(ValidationError, match="unscoped or default sentinel"):
        _scope(build1_ref_factory, organization_id=TermId(sentinel))


def test_scope_term_registry_fails_closed_on_unknown_dimension_term(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    result = evaluate_capture_profile(
        _profile(build1_ref_factory),
        _scope(build1_ref_factory, organization_id=TermId("org.not-registered")),
        _scope(build1_ref_factory, ref_id="build1.scope.run"),
        _term_registry(build1_ref_factory),
        TermId("source-class.test-report"),
        AS_OF,
    )

    assert isinstance(result, CaptureProfileNotReady)
    assert isinstance(result.scope_result, ScopeTermUnknown)
    assert result.reason_id == "build1.scope.term-unknown"
    assert result.scope_result.unknown_dimension_ids == (ORGANIZATION_DIMENSION_ID,)


def test_wildcard_character_is_rejected_by_the_scalar_type(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    with pytest.raises(ValidationError, match="String should match pattern"):
        _scope(build1_ref_factory, organization_id=TermId("*"))


def test_scope_requires_all_fields_and_forbids_extra(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    payload = _scope(build1_ref_factory).model_dump(mode="python")

    missing_context = dict(payload)
    missing_context.pop("context_id")
    with pytest.raises(ValidationError, match="context_id"):
        EvidenceScopeV1.model_validate(missing_context)

    with_extra = dict(payload)
    with_extra["implicit_parent_scope"] = "scope.parent"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        EvidenceScopeV1.model_validate(with_extra)


def test_capability_profile_lists_are_order_independent(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    profile_a = _profile(build1_ref_factory, unordered=True)
    profile_b = _profile(build1_ref_factory, unordered=False)

    assert canonical_bytes(profile_a, policy) == canonical_bytes(profile_b, policy)
    assert tuple(profile_a.instrument_tool_type_ids) == (
        "tool.microhardness",
        "tool.sem",
    )
    assert tuple(item.source_system_id for item in profile_a.source_systems) == (
        "source-system.file-drop",
        "source-system.lims",
    )
    assert tuple(item.source_class_id for item in profile_a.accepted_source_classes) == (
        "source-class.manual-upload",
        "source-class.test-report",
    )
    assert profile_a.unsupported_source_classes == ("source-class.vendor-binary",)


def test_duplicate_capability_entries_are_rejected(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    payload = _profile_payload(build1_ref_factory)
    payload["source_systems"] = (
        {
            "source_system_id": "source-system.lims",
            "lifecycle_state": "ACTIVE",
            "source_system_class_id": "source-system-class.lims",
        },
        {
            "source_system_id": "source-system.lims",
            "lifecycle_state": "ACTIVE",
            "source_system_class_id": "source-system-class.file-drop",
        },
    )

    with pytest.raises(ValidationError, match="source systems must be unique"):
        _validate_profile_payload(payload)


def test_profile_declares_slice1_fields_from_plan_section_4(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    profile = _profile(build1_ref_factory)

    assert profile.canonicalization_policy_ref.logical_id == "build1.canonicalization.policy"
    assert profile.effective_at == "2026-06-01T00:00:00.000Z"
    assert profile.expires_at == "2026-12-31T23:59:59.000Z"
    assert profile.owner_ref.logical_id == "build1.owner.materials"
    assert profile.authority_policy_ref.logical_id == "build1.authority.policy"
    assert profile.instrument_tool_type_ids == ("tool.microhardness", "tool.sem")
    assert profile.measurement_class_ids == ("measurement.hardness", "measurement.micrograph")
    assert profile.calibration_msa_capability_label_ids == (
        "capability-label.calibration-records-present",
        "capability-label.msa-records-present",
    )
    assert profile.evidence_refs


def test_capture_readiness_requires_active_profile_and_scope(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    profile = _profile(build1_ref_factory)
    candidate_scope = _scope(build1_ref_factory)
    run_scope = _scope(build1_ref_factory, ref_id="build1.scope.run")

    ready = evaluate_capture_profile(
        profile,
        candidate_scope,
        run_scope,
        _term_registry(build1_ref_factory),
        TermId("source-class.test-report"),
        AS_OF,
    )
    inactive_profile = profile.model_copy(update={"lifecycle_state": "INACTIVE"})
    inactive = evaluate_capture_profile(
        inactive_profile,
        candidate_scope,
        run_scope,
        _term_registry(build1_ref_factory),
        TermId("source-class.test-report"),
        AS_OF,
    )

    assert isinstance(ready, CaptureProfileReady)
    assert ready.status == "READY"
    assert ready.evidence_scope_ref == run_scope.scope_ref
    assert isinstance(inactive, CaptureProfileNotReady)
    assert inactive.reason_id == CAPABILITY_PROFILE_INACTIVE_REASON_ID
    assert inactive.capability_failure is not None
    assert inactive.capability_failure.status == "UNAVAILABLE"


def test_expired_profile_fails_before_source_selection(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    result = evaluate_capture_profile(
        _profile(build1_ref_factory),
        _scope(build1_ref_factory),
        _scope(build1_ref_factory, ref_id="build1.scope.run"),
        _term_registry(build1_ref_factory),
        TermId("source-class.test-report"),
        "2027-01-01T00:00:00.000Z",
    )

    assert isinstance(result, CaptureProfileNotReady)
    assert result.reason_id == CAPABILITY_PROFILE_EXPIRED_REASON_ID
    assert result.capability_failure is not None
    assert result.capability_failure.status == "UNAVAILABLE"


def test_scope_failure_stops_before_source_class_resolution(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    profile = _profile(build1_ref_factory)
    candidate_scope = _scope(build1_ref_factory)
    run_scope = _scope(
        build1_ref_factory,
        ref_id="build1.scope.run",
        organization_id=TermId("org.other"),
    )

    result = evaluate_capture_profile(
        profile,
        candidate_scope,
        run_scope,
        _term_registry(build1_ref_factory, organization_id=TermId("org.other")),
        TermId("source-class.unknown"),
        AS_OF,
    )

    assert isinstance(result, CaptureProfileNotReady)
    assert result.scope_result is not None
    assert result.capability_failure is None
    assert result.reason_id == "build1.scope.incompatible"


def test_unknown_and_unsupported_source_classes_are_distinct(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    unknown = evaluate_capture_profile(
        _profile(build1_ref_factory),
        _scope(build1_ref_factory),
        _scope(build1_ref_factory, ref_id="build1.scope.run"),
        _term_registry(build1_ref_factory),
        TermId("source-class.not-declared"),
        AS_OF,
    )
    unsupported = evaluate_capture_profile(
        _profile(build1_ref_factory),
        _scope(build1_ref_factory),
        _scope(build1_ref_factory, ref_id="build1.scope.run"),
        _term_registry(build1_ref_factory),
        TermId("source-class.vendor-binary"),
        AS_OF,
    )

    assert isinstance(unknown, CaptureProfileNotReady)
    assert isinstance(unsupported, CaptureProfileNotReady)
    assert unknown.reason_id == SOURCE_CLASS_UNKNOWN_REASON_ID
    assert unsupported.reason_id == SOURCE_CLASS_UNSUPPORTED_REASON_ID
    assert unknown.capability_failure is not None
    assert unsupported.capability_failure is not None
    assert unknown.capability_failure.status == "UNKNOWN"
    assert unsupported.capability_failure.status == "UNSUPPORTED"


@pytest.mark.parametrize("field", ("owner_ref", "authority_policy_ref"))
def test_owner_and_authority_policy_are_required_before_capture_selection(
    build1_ref_factory: Callable[[str], GovernedRef],
    field: str,
) -> None:
    payload = _profile_payload(build1_ref_factory)
    payload.pop(field)

    with pytest.raises(ValidationError, match=field):
        _validate_profile_payload(payload)


def test_storage_policy_requires_positive_governed_byte_limit(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        SourceStoragePolicy.model_validate(
            {
                "storage_policy_ref": build1_ref_factory("build1.storage.invalid"),
                "canonicalization_policy_ref": build1_ref_factory(
                    "build1.canonicalization.policy"
                ),
                "lifecycle_state": "ACTIVE",
                "max_bytes_per_source_record": 0,
                "allowed_evidence_locator_classes": (TermId("evidence.byte-range"),),
            }
        )


def test_self_content_hash_is_excluded_from_governed_record_hash(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    policy = canonicalization_policy()
    scope = _scope(build1_ref_factory)
    changed_hash_ref = scope.scope_ref.model_copy(update={"content_hash": "f" * 64})
    changed_hash = scope.model_copy(update={"scope_ref": changed_hash_ref})
    changed_context = scope.model_copy(update={"context_id": TermId("context.changed")})

    assert governed_record_content_hash(scope, "scope_ref", policy) == governed_record_content_hash(
        changed_hash,
        "scope_ref",
        policy,
    )
    assert governed_record_content_hash(scope, "scope_ref", policy) != governed_record_content_hash(
        changed_context,
        "scope_ref",
        policy,
    )


def test_scope_publication_for_build0_uses_complete_governed_ref(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    scope = _scope(build1_ref_factory)
    ref = scope_ref_for_build0(scope)

    assert ref == scope.scope_ref
    assert set(GovernedRef.model_fields) == {
        "logical_id",
        "version_id",
        "version_number",
        "content_hash",
    }


def test_slice1_runtime_sources_do_not_introduce_prohibited_mechanisms(
    runtime_source_guard,
) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard(
        (
            repository_root / "src" / "gptl" / "core" / "capabilities.py",
            repository_root / "src" / "gptl" / "core" / "scope.py",
        )
    )


def _scope(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    ref_id: str = "build1.scope.candidate",
    lifecycle_state: str = "ACTIVE",
    scope_class: str = "TEST_FIXTURE",
    organization_id: TermId = DEFAULT_ORGANIZATION_ID,
    site_id: TermId = DEFAULT_SITE_ID,
    workspace_id: TermId = DEFAULT_WORKSPACE_ID,
    data_boundary_id: TermId = DEFAULT_DATA_BOUNDARY_ID,
    context_id: TermId = DEFAULT_CONTEXT_ID,
) -> EvidenceScopeV1:
    return EvidenceScopeV1(
        schema_version="gptl.build1.evidence-scope.v1",
        scope_ref=build1_ref_factory(ref_id),
        canonicalization_policy_ref=build1_ref_factory("build1.canonicalization.policy"),
        lifecycle_state=lifecycle_state,
        scope_class=scope_class,
        organization_id=organization_id,
        site_id=site_id,
        workspace_id=workspace_id,
        data_boundary_id=data_boundary_id,
        context_id=context_id,
    )


def _term_registry(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    organization_id: TermId = DEFAULT_ORGANIZATION_ID,
) -> ScopeTermRegistry:
    organization_terms = tuple(sorted({DEFAULT_ORGANIZATION_ID, organization_id}))
    return ScopeTermRegistry.model_validate(
        {
            "registry_ref": build1_ref_factory("build1.scope-term-registry"),
            "term_sets": (
                {
                    "dimension_id": SCOPE_CLASS_DIMENSION_ID,
                    "allowed_term_ids": ("TEST_FIXTURE", "RESEARCH_CORPUS"),
                },
                {
                    "dimension_id": ORGANIZATION_DIMENSION_ID,
                    "allowed_term_ids": organization_terms,
                },
                {
                    "dimension_id": SITE_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_SITE_ID,),
                },
                {
                    "dimension_id": WORKSPACE_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_WORKSPACE_ID,),
                },
                {
                    "dimension_id": DATA_BOUNDARY_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_DATA_BOUNDARY_ID,),
                },
                {
                    "dimension_id": CONTEXT_DIMENSION_ID,
                    "allowed_term_ids": (DEFAULT_CONTEXT_ID,),
                },
            ),
        }
    )


def _profile(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    unordered: bool = False,
) -> CapabilityProfile:
    payload = _profile_payload(build1_ref_factory)
    if unordered:
        payload["instrument_tool_type_ids"] = tuple(reversed(payload["instrument_tool_type_ids"]))
        payload["source_systems"] = tuple(reversed(payload["source_systems"]))
        payload["accepted_source_classes"] = tuple(reversed(payload["accepted_source_classes"]))
        payload["unsupported_source_classes"] = tuple(
            reversed(payload["unsupported_source_classes"])
        )
        payload["measurement_class_ids"] = tuple(reversed(payload["measurement_class_ids"]))
        payload["calibration_msa_capability_label_ids"] = tuple(
            reversed(payload["calibration_msa_capability_label_ids"])
        )
        payload["storage_policies"] = tuple(reversed(payload["storage_policies"]))
        payload["evidence_refs"] = tuple(reversed(payload["evidence_refs"]))
    return _validate_profile_payload(payload)


def _validate_profile_payload(payload: dict[str, object]) -> CapabilityProfile:
    return CapabilityProfile.model_validate(
        payload,
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _profile_payload(build1_ref_factory: Callable[[str], GovernedRef]) -> dict[str, object]:
    storage_report = build1_ref_factory("build1.storage.report")
    storage_upload = build1_ref_factory("build1.storage.upload")
    canonicalization_policy_ref = build1_ref_factory("build1.canonicalization.policy")
    return {
        "schema_version": "gptl.build1.capability-profile.v1",
        "profile_ref": build1_ref_factory("build1.capability.profile"),
        "canonicalization_policy_ref": canonicalization_policy_ref,
        "lifecycle_state": "ACTIVE",
        "effective_at": "2026-06-01T00:00:00.000Z",
        "expires_at": "2026-12-31T23:59:59.000Z",
        "owner_ref": build1_ref_factory("build1.owner.materials"),
        "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
        "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
        "instrument_tool_type_ids": ("tool.sem", "tool.microhardness"),
        "source_systems": (
            {
                "source_system_id": "source-system.lims",
                "lifecycle_state": "ACTIVE",
                "source_system_class_id": "source-system-class.lims",
            },
            {
                "source_system_id": "source-system.file-drop",
                "lifecycle_state": "ACTIVE",
                "source_system_class_id": "source-system-class.file-drop",
            },
        ),
        "accepted_source_classes": (
            {
                "source_class_id": "source-class.test-report",
                "source_system_id": "source-system.lims",
                "storage_policy_ref": storage_report,
            },
            {
                "source_class_id": "source-class.manual-upload",
                "source_system_id": "source-system.file-drop",
                "storage_policy_ref": storage_upload,
            },
        ),
        "unsupported_source_classes": ("source-class.vendor-binary",),
        "measurement_class_ids": ("measurement.micrograph", "measurement.hardness"),
        "calibration_msa_capability_label_ids": (
            "capability-label.msa-records-present",
            "capability-label.calibration-records-present",
        ),
        "storage_policies": (
            {
                "storage_policy_ref": storage_report,
                "canonicalization_policy_ref": canonicalization_policy_ref,
                "lifecycle_state": "ACTIVE",
                "max_bytes_per_source_record": TEST_REPORT_MAX_SOURCE_BYTES,
                "allowed_evidence_locator_classes": (
                    "evidence.cell-range",
                    "evidence.byte-range",
                ),
            },
            {
                "storage_policy_ref": storage_upload,
                "canonicalization_policy_ref": canonicalization_policy_ref,
                "lifecycle_state": "ACTIVE",
                "max_bytes_per_source_record": MANUAL_UPLOAD_MAX_SOURCE_BYTES,
                "allowed_evidence_locator_classes": (
                    "evidence.byte-range",
                    "evidence.page-region",
                ),
            },
        ),
        "evidence_refs": (
            build1_ref_factory("build1.evidence.capability-owner"),
            build1_ref_factory("build1.evidence.capability-source-inventory"),
        ),
    }
