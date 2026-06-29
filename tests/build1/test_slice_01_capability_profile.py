from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from gptl.core.canonical import canonical_bytes
from gptl.core.capabilities import (
    CAPABILITY_PROFILE_INACTIVE_REASON_ID,
    SOURCE_CLASS_UNSUPPORTED_REASON_ID,
    CapabilityProfile,
    CaptureProfileNotReady,
    CaptureProfileReady,
    SourceStoragePolicy,
    evaluate_capture_profile,
)
from gptl.core.records import GovernedRef
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
    scope_matches,
    scope_ref_for_build0,
)
from gptl.core.semantic_types import TermId
from gptl.slice1_fixture import canonicalization_policy

DEFAULT_ORGANIZATION_ID = TermId("org.boundstate")
DEFAULT_SITE_ID = TermId("site.materials-lab")
DEFAULT_WORKSPACE_ID = TermId("workspace.gptl-build1")
DEFAULT_DATA_BOUNDARY_ID = TermId("boundary.synthetic-build1")
DEFAULT_CONTEXT_ID = TermId("context.slice1")


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
    assert tuple(item.source_system_id for item in profile_a.source_systems) == (
        "source-system.file-drop",
        "source-system.lims",
    )
    assert tuple(item.source_class_id for item in profile_a.accepted_source_classes) == (
        "source-class.manual-upload",
        "source-class.test-report",
    )


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
        CapabilityProfile.model_validate(payload)


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
        TermId("source-class.test-report"),
    )
    inactive_profile = profile.model_copy(update={"lifecycle_state": "INACTIVE"})
    inactive = evaluate_capture_profile(
        inactive_profile,
        candidate_scope,
        run_scope,
        TermId("source-class.test-report"),
    )

    assert isinstance(ready, CaptureProfileReady)
    assert ready.status == "READY"
    assert ready.evidence_scope_ref == run_scope.scope_ref
    assert isinstance(inactive, CaptureProfileNotReady)
    assert inactive.reason_id == CAPABILITY_PROFILE_INACTIVE_REASON_ID


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
        TermId("source-class.unknown"),
    )

    assert isinstance(result, CaptureProfileNotReady)
    assert result.scope_result is not None
    assert result.capability_gap is None
    assert result.reason_id == "build1.scope.incompatible"


def test_unknown_source_class_returns_explicit_capability_gap(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    result = evaluate_capture_profile(
        _profile(build1_ref_factory),
        _scope(build1_ref_factory),
        _scope(build1_ref_factory, ref_id="build1.scope.run"),
        TermId("source-class.unknown"),
    )

    assert isinstance(result, CaptureProfileNotReady)
    assert result.scope_result is None
    assert result.capability_gap is not None
    assert result.reason_id == SOURCE_CLASS_UNSUPPORTED_REASON_ID


@pytest.mark.parametrize("field", ("owner_ref", "authority_policy_ref"))
def test_owner_and_authority_policy_are_required_before_capture_selection(
    build1_ref_factory: Callable[[str], GovernedRef],
    field: str,
) -> None:
    payload = _profile_payload(build1_ref_factory)
    payload.pop(field)

    with pytest.raises(ValidationError, match=field):
        CapabilityProfile.model_validate(payload)


def test_storage_policy_requires_positive_governed_byte_limit(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        SourceStoragePolicy(
            storage_policy_ref=build1_ref_factory("build1.storage.invalid"),
            lifecycle_state="ACTIVE",
            max_bytes_per_source_record=0,
            allowed_evidence_locator_classes=(TermId("evidence.byte-range"),),
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
        lifecycle_state=lifecycle_state,
        scope_class=scope_class,
        organization_id=organization_id,
        site_id=site_id,
        workspace_id=workspace_id,
        data_boundary_id=data_boundary_id,
        context_id=context_id,
    )


def _profile(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    unordered: bool = False,
) -> CapabilityProfile:
    payload = _profile_payload(build1_ref_factory)
    if not unordered:
        return CapabilityProfile.model_validate(payload)

    payload["source_systems"] = tuple(reversed(payload["source_systems"]))
    payload["accepted_source_classes"] = tuple(reversed(payload["accepted_source_classes"]))
    payload["storage_policies"] = tuple(reversed(payload["storage_policies"]))
    return CapabilityProfile.model_validate(payload)


def _profile_payload(build1_ref_factory: Callable[[str], GovernedRef]) -> dict[str, object]:
    storage_report = build1_ref_factory("build1.storage.report")
    storage_upload = build1_ref_factory("build1.storage.upload")
    return {
        "schema_version": "gptl.build1.capability-profile.v1",
        "profile_ref": build1_ref_factory("build1.capability.profile"),
        "lifecycle_state": "ACTIVE",
        "owner_ref": build1_ref_factory("build1.owner.materials"),
        "authority_policy_ref": build1_ref_factory("build1.authority.policy"),
        "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
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
        "storage_policies": (
            {
                "storage_policy_ref": storage_report,
                "lifecycle_state": "ACTIVE",
                "max_bytes_per_source_record": 1024,
                "allowed_evidence_locator_classes": (
                    "evidence.cell-range",
                    "evidence.byte-range",
                ),
            },
            {
                "storage_policy_ref": storage_upload,
                "lifecycle_state": "ACTIVE",
                "max_bytes_per_source_record": 2048,
                "allowed_evidence_locator_classes": (
                    "evidence.byte-range",
                    "evidence.page-region",
                ),
            },
        ),
    }
