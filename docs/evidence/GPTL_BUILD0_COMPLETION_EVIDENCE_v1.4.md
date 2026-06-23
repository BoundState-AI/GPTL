# GPTL MIE Build 0 Completion Evidence
## Repository Self-Audit Freeze Record - v1.4

**Implementation commit:** `bb144bf07514278fc1cad832a11d08828922633a`

**Git tree:** `a128fe5541b6a2e18df85c103dcce592df8de152`

**Governing spec SHA-256:** `6b29de109134195b1ec4ebf84490ac773384f88ef8f7077c8b939a809b61c064`

**Build plan SHA-256:** `e2eefb0a2a907c53e5a75403fa786289934a3ec294a120279cf5168df631a718`

**Collected tests:** `302`

**Test inventory SHA-256:** `cad38d0088a6cb252aaf13fcec76b9553ade60648e5de5bd19aaa0d5481cdf27`

**Disposition:** `BUILD_0_COMPLETE_READY_TO_FREEZE`

This disposition is derived only because every recorded command exited zero and every governed gate mapped to at least one exact collected test. It does not qualify a method, lab, instrument, or production process.

## Executed Gates

### `GATE-01`

- Command: `python -m ruff check src tests scripts`
- Exit code: `0`
- Output SHA-256: `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`
- Normalized output:

```text
All checks passed!
```

### `GATE-02`

- Command: `python -m ruff format --check src tests scripts`
- Exit code: `0`
- Output SHA-256: `4cfce4314a68bfd72805ca6ee4c4477596a8626548f54945751eb6fcfa34f996`
- Normalized output:

```text
68 files already formatted
```

### `GATE-03`

- Command: `python -m mypy src`
- Exit code: `0`
- Output SHA-256: `34df9cf38736563d4bb02e64b66effac851acb546ad0a3c3761547e25bbe3570`
- Normalized output:

```text
Success: no issues found in 37 source files
```

### `GATE-04`

- Command: `uv build`
- Exit code: `0`
- Output SHA-256: `e97f40655bf9340378e6c8cadc1d143a94bb790cc4e0b212b5d9cf1beea1817f`
- Normalized output:

```text
Building source distribution...
Building wheel from source distribution...
Successfully built dist/boundstate_gptl-0.1.0.tar.gz
Successfully built dist/boundstate_gptl-0.1.0-py3-none-any.whl
```

### `GATE-05`

- Command: `uv run --isolated --python 3.10 --group dev pytest -q`
- Exit code: `0`
- Output SHA-256: `502bf564c421779dea32da513bbd769db95560a27e849312b52207d9261cbb78`
- Normalized output:

```text
........................................................................ [ 23%]
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 95%]
..............                                                           [100%]
302 passed in <elapsed>
Installed 21 packages in <elapsed>
```

### `GATE-06`

- Command: `uv run --isolated --python 3.11 --group dev pytest -q`
- Exit code: `0`
- Output SHA-256: `6706c86f582d3d771c659055fa3b8d2ee058730beccc355be2dec75c182204b7`
- Normalized output:

```text
........................................................................ [ 23%]
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 95%]
..............                                                           [100%]
302 passed in <elapsed>
Installed 19 packages in <elapsed>
```

### `GATE-07`

- Command: `uv run --isolated --python 3.12 --group dev pytest -q`
- Exit code: `0`
- Output SHA-256: `6706c86f582d3d771c659055fa3b8d2ee058730beccc355be2dec75c182204b7`
- Normalized output:

```text
........................................................................ [ 23%]
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 95%]
..............                                                           [100%]
302 passed in <elapsed>
Installed 19 packages in <elapsed>
```

## Requirement-to-Test Traceability

### `SLICE_1_SAFE_REFUSAL`

Deterministic preflight refusal and atomic append-only PostgreSQL persistence

Matched tests: `32`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#5-slice-1--safe-refusal`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_absent_pack_produces_deterministic_preflight_refusal`
- `tests/slices/test_slice_01_safe_refusal.py::test_available_exact_pack_stops_at_later_slice_boundary`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_bound_versions-binding_id-binding.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_citations-citation_id-citation.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_snapshots-None-None]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_late_audit_row_that_exceeds_declared_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_run_without_declared_audit_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_truncate_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[audit]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[run]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_update_and_delete_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_zero_audit_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_documented_demo_runs_against_postgres`
- `tests/slices/test_slice_01_safe_refusal.py::test_duplicate_run_id_is_not_an_idempotent_write`
- `tests/slices/test_slice_01_safe_refusal.py::test_failure_between_run_and_audit_insert_rolls_back`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_empty_migration_history`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_migration_checksum_drift`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-0-WRONG_AUDIT_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-0-WRONG_RUN_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_migrations_are_ordered_checksummed_and_idempotent`
- `tests/slices/test_slice_01_safe_refusal.py::test_persisted_run_is_readable_from_a_fresh_process`
- `tests/slices/test_slice_01_safe_refusal.py::test_postgres_persists_atomic_run_and_audit_across_connections`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_has_no_non_postgres_fallback`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_honors_connection_selected_schema`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_a_well_formed_but_incorrect_decision_hash`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[as_of_time-2026-06-21T12:00:00.001Z-as_of_time mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[decision_hash-ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff-decision hash mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[requested_pack_id-pack.other-requested pack mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[run_id-run.other-run ID mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[sequence-1-sequence must be contiguous]`

### `SLICE_2_CANDIDATE_PRESERVATION`

Candidate preservation, four-state applicability, ratification, and snapshot persistence

Matched tests: `20`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#6-slice-2--candidate-preservation`

Exact passed node IDs:
- `tests/slices/test_slice_02_candidate_preservation.py::test_backdated_revocation_applies_only_after_its_recorded_time`
- `tests/slices/test_slice_02_candidate_preservation.py::test_database_rejects_incomplete_snapshot_bound_commit`
- `tests/slices/test_slice_02_candidate_preservation.py::test_documented_candidate_preservation_demo_runs_against_postgres`
- `tests/slices/test_slice_02_candidate_preservation.py::test_fully_ratified_candidate_set_reaches_slice_3_boundary`
- `tests/slices/test_slice_02_candidate_preservation.py::test_integrity_failure_precedes_ratification_state_and_candidate_loading`
- `tests/slices/test_slice_02_candidate_preservation.py::test_invalid_pack_returns_configuration_refusal`
- `tests/slices/test_slice_02_candidate_preservation.py::test_pack_version_mismatch_raises_named_binding_error`
- `tests/slices/test_slice_02_candidate_preservation.py::test_ratification_lookup_requires_the_exact_governed_event_identity`
- `tests/slices/test_slice_02_candidate_preservation.py::test_refusal_context_scoping_rejects_cross_boundary_records`
- `tests/slices/test_slice_02_candidate_preservation.py::test_revocation_changes_new_run_without_rewriting_historical_run`
- `tests/slices/test_slice_02_candidate_preservation.py::test_runtime_invalid_applicability_surfaces_candidate_error_and_evidence`
- `tests/slices/test_slice_02_candidate_preservation.py::test_scalar_intake_rejects_multiple_values_for_one_field`
- `tests/slices/test_slice_02_candidate_preservation.py::test_selection_rank_tie_fails_pack_validation`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_binds_every_decision_effective_version`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_bound_run_persists_and_reloads_complete_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_write_failure_rolls_back_every_dependent_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_rejects_output_snapshot_hash_mismatch`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_retains_verified_read_compatibility_with_slice2_v1`
- `tests/slices/test_slice_02_candidate_preservation.py::test_unknown_applicability_is_preserved_and_blocks_negative_conclusion`
- `tests/slices/test_slice_02_candidate_preservation.py::test_unratified_human_input_returns_non_dispositional_advisory`

### `SLICE_3_MSA_CALIBRATION`

Calibration precedence and qualified scope-matched MSA hard gate

Matched tests: `31`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#7-slice-3--msa-and-calibration-gate`

Exact passed node IDs:
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_calibration_validity_boundaries_are_inclusive_and_policy_bound`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_documented_slice3_demo_runs_against_postgres`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_gate_precedence_stops_before_invalid_downstream_state`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_grouped_msa_precedence_applies_and_ungrouped_overlap_is_invalid`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_stale]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-True-TIER1_DECISION-MISSING_REQUIRED_EVIDENCE-calibration_unavailable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-True-TIER1_DECISION-WITHIN_MEASUREMENT_VARIATION-within_variation]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_invalid_deviation_and_contract_mismatch_fail_closed`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_boundary_uses_snapshot_bound_unit_conversion`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_reason_precedence_is_governed_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[GROUPED_TIE-CONFIGURATION_INVALID-msa_configuration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[INVALID_UNIT-CONFIGURATION_INVALID-msa_configuration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[MISSING-MSA_UNCHARACTERIZED-msa_missing]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NON_TEST_SCOPE-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NOT_APPLICABLE-MSA_UNCHARACTERIZED-msa_not_applicable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[SCOPE_MISMATCH-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNIMPLEMENTED-MSA_UNCHARACTERIZED-msa_unimplemented_class]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNKNOWN-MSA_UNCHARACTERIZED-msa_unknown_applicability]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNQUALIFIED-MSA_UNCHARACTERIZED-msa_unqualified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_outside_variation_returns_open_unassessed_candidates`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_persists_with_explicit_schema_and_reloads_complete_record`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_replay_is_byte_identical[UNAVAILABLE-INVALID_UNIT-deviation1]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_replay_is_byte_identical[VALID-QUALIFIED-deviation0]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binding_rejects_conflicting_runtime_reference`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binds_calibration_msa_scope_capability_and_route_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_test_fixture_msa_cannot_satisfy_a_non_test_scope`

### `SLICE_4_ARTIFACT_CONFIRMATION`

Governed scoring, evidence gating, and structured or attested artifact confirmation

Matched tests: `37`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#8-slice-4--artifact-confirmation`

Exact passed node IDs:
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_SUPERSEDED-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[DISALLOWED_ROLE-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[LATE_ATTESTATION_REVOCATION-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ROLE_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_APPROVER-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_AUTHOR-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[VALID-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold0-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold1-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold2-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_contradictory_unsuperseded_results_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_diagnostic_state_hash_has_one_exact_canonical_payload`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_aggregation_is_commutative_over_finite_outcome_domain`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_aggregation_is_invariant_to_result_order`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_result_must_bind_evaluated_observation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_documented_slice4_demo_runs_against_postgres`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta0-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta1-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta2-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_explicit_discriminator_supersession_selects_one_active_result`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_failed_structured_confirm_predicate_blocks_confirmation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_later_recorded_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_referenced_numeric_policy_fails_configuration`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_required_structured_evidence_blocks_confirmation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_supersession_target_fails_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_multiple_active_attestations_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_multiple_active_role_authorizations_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_output_schema_failure_returns_governed_engine_refusal`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_overlapping_discriminator_outcomes_fail_configuration`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_partial_required_signature_evidence_never_aggregates_support`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_authoritative_path_has_no_renderer_dependency`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_snapshot_binds_numeric_policy_confirmation_and_authority`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_structured_confirmation_returns_cited_method_artifact`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_uniquely_dominant_winner_allows_a_second_confirmed_candidate`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_zero_signature_observations_remain_open_unassessed`

### `SLICE_5_HONEST_NEGATIVE`

Evidence-complete elimination and bounded-catalog negative verdict

Matched tests: `21`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#9-slice-5--honest-negative`

Exact passed node IDs:
- `tests/slices/test_slice_05_honest_negative.py::test_catalog_fraction_below_governed_minimum_remains_indeterminate`
- `tests/slices/test_slice_05_honest_negative.py::test_complete_terminal_catalog_returns_honest_bounded_negative`
- `tests/slices/test_slice_05_honest_negative.py::test_documented_slice5_demo_runs_against_postgres`
- `tests/slices/test_slice_05_honest_negative.py::test_hard_elimination_stops_before_candidate_scoring`
- `tests/slices/test_slice_05_honest_negative.py::test_identical_negative_run_replays_byte_identically`
- `tests/slices/test_slice_05_honest_negative.py::test_missing_terminal_ruling_citation_fails_closed`
- `tests/slices/test_slice_05_honest_negative.py::test_open_unassessed_candidate_blocks_negative_verdict`
- `tests/slices/test_slice_05_honest_negative.py::test_positive_artifact_verdict_has_precedence_over_bounded_negative`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_contract_must_cover_every_published_candidate`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold0-IndeterminateDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold1-KnownArtifactsExcludedDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold2-KnownArtifactsExcludedDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_ruling_citation_intersection_requires_full_governed_identity`
- `tests/slices/test_slice_05_honest_negative.py::test_slice5_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_05_honest_negative.py::test_slice5_snapshot_binds_every_negative_contract`
- `tests/slices/test_slice_05_honest_negative.py::test_unknown_catalog_denominator_refuses_configuration`
- `tests/slices/test_slice_05_honest_negative.py::test_unknown_gap_template_is_configuration_invalid`
- `tests/slices/test_slice_05_honest_negative.py::test_unregistered_policy_directive_is_rejected_at_construction[catalog_boundary]`
- `tests/slices/test_slice_05_honest_negative.py::test_unregistered_policy_directive_is_rejected_at_construction[known_artifacts_excluded_action]`
- `tests/slices/test_slice_05_honest_negative.py::test_unresolved_applicability_blocks_negative_verdict`
- `tests/slices/test_slice_05_honest_negative.py::test_zero_support_without_every_required_discriminator_never_rules_out`

### `SLICE_6_TIER2_ADVISORY`

Deterministic model-free Tier 2 advisory with one output per run

Matched tests: `38`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#10-slice-6--tier-2-advisory`

Exact passed node IDs:
- `tests/conformance/test_build0_closeout.py::test_tier2_execution_has_one_output_envelope`
- `tests/slices/test_slice_06_tier2_advisory.py::test_advisory_schema_cannot_carry_verdict_refusal_or_support`
- `tests/slices/test_slice_06_tier2_advisory.py::test_ambiguous_alias_preserves_every_bounded_candidate_without_selecting_method`
- `tests/slices/test_slice_06_tier2_advisory.py::test_authoritative_advisory_path_has_no_model_adapter_surface`
- `tests/slices/test_slice_06_tier2_advisory.py::test_documented_slice6_demo_runs_against_postgres`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[AMBIGUOUS_METHOD-AMBIGUOUS-gap.method-ambiguous-proposed1-measurements1-records1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[MISSING_MSA-RESOLVED-gap.msa-missing-proposed3-measurements3-records3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[STALE_CALIBRATION-RESOLVED-gap.calibration-stale-proposed5-measurements5-records5]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNAVAILABLE_CALIBRATION-RESOLVED-gap.calibration-unavailable-proposed6-measurements6-records6]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNIMPLEMENTED_MSA-RESOLVED-gap.msa-unimplemented-proposed4-measurements4-records4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_APPLICABILITY-RESOLVED-gap.applicability-unknown-proposed7-measurements7-records7]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_METHOD-UNKNOWN-gap.method-unknown-proposed2-measurements2-records2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNRATIFIED_INTAKE-RESOLVED-gap.intake-unratified-proposed0-measurements0-records0]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_equivalent_text_search_accelerator_cannot_change_output`
- `tests/slices/test_slice_06_tier2_advisory.py::test_exact_advisory_query_is_snapshot_bound_and_cited`
- `tests/slices/test_slice_06_tier2_advisory.py::test_identical_advisory_replays_byte_identically`
- `tests/slices/test_slice_06_tier2_advisory.py::test_lexical_normalization_uses_governed_fixed_unicode_data`
- `tests/slices/test_slice_06_tier2_advisory.py::test_lexical_tie_break_replays_across_process_hash_seeds`
- `tests/slices/test_slice_06_tier2_advisory.py::test_non_equivalent_text_search_accelerator_fails_configuration`
- `tests/slices/test_slice_06_tier2_advisory.py::test_rendered_prose_is_separate_and_cannot_modify_advisory_hash`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolved_advisory_preserves_complete_published_candidate_set`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_policy_rejects_an_unimplemented_unicode_data_version`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query0-EXACT-RESOLVED-expected_refs0]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query1-CONTROLLED_TERM-AMBIGUOUS-expected_refs1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query2-RELATIONAL-RESOLVED-expected_refs2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query3-LEXICAL-RESOLVED-expected_refs3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query4-LEXICAL-AMBIGUOUS-expected_refs4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[advisory_bound_refs]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[build_tier2_advisory]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[execute_tier2_advisory]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[normalize_lexical_text]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[resolve_advisory_method]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_tier2_rejects_a_positive_tier1_verdict_before_route_selection`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unexpected_unicode_data_version_fails_closed`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unknown_applicability_evidence_remains_explicit`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unknown_method_remains_explicit_without_candidates`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unregistered_advisory_directive_is_rejected`

### `SLICE_7_REPLAY_INTEGRITY`

Exact-input replay, tamper refusal, and immutable pack evolution

Matched tests: `24`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#11-slice-7--replay-and-integrity`

Exact passed node IDs:
- `tests/slices/test_slice_07_replay_integrity.py::test_correction_creates_new_version_and_run_without_rewriting_history`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_process_replay_uses_only_persisted_capsule`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_run_capsule_substitution_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_database_rejects_replay_capsule_mutation`
- `tests/slices/test_slice_07_replay_integrity.py::test_documented_slice7_demo_replays_all_prior_slices`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_documented_demo_requires_an_explicit_database_url`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_prior_slice_replays_exactly_after_store_reopen`
- `tests/slices/test_slice_07_replay_integrity.py::test_explicit_pack_evolution_never_resolves_latest`
- `tests/slices/test_slice_07_replay_integrity.py::test_identical_replay_is_byte_identical`
- `tests/slices/test_slice_07_replay_integrity.py::test_later_attestation_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_07_replay_integrity.py::test_missing_run_returns_governed_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_noncanonical_replay_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_reexecution_exception_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_capsule_and_run_commit_atomically`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_has_no_network_or_implicit_latest_surface`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_policy_reference_mismatch_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_recipe_schema_mismatch_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_run_without_exact_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_snapshot_bound_discriminator_supersession_replays_exactly`
- `tests/slices/test_slice_07_replay_integrity.py::test_stale_run_payload_checksum_returns_stored_content_invalid`
- `tests/slices/test_slice_07_replay_integrity.py::test_tampered_replay_capsule_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_bound_content_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_replay_algorithm_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_validly_rehashed_output_tamper_is_caught_by_reexecution`

### `ORACLE_TIMESTAMP_IDENTITY_SCHEMA_CLOSEOUT`

Source-audited timestamp, identity, calibration, output, refusal, and replay-schema boundaries

Matched tests: `7`

Source references:
- `docs/GPTL_Manufacturing_Platform_v0.4.19.md#212-determinism-contract-with-numeric-representation-closes-finding-1`
- `docs/GPTL_Manufacturing_Platform_v0.4.19.md#213-canonical-serialization-and-hashing-contract`
- `docs/GPTL_Manufacturing_Platform_v0.4.19.md#77-cases-and-snapshots`

Exact passed node IDs:
- `tests/conformance/test_build0_closeout.py::test_authoritative_identifiers_are_caller_bound_replay_inputs`
- `tests/conformance/test_build0_closeout.py::test_authoritative_source_does_not_generate_identity`
- `tests/conformance/test_build0_closeout.py::test_authoritative_writes_do_not_upsert_identity`
- `tests/conformance/test_build0_closeout.py::test_preflight_timestamp_width_is_explicitly_policy_bound`
- `tests/conformance/test_build0_closeout.py::test_refusal_and_replay_result_unions_are_closed`
- `tests/conformance/test_build0_closeout.py::test_tier2_execution_has_one_output_envelope`
- `tests/conformance/test_build0_closeout.py::test_unavailable_calibration_remains_an_explicit_cited_record`

### `PERSISTENCE_ATOMICITY`

Dependent records and replay capsules commit or roll back as one PostgreSQL transaction

Matched tests: `4`

Source references:
- `src/gptl/core/persistence.py`
- `src/gptl/core/migrations/0004_replay_capsules.sql`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_failure_between_run_and_audit_insert_rolls_back`
- `tests/slices/test_slice_02_candidate_preservation.py::test_database_rejects_incomplete_snapshot_bound_commit`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_write_failure_rolls_back_every_dependent_record`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_capsule_and_run_commit_atomically`

### `PERSISTENCE_APPEND_ONLY`

Database triggers reject mutation, deletion, and truncation of immutable records

Matched tests: `4`

Source references:
- `src/gptl/core/migrations`

Exact passed node IDs:
- `tests/conformance/test_migrations.py::test_published_migrations_are_byte_immutable`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_truncate_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_update_and_delete_of_committed_rows`
- `tests/slices/test_slice_07_replay_integrity.py::test_database_rejects_replay_capsule_mutation`

### `RESTART_CROSS_PROCESS_REPLAY`

Persisted decisions and exact recipes reconstruct after store reopen and in a fresh process

Matched tests: `3`

Source references:
- `src/gptl/mie/replay.py`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_persisted_run_is_readable_from_a_fresh_process`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_process_replay_uses_only_persisted_capsule`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_prior_slice_replays_exactly_after_store_reopen`

### `TAMPER_MISSING_CONTENT_REFUSAL`

Altered, stale, absent, substituted, or non-canonical replay material fails closed

Matched tests: `6`

Source references:
- `src/gptl/core/persistence.py`
- `src/gptl/mie/replay.py`

Exact passed node IDs:
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_run_capsule_substitution_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_noncanonical_replay_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_stale_run_payload_checksum_returns_stored_content_invalid`
- `tests/slices/test_slice_07_replay_integrity.py::test_tampered_replay_capsule_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_bound_content_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_validly_rehashed_output_tamper_is_caught_by_reexecution`

### `PACK_LIFECYCLE_EVOLUTION`

Upgrade, correction, revocation, and supersession affect new runs without rewriting history

Matched tests: `4`

Source references:
- `src/gptl/mie/replay.py`

Exact passed node IDs:
- `tests/slices/test_slice_07_replay_integrity.py::test_correction_creates_new_version_and_run_without_rewriting_history`
- `tests/slices/test_slice_07_replay_integrity.py::test_explicit_pack_evolution_never_resolves_latest`
- `tests/slices/test_slice_07_replay_integrity.py::test_later_attestation_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_07_replay_integrity.py::test_snapshot_bound_discriminator_supersession_replays_exactly`

### `COMPLETION_1_ALL_ACCEPTANCE_GATES`

Every collected Build 0 acceptance and conformance test passes

Matched tests: `302`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#13-build-0-completion-gate`

Exact passed node IDs:
- `tests/conformance/test_build0_closeout.py::test_authoritative_identifiers_are_caller_bound_replay_inputs`
- `tests/conformance/test_build0_closeout.py::test_authoritative_source_does_not_generate_identity`
- `tests/conformance/test_build0_closeout.py::test_authoritative_writes_do_not_upsert_identity`
- `tests/conformance/test_build0_closeout.py::test_preflight_timestamp_width_is_explicitly_policy_bound`
- `tests/conformance/test_build0_closeout.py::test_refusal_and_replay_result_unions_are_closed`
- `tests/conformance/test_build0_closeout.py::test_tier2_execution_has_one_output_envelope`
- `tests/conformance/test_build0_closeout.py::test_unavailable_calibration_remains_an_explicit_cited_record`
- `tests/conformance/test_canonical.py::test_decimal_overflow_is_rejected_by_explicit_policy`
- `tests/conformance/test_canonical.py::test_decimal_uses_explicit_fixed_scale_policy`
- `tests/conformance/test_canonical.py::test_duplicate_keys_after_nfc_normalization_are_rejected`
- `tests/conformance/test_canonical.py::test_float_is_rejected_at_any_depth`
- `tests/conformance/test_canonical.py::test_signed_decimal_zero_has_one_canonical_representation`
- `tests/conformance/test_canonical.py::test_unicode_nfc_variants_have_identical_bytes_and_hashes`
- `tests/conformance/test_completion_evidence.py::test_canonical_wire_schemas_publish_canonical_decimal_semantics`
- `tests/conformance/test_completion_evidence.py::test_canonical_wire_schemas_reject_numeric_decimals`
- `tests/conformance/test_completion_evidence.py::test_cross_minor_divergence_blocks_ready_disposition`
- `tests/conformance/test_completion_evidence.py::test_gate_map_selectors_and_markdown_anchors_resolve`
- `tests/conformance/test_completion_evidence.py::test_generator_identity_is_self_checked`
- `tests/conformance/test_completion_evidence.py::test_package_and_evidence_support_matrices_agree`
- `tests/conformance/test_completion_evidence.py::test_ready_disposition_is_derived_from_self_audit_evidence`
- `tests/conformance/test_completion_evidence.py::test_ready_disposition_rejects_failed_or_incomplete_evidence`
- `tests/conformance/test_completion_evidence.py::test_replay_capsule_wrapper_schema_is_published`
- `tests/conformance/test_completion_evidence.py::test_replay_schema_artifacts_publish_nested_definitions`
- `tests/conformance/test_completion_evidence.py::test_requirement_coverage_includes_every_matrix_row_and_criterion`
- `tests/conformance/test_migrations.py::test_migration_history_must_be_an_exact_packaged_prefix[applied_ids0]`
- `tests/conformance/test_migrations.py::test_migration_history_must_be_an_exact_packaged_prefix[applied_ids1]`
- `tests/conformance/test_migrations.py::test_migration_history_must_be_an_exact_packaged_prefix[applied_ids2]`
- `tests/conformance/test_migrations.py::test_published_migrations_are_byte_immutable`
- `tests/conformance/test_predicates.py::test_incompatible_declared_unit_fails_pack_validation`
- `tests/conformance/test_predicates.py::test_incompatible_runtime_unit_is_invalid`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-FALSE-FALSE-FALSE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-FALSE-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-FALSE-TRUE-FALSE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-FALSE-UNKNOWN-FALSE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-INVALID-FALSE-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-INVALID-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-INVALID-TRUE-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-INVALID-UNKNOWN-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-TRUE-FALSE-FALSE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-TRUE-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-TRUE-TRUE-TRUE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-TRUE-UNKNOWN-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-UNKNOWN-FALSE-FALSE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-UNKNOWN-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-UNKNOWN-TRUE-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[all-UNKNOWN-UNKNOWN-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-FALSE-FALSE-FALSE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-FALSE-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-FALSE-TRUE-TRUE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-FALSE-UNKNOWN-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-INVALID-FALSE-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-INVALID-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-INVALID-TRUE-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-INVALID-UNKNOWN-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-TRUE-FALSE-TRUE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-TRUE-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-TRUE-TRUE-TRUE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-TRUE-UNKNOWN-TRUE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-UNKNOWN-FALSE-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-UNKNOWN-INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-UNKNOWN-TRUE-TRUE]`
- `tests/conformance/test_predicates.py::test_logical_truth_tables_are_exhaustive[any-UNKNOWN-UNKNOWN-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_malformed_closed_ast_is_rejected[payload0-logical predicate has an invalid shape]`
- `tests/conformance/test_predicates.py::test_malformed_closed_ast_is_rejected[payload1-membership terms cannot be empty]`
- `tests/conformance/test_predicates.py::test_malformed_closed_ast_is_rejected[payload2-membership terms must be unique]`
- `tests/conformance/test_predicates.py::test_malformed_closed_ast_is_rejected[payload3-range low cannot exceed high]`
- `tests/conformance/test_predicates.py::test_missing_registered_field_is_unknown_with_no_evidence`
- `tests/conformance/test_predicates.py::test_not_truth_table_is_exhaustive[FALSE-TRUE]`
- `tests/conformance/test_predicates.py::test_not_truth_table_is_exhaustive[INVALID-INVALID]`
- `tests/conformance/test_predicates.py::test_not_truth_table_is_exhaustive[TRUE-FALSE]`
- `tests/conformance/test_predicates.py::test_not_truth_table_is_exhaustive[UNKNOWN-UNKNOWN]`
- `tests/conformance/test_predicates.py::test_numeric_policy_overflow_is_invalid_instead_of_escaping_evaluation`
- `tests/conformance/test_predicates.py::test_range_boundaries_are_explicit[20-EXCLUSIVE-INCLUSIVE-FALSE]`
- `tests/conformance/test_predicates.py::test_range_boundaries_are_explicit[20-INCLUSIVE-INCLUSIVE-TRUE]`
- `tests/conformance/test_predicates.py::test_range_boundaries_are_explicit[30-INCLUSIVE-EXCLUSIVE-FALSE]`
- `tests/conformance/test_predicates.py::test_range_boundaries_are_explicit[30-INCLUSIVE-INCLUSIVE-TRUE]`
- `tests/conformance/test_predicates.py::test_snapshot_bound_unit_conversion_is_used_for_comparison`
- `tests/conformance/test_schema.py::test_conflicting_metadata_for_one_governed_identity_is_rejected`
- `tests/conformance/test_schema.py::test_display_parameter_kind_must_match_registered_kind`
- `tests/conformance/test_schema.py::test_float_cannot_enter_a_decimal_field_by_coercion`
- `tests/conformance/test_schema.py::test_malformed_hash_is_rejected`
- `tests/conformance/test_schema.py::test_malformed_identifiers_are_rejected[audit_event_id-?bad]`
- `tests/conformance/test_schema.py::test_malformed_identifiers_are_rejected[requested_pack_id-]`
- `tests/conformance/test_schema.py::test_malformed_identifiers_are_rejected[run_id-bad id]`
- `tests/conformance/test_schema.py::test_noncanonical_timestamps_are_rejected[2026-02-30T12:00:00.000Z]`
- `tests/conformance/test_schema.py::test_noncanonical_timestamps_are_rejected[2026-06-21T12:00:00.000+00:00]`
- `tests/conformance/test_schema.py::test_noncanonical_timestamps_are_rejected[2026-06-21T12:00:00.00Z]`
- `tests/conformance/test_schema.py::test_noncanonical_timestamps_are_rejected[2026-06-21T12:00:00Z]`
- `tests/conformance/test_schema.py::test_noncanonical_timestamps_are_rejected[2026-06-21T25:00:00.000Z]`
- `tests/conformance/test_schema.py::test_record_versions_are_strict_jcs_safe_integers[9007199254740992]`
- `tests/conformance/test_schema.py::test_record_versions_are_strict_jcs_safe_integers[True]`
- `tests/conformance/test_schema.py::test_required_display_parameter_cannot_be_omitted`
- `tests/conformance/test_schema.py::test_timestamp_policy_context_is_mandatory`
- `tests/conformance/test_schema.py::test_unknown_display_parameter_is_rejected`
- `tests/conformance/test_schema.py::test_unknown_display_template_is_rejected`
- `tests/conformance/test_selection.py::test_overlapping_ungrouped_msa_records_are_invalid_configuration`
- `tests/conformance/test_selection.py::test_selection_group_rank_tie_is_invalid_configuration`
- `tests/conformance/test_selection.py::test_selection_preserves_distinct_ungrouped_records_and_group_winner`
- `tests/conformance/test_source_boundaries.py::test_authoritative_source_has_no_prohibited_runtime_dependencies`
- `tests/conformance/test_source_boundaries.py::test_diagnostic_engine_has_no_domain_numeric_constants_through_slice7`
- `tests/slices/test_slice_01_safe_refusal.py::test_absent_pack_produces_deterministic_preflight_refusal`
- `tests/slices/test_slice_01_safe_refusal.py::test_available_exact_pack_stops_at_later_slice_boundary`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_bound_versions-binding_id-binding.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_citations-citation_id-citation.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_snapshots-None-None]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_late_audit_row_that_exceeds_declared_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_run_without_declared_audit_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_truncate_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[audit]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[run]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_update_and_delete_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_zero_audit_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_documented_demo_runs_against_postgres`
- `tests/slices/test_slice_01_safe_refusal.py::test_duplicate_run_id_is_not_an_idempotent_write`
- `tests/slices/test_slice_01_safe_refusal.py::test_failure_between_run_and_audit_insert_rolls_back`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_empty_migration_history`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_migration_checksum_drift`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-0-WRONG_AUDIT_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-0-WRONG_RUN_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_migrations_are_ordered_checksummed_and_idempotent`
- `tests/slices/test_slice_01_safe_refusal.py::test_persisted_run_is_readable_from_a_fresh_process`
- `tests/slices/test_slice_01_safe_refusal.py::test_postgres_persists_atomic_run_and_audit_across_connections`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_has_no_non_postgres_fallback`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_honors_connection_selected_schema`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_a_well_formed_but_incorrect_decision_hash`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[as_of_time-2026-06-21T12:00:00.001Z-as_of_time mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[decision_hash-ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff-decision hash mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[requested_pack_id-pack.other-requested pack mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[run_id-run.other-run ID mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[sequence-1-sequence must be contiguous]`
- `tests/slices/test_slice_02_candidate_preservation.py::test_backdated_revocation_applies_only_after_its_recorded_time`
- `tests/slices/test_slice_02_candidate_preservation.py::test_database_rejects_incomplete_snapshot_bound_commit`
- `tests/slices/test_slice_02_candidate_preservation.py::test_documented_candidate_preservation_demo_runs_against_postgres`
- `tests/slices/test_slice_02_candidate_preservation.py::test_fully_ratified_candidate_set_reaches_slice_3_boundary`
- `tests/slices/test_slice_02_candidate_preservation.py::test_integrity_failure_precedes_ratification_state_and_candidate_loading`
- `tests/slices/test_slice_02_candidate_preservation.py::test_invalid_pack_returns_configuration_refusal`
- `tests/slices/test_slice_02_candidate_preservation.py::test_pack_version_mismatch_raises_named_binding_error`
- `tests/slices/test_slice_02_candidate_preservation.py::test_ratification_lookup_requires_the_exact_governed_event_identity`
- `tests/slices/test_slice_02_candidate_preservation.py::test_refusal_context_scoping_rejects_cross_boundary_records`
- `tests/slices/test_slice_02_candidate_preservation.py::test_revocation_changes_new_run_without_rewriting_historical_run`
- `tests/slices/test_slice_02_candidate_preservation.py::test_runtime_invalid_applicability_surfaces_candidate_error_and_evidence`
- `tests/slices/test_slice_02_candidate_preservation.py::test_scalar_intake_rejects_multiple_values_for_one_field`
- `tests/slices/test_slice_02_candidate_preservation.py::test_selection_rank_tie_fails_pack_validation`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_binds_every_decision_effective_version`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_bound_run_persists_and_reloads_complete_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_write_failure_rolls_back_every_dependent_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_rejects_output_snapshot_hash_mismatch`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_retains_verified_read_compatibility_with_slice2_v1`
- `tests/slices/test_slice_02_candidate_preservation.py::test_unknown_applicability_is_preserved_and_blocks_negative_conclusion`
- `tests/slices/test_slice_02_candidate_preservation.py::test_unratified_human_input_returns_non_dispositional_advisory`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_calibration_validity_boundaries_are_inclusive_and_policy_bound`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_documented_slice3_demo_runs_against_postgres`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_gate_precedence_stops_before_invalid_downstream_state`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_grouped_msa_precedence_applies_and_ungrouped_overlap_is_invalid`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_stale]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-True-TIER1_DECISION-MISSING_REQUIRED_EVIDENCE-calibration_unavailable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-True-TIER1_DECISION-WITHIN_MEASUREMENT_VARIATION-within_variation]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_invalid_deviation_and_contract_mismatch_fail_closed`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_boundary_uses_snapshot_bound_unit_conversion`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_reason_precedence_is_governed_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[GROUPED_TIE-CONFIGURATION_INVALID-msa_configuration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[INVALID_UNIT-CONFIGURATION_INVALID-msa_configuration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[MISSING-MSA_UNCHARACTERIZED-msa_missing]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NON_TEST_SCOPE-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NOT_APPLICABLE-MSA_UNCHARACTERIZED-msa_not_applicable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[SCOPE_MISMATCH-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNIMPLEMENTED-MSA_UNCHARACTERIZED-msa_unimplemented_class]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNKNOWN-MSA_UNCHARACTERIZED-msa_unknown_applicability]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNQUALIFIED-MSA_UNCHARACTERIZED-msa_unqualified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_outside_variation_returns_open_unassessed_candidates`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_persists_with_explicit_schema_and_reloads_complete_record`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_replay_is_byte_identical[UNAVAILABLE-INVALID_UNIT-deviation1]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_replay_is_byte_identical[VALID-QUALIFIED-deviation0]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binding_rejects_conflicting_runtime_reference`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binds_calibration_msa_scope_capability_and_route_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_test_fixture_msa_cannot_satisfy_a_non_test_scope`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_SUPERSEDED-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[DISALLOWED_ROLE-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[LATE_ATTESTATION_REVOCATION-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ROLE_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_APPROVER-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_AUTHOR-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[VALID-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold0-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold1-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold2-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_contradictory_unsuperseded_results_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_diagnostic_state_hash_has_one_exact_canonical_payload`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_aggregation_is_commutative_over_finite_outcome_domain`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_aggregation_is_invariant_to_result_order`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_result_must_bind_evaluated_observation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_documented_slice4_demo_runs_against_postgres`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta0-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta1-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta2-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_explicit_discriminator_supersession_selects_one_active_result`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_failed_structured_confirm_predicate_blocks_confirmation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_later_recorded_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_referenced_numeric_policy_fails_configuration`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_required_structured_evidence_blocks_confirmation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_supersession_target_fails_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_multiple_active_attestations_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_multiple_active_role_authorizations_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_output_schema_failure_returns_governed_engine_refusal`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_overlapping_discriminator_outcomes_fail_configuration`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_partial_required_signature_evidence_never_aggregates_support`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_authoritative_path_has_no_renderer_dependency`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_snapshot_binds_numeric_policy_confirmation_and_authority`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_structured_confirmation_returns_cited_method_artifact`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_uniquely_dominant_winner_allows_a_second_confirmed_candidate`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_zero_signature_observations_remain_open_unassessed`
- `tests/slices/test_slice_05_honest_negative.py::test_catalog_fraction_below_governed_minimum_remains_indeterminate`
- `tests/slices/test_slice_05_honest_negative.py::test_complete_terminal_catalog_returns_honest_bounded_negative`
- `tests/slices/test_slice_05_honest_negative.py::test_documented_slice5_demo_runs_against_postgres`
- `tests/slices/test_slice_05_honest_negative.py::test_hard_elimination_stops_before_candidate_scoring`
- `tests/slices/test_slice_05_honest_negative.py::test_identical_negative_run_replays_byte_identically`
- `tests/slices/test_slice_05_honest_negative.py::test_missing_terminal_ruling_citation_fails_closed`
- `tests/slices/test_slice_05_honest_negative.py::test_open_unassessed_candidate_blocks_negative_verdict`
- `tests/slices/test_slice_05_honest_negative.py::test_positive_artifact_verdict_has_precedence_over_bounded_negative`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_contract_must_cover_every_published_candidate`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold0-IndeterminateDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold1-KnownArtifactsExcludedDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold2-KnownArtifactsExcludedDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_ruling_citation_intersection_requires_full_governed_identity`
- `tests/slices/test_slice_05_honest_negative.py::test_slice5_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_05_honest_negative.py::test_slice5_snapshot_binds_every_negative_contract`
- `tests/slices/test_slice_05_honest_negative.py::test_unknown_catalog_denominator_refuses_configuration`
- `tests/slices/test_slice_05_honest_negative.py::test_unknown_gap_template_is_configuration_invalid`
- `tests/slices/test_slice_05_honest_negative.py::test_unregistered_policy_directive_is_rejected_at_construction[catalog_boundary]`
- `tests/slices/test_slice_05_honest_negative.py::test_unregistered_policy_directive_is_rejected_at_construction[known_artifacts_excluded_action]`
- `tests/slices/test_slice_05_honest_negative.py::test_unresolved_applicability_blocks_negative_verdict`
- `tests/slices/test_slice_05_honest_negative.py::test_zero_support_without_every_required_discriminator_never_rules_out`
- `tests/slices/test_slice_06_tier2_advisory.py::test_advisory_schema_cannot_carry_verdict_refusal_or_support`
- `tests/slices/test_slice_06_tier2_advisory.py::test_ambiguous_alias_preserves_every_bounded_candidate_without_selecting_method`
- `tests/slices/test_slice_06_tier2_advisory.py::test_authoritative_advisory_path_has_no_model_adapter_surface`
- `tests/slices/test_slice_06_tier2_advisory.py::test_documented_slice6_demo_runs_against_postgres`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[AMBIGUOUS_METHOD-AMBIGUOUS-gap.method-ambiguous-proposed1-measurements1-records1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[MISSING_MSA-RESOLVED-gap.msa-missing-proposed3-measurements3-records3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[STALE_CALIBRATION-RESOLVED-gap.calibration-stale-proposed5-measurements5-records5]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNAVAILABLE_CALIBRATION-RESOLVED-gap.calibration-unavailable-proposed6-measurements6-records6]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNIMPLEMENTED_MSA-RESOLVED-gap.msa-unimplemented-proposed4-measurements4-records4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_APPLICABILITY-RESOLVED-gap.applicability-unknown-proposed7-measurements7-records7]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_METHOD-UNKNOWN-gap.method-unknown-proposed2-measurements2-records2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNRATIFIED_INTAKE-RESOLVED-gap.intake-unratified-proposed0-measurements0-records0]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_equivalent_text_search_accelerator_cannot_change_output`
- `tests/slices/test_slice_06_tier2_advisory.py::test_exact_advisory_query_is_snapshot_bound_and_cited`
- `tests/slices/test_slice_06_tier2_advisory.py::test_identical_advisory_replays_byte_identically`
- `tests/slices/test_slice_06_tier2_advisory.py::test_lexical_normalization_uses_governed_fixed_unicode_data`
- `tests/slices/test_slice_06_tier2_advisory.py::test_lexical_tie_break_replays_across_process_hash_seeds`
- `tests/slices/test_slice_06_tier2_advisory.py::test_non_equivalent_text_search_accelerator_fails_configuration`
- `tests/slices/test_slice_06_tier2_advisory.py::test_rendered_prose_is_separate_and_cannot_modify_advisory_hash`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolved_advisory_preserves_complete_published_candidate_set`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_policy_rejects_an_unimplemented_unicode_data_version`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query0-EXACT-RESOLVED-expected_refs0]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query1-CONTROLLED_TERM-AMBIGUOUS-expected_refs1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query2-RELATIONAL-RESOLVED-expected_refs2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query3-LEXICAL-RESOLVED-expected_refs3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query4-LEXICAL-AMBIGUOUS-expected_refs4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[advisory_bound_refs]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[build_tier2_advisory]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[execute_tier2_advisory]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[normalize_lexical_text]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[resolve_advisory_method]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_tier2_rejects_a_positive_tier1_verdict_before_route_selection`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unexpected_unicode_data_version_fails_closed`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unknown_applicability_evidence_remains_explicit`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unknown_method_remains_explicit_without_candidates`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unregistered_advisory_directive_is_rejected`
- `tests/slices/test_slice_07_replay_integrity.py::test_correction_creates_new_version_and_run_without_rewriting_history`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_process_replay_uses_only_persisted_capsule`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_run_capsule_substitution_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_database_rejects_replay_capsule_mutation`
- `tests/slices/test_slice_07_replay_integrity.py::test_documented_slice7_demo_replays_all_prior_slices`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_documented_demo_requires_an_explicit_database_url`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_prior_slice_replays_exactly_after_store_reopen`
- `tests/slices/test_slice_07_replay_integrity.py::test_explicit_pack_evolution_never_resolves_latest`
- `tests/slices/test_slice_07_replay_integrity.py::test_identical_replay_is_byte_identical`
- `tests/slices/test_slice_07_replay_integrity.py::test_later_attestation_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_07_replay_integrity.py::test_missing_run_returns_governed_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_noncanonical_replay_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_reexecution_exception_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_capsule_and_run_commit_atomically`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_has_no_network_or_implicit_latest_surface`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_policy_reference_mismatch_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_recipe_schema_mismatch_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_run_without_exact_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_snapshot_bound_discriminator_supersession_replays_exactly`
- `tests/slices/test_slice_07_replay_integrity.py::test_stale_run_payload_checksum_returns_stored_content_invalid`
- `tests/slices/test_slice_07_replay_integrity.py::test_tampered_replay_capsule_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_bound_content_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_replay_algorithm_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_validly_rehashed_output_tamper_is_caught_by_reexecution`

### `COMPLETION_2_REQUIREMENT_OWNERSHIP`

Every Build 0 requirement has one implementation slice and executable coverage

Matched tests: `202`

Source references:
- `docs/GPTL_BUILD_PLAN_v0.20.md#12-requirement-ownership-matrix`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_absent_pack_produces_deterministic_preflight_refusal`
- `tests/slices/test_slice_01_safe_refusal.py::test_available_exact_pack_stops_at_later_slice_boundary`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_bound_versions-binding_id-binding.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_citations-citation_id-citation.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_snapshots-None-None]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_late_audit_row_that_exceeds_declared_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_run_without_declared_audit_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_truncate_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[audit]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[run]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_update_and_delete_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_zero_audit_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_documented_demo_runs_against_postgres`
- `tests/slices/test_slice_01_safe_refusal.py::test_duplicate_run_id_is_not_an_idempotent_write`
- `tests/slices/test_slice_01_safe_refusal.py::test_failure_between_run_and_audit_insert_rolls_back`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_empty_migration_history`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_migration_checksum_drift`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-0-WRONG_AUDIT_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-0-WRONG_RUN_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_migrations_are_ordered_checksummed_and_idempotent`
- `tests/slices/test_slice_01_safe_refusal.py::test_persisted_run_is_readable_from_a_fresh_process`
- `tests/slices/test_slice_01_safe_refusal.py::test_postgres_persists_atomic_run_and_audit_across_connections`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_has_no_non_postgres_fallback`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_honors_connection_selected_schema`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_a_well_formed_but_incorrect_decision_hash`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[as_of_time-2026-06-21T12:00:00.001Z-as_of_time mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[decision_hash-ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff-decision hash mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[requested_pack_id-pack.other-requested pack mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[run_id-run.other-run ID mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[sequence-1-sequence must be contiguous]`
- `tests/slices/test_slice_02_candidate_preservation.py::test_backdated_revocation_applies_only_after_its_recorded_time`
- `tests/slices/test_slice_02_candidate_preservation.py::test_database_rejects_incomplete_snapshot_bound_commit`
- `tests/slices/test_slice_02_candidate_preservation.py::test_documented_candidate_preservation_demo_runs_against_postgres`
- `tests/slices/test_slice_02_candidate_preservation.py::test_fully_ratified_candidate_set_reaches_slice_3_boundary`
- `tests/slices/test_slice_02_candidate_preservation.py::test_integrity_failure_precedes_ratification_state_and_candidate_loading`
- `tests/slices/test_slice_02_candidate_preservation.py::test_invalid_pack_returns_configuration_refusal`
- `tests/slices/test_slice_02_candidate_preservation.py::test_pack_version_mismatch_raises_named_binding_error`
- `tests/slices/test_slice_02_candidate_preservation.py::test_ratification_lookup_requires_the_exact_governed_event_identity`
- `tests/slices/test_slice_02_candidate_preservation.py::test_refusal_context_scoping_rejects_cross_boundary_records`
- `tests/slices/test_slice_02_candidate_preservation.py::test_revocation_changes_new_run_without_rewriting_historical_run`
- `tests/slices/test_slice_02_candidate_preservation.py::test_runtime_invalid_applicability_surfaces_candidate_error_and_evidence`
- `tests/slices/test_slice_02_candidate_preservation.py::test_scalar_intake_rejects_multiple_values_for_one_field`
- `tests/slices/test_slice_02_candidate_preservation.py::test_selection_rank_tie_fails_pack_validation`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_binds_every_decision_effective_version`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_bound_run_persists_and_reloads_complete_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_write_failure_rolls_back_every_dependent_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_rejects_output_snapshot_hash_mismatch`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_retains_verified_read_compatibility_with_slice2_v1`
- `tests/slices/test_slice_02_candidate_preservation.py::test_unknown_applicability_is_preserved_and_blocks_negative_conclusion`
- `tests/slices/test_slice_02_candidate_preservation.py::test_unratified_human_input_returns_non_dispositional_advisory`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_calibration_validity_boundaries_are_inclusive_and_policy_bound`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_documented_slice3_demo_runs_against_postgres`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_gate_precedence_stops_before_invalid_downstream_state`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_grouped_msa_precedence_applies_and_ungrouped_overlap_is_invalid`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_stale]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-True-TIER1_DECISION-MISSING_REQUIRED_EVIDENCE-calibration_unavailable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-True-TIER1_DECISION-WITHIN_MEASUREMENT_VARIATION-within_variation]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_invalid_deviation_and_contract_mismatch_fail_closed`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_boundary_uses_snapshot_bound_unit_conversion`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_reason_precedence_is_governed_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[GROUPED_TIE-CONFIGURATION_INVALID-msa_configuration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[INVALID_UNIT-CONFIGURATION_INVALID-msa_configuration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[MISSING-MSA_UNCHARACTERIZED-msa_missing]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NON_TEST_SCOPE-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NOT_APPLICABLE-MSA_UNCHARACTERIZED-msa_not_applicable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[SCOPE_MISMATCH-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNIMPLEMENTED-MSA_UNCHARACTERIZED-msa_unimplemented_class]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNKNOWN-MSA_UNCHARACTERIZED-msa_unknown_applicability]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[UNQUALIFIED-MSA_UNCHARACTERIZED-msa_unqualified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_outside_variation_returns_open_unassessed_candidates`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_persists_with_explicit_schema_and_reloads_complete_record`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_replay_is_byte_identical[UNAVAILABLE-INVALID_UNIT-deviation1]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_slice3_replay_is_byte_identical[VALID-QUALIFIED-deviation0]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binding_rejects_conflicting_runtime_reference`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binds_calibration_msa_scope_capability_and_route_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_test_fixture_msa_cannot_satisfy_a_non_test_scope`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_SUPERSEDED-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[DISALLOWED_ROLE-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[LATE_ATTESTATION_REVOCATION-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ROLE_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_APPROVER-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_AUTHOR-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[VALID-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold0-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold1-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_confirmation_threshold_uses_exact_decimal_boundary[threshold2-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_contradictory_unsuperseded_results_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_diagnostic_state_hash_has_one_exact_canonical_payload`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_aggregation_is_commutative_over_finite_outcome_domain`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_aggregation_is_invariant_to_result_order`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_discriminator_result_must_bind_evaluated_observation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_documented_slice4_demo_runs_against_postgres`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta0-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta1-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_dominance_margin_uses_exact_decimal_boundary[delta2-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_explicit_discriminator_supersession_selects_one_active_result`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_failed_structured_confirm_predicate_blocks_confirmation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_later_recorded_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_referenced_numeric_policy_fails_configuration`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_required_structured_evidence_blocks_confirmation`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_missing_supersession_target_fails_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_multiple_active_attestations_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_multiple_active_role_authorizations_fail_integrity`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_output_schema_failure_returns_governed_engine_refusal`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_overlapping_discriminator_outcomes_fail_configuration`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_partial_required_signature_evidence_never_aggregates_support`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_authoritative_path_has_no_renderer_dependency`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_snapshot_binds_numeric_policy_confirmation_and_authority`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_structured_confirmation_returns_cited_method_artifact`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_uniquely_dominant_winner_allows_a_second_confirmed_candidate`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_zero_signature_observations_remain_open_unassessed`
- `tests/slices/test_slice_05_honest_negative.py::test_catalog_fraction_below_governed_minimum_remains_indeterminate`
- `tests/slices/test_slice_05_honest_negative.py::test_complete_terminal_catalog_returns_honest_bounded_negative`
- `tests/slices/test_slice_05_honest_negative.py::test_documented_slice5_demo_runs_against_postgres`
- `tests/slices/test_slice_05_honest_negative.py::test_hard_elimination_stops_before_candidate_scoring`
- `tests/slices/test_slice_05_honest_negative.py::test_identical_negative_run_replays_byte_identically`
- `tests/slices/test_slice_05_honest_negative.py::test_missing_terminal_ruling_citation_fails_closed`
- `tests/slices/test_slice_05_honest_negative.py::test_open_unassessed_candidate_blocks_negative_verdict`
- `tests/slices/test_slice_05_honest_negative.py::test_positive_artifact_verdict_has_precedence_over_bounded_negative`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_contract_must_cover_every_published_candidate`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold0-IndeterminateDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold1-KnownArtifactsExcludedDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_rule_out_threshold_uses_exact_decimal_boundary[threshold2-KnownArtifactsExcludedDecision]`
- `tests/slices/test_slice_05_honest_negative.py::test_ruling_citation_intersection_requires_full_governed_identity`
- `tests/slices/test_slice_05_honest_negative.py::test_slice5_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_05_honest_negative.py::test_slice5_snapshot_binds_every_negative_contract`
- `tests/slices/test_slice_05_honest_negative.py::test_unknown_catalog_denominator_refuses_configuration`
- `tests/slices/test_slice_05_honest_negative.py::test_unknown_gap_template_is_configuration_invalid`
- `tests/slices/test_slice_05_honest_negative.py::test_unregistered_policy_directive_is_rejected_at_construction[catalog_boundary]`
- `tests/slices/test_slice_05_honest_negative.py::test_unregistered_policy_directive_is_rejected_at_construction[known_artifacts_excluded_action]`
- `tests/slices/test_slice_05_honest_negative.py::test_unresolved_applicability_blocks_negative_verdict`
- `tests/slices/test_slice_05_honest_negative.py::test_zero_support_without_every_required_discriminator_never_rules_out`
- `tests/slices/test_slice_06_tier2_advisory.py::test_advisory_schema_cannot_carry_verdict_refusal_or_support`
- `tests/slices/test_slice_06_tier2_advisory.py::test_ambiguous_alias_preserves_every_bounded_candidate_without_selecting_method`
- `tests/slices/test_slice_06_tier2_advisory.py::test_authoritative_advisory_path_has_no_model_adapter_surface`
- `tests/slices/test_slice_06_tier2_advisory.py::test_documented_slice6_demo_runs_against_postgres`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[AMBIGUOUS_METHOD-AMBIGUOUS-gap.method-ambiguous-proposed1-measurements1-records1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[MISSING_MSA-RESOLVED-gap.msa-missing-proposed3-measurements3-records3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[STALE_CALIBRATION-RESOLVED-gap.calibration-stale-proposed5-measurements5-records5]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNAVAILABLE_CALIBRATION-RESOLVED-gap.calibration-unavailable-proposed6-measurements6-records6]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNIMPLEMENTED_MSA-RESOLVED-gap.msa-unimplemented-proposed4-measurements4-records4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_APPLICABILITY-RESOLVED-gap.applicability-unknown-proposed7-measurements7-records7]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_METHOD-UNKNOWN-gap.method-unknown-proposed2-measurements2-records2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNRATIFIED_INTAKE-RESOLVED-gap.intake-unratified-proposed0-measurements0-records0]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_equivalent_text_search_accelerator_cannot_change_output`
- `tests/slices/test_slice_06_tier2_advisory.py::test_exact_advisory_query_is_snapshot_bound_and_cited`
- `tests/slices/test_slice_06_tier2_advisory.py::test_identical_advisory_replays_byte_identically`
- `tests/slices/test_slice_06_tier2_advisory.py::test_lexical_normalization_uses_governed_fixed_unicode_data`
- `tests/slices/test_slice_06_tier2_advisory.py::test_lexical_tie_break_replays_across_process_hash_seeds`
- `tests/slices/test_slice_06_tier2_advisory.py::test_non_equivalent_text_search_accelerator_fails_configuration`
- `tests/slices/test_slice_06_tier2_advisory.py::test_rendered_prose_is_separate_and_cannot_modify_advisory_hash`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolved_advisory_preserves_complete_published_candidate_set`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_policy_rejects_an_unimplemented_unicode_data_version`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query0-EXACT-RESOLVED-expected_refs0]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query1-CONTROLLED_TERM-AMBIGUOUS-expected_refs1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query2-RELATIONAL-RESOLVED-expected_refs2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query3-LEXICAL-RESOLVED-expected_refs3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_resolver_uses_declared_lane_order_and_stable_governed_tie_break[query4-LEXICAL-AMBIGUOUS-expected_refs4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_persists_explicit_schema_and_complete_payload`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[advisory_bound_refs]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[build_tier2_advisory]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[execute_tier2_advisory]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[normalize_lexical_text]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_slice6_public_functions_declare_their_contract[resolve_advisory_method]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_tier2_rejects_a_positive_tier1_verdict_before_route_selection`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unexpected_unicode_data_version_fails_closed`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unknown_applicability_evidence_remains_explicit`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unknown_method_remains_explicit_without_candidates`
- `tests/slices/test_slice_06_tier2_advisory.py::test_unregistered_advisory_directive_is_rejected`
- `tests/slices/test_slice_07_replay_integrity.py::test_correction_creates_new_version_and_run_without_rewriting_history`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_process_replay_uses_only_persisted_capsule`
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_run_capsule_substitution_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_database_rejects_replay_capsule_mutation`
- `tests/slices/test_slice_07_replay_integrity.py::test_documented_slice7_demo_replays_all_prior_slices`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_documented_demo_requires_an_explicit_database_url`
- `tests/slices/test_slice_07_replay_integrity.py::test_every_prior_slice_replays_exactly_after_store_reopen`
- `tests/slices/test_slice_07_replay_integrity.py::test_explicit_pack_evolution_never_resolves_latest`
- `tests/slices/test_slice_07_replay_integrity.py::test_identical_replay_is_byte_identical`
- `tests/slices/test_slice_07_replay_integrity.py::test_later_attestation_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_07_replay_integrity.py::test_missing_run_returns_governed_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_noncanonical_replay_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_reexecution_exception_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_capsule_and_run_commit_atomically`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_has_no_network_or_implicit_latest_surface`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_policy_reference_mismatch_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_recipe_schema_mismatch_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_run_without_exact_recipe_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_snapshot_bound_discriminator_supersession_replays_exactly`
- `tests/slices/test_slice_07_replay_integrity.py::test_stale_run_payload_checksum_returns_stored_content_invalid`
- `tests/slices/test_slice_07_replay_integrity.py::test_tampered_replay_capsule_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_bound_content_returns_integrity_failure`
- `tests/slices/test_slice_07_replay_integrity.py::test_unavailable_replay_algorithm_fails_closed`
- `tests/slices/test_slice_07_replay_integrity.py::test_validly_rehashed_output_tamper_is_caught_by_reexecution`

### `COMPLETION_3_CANONICAL_REPRODUCTION`

Committed canonical results reproduce byte-identically

Matched tests: `9`

Source references:
- `src/gptl/core/canonical.py`

Exact passed node IDs:
- `tests/conformance/test_canonical.py::test_decimal_overflow_is_rejected_by_explicit_policy`
- `tests/conformance/test_canonical.py::test_decimal_uses_explicit_fixed_scale_policy`
- `tests/conformance/test_canonical.py::test_duplicate_keys_after_nfc_normalization_are_rejected`
- `tests/conformance/test_canonical.py::test_float_is_rejected_at_any_depth`
- `tests/conformance/test_canonical.py::test_signed_decimal_zero_has_one_canonical_representation`
- `tests/conformance/test_canonical.py::test_unicode_nfc_variants_have_identical_bytes_and_hashes`
- `tests/slices/test_slice_05_honest_negative.py::test_identical_negative_run_replays_byte_identically`
- `tests/slices/test_slice_06_tier2_advisory.py::test_identical_advisory_replays_byte_identically`
- `tests/slices/test_slice_07_replay_integrity.py::test_identical_replay_is_byte_identical`

### `COMPLETION_4_MODEL_INDEPENDENCE`

Removing model and renderer adapters cannot alter authoritative structured output

Matched tests: `3`

Source references:
- `tests/conformance/test_source_boundaries.py`

Exact passed node IDs:
- `tests/slices/test_slice_04_artifact_confirmation.py::test_slice4_authoritative_path_has_no_renderer_dependency`
- `tests/slices/test_slice_06_tier2_advisory.py::test_authoritative_advisory_path_has_no_model_adapter_surface`
- `tests/slices/test_slice_06_tier2_advisory.py::test_rendered_prose_is_separate_and_cannot_modify_advisory_hash`

### `COMPLETION_5_SOURCE_BOUNDARIES`

Static scans find no vector/model authority or domain numeric constants in generic modules

Matched tests: `2`

Source references:
- `src/gptl`

Exact passed node IDs:
- `tests/conformance/test_source_boundaries.py::test_authoritative_source_has_no_prohibited_runtime_dependencies`
- `tests/conformance/test_source_boundaries.py::test_diagnostic_engine_has_no_domain_numeric_constants_through_slice7`

### `COMPLETION_6_RESEARCH_ONLY_OUTPUT`

Build 0 outputs remain non-dispositional, non-record-of-record, and RESEARCH_ONLY

Matched tests: `11`

Source references:
- `src/gptl/mie/schema.py`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_absent_pack_produces_deterministic_preflight_refusal`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_structured_confirmation_returns_cited_method_artifact`
- `tests/slices/test_slice_05_honest_negative.py::test_complete_terminal_catalog_returns_honest_bounded_negative`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[AMBIGUOUS_METHOD-AMBIGUOUS-gap.method-ambiguous-proposed1-measurements1-records1]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[MISSING_MSA-RESOLVED-gap.msa-missing-proposed3-measurements3-records3]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[STALE_CALIBRATION-RESOLVED-gap.calibration-stale-proposed5-measurements5-records5]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNAVAILABLE_CALIBRATION-RESOLVED-gap.calibration-unavailable-proposed6-measurements6-records6]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNIMPLEMENTED_MSA-RESOLVED-gap.msa-unimplemented-proposed4-measurements4-records4]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_APPLICABILITY-RESOLVED-gap.applicability-unknown-proposed7-measurements7-records7]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNKNOWN_METHOD-UNKNOWN-gap.method-unknown-proposed2-measurements2-records2]`
- `tests/slices/test_slice_06_tier2_advisory.py::test_each_ineligible_case_returns_typed_nonverdict_advisory[UNRATIFIED_INTAKE-RESOLVED-gap.intake-unratified-proposed0-measurements0-records0]`

### `COMPLETION_7_FIXTURE_LABELING`

Synthetic/reference evidence remains honestly scoped and cannot imply production fidelity

Matched tests: `2`

Source references:
- `src/gptl/slice3_fixture.py`

Exact passed node IDs:
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_snapshot_binds_calibration_msa_scope_capability_and_route_policy`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_test_fixture_msa_cannot_satisfy_a_non_test_scope`

### `COMPLETION_8_SCOPE_ISOLATION`

TEST_FIXTURE MSA and evidence cannot satisfy another scope

Matched tests: `3`

Source references:
- `src/gptl/mie/msa.py`

Exact passed node IDs:
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[NON_TEST_SCOPE-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_msa_failure_routes_are_explicit_and_stop_before_candidates[SCOPE_MISMATCH-MSA_UNCHARACTERIZED-msa_scope_mismatch]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_test_fixture_msa_cannot_satisfy_a_non_test_scope`

### `COMPLETION_9_GOVERNED_CONFIRMATION_ROUTING`

Confirmation, ratification, calibration, MSA, and display-template gates are fail-closed

Matched tests: `18`

Source references:
- `src/gptl/mie/diagnostics.py`
- `src/gptl/mie/calibration.py`

Exact passed node IDs:
- `tests/conformance/test_schema.py::test_unknown_display_template_is_rejected`
- `tests/slices/test_slice_02_candidate_preservation.py::test_ratification_lookup_requires_the_exact_governed_event_identity`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[INVALID-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_invalid]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[STALE-True-TIER1_DECISION-STALE_OR_INVALID_CALIBRATION-calibration_stale]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[UNAVAILABLE-True-TIER1_DECISION-MISSING_REQUIRED_EVIDENCE-calibration_unavailable]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-False-TIER2_ADVISORY-ADVISORY_NO_VERDICT-intake_unratified]`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_intake_calibration_matrix_has_one_deterministic_route[VALID-True-TIER1_DECISION-WITHIN_MEASUREMENT_VARIATION-within_variation]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ATTESTATION_SUPERSEDED-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[DISALLOWED_ROLE-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[LATE_ATTESTATION_REVOCATION-METHOD_ARTIFACT]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[ROLE_REVOKED-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_APPROVER-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[SEPARATION_AUTHOR-INDETERMINATE]`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_attested_confirmation_enforces_authority_and_lifecycle[VALID-METHOD_ARTIFACT]`

### `COMPLETION_10_PERSISTENCE_CONTRACT`

Atomicity, append-only, checksum, schema, recovery, and record-set constraints pass

Matched tests: `35`

Source references:
- `src/gptl/core/persistence.py`
- `src/gptl/core/migrations`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_absent_pack_produces_deterministic_preflight_refusal`
- `tests/slices/test_slice_01_safe_refusal.py::test_available_exact_pack_stops_at_later_slice_boundary`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_bound_versions-binding_id-binding.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_citations-citation_id-citation.fabricated]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_fabricated_preflight_bindings[gptl_snapshots-None-None]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_late_audit_row_that_exceeds_declared_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_run_without_declared_audit_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_truncate_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[audit]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_unknown_hash_algorithm[run]`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_update_and_delete_of_committed_rows`
- `tests/slices/test_slice_01_safe_refusal.py::test_database_rejects_zero_audit_count`
- `tests/slices/test_slice_01_safe_refusal.py::test_documented_demo_runs_against_postgres`
- `tests/slices/test_slice_01_safe_refusal.py::test_duplicate_run_id_is_not_an_idempotent_write`
- `tests/slices/test_slice_01_safe_refusal.py::test_failure_between_run_and_audit_insert_rolls_back`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_empty_migration_history`
- `tests/slices/test_slice_01_safe_refusal.py::test_initialize_rejects_migration_checksum_drift`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-0-WRONG_AUDIT_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[audit-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-0-WRONG_RUN_TYPE-record type mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_load_rejects_incorrect_persisted_metadata[run-1-wrong.schema-schema version mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_migrations_are_ordered_checksummed_and_idempotent`
- `tests/slices/test_slice_01_safe_refusal.py::test_persisted_run_is_readable_from_a_fresh_process`
- `tests/slices/test_slice_01_safe_refusal.py::test_postgres_persists_atomic_run_and_audit_across_connections`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_has_no_non_postgres_fallback`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_honors_connection_selected_schema`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_a_well_formed_but_incorrect_decision_hash`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[as_of_time-2026-06-21T12:00:00.001Z-as_of_time mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[decision_hash-ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff-decision hash mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[requested_pack_id-pack.other-requested pack mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[run_id-run.other-run ID mismatch]`
- `tests/slices/test_slice_01_safe_refusal.py::test_store_rejects_audit_records_not_bound_to_the_decision[sequence-1-sequence must be contiguous]`
- `tests/slices/test_slice_02_candidate_preservation.py::test_snapshot_write_failure_rolls_back_every_dependent_record`
- `tests/slices/test_slice_02_candidate_preservation.py::test_store_rejects_output_snapshot_hash_mismatch`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_capsule_and_run_commit_atomically`

### `COMPLETION_11_HISTORICAL_REPLAY`

Replay uses original bound state and never live/latest state

Matched tests: `4`

Source references:
- `src/gptl/mie/replay.py`

Exact passed node IDs:
- `tests/slices/test_slice_07_replay_integrity.py::test_cross_process_replay_uses_only_persisted_capsule`
- `tests/slices/test_slice_07_replay_integrity.py::test_explicit_pack_evolution_never_resolves_latest`
- `tests/slices/test_slice_07_replay_integrity.py::test_later_attestation_revocation_changes_new_run_not_historical_replay`
- `tests/slices/test_slice_07_replay_integrity.py::test_replay_has_no_network_or_implicit_latest_surface`

### `COMPLETION_12_DOCUMENTED_DEMOS`

Every documented slice demonstration executes against explicit PostgreSQL

Matched tests: `7`

Source references:
- `scripts/run_slice.py`

Exact passed node IDs:
- `tests/slices/test_slice_01_safe_refusal.py::test_documented_demo_runs_against_postgres`
- `tests/slices/test_slice_02_candidate_preservation.py::test_documented_candidate_preservation_demo_runs_against_postgres`
- `tests/slices/test_slice_03_msa_calibration_gate.py::test_documented_slice3_demo_runs_against_postgres`
- `tests/slices/test_slice_04_artifact_confirmation.py::test_documented_slice4_demo_runs_against_postgres`
- `tests/slices/test_slice_05_honest_negative.py::test_documented_slice5_demo_runs_against_postgres`
- `tests/slices/test_slice_06_tier2_advisory.py::test_documented_slice6_demo_runs_against_postgres`
- `tests/slices/test_slice_07_replay_integrity.py::test_documented_slice7_demo_replays_all_prior_slices`

### `COMPLETION_13_EVIDENCE_MANIFEST`

The closeout generator validates mappings and derives all result state from executed artifacts

Matched tests: `11`

Source references:
- `scripts/generate_build0_completion_evidence_v1_4.py`
- `docs/evidence/BUILD0_GATE_MAP_v1.4.json`

Exact passed node IDs:
- `tests/conformance/test_completion_evidence.py::test_canonical_wire_schemas_publish_canonical_decimal_semantics`
- `tests/conformance/test_completion_evidence.py::test_canonical_wire_schemas_reject_numeric_decimals`
- `tests/conformance/test_completion_evidence.py::test_cross_minor_divergence_blocks_ready_disposition`
- `tests/conformance/test_completion_evidence.py::test_gate_map_selectors_and_markdown_anchors_resolve`
- `tests/conformance/test_completion_evidence.py::test_generator_identity_is_self_checked`
- `tests/conformance/test_completion_evidence.py::test_package_and_evidence_support_matrices_agree`
- `tests/conformance/test_completion_evidence.py::test_ready_disposition_is_derived_from_self_audit_evidence`
- `tests/conformance/test_completion_evidence.py::test_ready_disposition_rejects_failed_or_incomplete_evidence`
- `tests/conformance/test_completion_evidence.py::test_replay_capsule_wrapper_schema_is_published`
- `tests/conformance/test_completion_evidence.py::test_replay_schema_artifacts_publish_nested_definitions`
- `tests/conformance/test_completion_evidence.py::test_requirement_coverage_includes_every_matrix_row_and_criterion`

## Coverage and Cross-Minor Equality

- Requirement ownership rows covered: `28`
- Completion criteria covered: `13`
- Cross-minor canonical fixture corpus identical: `True`
- Cross-minor canonical fixture corpus SHA-256: `b4db3ed4d3ebedfc275c505d4abeb1279c38df850c0eeb0dedc9b26b7f1eba51`

## Canonical Artifact Samples

### `SAFE_REFUSAL`

- Run ID: `run.slice1.safe-refusal`
- Output kind: `TIER1_DECISION`
- Output payload SHA-256: `315af6e8c4bd5b03fa8747e1e7ebffdeecbd01303371f049933b988132ae341b`
- Decision/advisory hash: `41a41a3d3e171f65dd509de228dee114b2e2375282388392fe51330f3666c995`
- Snapshot SHA-256: `None`
- Audit payload hashes: `["0ce690cd24f99080742e942fc0ded2fdc004021b3e119c47fb283fadc063d1fa"]`
- Citation payload hashes: `[]`
- Bound-version payload hashes: `[]`

### `CANDIDATE_PRESERVATION`

- Run ID: `run.slice2.slice7-replay`
- Output kind: `TIER1_DECISION`
- Output payload SHA-256: `a5fa9f6721f1e495e0ad72c0db253447f0a8f81be9c47f762078ba81b646f9d5`
- Decision/advisory hash: `545dc05e0ff8933e40dc635e21f246d1e9a1c98504dcd773a39611958ecb7745`
- Snapshot SHA-256: `220ff5099cec6b15817ded35ac9b1409fa54465ed7eb1e6b5fa95147364a302f`
- Audit payload hashes: `["3f5d4982e655528fabcc0d436fd02a8ad4cfcdd0bb9bd33e91a366440122e297"]`
- Citation payload hashes: `["86667e3bf1fe7ad5349e88b96b79af697ef6072d0d1d1d7b3dbe6cee1a3339e4"]`
- Bound-version payload hashes: `["01dab0eda904dfc94a5bf8d38c15002e0e39db037ed5b961798a872850f77def", "02f25da3bc2a53d60290ac40c70f21b58e0590803ebbe127af215f9a7d958d87", "041e2dc72ab73f0e401aabb20d4b6ce813192b66dae6e92d1f65b28f56a20d2f", "04835ccbe3a44cd26cca809a86017e70c5a805d45a0411949d7b44850683ec01", "073b3f6d4f12d724df91ac8d5d5793ebee3531a9ce257cd1f50595d475459e9d", "09dc8d7409042946bb41a0f364ee109452242b22e2d9b8483eaa2ac4da8a5001", "0d6c75552847c40739050113b170ed50a9356b938637e82fcce7ad428d29fcdb", "11fd49ea73d264ebb770f6c2593484822ae24d67a35e7172256d6d8fedf65c4a", "17dc3817f3c6c1c608bf5009aa400793ad7141403b6a78bd8019183b41cd21fd", "1ffa707603a82229faaff305b379a2d50b1d3f944131dc3c73f20e8bfeacb904", "46dc58609bec8c0a57c6a70fd4471bc3cf506b4490042ccf5bb7a0d0bcccbcd3", "4af58db843ba4e0cfb7c98b923663658767415406c90d1064ea104a8b3fd0843", "584cba229d76a91788fa95bb2f5815862e9f37d8b1f95e4bb4fab23e4f1008c9", "5f5d50f914a0cd5e84a59129fddd6091c161cd22aec3efad6dfbc9b9e2e82d4d", "63587c04430e3183b8af4d08c342afd377f48507a37f439667b776b247172b71", "7241af769419ff4b1307050bfee67e5752ffde0438e9d93dbcbba9bf5985db88", "7d6796e5f74c47d561337d5419e15aaf14a69e392855b51c2d3b6c3b007c84e0", "807a8625111f90f06e1645750caadb3bffc94da53762d1475f79b83354ba146a", "81b3e22253a123d1fec2de4663d6409071c8d106f11b03693d3ca626828d6d46", "8409ac5b3a86ab663351ebf3ccaad0e9ecb6e4eab8fe988c61344331bcdfc575", "8d482c3e6cd5a539673c28763da02b21d5f22e189e4dce3f0fbad1ffcc554cbe", "9a186db7e92af40e8e4bc41e717aff60f3aca63f5bd45234c9f04c21b8a3a117", "9dff0c5dec65088799f62a0d148fb157835d5e2051467a654e90d95cce2f1e5d", "9e3120b076bd73240105b4de4bc5b6cdf1791d165694383cbdedd764668b6ee4", "a06405d9dca9e78d49fac15522fc4ceca3519ef13ef6befb4b10967636a0976e", "a212fe60d1e433eebb22ed9edabaa014c46d99cdc108d5a690699c1161122428", "b5de2778fdaba130bd1fa81b605d1be59b2baa9f2ad54548df3488e2c6651480", "bb4939d5ab9cd22d83ed16e9e717d79760c0c42e6952e0b0c89589579663c109", "bf67d4f2595a7feaa0161c9fa066187a18055718c7ac025cc31e1bf68a3ed5aa", "c1334f0b7d5fe10ad3937fd282e69bf00348020d3ec28d4dee3ebd8035fe0eca", "c434e61e466aa593aa0582b75e794b67f6197235566eebd5f99da07e35068356", "c4f19cf06cdbabd7dc0cd16ee42aeb9da3460cc1616e97b41ca4f8f340c98a5b", "c5169e5b6f42afbd441131de67c0b64c5f658be5b2e2d411eea39c612e22affd", "dc26f7b29b6ae88027569a39e8f71b7e8abef7362341ef41f9e2e57d74b6d1f4", "e1c6ca6f9548e2d4fc135fbda7e8e0935e78c68a0461054844a92720fa549a2f", "e276f6bb8c597065bd15bcaa26d4229b7981bd1b2f7e72b7221f12d6232fc98f", "e4c9686133bbd55c06f941b1b90e908166941172c32c1edacff856b6d1b92186", "e5336b343b4d93d997d89b2c5345eecde072aae68b19bada24733791c8b1c5a9", "e562e578c6c61d1588b9d0aadacaef8684e4393f5f48cb210cfc66b90141af0c", "f68e3e60bd9ec2aeeaeba442c8f1f41e9d609a57b1fec0046e977f6244891459", "fe718adeb78f5f177a0cc2521eba9368ad618ff190ff1922e7bea4b745cd533d"]`

### `MSA_GATE`

- Run ID: `run.slice2.slice3-slice7-replay`
- Output kind: `TIER1_DECISION`
- Output payload SHA-256: `0f7ee0d8a1378e34661f5f011861ebdfaabf05b1d7c2f588fabcebaea6f7b497`
- Decision/advisory hash: `cb711fc565552f2a9dfec9fddb0abb5b3d3ff20c9dae25ec9855a43fe6a57abd`
- Snapshot SHA-256: `60c797a39f1691b61f8c70fb4b1ca4a489eb83ebc83b38e35b8e0e14975e45e3`
- Audit payload hashes: `["3e308b396df6e54b40f7cc2e87a2c55aa78076a66a3e4f97b4bd3246e604f1e6"]`
- Citation payload hashes: `["524d1ec7af3b4234354c20106808126a1df3e352bf7d629404328e7b13d5533a", "d07d6aca178a4f5d97f2c8f1463f77427ad8801caee496c59ecaa0240181d9cc"]`
- Bound-version payload hashes: `["004bebcaf040b1357ea5e808160d25877d9b20e9aac902dff2e1d85f4d5392e9", "01dab0eda904dfc94a5bf8d38c15002e0e39db037ed5b961798a872850f77def", "02f25da3bc2a53d60290ac40c70f21b58e0590803ebbe127af215f9a7d958d87", "041e2dc72ab73f0e401aabb20d4b6ce813192b66dae6e92d1f65b28f56a20d2f", "04835ccbe3a44cd26cca809a86017e70c5a805d45a0411949d7b44850683ec01", "073b3f6d4f12d724df91ac8d5d5793ebee3531a9ce257cd1f50595d475459e9d", "09dc8d7409042946bb41a0f364ee109452242b22e2d9b8483eaa2ac4da8a5001", "0d679798551732e34240edd7eb13d2b4060709051c9f6a175d51a704d73651e3", "0d6c75552847c40739050113b170ed50a9356b938637e82fcce7ad428d29fcdb", "11fd49ea73d264ebb770f6c2593484822ae24d67a35e7172256d6d8fedf65c4a", "165f1f0bd94bbb32cc95281be07b61dfa8a881b77b0174a137d6bd00cc8645d6", "17dc3817f3c6c1c608bf5009aa400793ad7141403b6a78bd8019183b41cd21fd", "1f971823d164e1cb72fab613017817154865cde7c1ff7f24e7f2f7d6ee469ae9", "1ffa707603a82229faaff305b379a2d50b1d3f944131dc3c73f20e8bfeacb904", "26d018f09c37edda9dec1693afc07c83e777064760ba81f435453552b4907f0e", "277660d9e53044891aa754c330fdfdd652eae5efc59d715391a3ac41ea5a52b6", "30723ff0a8d8a511ed7ca1fe9643029507d9e2ac31e08d24a954a64e35aa3273", "31a33ac586ca1a1446e15b9218175c0e9298daeac0b224853bb1125284cf827a", "350cbd83085385b9c9be5bb8de677050902d3d059566636afc23163c83e9088f", "3d60e44073efb0c894fbef74624c7a5757791280b433dcd0cc00e796997e99eb", "46dc58609bec8c0a57c6a70fd4471bc3cf506b4490042ccf5bb7a0d0bcccbcd3", "584cba229d76a91788fa95bb2f5815862e9f37d8b1f95e4bb4fab23e4f1008c9", "5a2485bc6eb991b5bdc7980f5572b215d3c25153aa6df2d02f13deebbab00cb5", "5f5d50f914a0cd5e84a59129fddd6091c161cd22aec3efad6dfbc9b9e2e82d4d", "63587c04430e3183b8af4d08c342afd377f48507a37f439667b776b247172b71", "671b4376cd7b2126e7375a3e8de7a67d4b9d42f063726c8aa3cf162617ebeecc", "7241af769419ff4b1307050bfee67e5752ffde0438e9d93dbcbba9bf5985db88", "799547518ed9bc5fdd13f7ba56fc6e27d8839a2d3d87dc5ff2e9e7b167833c25", "8409ac5b3a86ab663351ebf3ccaad0e9ecb6e4eab8fe988c61344331bcdfc575", "89b8b982cfe614149ae76235f00b99534d751f44440a169e9e5548fb635d877a", "8d482c3e6cd5a539673c28763da02b21d5f22e189e4dce3f0fbad1ffcc554cbe", "99a539b21b0ca3a973e996b7e2ee58fc72759e3c0d55d35e24679daee491a966", "9a186db7e92af40e8e4bc41e717aff60f3aca63f5bd45234c9f04c21b8a3a117", "9b6da3431daae3e618f6b07c268ff5d3af667c9426f203015215eba294e50f24", "9ca623715b821e7d5ea368170340488f3382f4956bf25c98c5993f44879ebd16", "9dff0c5dec65088799f62a0d148fb157835d5e2051467a654e90d95cce2f1e5d", "9e3120b076bd73240105b4de4bc5b6cdf1791d165694383cbdedd764668b6ee4", "a212fe60d1e433eebb22ed9edabaa014c46d99cdc108d5a690699c1161122428", "b15e33e6c563f7039194a7c1e2b780f29c56f65da223ec408a06ee2ca3ef5b52", "b2e436d4acba3b0c6888e684501e61c4af7f27fabba3d333941b6365f4db451a", "b5de2778fdaba130bd1fa81b605d1be59b2baa9f2ad54548df3488e2c6651480", "bb4939d5ab9cd22d83ed16e9e717d79760c0c42e6952e0b0c89589579663c109", "be8233a572fc427ff5bcc2f386a5d229d7c66af2fd46f8042d6e7b0422dc621a", "c1334f0b7d5fe10ad3937fd282e69bf00348020d3ec28d4dee3ebd8035fe0eca", "c4f19cf06cdbabd7dc0cd16ee42aeb9da3460cc1616e97b41ca4f8f340c98a5b", "c5169e5b6f42afbd441131de67c0b64c5f658be5b2e2d411eea39c612e22affd", "d679cd5370ee5c5abf61496971f75063f0e1145a477d8dd2bcbd73139badcc28", "d7b24c622540b4715297b66b3f5ffe84843786fb0b7738259917a27a9599f3b2", "d7b4e42ed69e561af8a12382d3af241495d2efd3ac6438678b5f608a8744987c", "dc26f7b29b6ae88027569a39e8f71b7e8abef7362341ef41f9e2e57d74b6d1f4", "def2ceddcbb98ec8fe82aa9f215ebbd4b0c096a727a1f35444d8f34c73d60e58", "e011b85461a2fcd31614602bd229b2aaa66e7ecf24dcdace8c2e852578042396", "e1c6ca6f9548e2d4fc135fbda7e8e0935e78c68a0461054844a92720fa549a2f", "e276f6bb8c597065bd15bcaa26d4229b7981bd1b2f7e72b7221f12d6232fc98f", "e5336b343b4d93d997d89b2c5345eecde072aae68b19bada24733791c8b1c5a9", "e562e578c6c61d1588b9d0aadacaef8684e4393f5f48cb210cfc66b90141af0c", "f03bba415ffb7890f631bf00ec049f73b33aed026121b4220da263d3f84a5fdb", "f03f1c185520a1c0a0e0527e9698166880d1774c7940bafe17bc9718395a822d", "f1bae80e2ed1fd347334853c1ed9015e4d9330bf4a84560f8dc3a61f70efb12b", "f1f7e1114242feec5819bbadd37b8e1ed4b9947c461939580073333742c99088", "f29d827b62f31d405662141a929321ef55b9e4ae36debb5240555631a4d3ad79", "f68e3e60bd9ec2aeeaeba442c8f1f41e9d609a57b1fec0046e977f6244891459", "f9bd60ac116381ad711996a82864fc17512a82b7705ef8cd73e072efb7f474b8", "fd14d07364a83521fdc0f203a8186ece7449946b0b76cd5859dfef7454e0539a", "fe718adeb78f5f177a0cc2521eba9368ad618ff190ff1922e7bea4b745cd533d"]`

### `ARTIFACT_CONFIRMATION`

- Run ID: `run.slice4.slice7-replay`
- Output kind: `TIER1_DECISION`
- Output payload SHA-256: `4ba6cf223efdffb04a50f19c40efec11b78b7e8b8612f42b2244e67f996a04a1`
- Decision/advisory hash: `fb609a3145d6633f231b987a9edcf690d82b45805a9fa09fa413232051ac3dab`
- Snapshot SHA-256: `90b9e23bc55ea5ab90b11ec400d5bbb8c7cc8a12019ffab92011245b382f2219`
- Audit payload hashes: `["c7b1c1a4129df67c532fa2d5cdebb8ac1e31b9646798a7fb07db027fc2c380ff"]`
- Citation payload hashes: `["0005f610d2707d5cd853eb3affe91f6bd13fda9cd9f546275b786477d4421428", "0b54754f86c28887b98aa9b968ef1284d87783376551cf128f7acbd240479f5d", "0f999310d118c7f5f05ec9ededfecf72fe4f7d4cda742770d5972bd00d0696b2", "2ec4e23b1ca3271ada39a5158f7fbf947f52d49ccb943749674ffa1a167a256e", "355b889a3eff1b3cf2919fbf5d079203ee4872c6c620b4124b4faa0155a2871b", "3845f2565b5f22b605f5fbc46a3579f8fdf9ea1e255505ee0ddefea2eee3366c", "393e77ff6c48dd12c420846d1a862d6e5e4dd06151f0538f5541c7f653203dcd", "39792ee56ba83d8e549fb3b84e37e5b6711b5a9235179413c35ceaf07eefdda6", "5058f9f624b21b712232d2d079c2c522ab2933c629fc369dd13e6110bf1bcfec", "524d1ec7af3b4234354c20106808126a1df3e352bf7d629404328e7b13d5533a", "582b1e4a7a0076034224d585e8d0aaf48026560714886fae363f69fa68a07531", "6d3f6d979863932d4eb02d3c2827f41c0a610f3181583eed8a4dcb1443ceb536", "715fa449bd56f686d88a369ba7574f0769733eb07143ed7a60ad25b9508190c2", "84635e18fab1400caa8417b7d534f30c93010ff7a558498b1add18a96ceb542b", "89e9db8dd2134acd41e66861bceb812fa8805ffc0667d9162d8c8c0fcaea7bad", "9723add51c785e470ea4e171098fd972045bb8f4fa7d87d7fd5414b11a026958", "975e2a64c85b83a2240ae4dcf238d7a730fc17186625911b93d5f7fa45073498", "9c998f499b412dfc4fd751aed467fb1219c52797d04195af8c61ea7e1d200210", "a3c7ff85c1caf746889e56f8cff89f80954de3957745eb592235030dfa01c35c", "b23d91d98f706456e33c637b4d5f9219c1dd35783a4b45cf345493ca94a255e4", "bfd21b15e0a4649e2c76634946f582939859843966e076015b97719ed90a231f", "c38e6bd63757ee4c55d1c33deb8dea5e57f6b237991491a9bd7ddbb2adee57b9", "d07d6aca178a4f5d97f2c8f1463f77427ad8801caee496c59ecaa0240181d9cc", "dedc95da41f60f1c9dbbd5b5f1d336ffd789873ec59e5f1d09c898f6a81c97d2"]`
- Bound-version payload hashes: `["004bebcaf040b1357ea5e808160d25877d9b20e9aac902dff2e1d85f4d5392e9", "005de12463d8d62111fb707d13e3261406127fd0c8362915f3dd46e7a24a17b6", "0ad336a922fa439f676c1c844ae8bc82e4ceff4852bb7f3f3af160915aab4280", "0d679798551732e34240edd7eb13d2b4060709051c9f6a175d51a704d73651e3", "0d6c75552847c40739050113b170ed50a9356b938637e82fcce7ad428d29fcdb", "0e542c2cc14404e07084d4ae97127925d5a7b092eb5ce1bf0fab6436a6d921a6", "11fd49ea73d264ebb770f6c2593484822ae24d67a35e7172256d6d8fedf65c4a", "139da5cb233e126676d9976d977458a3871cb8429ba18421481dc05e9ed7a704", "165f1f0bd94bbb32cc95281be07b61dfa8a881b77b0174a137d6bd00cc8645d6", "1a8dfb275f6153a5ce6b957c81c490536a0232fb9c56cff0c114c29c1ed7e5fd", "1aa433f04906604f33244dfff1f2eb6e7ad3b590fb04037bf44d9a4a492ef7a5", "1c2d49bf0b1a68b5a5ac8bb5fba95f128c45420e31d4620a9a49ad7efc7d8eac", "1c6cb895e9324474e1dcf488c0e06cfa7b808e678b7c0a703afd9b703af901d6", "1f07f48dd61d015cab226cc473b1f0668c14f9e7a4d4d33a14d5bb77e7589314", "1f971823d164e1cb72fab613017817154865cde7c1ff7f24e7f2f7d6ee469ae9", "20b8b661de3ff24ec24360a14fc2d31f3bd159ad6786066062b62706fc86fc1e", "215fd2df0d7139fda263d07fc67ac4e7828b16f523164dd5320588da914b37fe", "2206389cb876531faec08f368b0c19c13f4e114f49b747a4c6ad09ba205b0211", "222beee27f6f5d84c91c1d6072b2667f4f8feac41eb74617a5ae6a21994ccee4", "22e5f7715e3c7d25a5d47a77f339e130763d4ff916652d508d140274ca0bd0ac", "259524d810bdd9dac2dad92b5cd7da9ed0cb52550a39c9dc95dc134c2f8fba8f", "26e6889774291bcee903ecfeefe96f5f50465cd1a183d9677e080f927d47afe3", "277660d9e53044891aa754c330fdfdd652eae5efc59d715391a3ac41ea5a52b6", "2a755c1bc39b3a8b84b4751cdaeff3a84939617ceec71ce4e20c267137a40665", "2b3ff6221d8b4770a9a3677804eb523ffdf069bd2cdcabb41274d80558591768", "304f87eb851d24f2f903dbf30a6f2d9addd6a35a5c6d816fd27badabd0207dd0", "30723ff0a8d8a511ed7ca1fe9643029507d9e2ac31e08d24a954a64e35aa3273", "309733723683e740a07dba36979fe667fac04961a7dab06d6f21c381c4b04bd4", "31a1562c6cda57a95b3d4abc28e8e08487d48e4d21309adc245b8cc3cf964a02", "31e00025251f7b3513dbfa05577e72cd3c208c9f0682020bfc0f61f77ab698a2", "38bb602999ab7c822d64309556581951357427d5b106ba384672f2578c51f17e", "3a4ed3739528d1c449d5cb0d8d228690b57054afb7a96e2f6125a4ff9e2c0ada", "3d60e44073efb0c894fbef74624c7a5757791280b433dcd0cc00e796997e99eb", "3d7d3574befd27553fd3301c03a5e94acd67f874222723c04950157504ff7c0d", "3e71ed490e332706deae4f1ae83da31d7bed431414cc0897a82d60fae3f7a025", "4367bad683058617ffc5cdb007d6d385137b9b52d6c6836ae70323a89a30ab2e", "463025b02e8538e3dabbbe65da4ebe7db12b9eac9bb1c650b2c11cf50144b60e", "467ecf05e7b9ae61fc72ed6c2461f4954d8c4e3099b383eda5ed67252d3f0303", "46cfb73d720e7fd0c7957bd85b346d72450e3fe586f76448b59a134413f74dfd", "4dc528597c61b548776998d965ba05b6acc72fddf7a9b809228029060e730954", "4ff442ab861d3a7e41d7b03044c0fa5277fad53984af1daa9e9d8b1a7baead59", "51845eef6abd85da11acd77b758b08cf1185788eaad762c50eab6a35c8cc1154", "528dcc2a8059b2283b79da2a49bdf493c6ffc6ce6fb9c4e81401d4ac8ef29fbd", "57ef7dccdebfacbcabf51ebb92966f9b3c58273d8adf382ec012e5a4ca353e3a", "5a2485bc6eb991b5bdc7980f5572b215d3c25153aa6df2d02f13deebbab00cb5", "5b5e40508f7e130260e42f070c0ade3527dd246a74afdad4bdb39b3621cf82cb", "5c5213b6ce9e0117e6bad7dc2a9059be5aa2a717f8b573a6e8d3c7af0f0ae922", "5e79e72cab4fdfd63d852c7a6734c6d6b254b9e974815a510bab16630c451426", "6bf35e65468030e0bee2c5791514d67df76763161e6db50fdcbff3a36effc779", "6d712eb7024f55458b4143700af18ba167d9ec7fd9555a84bdd58425485bc344", "6ecb64055c7bcd870c594a9db94eec5e6a3edbec94358117f4a05ec94c2ed146", "6f7b1e9a78e7fa080b888633639dbd036be0c3351e85169e878971d0627731f0", "70e3d28b80fd3e0244e2b27d95ebe860e7610fb5125df60fc5c07e31ccdbef06", "7241af769419ff4b1307050bfee67e5752ffde0438e9d93dbcbba9bf5985db88", "727d147c587f7d9b4169262f093ae92fdd867749d3bab009271d6a4aa265747e", "72d1556008687fbbaf28b5714be1ff8c0d588a082ca9ccb364011dc9c4779a25", "733c532e40759f7496aea3e194b588b6f88341f1473dfd95b4122c5d64bb1e41", "73c6d6c094cf4c9c244e7a67d53f67abf9e28513d662f7e4ef39b639f18200f9", "73cb634cb0171a005a8ebc7104c22c86d56380753e389ec13f7f4c3dcdcf4485", "7509adce957554c60ffcec56d0f15e40248f61c17a427b37c8e132383563c360", "78c395c9d1917cb4dd7ff0b3329752fcdcee36243c5a42ffea8680c39d01e09c", "799547518ed9bc5fdd13f7ba56fc6e27d8839a2d3d87dc5ff2e9e7b167833c25", "7c6368dcd4bbc20cbfae22559bf8c92d1927629e753fc6a6c3a3f159e9ad66fe", "7db394bf5b7eb8ecff618dbcee82b5cc71fd5fb8b4cd812e7893541d03ebae75", "81ebd380be04b3c0143f2ea2723a2b2ccafa8a301f9642c893991e781fb8f8f7", "838fefacc0a6b718e72258ce2d4d8f2eb60b9e6ac0609d5a041ae43ed11667c8", "8592649d88abd61c9f2b5ac82fc907f98b07075fd487b3c2cd8d7cb764397106", "86715ac724cfbf6ec5273fe2b4f42cf22ff346c5906cd4126e5097cb06022eec", "89b8b982cfe614149ae76235f00b99534d751f44440a169e9e5548fb635d877a", "8ac64413391d38363537a6c36782bbab5235badebbd0fbaf96fa0009c0409c19", "8c409f36bedfd7fd541127f9f594b4d2c6803f10755bc5f2c5703993d979e80c", "8d482c3e6cd5a539673c28763da02b21d5f22e189e4dce3f0fbad1ffcc554cbe", "972626e80cdc1aa5c65f4af390b728586b5826a2478e5aa7365ad5e298f1db9b", "97752c6272be9604586b4919bec885b658f58d98dd6ce04406f17ec009786360", "97ec4bdf20886e5d225a7a752d17ec7b16b24f8f56119ea69280439db51ec415", "98e1809325cbd80a2bac752b379b837b9ac541bc874244daa64115ff9f110ea1", "99a539b21b0ca3a973e996b7e2ee58fc72759e3c0d55d35e24679daee491a966", "9b6da3431daae3e618f6b07c268ff5d3af667c9426f203015215eba294e50f24", "9b8fece14fa9955f4f86ef30dbaf8b1daa8f3f3c91dc6d13997b3736cb39fcc5", "9ca623715b821e7d5ea368170340488f3382f4956bf25c98c5993f44879ebd16", "9e89065429de9281d57aa1d1ceecf2aa03cb8bfb5e013f50bfbfe57f13cb5d81", "a03f556f3b411f22959f55ceb6d99773368b955327d80ad41f98260ff9ed11ed", "a09d8d577e3a5ab12cff95d9f6e4fc19f466dae7650313f84fb502e77dbf779b", "a183dcdf002467f66e29e52d0265a6e4c55e8d84df8636387ea9afe94b66256e", "aa4b8b3d59e00a8e032f48976c9b509860a2f6ab14bd1b1c30f1f52b47726f4d", "aaa6a9f697dccfe13ac679b73d07ebbc434ce44aae1b43e02852d50f85d9fcf8", "b01996a84a528936c8d313f182acf551215ba112ea9c4b847ed4037920b1a6e6", "b15e33e6c563f7039194a7c1e2b780f29c56f65da223ec408a06ee2ca3ef5b52", "b21bf245c211f7ae2195dc61ff061bfa4e128e4408f929e78f08bcd9c36ac49b", "b2b86171b5860ee7cb5c7b3c026f4aac25a7751dee3742a957e5c5ec39d0a280", "b2e436d4acba3b0c6888e684501e61c4af7f27fabba3d333941b6365f4db451a", "b2ef5cfc09cdc18bca4992c177e2ac969c0fe496fb8650dccea95b86be8de717", "b47f07fa9f9c02030dc733e6e6458f415eaf6c74d393b3a78fbd0b80e7501301", "b5de2778fdaba130bd1fa81b605d1be59b2baa9f2ad54548df3488e2c6651480", "bbad2a22790314bb026f6d766a1a09e28d640f11eb720852dfaf0a40cc4ddd03", "bdba234c23bdbd8bb4af9a5eeb01a3c7f504745260be92dbc0cbf29481024d53", "be8233a572fc427ff5bcc2f386a5d229d7c66af2fd46f8042d6e7b0422dc621a", "bf24a2e8492a8b75997e44288ba152e734ca859d5916040bf028fb76debe2fe1", "c06a77d7fe9cb0c21eabf39b5bb6a007c973b2acfa42793ab0757c860d99500d", "c0c7cc4a9f81b94c6c69497d462de00a257101390c3c1c37357cb4a6fe513c70", "c9ff8b541276cc48f72a7f6f41d3164cebc530f99c7c4d3e2e081d7149d02e18", "d4681afed3ca7046450779b3580ddf32be704d9723be999817255d0bf6b9d4f3", "d679cd5370ee5c5abf61496971f75063f0e1145a477d8dd2bcbd73139badcc28", "d7b24c622540b4715297b66b3f5ffe84843786fb0b7738259917a27a9599f3b2", "d7b4e42ed69e561af8a12382d3af241495d2efd3ac6438678b5f608a8744987c", "d8bbd3747acb69372aa8e6da185569a5ebfffda630d712e1c5798f27fa12772f", "dc26f7b29b6ae88027569a39e8f71b7e8abef7362341ef41f9e2e57d74b6d1f4", "def2ceddcbb98ec8fe82aa9f215ebbd4b0c096a727a1f35444d8f34c73d60e58", "df609126bfabac15c7e6f49aefb77e16c8b08ca3acce85f69ea0d2193f24b1cc", "e00fd036eb1daf4d3703c7f28ab53dc114b77c231c7a628f840b1e1e169fd334", "e011b85461a2fcd31614602bd229b2aaa66e7ecf24dcdace8c2e852578042396", "e3677994ece6ea40060aea98bce07b18be33c65dece364fb2da58a2ee1073ab9", "e39640a9f619fe50c5174bd6a9721d4cc0393b84a5818d68e20a69c5ba0ab83a", "e5336b343b4d93d997d89b2c5345eecde072aae68b19bada24733791c8b1c5a9", "e562e578c6c61d1588b9d0aadacaef8684e4393f5f48cb210cfc66b90141af0c", "e86db6a388b930f8bfa9e39815905184df8581db3cd2702dec0c204f9d44b4ee", "e949e09ee0d2a5bedd46d414e1dbd2a5ead85948bc7e37ef256280b710659226", "eb770f954bd07f1a4cf50ef79d49b18e483a41ccccb44dc3ef15fb8015d89f52", "edb352e0b2bce245c33695085cac531c0a7d82e143148eb09109ad40218a3043", "ef1738f409eaa3d500fa44be440b8ebe17b15d71c67be158727834716cc7db4f", "f03bba415ffb7890f631bf00ec049f73b33aed026121b4220da263d3f84a5fdb", "f1bae80e2ed1fd347334853c1ed9015e4d9330bf4a84560f8dc3a61f70efb12b", "f1f7e1114242feec5819bbadd37b8e1ed4b9947c461939580073333742c99088", "f29d827b62f31d405662141a929321ef55b9e4ae36debb5240555631a4d3ad79", "f565e969ec1197d3b732fc2eea504d733013ae36e2382f3753c916eb46368771", "f780ae7b1c8b61c49484a352a5489f4ebe56da6e4196d62861a094753cd8707b", "f98142df97b9a6372f10f31d847e155cd4f9b04fd319c31ae3086afa6c5fb67c", "f9bd60ac116381ad711996a82864fc17512a82b7705ef8cd73e072efb7f474b8", "fca6fc0277ad8b20c476766dce5149ce310324d968f000792d9c5655d4451214", "ff1b3ce2d9e61ab7e6fa45cb11a4632fea3fa46deaa044f47fbb80291d26267a"]`

### `HONEST_NEGATIVE`

- Run ID: `run.slice5.slice7-replay`
- Output kind: `TIER1_DECISION`
- Output payload SHA-256: `099d2caa80825b198b6119b6a8de89635c8bbcb3979f050c456b8ef53689d1ee`
- Decision/advisory hash: `37234b970fb06bd76dbf6dcdf3ee0d8d8fecc455b9e0b7dbdc2152b85a440ffe`
- Snapshot SHA-256: `113a1ab8b3c9179a3bc4d4dc4df4b0e30d2dedf2076b34005658555a246c4b4a`
- Audit payload hashes: `["d64cbbc8fd7fe43b0d641e09eefda38b093c6da93d1b4f1fdd2d9de07612dc2e"]`
- Citation payload hashes: `["0005f610d2707d5cd853eb3affe91f6bd13fda9cd9f546275b786477d4421428", "09160356d5c526f74bc7424813dc03780e4ca1544e2b11d5102ee03a1efe32d3", "0b54754f86c28887b98aa9b968ef1284d87783376551cf128f7acbd240479f5d", "0f93d4399987f50aba35871b222aa1cd1b5a62c0af3686f3aa3795080cb90a56", "0f999310d118c7f5f05ec9ededfecf72fe4f7d4cda742770d5972bd00d0696b2", "2ec4e23b1ca3271ada39a5158f7fbf947f52d49ccb943749674ffa1a167a256e", "355b889a3eff1b3cf2919fbf5d079203ee4872c6c620b4124b4faa0155a2871b", "3845f2565b5f22b605f5fbc46a3579f8fdf9ea1e255505ee0ddefea2eee3366c", "393e77ff6c48dd12c420846d1a862d6e5e4dd06151f0538f5541c7f653203dcd", "39792ee56ba83d8e549fb3b84e37e5b6711b5a9235179413c35ceaf07eefdda6", "5058f9f624b21b712232d2d079c2c522ab2933c629fc369dd13e6110bf1bcfec", "513a15d00bce67eefdaaaec47b16fc22a7f256f626b897f608abb593d069c0df", "524d1ec7af3b4234354c20106808126a1df3e352bf7d629404328e7b13d5533a", "546972e610a00f9e0eef3ff73339987a4b904a618b527428b3887bb2c497db36", "582b1e4a7a0076034224d585e8d0aaf48026560714886fae363f69fa68a07531", "6d3f6d979863932d4eb02d3c2827f41c0a610f3181583eed8a4dcb1443ceb536", "715fa449bd56f686d88a369ba7574f0769733eb07143ed7a60ad25b9508190c2", "7dbcbc55e2dade36e0a624bc12accb29bd90e690ee4dfebe83dd08cac20fa2d1", "84635e18fab1400caa8417b7d534f30c93010ff7a558498b1add18a96ceb542b", "89e9db8dd2134acd41e66861bceb812fa8805ffc0667d9162d8c8c0fcaea7bad", "9723add51c785e470ea4e171098fd972045bb8f4fa7d87d7fd5414b11a026958", "975e2a64c85b83a2240ae4dcf238d7a730fc17186625911b93d5f7fa45073498", "9c998f499b412dfc4fd751aed467fb1219c52797d04195af8c61ea7e1d200210", "a3c7ff85c1caf746889e56f8cff89f80954de3957745eb592235030dfa01c35c", "b23d91d98f706456e33c637b4d5f9219c1dd35783a4b45cf345493ca94a255e4", "b2a04563947ceabc8e7592ca92fe8065e836d38c352081c3219e9bcf40a1ca4c", "bfd21b15e0a4649e2c76634946f582939859843966e076015b97719ed90a231f", "c38e6bd63757ee4c55d1c33deb8dea5e57f6b237991491a9bd7ddbb2adee57b9", "d07d6aca178a4f5d97f2c8f1463f77427ad8801caee496c59ecaa0240181d9cc", "dedc95da41f60f1c9dbbd5b5f1d336ffd789873ec59e5f1d09c898f6a81c97d2", "fd06547dfc6bd5f41c27c797ecda74f9324bbe52086779b07e544a1cebb6b96a"]`
- Bound-version payload hashes: `["004bebcaf040b1357ea5e808160d25877d9b20e9aac902dff2e1d85f4d5392e9", "005de12463d8d62111fb707d13e3261406127fd0c8362915f3dd46e7a24a17b6", "045517675e046a4da4cc26b3f22fa38cc5b265516250b8d4517f2e964ca19855", "0ad336a922fa439f676c1c844ae8bc82e4ceff4852bb7f3f3af160915aab4280", "0d679798551732e34240edd7eb13d2b4060709051c9f6a175d51a704d73651e3", "0d6c75552847c40739050113b170ed50a9356b938637e82fcce7ad428d29fcdb", "0e542c2cc14404e07084d4ae97127925d5a7b092eb5ce1bf0fab6436a6d921a6", "11fd49ea73d264ebb770f6c2593484822ae24d67a35e7172256d6d8fedf65c4a", "139da5cb233e126676d9976d977458a3871cb8429ba18421481dc05e9ed7a704", "165f1f0bd94bbb32cc95281be07b61dfa8a881b77b0174a137d6bd00cc8645d6", "1a8dfb275f6153a5ce6b957c81c490536a0232fb9c56cff0c114c29c1ed7e5fd", "1aa433f04906604f33244dfff1f2eb6e7ad3b590fb04037bf44d9a4a492ef7a5", "1c2d49bf0b1a68b5a5ac8bb5fba95f128c45420e31d4620a9a49ad7efc7d8eac", "1c6cb895e9324474e1dcf488c0e06cfa7b808e678b7c0a703afd9b703af901d6", "1f07f48dd61d015cab226cc473b1f0668c14f9e7a4d4d33a14d5bb77e7589314", "1f971823d164e1cb72fab613017817154865cde7c1ff7f24e7f2f7d6ee469ae9", "20b8b661de3ff24ec24360a14fc2d31f3bd159ad6786066062b62706fc86fc1e", "215fd2df0d7139fda263d07fc67ac4e7828b16f523164dd5320588da914b37fe", "2206389cb876531faec08f368b0c19c13f4e114f49b747a4c6ad09ba205b0211", "222beee27f6f5d84c91c1d6072b2667f4f8feac41eb74617a5ae6a21994ccee4", "259524d810bdd9dac2dad92b5cd7da9ed0cb52550a39c9dc95dc134c2f8fba8f", "26e6889774291bcee903ecfeefe96f5f50465cd1a183d9677e080f927d47afe3", "277660d9e53044891aa754c330fdfdd652eae5efc59d715391a3ac41ea5a52b6", "2a755c1bc39b3a8b84b4751cdaeff3a84939617ceec71ce4e20c267137a40665", "2b3ff6221d8b4770a9a3677804eb523ffdf069bd2cdcabb41274d80558591768", "304f87eb851d24f2f903dbf30a6f2d9addd6a35a5c6d816fd27badabd0207dd0", "30723ff0a8d8a511ed7ca1fe9643029507d9e2ac31e08d24a954a64e35aa3273", "309733723683e740a07dba36979fe667fac04961a7dab06d6f21c381c4b04bd4", "31a1562c6cda57a95b3d4abc28e8e08487d48e4d21309adc245b8cc3cf964a02", "31e00025251f7b3513dbfa05577e72cd3c208c9f0682020bfc0f61f77ab698a2", "38bb602999ab7c822d64309556581951357427d5b106ba384672f2578c51f17e", "3a4ed3739528d1c449d5cb0d8d228690b57054afb7a96e2f6125a4ff9e2c0ada", "3d60e44073efb0c894fbef74624c7a5757791280b433dcd0cc00e796997e99eb", "3d7d3574befd27553fd3301c03a5e94acd67f874222723c04950157504ff7c0d", "3e71ed490e332706deae4f1ae83da31d7bed431414cc0897a82d60fae3f7a025", "4367bad683058617ffc5cdb007d6d385137b9b52d6c6836ae70323a89a30ab2e", "463025b02e8538e3dabbbe65da4ebe7db12b9eac9bb1c650b2c11cf50144b60e", "467ecf05e7b9ae61fc72ed6c2461f4954d8c4e3099b383eda5ed67252d3f0303", "46cfb73d720e7fd0c7957bd85b346d72450e3fe586f76448b59a134413f74dfd", "4dc528597c61b548776998d965ba05b6acc72fddf7a9b809228029060e730954", "4fe4b39cc19fc8fa9501665c145d347f89473969e3668c37dc26a8719a43b0d2", "4ff442ab861d3a7e41d7b03044c0fa5277fad53984af1daa9e9d8b1a7baead59", "51845eef6abd85da11acd77b758b08cf1185788eaad762c50eab6a35c8cc1154", "528dcc2a8059b2283b79da2a49bdf493c6ffc6ce6fb9c4e81401d4ac8ef29fbd", "57ef7dccdebfacbcabf51ebb92966f9b3c58273d8adf382ec012e5a4ca353e3a", "583ad915743fc94989d78ece097c2b4ca4382e9f56fa591d43e7503976c4eace", "5938ceb1b0377f2c6a9ed1e88fb9a5eaf85eaaab9810ed5e8da1e5fef3bec6c7", "5a2485bc6eb991b5bdc7980f5572b215d3c25153aa6df2d02f13deebbab00cb5", "5b5e40508f7e130260e42f070c0ade3527dd246a74afdad4bdb39b3621cf82cb", "5c5213b6ce9e0117e6bad7dc2a9059be5aa2a717f8b573a6e8d3c7af0f0ae922", "5e79e72cab4fdfd63d852c7a6734c6d6b254b9e974815a510bab16630c451426", "67195dd214be452edcc27201beac8eb986fe51b0c22f84aa4babfbbf3c9342bd", "6b76f91ece563514162bd800a4b8f76c6451e14133f84ee1e6633c7b01108571", "6bf35e65468030e0bee2c5791514d67df76763161e6db50fdcbff3a36effc779", "6d712eb7024f55458b4143700af18ba167d9ec7fd9555a84bdd58425485bc344", "6f7b1e9a78e7fa080b888633639dbd036be0c3351e85169e878971d0627731f0", "70e3d28b80fd3e0244e2b27d95ebe860e7610fb5125df60fc5c07e31ccdbef06", "7241af769419ff4b1307050bfee67e5752ffde0438e9d93dbcbba9bf5985db88", "727d147c587f7d9b4169262f093ae92fdd867749d3bab009271d6a4aa265747e", "72d1556008687fbbaf28b5714be1ff8c0d588a082ca9ccb364011dc9c4779a25", "73153e193876241c88c52ad83a113c14c9b6f9b785b934d5f94de1dbc02ea67a", "733c532e40759f7496aea3e194b588b6f88341f1473dfd95b4122c5d64bb1e41", "73c6d6c094cf4c9c244e7a67d53f67abf9e28513d662f7e4ef39b639f18200f9", "73cb634cb0171a005a8ebc7104c22c86d56380753e389ec13f7f4c3dcdcf4485", "74c7314a0bfb4762a9ee0c1cc08d69a4788603e4b94dd9676b7991bff9975ea9", "7509adce957554c60ffcec56d0f15e40248f61c17a427b37c8e132383563c360", "7804558dcfe428cfea0e0f962f4566ea980dd9e3a24d68dd96fc79d07a576206", "78c395c9d1917cb4dd7ff0b3329752fcdcee36243c5a42ffea8680c39d01e09c", "799547518ed9bc5fdd13f7ba56fc6e27d8839a2d3d87dc5ff2e9e7b167833c25", "7c0e8a35710fbf59b3612a5815b0e37fdb18e75052f449d1cd9b41e35e12df90", "7c6368dcd4bbc20cbfae22559bf8c92d1927629e753fc6a6c3a3f159e9ad66fe", "7db394bf5b7eb8ecff618dbcee82b5cc71fd5fb8b4cd812e7893541d03ebae75", "805057deb3171c1fa72c0394480d8a1e0538ecb58f5eb74f3bdc1c28ed2d49fc", "81ebd380be04b3c0143f2ea2723a2b2ccafa8a301f9642c893991e781fb8f8f7", "838fefacc0a6b718e72258ce2d4d8f2eb60b9e6ac0609d5a041ae43ed11667c8", "8592649d88abd61c9f2b5ac82fc907f98b07075fd487b3c2cd8d7cb764397106", "86715ac724cfbf6ec5273fe2b4f42cf22ff346c5906cd4126e5097cb06022eec", "89b8b982cfe614149ae76235f00b99534d751f44440a169e9e5548fb635d877a", "8ac64413391d38363537a6c36782bbab5235badebbd0fbaf96fa0009c0409c19", "8c409f36bedfd7fd541127f9f594b4d2c6803f10755bc5f2c5703993d979e80c", "8d482c3e6cd5a539673c28763da02b21d5f22e189e4dce3f0fbad1ffcc554cbe", "8ea0bae1ab64e54b5467b4e412acb8d9babe973adb7c7a4deefe84cb083dbe8a", "8eb65dbe9b82459c4e6129d2f7ae5046db38917bbd792380cfe1c6f4a564fd3e", "907d71dde79dafa79cc7353a91edf33e2093002eab9e216c7317071988af9b3e", "972626e80cdc1aa5c65f4af390b728586b5826a2478e5aa7365ad5e298f1db9b", "97752c6272be9604586b4919bec885b658f58d98dd6ce04406f17ec009786360", "97ec4bdf20886e5d225a7a752d17ec7b16b24f8f56119ea69280439db51ec415", "98e1809325cbd80a2bac752b379b837b9ac541bc874244daa64115ff9f110ea1", "99a539b21b0ca3a973e996b7e2ee58fc72759e3c0d55d35e24679daee491a966", "9b6da3431daae3e618f6b07c268ff5d3af667c9426f203015215eba294e50f24", "9b8fece14fa9955f4f86ef30dbaf8b1daa8f3f3c91dc6d13997b3736cb39fcc5", "9ca623715b821e7d5ea368170340488f3382f4956bf25c98c5993f44879ebd16", "9e89065429de9281d57aa1d1ceecf2aa03cb8bfb5e013f50bfbfe57f13cb5d81", "9edbe98d3e3aa5d4403ac65fe506ca674f587c1487c4707b92606a993d764930", "a03f556f3b411f22959f55ceb6d99773368b955327d80ad41f98260ff9ed11ed", "a09d8d577e3a5ab12cff95d9f6e4fc19f466dae7650313f84fb502e77dbf779b", "a183dcdf002467f66e29e52d0265a6e4c55e8d84df8636387ea9afe94b66256e", "a38aac0b1296d50d567a54cc6e06854826406b560d32b35133bc6a0ff043f990", "a85ace57a1c62fc38b076bad4ce4c6e9f0bae944dff23ce05738441448e7c103", "a9d046e108129ad3c5a2a6fa307df62790b2b491bb77975fbb69c48c345c5425", "aa4b8b3d59e00a8e032f48976c9b509860a2f6ab14bd1b1c30f1f52b47726f4d", "aedbc19b446062d715ddbde454b93a91b95e97686b19c50ff2803b41a3c21f93", "b01996a84a528936c8d313f182acf551215ba112ea9c4b847ed4037920b1a6e6", "b15e33e6c563f7039194a7c1e2b780f29c56f65da223ec408a06ee2ca3ef5b52", "b21bf245c211f7ae2195dc61ff061bfa4e128e4408f929e78f08bcd9c36ac49b", "b2b86171b5860ee7cb5c7b3c026f4aac25a7751dee3742a957e5c5ec39d0a280", "b2e436d4acba3b0c6888e684501e61c4af7f27fabba3d333941b6365f4db451a", "b2ef5cfc09cdc18bca4992c177e2ac969c0fe496fb8650dccea95b86be8de717", "b47f07fa9f9c02030dc733e6e6458f415eaf6c74d393b3a78fbd0b80e7501301", "b5de2778fdaba130bd1fa81b605d1be59b2baa9f2ad54548df3488e2c6651480", "bb7af282f85d5fa83b7672a0310c98ac30a75494d1057b550e5e6c853080d82e", "bbad2a22790314bb026f6d766a1a09e28d640f11eb720852dfaf0a40cc4ddd03", "bdba234c23bdbd8bb4af9a5eeb01a3c7f504745260be92dbc0cbf29481024d53", "be8233a572fc427ff5bcc2f386a5d229d7c66af2fd46f8042d6e7b0422dc621a", "bf24a2e8492a8b75997e44288ba152e734ca859d5916040bf028fb76debe2fe1", "c06a77d7fe9cb0c21eabf39b5bb6a007c973b2acfa42793ab0757c860d99500d", "c0c7cc4a9f81b94c6c69497d462de00a257101390c3c1c37357cb4a6fe513c70", "c2da8d165135808da43071ba4b406aee390d6618ae890d324f00bb2b4baf12ba", "c9ff8b541276cc48f72a7f6f41d3164cebc530f99c7c4d3e2e081d7149d02e18", "ce4dd2be122f0c6af3aa77f204b8ed9f2e4698c3e2d5b700249da211f77998aa", "cf8846e4bf74e86c755f050a2ea23d67d7718999bcc8b248d94412e6c02e779a", "d0218311998c8ffe6d002a6687fe2cce16e303e023cece81b130794f135b1427", "d382ac2c6c4935778f832d97b2ecbb3731c8e52c91a17f9733aecd25c27cb76b", "d4681afed3ca7046450779b3580ddf32be704d9723be999817255d0bf6b9d4f3", "d679cd5370ee5c5abf61496971f75063f0e1145a477d8dd2bcbd73139badcc28", "d7b24c622540b4715297b66b3f5ffe84843786fb0b7738259917a27a9599f3b2", "d7b4e42ed69e561af8a12382d3af241495d2efd3ac6438678b5f608a8744987c", "d8bbd3747acb69372aa8e6da185569a5ebfffda630d712e1c5798f27fa12772f", "da96483016929537d9f343982b8865a4d2407fdc9265dad9f097fafddf6f49b1", "dc26f7b29b6ae88027569a39e8f71b7e8abef7362341ef41f9e2e57d74b6d1f4", "def2ceddcbb98ec8fe82aa9f215ebbd4b0c096a727a1f35444d8f34c73d60e58", "df609126bfabac15c7e6f49aefb77e16c8b08ca3acce85f69ea0d2193f24b1cc", "e00fd036eb1daf4d3703c7f28ab53dc114b77c231c7a628f840b1e1e169fd334", "e011b85461a2fcd31614602bd229b2aaa66e7ecf24dcdace8c2e852578042396", "e3677994ece6ea40060aea98bce07b18be33c65dece364fb2da58a2ee1073ab9", "e39640a9f619fe50c5174bd6a9721d4cc0393b84a5818d68e20a69c5ba0ab83a", "e5336b343b4d93d997d89b2c5345eecde072aae68b19bada24733791c8b1c5a9", "e562e578c6c61d1588b9d0aadacaef8684e4393f5f48cb210cfc66b90141af0c", "e834125af3d4d0b6417067a7a4eeadaf1a1fca54ee402a94a98c91c14cfce48f", "e86db6a388b930f8bfa9e39815905184df8581db3cd2702dec0c204f9d44b4ee", "e949e09ee0d2a5bedd46d414e1dbd2a5ead85948bc7e37ef256280b710659226", "eb770f954bd07f1a4cf50ef79d49b18e483a41ccccb44dc3ef15fb8015d89f52", "edb352e0b2bce245c33695085cac531c0a7d82e143148eb09109ad40218a3043", "ef1738f409eaa3d500fa44be440b8ebe17b15d71c67be158727834716cc7db4f", "ef81f162c1b717f62b8c2e7142dfa5d656b9c9c28fb85cfefc049bc0ef7183ab", "f03bba415ffb7890f631bf00ec049f73b33aed026121b4220da263d3f84a5fdb", "f1bae80e2ed1fd347334853c1ed9015e4d9330bf4a84560f8dc3a61f70efb12b", "f1f7e1114242feec5819bbadd37b8e1ed4b9947c461939580073333742c99088", "f29d827b62f31d405662141a929321ef55b9e4ae36debb5240555631a4d3ad79", "f565e969ec1197d3b732fc2eea504d733013ae36e2382f3753c916eb46368771", "f780ae7b1c8b61c49484a352a5489f4ebe56da6e4196d62861a094753cd8707b", "f97eadfbb83c6dab13db6536fb13a2d77249df749bf46efa1e3498f7198469fe", "f98142df97b9a6372f10f31d847e155cd4f9b04fd319c31ae3086afa6c5fb67c", "f9bd60ac116381ad711996a82864fc17512a82b7705ef8cd73e072efb7f474b8", "fca6fc0277ad8b20c476766dce5149ce310324d968f000792d9c5655d4451214", "ff1b3ce2d9e61ab7e6fa45cb11a4632fea3fa46deaa044f47fbb80291d26267a"]`

### `TIER2_ADVISORY`

- Run ID: `run.slice6.slice7-replay`
- Output kind: `TIER2_ADVISORY`
- Output payload SHA-256: `953d79590b8da308e814c99a59b30776a1e5908dbb3780749e13e5a7d24df483`
- Decision/advisory hash: `d633232523b115efedf0eff13ac81797b03cf537a0635eafa4e335cd09569678`
- Snapshot SHA-256: `aa47d9654a5486c7916557fee261240e64a229a9d777748e3d289726946eebcd`
- Audit payload hashes: `["34ba7114774a89df32ecc5fc6788d9de07f8788033e903f46230219ac939583b"]`
- Citation payload hashes: `["2034189ddc141c806e13d32fa962fb4171feba52bdc5a158c2769916ec8c7c5e", "4b496e620a3d07aa3a4adf14eafe2e36c1bd2c01673ec673f87c6d235f28ebd6", "524d1ec7af3b4234354c20106808126a1df3e352bf7d629404328e7b13d5533a", "580ee7d2ba5e1804555481514c926d63c0bf0cf553baccb7aab28cf626411e91", "84055178a83e641208586873cd8e890bcf357c7f7fe6cfc1520abed6c1caeb0a", "bf964590d3426d8eb2ac68743dff155efdc880749f540438435baff6319212ce"]`
- Bound-version payload hashes: `["004bebcaf040b1357ea5e808160d25877d9b20e9aac902dff2e1d85f4d5392e9", "005de12463d8d62111fb707d13e3261406127fd0c8362915f3dd46e7a24a17b6", "045517675e046a4da4cc26b3f22fa38cc5b265516250b8d4517f2e964ca19855", "0ad336a922fa439f676c1c844ae8bc82e4ceff4852bb7f3f3af160915aab4280", "0d679798551732e34240edd7eb13d2b4060709051c9f6a175d51a704d73651e3", "0d6c75552847c40739050113b170ed50a9356b938637e82fcce7ad428d29fcdb", "0e542c2cc14404e07084d4ae97127925d5a7b092eb5ce1bf0fab6436a6d921a6", "11fd49ea73d264ebb770f6c2593484822ae24d67a35e7172256d6d8fedf65c4a", "133e416534a514edc9d437f9d809a9b9577f6e217d81ce52bd896269ceb58e34", "139da5cb233e126676d9976d977458a3871cb8429ba18421481dc05e9ed7a704", "165f1f0bd94bbb32cc95281be07b61dfa8a881b77b0174a137d6bd00cc8645d6", "1a8dfb275f6153a5ce6b957c81c490536a0232fb9c56cff0c114c29c1ed7e5fd", "1aa433f04906604f33244dfff1f2eb6e7ad3b590fb04037bf44d9a4a492ef7a5", "1c2d49bf0b1a68b5a5ac8bb5fba95f128c45420e31d4620a9a49ad7efc7d8eac", "1c6cb895e9324474e1dcf488c0e06cfa7b808e678b7c0a703afd9b703af901d6", "1f07f48dd61d015cab226cc473b1f0668c14f9e7a4d4d33a14d5bb77e7589314", "1f971823d164e1cb72fab613017817154865cde7c1ff7f24e7f2f7d6ee469ae9", "20b8b661de3ff24ec24360a14fc2d31f3bd159ad6786066062b62706fc86fc1e", "215fd2df0d7139fda263d07fc67ac4e7828b16f523164dd5320588da914b37fe", "2206389cb876531faec08f368b0c19c13f4e114f49b747a4c6ad09ba205b0211", "222beee27f6f5d84c91c1d6072b2667f4f8feac41eb74617a5ae6a21994ccee4", "259524d810bdd9dac2dad92b5cd7da9ed0cb52550a39c9dc95dc134c2f8fba8f", "26e6889774291bcee903ecfeefe96f5f50465cd1a183d9677e080f927d47afe3", "277660d9e53044891aa754c330fdfdd652eae5efc59d715391a3ac41ea5a52b6", "29eb93a1598262500a2d34ecec0e123dd8c1c56aeec43eca1958ad871de65fe8", "2a755c1bc39b3a8b84b4751cdaeff3a84939617ceec71ce4e20c267137a40665", "2b3ff6221d8b4770a9a3677804eb523ffdf069bd2cdcabb41274d80558591768", "304f87eb851d24f2f903dbf30a6f2d9addd6a35a5c6d816fd27badabd0207dd0", "30723ff0a8d8a511ed7ca1fe9643029507d9e2ac31e08d24a954a64e35aa3273", "309733723683e740a07dba36979fe667fac04961a7dab06d6f21c381c4b04bd4", "31a1562c6cda57a95b3d4abc28e8e08487d48e4d21309adc245b8cc3cf964a02", "31e00025251f7b3513dbfa05577e72cd3c208c9f0682020bfc0f61f77ab698a2", "387d18505713a94a5c47eca46277da83ed9a9d85671c60206962f3f7ec6fa1e1", "38bb602999ab7c822d64309556581951357427d5b106ba384672f2578c51f17e", "3a4ed3739528d1c449d5cb0d8d228690b57054afb7a96e2f6125a4ff9e2c0ada", "3d60e44073efb0c894fbef74624c7a5757791280b433dcd0cc00e796997e99eb", "3d7d3574befd27553fd3301c03a5e94acd67f874222723c04950157504ff7c0d", "3e71ed490e332706deae4f1ae83da31d7bed431414cc0897a82d60fae3f7a025", "434aaa8b180edb666c448852b7add44fd50e180004575a0e2e2e3257a54ca771", "4367bad683058617ffc5cdb007d6d385137b9b52d6c6836ae70323a89a30ab2e", "457fd4725d8ee1f6fe0165d6f20f691206750a675d4f0e0cb3ae23acc17b9f27", "463025b02e8538e3dabbbe65da4ebe7db12b9eac9bb1c650b2c11cf50144b60e", "467ecf05e7b9ae61fc72ed6c2461f4954d8c4e3099b383eda5ed67252d3f0303", "46cfb73d720e7fd0c7957bd85b346d72450e3fe586f76448b59a134413f74dfd", "4d59ac5295cd2d152e8cc993408dc650868f9ee6dbb2d276eeb46997c9d2d9de", "4dc528597c61b548776998d965ba05b6acc72fddf7a9b809228029060e730954", "4fe4b39cc19fc8fa9501665c145d347f89473969e3668c37dc26a8719a43b0d2", "4ff442ab861d3a7e41d7b03044c0fa5277fad53984af1daa9e9d8b1a7baead59", "51845eef6abd85da11acd77b758b08cf1185788eaad762c50eab6a35c8cc1154", "528dcc2a8059b2283b79da2a49bdf493c6ffc6ce6fb9c4e81401d4ac8ef29fbd", "5355c11b44aa49750d9f4d487ce6f5b7af565b37c860eeb6137fae13814090d4", "55ced36a8a82d70bb90e369119ac470a88c9d7c11a9761e2c818d50124cf3707", "57ef7dccdebfacbcabf51ebb92966f9b3c58273d8adf382ec012e5a4ca353e3a", "583ad915743fc94989d78ece097c2b4ca4382e9f56fa591d43e7503976c4eace", "5a2485bc6eb991b5bdc7980f5572b215d3c25153aa6df2d02f13deebbab00cb5", "5a3c1fd44eed9279abb8be3f5d69261bd7256e8727aade9b9a3b56c6b390c999", "5b5e40508f7e130260e42f070c0ade3527dd246a74afdad4bdb39b3621cf82cb", "5b65196c93eea9618262bd4e166a5edad07a33238c81209ff7b8d9e1cf782717", "5c5213b6ce9e0117e6bad7dc2a9059be5aa2a717f8b573a6e8d3c7af0f0ae922", "5e79e72cab4fdfd63d852c7a6734c6d6b254b9e974815a510bab16630c451426", "64f3e2aa5bd83ffd7ff7c164a6bb5219d841b8bb69d8341a1ebda9b01a313cdd", "67195dd214be452edcc27201beac8eb986fe51b0c22f84aa4babfbbf3c9342bd", "6b76f91ece563514162bd800a4b8f76c6451e14133f84ee1e6633c7b01108571", "6bf35e65468030e0bee2c5791514d67df76763161e6db50fdcbff3a36effc779", "6d712eb7024f55458b4143700af18ba167d9ec7fd9555a84bdd58425485bc344", "6e5530fcc8b0d13ebf829990cbcf67bcd04ffce0720b2c66111ef1319bd89fa6", "6f7b1e9a78e7fa080b888633639dbd036be0c3351e85169e878971d0627731f0", "70e3d28b80fd3e0244e2b27d95ebe860e7610fb5125df60fc5c07e31ccdbef06", "7241af769419ff4b1307050bfee67e5752ffde0438e9d93dbcbba9bf5985db88", "727d147c587f7d9b4169262f093ae92fdd867749d3bab009271d6a4aa265747e", "72d1556008687fbbaf28b5714be1ff8c0d588a082ca9ccb364011dc9c4779a25", "73153e193876241c88c52ad83a113c14c9b6f9b785b934d5f94de1dbc02ea67a", "733c532e40759f7496aea3e194b588b6f88341f1473dfd95b4122c5d64bb1e41", "73a49c3982da331f88b240b2d3ef19f932ebfbb5f291bd69fe7463931cbb413d", "73b8f9d13c906c187405945f425f581bb8bf9e326c946a9e0eae8ebe7c85379e", "73c6d6c094cf4c9c244e7a67d53f67abf9e28513d662f7e4ef39b639f18200f9", "73cb634cb0171a005a8ebc7104c22c86d56380753e389ec13f7f4c3dcdcf4485", "74c7314a0bfb4762a9ee0c1cc08d69a4788603e4b94dd9676b7991bff9975ea9", "7509adce957554c60ffcec56d0f15e40248f61c17a427b37c8e132383563c360", "7804558dcfe428cfea0e0f962f4566ea980dd9e3a24d68dd96fc79d07a576206", "78c395c9d1917cb4dd7ff0b3329752fcdcee36243c5a42ffea8680c39d01e09c", "795f2b413ce1de65325a868b615a1fa3a6bc7336818d19c27a3bb65a6d990ab5", "799547518ed9bc5fdd13f7ba56fc6e27d8839a2d3d87dc5ff2e9e7b167833c25", "7c0e8a35710fbf59b3612a5815b0e37fdb18e75052f449d1cd9b41e35e12df90", "7c6368dcd4bbc20cbfae22559bf8c92d1927629e753fc6a6c3a3f159e9ad66fe", "7db394bf5b7eb8ecff618dbcee82b5cc71fd5fb8b4cd812e7893541d03ebae75", "805057deb3171c1fa72c0394480d8a1e0538ecb58f5eb74f3bdc1c28ed2d49fc", "81ebd380be04b3c0143f2ea2723a2b2ccafa8a301f9642c893991e781fb8f8f7", "838fefacc0a6b718e72258ce2d4d8f2eb60b9e6ac0609d5a041ae43ed11667c8", "8592649d88abd61c9f2b5ac82fc907f98b07075fd487b3c2cd8d7cb764397106", "861d3fd5bab7fcd212409059de944f1487b3ef75ae3fdc9447124934cf520e4f", "86715ac724cfbf6ec5273fe2b4f42cf22ff346c5906cd4126e5097cb06022eec", "89b8b982cfe614149ae76235f00b99534d751f44440a169e9e5548fb635d877a", "8ac64413391d38363537a6c36782bbab5235badebbd0fbaf96fa0009c0409c19", "8c409f36bedfd7fd541127f9f594b4d2c6803f10755bc5f2c5703993d979e80c", "8d482c3e6cd5a539673c28763da02b21d5f22e189e4dce3f0fbad1ffcc554cbe", "8ea0bae1ab64e54b5467b4e412acb8d9babe973adb7c7a4deefe84cb083dbe8a", "8eb65dbe9b82459c4e6129d2f7ae5046db38917bbd792380cfe1c6f4a564fd3e", "907d71dde79dafa79cc7353a91edf33e2093002eab9e216c7317071988af9b3e", "93a38e0d727f2f7a0d77a135d82ecc809c3bb5bd82036469b561e26e62f312b7", "972626e80cdc1aa5c65f4af390b728586b5826a2478e5aa7365ad5e298f1db9b", "97752c6272be9604586b4919bec885b658f58d98dd6ce04406f17ec009786360", "97ec4bdf20886e5d225a7a752d17ec7b16b24f8f56119ea69280439db51ec415", "98e1809325cbd80a2bac752b379b837b9ac541bc874244daa64115ff9f110ea1", "99a539b21b0ca3a973e996b7e2ee58fc72759e3c0d55d35e24679daee491a966", "9b6da3431daae3e618f6b07c268ff5d3af667c9426f203015215eba294e50f24", "9b8fece14fa9955f4f86ef30dbaf8b1daa8f3f3c91dc6d13997b3736cb39fcc5", "9ca623715b821e7d5ea368170340488f3382f4956bf25c98c5993f44879ebd16", "9e89065429de9281d57aa1d1ceecf2aa03cb8bfb5e013f50bfbfe57f13cb5d81", "9edbe98d3e3aa5d4403ac65fe506ca674f587c1487c4707b92606a993d764930", "a03f556f3b411f22959f55ceb6d99773368b955327d80ad41f98260ff9ed11ed", "a09d8d577e3a5ab12cff95d9f6e4fc19f466dae7650313f84fb502e77dbf779b", "a183dcdf002467f66e29e52d0265a6e4c55e8d84df8636387ea9afe94b66256e", "a22895e066a1c777f358b7daa2d8f053a4776a92ced468a4ff2122435de60613", "a373f32b221736d04f6cc43e2db58b455f0974c5ed4a17f1b20c5d038e4a6ca1", "a38aac0b1296d50d567a54cc6e06854826406b560d32b35133bc6a0ff043f990", "a85ace57a1c62fc38b076bad4ce4c6e9f0bae944dff23ce05738441448e7c103", "a9d046e108129ad3c5a2a6fa307df62790b2b491bb77975fbb69c48c345c5425", "aa4b8b3d59e00a8e032f48976c9b509860a2f6ab14bd1b1c30f1f52b47726f4d", "aedbc19b446062d715ddbde454b93a91b95e97686b19c50ff2803b41a3c21f93", "b01996a84a528936c8d313f182acf551215ba112ea9c4b847ed4037920b1a6e6", "b15e33e6c563f7039194a7c1e2b780f29c56f65da223ec408a06ee2ca3ef5b52", "b21bf245c211f7ae2195dc61ff061bfa4e128e4408f929e78f08bcd9c36ac49b", "b2b86171b5860ee7cb5c7b3c026f4aac25a7751dee3742a957e5c5ec39d0a280", "b2e436d4acba3b0c6888e684501e61c4af7f27fabba3d333941b6365f4db451a", "b2ef5cfc09cdc18bca4992c177e2ac969c0fe496fb8650dccea95b86be8de717", "b47f07fa9f9c02030dc733e6e6458f415eaf6c74d393b3a78fbd0b80e7501301", "b5de2778fdaba130bd1fa81b605d1be59b2baa9f2ad54548df3488e2c6651480", "bb7af282f85d5fa83b7672a0310c98ac30a75494d1057b550e5e6c853080d82e", "bbad2a22790314bb026f6d766a1a09e28d640f11eb720852dfaf0a40cc4ddd03", "bc7baeb2db763ad6f5af6de9f2bb52e0e9c5d0c11c035a135089e7a3631a7af2", "bda6b4bff3c4f2862dea40afbad0d8e73acf8faf6e0dbdba888ff546ddf358f3", "bdba234c23bdbd8bb4af9a5eeb01a3c7f504745260be92dbc0cbf29481024d53", "be8233a572fc427ff5bcc2f386a5d229d7c66af2fd46f8042d6e7b0422dc621a", "bf24a2e8492a8b75997e44288ba152e734ca859d5916040bf028fb76debe2fe1", "c06a77d7fe9cb0c21eabf39b5bb6a007c973b2acfa42793ab0757c860d99500d", "c0c7cc4a9f81b94c6c69497d462de00a257101390c3c1c37357cb4a6fe513c70", "c13f224dadbb20b6b92e81bcb58c16c524ab797572edab4f037cb3dc09ad727c", "c19fccb025f5153cf6ddd66f7f72118c10dc6fee38b3288784cfcc30b2144386", "c2b263809cb20ec00c3d88ff11fdbe5538edef02294f54d30b4da74846ea4989", "c2da8d165135808da43071ba4b406aee390d6618ae890d324f00bb2b4baf12ba", "c326c47f2a5b1273d875dabfc89160d4981479f6d61271095bd5bd9fe14df053", "c64aa950d30126c6779d02c3fc7f56f0f780c2be1b52b42d8da4fa31eef07587", "c9ff8b541276cc48f72a7f6f41d3164cebc530f99c7c4d3e2e081d7149d02e18", "cd39a7780f6102fe3375d48b040390780bd4ded415e2a4c48f04f47ab31d4c0e", "ce4dd2be122f0c6af3aa77f204b8ed9f2e4698c3e2d5b700249da211f77998aa", "cf8846e4bf74e86c755f050a2ea23d67d7718999bcc8b248d94412e6c02e779a", "d0218311998c8ffe6d002a6687fe2cce16e303e023cece81b130794f135b1427", "d382ac2c6c4935778f832d97b2ecbb3731c8e52c91a17f9733aecd25c27cb76b", "d4681afed3ca7046450779b3580ddf32be704d9723be999817255d0bf6b9d4f3", "d679cd5370ee5c5abf61496971f75063f0e1145a477d8dd2bcbd73139badcc28", "d7b24c622540b4715297b66b3f5ffe84843786fb0b7738259917a27a9599f3b2", "d7b4e42ed69e561af8a12382d3af241495d2efd3ac6438678b5f608a8744987c", "d8bbd3747acb69372aa8e6da185569a5ebfffda630d712e1c5798f27fa12772f", "da96483016929537d9f343982b8865a4d2407fdc9265dad9f097fafddf6f49b1", "dc26f7b29b6ae88027569a39e8f71b7e8abef7362341ef41f9e2e57d74b6d1f4", "def2ceddcbb98ec8fe82aa9f215ebbd4b0c096a727a1f35444d8f34c73d60e58", "df609126bfabac15c7e6f49aefb77e16c8b08ca3acce85f69ea0d2193f24b1cc", "e00fd036eb1daf4d3703c7f28ab53dc114b77c231c7a628f840b1e1e169fd334", "e011b85461a2fcd31614602bd229b2aaa66e7ecf24dcdace8c2e852578042396", "e204c58abb10b0946e18ba0201873bbff0b07ba198d828828eb2fab5009ec5e0", "e2c3d8d3e3141c3f4211f6e99c0a780012af62836c12ca4726d19b7036fe16e9", "e3677994ece6ea40060aea98bce07b18be33c65dece364fb2da58a2ee1073ab9", "e39640a9f619fe50c5174bd6a9721d4cc0393b84a5818d68e20a69c5ba0ab83a", "e5336b343b4d93d997d89b2c5345eecde072aae68b19bada24733791c8b1c5a9", "e562e578c6c61d1588b9d0aadacaef8684e4393f5f48cb210cfc66b90141af0c", "e834125af3d4d0b6417067a7a4eeadaf1a1fca54ee402a94a98c91c14cfce48f", "e86db6a388b930f8bfa9e39815905184df8581db3cd2702dec0c204f9d44b4ee", "e949e09ee0d2a5bedd46d414e1dbd2a5ead85948bc7e37ef256280b710659226", "e9ba374f8b31f85cf2a88cb1a1459ab7d2f4764ead5669cb4b926d06db16cc59", "eb770f954bd07f1a4cf50ef79d49b18e483a41ccccb44dc3ef15fb8015d89f52", "edb352e0b2bce245c33695085cac531c0a7d82e143148eb09109ad40218a3043", "ef1738f409eaa3d500fa44be440b8ebe17b15d71c67be158727834716cc7db4f", "ef81f162c1b717f62b8c2e7142dfa5d656b9c9c28fb85cfefc049bc0ef7183ab", "f03bba415ffb7890f631bf00ec049f73b33aed026121b4220da263d3f84a5fdb", "f0e2d60c5605af15f282145264af0b79bbcb7646c8adc43532a6dca5d5cfc6bd", "f1bae80e2ed1fd347334853c1ed9015e4d9330bf4a84560f8dc3a61f70efb12b", "f1f7e1114242feec5819bbadd37b8e1ed4b9947c461939580073333742c99088", "f29d827b62f31d405662141a929321ef55b9e4ae36debb5240555631a4d3ad79", "f565e969ec1197d3b732fc2eea504d733013ae36e2382f3753c916eb46368771", "f6508f0da69ea834b97ef33ef031ee6e9534e26fb58a4e1b635e4b171fdcf238", "f780ae7b1c8b61c49484a352a5489f4ebe56da6e4196d62861a094753cd8707b", "f97eadfbb83c6dab13db6536fb13a2d77249df749bf46efa1e3498f7198469fe", "f98142df97b9a6372f10f31d847e155cd4f9b04fd319c31ae3086afa6c5fb67c", "f9bd60ac116381ad711996a82864fc17512a82b7705ef8cd73e072efb7f474b8", "fca6fc0277ad8b20c476766dce5149ce310324d968f000792d9c5655d4451214", "ff1b3ce2d9e61ab7e6fa45cb11a4632fea3fa46deaa044f47fbb80291d26267a"]`

## Closed Schema Digests

- `gptl.core.semantic_types.CanonicalizationPolicy` validation: `40752ab6703738149b83268f55b6f53e334c1a992e117d5d88481240de097dd7`; wire: `40752ab6703738149b83268f55b6f53e334c1a992e117d5d88481240de097dd7`
- `gptl.core.records.GovernedRef` validation: `7f73d84201c71f6df8a461a247702fe0a4d3f725555161a1d85a558e7afea484`; wire: `7f73d84201c71f6df8a461a247702fe0a4d3f725555161a1d85a558e7afea484`
- `gptl.mie.calibration.CalibrationEvaluation` validation: `4f023ba60d030ec89aa9b8d8ad0f1df014e18de9accfcc334b77bfa7e65d8da8`; wire: `4f023ba60d030ec89aa9b8d8ad0f1df014e18de9accfcc334b77bfa7e65d8da8`
- `gptl.mie.schema.RefusalDecision` validation: `9fd724002ce002be59ba8a71d02415be64247c9bcc6a5590dc03726f62eeb26a`; wire: `b471729f83835e8c68ce3bdc41c6ac1c8da50cd69f01a2f6efb9d3bdcb88b2d1`
- `gptl.mie.schema.Tier1Output` validation: `1b5bcebe4b16a9bfbb04ff1cf8f4897b39d74e76652d8dda1400d0f67c9a0b3e`; wire: `8d568f5459172b78814ee13768030c86d39b1b58e533cce8bb2e72c6e0fef11b`
- `gptl.mie.schema.Tier2Output` validation: `ec37b887f68a115f9c55091a63dd021022618ad6a2884f9ff6323f0d8899d086`; wire: `583289e6fef6d73cfa478dd7ba00387b0f9623fc7cf079cb4f002654e851f092`
- `gptl.core.snapshot.KnowledgeSnapshot` validation: `7e3e05e64d26467c8322333598eb2539e35f7c226b1b1f000993857f9be664c3`; wire: `7e3e05e64d26467c8322333598eb2539e35f7c226b1b1f000993857f9be664c3`
- `gptl.core.audit.PreflightRefusalAuditEvent` validation: `a8900da5f37706cdcf3dada0c4f0e03fdb8dcd1892a63396c0d3081dd11bb5c9`; wire: `a8900da5f37706cdcf3dada0c4f0e03fdb8dcd1892a63396c0d3081dd11bb5c9`
- `gptl.core.audit.SnapshotDecisionAuditEvent` validation: `f94aaad2702d44f372f9ac29e0ffe090b724bae12ec81d2b58107ca3d22fb7b5`; wire: `f94aaad2702d44f372f9ac29e0ffe090b724bae12ec81d2b58107ca3d22fb7b5`
- `gptl.core.persistence.ReplayCapsuleRecord` validation: `fe31d8158f7da5563049a9d0a6b0f79fc4189902e2939480dff73352ddc21674`; wire: `fe31d8158f7da5563049a9d0a6b0f79fc4189902e2939480dff73352ddc21674`
- `gptl.mie.replay.ReplayPolicy` validation: `e70fdd622886ceefa5dc932985e2d1a724135b1c7e4e96969fa97b2d93c2c582`; wire: `e70fdd622886ceefa5dc932985e2d1a724135b1c7e4e96969fa97b2d93c2c582`
- `gptl.mie.replay.SafeRefusalReplayRecipe` validation: `04c59deffec2da08137b6c47c755cba2de1df60dbaed8d9ea5a1a06bd27d27c5`; wire: `513471fd11bad21d441a73ae849d2e1be8932555ad50d89e71b4a5feb13fc02b`
- `gptl.mie.replay.CandidatePreservationReplayRecipe` validation: `b0adeea746353e69392d39b8fb6392150557e711c6faa05d60b1239f146ec0cf`; wire: `5e7f777df7ac9cd72aef3e892bff3cbf9b33d455e2d93df5f6092eb5ceebb31e`
- `gptl.mie.replay.MSAGateReplayRecipe` validation: `7304e5ac215916ba7aaf3fa47b75f20b5654046a1d499edfad19cb113b690128`; wire: `df80332098a26c62349376b79b88b2eb46803af431f1fc2060a3a3cd6ab6c6d8`
- `gptl.mie.replay.ArtifactConfirmationReplayRecipe` validation: `033da62abd8f395aec3078e6b5f94a3d6483829acbba95ccacafd699005ce1cd`; wire: `02665e849a4eedfda3226afacf504749e62b072cfa7816a4b8cc4332bb020ee8`
- `gptl.mie.replay.HonestNegativeReplayRecipe` validation: `369cb8644a38f3ce5469460cfbf047109ae61613aaec2c4b310f202cb114c85c`; wire: `afdcbc29541ff803cd85b3d9b61cd631cae85abdd731b01a63c06d3a05234c50`
- `gptl.mie.replay.Tier2AdvisoryReplayRecipe` validation: `81ee87499152fef04e6d66c29557a1ac3636b5d0bb1d7d27ac9caace847f5d8e`; wire: `bfad16fd44e8aacab6a2cf4346d17a155ae964ce7441149b4af79c977ec6f822`
- `gptl.mie.replay.ReplayVerified` validation: `72b667628e06c4a2f7a0398f158a77a03664843e697a5c805ecb050864a95096`; wire: `72b667628e06c4a2f7a0398f158a77a03664843e697a5c805ecb050864a95096`
- `gptl.mie.replay.ReplayIntegrityFailure` validation: `4bee87e70b737ec29a165d4f5fd084e3aae9ae0274a2b08564e44b564d63578b`; wire: `4bee87e70b737ec29a165d4f5fd084e3aae9ae0274a2b08564e44b564d63578b`

## Source and Migration Digests

- Source tree: `8d14e054e03e97fc6910b8c8cd572b2c2c55cb29c1b7f262ee99cfb662f63d3f`
- Migration tree: `e69780ce9630bd220477c5099255bce264bb045b8e9e23d56d1aab756223257d`
- Gate map: `82eac778819ccadf148836d91c14229bbde3e191aeb6990cb15bf70823033792`
- Generator: `ac7c466cd9fcd173fdd65a5a07ff74b5eecc15fe5184145b5e4a2631046a9b2f`

The companion JSON contains the complete per-file source and migration digest inventories.
