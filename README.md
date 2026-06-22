# GPTL

Canonical architecture and implementation contracts for the BoundState General Purpose Translation Layer.

Current governing specification:

- [GPTL Manufacturing Intelligence Platform v0.4.15](docs/GPTL_Manufacturing_Platform_v0.4.15.md)
- [MIE Build 0 vertical-slice plan v0.16](docs/GPTL_BUILD_PLAN_v0.16.md)

Most recent immutable ORACLE review input:

- [Build 0 completion review bundle v1.0](docs/GPTL_ORACLE_BUILD0_COMPLETION_REVIEW_v1.0.md)

Prior immutable ORACLE review input:

- [MIE Build 0 vertical-slice plan v0.1](docs/GPTL_BUILD_PLAN_v0.1.md)
- [Single-file specification/build review bundle v0.1](docs/GPTL_ORACLE_BUILD_REVIEW_v0.1.md)

Prior immutable revision:

- [MIE Build 0 vertical-slice plan v0.15](docs/GPTL_BUILD_PLAN_v0.15.md)
- [GPTL Manufacturing Intelligence Platform v0.4.14](docs/GPTL_Manufacturing_Platform_v0.4.14.md)
- [MIE Build 0 vertical-slice plan v0.14](docs/GPTL_BUILD_PLAN_v0.14.md)
- [GPTL Manufacturing Intelligence Platform v0.4.13](docs/GPTL_Manufacturing_Platform_v0.4.13.md)
- [MIE Build 0 vertical-slice plan v0.13](docs/GPTL_BUILD_PLAN_v0.13.md)
- [GPTL Manufacturing Intelligence Platform v0.4.12](docs/GPTL_Manufacturing_Platform_v0.4.12.md)
- [MIE Build 0 vertical-slice plan v0.12](docs/GPTL_BUILD_PLAN_v0.12.md)
- [GPTL Manufacturing Intelligence Platform v0.4.11](docs/GPTL_Manufacturing_Platform_v0.4.11.md)
- [MIE Build 0 vertical-slice plan v0.11](docs/GPTL_BUILD_PLAN_v0.11.md)
- [GPTL Manufacturing Intelligence Platform v0.4.10](docs/GPTL_Manufacturing_Platform_v0.4.10.md)
- [MIE Build 0 vertical-slice plan v0.10](docs/GPTL_BUILD_PLAN_v0.10.md)
- [GPTL Manufacturing Intelligence Platform v0.4.9](docs/GPTL_Manufacturing_Platform_v0.4.9.md)
- [MIE Build 0 vertical-slice plan v0.9](docs/GPTL_BUILD_PLAN_v0.9.md)
- [GPTL Manufacturing Intelligence Platform v0.4.8](docs/GPTL_Manufacturing_Platform_v0.4.8.md)
- [MIE Build 0 vertical-slice plan v0.8](docs/GPTL_BUILD_PLAN_v0.8.md)
- [GPTL Manufacturing Intelligence Platform v0.4.7](docs/GPTL_Manufacturing_Platform_v0.4.7.md)
- [MIE Build 0 vertical-slice plan v0.7](docs/GPTL_BUILD_PLAN_v0.7.md)
- [GPTL Manufacturing Intelligence Platform v0.4.6](docs/GPTL_Manufacturing_Platform_v0.4.6.md)
- [MIE Build 0 vertical-slice plan v0.6](docs/GPTL_BUILD_PLAN_v0.6.md)
- [GPTL Manufacturing Intelligence Platform v0.4.5](docs/GPTL_Manufacturing_Platform_v0.4.5.md)
- [MIE Build 0 vertical-slice plan v0.5](docs/GPTL_BUILD_PLAN_v0.5.md)
- [GPTL Manufacturing Intelligence Platform v0.4.4](docs/GPTL_Manufacturing_Platform_v0.4.4.md)
- [MIE Build 0 vertical-slice plan v0.4](docs/GPTL_BUILD_PLAN_v0.4.md)
- [GPTL Manufacturing Intelligence Platform v0.4.3](docs/GPTL_Manufacturing_Platform_v0.4.3.md)

v0.4.15 defines the owner-ratified platform architecture and the deterministic, vector-free, model-optional, PostgreSQL-backed, `RESEARCH_ONLY` MIE Build 0 contract. Production method knowledge, vendor instrument adapters, and qualification are explicitly later work.

Slice 1 implements deterministic safe refusal. Slice 2 adds governed candidate preservation and snapshot-bound PostgreSQL persistence. Slice 3 adds deterministic calibration and qualified, scope-matched MSA hard gates. Slice 4 adds governed signature scoring, commutative discriminator aggregation, structured and attested confirmation, and cited `METHOD_ARTIFACT` research verdicts. Slice 5 adds governed hard elimination, evidence-complete rule-out, and cited bounded-catalog negative verdicts. Slice 6 adds deterministic model-free Tier 2 method resolution and eligibility guidance. Slice 7 closes Build 0 with exact-input historical replay, tamper/missing-content refusal, and explicit pack evolution.

```bash
uv sync --group dev
uv run ruff check src tests scripts/run_slice.py
uv run ruff format --check src tests scripts/run_slice.py
uv run mypy src
uv run pytest -q
uv run python scripts/run_slice.py safe-refusal --database-url "$GPTL_DATABASE_URL"
uv run python scripts/run_slice.py candidate-preservation --database-url "$GPTL_DATABASE_URL"
uv run python scripts/run_slice.py msa-gate --database-url "$GPTL_DATABASE_URL"
uv run python scripts/run_slice.py artifact-confirmation --database-url "$GPTL_DATABASE_URL"
uv run python scripts/run_slice.py honest-negative --database-url "$GPTL_DATABASE_URL"
uv run python scripts/run_slice.py tier2-advisory --database-url "$GPTL_DATABASE_URL"
uv run python scripts/run_slice.py replay-integrity --database-url "$GPTL_DATABASE_URL"
```

The database URL is mandatory. There is no embedded-database fallback or application default. `scripts/rebuild_oracle_build0_completion_bundle_v1_0.py` reproduces the current completion-review bundle from the active contract. The ORACLE v0.1 review bundle remains an immutable historical review input; `scripts/rebuild_oracle_bundle_v0_1.py` reproduces that artifact and intentionally does not use the active contract.
