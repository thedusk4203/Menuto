# M1.3 Inventory Physical Ledger — architecture review

Review baseline: frozen M1.1/M1.2, commit `05382b6425a072433e38db99a1de101b577804a0`, 0001–0006, 33 tables. Read ADR-005/006/009/010, INV-011–021/030, spec §13 and §18, Retail mapping and Recipe snapshot contracts. No contradiction requires changing frozen architecture.

## A. Physical truth vs projection
Only explicit confirmed evidence creates physical facts. No planned/assumed/projected flag or physical lifecycle. System inference, retail observation and planning quotes cannot serve as acquisition evidence. No projection builder or full POSTFACT validator is implemented.

## B. Lot identity and lifecycle
One tagged household-owned lot identity: RAW_INGREDIENT (Ingredient + AP_G/EP_RAW_G/COUNT), PREPARED_COMPONENT (Ingredient + COOKED_G), COOKED_DISH (SERVING + explicit serving definition/item_ref, no fake ingredient). These are distinct immutable assets. The unified table shares accounting, not conversion semantics. ACTIVE/DEPLETED/DISCARDED are recorded material states; EXPIRED can be an explicit event, and effective expiry is also derived at snapshot time from resolved usable_until. Passing time never writes history. No mutable status on immutable identity.

## C. Movement ledger
Append-only ACQUIRE, CONSUME, DISCARD, RECONCILE_INCREASE/DECREASE and EXPIRE. Positive amount + explicit movement direction; EXPIRE carries zero amount and retains remaining physical matter. Corrections append movements, optionally referencing exact prior same-lot movement, with required reason/actor/source. No delete/rewrite. Five tables: inventory_lots, inventory_lot_balances (guarded cache), inventory_movements, inventory_reservations, inventory_reservation_releases. Orphan lots cannot commit without exact opening acquisition. All updates/deletes/truncates of historical tables fail.

## D. Measurement
StoredQuantity semantics, unconstrained NUMERIC plus exact scale/range checks to prevent SQL typmod rounding. No float or implicit conversion. All events must match lot basis and contextual item_ref. AP retail origin retains the immutable mapping FK and complete mapping in read snapshot, including Product/Ingredient/version/yield/provenance; Inventory does not own edible yield. No generic conversion persistence. Calculated quantities require prior explicit QuantizationPolicy at caller seam.

## E. Raw vs prepared ownership
Physical assets belong to Household. Recipe does not own inventory; no required Plan/Recipe/Retailer FK on lot. Ingredient is canonical FK for ingredient assets. Optional reviewed Retail mapping provenance binds exact ingredient; no raw offer or quote creates stock. Prepared manual confirmation is supported for existing food, not fictitious batch production.

## F. Reservations
Separate immutable allocation intents plus immutable release facts. V1 reservations are active until explicit release (no scheduled windows, partial fulfillment or Plan integration). They do not change physical quantity. New reservations require usable stock; sum of unreleased intents cannot exceed physical remaining. If time later expires stock, historical intent stays visible but allocatable becomes zero; future projection builders must resolve stale intents. Consuming/reconciling/discarding reserved material requires explicit release first, in the same caller transaction if atomicity is needed. No automatic consumption or silent reservation cancellation.

## G. Expiry and usability
Resolved usable_until is immutable, finite, later than acquisition if provided. Confirmed consumption/reservation cannot use expired material. Reconciliation/discard can still record actual counts/waste. EXPIRE may explicitly mark the remaining material unusable; it does not fabricate disappearance. Confidence CONFIRMED/STALE/UNKNOWN is separate from lifecycle; each physical record still needs explicit confirmation. No shelf-life inference.

## H. Purchase boundary
AcquireInventoryCommand requires explicit confirmation by a Household membership actor and USER/RECEIPT/BARCODE/EXECUTION source identity. Provenance source is distinct from observation confidence. Retail origin is optional evidence, not purchase confirmation. Service supplies idempotency via household × source_system × key within each event family (movement, reservation, release), verifies exact command fingerprint on retry, and preserves external source identity. No receipt/barcode workflow or PurchaseFulfillment domain.

## I. Future CookingBatch
Draft boundary describes exact input/output asset quantities and evidence references, not an implemented execution service. Future batch must consume inputs and create separate prepared outputs atomically; retain RecipeVersion/resolved composition and retail mapping evidence in orchestration. M1.3 does not claim yield conservation validation or allow an unconfirmed inferred batch to create stock. PreparedFood V1 dish tracking uses servings per ADR-009/spec §13.11; net cooking yield stays Recipe-owned.

## J. Chronological replay / validation handoff
Each fact has occurred_at, server recorded_at and DB-assigned ledger_sequence; UUID ordering is never used. Canonical same-time phases: acquisition 10 (prepared acquisition 40), reconciliation/reservation 20, raw consumption 30, prepared production 40, meal consumption 50, expiry/discard 60; sequence breaks equal-phase ties. Commands append in nondecreasing effective order per lot; backdated insertion before recorded material history and future physical claims are rejected in this foundation. Correction is a new event. Full diagnostic late-evidence ingestion remains deferred (INV-021 does not mean silently accepting an impossible ledger).

All inventory DB writes first take a household advisory transaction fence (read snapshots take its shared form), serializing household writes in V1 and preventing mixed-statement reads. A protected balance row is locked and updated on every physical/reservation event. At READ COMMITTED competing writers see committed balances; at REPEATABLE READ stale writers fail serialization and must retry. This is stronger than locking an immutable lot without writing it. Movement + balance update are atomic. Snapshot reads use one repeatable snapshot and carry all lot, movement, reservation/release primitive facts, derived balances and source evidence; no cached valid=true. Future independent validator recomputes chronological stock and batch links; not implemented here.

## Scope / trade-offs
No redesign of seals or frozen contracts/migrations. Strict append chronology, full explicit reservation release, no storage transfers/cost valuation/confidence-history editing in V1. Draft transformation integration is not CookingBatch execution. Populated downgrade to 0006 fails closed; lossless populated roundtrip means existing Foundation rows with no ledger history. M1.3 was user APPROVED/FROZEN on 2026-10-23 at `fef629965dd7401e27c98b5a0c523998a27017c4` (head0007, 38 tables). No M1.4 work.
