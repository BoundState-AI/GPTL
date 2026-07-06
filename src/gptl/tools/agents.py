"""Build 2 tool capture agents: the model boundary, wrapped fail-closed.

A ``ToolCaptureAgent`` is a governed actor bound to one or more analytical tools and an
analysis backend. The backend (a vision model for the visual family, a spectrum model
or deterministic parser for the spectral family) is a pluggable ``Protocol``: this
module never imports a model provider. Whatever the backend does — return findings,
declare itself unavailable, violate its contract, or throw — the agent converts the
outcome into a typed capture result. Findings that survive validation become
MODEL_ASSISTED proposals and UNVALIDATED observations via ``assemble_tool_capture``;
they still face the Slice 3 validator and the Slice 4 human ratification gate, which
bars this same agent actor from ratifying its own capture.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Final, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import CanonicalizationPolicy, TermId
from gptl.tools.capture import (
    ToolAgentIdentity,
    ToolAnalysisFindings,
    ToolAnalysisOutcome,
    ToolAnalysisUnavailable,
    ToolCaptureRefused,
    ToolCaptureRequest,
    ToolCaptureResult,
    assemble_tool_capture,
)
from gptl.tools.taxonomy import (
    AnalyticalToolDefinition,
    AnalyticalToolRegistry,
    ToolModality,
    ToolResolved,
)

CAPTURE_TOOL_NOT_ASSIGNED_REASON_ID: Final = TermId("build2.capture.tool-not-assigned")
CAPTURE_SOURCE_TAMPERED_REASON_ID: Final = TermId("build2.capture.source-tampered")
CAPTURE_BACKEND_UNAVAILABLE_REASON_ID: Final = TermId("build2.capture.backend-unavailable")
CAPTURE_BACKEND_FAILED_REASON_ID: Final = TermId("build2.capture.backend-failed")
CAPTURE_BACKEND_CONTRACT_VIOLATION_REASON_ID: Final = TermId(
    "build2.capture.backend-contract-violation"
)


class ToolAnalysisTask(BaseModel):
    """What a backend is given: the governed tool definition and the raw artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: AnalyticalToolDefinition
    source_artifact_ref: GovernedRef
    source_class_id: TermId
    source_bytes: bytes


@runtime_checkable
class ToolAnalysisBackend(Protocol):
    """The analysis seam. Implementations may be models, parsers, or transcription UIs.

    The contract is closed: return ``ToolAnalysisFindings`` or
    ``ToolAnalysisUnavailable``. There is no field anywhere in those models for a
    score, weight, or model self-assessment — a backend that wants one cannot express
    it, and a backend that raises is converted to a typed fail-closed refusal.
    """

    def analyze(self, task: ToolAnalysisTask) -> ToolAnalysisOutcome: ...


class ToolCaptureAgent:
    """One governed capture agent serving a fixed set of tools with one backend."""

    def __init__(
        self,
        identity: ToolAgentIdentity,
        registry: AnalyticalToolRegistry,
        tool_type_ids: tuple[TermId, ...],
        modality: ToolModality,
        backend: ToolAnalysisBackend,
    ) -> None:
        if not tool_type_ids:
            raise ValueError("capture agent requires at least one assigned tool")
        for tool_type_id in tool_type_ids:
            resolution = registry.resolve(tool_type_id)
            if not isinstance(resolution, ToolResolved):
                raise ValueError(f"capture agent assigned an unresolvable tool: {tool_type_id}")
            tool = resolution.tool
            if tool.modality != modality:
                raise ValueError(f"capture agent modality does not match tool: {tool_type_id}")
            if tool.agent_role_id != identity.role_id:
                raise ValueError(f"capture agent role does not match tool: {tool_type_id}")
        self.identity = identity
        self.registry = registry
        self.tool_type_ids = tuple(sorted(set(tool_type_ids)))
        self.modality: ToolModality = modality
        self.backend = backend

    def capture(
        self,
        request: ToolCaptureRequest,
        ref_factory: Callable[[str], GovernedRef],
        canonicalization_policy: CanonicalizationPolicy,
    ) -> ToolCaptureResult:
        if request.tool_type_id not in self.tool_type_ids:
            return self._refused(request, CAPTURE_TOOL_NOT_ASSIGNED_REASON_ID)

        resolution = self.registry.resolve(request.tool_type_id)
        if not isinstance(resolution, ToolResolved):
            return self._refused(request, resolution.reason_id)
        tool = resolution.tool

        if hashlib.sha256(request.source_bytes).hexdigest() != request.source_raw_byte_hash:
            return self._refused(request, CAPTURE_SOURCE_TAMPERED_REASON_ID)

        try:
            outcome = self.backend.analyze(
                ToolAnalysisTask(
                    tool=tool,
                    source_artifact_ref=request.source_artifact_ref,
                    source_class_id=request.source_class_id,
                    source_bytes=request.source_bytes,
                )
            )
        except Exception:
            # The model/parser boundary: any backend fault becomes a typed refusal,
            # never an exception escaping the governed capture path.
            return self._refused(request, CAPTURE_BACKEND_FAILED_REASON_ID)

        if isinstance(outcome, ToolAnalysisUnavailable):
            return self._refused(request, CAPTURE_BACKEND_UNAVAILABLE_REASON_ID)
        if not isinstance(outcome, ToolAnalysisFindings):
            return self._refused(request, CAPTURE_BACKEND_CONTRACT_VIOLATION_REASON_ID)

        return assemble_tool_capture(
            tool,
            self.identity,
            request,
            outcome,
            ref_factory,
            canonicalization_policy,
        )

    def _refused(self, request: ToolCaptureRequest, reason_id: TermId) -> ToolCaptureRefused:
        return ToolCaptureRefused(
            status="CAPTURE_REFUSED",
            reason_id=reason_id,
            tool_type_id=request.tool_type_id,
            source_artifact_ref=request.source_artifact_ref,
        )


def spectral_tool_agents(
    registry: AnalyticalToolRegistry,
    identity: ToolAgentIdentity,
    backend_for_tool: Callable[[AnalyticalToolDefinition], ToolAnalysisBackend],
) -> tuple[ToolCaptureAgent, ...]:
    """One agent per SPECTRAL tool, each with its own (possibly shared) backend."""
    return tuple(
        ToolCaptureAgent(
            identity=identity,
            registry=registry,
            tool_type_ids=(tool.tool_type_id,),
            modality="SPECTRAL",
            backend=backend_for_tool(tool),
        )
        for tool in registry.tools_for_modality("SPECTRAL")
    )


def visual_tool_agent(
    registry: AnalyticalToolRegistry,
    identity: ToolAgentIdentity,
    backend: ToolAnalysisBackend,
) -> ToolCaptureAgent:
    """A single visual agent covering the whole imaging family (optical, SEM, TEM, FIB)."""
    visual_tools = registry.tools_for_modality("VISUAL")
    return ToolCaptureAgent(
        identity=identity,
        registry=registry,
        tool_type_ids=tuple(tool.tool_type_id for tool in visual_tools),
        modality="VISUAL",
        backend=backend,
    )
