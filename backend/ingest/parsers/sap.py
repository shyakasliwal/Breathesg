from decimal import Decimal

from .common import (
    convert_to_liters,
    normalize_row_keys,
    parse_date,
    parse_decimal,
    read_csv_rows,
    row_hash,
)

FUEL_MATERIAL_PREFIXES = ("DIESEL", "PETROL", "GASOL", "HEIZ", "KEROS", "LPG", "CNG")
PROCUREMENT_HINTS = ("PURCHASE", "PROC", "RAW", "PACK", "OFFICE")


def _pick(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row and row[key]:
            return row[key]
    return ""


def parse_sap_csv(file_bytes: bytes) -> list[dict]:
    rows = [normalize_row_keys(r) for r in read_csv_rows(file_bytes)]
    parsed = []

    for idx, row in enumerate(rows, start=2):
        plant = _pick(row, "werks", "plant", "plant_code")
        material = _pick(row, "matnr", "material", "material_number")
        description = _pick(row, "maktx", "material_text", "description")
        qty = parse_decimal(_pick(row, "menge", "quantity", "qty"))
        unit = _pick(row, "meins", "unit", "uom")
        posting_date = parse_date(_pick(row, "budat", "posting_date", "document_date"))
        doc_number = _pick(row, "belnr", "document_number", "doc_no")
        vendor = _pick(row, "lifnr", "vendor", "supplier")
        cost_center = _pick(row, "kostl", "cost_center")

        flags = []
        if not plant:
            flags.append("missing_plant_code")
        if qty is None:
            flags.append("missing_quantity")
        if not unit:
            flags.append("missing_unit")

        material_upper = (material + " " + description).upper()
        is_fuel = any(h in material_upper for h in FUEL_MATERIAL_PREFIXES)
        is_procurement = any(h in material_upper for h in PROCUREMENT_HINTS) or not is_fuel

        if is_fuel:
            scope = "scope_1"
            category = "fuel"
            normalized_qty, normalized_unit = convert_to_liters(qty, unit)
            if unit and normalized_unit not in ("L", "") and unit.upper() not in ("L", "LTR", "GAL", "KG"):
                flags.append("unusual_fuel_unit")
        else:
            scope = "scope_3"
            category = "procurement"
            normalized_qty, normalized_unit = qty, unit

        if qty is not None and qty <= 0:
            flags.append("non_positive_quantity")
        if posting_date is None:
            flags.append("unparsed_date")

        parse_ok = "missing_quantity" not in flags and "non_positive_quantity" not in flags

        parsed.append(
            {
                "scope": scope,
                "category": category,
                "activity_date": posting_date,
                "period_start": None,
                "period_end": None,
                "facility_code": plant or cost_center,
                "vendor_or_carrier": vendor,
                "description": description or material,
                "quantity": qty,
                "unit": unit,
                "normalized_quantity": normalized_qty,
                "normalized_unit": normalized_unit or "",
                "spend_amount": parse_decimal(_pick(row, "dmbtr", "amount", "value_local")),
                "spend_currency": _pick(row, "waers", "currency") or "EUR",
                "origin": "",
                "destination": "",
                "distance_km": None,
                "raw_payload": row,
                "source_row_hash": row_hash("sap", row),
                "source_reference": doc_number or f"row-{idx}",
                "parse_ok": parse_ok,
                "validation_flags": flags,
                "validation_message": "; ".join(flags),
            }
        )

    return parsed
