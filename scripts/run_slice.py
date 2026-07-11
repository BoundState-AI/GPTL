#!/usr/bin/env python3
"""
Module: Slice Demonstration Runner
Purpose: Local model-free slice demonstrations.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import PostgresRunStore
from gptl.mie.replay import execute_replayable_run, verify_persisted_replay
from gptl.mie.service import execute_safe_refusal
from gptl.mie.slice2_service import execute_candidate_preservation
from gptl.mie.slice3_service import execute_msa_calibration_gate
from gptl.mie.slice4_service import execute_artifact_confirmation
from gptl.mie.slice5_service import execute_honest_negative
from gptl.mie.slice6_service import execute_tier2_advisory
from gptl.slice1_fixture import (
    empty_pack_registry,
    safe_refusal_policy,
    safe_refusal_request,
)
from gptl.slice2_fixture import ratified_runtime, slice2_policy, slice2_request
from gptl.slice3_fixture import slice3_policy, slice3_request, slice3_runtime
from gptl.slice4_fixture import AS_OF, slice4_policy, slice4_request, slice4_runtime
from gptl.slice5_fixture import slice5_policy, slice5_request, slice5_runtime
from gptl.slice6_fixture import slice6_policy, slice6_query, slice6_request, slice6_runtime
from gptl.slice7_fixture import replay_policy, replay_recipes


def run_safe_refusal(database_url: str) -> None:
    policy = safe_refusal_policy()
    request = safe_refusal_request()
    store = PostgresRunStore(database_url, policy.canonicalization_policy)
    store.initialize()
    result = execute_safe_refusal(request, empty_pack_registry(), policy, store)
    persisted = store.load_run(request.run_id)
    if persisted is None:
        raise RuntimeError("safe-refusal run was not persisted")
    output_bytes = canonical_bytes(result.output, policy.canonicalization_policy)
    print(json.dumps(json.loads(output_bytes), indent=2))
    print(json.dumps(json.loads(persisted.audit_payloads[0]), indent=2))


def run_candidate_preservation(database_url: str) -> None:
    policy = slice2_policy()
    request = slice2_request("demo")
    store = PostgresRunStore(database_url, policy.canonicalization_policy)
    store.initialize()
    result = execute_candidate_preservation(
        request,
        ratified_runtime(),
        policy,
        store,
    )
    persisted = store.load_run(request.run_id)
    if persisted is None or persisted.snapshot_payload is None:
        raise RuntimeError("candidate-preservation run was not persisted completely")
    print(
        json.dumps(
            json.loads(canonical_bytes(result.output, policy.canonicalization_policy)), indent=2
        )
    )
    print(json.dumps(json.loads(persisted.snapshot_payload), indent=2))
    print(json.dumps(json.loads(persisted.audit_payloads[0]), indent=2))


def run_msa_gate(database_url: str) -> None:
    policy = slice3_policy()
    request = slice3_request("demo")
    runtime = slice3_runtime("VALID", "QUALIFIED", Decimal("0.0100"), True)
    store = PostgresRunStore(database_url, policy.slice2_policy.canonicalization_policy)
    store.initialize()
    result = execute_msa_calibration_gate(request, runtime, policy, store)
    persisted = store.load_run(request.run_id)
    if persisted is None or persisted.snapshot_payload is None:
        raise RuntimeError("MSA-gate run was not persisted completely")
    print(
        json.dumps(
            json.loads(
                canonical_bytes(
                    result.output,
                    policy.slice2_policy.canonicalization_policy,
                )
            ),
            indent=2,
        )
    )
    print(json.dumps(json.loads(persisted.snapshot_payload), indent=2))
    print(json.dumps(json.loads(persisted.audit_payloads[0]), indent=2))


def run_artifact_confirmation(database_url: str) -> None:
    policy = slice4_policy()
    request = slice4_request("demo", AS_OF)
    runtime = slice4_runtime("STRUCTURED", "NONE", True, "NONE")
    store = PostgresRunStore(
        database_url, policy.slice3_policy.slice2_policy.canonicalization_policy
    )
    store.initialize()
    result = execute_artifact_confirmation(request, runtime, policy, store)
    persisted = store.load_run(request.run_id)
    if persisted is None or persisted.snapshot_payload is None:
        raise RuntimeError("artifact-confirmation run was not persisted completely")
    print(
        json.dumps(
            json.loads(
                canonical_bytes(
                    result.output,
                    policy.slice3_policy.slice2_policy.canonicalization_policy,
                )
            ),
            indent=2,
        )
    )
    print(json.dumps(json.loads(persisted.snapshot_payload), indent=2))
    print(json.dumps(json.loads(persisted.audit_payloads[0]), indent=2))


def run_honest_negative(database_url: str) -> None:
    policy = slice5_policy()
    request = slice5_request("demo")
    runtime = slice5_runtime("COMPLETE")
    store = PostgresRunStore(
        database_url,
        policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    store.initialize()
    result = execute_honest_negative(request, runtime, policy, store)
    persisted = store.load_run(request.run_id)
    if persisted is None or persisted.snapshot_payload is None:
        raise RuntimeError("honest-negative run was not persisted completely")
    print(
        json.dumps(
            json.loads(
                canonical_bytes(
                    result.output,
                    policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy,
                )
            ),
            indent=2,
        )
    )
    print(json.dumps(json.loads(persisted.snapshot_payload), indent=2))
    print(json.dumps(json.loads(persisted.audit_payloads[0]), indent=2))


def run_tier2_advisory(database_url: str) -> None:
    policy = slice6_policy()
    request = slice6_request("demo")
    query = slice6_query("MISSING_MSA")
    runtime = slice6_runtime("MISSING_MSA")
    store = PostgresRunStore(
        database_url,
        policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy,
    )
    store.initialize()
    result = execute_tier2_advisory(request, query, runtime, policy, store)
    persisted = store.load_run(request.run_id)
    if persisted is None or persisted.snapshot_payload is None:
        raise RuntimeError("Tier 2 advisory run was not persisted completely")
    print(
        json.dumps(
            json.loads(
                canonical_bytes(
                    result.output,
                    policy.slice5_policy.slice4_policy.slice3_policy.slice2_policy.canonicalization_policy,
                )
            ),
            indent=2,
        )
    )
    print(json.dumps(json.loads(persisted.snapshot_payload), indent=2))
    print(json.dumps(json.loads(persisted.audit_payloads[0]), indent=2))


def run_replay_integrity(database_url: str, run_id: str | None) -> None:
    policy = replay_policy()
    store = PostgresRunStore(database_url, policy.canonicalization_policy)
    store.initialize()
    if run_id is not None:
        result = verify_persisted_replay(
            f"replay.cli.{run_id}",
            run_id,
            store,
            policy,
        )
        print(
            json.dumps(
                json.loads(canonical_bytes(result, policy.canonicalization_policy)), indent=2
            )
        )
        if result.status != "VERIFIED":
            raise RuntimeError("persisted replay failed integrity verification")
        return
    results = []
    for recipe in replay_recipes():
        execute_replayable_run(recipe, policy, store)
        results.append(
            verify_persisted_replay(
                f"replay.cli.{recipe.request.run_id}",
                recipe.request.run_id,
                store,
                policy,
            )
        )
    if any(item.status != "VERIFIED" for item in results):
        raise RuntimeError("Build 0 replay demonstration failed integrity verification")
    print(
        json.dumps(
            json.loads(canonical_bytes(tuple(results), policy.canonicalization_policy)), indent=2
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario",
        choices=(
            "safe-refusal",
            "candidate-preservation",
            "msa-gate",
            "artifact-confirmation",
            "honest-negative",
            "tier2-advisory",
            "replay-integrity",
        ),
    )
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--run-id")
    arguments = parser.parse_args()
    if arguments.scenario == "safe-refusal":
        run_safe_refusal(arguments.database_url)
    elif arguments.scenario == "candidate-preservation":
        run_candidate_preservation(arguments.database_url)
    elif arguments.scenario == "msa-gate":
        run_msa_gate(arguments.database_url)
    elif arguments.scenario == "artifact-confirmation":
        run_artifact_confirmation(arguments.database_url)
    elif arguments.scenario == "honest-negative":
        run_honest_negative(arguments.database_url)
    elif arguments.scenario == "tier2-advisory":
        run_tier2_advisory(arguments.database_url)
    else:
        run_replay_integrity(arguments.database_url, arguments.run_id)


if __name__ == "__main__":
    main()
