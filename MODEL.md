# Data model

## Design goal

Represent **multi-tenant emissions activity** from heterogeneous client sources, normalized enough for analyst review and audit lock, without pretending we already run a full carbon engine.

## Core entities

### `Organization`
Tenant boundary. Every query and record is scoped to one organization via `OrganizationMembership`.

### `OrganizationMembership`
Links Django `User` to `Organization` with role (`analyst`, `admin`). This is the multi-tenancy gate used by API views.

### `DataSource`
Configured connector per tenant and source type:
- `sap` — fuel & procurement flat export
- `utility` — electricity portal CSV
- `travel` — corporate travel export

Stores display metadata and optional JSON `config` (e.g. delimiter hints, plant lookup table IDs in a real deployment).

### `IngestionBatch`
One uploaded file (or future API pull) per ingest attempt.
Tracks filename, uploader, counts (`row_count`, `success_count`, `error_count`, `warning_count`), and batch-level failure reason.

This separates **file-level outcomes** from **row-level outcomes**.

### `ActivityRecord`
Canonical normalized row used by analysts.

| Concern | Fields |
|--------|--------|
| Multi-tenancy | `organization` |
| GHG scope | `scope` (`scope_1`, `scope_2`, `scope_3`) |
| Activity type | `category` (fuel, procurement, electricity, flight, hotel, ground) |
| Source of truth | `source`, `batch`, `source_reference`, `source_row_hash`, `raw_payload` |
| Time | `activity_date`, optional `period_start` / `period_end` (utility billing windows) |
| Location / counterparty | `facility_code`, `vendor_or_carrier` |
| Quantities | `quantity`, `unit`, `normalized_quantity`, `normalized_unit` |
| Spend (where relevant) | `spend_amount`, `spend_currency` |
| Travel specifics | `origin`, `destination`, `distance_km` |
| Quality | `parse_ok`, `validation_flags`, `validation_message` |
| Review / audit | `review_status`, `reviewed_by`, `reviewed_at`, `is_locked_for_audit` |

**Scope mapping in this prototype**
- SAP diesel/heating fuels → Scope 1 (`fuel`)
- SAP non-fuel materials → Scope 3 (`procurement`)
- Utility electricity → Scope 2 (`electricity`)
- Travel (air/hotel/ground) → Scope 3

### `AuditEvent`
Append-only trail for ingest and review actions with `before_state` / `after_state` JSON snapshots.

## Source-of-truth rules

1. `raw_payload` is never overwritten after ingest.
2. Analyst approval does not mutate quantities; it changes `review_status` and sets `is_locked_for_audit`.
3. Every approve/reject writes an `AuditEvent` with actor and timestamp.
4. `source_row_hash` supports idempotency checks if the same export row is re-uploaded.

## Unit normalization strategy

Normalization is intentionally **minimal but explicit**:
- Fuel → liters (`L`) when unit is `L`, `GAL`, or approximate `KG` conversion
- Electricity → `kWh` (supports `MWh` uplift)
- Travel distance → `km` when provided or inferred from airport pair lookup table

A production system would move factors and conversions into versioned reference tables.

## What we deliberately did not model yet

- Emission factor catalog and CO₂e calculation outputs
- Plant / facility master data tables (we keep codes as strings + flags)
- Full double-entry financial reconciliation for SAP amounts

These are documented in `TRADEOFFS.md`.
