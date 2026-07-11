"""
Module: Slice 7 Fixtures
Purpose: Governed synthetic Slice 7 replay and evolution fixtures.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False
"""

from __future__ import annotations

from decimal import Decimal

from gptl.core.canonical import canonical_sha256
from gptl.core.ratification import IntakeRecord, IntakeValue
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import EvidenceLocator, TermId
from gptl.mie.predicates import NumericValue
from gptl.mie.replay import (
    ArtifactConfirmationReplayRecipe,
    CandidatePreservationReplayRecipe,
    HonestNegativeReplayRecipe,
    MSAGateReplayRecipe,
    PackLifecycleCatalog,
    PackLifecycleEvent,
    PackLifecyclePolicy,
    ReplayPolicy,
    ReplayRecipe,
    SafeRefusalReplayRecipe,
    Tier2AdvisoryReplayRecipe,
)
from gptl.slice1_fixture import (
    empty_pack_registry,
    safe_refusal_policy,
    safe_refusal_request,
)
from gptl.slice2_fixture import (
    ORIGINAL_AS_OF,
    UNIT_CELSIUS,
    canonicalization_policy,
    governed_ref,
    ratified_runtime,
    slice2_policy,
    slice2_request,
)
from gptl.slice3_fixture import slice3_policy, slice3_request, slice3_runtime
from gptl.slice4_fixture import AS_OF, slice4_policy, slice4_request, slice4_runtime
from gptl.slice5_fixture import slice5_policy, slice5_request, slice5_runtime
from gptl.slice6_fixture import slice6_policy, slice6_query, slice6_request, slice6_runtime

PACK_V1 = governed_ref("pack.lifecycle-reference", 1)
PACK_V2 = governed_ref("pack.lifecycle-reference", 2)
PACK_V2_PUBLISHED_AT = "2026-06-21T09:00:00.000Z"
PACK_V1_DEPRECATED_AT = "2026-06-22T09:00:00.000Z"
PACK_V1_REVOKED_AT = "2026-06-23T09:00:00.000Z"
PACK_ROLLBACK_AS_OF = "2026-06-21T12:00:00.000Z"


def replay_policy() -> ReplayPolicy:
    return ReplayPolicy(
        policy_ref=governed_ref("policy.replay.slice7"),
        record_type_id=TermId("record.replay-policy"),
        evidence_location=EvidenceLocator("fixture:replay-policy"),
        algorithm_id="BUILD0_EXACT_REPLAY_V1",
        recipe_schema_version="gptl.replay-recipe.v1",
        canonicalization_policy=canonicalization_policy(),
        run_missing_reason_id=TermId("replay.run-missing"),
        capsule_missing_reason_id=TermId("replay.capsule-missing"),
        stored_content_invalid_reason_id=TermId("replay.stored-content-invalid"),
        recipe_invalid_reason_id=TermId("replay.recipe-invalid"),
        algorithm_unavailable_reason_id=TermId("replay.algorithm-unavailable"),
        replay_mismatch_reason_id=TermId("replay.reexecution-mismatch"),
        evidence_refs=(governed_ref("evidence.replay-policy.slice7"),),
    )


def replay_recipes() -> tuple[ReplayRecipe, ...]:
    return (
        SafeRefusalReplayRecipe(
            recipe_kind="SAFE_REFUSAL",
            request=safe_refusal_request(),
            pack_registry=empty_pack_registry(),
            policy=safe_refusal_policy(),
        ),
        CandidatePreservationReplayRecipe(
            recipe_kind="CANDIDATE_PRESERVATION",
            request=slice2_request("slice7-replay", ORIGINAL_AS_OF),
            runtime=ratified_runtime(),
            policy=slice2_policy(),
        ),
        MSAGateReplayRecipe(
            recipe_kind="MSA_GATE",
            request=slice3_request("slice7-replay"),
            runtime=slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True),
            policy=slice3_policy(),
        ),
        ArtifactConfirmationReplayRecipe(
            recipe_kind="ARTIFACT_CONFIRMATION",
            request=slice4_request("slice7-replay", AS_OF),
            runtime=slice4_runtime("STRUCTURED", "NONE", True, "NONE"),
            policy=slice4_policy(),
        ),
        HonestNegativeReplayRecipe(
            recipe_kind="HONEST_NEGATIVE",
            request=slice5_request("slice7-replay"),
            runtime=slice5_runtime("COMPLETE"),
            policy=slice5_policy(),
        ),
        Tier2AdvisoryReplayRecipe(
            recipe_kind="TIER2_ADVISORY",
            request=slice6_request("slice7-replay"),
            query=slice6_query("MISSING_MSA"),
            runtime=slice6_runtime("MISSING_MSA"),
            policy=slice6_policy(),
        ),
    )


def corrected_candidate_recipe() -> CandidatePreservationReplayRecipe:
    runtime = ratified_runtime()
    intake = runtime.intake
    corrected_values = tuple(
        _correct_temperature(item) if item.field_id == "field.temperature" else item
        for item in intake.values
    )
    corrected_intake = IntakeRecord(
        intake_ref=governed_ref(intake.intake_ref.logical_id, 2),
        values=corrected_values,
    )
    corrected_runtime = runtime.model_copy(update={"intake": corrected_intake})
    return CandidatePreservationReplayRecipe(
        recipe_kind="CANDIDATE_PRESERVATION",
        request=slice2_request("slice7-corrected", ORIGINAL_AS_OF),
        runtime=corrected_runtime,
        policy=slice2_policy(),
    )


def pack_lifecycle_catalog() -> PackLifecycleCatalog:
    policy = canonicalization_policy()
    events = (
        _lifecycle_event(
            governed_ref("pack-lifecycle.reference-v1", 1),
            PACK_V1,
            "PUBLISHED",
            "2026-06-19T09:00:00.000Z",
            None,
        ),
        _lifecycle_event(
            governed_ref("pack-lifecycle.reference-v1", 2),
            PACK_V1,
            "DEPRECATED",
            PACK_V1_DEPRECATED_AT,
            "pack-lifecycle.reference-v1.v1",
        ),
        _lifecycle_event(
            governed_ref("pack-lifecycle.reference-v1", 3),
            PACK_V1,
            "REVOKED",
            PACK_V1_REVOKED_AT,
            "pack-lifecycle.reference-v1.v2",
        ),
        _lifecycle_event(
            governed_ref("pack-lifecycle.reference-v2", 1),
            PACK_V2,
            "PUBLISHED",
            PACK_V2_PUBLISHED_AT,
            None,
        ),
    )
    return PackLifecycleCatalog.model_validate(
        {
            "catalog_ref": governed_ref("catalog.pack-lifecycle.slice7"),
            "record_type_id": "record.pack-lifecycle-catalog",
            "evidence_location": "fixture:pack-lifecycle-catalog",
            "pack_refs": (PACK_V1, PACK_V2),
            "events": events,
            "evidence_refs": (governed_ref("evidence.pack-lifecycle-catalog.slice7"),),
        },
        context={"canonicalization_policy": policy},
    )


def pack_lifecycle_policy() -> PackLifecyclePolicy:
    return PackLifecyclePolicy(
        policy_ref=governed_ref("policy.pack-lifecycle.slice7"),
        record_type_id=TermId("record.pack-lifecycle-policy"),
        evidence_location=EvidenceLocator("fixture:pack-lifecycle-policy"),
        eligible_reason_id=TermId("pack.lifecycle-published"),
        unavailable_reason_id=TermId("pack.version-unavailable"),
        deprecated_reason_id=TermId("pack.lifecycle-deprecated"),
        revoked_reason_id=TermId("pack.lifecycle-revoked"),
        evidence_refs=(governed_ref("evidence.pack-lifecycle-policy.slice7"),),
    )


def _correct_temperature(value: IntakeValue) -> IntakeValue:
    corrected = NumericValue(
        kind="NUMERIC",
        value=Decimal("26"),
        unit_id=UNIT_CELSIUS,
    )
    value_hash = canonical_sha256(
        {"field_id": value.field_id, "value": corrected},
        canonicalization_policy(),
    )
    return value.model_copy(update={"value": corrected, "value_hash": value_hash})


def _lifecycle_event(
    event_ref: GovernedRef,
    pack_ref: GovernedRef,
    state: str,
    event_time: str,
    supersedes_version_id: str | None,
) -> PackLifecycleEvent:
    return PackLifecycleEvent.model_validate(
        {
            "event_ref": event_ref,
            "record_type_id": "record.pack-lifecycle-event",
            "evidence_location": "fixture:pack-lifecycle-event",
            "pack_ref": pack_ref,
            "state": state,
            "effective_at": event_time,
            "recorded_at": event_time,
            "supersedes_version_id": supersedes_version_id,
            "actor_id": "actor.pack-release-authority",
            "evidence_refs": (
                governed_ref(f"evidence.{event_ref.logical_id}.v{event_ref.version_number}"),
            ),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
