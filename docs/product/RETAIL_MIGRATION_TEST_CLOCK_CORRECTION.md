# Retail migration test clock correction

Observed while recording the user-approved MTR-041A freeze (PR #74).
Canonical runtime baseline remains `774405ebe51f126fec10ce61c4dd41b9d229230a`.

CI run40068534328: Python had1 failure/1402 passes; web passed. The failing existing test was
`test_populated_upgrade_preserves_source_pair_status_and_legacy_flags`. Local reproduction at
the unchanged canonical baseline also failed (1 failed in1.87s).

Retail fixture NOW is2026-10-22 UTC. The test queried status at NOW+2 days,2026-10-24 midnight.
Frozen0004 correctly preserves the legacy retailer's actual created_at as effective_at and
observed_at; that source row is created at DB wall time during the test. Once execution passed
the fixed query date, the test asked for a status before the retailer existed. Returning None
was correct. This is a test clock defect, not a frozen domain/architecture contradiction.

The test now captures the source retailer's created_at before migration and queries exactly at
that timestamp. It additionally checks no status exists one microsecond earlier, and that both
effective_at/observed_at preserve the original timestamp. All existing source/mapping/price/
status/provenance/legacy-assessment assertions remain. No skips, weakened assertions, fixture
date bump, runtime change, contract change or migration edit.

Schema remains0012 /58 tables. Migrations0001–0012 and MTR-041A/040A semantics are unchanged.
This isolated test correction does not start MTR-024, Execution or any new architecture slice.

Executed locally: **16/16 PostgreSQL Retail correction tests passed** in10.28s after reproducing
baseline failure. Ruff and whitespace checks pass. Full CI runs on the isolated test-only PR;
its exact PR/run and the later freeze-record CI are reported at delivery.
