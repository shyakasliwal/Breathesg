# Tradeoffs — three things we did not build

## 1. CO₂e calculation engine

**Not built:** Emission factor library, GWP versions, market- vs location-based Scope 2 logic, and calculated tCO₂e per row.

**Why:** The assignment’s core risk is **data ingestion quality and analyst sign-off**, not factor selection politics. Shipping a fake calculator would look feature-rich but dodge the hard problem.

**Impact:** Analysts approve normalized activity, not final audit numbers. Downstream service can consume locked rows.

---

## 2. Live API connectors (SAP OData, utility API, Concur API)

**Not built:** Scheduled pulls, OAuth token vaults, pagination, retry/backoff, and schema versioning per vendor API.

**Why:** Real connectors need client-specific credentials and security review. File upload matches first-week enterprise reality and keeps the prototype defensible.

**Impact:** Operations uploads exports manually. We still modeled `DataSource` so connectors can slot in later without schema churn.

---

## 3. PDF utility bill ingestion (OCR / layout parsing)

**Not built:** PDF upload, OCR, line-item extraction, and tariff table parsing.

**Why:** PDF layouts vary by utility and break often; CSV portal exports are what facilities teams already use when they need spreadsheets.

**Impact:** Clients on PDF-only workflows would need a one-time CSV conversion step or a future OCR pipeline (`SOURCES.md` covers failure modes).
