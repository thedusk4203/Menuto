# Identity catalog-cut correction — reproduction and execution evidence

**Author-executed diagnostics only / no independent acceptance / no implementation resumption**.

Canonical baseline120d28f62b66720e8631b64e0b2a50cdc57e6c42. Governing [correction](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md).
The complete [historical blocker](IDENTITY_CATALOG_CUT_FRESHNESS_IMPLEMENTATION_BLOCKER.md) is preserved.

## What was and was not executed

This new diagnostic used actual disposable PostgreSQL18.4 (server_version_num180004), real
SCRAM/verify-full loopback sessions, two scratch databases in one cluster and a dummy actor.
It made native TEST_ONLY parameter ACL GRANT/REVOKE operations only. It installed **no Identity
migration, table, function or entry**, changed no implementation runtime/test and added no repository
SQL/session/privilege mechanism. It executed no ALTER SYSTEM setting change. The cluster was stopped
in finally; the transient credentials/certificate private key are not published.

There are8native cut cases (2isolations x2writer databases xGRANT/REVOKE), plus1observed-mismatch
native predicate case. The additional7checker cases read the unchanged draft and explicit synthetic
TEST_ONLY fixtures, with bytecode writes disabled. They are pure/offline, **not real-PG Identity
integration tests or canonical-origin evidence**. The new42501guard and40001predicate are anonymous
test-local DO blocks, not the actual protected Identity entry. Do not mislabel them.

The earlier actual protected-entry diagnostic and86-case run are retained separately below. They
were not rerun or repaired here. The new native experiment substantiates catalog visibility; it does
not complete live protected-entry acceptance under the corrected design. ITR018/040/041/055/066 and
all other implementation obligations remain subject to future separately authorized execution.

## Measured transaction ordering

For each case: BEGIN READ ONLY RR/SERIALIZABLE; first query establishes pg_current_snapshot and
records DB/PID/time; enumerate the complete pg_parameter_acl; writer starts its own transaction,
records pg_current_xact_id, GRANTs/REVOKEs and commits; separate writer query confirms commit time
and actual native actor right; original reader enumerates again and records its same snapshot;
original transaction ends; a genuinely fresh reader transaction records a new snapshot/catalog;
finally a new native guard transaction tests explicit actor permission. No wall-clock ordering is
inferred from equal hashes; the sequential transaction steps are explicit in the harness.

For REVOKE, the actor starts with an unsafe extra SQL privilege. Historical unsafe observations
stay unsafe, although the new cut after REVOKE is safe for this isolated parameter-ACL predicate.
This is **not** an AVAILABLE Identity source; an unsafe requester would be rejected without sources.
The native control says nothing about root/binding/operation enrollment or later consumer admission.

| Diagnostic case | Initial snapshot | Writer XID | Commit confirmed at | End snapshot | Fresh snapshot | Retained/current extra ACL | Fresh native guard SQLSTATE |
|---|---|---|---|---|---|---|---|
| REPEATABLE_READ_itr_cut_a_GRANT | 756:756: | 756 | 2026-11-16 20:57:04.337709+07 | 756:756: | 757:757: | False / True | 42501 |
| REPEATABLE_READ_itr_cut_a_REVOKE | 759:759: | 759 | 2026-11-16 20:57:04.659758+07 | 759:759: | 760:760: | True / False | 00000 |
| REPEATABLE_READ_itr_cut_b_GRANT | 760:760: | 760 | 2026-11-16 20:57:04.867053+07 | 760:760: | 761:761: | False / True | 42501 |
| REPEATABLE_READ_itr_cut_b_REVOKE | 763:763: | 763 | 2026-11-16 20:57:05.196951+07 | 763:763: | 764:764: | True / False | 00000 |
| SERIALIZABLE_itr_cut_a_GRANT | 764:764: | 764 | 2026-11-16 20:57:05.407622+07 | 764:764: | 765:765: | False / True | 42501 |
| SERIALIZABLE_itr_cut_a_REVOKE | 767:767: | 767 | 2026-11-16 20:57:05.595602+07 | 767:767: | 768:768: | True / False | 00000 |
| SERIALIZABLE_itr_cut_b_GRANT | 768:768: | 768 | 2026-11-16 20:57:05.876424+07 | 768:768: | 769:769: | False / True | 42501 |
| SERIALIZABLE_itr_cut_b_REVOKE | 771:771: | 771 | 2026-11-16 20:57:06.050069+07 | 771:771: | 772:772: | True / False | 00000 |

All8same-cut before/after catalog arrays are equal;4post-GRANT fresh guard checks reject42501;
4post-REVOKE fresh guard checks return00000 for this ACL predicate only. DatabaseB mutations affect
fresh observations in databaseA, proving same-cluster shared-catalog behavior. The9th native case
compares two actually different committed observations and raises40001 with null payload. It
**intentionally uses different cuts** to exercise the observed-mismatch predicate and is not a
single-source capture assembled from those cuts.

## Raw new observations and independent results

These complete parameter observations carry actual transient rowOID/grantor/grantee facts. They
are diagnostic data, never proposed production constants or Identity contract additions.

```json
{
  "purpose": "DOCS_ONLY_NATIVE_MVCC_DIAGNOSTIC_NOT_ITR_ACCEPTANCE",
  "cases": [
    {
      "id": "REPEATABLE_READ_itr_cut_a_GRANT",
      "reader_start": {
        "snapshot_id": "756:756:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 31472,
        "observed_at": "2026-11-16 20:57:04.33229+07"
      },
      "reader_end": {
        "snapshot_id": "756:756:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 31472,
        "observed_at": "2026-11-16 20:57:04.338771+07"
      },
      "writer_database": "itr_cut_a",
      "writer_xid": "756",
      "commit_confirmed_at": "2026-11-16 20:57:04.337709+07",
      "complete_catalog_before": [],
      "complete_catalog_after": [],
      "before_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "after_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "native_current_extra_acl": true,
      "retained_extra_acl": false,
      "fresh_cut": {
        "snapshot_id": "757:757:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 42680,
        "observed_at": "2026-11-16 20:57:04.490025+07"
      },
      "fresh_complete_catalog": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16387,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_faa950eb7c2e",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "fresh_guard_sqlstate": "42501",
      "retained_meaning": "HISTORICAL_NO_EXTRA_ACL_ONLY",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "REPEATABLE_READ_itr_cut_a_REVOKE",
      "reader_start": {
        "snapshot_id": "759:759:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 41076,
        "observed_at": "2026-11-16 20:57:04.653383+07"
      },
      "reader_end": {
        "snapshot_id": "759:759:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 41076,
        "observed_at": "2026-11-16 20:57:04.661486+07"
      },
      "writer_database": "itr_cut_a",
      "writer_xid": "759",
      "commit_confirmed_at": "2026-11-16 20:57:04.659758+07",
      "complete_catalog_before": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16388,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_0a966d8e4d63",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "complete_catalog_after": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16388,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_0a966d8e4d63",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "before_hash": "e29db2f08b4b8695ee98ecdf486d2f212f858fe0a81064fa7b0cd875561286a9",
      "after_hash": "e29db2f08b4b8695ee98ecdf486d2f212f858fe0a81064fa7b0cd875561286a9",
      "native_current_extra_acl": false,
      "retained_extra_acl": true,
      "fresh_cut": {
        "snapshot_id": "760:760:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 41632,
        "observed_at": "2026-11-16 20:57:04.709855+07"
      },
      "fresh_complete_catalog": [],
      "fresh_guard_sqlstate": "00000",
      "retained_meaning": "HISTORICAL_UNSAFE_NO_IDENTITY_SOURCE",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "REPEATABLE_READ_itr_cut_b_GRANT",
      "reader_start": {
        "snapshot_id": "760:760:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 43820,
        "observed_at": "2026-11-16 20:57:04.859189+07"
      },
      "reader_end": {
        "snapshot_id": "760:760:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 43820,
        "observed_at": "2026-11-16 20:57:04.8684+07"
      },
      "writer_database": "itr_cut_b",
      "writer_xid": "760",
      "commit_confirmed_at": "2026-11-16 20:57:04.867053+07",
      "complete_catalog_before": [],
      "complete_catalog_after": [],
      "before_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "after_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "native_current_extra_acl": true,
      "retained_extra_acl": false,
      "fresh_cut": {
        "snapshot_id": "761:761:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 33400,
        "observed_at": "2026-11-16 20:57:04.9144+07"
      },
      "fresh_complete_catalog": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16389,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_272d826d781d",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "fresh_guard_sqlstate": "42501",
      "retained_meaning": "HISTORICAL_NO_EXTRA_ACL_ONLY",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "REPEATABLE_READ_itr_cut_b_REVOKE",
      "reader_start": {
        "snapshot_id": "763:763:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 4660,
        "observed_at": "2026-11-16 20:57:05.190976+07"
      },
      "reader_end": {
        "snapshot_id": "763:763:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 4660,
        "observed_at": "2026-11-16 20:57:05.198276+07"
      },
      "writer_database": "itr_cut_b",
      "writer_xid": "763",
      "commit_confirmed_at": "2026-11-16 20:57:05.196951+07",
      "complete_catalog_before": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16390,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_0d9f0e419c8c",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "complete_catalog_after": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16390,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_0d9f0e419c8c",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "before_hash": "c9f0e631fa89dee2130044187da0b94854859f8f56933eaf729c7c5a27a382ea",
      "after_hash": "c9f0e631fa89dee2130044187da0b94854859f8f56933eaf729c7c5a27a382ea",
      "native_current_extra_acl": false,
      "retained_extra_acl": true,
      "fresh_cut": {
        "snapshot_id": "764:764:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 38452,
        "observed_at": "2026-11-16 20:57:05.25546+07"
      },
      "fresh_complete_catalog": [],
      "fresh_guard_sqlstate": "00000",
      "retained_meaning": "HISTORICAL_UNSAFE_NO_IDENTITY_SOURCE",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "SERIALIZABLE_itr_cut_a_GRANT",
      "reader_start": {
        "snapshot_id": "764:764:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 14352,
        "observed_at": "2026-11-16 20:57:05.400004+07"
      },
      "reader_end": {
        "snapshot_id": "764:764:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 14352,
        "observed_at": "2026-11-16 20:57:05.408925+07"
      },
      "writer_database": "itr_cut_a",
      "writer_xid": "764",
      "commit_confirmed_at": "2026-11-16 20:57:05.407622+07",
      "complete_catalog_before": [],
      "complete_catalog_after": [],
      "before_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "after_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "native_current_extra_acl": true,
      "retained_extra_acl": false,
      "fresh_cut": {
        "snapshot_id": "765:765:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 27820,
        "observed_at": "2026-11-16 20:57:05.453284+07"
      },
      "fresh_complete_catalog": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16391,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_c60c5f9e8a2f",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "fresh_guard_sqlstate": "42501",
      "retained_meaning": "HISTORICAL_NO_EXTRA_ACL_ONLY",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "SERIALIZABLE_itr_cut_a_REVOKE",
      "reader_start": {
        "snapshot_id": "767:767:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 38460,
        "observed_at": "2026-11-16 20:57:05.591248+07"
      },
      "reader_end": {
        "snapshot_id": "767:767:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 38460,
        "observed_at": "2026-11-16 20:57:05.596727+07"
      },
      "writer_database": "itr_cut_a",
      "writer_xid": "767",
      "commit_confirmed_at": "2026-11-16 20:57:05.595602+07",
      "complete_catalog_before": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16392,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_da2f17bae25f",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "complete_catalog_after": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16392,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_da2f17bae25f",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "before_hash": "1c44183b9437fa65f6d506ff8a43f9929498c394bfe3e9681e2042827657f49a",
      "after_hash": "1c44183b9437fa65f6d506ff8a43f9929498c394bfe3e9681e2042827657f49a",
      "native_current_extra_acl": false,
      "retained_extra_acl": true,
      "fresh_cut": {
        "snapshot_id": "768:768:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 20496,
        "observed_at": "2026-11-16 20:57:05.739303+07"
      },
      "fresh_complete_catalog": [],
      "fresh_guard_sqlstate": "00000",
      "retained_meaning": "HISTORICAL_UNSAFE_NO_IDENTITY_SOURCE",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "SERIALIZABLE_itr_cut_b_GRANT",
      "reader_start": {
        "snapshot_id": "768:768:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 17524,
        "observed_at": "2026-11-16 20:57:05.870676+07"
      },
      "reader_end": {
        "snapshot_id": "768:768:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 17524,
        "observed_at": "2026-11-16 20:57:05.877264+07"
      },
      "writer_database": "itr_cut_b",
      "writer_xid": "768",
      "commit_confirmed_at": "2026-11-16 20:57:05.876424+07",
      "complete_catalog_before": [],
      "complete_catalog_after": [],
      "before_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "after_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
      "native_current_extra_acl": true,
      "retained_extra_acl": false,
      "fresh_cut": {
        "snapshot_id": "769:769:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 43160,
        "observed_at": "2026-11-16 20:57:05.91881+07"
      },
      "fresh_complete_catalog": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16393,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_14e8698e701e",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "fresh_guard_sqlstate": "42501",
      "retained_meaning": "HISTORICAL_NO_EXTRA_ACL_ONLY",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "SERIALIZABLE_itr_cut_b_REVOKE",
      "reader_start": {
        "snapshot_id": "771:771:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 38664,
        "observed_at": "2026-11-16 20:57:06.046478+07"
      },
      "reader_end": {
        "snapshot_id": "771:771:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 38664,
        "observed_at": "2026-11-16 20:57:06.051109+07"
      },
      "writer_database": "itr_cut_b",
      "writer_xid": "771",
      "commit_confirmed_at": "2026-11-16 20:57:06.050069+07",
      "complete_catalog_before": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16394,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_2388cd58fbaa",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "complete_catalog_after": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16394,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.diag_2388cd58fbaa",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "before_hash": "0717a4474b50bc06cbb4913957ebbfecb1cc6c98c523e004f4e5f2847b514880",
      "after_hash": "0717a4474b50bc06cbb4913957ebbfecb1cc6c98c523e004f4e5f2847b514880",
      "native_current_extra_acl": false,
      "retained_extra_acl": true,
      "fresh_cut": {
        "snapshot_id": "772:772:",
        "database_oid": 16385,
        "database_name": "itr_cut_a",
        "backend_pid": 39632,
        "observed_at": "2026-11-16 20:57:06.092392+07"
      },
      "fresh_complete_catalog": [],
      "fresh_guard_sqlstate": "00000",
      "retained_meaning": "HISTORICAL_UNSAFE_NO_IDENTITY_SOURCE",
      "transport": "UNVERIFIED_TRANSPORT",
      "numerical_use": "NOT_ADMITTED",
      "identity_migration_installed": false
    },
    {
      "id": "OBSERVED_DISTINCT_CUT_ACL_MISMATCH",
      "before": [],
      "after": [
        {
          "version": 1,
          "kind": "PARAMETER",
          "object_oid": 16395,
          "sub_id": 0,
          "schema_name": null,
          "object_name": "menuto_itr.observed_344ef3a75137",
          "owner_oid": null,
          "definition_fingerprint": null,
          "acl": [
            [
              10,
              10,
              "ALTER SYSTEM",
              false
            ],
            [
              10,
              10,
              "SET",
              false
            ],
            [
              16384,
              10,
              "ALTER SYSTEM",
              false
            ]
          ]
        }
      ],
      "sqlstate": "40001",
      "payload": null,
      "scope": "NATIVE_DIAGNOSTIC_PREDICATE_NOT_IDENTITY_PROTECTED_ENTRY"
    }
  ],
  "independent_cases": [
    {
      "id": "UNCHANGED_DRAFT_OFFLINE_CONTROL",
      "decision": "CONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "transport": "UNVERIFIED_TRANSPORT",
      "source": "EXPLICIT_TEST_ONLY_SYNTHETIC_FIXTURE_NOT_CANONICAL_DATABASE"
    },
    {
      "id": "omitted_routine",
      "decision": "INCONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "reconstructed_outcome": null,
      "source": "UNCHANGED_DRAFT_TEST_ONLY_FIXTURE"
    },
    {
      "id": "substituted_oid",
      "decision": "INCONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "reconstructed_outcome": null,
      "source": "UNCHANGED_DRAFT_TEST_ONLY_FIXTURE"
    },
    {
      "id": "acl_mismatch",
      "decision": "INCONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "reconstructed_outcome": null,
      "source": "UNCHANGED_DRAFT_TEST_ONLY_FIXTURE"
    },
    {
      "id": "forged_classification",
      "decision": "INCONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "reconstructed_outcome": null,
      "source": "UNCHANGED_DRAFT_TEST_ONLY_FIXTURE"
    },
    {
      "id": "omitted_edge",
      "decision": "INCONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "reconstructed_outcome": null,
      "source": "UNCHANGED_DRAFT_TEST_ONLY_FIXTURE"
    },
    {
      "id": "forged_report",
      "decision": "INCONSISTENT",
      "numerical_use": "NOT_ADMITTED",
      "reconstructed_outcome": null,
      "source": "UNCHANGED_DRAFT_TEST_ONLY_FIXTURE"
    }
  ],
  "failures": [],
  "server_version_num": "180004",
  "system_identifier": "7708768004042822560",
  "totals": {
    "native_cases": 9,
    "independent_cases": 7,
    "failures": 0,
    "skips": 0
  },
  "finished_at": "2026-11-16T13:57:06.872211+00:00"
}
```

## Unchanged draft provenance for offline checks

The implementation HEAD remains120d28f62b66720e8631b64e0b2a50cdc57e6c42 plus uncommitted work.
These file SHA-256 values identify the exact local inputs; no independently reviewed implementation
commit is implied. The draft source has not been published by this docs-only PR, so its offline
checker observations are author-execution evidence until separate implementation review.

```json
{
  "apps/backend/app/modules/validation/identity_source.py": "c0a2dc510feb347c40d11b365ff2ac5c60c5a74441d8d123a5bde44d6954b4c2",
  "apps/backend/app/modules/identity/source_replay.py": "8baa44d5a3b4c1148158a9374ebc08fc9399108da7523d43976104cfad6484b4",
  "apps/backend/tests/identity_source_fixtures.py": "1be2e19c222dc7de33d62dae2c914236978807dd96bd0cdb3719fdc13e3a9c0c",
  "apps/backend/tests/test_postgres_identity_source.py": "2d36ab1b33083510fdbae18f9effebfbe6f6157b6a167565df9cbaf3e3b911d3",
  "apps/backend/migrations/versions/0018_identity_principal_user_sources.py": "77f1b16e34688939984e5a567406e20767e725547aff55b619513989ca5497c9"
}
```

## Full new diagnostic harness (documentation, not a repository test/tool)

The native part is self-contained with Python/psycopg, PostgreSQL18.4 and OpenSSL already installed.
Set the scratch root/toolchain paths for a disposable local environment. Never target a shared or
production cluster. The final optional checker section requires the exact unchanged local draft
identified above; its absolute source paths are documentation of the author-run environment.
The script lives only in ignored diagnostic scratch; it is not registered as CI/runtime code.

```python
"""Diagnostic only: no Identity migration/function installation or implementation edits."""
import copy,hashlib,json,os,secrets,socket,subprocess,sys,time
from datetime import datetime,UTC
from pathlib import Path
root=Path.cwd(); scratch=root/'.local/catalog-cut-diagnostics'
scratch.mkdir(exist_ok=False)
pg=Path(r'C:\Program Files\PostgreSQL\18\bin');openssl=Path(r'C:\Program Files\Git\usr\bin\openssl.exe')
def run(args):
    path=scratch/('process-'+str(len(list(scratch.glob('process-*'))))+'.log')
    with path.open('wb') as out:
        completed=subprocess.run([str(x) for x in args],stdout=out,stderr=subprocess.STDOUT,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
    if completed.returncode:raise RuntimeError(path.read_text(errors='replace')[-2000:])
password=secrets.token_urlsafe(32);actor_password=secrets.token_urlsafe(32)
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
(scratch/'pw').write_text(password)
run([pg/'initdb.exe','-D',scratch/'data','-U','itr_cut_admin','-A','scram-sha-256','--pwfile',scratch/'pw','--encoding=UTF8','--locale=C'])
(scratch/'pw').unlink();(scratch/'openssl.cnf').write_text('[req]\ndistinguished_name=dn\n[dn]\n')
run([openssl,'req','-config',scratch/'openssl.cnf','-x509','-newkey','rsa:2048','-nodes','-days','2','-keyout',scratch/'server.key','-out',scratch/'server.crt','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'])
with (scratch/'data/postgresql.conf').open('a') as out:
    out.write('\n'+ '\n'.join(["listen_addresses='127.0.0.1'",f'port={port}','ssl=on',f"ssl_cert_file='{(scratch/'server.crt').as_posix()}'",f"ssl_key_file='{(scratch/'server.key').as_posix()}'","password_encryption='scram-sha-256'","statement_timeout='5s'","lock_timeout='1s'","shared_buffers='32MB'","max_connections=12"])+'\n')
run([pg/'pg_ctl.exe','-D',scratch/'data','-l',scratch/'server.log','-w','start'])
result=dict(purpose='DOCS_ONLY_NATIVE_MVCC_DIAGNOSTIC_NOT_ITR_ACCEPTANCE',cases=[],independent_cases=[],failures=[])
try:
    import psycopg
    from psycopg import sql
    def connect(db='postgres',actor=False):return psycopg.connect(host='127.0.0.1',port=port,dbname=db,user='itr_cut_actor' if actor else 'itr_cut_admin',password=actor_password if actor else password,sslmode='verify-full',sslrootcert=str(scratch/'server.crt'),autocommit=True,connect_timeout=3)
    with connect() as admin:
        version=admin.execute('SHOW server_version_num').fetchone()[0];assert version=='180004',version
        result['server_version_num']=version
        result['system_identifier']=str(admin.execute('SELECT system_identifier FROM pg_control_system()').fetchone()[0])
        admin.execute(sql.SQL('CREATE ROLE itr_cut_actor LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}').format(sql.Literal(actor_password)))
        admin.execute('CREATE DATABASE itr_cut_a');admin.execute('CREATE DATABASE itr_cut_b')
    def facts(connection):
        return [dict(version=1,kind='PARAMETER',object_oid=row[0],sub_id=0,schema_name=None,object_name=row[1],owner_oid=None,definition_fingerprint=None,acl=row[2]) for row in connection.execute("""SELECT p.oid::bigint,p.parname,CASE WHEN p.paracl IS NULL THEN NULL WHEN cardinality(p.paracl)=0 THEN '[]'::jsonb ELSE (SELECT jsonb_agg(jsonb_build_array(x.grantee::bigint,x.grantor::bigint,x.privilege_type,x.is_grantable) ORDER BY x.grantee,x.grantor,x.privilege_type,x.is_grantable) FROM aclexplode(p.paracl) x) END FROM pg_parameter_acl p ORDER BY p.parname,p.oid""").fetchall()]
    def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def identity(c):return dict(zip(['snapshot_id','database_oid','database_name','backend_pid','observed_at'],c.execute("SELECT pg_current_snapshot()::text,(SELECT oid::bigint FROM pg_database WHERE datname=current_database()),current_database(),pg_backend_pid(),clock_timestamp()::text").fetchone()))
    def extra(facts,name,actor_oid):return any(f['object_name']==name and any(a[0] in (0,actor_oid) and a[2] in ('SET','ALTER SYSTEM') for a in f['acl'] or []) for f in facts)
    def fresh_guard(c,name):
        try:
            with c.transaction():
                c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                c.execute(sql.SQL("DO $d$ BEGIN IF has_parameter_privilege(session_user,{},'ALTER SYSTEM') THEN RAISE EXCEPTION 'TEST_ONLY native extra-ACL guard rejection' USING ERRCODE='42501'; END IF; END $d$").format(sql.Literal(name)))
            return '00000'
        except psycopg.Error as e:return e.sqlstate
    for isolation in ('REPEATABLE READ','SERIALIZABLE'):
      for writer_db in ('itr_cut_a','itr_cut_b'):
       for mutation in ('GRANT','REVOKE'):
        case_id=f"{isolation.replace(' ','_')}_{writer_db}_{mutation}"
        name='menuto_itr.diag_'+secrets.token_hex(6)
        with connect('itr_cut_a') as admin,connect(writer_db) as writer,connect('itr_cut_a',True) as reader:
          oid=admin.execute("SELECT oid::bigint FROM pg_roles WHERE rolname='itr_cut_actor'").fetchone()[0]
          def change(action):writer.execute(sql.SQL(action+' ALTER SYSTEM ON PARAMETER {} '+('TO' if action=='GRANT' else 'FROM')+' itr_cut_actor').format(sql.Identifier(name)))
          try:
            if mutation=='REVOKE':change('GRANT')
            with reader.transaction():
              reader.execute('SET TRANSACTION ISOLATION LEVEL '+isolation+' READ ONLY')
              first=identity(reader);before=facts(reader)
              with writer.transaction():
                writer_xid=str(writer.execute('SELECT pg_current_xact_id()::text').fetchone()[0])
                change(mutation)
              committed_at=writer.execute('SELECT clock_timestamp()::text').fetchone()[0]
              actual=writer.execute("SELECT has_parameter_privilege('itr_cut_actor',%s,'ALTER SYSTEM')",(name,)).fetchone()[0]
              after=facts(reader);last=identity(reader)
              assert first['snapshot_id']==last['snapshot_id'] and before==after
              assert extra(before,name,oid)==(mutation=='REVOKE') and actual==(mutation=='GRANT')
            with connect('itr_cut_a',True) as fresh:
              with fresh.transaction():
                fresh.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                fresh_id=identity(fresh);fresh_facts=facts(fresh)
              state=fresh_guard(fresh,name)
            assert extra(fresh_facts,name,oid)==(mutation=='GRANT')
            assert state==('42501' if mutation=='GRANT' else '00000')
            result['cases'].append(dict(id=case_id,reader_start=first,reader_end=last,writer_database=writer_db,writer_xid=writer_xid,commit_confirmed_at=committed_at,complete_catalog_before=before,complete_catalog_after=after,before_hash=digest(before),after_hash=digest(after),native_current_extra_acl=actual,retained_extra_acl=extra(before,name,oid),fresh_cut=fresh_id,fresh_complete_catalog=fresh_facts,fresh_guard_sqlstate=state,retained_meaning='HISTORICAL_UNSAFE_NO_IDENTITY_SOURCE' if mutation=='REVOKE' else 'HISTORICAL_NO_EXTRA_ACL_ONLY',transport='UNVERIFIED_TRANSPORT',numerical_use='NOT_ADMITTED',identity_migration_installed=False))
          finally:
            writer.execute(sql.SQL('REVOKE ALL ON PARAMETER {} FROM itr_cut_actor').format(sql.Identifier(name)))
    # Distinct cuts really do expose a mismatch; the predicate is NOT an entry-point implementation.
    with connect('itr_cut_a') as writer,connect('itr_cut_a',True) as reader:
      before=facts(reader);name='menuto_itr.observed_'+secrets.token_hex(6)
      writer.execute(sql.SQL('GRANT ALTER SYSTEM ON PARAMETER {} TO itr_cut_actor').format(sql.Identifier(name)))
      try:
        after=facts(reader);assert before!=after
        try:
          reader.execute(sql.SQL("DO $d$ BEGIN IF {} IS DISTINCT FROM {} THEN RAISE EXCEPTION 'TEST_ONLY observed mismatch' USING ERRCODE='40001'; END IF; END $d$").format(sql.Literal(json.dumps(before)),sql.Literal(json.dumps(after))))
        except psycopg.Error as error:state=error.sqlstate
        else:state='00000'
        assert state=='40001'
        result['cases'].append(dict(id='OBSERVED_DISTINCT_CUT_ACL_MISMATCH',before=before,after=after,sqlstate=state,payload=None,scope='NATIVE_DIAGNOSTIC_PREDICATE_NOT_IDENTITY_PROTECTED_ENTRY'))
      finally:writer.execute(sql.SQL('REVOKE ALL ON PARAMETER {} FROM itr_cut_actor').format(sql.Identifier(name)))
    # Read the unchanged draft checker/fixtures; no new modules, test edits or source installation.
    impl=Path(r'C:\Users\TheDusk4203\.codex\worktrees\identity-source-implementation\Menuto')
    sys.path[:0]=[str(impl/'apps/backend'),str(impl/'apps/backend/tests')]
    from identity_source_fixtures import available_source,rehash
    from app.modules.validation.identity_source import check_identity_source_v1
    control=available_source();check=check_identity_source_v1(control,control['binding'])
    assert check.decision=='CONSISTENT' and check.numerical_use=='NOT_ADMITTED' and check.transport=='UNVERIFIED_TRANSPORT'
    result['independent_cases'].append(dict(id='UNCHANGED_DRAFT_OFFLINE_CONTROL',decision=check.decision,numerical_use=check.numerical_use,transport=check.transport,source='EXPLICIT_TEST_ONLY_SYNTHETIC_FIXTURE_NOT_CANONICAL_DATABASE'))
    for mutation in ('omitted_routine','substituted_oid','acl_mismatch','forged_classification','omitted_edge','forged_report'):
        value=available_source();session=value['frame']['session_end']
        if mutation=='omitted_routine':session['objects']= [x for x in session['objects'] if not (x['kind']=='FUNCTION' and x['object_name']=='menuto_plan_canonical')]
        elif mutation=='substituted_oid':next(x for x in session['objects'] if x['kind']=='FUNCTION')['object_oid']+=100000
        elif mutation=='acl_mismatch':next(x for x in session['objects'] if x['kind']=='FUNCTION')['acl'].append([0,session['database_owner_oid'],'EXECUTE',True])
        elif mutation=='forged_classification':next(x for x in session['objects'] if x['kind']=='FUNCTION')['classification']='EXACT_BASELINE_SAFE_INVOKER'
        elif mutation=='omitted_edge':session['edges']=[]
        if mutation=='forged_report':value=check.model_dump(mode='json')
        else:rehash(value)
        observed=check_identity_source_v1(value,control['binding'])
        assert observed.decision=='INCONSISTENT' and observed.reconstructed_outcome is None and observed.numerical_use=='NOT_ADMITTED',(mutation,observed)
        result['independent_cases'].append(dict(id=mutation,decision=observed.decision,numerical_use=observed.numerical_use,reconstructed_outcome=observed.reconstructed_outcome,source='UNCHANGED_DRAFT_TEST_ONLY_FIXTURE'))
    result['totals']=dict(native_cases=len(result['cases']),independent_cases=len(result['independent_cases']),failures=0,skips=0)
except BaseException as error:
    result['failures'].append(dict(type=type(error).__name__,message=str(error)))
    raise
finally:
    result['finished_at']=datetime.now(UTC).isoformat()
    (scratch/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    run([pg/'pg_ctl.exe','-D',scratch/'data','-m','fast','-w','stop'])
    print(json.dumps(dict(totals=result.get('totals'),failures=result['failures'],cluster_stopped=True)),flush=True)

```

## Complete original protected-entry reproduction and historical result

This is the original diagnostic source unchanged, including its **failing** assertion for the
stronger universal-mutation expectation. Publishing it does not apply the corrected expectation
or change the two failing inherited-edge tests. Its fixture imports refer to the unpublished
paused implementation. It was executed before this correction, not newly executed here.

```python
import json,time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest,psycopg
from psycopg import sql
from identity_postgres_fixtures import identity_scenario,identity_server
from app.modules.validation.identity_source import check_identity_source_v1

def test_native_catalog_cut(identity_scenario):
    s=identity_scenario
    # Compile/capture normally first, then block precisely after the initial catalog capture.
    before=s.capture();name="menuto_itr.cut_"+uuid4().hex
    with s.connect() as locker,s.connect() as admin,s.connect("requester") as reader:
        pid=reader.info.backend_pid
        def capture():
            try:
                with reader.transaction():
                    reader.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                    return reader.execute("SELECT menuto_identity_source.capture_request_source(%s)",(json.dumps(s.raw),)).fetchone()[0]
            except psycopg.Error as error:return dict(sqlstate=error.sqlstate,message=str(error))
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                with locker.transaction():
                    locker.execute("LOCK public.memberships IN ACCESS EXCLUSIVE MODE")
                    future=pool.submit(capture)
                    limit=time.monotonic()+3
                    while time.monotonic()<limit:
                        if admin.execute("SELECT EXISTS(SELECT FROM pg_locks WHERE pid=%s AND relation='public.memberships'::regclass AND NOT granted)",(pid,)).fetchone()[0]:break
                        time.sleep(.01)
                    else:raise AssertionError("Could not place the two capture boundaries around the mutation")
                    admin.execute(sql.SQL("GRANT ALTER SYSTEM ON PARAMETER {} TO {}").format(sql.Identifier(name),sql.Identifier(s.roles["requester"])))
                    assert admin.execute("SELECT has_parameter_privilege(%s,%s,'ALTER SYSTEM')",(s.roles["requester"],name)).fetchone()[0]
                result=future.result(timeout=5)
            evidence={"mutation":"committed GRANT ALTER SYSTEM between catalog boundaries","result":result.get("outcome"),"reason":result.get("reason"),"sqlstate":result.get("sqlstate")}
            if "frame" in result:
                evidence["start_contains_parameter"]=any(o["kind"]=="PARAMETER" and o["object_name"]==name for o in result["frame"]["session_start"]["objects"])
                evidence["end_contains_parameter"]=any(o["kind"]=="PARAMETER" and o["object_name"]==name for o in result["frame"]["session_end"]["objects"])
                evidence["independent_decision"]=check_identity_source_v1(result,s.raw).decision
            try:s.capture();evidence["next_fresh_capture"]="unexpected success"
            except psycopg.Error as error:evidence["next_fresh_capture"]=error.sqlstate
            print("CUT_EVIDENCE "+json.dumps(evidence),flush=True)
            assert result.get("outcome")!="AVAILABLE_AT_RETAINED_CUT", evidence
        finally:
            admin.execute(sql.SQL("REVOKE ALL ON PARAMETER {} FROM {}").format(sql.Identifier(name),sql.Identifier(s.roles["requester"])))

```

Historical artifact/measurement inventory (the86-test suite had84pass/2fail/0skip; the separate
cut probe had1failure). Counts are never summed into a full-suite pass:

```json
{
  "baseline": "120d28f62b66720e8631b64e0b2a50cdc57e6c42",
  "status": "BLOCKED / CATALOG CUT FRESHNESS REQUIREMENT NOT SATISFIED",
  "native_postgresql": "18.4",
  "probe": {
    "mutation": "committed GRANT ALTER SYSTEM between catalog boundaries",
    "result": "AVAILABLE_AT_RETAINED_CUT",
    "reason": "SOURCE_AVAILABLE",
    "sqlstate": null,
    "start_contains_parameter": false,
    "end_contains_parameter": false,
    "independent_decision": "CONSISTENT",
    "next_fresh_capture": "42501"
  },
  "expanded_pg": {
    "name": "pytest",
    "errors": "0",
    "failures": "2",
    "skipped": "0",
    "tests": "86",
    "time": "425.224",
    "timestamp": "2026-11-16T20:29:05.396343+07:00",
    "hostname": "TheDusk"
  },
  "artifacts": {
    ".local/identity_cut_probe.py": "5ecdf983f871a86ef6fc4fe67eed4b40c32dc0098ae39620cc0de8e9b39b3d1f",
    ".local/identity-cut-probe-1.py": "719bd00fd484fe31dc1b1fa03fcdc0735d093d5a21cb8020c201ad9235161775",
    ".local/identity-cut-probe-1/pytest.log": "c5c518af09e06176542ffd3a72100697a73b5aebd4fcfef70b193a0a8c6d7327",
    ".local/identity-cut-probe-1/results.xml": "c2a7e0da801c0cdf5c864c5bd735420ea9ef8e4f50ea842ae7b33f41ae9749ea",
    ".local/identity-itr-all-2/results.xml": "c1fabc1e898c9455b9d0dddef460dab8a3f711e6f03418cccff6c7b2d30c0029",
    ".local/identity-catalog-cut-compatibility.json": "d78a1c36ae73a04747e083c65456f1947a037fc772b7daefdee71bb9b62511bb"
  }
}
```

## Exact design/acceptance diff

The following zero-context unified diff is generated against the exact baseline for the five narrowly corrected
design/contract/acceptance/preflight Markdown files. No runtime/schema/test/guard patch is included.

```diff
diff --git a/docs/product/IDENTITY_IMPLEMENTATION_ACCEPTANCE_PREFLIGHT.md b/docs/product/IDENTITY_IMPLEMENTATION_ACCEPTANCE_PREFLIGHT.md
index 89e8ec2..e6b8142 100644
--- a/docs/product/IDENTITY_IMPLEMENTATION_ACCEPTANCE_PREFLIGHT.md
+++ b/docs/product/IDENTITY_IMPLEMENTATION_ACCEPTANCE_PREFLIGHT.md
@@ -2,0 +3,2 @@
+> Catalog-cut semantics corrigendum proposed under [owner authorization6918157643](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6918157643): [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md). Implementation remains paused; historical stage records and all19 shapes/96 IDs/48 PG groups are retained. New diagnostic observations are not completed ITR acceptance.
+
@@ -41 +43 @@ No obligation may be omitted to fit counts. Scope/authority changes still need a
-| ITR018 | apps/backend/tests/test_postgres_identity_source.py::test_itr018_privilege_graph_closure | p1_default, p2_real_row, p3_set, p3_set_grant_option, p3_alter_system, p3_alter_system_grant_option, p4_public_set, p4_public_alter_system, p4_inherit_true_set, p4_inherit_true_alter_system, p4_inherit_false_set, p4_inherit_false_alter_system, p5_grant_set, p5_grant_alter_system, p5_revoke_set, p5_revoke_alter_system, p5_cross_database_set, p5_cross_database_alter_system, p6_absent, p6_null, p6_empty, p7_custom, p7_other_grantee, p7_overflow | Unsafe direct/inherited CREATEROLE/CREATEDB/BYPASSRLS/replication/ownership/owner-SET reachability denied, not hidden by benign immediate role. Extend within this same PG obligation with contract section2.1 catalog cases: actual ownerless parameter rows/default absence, direct/PUBLIC/INHERIT TRUE SET and ALTER SYSTEM grants plus grant options, INHERIT FALSE control, grant/revoke mutation and explicit-login has_parameter_privilege parity; compare producer capture and independent reconstruction, including benign no-extra-rights positive capture. No synthetic parameter owner/OID or inferred zero total SET authority. |
+| ITR018 | apps/backend/tests/test_postgres_identity_source.py::test_itr018_privilege_graph_closure | p1_default, p2_real_row, p3_set, p3_set_grant_option, p3_alter_system, p3_alter_system_grant_option, p4_public_set, p4_public_alter_system, p4_inherit_true_set, p4_inherit_true_alter_system, p4_inherit_false_set, p4_inherit_false_alter_system, p5_grant_set, p5_grant_alter_system, p5_revoke_set, p5_revoke_alter_system, p5_cross_database_set, p5_cross_database_alter_system, p6_absent, p6_null, p6_empty, p7_custom, p7_other_grantee, p7_overflow | Unsafe direct/inherited CREATEROLE/CREATEDB/BYPASSRLS/replication/ownership/owner-SET reachability denied, not hidden by a benign immediate role. Preserve ownerless parameter rows/default absence, direct/PUBLIC/inherited SET and ALTER SYSTEM/grant-option cases and INHERIT FALSE control. Compare explicit-login has_parameter_privilege at a matching observation/cut; a later live oracle must not be mislabeled as pre-cut truth. P5 separately tests commits before a fresh cut, invisible mid-cut GRANT/REVOKE, actual observed mismatch and cross-database mutation. No invented owner/OID or inferred zero total SET authority. |
@@ -63,2 +65,2 @@ No obligation may be omitted to fit counts. Scope/authority changes still need a
-| ITR040 | apps/backend/tests/test_postgres_identity_source.py::test_itr040_coherent_cut | unchanged, mutation_before_cut, mutation_after_cut | Concurrent membership/source mutation during RR capture produces one faithful cut or whole-cut failure; no mixed favorable rows. Include concurrent parameter GRANT/REVOKE and unchanged-catalog control: retain complete cluster-wide enumeration at both boundaries, reject an observed ACL/OID/role-closure change and require fresh post-commit capture to reflect changed privileges; an earlier retained cut never authorizes new work. |
-| ITR041 | apps/backend/tests/test_postgres_identity_source.py::test_itr041_fresh_versus_retained_revoke | single | Revoke committed before first fresh snapshot denies it; earlier RR cut replays only historical authority and cannot be submitted for new live inspection/admission. |
+| ITR040 | apps/backend/tests/test_postgres_identity_source.py::test_itr040_coherent_cut | unchanged, mutation_before_cut, mutation_after_cut | One actual read-only RR/SERIALIZABLE cut retains complete coherent source evidence or fails whole-cut. Separate unchanged control; unsafe GRANT committed before the fresh initial cut rejects42501; invisible GRANT/REVOKE committed after cut may leave equal historical observations, never current authority. Actually observed ACL/OID/role/catalog disagreement fails SOURCE_CUT_INCOHERENT with no partial source. Include cross-database parameter writes and exact transaction/commit/snapshot ordering. Equal reads/hashes are not a universal mutation detector. |
+| ITR041 | apps/backend/tests/test_postgres_identity_source.py::test_itr041_fresh_versus_retained_revoke | single | Identity revoke committed before a genuinely new initial snapshot denies fresh authority use; an unsafe extra SQL privilege visible then rejects42501. An earlier RR/SERIALIZABLE cut may retain earlier evidence and replay CONSISTENT only historically. Later removal of unsafe SQL rights does not repair that earlier unsafe observation. No cached source/report, rewritten timestamp or digest can replace a new authenticated transaction/capture/check; no consumer admission. |
@@ -83 +85 @@ No obligation may be omitted to fit counts. Scope/authority changes still need a
-| ITR055 | apps/backend/tests/test_identity_source.py::test_itr055_role_graph_reconstruction | fabricated_owner, removed_grant, omitted_inherited_edge, public_grant_option, alter_system_bit, forged_absence, unsupported_catalog, benign_default_control | Forged omitted privilege edge/default ACL/owner privilege detected from retained complete primitives; unsupported catalog shape fails closed. Independently replay ownerless parameter NULL/default/explicit cases and PUBLIC/inherited SET/ALTER SYSTEM plus grant options against ITR018 actual-catalog vectors. Fully rehashed fabricated owner, removed grant, forged absent row relative to retained boundary facts or omitted inherited edge cannot yield a safe positive; preserve fully coherent replacement/non-origin limitation. |
+| ITR055 | apps/backend/tests/test_identity_source.py::test_itr055_role_graph_reconstruction | fabricated_owner, removed_grant, omitted_inherited_edge, public_grant_option, alter_system_bit, forged_absence, unsupported_catalog, benign_default_control | Reconstruct role closure/default/explicit ACLs independently from complete retained primitives and pinned identities; unsupported shape fails closed. Omissions, substituted OIDs/owners, forged favorable classifications or hashes that contradict retained boundary/authority evidence must be INCONSISTENT/NOT_ADMITTED. Include complete inherited-edge facts in adversaries; do not call an unrelated other-grantee ACL an effective actor grant without its edge. Fully coherent replacement/omission with no retained contradiction remains subject to ITR061 UNVERIFIED_TRANSPORT; it cannot be authenticated offline or authorize new work. |
@@ -94 +96 @@ No obligation may be omitted to fit counts. Scope/authority changes still need a
-| ITR066 | apps/backend/tests/test_identity_source.py::test_itr066_catalog_changes | single | Start/end login/database/privilege descriptor differences fail incoherent cut; no partial success or retained catalog-origin overclaim. Include parameter-row creation/deletion, ACL mutation, NULL/empty changes and inherited permission changes, even when only another database in the cluster issued the parameter GRANT/REVOKE. |
+| ITR066 | apps/backend/tests/test_identity_source.py::test_itr066_catalog_changes | single | Actually observed start/end DB/login/OID/ACL/role descriptor differences fail whole capture, including observed parameter creation/deletion/NULL/empty/ACL or inherited-edge changes from either database in the cluster. Contrast an invisible post-cut commit: matching complete historical observations may remain CONSISTENT/NOT_ADMITTED, not current-at-return proof. Tampered/omitted/substituted retained primitives inconsistent with the remaining cut must fail; no favorable prefix, cached authority or partial source. Preserve fully coherent forgery/non-origin limit. |
@@ -135 +137 @@ P3 direct SET/ALTER SYSTEM/grant options and P4 PUBLIC/inherited edges compare e
-P5 observes real GRANT/REVOKE/inherited-edge/cross-database mutation. ITR040 stable/change-boundary cuts andITR042 full all-grantee/custom enumeration cross-check it. Old RR consistency cannot authorize fresh work.
+P5 separates real GRANT/REVOKE/inherited-edge writes committed before a fresh cut from writes invisible to an established RR/SERIALIZABLE cut, including writes in a second database of the same cluster. ITR040 retains its three parameter IDs: unchanged control; mutation_before_cut must reflect fresh effective rights; mutation_after_cut must test both invisible historical consistency and actually observed mismatch as distinct assertions. ITR042 still requires complete all-grantee/custom enumeration at that cut. Equal reads/hashes do not prove no concurrent mutation. Old consistency/report possession never authorizes fresh work.
diff --git a/docs/product/IDENTITY_IMPLEMENTATION_DATABASE_SECURITY_PREFLIGHT.md b/docs/product/IDENTITY_IMPLEMENTATION_DATABASE_SECURITY_PREFLIGHT.md
index 2679dc5..47b6b9c 100644
--- a/docs/product/IDENTITY_IMPLEMENTATION_DATABASE_SECURITY_PREFLIGHT.md
+++ b/docs/product/IDENTITY_IMPLEMENTATION_DATABASE_SECURITY_PREFLIGHT.md
@@ -172 +172,7 @@ hashes. Bounded full capture or error; fully coherent offline forgery remains un
-ITR018 P1–P7/ITR055 are future actual-catalog and mutation proofs, not current executed tests.
+ITR018 P1–P7/ITR055 remain implementation obligations, not completed by this correction.
+Catalog enumeration is complete as of one initial read-only RR/SERIALIZABLE cut. Actually observed
+start/end safety mismatch fails whole capture; equal MVCC reads do not prove absence of a concurrent
+GRANT/REVOKE, including a write from another database in the cluster. Current-at-return attestation,
+extra observation sessions, catalog locks and an epoch/writer-coordination authority are separate
+unapproved alternatives; this clarification installs none. Retained evidence remains non-admitting.
+See the [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md).
diff --git a/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_ACCEPTANCE.md b/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_ACCEPTANCE.md
index e150611..fccd4b3 100644
--- a/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_ACCEPTANCE.md
+++ b/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_ACCEPTANCE.md
@@ -2,0 +3,2 @@
+> Catalog-cut semantics corrigendum proposed under [owner authorization6918157643](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6918157643): [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md). Implementation remains paused; historical stage records and all19 shapes/96 IDs/48 PG groups are retained. New diagnostic observations are not completed ITR acceptance.
+
@@ -42 +44 @@ Fault injection belongs to controlled disposable test setup, never ordinary runt
-| ITR018 | Privilege graph closure | Unsafe direct/inherited CREATEROLE/CREATEDB/BYPASSRLS/replication/ownership/owner-SET reachability denied, not hidden by benign immediate role. Extend within this same PG obligation with contract section2.1 catalog cases: actual ownerless parameter rows/default absence, direct/PUBLIC/INHERIT TRUE SET and ALTER SYSTEM grants plus grant options, INHERIT FALSE control, grant/revoke mutation and explicit-login has_parameter_privilege parity; compare producer capture and independent reconstruction, including benign no-extra-rights positive capture. No synthetic parameter owner/OID or inferred zero total SET authority. |
+| ITR018 | Privilege graph closure | Unsafe direct/inherited CREATEROLE/CREATEDB/BYPASSRLS/replication/ownership/owner-SET reachability denied, not hidden by a benign immediate role. Preserve ownerless parameter rows/default absence, direct/PUBLIC/inherited SET and ALTER SYSTEM/grant-option cases and INHERIT FALSE control. Compare explicit-login has_parameter_privilege at a matching observation/cut; a later live oracle must not be mislabeled as pre-cut truth. P5 separately tests commits before a fresh cut, invisible mid-cut GRANT/REVOKE, actual observed mismatch and cross-database mutation. No invented owner/OID or inferred zero total SET authority. |
@@ -64,2 +66,2 @@ Fault injection belongs to controlled disposable test setup, never ordinary runt
-| ITR040 | Coherent cut | Concurrent membership/source mutation during RR capture produces one faithful cut or whole-cut failure; no mixed favorable rows. Include concurrent parameter GRANT/REVOKE and unchanged-catalog control: retain complete cluster-wide enumeration at both boundaries, reject an observed ACL/OID/role-closure change and require fresh post-commit capture to reflect changed privileges; an earlier retained cut never authorizes new work. |
-| ITR041 | Fresh versus retained revoke | Revoke committed before first fresh snapshot denies it; earlier RR cut replays only historical authority and cannot be submitted for new live inspection/admission. |
+| ITR040 | Coherent cut | One actual read-only RR/SERIALIZABLE cut retains complete coherent source evidence or fails whole-cut. Separate unchanged control; unsafe GRANT committed before the fresh initial cut rejects42501; invisible GRANT/REVOKE committed after cut may leave equal historical observations, never current authority. Actually observed ACL/OID/role/catalog disagreement fails SOURCE_CUT_INCOHERENT with no partial source. Include cross-database parameter writes and exact transaction/commit/snapshot ordering. Equal reads/hashes are not a universal mutation detector. |
+| ITR041 | Fresh versus retained revoke | Identity revoke committed before a genuinely new initial snapshot denies fresh authority use; an unsafe extra SQL privilege visible then rejects42501. An earlier RR/SERIALIZABLE cut may retain earlier evidence and replay CONSISTENT only historically. Later removal of unsafe SQL rights does not repair that earlier unsafe observation. No cached source/report, rewritten timestamp or digest can replace a new authenticated transaction/capture/check; no consumer admission. |
@@ -84 +86 @@ Fault injection belongs to controlled disposable test setup, never ordinary runt
-| ITR055 | Role graph reconstruction | Forged omitted privilege edge/default ACL/owner privilege detected from retained complete primitives; unsupported catalog shape fails closed. Independently replay ownerless parameter NULL/default/explicit cases and PUBLIC/inherited SET/ALTER SYSTEM plus grant options against ITR018 actual-catalog vectors. Fully rehashed fabricated owner, removed grant, forged absent row relative to retained boundary facts or omitted inherited edge cannot yield a safe positive; preserve fully coherent replacement/non-origin limitation. |
+| ITR055 | Role graph reconstruction | Reconstruct role closure/default/explicit ACLs independently from complete retained primitives and pinned identities; unsupported shape fails closed. Omissions, substituted OIDs/owners, forged favorable classifications or hashes that contradict retained boundary/authority evidence must be INCONSISTENT/NOT_ADMITTED. Include complete inherited-edge facts in adversaries; do not call an unrelated other-grantee ACL an effective actor grant without its edge. Fully coherent replacement/omission with no retained contradiction remains subject to ITR061 UNVERIFIED_TRANSPORT; it cannot be authenticated offline or authorize new work. |
@@ -95 +97 @@ Fault injection belongs to controlled disposable test setup, never ordinary runt
-| ITR066 | Catalog changes | Start/end login/database/privilege descriptor differences fail incoherent cut; no partial success or retained catalog-origin overclaim. Include parameter-row creation/deletion, ACL mutation, NULL/empty changes and inherited permission changes, even when only another database in the cluster issued the parameter GRANT/REVOKE. |
+| ITR066 | Catalog changes | Actually observed start/end DB/login/OID/ACL/role descriptor differences fail whole capture, including observed parameter creation/deletion/NULL/empty/ACL or inherited-edge changes from either database in the cluster. Contrast an invisible post-cut commit: matching complete historical observations may remain CONSISTENT/NOT_ADMITTED, not current-at-return proof. Tampered/omitted/substituted retained primitives inconsistent with the remaining cut must fail; no favorable prefix, cached authority or partial source. Preserve fully coherent forgery/non-origin limit. |
@@ -144 +146 @@ Future evidence must report each executed node/parameter and actual expansion co
-| P5 revoke/mutation | Retain complete before/after catalog cuts across GRANT, REVOKE and inherited-edge changes, including mutation from a second database | Fresh capture tracks effective rights; observed within-capture descriptor changes fail whole-cut; faithful old cuts stay historical-only. Rehashed deleted grant/owner forgery rejected against retained primitives. |
+| P5 revoke/mutation | Record initial MVCC cut, before/after observations, mutation transaction/commit order and genuinely fresh post-commit transaction; exercise GRANT/REVOKE/inherited edges and a second database in the same cluster | Unsafe grants visible to the fresh cut reject42501; actually observed mismatch fails whole capture. An invisible mid-cut mutation can leave historical observations equal, never current authority. An earlier unsafe observation cannot become safe merely because of a later REVOKE. Reject contradictory retained forgeries; preserve ITR061 coherent-forgery limit. |
diff --git a/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md b/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md
index 7ca43e7..79ee20b 100644
--- a/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md
+++ b/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md
@@ -2,0 +3,2 @@
+> Catalog-cut semantics corrigendum proposed under [owner authorization6918157643](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6918157643): [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md). Implementation remains paused; historical stage records and all19 shapes/96 IDs/48 PG groups are retained. New diagnostic observations are not completed ITR acceptance.
+
@@ -212,7 +214,31 @@ no PIV purpose/lease is reused or expanded.
-Authority/Membership rows are observed at the retained MVCC cut. A revoke committed before a fresh
-transaction's first snapshot must deny it. A transaction already holding an earlier repeatable cut
-may faithfully see earlier authority; its report never certifies permission after that cut or over
-the planning horizon. New privileged work cannot use that report; it needs fresh source capture.
-Catalog safety is checked at capture start/end; changed DB/login/OID/privilege descriptors fail as
-SOURCE_CUT_INCOHERENT. Superuser/catalog tampering is outside the TCB threat model, not hidden by
-claims that PostgreSQL catalog state and application history provide an eternally current authorization.
+The owner-selected V1 clarification is proposed in the [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md).
+One actual clean read-only RR/SERIALIZABLE transaction retains source and MVCC-visible catalog
+truth as of its initial snapshot. `snapshot_id` identifies that retained cut; `observed_at` and
+`finished_at` do not make it a current-at-return attestation.
+
+Distinguish four cases:
+
+- **Snapshot consistency:** complete source histories, Membership and applicable catalog evidence
+  must reconstruct coherently at the same retained cut; no favorable mixed-cut or partial source.
+- **Observed catalog mismatch:** actually unequal start/end safety descriptors (DB/login/OID/ACL/
+  role closure) fail the whole capture as SOURCE_CUT_INCOHERENT, with no partial source. Native
+  catalog/cache primitives need not all have identical MVCC visibility; any observed disagreement
+  remains a failure, not permission to choose the favorable observation.
+- **Unobserved concurrent mutation:** GRANT/REVOKE committed after the snapshot was established
+  need not appear in either MVCC catalog enumeration. Equal reads or hashes do not prove no
+  intervening mutation. SERIALIZABLE alone does not turn this into wall-clock freshness.
+- **Current authorization:** AVAILABLE_AT_RETAINED_CUT / CONSISTENT describe retained historical
+  evidence only, always TEST_ONLY / UNVERIFIED_TRANSPORT / NOT_ADMITTED. A new trusted operation
+  requires a new actual authenticated transaction and fresh checks. A retained source/report,
+  matching digest or rewritten timestamp cannot authorize it, and no consumer admission is added.
+
+A revoke committed before a new transaction's initial snapshot must deny fresh authority use; an
+unsafe extra parameter grant visible to that new cut must reject the ordinary principal (42501),
+not return a positive source. A previously established cut may faithfully retain earlier authority;
+its result proves neither present permission nor permission over the planning horizon. If a revoke
+removes a previously unsafe SQL privilege, the earlier unsafe observation must still deny capture;
+removing it later does not retroactively make that old cut safe.
+
+Stronger guarantees that every concurrent catalog commit must invalidate a capture require a
+separately approved freshness/fencing mechanism; none is introduced here. Superuser/catalog tampering
+remains outside the TCB threat model, not hidden by claims of eternally current authorization.
diff --git a/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_CONTRACTS.md b/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_CONTRACTS.md
index dcb3aa3..f50d15d 100644
--- a/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_CONTRACTS.md
+++ b/docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_CONTRACTS.md
@@ -2,0 +3,2 @@
+> Catalog-cut semantics corrigendum proposed under [owner authorization6918157643](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6918157643): [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md). Implementation remains paused; historical stage records and all19 shapes/96 IDs/48 PG groups are retained. New diagnostic observations are not completed ITR acceptance.
+
@@ -146,2 +148,5 @@ add a public definition. These conventions fix the exact 19-name export boundary
-    descriptor, not a claim that replay has a live transaction. Start/end safety descriptors must
-    agree; changes fail the whole capture. No password/token or unrelated source rows.
+    descriptor of the initial coherent read-only RR/SERIALIZABLE cut, not a live transaction or
+    current-at-return attestation. Actually observed start/end safety descriptors must agree;
+    mismatch fails the whole capture, with no partial source. Equal observations do not prove no
+    post-snapshot commit: an MVCC-invisible concurrent mutation may be absent from both. No new
+    fields, liveness token or freshness authority is added. No password/token or unrelated rows.
@@ -160 +165,4 @@ add a public definition. These conventions fix the exact 19-name export boundary
-    and revoked rows; issuer_history includes the complete issuer directory. No payload-owned limits.
+    and revoked rows; issuer_history includes the complete issuer directory. Availability is only
+    as of the retained cut: no current privilege, freshness, canonical-origin or consumer-admission
+    claim. Replaying a complete earlier cut after a later commit does not authorize a new operation;
+    new trusted work requires a new authenticated transaction and fresh capture/checks. No payload-owned limits.
@@ -210,2 +218,6 @@ canonical stored names; no Python Unicode case folding or caller-selected alias
-The objects arrays include all these facts, and both boundary enumerations must match. Use the
-existing catalog4096-object, source-byte/node/work/time bounds before accepting/expanding a complete
+The objects arrays include all these facts visible at the retained cut, and both actually observed
+boundary enumerations must match. A matching pair is not proof that the cluster had no concurrent
+mutation; new parameter rows/ACL changes committed after the cut may be invisible in both RR or
+SERIALIZABLE enumerations, including writes from another database. Do not synthesize a missing row
+or drop an observed unfavorable row to force equality. Use the existing catalog4096-object,
+source-byte/node/work/time bounds before accepting/expanding a complete
@@ -236,2 +248,4 @@ ALTER SYSTEM capability, directly, through PUBLIC or inheritance, including gran
-new grant makes fresh capture fail the safe-role gate; revoking it removes that ACL capability but
-does not renew any Identity enrollment. No grants are installed by this design correction.
+new grant committed before a new capture's initial cut makes the ordinary safe-role gate fail
+(42501). Revoking it removes that extra ACL capability in subsequent cuts, but does not renew any
+Identity enrollment or retroactively change an earlier unsafe observation. A mid-capture mutation
+invisible to the retained cut need not be detected. No grants are installed by this design correction.
@@ -253,0 +268,4 @@ replacement of a complete catalog and all hashes retains the existing UNVERIFIED
+An omitted/substituted fact or forged favorable classification that contradicts other retained
+primitives, pinned routine identity, role closure or boundary completeness must be rejected. A fully
+coherent replacement with no retained contradiction cannot be proved authentic by this offline
+checker; CONSISTENT never supplies origin, present authorization or numerical use. See the [catalog-cut correction and diagnostic evidence](IDENTITY_CATALOG_CUT_SEMANTICS_CORRECTION.md).
```
