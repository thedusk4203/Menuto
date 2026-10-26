# Reviewed Exact-target Preference Prior Source — Freeze Receipt

Status: **FROZEN / APPROVED**

Freeze decision recorded after independent architecture/freeze review on 2026-10-26.

## Canonical receipt

- repository: `thedusk4203/Menuto`
- implementation PR: #97
- implementation commit: `2c97d8e09141e0d528c96625717f51189569016c`
- final PR head: `ebcbf7d21e4b32e41053a9864052ecb8022dfe5f`
- canonical merge/freeze SHA: `fce85327cc8c3f4444847522d8ef474ef8d4e670`
- exact post-merge CI: `40293195051`, SUCCESS on the canonical SHA
- migration: `0014`
- schema: `0014 / 78 domain tables`
- exported definitions: `299 = 276 retained + 23 additive`
- full tests: `2377 passed`
- retained prior test identities: `2237 / 2237`
- additive tests: `140`
- PostgreSQL-real tests: `918`
- new SCRAM/source PostgreSQL cases: `120`
- explicit authority/authentication cases: `73`
- benchmark: `22/22`
- client: `10/10`

## Frozen semantic scope

The frozen source provides:

1. canonical reviewed exact-target reference-prior publication/retraction;
2. provider-scoped PostgreSQL-authenticated `REVIEW_PUBLISH`, `RETRACT`, and `CAPTURE` authority;
3. immutable provider/principal/authority/publication/mutation/stream/frontier facts;
4. distinct `ReferencePriorAmount` coordinate semantics;
5. exact `PreferenceTarget` identity for INGREDIENT / DIRECT_RECIPE / PROTEIN / METHOD / FLAVOR;
6. one explicitly selected provider per capture;
7. explicit `NO_PUBLICATION != RETRACTED != AVAILABLE 0/1` missingness semantics;
8. coherent complete-provider read-only capture;
9. zero-IO independent replay/resolution;
10. real database privilege/direct-SQL/SCRAM/concurrency enforcement evidence.

The source remains separate from member preference authorship and does not convert shared reference data into a member declaration or EvidenceStrength.

## Frozen non-goals / unavailable outputs

This freeze does not authorize or provide:

- production prior values;
- automatic provider selection/fallback/aggregation;
- reference-to-explicit coordinate conversion;
- shrinkage;
- hierarchical/cross-target preference inference;
- learned/contextual/passive evidence;
- MemberBehaviorProfile completion;
- TasteFit or candidate ranking;
- MTR-024 utility composition;
- MTR-020B role portfolio;
- MTR-021 feasibility;
- Execution;
- PRECOMMIT authority.

Frozen 040B continues to return prior/shrinkage as unavailable. The source capability existing or later being populated must not silently modify frozen 040B semantics.

## Compatibility

- migrations `0001–0013` remain frozen/byte-compatible;
- 276 pre-source exported definitions remain structurally compatible;
- frozen MTR-040A/B, MTR-041A/B/C/D/E/F and MTR-046A semantics remain unchanged;
- migration `0014` creates an empty capable source and seeds no provider, principal, capability grant, prior amount, neutral/default prior, credential or production policy value.

## Superseded historical status wording

Earlier documents may contain `IMPLEMENTED / NOT FROZEN` because they are implementation-delivery records written before this architecture decision. Those lines remain historical evidence of the pre-review state.

For current canonical status, this freeze receipt and `POST_PREFERENCE_PRIOR_SOURCE_DEPENDENCY_REVIEW.md` supersede only that delivery-status wording; they do not rewrite historical implementation evidence or alter runtime semantics.

## Next boundary

The next selected work is **design only** for:

`Exact-target Prior Compatibility & Shrinkage Foundation`

Implementation is not authorized by this freeze.
