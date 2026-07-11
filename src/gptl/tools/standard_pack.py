"""
Module: Standard Analytical Tool Pack
Purpose: Standard analytical tool pack: governed definitions for the common lab techniques.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False

Two modalities, per the platform taxonomy:

* SPECTRAL — signal/spectrum artifacts: XRD, XRF, FTIR, Raman, OES, ICP-OES, ICP-MS,
  GC-MS, EDS, DSC, TGA.
* VISUAL — image artifacts: optical metallography, SEM, TEM, FIB cross-sections.

These are fixture *records*, not engine behavior: measurement classes, observation
classes, emitted source classes, and required calibration/MSA labels are governed
vocabulary a program can supersede. Numeric acceptance criteria never live here — they
belong to designed validation protocols (Slice 6) authored per program.
"""

from __future__ import annotations

import hashlib
from typing import Final

from gptl.core.records import GovernedRef
from gptl.core.semantic_types import (
    CanonicalizationPolicy,
    LogicalId,
    TermId,
    VersionId,
)
from gptl.tools.taxonomy import (
    ANALYTICAL_TOOL_RECORD_TYPE,
    ANALYTICAL_TOOL_SCHEMA_VERSION,
    HASH_ALGORITHM,
    AnalyticalToolDefinition,
    AnalyticalToolRegistry,
    ProposalMethodId,
    ToolModality,
    finalize_analytical_tool_definition,
)

# ── governed vocabulary (fixture terms; programs may supersede) ────────────────────────
ROLE_SPECTRAL_CAPTURE_AGENT: Final = TermId("role.spectral-capture-agent")
ROLE_VISUAL_CAPTURE_AGENT: Final = TermId("role.visual-capture-agent")

CAL_RECORDS_PRESENT: Final = TermId("capability-label.calibration-records-present")
CAL_REFERENCE_MATERIAL: Final = TermId(
    "capability-label.reference-material-verification-present"
)
CAL_MAGNIFICATION: Final = TermId("capability-label.magnification-calibration-present")
CAL_MS_TUNE: Final = TermId("capability-label.mass-spectrometer-tune-present")
CAL_INTERNAL_STANDARD: Final = TermId("capability-label.internal-standard-program-present")

OBS_MICROSTRUCTURE: Final = TermId("observation-class.microstructure-morphology")
OBS_FRACTOGRAPHY: Final = TermId("observation-class.fractography-features")
OBS_SURFACE_CONDITION: Final = TermId("observation-class.surface-condition")
OBS_DEFECT_ANOMALY: Final = TermId("observation-class.defect-anomaly")
OBS_SIGNAL_ANOMALY: Final = TermId("observation-class.signal-anomaly")

SPECTRAL_METHODS: Final[tuple[ProposalMethodId, ...]] = (
    "DETERMINISTIC_PARSER",
    "MANUAL_TRANSLATION",
    "MODEL_ASSISTED",
)
VISUAL_METHODS: Final[tuple[ProposalMethodId, ...]] = (
    "MANUAL_TRANSLATION",
    "MODEL_ASSISTED",
)

_STANDARD_TOOLS: Final[tuple[dict[str, object], ...]] = (
    # ── SPECTRAL ──
    {
        "tool_type_id": "tool.xrd",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.x-ray-diffraction",
        "measurement_class_ids": (
            "measurement.phase-fraction",
            "measurement.lattice-parameter",
            "measurement.crystallite-size",
            "measurement.residual-stress",
        ),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.xrd-pattern",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_REFERENCE_MATERIAL),
    },
    {
        "tool_type_id": "tool.xrf",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.x-ray-fluorescence",
        "measurement_class_ids": ("measurement.elemental-composition",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.xrf-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_REFERENCE_MATERIAL),
    },
    {
        "tool_type_id": "tool.ftir",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.ftir-spectroscopy",
        "measurement_class_ids": ("measurement.functional-group-identification",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.ir-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT,),
    },
    {
        "tool_type_id": "tool.raman",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.raman-spectroscopy",
        "measurement_class_ids": ("measurement.functional-group-identification",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.raman-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT,),
    },
    {
        "tool_type_id": "tool.oes",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.optical-emission-spectroscopy",
        "measurement_class_ids": ("measurement.elemental-composition",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.oes-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_REFERENCE_MATERIAL),
    },
    {
        "tool_type_id": "tool.icp-oes",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.icp-optical-emission",
        "measurement_class_ids": ("measurement.elemental-composition",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.icp-oes-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_INTERNAL_STANDARD),
    },
    {
        "tool_type_id": "tool.icp-ms",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.icp-mass-spectrometry",
        "measurement_class_ids": ("measurement.trace-elemental-composition",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.icp-mass-spectrum",),
        "required_calibration_label_ids": (
            CAL_RECORDS_PRESENT,
            CAL_INTERNAL_STANDARD,
            CAL_MS_TUNE,
        ),
    },
    {
        "tool_type_id": "tool.gc-ms",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.gc-mass-spectrometry",
        "measurement_class_ids": (
            "measurement.organic-species-identification",
            "measurement.outgassing-mass-fraction",
        ),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.gc-chromatogram-mass-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_MS_TUNE),
    },
    {
        "tool_type_id": "tool.eds",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.energy-dispersive-spectroscopy",
        "measurement_class_ids": ("measurement.elemental-composition",),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.eds-spectrum",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT,),
    },
    {
        "tool_type_id": "tool.dsc",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.differential-scanning-calorimetry",
        "measurement_class_ids": (
            "measurement.phase-transition-temperature",
            "measurement.transition-enthalpy",
        ),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.dsc-thermogram",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_REFERENCE_MATERIAL),
    },
    {
        "tool_type_id": "tool.tga",
        "modality": "SPECTRAL",
        "display_label_id": "display.tool.thermogravimetric-analysis",
        "measurement_class_ids": (
            "measurement.mass-loss-fraction",
            "measurement.decomposition-temperature",
        ),
        "observation_class_ids": (OBS_SIGNAL_ANOMALY,),
        "emitted_source_class_ids": ("source-class.tga-thermogram",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT,),
    },
    # ── VISUAL ──
    {
        "tool_type_id": "tool.optical-microscopy",
        "modality": "VISUAL",
        "display_label_id": "display.tool.optical-metallography",
        "measurement_class_ids": (
            "measurement.grain-size",
            "measurement.porosity-area-fraction",
            "measurement.phase-area-fraction",
            "measurement.coating-thickness",
            "measurement.inclusion-rating",
        ),
        "observation_class_ids": (
            OBS_MICROSTRUCTURE,
            OBS_SURFACE_CONDITION,
            OBS_DEFECT_ANOMALY,
        ),
        "emitted_source_class_ids": ("source-class.optical-micrograph",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_MAGNIFICATION),
    },
    {
        "tool_type_id": "tool.sem",
        "modality": "VISUAL",
        "display_label_id": "display.tool.scanning-electron-microscopy",
        "measurement_class_ids": (
            "measurement.grain-size",
            "measurement.porosity-area-fraction",
            "measurement.coating-thickness",
            "measurement.particle-size",
        ),
        "observation_class_ids": (
            OBS_MICROSTRUCTURE,
            OBS_FRACTOGRAPHY,
            OBS_SURFACE_CONDITION,
            OBS_DEFECT_ANOMALY,
        ),
        "emitted_source_class_ids": ("source-class.sem-micrograph",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_MAGNIFICATION),
    },
    {
        "tool_type_id": "tool.tem",
        "modality": "VISUAL",
        "display_label_id": "display.tool.transmission-electron-microscopy",
        "measurement_class_ids": (
            "measurement.precipitate-size",
            "measurement.dislocation-density",
        ),
        "observation_class_ids": (OBS_MICROSTRUCTURE, OBS_DEFECT_ANOMALY),
        "emitted_source_class_ids": ("source-class.tem-micrograph",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_MAGNIFICATION),
    },
    {
        "tool_type_id": "tool.fib",
        "modality": "VISUAL",
        "display_label_id": "display.tool.focused-ion-beam-cross-section",
        "measurement_class_ids": ("measurement.layer-thickness",),
        "observation_class_ids": (OBS_MICROSTRUCTURE, OBS_DEFECT_ANOMALY),
        "emitted_source_class_ids": ("source-class.fib-cross-section-image",),
        "required_calibration_label_ids": (CAL_RECORDS_PRESENT, CAL_MAGNIFICATION),
    },
)


def _fixture_ref(logical_id: str) -> GovernedRef:
    return GovernedRef(
        logical_id=LogicalId(logical_id),
        version_id=VersionId(f"{logical_id}.v1"),
        version_number=1,
        content_hash=hashlib.sha256(f"fixture:{logical_id}:v1".encode()).hexdigest(),
    )


def standard_tool_definitions(
    canonicalization_policy: CanonicalizationPolicy,
) -> tuple[AnalyticalToolDefinition, ...]:
    """Build every standard tool definition with real governed content hashes."""
    policy_ref = _fixture_ref("build2.canonicalization.policy")
    evidence_ref = _fixture_ref("build2.evidence.standard-tool-pack")
    definitions = []
    for entry in _STANDARD_TOOLS:
        modality = entry["modality"]
        if modality not in ("SPECTRAL", "VISUAL"):
            raise ValueError("standard tool entry declares an unknown modality")
        tool = AnalyticalToolDefinition.model_validate(
            {
                "schema_version": ANALYTICAL_TOOL_SCHEMA_VERSION,
                "record_type": ANALYTICAL_TOOL_RECORD_TYPE,
                "hash_algorithm": HASH_ALGORITHM,
                "tool_ref": _fixture_ref(f"build2.{entry['tool_type_id']}"),
                "canonicalization_policy_ref": policy_ref,
                "tool_type_id": entry["tool_type_id"],
                "modality": modality,
                "lifecycle_state": "ACTIVE",
                "display_label_id": entry["display_label_id"],
                "measurement_class_ids": entry["measurement_class_ids"],
                "observation_class_ids": entry["observation_class_ids"],
                "emitted_source_class_ids": entry["emitted_source_class_ids"],
                "required_calibration_label_ids": entry["required_calibration_label_ids"],
                "allowed_proposal_methods": SPECTRAL_METHODS
                if modality == "SPECTRAL"
                else VISUAL_METHODS,
                "agent_role_id": ROLE_SPECTRAL_CAPTURE_AGENT
                if modality == "SPECTRAL"
                else ROLE_VISUAL_CAPTURE_AGENT,
                "evidence_refs": (evidence_ref,),
            }
        )
        definitions.append(finalize_analytical_tool_definition(tool, canonicalization_policy))
    return tuple(definitions)


def standard_tool_registry(
    canonicalization_policy: CanonicalizationPolicy,
) -> AnalyticalToolRegistry:
    return AnalyticalToolRegistry(
        registry_ref=_fixture_ref("build2.analytical-tool-registry"),
        canonicalization_policy_ref=_fixture_ref("build2.canonicalization.policy"),
        tools=standard_tool_definitions(canonicalization_policy),
    )


def modality_for(registry: AnalyticalToolRegistry, modality: ToolModality) -> tuple[TermId, ...]:
    return tuple(tool.tool_type_id for tool in registry.tools_for_modality(modality))
