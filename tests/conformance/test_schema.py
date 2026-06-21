import pytest
from pydantic import ValidationError

from gptl.core.directives import (
    DecimalDisplayValue,
    DisplayDirective,
    DisplayParam,
    DisplayParameterSpec,
    DisplayTemplate,
    DisplayTemplateRegistry,
    GovernedDisplayValue,
    TermDisplayValue,
)
from gptl.core.records import GovernedRef
from gptl.core.semantic_types import JCS_MAX_SAFE_INTEGER
from gptl.mie.service import SafeRefusalRequest
from gptl.slice1_fixture import canonicalization_policy, display_registry


def _request(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "run_id": "run.schema-test",
        "decision_id": "decision.schema-test",
        "case_id": "case.schema-test",
        "audit_event_id": "audit.schema-test.0",
        "requested_pack_id": "pack.absent.v1",
        "as_of_time": "2026-06-21T12:00:00.000Z",
    }
    values.update(overrides)
    return values


def _context() -> dict[str, object]:
    return {"canonicalization_policy": canonicalization_policy()}


def _registry_with_required_term() -> DisplayTemplateRegistry:
    registry = display_registry()
    original = registry.templates[0]
    template = DisplayTemplate(
        template_id=original.template_id,
        template_ref=original.template_ref,
        parameter_specs=(
            DisplayParameterSpec(
                key_id="param.required-term",
                value_kind="TERM_REF",
                required=True,
            ),
        ),
    )
    return DisplayTemplateRegistry(
        registry_ref=registry.registry_ref,
        templates=(template,),
    )


@pytest.mark.parametrize(
    "field,value",
    (("run_id", "bad id"), ("requested_pack_id", ""), ("audit_event_id", "?bad")),
)
def test_malformed_identifiers_are_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        SafeRefusalRequest.model_validate(_request(**{field: value}), context=_context())


@pytest.mark.parametrize(
    "timestamp",
    (
        "2026-06-21T12:00:00Z",
        "2026-06-21T12:00:00.00Z",
        "2026-02-30T12:00:00.000Z",
        "2026-06-21T25:00:00.000Z",
        "2026-06-21T12:00:00.000+00:00",
    ),
)
def test_noncanonical_timestamps_are_rejected(timestamp: str) -> None:
    with pytest.raises(ValidationError):
        SafeRefusalRequest.model_validate(_request(as_of_time=timestamp), context=_context())


def test_timestamp_policy_context_is_mandatory() -> None:
    with pytest.raises(ValidationError, match="canonicalization policy"):
        SafeRefusalRequest.model_validate(_request())


def test_unknown_display_template_is_rejected() -> None:
    directive = DisplayDirective(template_id="action.unknown", params=())
    with pytest.raises(ValueError, match="unknown template"):
        display_registry().validate_directive(directive)


def test_unknown_display_parameter_is_rejected() -> None:
    directive = DisplayDirective(
        template_id="action.provide-published-pack-version",
        params=(
            DisplayParam(
                key_id="param.unexpected",
                value=TermDisplayValue(kind="TERM_REF", value="term.value"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="unknown parameter"):
        display_registry().validate_directive(directive)


def test_required_display_parameter_cannot_be_omitted() -> None:
    registry = _registry_with_required_term()
    directive = DisplayDirective(
        template_id="action.provide-published-pack-version",
        params=(),
    )
    with pytest.raises(ValueError, match="required parameter"):
        registry.validate_directive(directive)


def test_display_parameter_kind_must_match_registered_kind() -> None:
    registry = _registry_with_required_term()
    directive = DisplayDirective(
        template_id="action.provide-published-pack-version",
        params=(
            DisplayParam(
                key_id="param.required-term",
                value=GovernedDisplayValue(
                    kind="GOVERNED_REF",
                    value=registry.registry_ref,
                ),
            ),
        ),
    )
    with pytest.raises(ValueError, match="wrong value kind"):
        registry.validate_directive(directive)


def test_malformed_hash_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GovernedRef(
            logical_id="record.test",
            version_id="record.test.v1",
            version_number=1,
            content_hash="not-a-sha256",
        )


def test_float_cannot_enter_a_decimal_field_by_coercion() -> None:
    with pytest.raises(ValidationError):
        DecimalDisplayValue(kind="DECIMAL", value=0.1, unit_id=None)


@pytest.mark.parametrize("version_number", (True, JCS_MAX_SAFE_INTEGER + 1))
def test_record_versions_are_strict_jcs_safe_integers(version_number: object) -> None:
    with pytest.raises(ValidationError):
        GovernedRef(
            logical_id="record.test",
            version_id="record.test.v1",
            version_number=version_number,
            content_hash="0" * 64,
        )
