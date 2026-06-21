#!/usr/bin/env python3
"""Local model-free slice demonstrations."""

from __future__ import annotations

import argparse
import json

from gptl.core.canonical import canonical_bytes
from gptl.core.persistence import PostgresRunStore
from gptl.mie.service import execute_safe_refusal
from gptl.slice1_fixture import (
    empty_pack_registry,
    safe_refusal_policy,
    safe_refusal_request,
)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=("safe-refusal",))
    parser.add_argument("--database-url", required=True)
    arguments = parser.parse_args()
    run_safe_refusal(arguments.database_url)


if __name__ == "__main__":
    main()
