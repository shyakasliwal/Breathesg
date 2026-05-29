# Decisions

## Product framing

**Chosen:** Build an analyst **review gate** between ingest and audit, not a full carbon accounting platform.

**Why:** The assignment stresses messy inbound data and sign-off. Calculation can be downstream once activity rows are trusted.

**Would ask PM:** Do auditors need calculated CO₂e in v1, or only approved activity quantities?

---

## Source 1 — SAP (fuel & procurement)

**Researched:** SAP MM movement / material document style exports (flat CSV with `WERKS`, `MATNR`, `MENGE`, `MEINS`, `BUDAT`), not full IDoc orchestration.

**Chosen mechanism:** **File upload** of a flat export (semicolon or comma; auto-detected).

**Why:** Enterprise SAP teams most often give consultants a scheduled flat file from a report variant or PI/PO job before API access is approved. Upload matches week-1 onboarding reality. Semicolon is common when European decimal commas would break comma-delimited files.

**Subset handled**
- One plant code per row
- Material number + text
- Quantity + unit
- Posting date in EU formats (`DD.MM.YYYY`)
- Optional local amount (`DMBTR`) and currency

**Ignored (for prototype)**
- IDoc ACK/NAK processing
- Batch-level goods movements aggregation
- Plant metadata enrichment (names, country, grid region)
- German/English header auto-detection beyond normalized keys

**Ambiguity:** Is heating oil Scope 1 or a district energy edge case?
**Decision:** Treat diesel/heating oil/gasoline material families as Scope 1 fuel; everything else defaults to Scope 3 procurement.

---

## Source 2 — Utility electricity

**Researched:** Utility portal CSV exports (account, meter, billing period, kWh, tariff, total charge). PDF bill parsing deferred.

**Chosen mechanism:** **CSV upload** from portal export.

**Why:** Facilities teams routinely download CSV/Excel from supplier portals. PDF OCR is higher risk for a 4-day prototype.

**Subset handled**
- Billing period start/end (non-calendar months)
- Meter ID + site code
- Usage + unit normalization to kWh
- Tariff label and bill total

**Ignored**
- Time-of-use interval data (15-min demand)
- Multi-meter aggregation rules
- Tariff cost allocation math

**Ambiguity:** Which date drives reporting when period crosses months?
**Decision:** Store full period on the row; use `period_end` as `activity_date` for sorting, flag spans >40 days.

---

## Source 3 — Corporate travel

**Researched:** Concur-style expense report exports (category, dates, airports, amount). Also reviewed public API patterns (OAuth, paginated expense reports).

**Chosen mechanism:** **CSV upload** shaped like a finance export.

**Why:** Travel API access often requires separate security review. CSV is what analysts receive first during onboarding.

**Subset handled**
- Air / hotel / ground categorization
- Airport codes with distance inference table when km missing
- High-spend flag for analyst attention

**Ignored**
- Live Concur/Navan API pull
- Cabin class emission factors
- Hotel nights vs spend-based hotel modeling

**Ambiguity:** Flight distance missing — block ingest or infer?
**Decision:** Ingest row, flag `distance_inferred_missing`, let analyst approve or reject.

---

## Ingestion & review workflow

| Step | Behavior |
|------|----------|
| Upload | Creates `IngestionBatch`, parses rows into `ActivityRecord` |
| Parse failure | Row kept with `parse_ok=false`, visible in Failed filter |
| Suspicious | Any non-empty `validation_flags` |
| Approve | Sets approved + `is_locked_for_audit=true` + audit event |
| Reject | Marks rejected, not locked |

**Would ask PM:** Can analysts edit quantities pre-approval, or only approve/reject? We implemented approve/reject only to preserve raw source integrity.

---

## Stack & deployment

- Django REST + SQLite locally (Postgres in production)
- React + Vite dashboard
- Render blueprint (`render.yaml`) for mandatory deployment
