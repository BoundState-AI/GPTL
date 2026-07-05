from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

import pytest
from pydantic import ValidationError

from gptl.core.observations import (
    ATTRIBUTED_OBSERVATION_RECORD_TYPE,
    ATTRIBUTED_OBSERVATION_SCHEMA_VERSION,
    HASH_ALGORITHM,
    OBSERVATION_PROMOTION_RECORD_TYPE,
    OBSERVATION_PROMOTION_SCHEMA_VERSION,
    OBSERVATION_TIER1_PROHIBITED_REASON_ID,
    AttributedObservation,
    ObservationMetadataEntry,
    ObservationPromotionRecord,
    ObservationVisibilityPolicy,
    build_observation_advisory_context,
    evaluate_observation_tier1_evidence,
    finalize_attributed_observation,
    finalize_observation_promotion,
    observation_replay_hash,
    render_observation_artifact,
)
from gptl.core.proposal_ratification import PROPOSAL_RATIFICATION_RECORD_TYPE
from gptl.core.proposals import TYPED_VALUE_PROPOSAL_RECORD_TYPE
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import LogicalId, TermId, VersionId
from gptl.mie.schema import AdvisoryDecision
from gptl.slice1_fixture import canonicalization_policy

AS_OF = "2026-07-01T12:00:00.000Z"
ADVISORY_HASH = "b" * 64


def test_unvalidated_observation_enters_tier2_context_by_ref_only(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    observation = _observation(build1_ref_factory)
    under_review = _observation(
        build1_ref_factory,
        observation_ref=_ref("build1.observation.under-review", 1),
        validation_state="UNDER_REVIEW",
        claim_text="This should not be surfaced yet.",
    )

    context = build_observation_advisory_context(
        (under_review, observation),
        build1_ref_factory("build1.canonicalization.policy"),
        AS_OF,
        canonicalization_policy(),
    )

    assert len(context.observation_refs) == 1
    assert context.observation_refs[0].tier == 2
    assert context.observation_refs[0].validation_state == "UNVALIDATED"
    assert context.observation_refs[0].attributed is True
    assert context.observation_refs[0].observation_ref == observation.observation_ref
    assert observation.claim_text not in repr(context.model_dump(mode="python"))


def test_observation_prose_renders_outside_structured_advisory_payload(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    observation = _observation(build1_ref_factory)
    context = build_observation_advisory_context(
        (observation,),
        build1_ref_factory("build1.canonicalization.policy"),
        AS_OF,
        canonicalization_policy(),
    )

    artifact = render_observation_artifact(
        context,
        (observation,),
        ADVISORY_HASH,
        "renderer.observation.v1",
        "1.0.0",
    )

    rendered = artifact.observations[0].rendered_text
    assert "attributed" in rendered.lower()
    assert "unvalidated" in rendered.lower()
    assert observation.claim_text in rendered
    assert artifact.generated_from_advisory_hash == ADVISORY_HASH
    assert artifact.non_record_of_record is True
    assert "claim_text" not in AdvisoryDecision.model_fields
    assert "observation_refs" not in AdvisoryDecision.model_fields
    assert "observation_prose" not in AdvisoryDecision.model_fields


def test_observation_text_cannot_satisfy_tier1_evidence(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    observation = _observation(build1_ref_factory)

    result = evaluate_observation_tier1_evidence(observation)

    assert result.status == "PROHIBITED"
    assert result.reason_id == OBSERVATION_TIER1_PROHIBITED_REASON_ID
    assert result.observation_ref == observation.observation_ref
    assert result.tier1_evidence_refs == ()


def test_observation_promotion_requires_governed_basis_and_ratification_next(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    observation = _observation(build1_ref_factory)
    proposal_ref = build1_ref_factory("build1.proposal.from-observation")

    with pytest.raises(ValidationError, match="protocol promotion requires only"):
        _promotion(
            build1_ref_factory,
            observation.observation_ref,
            proposal_ref,
            basis="VALIDATION_PROTOCOL_RESULT",
            validation_protocol_result_ref=None,
        )

    promotion = _promotion(
        build1_ref_factory,
        observation.observation_ref,
        proposal_ref,
        basis="CORROBORATING_GOVERNED_EVIDENCE",
        corroborating_evidence_refs=(build1_ref_factory("build1.evidence.protocol-output"),),
    )

    assert promotion.created_proposal_ref == proposal_ref
    assert promotion.created_proposal_record_type == TYPED_VALUE_PROPOSAL_RECORD_TYPE
    assert promotion.decision_effective is False
    assert promotion.required_next_record_type == PROPOSAL_RATIFICATION_RECORD_TYPE


@pytest.mark.parametrize(
    "metadata_key",
    (
        "operator.confidence",
        "operator.confidence_interval",
        "operator.probability",
        "operator.likelihood",
        "operator.sigma",
        "operator.p_value",
        "operator.pvalue",
        "operator.percentile",
        "operator.stddev",
        "operator.variance",
        "operator.weight",
        "operator.rank",
        "operator.posterior",
        "operator.risk_score",
    ),
)
def test_confidence_metadata_is_rejected(
    build1_ref_factory: Callable[[str], GovernedRef],
    metadata_key: str,
) -> None:
    with pytest.raises(ValidationError, match="confidence or score"):
        _observation(
            build1_ref_factory,
            metadata=(ObservationMetadataEntry(key=metadata_key, value="high"),),
        )


@pytest.mark.parametrize(
    "metadata_key",
    (
        "modelConfidence",
        "operator.modelConfidence",
        "confidenceScore",
        "confidence1",
        "operator.riskScore2",
        "posteriorWeight",
    ),
)
def test_camelcase_and_digit_confidence_metadata_is_rejected(
    build1_ref_factory: Callable[[str], GovernedRef],
    metadata_key: str,
) -> None:
    # NFC-1: the token scan must catch camelCase and digit-adjacent confidence/score keys,
    # not only delimiter-separated forms — OpaqueId admits these shapes.
    with pytest.raises(ValidationError, match="confidence or score"):
        _observation(
            build1_ref_factory,
            metadata=(ObservationMetadataEntry(key=metadata_key, value="high"),),
        )


def test_render_fails_closed_when_context_observation_is_not_supplied(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    # OBS-RENDER-KEYERROR: a render context referencing an observation absent from the
    # supplied set must fail closed with a diagnostic error, not a bare KeyError.
    observation = _observation(build1_ref_factory)
    context = build_observation_advisory_context(
        (observation,),
        build1_ref_factory("build1.canonicalization.policy"),
        AS_OF,
        canonicalization_policy(),
    )

    with pytest.raises(ValueError, match="not supplied"):
        render_observation_artifact(
            context,
            (),
            ADVISORY_HASH,
            "renderer.observation.v1",
            "1.0.0",
        )


def test_observations_are_append_only_and_replay_hash_is_order_independent(
    build1_ref_factory: Callable[[str], GovernedRef],
) -> None:
    original = _observation(build1_ref_factory)
    later = _observation(
        build1_ref_factory,
        observation_ref=_ref("build1.observation.temperature-note", 2),
        claim_text="Second shift reports the same discoloration near the aft edge.",
    )

    forward = observation_replay_hash((original, later), canonicalization_policy())
    reverse = observation_replay_hash((later, original), canonicalization_policy())

    assert original.observation_ref.content_hash != "0" * 64
    assert forward == reverse
    with pytest.raises(ValidationError, match="superseded observation requires"):
        _observation(build1_ref_factory, validation_state="SUPERSEDED")

    superseded = _observation(
        build1_ref_factory,
        observation_ref=_ref("build1.observation.temperature-note", 3),
        validation_state="SUPERSEDED",
        supersedes_observation_ref=original.observation_ref,
    )
    assert superseded.supersedes_observation_ref == original.observation_ref


def test_slice_5_runtime_source_guard(
    runtime_source_guard: Callable[[tuple[Path, ...]], None],
) -> None:
    repository_root = Path(__file__).parents[2]

    runtime_source_guard(
        (repository_root / "src" / "gptl" / "core" / "observations.py",)
    )


def _observation(
    build1_ref_factory: Callable[[str], GovernedRef],
    *,
    observation_ref: GovernedRef | None = None,
    claim_text: str = "Second shift reports blue discoloration after the bake cycle.",
    validation_state: Literal[
        "UNVALIDATED",
        "UNDER_REVIEW",
        "PROMOTED_BY_PROTOCOL",
        "REJECTED",
        "SUPERSEDED",
    ] = "UNVALIDATED",
    metadata: tuple[ObservationMetadataEntry, ...] = (),
    supersedes_observation_ref: GovernedRef | None = None,
) -> AttributedObservation:
    observation = AttributedObservation.model_validate(
        {
            "schema_version": ATTRIBUTED_OBSERVATION_SCHEMA_VERSION,
            "record_type": ATTRIBUTED_OBSERVATION_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "observation_ref": observation_ref or _ref("build1.observation.temperature-note", 1),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "claim_text": claim_text,
            "source_display_name": "Second shift technician",
            "source_role_id": TermId("role.production-technician"),
            "recorded_actor_ref": build1_ref_factory("build1.actor.observer"),
            "recorded_at": AS_OF,
            "production_context_ref": build1_ref_factory("build1.context.work-order-1"),
            "validation_state": validation_state,
            "evidence_scope_ref": build1_ref_factory("build1.scope.candidate"),
            "source_artifact_ref": build1_ref_factory("build1.source.shift-note"),
            "metadata": metadata,
            "visibility_policy": _visibility_policy(),
            "evidence_refs": (build1_ref_factory("build1.evidence.shift-note"),),
            "supersedes_observation_ref": supersedes_observation_ref,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return finalize_attributed_observation(observation, canonicalization_policy())


def _visibility_policy() -> ObservationVisibilityPolicy:
    return ObservationVisibilityPolicy(
        tier=2,
        advisory_context_allowed=True,
        rendered_artifact_allowed=True,
        structured_advisory_payload_allowed=False,
        tier1_evidence_allowed=False,
    )


def _promotion(
    build1_ref_factory: Callable[[str], GovernedRef],
    observation_ref: GovernedRef,
    proposal_ref: GovernedRef,
    *,
    basis: Literal["VALIDATION_PROTOCOL_RESULT", "CORROBORATING_GOVERNED_EVIDENCE"],
    validation_protocol_result_ref: GovernedRef | None = None,
    corroborating_evidence_refs: tuple[GovernedRef, ...] = (),
) -> ObservationPromotionRecord:
    promotion = ObservationPromotionRecord.model_validate(
        {
            "schema_version": OBSERVATION_PROMOTION_SCHEMA_VERSION,
            "record_type": OBSERVATION_PROMOTION_RECORD_TYPE,
            "hash_algorithm": HASH_ALGORITHM,
            "promotion_ref": _ref("build1.observation-promotion.temperature-note", 1),
            "canonicalization_policy_ref": build1_ref_factory("build1.canonicalization.policy"),
            "observation_ref": observation_ref,
            "created_proposal_record_type": TYPED_VALUE_PROPOSAL_RECORD_TYPE,
            "created_proposal_ref": proposal_ref,
            "promotion_basis": basis,
            "validation_protocol_result_ref": validation_protocol_result_ref,
            "corroborating_evidence_refs": corroborating_evidence_refs,
            "decision_effective": False,
            "required_next_record_type": PROPOSAL_RATIFICATION_RECORD_TYPE,
            "evidence_refs": (build1_ref_factory("build1.evidence.promotion-review"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    return finalize_observation_promotion(promotion, canonicalization_policy())


def _ref(logical_id: str, version_number: int) -> GovernedRef:
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v{version_number}"),
        version_number=version_number,
        content_hash="0" * 64,
    )
