# GPTL Slice 1 Claude Review Disposition

**Review basis:** `Slice 1 - Safe Refusal Review`

**Code basis reviewed here:** `be00dd4`

**Disposition:** Valid findings resolved. No Slice 2 work began during this review.

## Major Findings

| Finding | Disposition | Resolution |
|---|---|---|
| M1: Decimal `+2` and `28` magic values | Already resolved before this review landed | `be00dd4` removed both values. Decimal precision is derived from governed scale and maximum integer digits, with a named carry digit required by rounding. Signed zero is canonicalized. |
| M2: hardcoded `/tmp` | Accepted in principle; proposed fix rejected | Dropping the directory override reproduces the observed WSL failure because Windows `TEMP` points Linux PostgreSQL at drvfs, which cannot enforce mode `0700`. The fixture now tries the platform temp directory, verifies its permission semantics, retries under the dynamically resolved home directory, and otherwise fails explicitly. No absolute path remains. |
| M3: stale ORACLE bundle inputs | Recommendation rejected; ambiguity fixed | The v0.1 bundle is an immutable historical review artifact, so repointing its builder to v0.4.5/v0.5 would corrupt its identity. The script is renamed `rebuild_oracle_bundle_v0_1.py`, and the README states that it intentionally uses historical inputs. |
| M4: persisted schema/record metadata not verified | Accepted | `load_run` now verifies run and audit record type, schema version, and hash algorithm before returning data. Verified run metadata is surfaced in `StoredRun`; round-trip and adversarial database tests cover it. |
| M5: migration-integrity branches untested | Accepted; idempotency was already covered | Integration tests now cover empty migration history and checksum drift. Existing tests cover repeated initialization, exact-prefix ordering, immutable migration checksums, and unknown/out-of-order history. |

## Minor Findings

| Finding | Disposition | Resolution |
|---|---|---|
| Decorative safety-critical headers / NASA reference | Rejected | Neither is a governing GPTL requirement. Cargo-cult labels add no enforcement and conflict with the load-bearing-comment standard. |
| Same-process reconnect only | Accepted | A fresh Python process now loads and verifies the persisted run and audit event. |
| Required directive parameter and wrong-kind branches untested | Accepted | Both branches now have regression tests. |
| More docstrings requested | Rejected | Names and types already explain mechanics. Comments remain limited to non-obvious domain or invariant reasoning. |
| Duplicate directive validation in service | Accepted | Validation remains at `SafeRefusalPolicy` construction; the redundant call was removed. |
| Pydantic hook parameter name | Accepted | Renamed to `context`. |
| `exclude_none=True` could collapse future null semantics | Not a Slice 1 defect | Slice 1 has no authoritative field where null and absence are distinct. Any future such field requires an explicit schema and canonicalization decision before publication. |
| End-to-end Unicode decision fixture | Not representable in Slice 1 | Every authoritative Slice 1 string is an ASCII-constrained identifier or enum. NFC behavior remains covered at the canonicalization boundary where Unicode is accepted. |
| `audit_count > 0` untested | Accepted | A direct PostgreSQL zero-count insert is now required to fail its database constraint. |

## Exit Evidence

- No confidence, confidence interval, probability, or float can enter the Slice 1 refusal payload.
- No SQLite, vector retrieval, model authority, application database default, or absolute test path exists in the Slice 1 path.
- PostgreSQL tests exercise atomic rollback, append-only mutation rejection, truncate rejection, deferred audit cardinality, metadata integrity, migration drift, custom schemas, and cross-process durability.
- Release verification completed with Ruff, strict mypy, warnings-as-errors, Python 3.10/3.12 tests, lock validation, and wheel-content inspection.
