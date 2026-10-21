# ADR-006 — Retail Evidence and Procurement Abstraction

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
Direct optimization over exact retailer SKU encourages brittle plans around flash sales, stale availability and odd pack sizes. Yet over-abstracting retail loses the evidence needed for realistic shopping.

## Decision
Use four logical layers:

`Ingredient → RetailProduct → RetailOffer/PriceObservation → ProcurementClass`.

Global Planner normally optimizes `ProcurementClass`, not isolated brand SKU. Granularity types:

- `FIXED_PACK`;
- `CATCH_WEIGHT` with expected/low/high quantity;
- `LOOSE_SCALE` with minimum/step rules.

Raw observations are converted into versioned `PlanningPriceQuote` and `PlanningAvailability` using source quality, freshness, coverage, dispersion, promo state and mapping confidence.

Reference fallback is explicit and calibrated hierarchically by retailer × region × category where supported; weak category estimates shrink toward broader indices.

Shopping output resolves a `ShoppingRequirement` to primary + backup offers. Exact SKU becomes fixed input only when bought/reserved/locked.

## Consequences
- Flash-sale outliers do not define budget feasibility by default.
- Procurement fragility/substitution coverage become planner quality signals.
- Baseline/reference prices are never presented as retailer availability truth.
- Actual receipt data can later calibrate price/risk models.

## Invariants
INV-008, INV-009, INV-010, INV-011.
