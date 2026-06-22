"""Governed signature, discriminator, and confirmation evaluation."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gptl.core.canonical import CanonicalizationError, canonical_decimal, canonical_sha256
from gptl.core.records import GovernedRef, sorted_unique_refs
from gptl.core.semantic_types import (
    CanonicalDecimal,
    CanonicalizationPolicy,
    CanonicalTimestamp,
    EvidenceLocator,
    FieldId,
    LogicalId,
    OpaqueId,
    Sha256Hex,
    TermId,
    UnitId,
    VersionId,
)
from gptl.mie.predicates import (
    ApplicabilityEvaluation,
    ApplicabilityTruth,
    ContextValue,
    FieldRegistry,
    Predicate,
    PredicateConfigurationError,
    UnitRegistry,
    evaluate_applicability,
    validate_predicate_configuration,
)

DECIMAL_OPERATION_CARRY_DIGITS: Final = 1


class GovernedNumericPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    policy_kind: Literal[
        "SIGNATURE_WEIGHT",
        "DISCRIMINATING_POWER",
        "MIN_SIGNATURE_COVERAGE",
        "TAU_CONFIRM",
        "TAU_VERDICT",
        "DELTA_DOMINANCE",
        "HIGH_POWER_THRESHOLD",
    ]
    value: CanonicalDecimal
    unit_id: UnitId
    scope_ref: GovernedRef
    derivation_ref: GovernedRef
    governing_source_refs: tuple[GovernedRef, ...]
    owner_id: OpaqueId
    approver_id: OpaqueId
    qualification_state: Literal["RESEARCH_ONLY", "QUALIFIED"]
    validation_corpus_ref: GovernedRef
    validation_result: Literal["PASS", "FAIL"]
    effective_at: CanonicalTimestamp
    expires_at: CanonicalTimestamp
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_policy(self) -> GovernedNumericPolicy:
        if self.value < Decimal("0") or self.value > Decimal("1"):
            raise ValueError("diagnostic numeric policy must be bounded to [0,1]")
        if self.owner_id == self.approver_id:
            raise ValueError("numeric policy owner and approver must be distinct")
        if self.effective_at > self.expires_at:
            raise ValueError("numeric policy interval is inverted")
        for refs, label in (
            (self.governing_source_refs, "governing sources"),
            (self.evidence_refs, "numeric policy evidence"),
        ):
            if not refs or sorted_unique_refs(refs) != refs:
                raise ValueError(f"{label} must be nonempty, unique, and sorted")
        return self


class SignatureFeature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    feature_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    candidate_ref: GovernedRef
    observable_id: FieldId
    predicate_ref: GovernedRef
    match_predicate: Predicate
    weight_policy_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> SignatureFeature:
        if not self.evidence_refs or sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("signature feature evidence must be nonempty, unique, and sorted")
        return self


class Discriminator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    discriminator_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    candidate_ref: GovernedRef
    observable_id: FieldId
    artifact_predicate_ref: GovernedRef
    artifact_predicate: Predicate
    real_predicate_ref: GovernedRef
    real_predicate: Predicate
    discriminating_power_policy_ref: GovernedRef
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_definition(self) -> Discriminator:
        if self.artifact_predicate_ref == self.real_predicate_ref:
            raise ValueError("discriminator outcomes require distinct predicates")
        if not self.evidence_refs or sorted_unique_refs(self.evidence_refs) != self.evidence_refs:
            raise ValueError("discriminator evidence must be nonempty, unique, and sorted")
        return self


class DiscriminatorResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    result_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    discriminator_ref: GovernedRef
    supersedes_version_id: VersionId | None
    outcome: Literal[
        "CONSISTENT_WITH_ARTIFACT",
        "CONSISTENT_WITH_REAL",
        "INCONCLUSIVE",
    ]
    observed_value_ref: GovernedRef | None
    answered_by_actor_id: OpaqueId
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp


class EvidenceTypeAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    evidence_type_id: TermId


class StructuredConfirmTest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["STRUCTURED"]
    test_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    predicate_ref: GovernedRef
    predicate: Predicate
    required_evidence_type_ids: tuple[TermId, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_test(self) -> StructuredConfirmTest:
        _validate_terms(self.required_evidence_type_ids, "structured confirm evidence types")
        _validate_refs(self.evidence_refs, "structured confirm evidence")
        return self


class HumanAttestedConfirmTest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["HUMAN_ATTESTED"]
    test_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    authorized_role_policy_ref: GovernedRef
    required_evidence_type_ids: tuple[TermId, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_test(self) -> HumanAttestedConfirmTest:
        _validate_terms(self.required_evidence_type_ids, "attested confirm evidence types")
        _validate_refs(self.evidence_refs, "attested confirm evidence")
        return self


ConfirmTest = Annotated[
    StructuredConfirmTest | HumanAttestedConfirmTest,
    Field(discriminator="kind"),
]


class CandidateDiagnosticContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    failure_mode_ref: GovernedRef
    signature_feature_refs: tuple[GovernedRef, ...]
    required_signature_field_ids: tuple[FieldId, ...]
    discriminator_refs: tuple[GovernedRef, ...]
    confirm_test_ref: GovernedRef
    min_signature_coverage_policy_ref: GovernedRef
    tau_confirm_policy_ref: GovernedRef
    tau_verdict_policy_ref: GovernedRef
    author_id: OpaqueId
    approver_id: OpaqueId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_contract(self) -> CandidateDiagnosticContract:
        _validate_refs(self.signature_feature_refs, "signature feature refs")
        _validate_refs(self.discriminator_refs, "discriminator refs")
        _validate_terms(self.required_signature_field_ids, "required signature fields")
        _validate_refs(self.evidence_refs, "candidate diagnostic evidence")
        if self.author_id == self.approver_id:
            raise ValueError("failure-mode author and approver must be distinct")
        return self


class DiagnosticRoutePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    combine_algorithm_ref: GovernedRef
    implemented_combine_algorithm_id: Literal["BUILD0_COMMUTATIVE_V1"]
    delta_dominance_policy_ref: GovernedRef
    high_power_threshold_policy_ref: GovernedRef
    dimensionless_unit_id: UnitId
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> DiagnosticRoutePolicy:
        _validate_refs(self.evidence_refs, "diagnostic route-policy evidence")
        return self


class AuthorizedRolePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    method_ref: GovernedRef
    allowed_role_ids: tuple[TermId, ...]
    evidence_refs: tuple[GovernedRef, ...]

    @model_validator(mode="after")
    def validate_policy(self) -> AuthorizedRolePolicy:
        _validate_terms(self.allowed_role_ids, "authorized roles")
        _validate_refs(self.evidence_refs, "role-policy evidence")
        return self


class RoleAuthorizationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    policy_ref: GovernedRef
    actor_id: OpaqueId
    role_id: TermId
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    supersedes_version_id: VersionId | None

    @model_validator(mode="after")
    def validate_state(self) -> RoleAuthorizationEvent:
        if self.state != "ACTIVE" and self.supersedes_version_id is None:
            raise ValueError("terminal role authorization requires supersession")
        return self


class AttestationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    attestation_ref: GovernedRef
    record_type_id: TermId
    evidence_location: EvidenceLocator
    failure_mode_ref: GovernedRef
    method_ref: GovernedRef
    attester_id: OpaqueId
    attester_role_id: TermId
    supporting_evidence_refs: tuple[GovernedRef, ...]
    effective_at: CanonicalTimestamp
    recorded_at: CanonicalTimestamp
    state: Literal["ACTIVE", "REVOKED", "SUPERSEDED"]
    supersedes_version_id: VersionId | None

    @model_validator(mode="after")
    def validate_state(self) -> AttestationEvent:
        _validate_refs(self.supporting_evidence_refs, "attestation supporting evidence")
        if self.state != "ACTIVE" and self.supersedes_version_id is None:
            raise ValueError("terminal attestation requires supersession")
        return self


class SignatureEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    evidence_state: Literal["OPEN_UNASSESSED", "EVALUABLE"]
    signature_match_score: CanonicalDecimal | None
    signature_coverage: CanonicalDecimal
    missing_required_field_ids: tuple[FieldId, ...]
    predicate_evaluations: tuple[ApplicabilityEvaluation, ...]
    evidence_refs: tuple[GovernedRef, ...]


class DiscriminatorEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    discriminator_ref: GovernedRef
    outcome: Literal[
        "CONSISTENT_WITH_ARTIFACT",
        "CONSISTENT_WITH_REAL",
        "INCONCLUSIVE",
    ]
    artifact_evaluation: ApplicabilityEvaluation
    real_evaluation: ApplicabilityEvaluation
    active_result_ref: GovernedRef | None
    evidence_refs: tuple[GovernedRef, ...]


class SupportEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    artifact_mass: CanonicalDecimal
    real_mass: CanonicalDecimal
    support_score: CanonicalDecimal
    discriminator_evaluations: tuple[DiscriminatorEvaluation, ...]
    evidence_refs: tuple[GovernedRef, ...]


class ConfirmationEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_ref: GovernedRef
    satisfied: bool
    confirm_test_ref: GovernedRef
    predicate_evaluation: ApplicabilityEvaluation | None
    evidence_refs: tuple[GovernedRef, ...]


class DiagnosticActiveState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    as_of_time: CanonicalTimestamp
    active_discriminator_result_refs: tuple[GovernedRef, ...]
    active_role_authorization_refs: tuple[GovernedRef, ...]
    active_attestation_refs: tuple[GovernedRef, ...]
    state_hash: Sha256Hex


class DiagnosticConfigurationError(ValueError):
    pass


class DiagnosticIntegrityError(ValueError):
    pass


class DiagnosticEngineError(RuntimeError):
    pass


def resolve_diagnostic_active_state(
    discriminator_results: tuple[DiscriminatorResult, ...],
    role_events: tuple[RoleAuthorizationEvent, ...],
    attestations: tuple[AttestationEvent, ...],
    as_of_time: CanonicalTimestamp,
    policy: CanonicalizationPolicy,
) -> DiagnosticActiveState:
    discriminator_refs = sorted_unique_refs(
        tuple(
            item.result_ref
            for item in _active_discriminator_results(discriminator_results, as_of_time)
        )
    )
    role_refs = sorted_unique_refs(
        tuple(item.event_ref for item in _active_role_events(role_events, as_of_time))
    )
    attestation_refs = sorted_unique_refs(
        tuple(item.attestation_ref for item in _active_attestation_events(attestations, as_of_time))
    )
    payload = {
        "as_of_time": as_of_time,
        "active_discriminator_result_refs": discriminator_refs,
        "active_role_authorization_refs": role_refs,
        "active_attestation_refs": attestation_refs,
    }
    return DiagnosticActiveState.model_validate(
        {
            "as_of_time": as_of_time,
            "active_discriminator_result_refs": discriminator_refs,
            "active_role_authorization_refs": role_refs,
            "active_attestation_refs": attestation_refs,
            "state_hash": canonical_sha256(payload, policy),
        },
        context={"canonicalization_policy": policy},
    )


def numeric_policy_by_ref(
    ref: GovernedRef,
    policies: tuple[GovernedNumericPolicy, ...],
    expected_kind: str,
    expected_unit_id: UnitId,
    as_of_time: CanonicalTimestamp,
    operational_mode: str,
) -> GovernedNumericPolicy:
    matches = tuple(item for item in policies if item.policy_ref == ref)
    if len(matches) != 1:
        raise DiagnosticConfigurationError("numeric policy reference must resolve exactly once")
    selected = matches[0]
    if selected.policy_kind != expected_kind or selected.unit_id != expected_unit_id:
        raise DiagnosticConfigurationError("numeric policy kind or unit does not match its use")
    if not (selected.effective_at <= as_of_time <= selected.expires_at):
        raise DiagnosticConfigurationError("diagnostic numeric policy is outside its interval")
    if selected.validation_result != "PASS":
        raise DiagnosticConfigurationError("diagnostic numeric policy failed validation")
    if operational_mode == "QUALIFIED" and selected.qualification_state != "QUALIFIED":
        raise DiagnosticConfigurationError("research-only policy cannot drive a qualified run")
    return selected


def evaluate_signature(
    contract: CandidateDiagnosticContract,
    features: tuple[SignatureFeature, ...],
    context_values: tuple[ContextValue, ...],
    numeric_policies: tuple[GovernedNumericPolicy, ...],
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
    route_policy: DiagnosticRoutePolicy,
    as_of_time: CanonicalTimestamp,
    operational_mode: str,
    canonicalization_policy: CanonicalizationPolicy,
) -> SignatureEvaluation:
    expected_refs = contract.signature_feature_refs
    actual_refs = tuple(item.feature_ref for item in features)
    if actual_refs != expected_refs or any(
        item.candidate_ref != contract.failure_mode_ref for item in features
    ):
        raise DiagnosticConfigurationError("signature features do not match candidate contract")
    evaluations: list[ApplicabilityEvaluation] = []
    observed_weight = Decimal("0")
    matched_weight = Decimal("0")
    total_weight = Decimal("0")
    evidence: list[GovernedRef] = [contract.contract_ref, *contract.evidence_refs]
    for feature in features:
        if _predicate_field_ids(feature.match_predicate) != {feature.observable_id}:
            raise DiagnosticConfigurationError(
                "signature predicate must reference exactly its declared observable"
            )
        try:
            validate_predicate_configuration(feature.match_predicate, field_registry, unit_registry)
        except PredicateConfigurationError as exc:
            raise DiagnosticConfigurationError(str(exc)) from exc
        weight_policy = numeric_policy_by_ref(
            feature.weight_policy_ref,
            numeric_policies,
            "SIGNATURE_WEIGHT",
            route_policy.dimensionless_unit_id,
            as_of_time,
            operational_mode,
        )
        weight = weight_policy.value
        if weight <= Decimal("0"):
            raise DiagnosticConfigurationError("signature weight must be greater than zero")
        evaluation = evaluate_applicability(
            feature.match_predicate,
            feature.predicate_ref,
            context_values,
            field_registry,
            unit_registry,
            canonicalization_policy,
        )
        if evaluation.truth == ApplicabilityTruth.INVALID:
            raise DiagnosticConfigurationError("signature predicate evaluated INVALID")
        evaluations.append(evaluation)
        total_weight += weight
        evidence.extend((feature.feature_ref, feature.predicate_ref, *feature.evidence_refs))
        evidence.extend((weight_policy.policy_ref, *weight_policy.evidence_refs))
        evidence.extend(evaluation.evidence_refs)
        if evaluation.truth in {ApplicabilityTruth.TRUE, ApplicabilityTruth.FALSE}:
            observed_weight += weight
        if evaluation.truth == ApplicabilityTruth.TRUE:
            matched_weight += weight
    if total_weight <= Decimal("0"):
        raise DiagnosticConfigurationError("signature policy has no positive total weight")
    coverage = _ratio(observed_weight, total_weight, canonicalization_policy)
    score = (
        _ratio(matched_weight, observed_weight, canonicalization_policy)
        if observed_weight > Decimal("0")
        else None
    )
    present_fields = {item.field_id for item in context_values}
    missing_required = tuple(sorted(set(contract.required_signature_field_ids) - present_fields))
    state: Literal["OPEN_UNASSESSED", "EVALUABLE"] = (
        "EVALUABLE" if score is not None and not missing_required else "OPEN_UNASSESSED"
    )
    return SignatureEvaluation(
        candidate_ref=contract.failure_mode_ref,
        evidence_state=state,
        signature_match_score=score,
        signature_coverage=coverage,
        missing_required_field_ids=missing_required,
        predicate_evaluations=tuple(
            sorted(
                evaluations,
                key=lambda item: (item.predicate_ref.logical_id, item.predicate_ref.version_id),
            )
        ),
        evidence_refs=sorted_unique_refs(tuple(evidence)),
    )


def evaluate_discriminators(
    contract: CandidateDiagnosticContract,
    discriminators: tuple[Discriminator, ...],
    results: tuple[DiscriminatorResult, ...],
    context_values: tuple[ContextValue, ...],
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> tuple[DiscriminatorEvaluation, ...]:
    if tuple(item.discriminator_ref for item in discriminators) != contract.discriminator_refs:
        raise DiagnosticConfigurationError("discriminators do not match candidate contract")
    if any(item.candidate_ref != contract.failure_mode_ref for item in discriminators):
        raise DiagnosticConfigurationError("discriminator candidate binding mismatch")
    active_results = _active_discriminator_results(results, as_of_time)
    result_by_discriminator: dict[tuple[str, str], DiscriminatorResult] = {}
    for result in active_results:
        key = (result.discriminator_ref.logical_id, result.discriminator_ref.version_id)
        if key in result_by_discriminator:
            raise DiagnosticIntegrityError("discriminator has multiple unsuperseded result records")
        result_by_discriminator[key] = result
    evaluations: list[DiscriminatorEvaluation] = []
    for discriminator in discriminators:
        if _predicate_field_ids(discriminator.artifact_predicate) != {
            discriminator.observable_id
        } or _predicate_field_ids(discriminator.real_predicate) != {discriminator.observable_id}:
            raise DiagnosticConfigurationError(
                "discriminator predicates must reference exactly the declared observable"
            )
        try:
            validate_predicate_configuration(
                discriminator.artifact_predicate,
                field_registry,
                unit_registry,
            )
            validate_predicate_configuration(
                discriminator.real_predicate,
                field_registry,
                unit_registry,
            )
        except PredicateConfigurationError as exc:
            raise DiagnosticConfigurationError(str(exc)) from exc
        artifact = evaluate_applicability(
            discriminator.artifact_predicate,
            discriminator.artifact_predicate_ref,
            context_values,
            field_registry,
            unit_registry,
            canonicalization_policy,
        )
        real = evaluate_applicability(
            discriminator.real_predicate,
            discriminator.real_predicate_ref,
            context_values,
            field_registry,
            unit_registry,
            canonicalization_policy,
        )
        outcome = _discriminator_outcome(artifact, real)
        active_result = result_by_discriminator.get(
            (discriminator.discriminator_ref.logical_id, discriminator.discriminator_ref.version_id)
        )
        if active_result is not None and active_result.outcome != outcome:
            raise DiagnosticIntegrityError(
                "discriminator result contradicts its snapshot-bound predicates"
            )
        predicate_evidence = {*artifact.evidence_refs, *real.evidence_refs}
        if (
            active_result is not None
            and active_result.observed_value_ref is not None
            and active_result.observed_value_ref not in predicate_evidence
        ):
            raise DiagnosticIntegrityError(
                "discriminator result does not bind the evaluated observation"
            )
        evidence = (
            discriminator.discriminator_ref,
            discriminator.artifact_predicate_ref,
            discriminator.real_predicate_ref,
            *discriminator.evidence_refs,
            *artifact.evidence_refs,
            *real.evidence_refs,
            *((active_result.result_ref,) if active_result is not None else ()),
        )
        evaluations.append(
            DiscriminatorEvaluation(
                discriminator_ref=discriminator.discriminator_ref,
                outcome=outcome,
                artifact_evaluation=artifact,
                real_evaluation=real,
                active_result_ref=(active_result.result_ref if active_result is not None else None),
                evidence_refs=sorted_unique_refs(evidence),
            )
        )
    unknown_result_keys = set(result_by_discriminator) - {
        (item.discriminator_ref.logical_id, item.discriminator_ref.version_id)
        for item in discriminators
    }
    if unknown_result_keys:
        raise DiagnosticConfigurationError("result references a discriminator outside the contract")
    return tuple(
        sorted(
            evaluations,
            key=lambda item: (
                item.discriminator_ref.logical_id,
                item.discriminator_ref.version_id,
            ),
        )
    )


def evaluate_support(
    signature: SignatureEvaluation,
    discriminator_evaluations: tuple[DiscriminatorEvaluation, ...],
    discriminators: tuple[Discriminator, ...],
    numeric_policies: tuple[GovernedNumericPolicy, ...],
    route_policy: DiagnosticRoutePolicy,
    as_of_time: CanonicalTimestamp,
    operational_mode: str,
    canonicalization_policy: CanonicalizationPolicy,
) -> SupportEvaluation:
    if signature.evidence_state != "EVALUABLE" or signature.signature_match_score is None:
        raise DiagnosticConfigurationError("support aggregation requires an evaluable signature")
    discriminator_by_ref = {
        (item.discriminator_ref.logical_id, item.discriminator_ref.version_id): item
        for item in discriminators
    }
    artifact_powers: list[Decimal] = []
    real_powers: list[Decimal] = []
    evidence: list[GovernedRef] = [
        route_policy.policy_ref,
        route_policy.combine_algorithm_ref,
        *route_policy.evidence_refs,
    ]
    for evaluation in discriminator_evaluations:
        definition = discriminator_by_ref.get(
            (evaluation.discriminator_ref.logical_id, evaluation.discriminator_ref.version_id)
        )
        if definition is None:
            raise DiagnosticConfigurationError("discriminator evaluation has no definition")
        power_policy = numeric_policy_by_ref(
            definition.discriminating_power_policy_ref,
            numeric_policies,
            "DISCRIMINATING_POWER",
            route_policy.dimensionless_unit_id,
            as_of_time,
            operational_mode,
        )
        power = power_policy.value
        if evaluation.outcome == "CONSISTENT_WITH_ARTIFACT":
            artifact_powers.append(power)
        elif evaluation.outcome == "CONSISTENT_WITH_REAL":
            real_powers.append(power)
        evidence.extend(evaluation.evidence_refs)
        evidence.extend((power_policy.policy_ref, *power_policy.evidence_refs))
    artifact_mass = _commutative_mass(tuple(artifact_powers), canonicalization_policy)
    real_mass = _commutative_mass(tuple(real_powers), canonicalization_policy)
    base = signature.signature_match_score
    support = _canonical_value(
        base * (Decimal("1") - real_mass) + artifact_mass * (Decimal("1") - base),
        canonicalization_policy,
    )
    return SupportEvaluation(
        candidate_ref=signature.candidate_ref,
        artifact_mass=artifact_mass,
        real_mass=real_mass,
        support_score=min(max(support, Decimal("0")), Decimal("1")),
        discriminator_evaluations=discriminator_evaluations,
        evidence_refs=sorted_unique_refs(tuple(evidence)),
    )


def evaluate_confirmation(
    contract: CandidateDiagnosticContract,
    confirm_test: ConfirmTest,
    context_values: tuple[ContextValue, ...],
    evidence_types: tuple[EvidenceTypeAssertion, ...],
    role_policies: tuple[AuthorizedRolePolicy, ...],
    role_events: tuple[RoleAuthorizationEvent, ...],
    attestations: tuple[AttestationEvent, ...],
    method_ref: GovernedRef,
    field_registry: FieldRegistry,
    unit_registry: UnitRegistry,
    as_of_time: CanonicalTimestamp,
    canonicalization_policy: CanonicalizationPolicy,
) -> ConfirmationEvaluation:
    if confirm_test.test_ref != contract.confirm_test_ref:
        raise DiagnosticConfigurationError("confirm test does not match candidate contract")
    if isinstance(confirm_test, StructuredConfirmTest):
        try:
            validate_predicate_configuration(confirm_test.predicate, field_registry, unit_registry)
        except PredicateConfigurationError as exc:
            raise DiagnosticConfigurationError(str(exc)) from exc
        predicate_evaluation = evaluate_applicability(
            confirm_test.predicate,
            confirm_test.predicate_ref,
            context_values,
            field_registry,
            unit_registry,
            canonicalization_policy,
        )
        if predicate_evaluation.truth == ApplicabilityTruth.INVALID:
            raise DiagnosticConfigurationError("structured confirm predicate evaluated INVALID")
        typed_refs = _evidence_refs_for_types(
            confirm_test.required_evidence_type_ids,
            evidence_types,
        )
        satisfied = predicate_evaluation.truth == ApplicabilityTruth.TRUE and typed_refs is not None
        return ConfirmationEvaluation(
            candidate_ref=contract.failure_mode_ref,
            satisfied=satisfied,
            confirm_test_ref=confirm_test.test_ref,
            predicate_evaluation=predicate_evaluation,
            evidence_refs=sorted_unique_refs(
                (
                    confirm_test.test_ref,
                    confirm_test.predicate_ref,
                    *confirm_test.evidence_refs,
                    *predicate_evaluation.evidence_refs,
                    *(typed_refs or ()),
                )
            ),
        )
    role_policy = _role_policy(confirm_test.authorized_role_policy_ref, role_policies, method_ref)
    active_roles = _active_role_events(role_events, as_of_time)
    active_attestations = _active_attestation_events(attestations, as_of_time)
    satisfying: list[tuple[AttestationEvent, RoleAuthorizationEvent]] = []
    for attestation in active_attestations:
        if (
            attestation.failure_mode_ref != contract.failure_mode_ref
            or attestation.method_ref != method_ref
            or attestation.attester_role_id not in role_policy.allowed_role_ids
            or attestation.attester_id in {contract.author_id, contract.approver_id}
        ):
            continue
        authorizations = tuple(
            event
            for event in active_roles
            if event.policy_ref == role_policy.policy_ref
            and event.actor_id == attestation.attester_id
            and event.role_id == attestation.attester_role_id
        )
        if len(authorizations) > 1:
            raise DiagnosticIntegrityError(
                "multiple active role authorizations satisfy one attestation"
            )
        if not authorizations:
            continue
        authorization = authorizations[0]
        typed_refs = _evidence_refs_for_types(
            confirm_test.required_evidence_type_ids,
            tuple(
                item
                for item in evidence_types
                if item.evidence_ref in attestation.supporting_evidence_refs
            ),
        )
        if typed_refs is not None:
            satisfying.append((attestation, authorization))
    if len(satisfying) > 1:
        raise DiagnosticIntegrityError("multiple active attestations satisfy one confirm test")
    evidence = [confirm_test.test_ref, role_policy.policy_ref, *confirm_test.evidence_refs]
    if satisfying:
        attestation, authorization = satisfying[0]
        evidence.extend(
            (
                attestation.attestation_ref,
                authorization.event_ref,
                *attestation.supporting_evidence_refs,
                *role_policy.evidence_refs,
            )
        )
    return ConfirmationEvaluation(
        candidate_ref=contract.failure_mode_ref,
        satisfied=bool(satisfying),
        confirm_test_ref=confirm_test.test_ref,
        predicate_evaluation=None,
        evidence_refs=sorted_unique_refs(tuple(evidence)),
    )


def evaluated_fraction(
    evaluations: tuple[DiscriminatorEvaluation, ...],
    discriminators: tuple[Discriminator, ...],
    numeric_policies: tuple[GovernedNumericPolicy, ...],
    route_policy: DiagnosticRoutePolicy,
    as_of_time: CanonicalTimestamp,
    operational_mode: str,
    canonicalization_policy: CanonicalizationPolicy,
) -> CanonicalDecimal:
    threshold = numeric_policy_by_ref(
        route_policy.high_power_threshold_policy_ref,
        numeric_policies,
        "HIGH_POWER_THRESHOLD",
        route_policy.dimensionless_unit_id,
        as_of_time,
        operational_mode,
    ).value
    evaluation_by_ref = {
        (item.discriminator_ref.logical_id, item.discriminator_ref.version_id): item
        for item in evaluations
    }
    high_power: list[DiscriminatorEvaluation] = []
    for discriminator in discriminators:
        power = numeric_policy_by_ref(
            discriminator.discriminating_power_policy_ref,
            numeric_policies,
            "DISCRIMINATING_POWER",
            route_policy.dimensionless_unit_id,
            as_of_time,
            operational_mode,
        ).value
        if power >= threshold:
            evaluation = evaluation_by_ref.get(
                (
                    discriminator.discriminator_ref.logical_id,
                    discriminator.discriminator_ref.version_id,
                )
            )
            if evaluation is None:
                raise DiagnosticConfigurationError("high-power discriminator was not evaluated")
            high_power.append(evaluation)
    if not high_power:
        raise DiagnosticConfigurationError(
            "published candidate set has no high-power discriminator"
        )
    answered = sum(item.outcome != "INCONCLUSIVE" for item in high_power)
    return _ratio(Decimal(answered), Decimal(len(high_power)), canonicalization_policy)


def _discriminator_outcome(
    artifact: ApplicabilityEvaluation,
    real: ApplicabilityEvaluation,
) -> Literal["CONSISTENT_WITH_ARTIFACT", "CONSISTENT_WITH_REAL", "INCONCLUSIVE"]:
    if ApplicabilityTruth.INVALID in {artifact.truth, real.truth}:
        raise DiagnosticConfigurationError("discriminator outcome predicate evaluated INVALID")
    if ApplicabilityTruth.UNKNOWN in {artifact.truth, real.truth}:
        return "INCONCLUSIVE"
    artifact_true = artifact.truth == ApplicabilityTruth.TRUE
    real_true = real.truth == ApplicabilityTruth.TRUE
    if artifact_true and real_true:
        raise DiagnosticConfigurationError("discriminator outcome predicates overlap")
    if artifact_true:
        return "CONSISTENT_WITH_ARTIFACT"
    if real_true:
        return "CONSISTENT_WITH_REAL"
    return "INCONCLUSIVE"


def _predicate_field_ids(predicate: Predicate) -> set[FieldId]:
    if predicate.kind == "comparison":
        return {predicate.comparison.field_id} if predicate.comparison is not None else set()
    if predicate.kind == "not":
        return _predicate_field_ids(predicate.term) if predicate.term is not None else set()
    return {field_id for term in (predicate.terms or ()) for field_id in _predicate_field_ids(term)}


def _active_discriminator_results(
    events: tuple[DiscriminatorResult, ...],
    as_of_time: CanonicalTimestamp,
) -> tuple[DiscriminatorResult, ...]:
    eligible = tuple(
        item
        for item in events
        if item.effective_at <= as_of_time and item.recorded_at <= as_of_time
    )
    _validate_event_order(tuple(item.result_ref for item in events), "discriminator results")
    head_keys = _supersession_heads(
        tuple(
            (
                item.result_ref,
                item.supersedes_version_id,
                (item.discriminator_ref,),
            )
            for item in eligible
        ),
        "discriminator result",
    )
    return tuple(
        item
        for item in eligible
        if (item.result_ref.logical_id, item.result_ref.version_id) in head_keys
    )


def _active_role_events(
    events: tuple[RoleAuthorizationEvent, ...],
    as_of_time: CanonicalTimestamp,
) -> tuple[RoleAuthorizationEvent, ...]:
    _validate_event_order(tuple(item.event_ref for item in events), "role authorization events")
    eligible = tuple(
        item
        for item in events
        if item.effective_at <= as_of_time and item.recorded_at <= as_of_time
    )
    head_keys = _supersession_heads(
        tuple(
            (
                item.event_ref,
                item.supersedes_version_id,
                (item.policy_ref, item.actor_id, item.role_id),
            )
            for item in eligible
        ),
        "role authorization",
    )
    return tuple(
        item
        for item in eligible
        if item.state == "ACTIVE"
        and (item.event_ref.logical_id, item.event_ref.version_id) in head_keys
    )


def _active_attestation_events(
    events: tuple[AttestationEvent, ...],
    as_of_time: CanonicalTimestamp,
) -> tuple[AttestationEvent, ...]:
    _validate_event_order(tuple(item.attestation_ref for item in events), "attestation events")
    eligible = tuple(
        item
        for item in events
        if item.effective_at <= as_of_time and item.recorded_at <= as_of_time
    )
    head_keys = _supersession_heads(
        tuple(
            (
                item.attestation_ref,
                item.supersedes_version_id,
                (
                    item.failure_mode_ref,
                    item.method_ref,
                    item.attester_id,
                    item.attester_role_id,
                ),
            )
            for item in eligible
        ),
        "attestation",
    )
    return tuple(
        item
        for item in eligible
        if item.state == "ACTIVE"
        and (item.attestation_ref.logical_id, item.attestation_ref.version_id) in head_keys
    )


def _supersession_heads(
    entries: tuple[tuple[GovernedRef, VersionId | None, tuple[object, ...]], ...],
    label: str,
) -> set[tuple[LogicalId, VersionId]]:
    by_key = {
        (item.logical_id, item.version_id): (item, supersedes, binding)
        for item, supersedes, binding in entries
    }
    roots: dict[str, int] = {}
    superseded_keys: set[tuple[str, str]] = set()
    for item, supersedes, binding in entries:
        if supersedes is None:
            roots[item.logical_id] = roots.get(item.logical_id, 0) + 1
            continue
        # Explicit lineage, not timestamp recency, decides which immutable version
        # survives. A latest-by-time fallback would make replay query-dependent.
        target_key = (item.logical_id, supersedes)
        target = by_key.get(target_key)
        if target is None:
            raise DiagnosticIntegrityError(f"{label} supersedes an unavailable version")
        target_ref, _, target_binding = target
        if target_ref.version_number >= item.version_number or target_binding != binding:
            raise DiagnosticIntegrityError(f"{label} supersession changes identity or order")
        if target_key in superseded_keys:
            raise DiagnosticIntegrityError(f"{label} version has multiple successors")
        superseded_keys.add(target_key)
    if any(count != 1 for count in roots.values()):
        raise DiagnosticIntegrityError(f"{label} chain must have exactly one root")
    return set(by_key) - superseded_keys


def _role_policy(
    ref: GovernedRef,
    policies: tuple[AuthorizedRolePolicy, ...],
    method_ref: GovernedRef,
) -> AuthorizedRolePolicy:
    matches = tuple(item for item in policies if item.policy_ref == ref)
    if len(matches) != 1 or matches[0].method_ref != method_ref:
        raise DiagnosticConfigurationError("authorized role policy binding is invalid")
    return matches[0]


def _evidence_refs_for_types(
    required_types: tuple[TermId, ...],
    assertions: tuple[EvidenceTypeAssertion, ...],
) -> tuple[GovernedRef, ...] | None:
    available = {item.evidence_type_id for item in assertions}
    if not set(required_types).issubset(available):
        return None
    return sorted_unique_refs(
        tuple(item.evidence_ref for item in assertions if item.evidence_type_id in required_types)
    )


def _commutative_mass(
    powers: tuple[Decimal, ...],
    policy: CanonicalizationPolicy,
) -> Decimal:
    # Quantizing each update would make rounding depend on evidence order. The set
    # product stays at sufficient precision and crosses the canonical boundary once.
    with localcontext() as context:
        context.prec = (
            max(len(powers), 1) * (policy.decimal_max_integer_digits + policy.decimal_scale)
            + DECIMAL_OPERATION_CARRY_DIGITS
        )
        complement_product = Decimal("1")
        for power in powers:
            complement_product *= Decimal("1") - power
    return _canonical_value(Decimal("1") - complement_product, policy)


def _ratio(
    numerator: Decimal,
    denominator: Decimal,
    policy: CanonicalizationPolicy,
) -> Decimal:
    if denominator <= Decimal("0"):
        raise DiagnosticConfigurationError("diagnostic ratio denominator must be positive")
    try:
        with localcontext() as context:
            context.prec = (
                policy.decimal_max_integer_digits
                + policy.decimal_scale
                + len(numerator.as_tuple().digits)
                + len(denominator.as_tuple().digits)
                + DECIMAL_OPERATION_CARRY_DIGITS
            )
            value = numerator / denominator
    except InvalidOperation as exc:
        raise DiagnosticConfigurationError("diagnostic ratio cannot be represented") from exc
    return _canonical_value(value, policy)


def _canonical_value(value: Decimal, policy: CanonicalizationPolicy) -> Decimal:
    try:
        return Decimal(canonical_decimal(value, policy))
    except CanonicalizationError as exc:
        raise DiagnosticConfigurationError("diagnostic value violates numeric policy") from exc


def _validate_event_order(refs: tuple[GovernedRef, ...], label: str) -> None:
    keys = tuple((item.logical_id, item.version_number, item.version_id) for item in refs)
    if keys != tuple(sorted(set(keys))):
        raise DiagnosticConfigurationError(f"{label} must be unique and version-sorted")


def _validate_refs(refs: tuple[GovernedRef, ...], label: str) -> None:
    if not refs or sorted_unique_refs(refs) != refs:
        raise ValueError(f"{label} must be nonempty, unique, and sorted")


def _validate_terms(terms: tuple[str, ...], label: str) -> None:
    if not terms or terms != tuple(sorted(set(terms))):
        raise ValueError(f"{label} must be nonempty, unique, and sorted")
