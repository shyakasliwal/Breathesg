from .common import normalize_row_keys, parse_date, parse_decimal, read_csv_rows, row_hash

AIRPORT_DISTANCE_KM = {
    ("DEL", "BOM"): 1150,
    ("LHR", "JFK"): 5540,
    ("SFO", "SEA"): 1090,
    ("FRA", "MUC"): 300,
}


def _pick(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row and row[key]:
            return row[key]
    return ""


def _infer_distance(origin: str, destination: str):
    if not origin or not destination:
        return None, ["missing_route"]
    pair = (origin.upper(), destination.upper())
    rev = (pair[1], pair[0])
    if pair in AIRPORT_DISTANCE_KM:
        return AIRPORT_DISTANCE_KM[pair], []
    if rev in AIRPORT_DISTANCE_KM:
        return AIRPORT_DISTANCE_KM[rev], []
    if len(origin) == 3 and len(destination) == 3:
        return None, ["distance_inferred_missing"]
    return None, ["non_airport_route"]


def parse_travel_csv(file_bytes: bytes) -> list[dict]:
    rows = [normalize_row_keys(r) for r in read_csv_rows(file_bytes)]
    parsed = []

    for idx, row in enumerate(rows, start=2):
        trip_id = _pick(row, "report_id", "trip_id", "expense_id")
        traveler = _pick(row, "employee_id", "traveler", "employee")
        category_raw = _pick(row, "expense_type", "category", "type").lower()
        start_date = parse_date(_pick(row, "start_date", "transaction_date", "departure_date"))
        end_date = parse_date(_pick(row, "end_date", "return_date"))
        origin = _pick(row, "origin", "from", "departure_airport")
        destination = _pick(row, "destination", "to", "arrival_airport")
        distance = parse_decimal(_pick(row, "distance_km", "distance"))
        amount = parse_decimal(_pick(row, "amount", "approved_amount"))
        currency = _pick(row, "currency") or "USD"
        vendor = _pick(row, "vendor", "merchant", "airline")

        flags = []
        if "air" in category_raw or "flight" in category_raw:
            category = "flight"
            scope = "scope_3"
            if distance is None:
                distance, dist_flags = _infer_distance(origin, destination)
                flags.extend(dist_flags)
        elif "hotel" in category_raw or "lodging" in category_raw:
            category = "hotel"
            scope = "scope_3"
        elif "rail" in category_raw or "car" in category_raw or "ground" in category_raw:
            category = "ground"
            scope = "scope_3"
        else:
            category = "ground"
            scope = "scope_3"
            flags.append("unknown_travel_category")

        if start_date is None:
            flags.append("missing_travel_date")
        if amount is not None and amount > 20000:
            flags.append("high_spend")
        if category == "flight" and not origin and not destination:
            flags.append("missing_airport_codes")

        parse_ok = "missing_travel_date" not in flags

        parsed.append(
            {
                "scope": scope,
                "category": category,
                "activity_date": start_date,
                "period_start": start_date,
                "period_end": end_date,
                "facility_code": traveler,
                "vendor_or_carrier": vendor,
                "description": _pick(row, "description", "memo") or category_raw,
                "quantity": amount,
                "unit": currency,
                "normalized_quantity": distance,
                "normalized_unit": "km" if distance is not None else "",
                "spend_amount": amount,
                "spend_currency": currency,
                "origin": origin,
                "destination": destination,
                "distance_km": distance,
                "raw_payload": row,
                "source_row_hash": row_hash("travel", row),
                "source_reference": trip_id or f"row-{idx}",
                "parse_ok": parse_ok,
                "validation_flags": flags,
                "validation_message": "; ".join(flags),
            }
        )

    return parsed
