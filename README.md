# GPTL

Canonical architecture and implementation contracts for the BoundState General Purpose Translation Layer.

Current governing specification:

- [GPTL Manufacturing Intelligence Platform v0.4.9](docs/GPTL_Manufacturing_Platform_v0.4.9.md)
- [MIE Build 0 vertical-slice plan v0.9](docs/GPTL_BUILD_PLAN_v0.9.md)

Immutable ORACLE review input:

- [MIE Build 0 vertical-slice plan v0.1](docs/GPTL_BUILD_PLAN_v0.1.md)
- [Single-file specification/build review bundle v0.1](docs/GPTL_ORACLE_BUILD_REVIEW_v0.1.md)

Prior immutable revision:

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

v0.4.9 defines the owner-ratified platform architecture and the deterministic, vector-free, model-optional, PostgreSQL-backed, `RESEARCH_ONLY` MIE Build 0 contract. Production method knowledge, vendor instrument adapters, and qualification are explicitly later work.

Slice 1 implements deterministic safe refusal. Slice 2 adds governed candidate preservation and snapshot-bound PostgreSQL persistence. Slice 3 adds deterministic calibration and qualified, scope-matched MSA hard gates. Slice 4 adds governed signature scoring, commutative discriminator aggregation, structured and attested confirmation, and cited `METHOD_ARTIFACT` research verdicts.

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
```

The database URL is mandatory. There is no embedded-database fallback or application default. The ORACLE v0.1 review bundle remains an immutable historical review input; `scripts/rebuild_oracle_bundle_v0_1.py` reproduces that artifact and intentionally does not use the active contract.
