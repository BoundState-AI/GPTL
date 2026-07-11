"""
Module: Slice 1 Fixtures
Purpose: Fixed synthetic Slice 1 records used by the demo and acceptance tests.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False
"""

import hashlib

from gptl.core.directives import (
    DisplayDirective,
    DisplayTemplate,
    DisplayTemplateRegistry,
)
from gptl.core.pack_registry import ExactPackRegistry
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    LogicalId,
    TemplateId,
    TermId,
    VersionId,
)
from gptl.mie.service import SafeRefusalPolicy, SafeRefusalRequest


def _fixture_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def canonicalization_policy() -> CanonicalizationPolicy:
    return CanonicalizationPolicy(
        policy_id="canonical-policy.slice1",
        policy_version="1",
        timestamp_fraction_digits=3,
        decimal_scale=4,
        decimal_rounding="ROUND_HALF_EVEN",
        decimal_max_integer_digits=18,
        decimal_overflow="REJECT",
    )


def display_registry() -> DisplayTemplateRegistry:
    return DisplayTemplateRegistry(
        registry_ref=GovernedRef(
            logical_id=LogicalId("display-registry.slice1"),
            version_id=VersionId("display-registry.slice1.v1"),
            version_number=1,
            content_hash=_fixture_hash("fixture:display-registry.slice1:v1"),
        ),
        templates=(
            DisplayTemplate(
                template_id=TemplateId("action.provide-published-pack-version"),
                template_ref=GovernedRef(
                    logical_id=LogicalId("template.provide-published-pack-version"),
                    version_id=VersionId("template.provide-published-pack-version.v1"),
                    version_number=1,
                    content_hash=_fixture_hash(
                        "fixture:template.provide-published-pack-version:v1"
                    ),
                ),
                parameter_specs=(),
            ),
        ),
    )


def safe_refusal_policy() -> SafeRefusalPolicy:
    registry = display_registry()
    return SafeRefusalPolicy(
        canonicalization_policy=canonicalization_policy(),
        operational_mode="RESEARCH_ONLY",
        engine_id="mie.diagnostic-engine",
        engine_version="slice1.v1",
        failure_stage_id=TermId("preflight.pack-resolution"),
        audit_event_type_id=TermId("audit.preflight-refusal"),
        required_human_action=DisplayDirective(
            template_id=TemplateId("action.provide-published-pack-version"),
            params=(),
        ),
        display_registry=registry,
    )


def safe_refusal_request() -> SafeRefusalRequest:
    policy = canonicalization_policy()
    return SafeRefusalRequest.model_validate(
        {
            "run_id": "run.slice1.safe-refusal",
            "decision_id": "decision.slice1.safe-refusal",
            "case_id": "case.slice1.safe-refusal",
            "audit_event_id": "audit.slice1.safe-refusal.0",
            "requested_pack_id": "pack.absent.v1",
            "as_of_time": "2026-06-21T12:00:00.000Z",
        },
        context={"canonicalization_policy": policy},
    )


def empty_pack_registry() -> ExactPackRegistry:
    return ExactPackRegistry(available_pack_ids=())
