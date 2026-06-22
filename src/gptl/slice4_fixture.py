"""Governed synthetic Slice 4 EDS artifact-confirmation fixtures."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from gptl.core.directives import DisplayDirective, DisplayTemplate, DisplayTemplateRegistry
from gptl.core.ratification import IntakeRecord, IntakeValue, intake_value_hash
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import EvidenceLocator, FieldId, TemplateId, TermId, UnitId
from gptl.mie.diagnostics import (
    AttestationEvent,
    AuthorizedRolePolicy,
    CandidateDiagnosticContract,
    DiagnosticRoutePolicy,
    Discriminator,
    DiscriminatorResult,
    EvidenceTypeAssertion,
    GovernedNumericPolicy,
    HumanAttestedConfirmTest,
    RoleAuthorizationEvent,
    SignatureFeature,
    StructuredConfirmTest,
)
from gptl.mie.predicates import (
    EnumValue,
    EqualityComparison,
    FieldDefinition,
    FieldRegistry,
    MembershipComparison,
    Predicate,
    UnitDefinition,
    UnitRegistry,
)
from gptl.mie.records import (
    AuthorityPackManifest,
    CandidatePack,
    EnginePolicyManifest,
    FailureModeRecord,
)
from gptl.mie.slice2_service import Slice2Policy, Slice2Request
from gptl.mie.slice3_service import Slice3Policy
from gptl.mie.slice4_service import (
    Slice4Policy,
    Slice4RouteReasons,
    Slice4Runtime,
    diagnostic_bound_refs,
)
from gptl.slice2_fixture import (
    DIMENSION_TEMPERATURE,
    ENVIRONMENT_HUMID,
    FIELD_ENVIRONMENT,
    FIELD_MODE,
    FIELD_TEMPERATURE,
    MODE_PRODUCTION,
    UNIT_CELSIUS,
    UNIT_MM,
    canonicalization_policy,
    governed_ref,
)
from gptl.slice3_fixture import (
    FIELD_DEVIATION,
    TEST_SCOPE_REF,
    UNIT_MICROMETER,
    slice3_policy,
    slice3_runtime_for_pack,
)

FIELD_PEAK_SHAPE = FieldId("field.eds-peak-shape")
FIELD_REFERENCE_RESCAN = FieldId("field.eds-reference-rescan")
PEAK_OVERLAP = TermId("eds-peak-shape.overlap")
PEAK_ISOLATED = TermId("eds-peak-shape.isolated")
RESCAN_ARTIFACT = TermId("eds-rescan.artifact-consistent")
RESCAN_REAL = TermId("eds-rescan.real-consistent")
UNIT_DIMENSIONLESS = UnitId("unit.dimensionless")
DIMENSION_FRACTION = TermId("dimension.fraction")
EVIDENCE_TYPE_REFERENCE_RESCAN = TermId("evidence-type.reference-rescan")
ROLE_METHOD_REVIEWER = TermId("role.method-reviewer")
ROLE_UNAUTHORIZED = TermId("role.unauthorized")
AS_OF = "2026-06-21T12:00:00.000Z"
LATER_AS_OF = "2026-06-21T14:00:00.000Z"
LATE_EVENT_TIME = "2026-06-21T13:00:00.000Z"

ConfirmKind = Literal["STRUCTURED", "HUMAN_ATTESTED"]
AuthorityScenario = Literal[
    "NONE",
    "VALID",
    "DISALLOWED_ROLE",
    "SEPARATION_AUTHOR",
    "SEPARATION_APPROVER",
    "ATTESTATION_REVOKED",
    "ROLE_REVOKED",
    "LATE_ATTESTATION_REVOCATION",
    "ATTESTATION_SUPERSEDED",
]
ResultScenario = Literal["NONE", "CONTRADICTORY", "SUPERSEDED"]


def slice4_policy() -> Slice4Policy:
    base = slice3_policy()
    additions = tuple(
        DisplayTemplate(
            template_id=TemplateId(template_id),
            template_ref=governed_ref(f"template.{template_id}"),
            parameter_specs=(),
        )
        for template_id in (
            "action.collect-open-discriminators",
            "action.report-engine-failure",
            "action.retest-reference-standard",
            "action.review-artifact-evidence",
        )
    )
    registry = DisplayTemplateRegistry(
        registry_ref=governed_ref("display-registry.slice4"),
        templates=tuple(
            sorted(
                (*base.slice2_policy.display_registry.templates, *additions),
                key=lambda item: item.template_id,
            )
        ),
    )
    slice2 = Slice2Policy.model_validate(
        {
            **base.slice2_policy.model_dump(mode="python"),
            "engine_version": "slice4.v1",
            "display_registry": registry,
        }
    )
    slice3 = Slice3Policy.model_validate(
        {
            **base.model_dump(mode="python"),
            "slice2_policy": slice2,
        }
    )
    return Slice4Policy(
        slice3_policy=slice3,
        route_policy_ref=governed_ref("route-policy.slice4"),
        route_reasons=Slice4RouteReasons(
            diagnostic_configuration_invalid=TermId("route.diagnostic-configuration-invalid"),
            diagnostic_engine_failure=TermId("route.diagnostic-engine-failure"),
            diagnostic_integrity_failure=TermId("route.diagnostic-integrity-failure"),
            method_artifact=TermId("route.method-artifact"),
            diagnostic_indeterminate=TermId("route.diagnostic-indeterminate"),
        ),
        method_artifact_action=_directive("action.review-artifact-evidence"),
        indeterminate_action=_directive("action.collect-open-discriminators"),
        engine_failure_action=_directive("action.report-engine-failure"),
        what_would_change_artifact=(_directive("action.retest-reference-standard"),),
        method_artifact_event_type_id=TermId("audit.method-artifact"),
        indeterminate_event_type_id=TermId("audit.diagnostic-indeterminate"),
    )


def slice4_request(suffix: str, as_of_time: str) -> Slice2Request:
    policy = canonicalization_policy()
    return Slice2Request.model_validate(
        {
            "run_id": f"run.slice4.{suffix}",
            "decision_id": f"decision.slice4.{suffix}",
            "case_id": f"case.slice4.{suffix}",
            "audit_event_id": f"audit.slice4.{suffix}.0",
            "snapshot_id": f"snapshot.slice4.{suffix}",
            "requested_pack_version_id": slice4_candidate_pack().manifest.pack_ref.version_id,
            "as_of_time": as_of_time,
        },
        context={"canonicalization_policy": policy},
    )


def slice4_runtime(
    confirm_kind: ConfirmKind,
    authority_scenario: AuthorityScenario,
    include_signature_observations: bool,
    result_scenario: ResultScenario,
) -> Slice4Runtime:
    policy = slice4_policy()
    pack = slice4_candidate_pack()
    slice3 = slice3_runtime_for_pack(
        "VALID",
        "QUALIFIED",
        Decimal("0.0101"),
        True,
        pack,
        policy.slice3_policy,
    )
    intake = _diagnostic_intake(
        slice3.slice2_runtime.intake,
        include_signature_observations,
    )
    route_policy = _diagnostic_route_policy()
    numeric_policies = _numeric_policies(pack.manifest.pack_ref)
    contracts, features, discriminators, tests = _diagnostic_records(
        pack,
        confirm_kind,
    )
    evidence_types = (
        EvidenceTypeAssertion(
            evidence_ref=governed_ref("source.eds-reference-rescan"),
            record_type_id=TermId("record.structured-test-evidence"),
            evidence_location=EvidenceLocator("fixture:eds-reference-rescan"),
            evidence_type_id=EVIDENCE_TYPE_REFERENCE_RESCAN,
        ),
    )
    role_policies = (
        AuthorizedRolePolicy(
            policy_ref=governed_ref("role-policy.eds-review"),
            record_type_id=TermId("record.authorized-role-policy"),
            evidence_location=EvidenceLocator("fixture:role-policy"),
            method_ref=pack.manifest.method_ref,
            allowed_role_ids=(ROLE_METHOD_REVIEWER,),
            evidence_refs=(governed_ref("evidence.role-policy.eds-review"),),
        ),
    )
    role_events = _role_events(authority_scenario, role_policies[0].policy_ref)
    attestations = _attestations(
        authority_scenario,
        pack.manifest.method_ref,
        contracts[-1],
    )
    result_discriminator_ref = next(
        item.discriminator_ref
        for item in discriminators
        if item.discriminator_ref.logical_id == "discriminator.peak-overlap"
    )
    results = _discriminator_results(result_scenario, result_discriminator_ref)
    provisional = Slice4Runtime(
        slice3_runtime=slice3,
        diagnostic_route_policy=route_policy,
        numeric_policies=numeric_policies,
        candidate_contracts=contracts,
        signature_features=features,
        discriminators=discriminators,
        discriminator_results=results,
        confirm_tests=tests,
        evidence_type_assertions=evidence_types,
        role_policies=role_policies,
        role_authorization_events=role_events,
        attestation_events=attestations,
    )
    additional_refs = sorted_unique_refs(
        (
            *slice3.slice2_runtime.additional_bound_refs,
            policy.route_policy_ref,
            *diagnostic_bound_refs(provisional),
        )
    )
    slice2 = slice3.slice2_runtime.model_copy(
        update={"intake": intake, "additional_bound_refs": additional_refs}
    )
    bound_slice3 = slice3.model_copy(update={"slice2_runtime": slice2})
    return Slice4Runtime.model_validate(
        {
            **provisional.model_dump(mode="python"),
            "slice3_runtime": bound_slice3,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def slice4_candidate_pack() -> CandidatePack:
    field_registry = FieldRegistry(
        registry_ref=governed_ref("field-registry.slice4-eds"),
        fields=tuple(
            sorted(
                (
                    FieldDefinition(
                        field_id=FIELD_DEVIATION,
                        value_kind="NUMERIC",
                        canonical_unit_id=UNIT_MM,
                        allowed_terms=(),
                    ),
                    FieldDefinition(
                        field_id=FIELD_ENVIRONMENT,
                        value_kind="ENUM",
                        canonical_unit_id=None,
                        allowed_terms=(ENVIRONMENT_HUMID,),
                    ),
                    FieldDefinition(
                        field_id=FIELD_MODE,
                        value_kind="ENUM",
                        canonical_unit_id=None,
                        allowed_terms=(MODE_PRODUCTION,),
                    ),
                    FieldDefinition(
                        field_id=FIELD_PEAK_SHAPE,
                        value_kind="ENUM",
                        canonical_unit_id=None,
                        allowed_terms=(PEAK_ISOLATED, PEAK_OVERLAP),
                    ),
                    FieldDefinition(
                        field_id=FIELD_REFERENCE_RESCAN,
                        value_kind="ENUM",
                        canonical_unit_id=None,
                        allowed_terms=(RESCAN_ARTIFACT, RESCAN_REAL),
                    ),
                    FieldDefinition(
                        field_id=FIELD_TEMPERATURE,
                        value_kind="NUMERIC",
                        canonical_unit_id=UNIT_CELSIUS,
                        allowed_terms=(),
                    ),
                ),
                key=lambda item: item.field_id,
            )
        ),
    )
    unit_registry = UnitRegistry(
        registry_ref=governed_ref("unit-registry.slice4-eds"),
        units=tuple(
            sorted(
                (
                    UnitDefinition(
                        unit_id=UNIT_CELSIUS,
                        dimension_id=DIMENSION_TEMPERATURE,
                        scale_to_base=Decimal("1"),
                        offset_to_base=Decimal("0"),
                    ),
                    UnitDefinition(
                        unit_id=UNIT_DIMENSIONLESS,
                        dimension_id=DIMENSION_FRACTION,
                        scale_to_base=Decimal("1"),
                        offset_to_base=Decimal("0"),
                    ),
                    UnitDefinition(
                        unit_id=UNIT_MM,
                        dimension_id=TermId("dimension.length"),
                        scale_to_base=Decimal("1"),
                        offset_to_base=Decimal("0"),
                    ),
                    UnitDefinition(
                        unit_id=UNIT_MICROMETER,
                        dimension_id=TermId("dimension.length"),
                        scale_to_base=Decimal("0.001"),
                        offset_to_base=Decimal("0"),
                    ),
                ),
                key=lambda item: item.unit_id,
            )
        ),
    )
    method_ref = governed_ref("method.eds-reference")
    candidates = tuple(
        sorted(
            (
                _candidate("failure.detector-drift", method_ref),
                _candidate("failure.peak-overlap", method_ref),
            ),
            key=lambda item: item.failure_mode_ref.logical_id,
        )
    )
    engine_policy = EnginePolicyManifest(
        policy_ref=governed_ref("engine-policy.slice4-eds"),
        applicability_algorithm_ref=governed_ref("algorithm.applicability.slice4"),
        canonicalization_policy_ref=governed_ref("canonicalization-policy.slice4"),
        serialization_policy_ref=governed_ref("serialization-policy.slice4"),
        lexical_policy_ref=governed_ref("lexical-policy.slice4"),
        field_registry_ref=field_registry.registry_ref,
        unit_registry_ref=unit_registry.registry_ref,
        required_intake_field_ids=tuple(
            sorted((FIELD_DEVIATION, FIELD_ENVIRONMENT, FIELD_MODE, FIELD_TEMPERATURE))
        ),
    )
    manifest = AuthorityPackManifest(
        pack_ref=governed_ref("pack.slice4-eds-reference"),
        computation_type="DIAGNOSTIC",
        lifecycle="PUBLISHED",
        fixture_class="SYNTHETIC",
        method_ref=method_ref,
        engine_policy_ref=engine_policy.policy_ref,
        evidence_scope_ref=TEST_SCOPE_REF,
        candidate_refs=tuple(item.failure_mode_ref for item in candidates),
        selection_group_refs=(),
    )
    return CandidatePack(
        manifest=manifest,
        engine_policy=engine_policy,
        field_registry=field_registry,
        unit_registry=unit_registry,
        candidates=candidates,
        selection_groups=(),
    )


def _candidate(logical_id: str, method_ref: GovernedRef) -> FailureModeRecord:
    predicate = Predicate(
        kind="comparison",
        comparison=MembershipComparison(
            op="in",
            field_id=FIELD_MODE,
            allowed_terms=(MODE_PRODUCTION,),
        ),
    )
    return FailureModeRecord(
        failure_mode_ref=governed_ref(logical_id),
        method_ref=method_ref,
        mechanism_id=TermId(f"mechanism.{logical_id.removeprefix('failure.')}"),
        overlap_scope_id=TermId(f"scope.{logical_id}"),
        predicate_ref=governed_ref(f"predicate.{logical_id}.applicability"),
        predicate_record_type_id=TermId("record.applicability-predicate"),
        predicate_evidence_location=EvidenceLocator("fixture:eds-applicability"),
        applicability_predicate=predicate,
        selection_binding=None,
        evidence_refs=(governed_ref(f"evidence.{logical_id}"),),
        lifecycle="PUBLISHED",
    )


def _diagnostic_route_policy() -> DiagnosticRoutePolicy:
    return DiagnosticRoutePolicy(
        policy_ref=governed_ref("diagnostic-route-policy.slice4"),
        record_type_id=TermId("record.diagnostic-route-policy"),
        evidence_location=EvidenceLocator("fixture:diagnostic-route-policy"),
        combine_algorithm_ref=governed_ref("algorithm.combine.build0-commutative-v1"),
        implemented_combine_algorithm_id="BUILD0_COMMUTATIVE_V1",
        delta_dominance_policy_ref=governed_ref("numeric-policy.delta-dominance"),
        high_power_threshold_policy_ref=governed_ref("numeric-policy.high-power"),
        dimensionless_unit_id=UNIT_DIMENSIONLESS,
        evidence_refs=(governed_ref("evidence.diagnostic-route-policy"),),
    )


def _numeric_policies(pack_ref: GovernedRef) -> tuple[GovernedNumericPolicy, ...]:
    values = (
        ("delta-dominance", "DELTA_DOMINANCE", "0.20"),
        ("high-power", "HIGH_POWER_THRESHOLD", "0.50"),
        ("min-coverage", "MIN_SIGNATURE_COVERAGE", "1.00"),
        ("power-primary", "DISCRIMINATING_POWER", "0.80"),
        ("tau-confirm", "TAU_CONFIRM", "0.80"),
        ("tau-verdict", "TAU_VERDICT", "0.90"),
        ("weight-primary", "SIGNATURE_WEIGHT", "0.60"),
        ("weight-secondary", "SIGNATURE_WEIGHT", "0.40"),
    )
    policies = tuple(
        _numeric_policy(name, kind, Decimal(value), pack_ref) for name, kind, value in values
    )
    return tuple(sorted(policies, key=lambda item: item.policy_ref.logical_id))


def _numeric_policy(
    name: str,
    kind: str,
    value: Decimal,
    pack_ref: GovernedRef,
) -> GovernedNumericPolicy:
    return GovernedNumericPolicy.model_validate(
        {
            "policy_ref": governed_ref(f"numeric-policy.{name}"),
            "record_type_id": "record.governed-numeric-policy",
            "evidence_location": "fixture:numeric-policy",
            "policy_kind": kind,
            "value": value,
            "unit_id": UNIT_DIMENSIONLESS,
            "scope_ref": pack_ref,
            "derivation_ref": governed_ref(f"derivation.{name}"),
            "governing_source_refs": (governed_ref(f"source.numeric-policy.{name}"),),
            "owner_id": "actor.numeric-policy-owner",
            "approver_id": "actor.numeric-policy-approver",
            "qualification_state": "RESEARCH_ONLY",
            "validation_corpus_ref": governed_ref("validation-corpus.slice4-synthetic"),
            "validation_result": "PASS",
            "effective_at": "2026-06-20T00:00:00.000Z",
            "expires_at": "2026-06-22T23:59:59.999Z",
            "evidence_refs": (governed_ref(f"evidence.numeric-policy.{name}"),),
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _diagnostic_records(
    pack: CandidatePack,
    confirm_kind: ConfirmKind,
) -> tuple[
    tuple[CandidateDiagnosticContract, ...],
    tuple[SignatureFeature, ...],
    tuple[Discriminator, ...],
    tuple[StructuredConfirmTest | HumanAttestedConfirmTest, ...],
]:
    drift_ref, peak_ref = pack.manifest.candidate_refs
    features = tuple(
        sorted(
            (
                _signature_feature(
                    "drift-peak",
                    drift_ref,
                    FIELD_PEAK_SHAPE,
                    PEAK_ISOLATED,
                    "weight-primary",
                ),
                _signature_feature(
                    "drift-rescan",
                    drift_ref,
                    FIELD_REFERENCE_RESCAN,
                    RESCAN_REAL,
                    "weight-secondary",
                ),
                _signature_feature(
                    "peak-overlap-peak",
                    peak_ref,
                    FIELD_PEAK_SHAPE,
                    PEAK_OVERLAP,
                    "weight-primary",
                ),
                _signature_feature(
                    "peak-overlap-rescan",
                    peak_ref,
                    FIELD_REFERENCE_RESCAN,
                    RESCAN_ARTIFACT,
                    "weight-secondary",
                ),
            ),
            key=lambda item: item.feature_ref.logical_id,
        )
    )
    discriminators = tuple(
        sorted(
            (
                _discriminator(
                    "detector-drift",
                    drift_ref,
                    FIELD_PEAK_SHAPE,
                    PEAK_ISOLATED,
                    PEAK_OVERLAP,
                ),
                _discriminator(
                    "peak-overlap",
                    peak_ref,
                    FIELD_REFERENCE_RESCAN,
                    RESCAN_ARTIFACT,
                    RESCAN_REAL,
                ),
                _discriminator(
                    "peak-shape-confirmation",
                    peak_ref,
                    FIELD_PEAK_SHAPE,
                    PEAK_OVERLAP,
                    PEAK_ISOLATED,
                ),
            ),
            key=lambda item: item.discriminator_ref.logical_id,
        )
    )
    drift_test = _structured_confirm(
        "detector-drift",
        FIELD_PEAK_SHAPE,
        PEAK_ISOLATED,
    )
    peak_test: StructuredConfirmTest | HumanAttestedConfirmTest
    if confirm_kind == "STRUCTURED":
        peak_test = _structured_confirm(
            "peak-overlap",
            FIELD_REFERENCE_RESCAN,
            RESCAN_ARTIFACT,
        )
    else:
        peak_test = HumanAttestedConfirmTest(
            kind="HUMAN_ATTESTED",
            test_ref=governed_ref("confirm-test.peak-overlap"),
            record_type_id=TermId("record.human-attested-confirm-test"),
            evidence_location=EvidenceLocator("fixture:attested-confirm-test"),
            authorized_role_policy_ref=governed_ref("role-policy.eds-review"),
            required_evidence_type_ids=(EVIDENCE_TYPE_REFERENCE_RESCAN,),
            evidence_refs=(governed_ref("evidence.confirm-test.peak-overlap"),),
        )
    tests = tuple(sorted((drift_test, peak_test), key=lambda item: item.test_ref.logical_id))
    features_by_candidate = {
        candidate_ref: tuple(
            item.feature_ref for item in features if item.candidate_ref == candidate_ref
        )
        for candidate_ref in pack.manifest.candidate_refs
    }
    discriminators_by_candidate = {
        candidate_ref: tuple(
            item.discriminator_ref for item in discriminators if item.candidate_ref == candidate_ref
        )
        for candidate_ref in pack.manifest.candidate_refs
    }
    contracts = tuple(
        CandidateDiagnosticContract(
            contract_ref=governed_ref(f"contract.{candidate_ref.logical_id}"),
            record_type_id=TermId("record.candidate-diagnostic-contract"),
            evidence_location=EvidenceLocator("fixture:candidate-diagnostic-contract"),
            failure_mode_ref=candidate_ref,
            signature_feature_refs=features_by_candidate[candidate_ref],
            required_signature_field_ids=tuple(sorted((FIELD_PEAK_SHAPE, FIELD_REFERENCE_RESCAN))),
            discriminator_refs=discriminators_by_candidate[candidate_ref],
            confirm_test_ref=governed_ref(
                f"confirm-test.{candidate_ref.logical_id.removeprefix('failure.')}"
            ),
            min_signature_coverage_policy_ref=governed_ref("numeric-policy.min-coverage"),
            tau_confirm_policy_ref=governed_ref("numeric-policy.tau-confirm"),
            tau_verdict_policy_ref=governed_ref("numeric-policy.tau-verdict"),
            author_id="actor.failure-mode-author",
            approver_id="actor.failure-mode-approver",
            evidence_refs=(governed_ref(f"evidence.contract.{candidate_ref.logical_id}"),),
        )
        for candidate_ref in pack.manifest.candidate_refs
    )
    return contracts, features, discriminators, tests


def _signature_feature(
    name: str,
    candidate_ref: GovernedRef,
    field_id: FieldId,
    expected_term: TermId,
    weight_name: str,
) -> SignatureFeature:
    return SignatureFeature(
        feature_ref=governed_ref(f"signature-feature.{name}"),
        record_type_id=TermId("record.signature-feature"),
        evidence_location=EvidenceLocator("fixture:signature-feature"),
        candidate_ref=candidate_ref,
        observable_id=field_id,
        predicate_ref=governed_ref(f"predicate.signature-feature.{name}"),
        match_predicate=_enum_equals(field_id, expected_term),
        weight_policy_ref=governed_ref(f"numeric-policy.{weight_name}"),
        evidence_refs=(governed_ref(f"evidence.signature-feature.{name}"),),
    )


def _discriminator(
    name: str,
    candidate_ref: GovernedRef,
    field_id: FieldId,
    artifact_term: TermId,
    real_term: TermId,
) -> Discriminator:
    return Discriminator(
        discriminator_ref=governed_ref(f"discriminator.{name}"),
        record_type_id=TermId("record.discriminator"),
        evidence_location=EvidenceLocator("fixture:discriminator"),
        candidate_ref=candidate_ref,
        observable_id=field_id,
        artifact_predicate_ref=governed_ref(f"predicate.discriminator.{name}.artifact"),
        artifact_predicate=_enum_equals(field_id, artifact_term),
        real_predicate_ref=governed_ref(f"predicate.discriminator.{name}.real"),
        real_predicate=_enum_equals(field_id, real_term),
        discriminating_power_policy_ref=governed_ref("numeric-policy.power-primary"),
        evidence_refs=(governed_ref(f"evidence.discriminator.{name}"),),
    )


def _structured_confirm(
    name: str,
    field_id: FieldId,
    expected_term: TermId,
) -> StructuredConfirmTest:
    return StructuredConfirmTest(
        kind="STRUCTURED",
        test_ref=governed_ref(f"confirm-test.{name}"),
        record_type_id=TermId("record.structured-confirm-test"),
        evidence_location=EvidenceLocator("fixture:structured-confirm-test"),
        predicate_ref=governed_ref(f"predicate.confirm-test.{name}"),
        predicate=_enum_equals(field_id, expected_term),
        required_evidence_type_ids=(EVIDENCE_TYPE_REFERENCE_RESCAN,),
        evidence_refs=(governed_ref(f"evidence.confirm-test.{name}"),),
    )


def _diagnostic_intake(base: IntakeRecord, include_signature: bool) -> IntakeRecord:
    values = list(base.values)
    if include_signature:
        values.extend(
            (
                _instrument_enum_value(
                    "value.eds-peak-shape",
                    FIELD_PEAK_SHAPE,
                    PEAK_OVERLAP,
                    "source.eds-peak-shape",
                ),
                _instrument_enum_value(
                    "value.eds-reference-rescan",
                    FIELD_REFERENCE_RESCAN,
                    RESCAN_ARTIFACT,
                    "source.eds-reference-rescan",
                ),
            )
        )
    return IntakeRecord(
        intake_ref=governed_ref("intake.slice4-eds"),
        values=tuple(sorted(values, key=lambda item: (item.field_id, item.value_id))),
    )


def _instrument_enum_value(
    value_id: str,
    field_id: FieldId,
    term_id: TermId,
    source_id: str,
) -> IntakeValue:
    value = EnumValue(kind="ENUM", value=term_id)
    return IntakeValue(
        value_id=value_id,
        field_id=field_id,
        value=value,
        value_hash=intake_value_hash(field_id, value, canonicalization_policy()),
        source_kind="INSTRUMENT_EMITTED",
        source_ref=governed_ref(source_id),
        ratification_event_ref=None,
    )


def _role_events(
    scenario: AuthorityScenario,
    policy_ref: GovernedRef,
) -> tuple[RoleAuthorizationEvent, ...]:
    if scenario == "NONE":
        return ()
    role = ROLE_UNAUTHORIZED if scenario == "DISALLOWED_ROLE" else ROLE_METHOD_REVIEWER
    actor = {
        "SEPARATION_AUTHOR": "actor.failure-mode-author",
        "SEPARATION_APPROVER": "actor.failure-mode-approver",
    }.get(scenario, "actor.reviewer")
    active = RoleAuthorizationEvent.model_validate(
        {
            "event_ref": governed_ref("role-authorization.eds-reviewer", 1),
            "record_type_id": "record.role-authorization-event",
            "evidence_location": "fixture:role-authorization",
            "policy_ref": policy_ref,
            "actor_id": actor,
            "role_id": role,
            "effective_at": "2026-06-20T00:00:00.000Z",
            "recorded_at": "2026-06-20T00:00:00.000Z",
            "state": "ACTIVE",
            "supersedes_version_id": None,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    if scenario != "ROLE_REVOKED":
        return (active,)
    revoked = active.model_copy(
        update={
            "event_ref": governed_ref("role-authorization.eds-reviewer", 2),
            "effective_at": "2026-06-21T11:00:00.000Z",
            "recorded_at": "2026-06-21T11:00:00.000Z",
            "state": "REVOKED",
            "supersedes_version_id": active.event_ref.version_id,
        }
    )
    return (active, revoked)


def _attestations(
    scenario: AuthorityScenario,
    method_ref: GovernedRef,
    peak_contract: CandidateDiagnosticContract,
) -> tuple[AttestationEvent, ...]:
    if scenario == "NONE":
        return ()
    role = ROLE_UNAUTHORIZED if scenario == "DISALLOWED_ROLE" else ROLE_METHOD_REVIEWER
    actor = {
        "SEPARATION_AUTHOR": "actor.failure-mode-author",
        "SEPARATION_APPROVER": "actor.failure-mode-approver",
    }.get(scenario, "actor.reviewer")
    active = AttestationEvent.model_validate(
        {
            "attestation_ref": governed_ref("attestation.peak-overlap", 1),
            "record_type_id": "record.attestation-event",
            "evidence_location": "fixture:attestation",
            "failure_mode_ref": peak_contract.failure_mode_ref,
            "method_ref": method_ref,
            "attester_id": actor,
            "attester_role_id": role,
            "supporting_evidence_refs": (governed_ref("source.eds-reference-rescan"),),
            "effective_at": "2026-06-20T00:00:00.000Z",
            "recorded_at": "2026-06-20T00:00:00.000Z",
            "state": "ACTIVE",
            "supersedes_version_id": None,
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )
    if scenario not in {
        "ATTESTATION_REVOKED",
        "LATE_ATTESTATION_REVOCATION",
        "ATTESTATION_SUPERSEDED",
    }:
        return (active,)
    state = "ACTIVE" if scenario == "ATTESTATION_SUPERSEDED" else "REVOKED"
    event_time = (
        LATE_EVENT_TIME if scenario == "LATE_ATTESTATION_REVOCATION" else "2026-06-21T11:00:00.000Z"
    )
    replacement = active.model_copy(
        update={
            "attestation_ref": governed_ref("attestation.peak-overlap", 2),
            "effective_at": event_time,
            "recorded_at": event_time,
            "state": state,
            "supersedes_version_id": active.attestation_ref.version_id,
        }
    )
    return (active, replacement)


def _discriminator_results(
    scenario: ResultScenario,
    discriminator_ref: GovernedRef,
) -> tuple[DiscriminatorResult, ...]:
    if scenario == "NONE":
        return ()
    if scenario == "CONTRADICTORY":
        return tuple(
            sorted(
                (
                    _result("peak-overlap-a", 1, discriminator_ref, "CONSISTENT_WITH_ARTIFACT"),
                    _result("peak-overlap-b", 1, discriminator_ref, "CONSISTENT_WITH_REAL"),
                ),
                key=lambda item: (
                    item.result_ref.logical_id,
                    item.result_ref.version_number,
                    item.result_ref.version_id,
                ),
            )
        )
    first = _result("peak-overlap", 1, discriminator_ref, "CONSISTENT_WITH_REAL")
    second = _result("peak-overlap", 2, discriminator_ref, "CONSISTENT_WITH_ARTIFACT")
    return (first, second)


def _result(
    logical_suffix: str,
    version: int,
    discriminator_ref: GovernedRef,
    outcome: str,
) -> DiscriminatorResult:
    return DiscriminatorResult.model_validate(
        {
            "result_ref": governed_ref(f"discriminator-result.{logical_suffix}", version),
            "record_type_id": "record.discriminator-result",
            "evidence_location": "fixture:discriminator-result",
            "discriminator_ref": discriminator_ref,
            "supersedes_version_id": (
                f"discriminator-result.{logical_suffix}.v1" if version > 1 else None
            ),
            "outcome": outcome,
            "observed_value_ref": governed_ref("source.eds-reference-rescan"),
            "answered_by_actor_id": "actor.reference-operator",
            "effective_at": "2026-06-20T00:00:00.000Z",
            "recorded_at": "2026-06-20T00:00:00.000Z",
        },
        context={"canonicalization_policy": canonicalization_policy()},
    )


def _enum_equals(field_id: FieldId, term_id: TermId) -> Predicate:
    return Predicate(
        kind="comparison",
        comparison=EqualityComparison(
            op="eq",
            field_id=field_id,
            operand=EnumValue(kind="ENUM", value=term_id),
        ),
    )


def _directive(template_id: str) -> DisplayDirective:
    return DisplayDirective(template_id=TemplateId(template_id), params=())
