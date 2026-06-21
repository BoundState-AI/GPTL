# GPTL

Canonical architecture and implementation contracts for the BoundState General Purpose Translation Layer.

Current governing specification:

- [GPTL Manufacturing Intelligence Platform v0.4.4](docs/GPTL_Manufacturing_Platform_v0.4.4.md)
- [MIE Build 0 vertical-slice plan v0.4](docs/GPTL_BUILD_PLAN_v0.4.md)

Immutable ORACLE review input:

- [MIE Build 0 vertical-slice plan v0.1](docs/GPTL_BUILD_PLAN_v0.1.md)
- [Single-file specification/build review bundle v0.1](docs/GPTL_ORACLE_BUILD_REVIEW_v0.1.md)

Prior immutable revision:

- [GPTL Manufacturing Intelligence Platform v0.4.3](docs/GPTL_Manufacturing_Platform_v0.4.3.md)

v0.4.4 defines the owner-ratified platform architecture and the deterministic, vector-free, model-optional, `RESEARCH_ONLY` MIE Build 0 contract. Production method knowledge, vendor instrument adapters, and qualification are explicitly later work.

For ORACLE review, upload the single-file review bundle without a rule pack. Regenerate it deterministically after source edits with `python3 scripts/build_oracle_bundle.py`.
