# Sources — research, sample data, and production failure modes

## 1. SAP — fuel & procurement

### What we researched
- SAP MM material document / movement list exports used in sustainability extracts
- Common column names: `WERKS` (plant), `MATNR` (material), `MAKTX` (description), `MENGE` (quantity), `MEINS` (unit), `BUDAT` (posting date)
- Export channels considered: IDoc, OData, BAPI, flat file
- **Chose flat CSV upload** (semicolon or comma; parser auto-detects) because it is the lowest-friction handoff from client IT in early onboarding

### What we learned
- Units mix liters, gallons, pieces (`ST`), and sometimes mass
- Dates appear as German `DD.MM.YYYY`
- Plant codes are meaningless without a master mapping table
- Not every movement row is fuel — material text drives classification

### Sample file: `sample_data/sap_sample.csv`
- Includes diesel, heating oil, office paper, packaging, and a **zero-quantity gasoline** row to trigger validation failure
- Comma-delimited for readability in GitHub/docs; production SAP exports often use `;` when amounts use European decimals
- Uses `,` decimal separator in quantities (European style, quoted in CSV where needed)
- German-style dates and EUR amounts

### Would break in production
- Client sends XLSX with multiple tabs or changing column order without notice
- Material classification requires client-specific rules beyond keyword matching
- Duplicate postings across delta loads without idempotency policy
- Currency and UoM conversions need authoritative master data

---

## 2. Utility — electricity

### What we researched
- Typical utility portal CSV fields: account number, meter ID, billing period, kWh usage, tariff/rate schedule, total charge
- Billing periods often **do not align** to calendar months (mid-month cycles)

### What we learned
- Scope 2 reporting needs retained **billing period boundaries**, not just a single month bucket
- Extremely high kWh values are usually data errors or missing decimal separators — better flagged than silently accepted

### Sample file: `sample_data/utility_sample.csv`
- Mix of ~30-day and longer periods (Feb–Mar cross-month)
- One intentionally extreme usage row (`920450` kWh) to surface `suspiciously_high_usage`
- Multiple sites/meters for the same enterprise client

### Would break in production
- PDF-only utilities (no stable CSV schema)
- Multiple meters rolled into one bill without line-level detail
- Canceled/rebilled statements creating duplicate periods
- Missing grid region for location-based emission factors

---

## 3. Corporate travel

### What we researched
- Concur expense export patterns: `expense_type`, traveler/employee ID, dates, vendor, amount, airports
- API docs emphasize OAuth, report IDs, and paginated expense details — heavier than CSV for a prototype

### What we learned
- Flights often lack distance; airport codes are more reliable than free-text cities
- Different categories need different downstream factors (flight vs hotel nights vs car km)
- Finance exports include **outlier spend** that analysts must see before lock

### Sample file: `sample_data/travel_sample.csv`
- Air row DEL→BOM without distance (tests inference + missing flag)
- Hotel row without route
- Car row with explicit `distance_km`
- Air row LHR→JFK with very high amount to trigger `high_spend`

### Would break in production
- Multi-leg itineraries stored as one line item
- Personal vs business expense splits
- Refunds/chargebacks after approval
- API schema changes per TMC (Concur vs Navan vs custom)
