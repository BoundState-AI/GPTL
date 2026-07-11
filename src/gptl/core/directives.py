"""
Module: Display Directives
Purpose: Governed display directives; authoritative payloads contain no prose.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: True
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import CanonicalDecimal, TemplateId, TermId, UnitId


class GovernedDisplayValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["GOVERNED_REF"]
    value: GovernedRef


class TermDisplayValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["TERM_REF"]
    value: TermId


class DecimalDisplayValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["DECIMAL"]
    value: CanonicalDecimal
    unit_id: UnitId | None


DisplayValue = Annotated[
    GovernedDisplayValue | TermDisplayValue | DecimalDisplayValue,
    Field(discriminator="kind"),
]


class DisplayParam(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    key_id: TermId
    value: DisplayValue


class DisplayDirective(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    template_id: TemplateId
    params: tuple[DisplayParam, ...]

    @model_validator(mode="after")
    def validate_param_order(self) -> DisplayDirective:
        keys = tuple(param.key_id for param in self.params)
        if len(keys) != len(set(keys)):
            raise ValueError("display parameter keys must be unique")
        if keys != tuple(sorted(keys)):
            raise ValueError("display parameters must be sorted by key_id")
        return self


DisplayValueKind = Literal["GOVERNED_REF", "TERM_REF", "DECIMAL"]


class DisplayParameterSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    key_id: TermId
    value_kind: DisplayValueKind
    required: bool


class DisplayTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    template_id: TemplateId
    template_ref: GovernedRef
    parameter_specs: tuple[DisplayParameterSpec, ...]

    @model_validator(mode="after")
    def validate_spec_order(self) -> DisplayTemplate:
        keys = tuple(spec.key_id for spec in self.parameter_specs)
        if len(keys) != len(set(keys)):
            raise ValueError("template parameter keys must be unique")
        if keys != tuple(sorted(keys)):
            raise ValueError("template parameter specs must be sorted by key_id")
        return self


class DisplayTemplateRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    registry_ref: GovernedRef
    templates: tuple[DisplayTemplate, ...]

    @model_validator(mode="after")
    def validate_template_order(self) -> DisplayTemplateRegistry:
        ids = tuple(template.template_id for template in self.templates)
        if len(ids) != len(set(ids)):
            raise ValueError("template IDs must be unique")
        if ids != tuple(sorted(ids)):
            raise ValueError("templates must be sorted by template_id")
        return self

    def validate_directive(self, directive: DisplayDirective) -> None:
        template = next(
            (
                candidate
                for candidate in self.templates
                if candidate.template_id == directive.template_id
            ),
            None,
        )
        if template is None:
            raise ValueError("display directive references an unknown template")

        supplied = {param.key_id: param.value.kind for param in directive.params}
        allowed = {spec.key_id: spec for spec in template.parameter_specs}
        unknown = set(supplied) - set(allowed)
        if unknown:
            raise ValueError("display directive contains an unknown parameter")
        missing = {key for key, spec in allowed.items() if spec.required and key not in supplied}
        if missing:
            raise ValueError("display directive omits a required parameter")
        if any(supplied[key] != allowed[key].value_kind for key in supplied):
            raise ValueError("display directive parameter has the wrong value kind")
