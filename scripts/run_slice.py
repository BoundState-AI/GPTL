#!/usr/bin/env python3
"""Local model-free slice demonstrations."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import PostgresRunStore
from gptl.mie.service import execute_safe_refusal
from gptl.mie.slice2_service import execute_candidate_preservation
from gptl.mie.slice3_service import execute_msa_calibration_gate
from gptl.mie.slice4_service import execute_artifact_confirmation
from gptl.slice1_fixture import (
    empty_pack_registry,
    safe_refusal_policy,
    safe_refusal_request,
)
from gptl.slice2_fixture import ratified_runtime, slice2_policy, slice2_request
from gptl.slice3_fixture import slice3_policy, slice3_request, slice3_runtime
from gptl.slice4_fixture import AS_OF, slice4_policy, slice4_request, slice4_runtime


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario",
        choices=(
            "safe-refusal",
            "candidate-preservation",
            "msa-gate",
            "artifact-confirmation",
        ),
    )
    parser.add_argument("--database-url", required=True)
    arguments = parser.parse_args()
    if arguments.scenario == "safe-refusal":
        run_safe_refusal(arguments.database_url)
    elif arguments.scenario == "candidate-preservation":
        run_candidate_preservation(arguments.database_url)
    elif arguments.scenario == "msa-gate":
        run_msa_gate(arguments.database_url)
    else:
        run_artifact_confirmation(arguments.database_url)


if __name__ == "__main__":
    main()
