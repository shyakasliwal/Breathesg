import csv
import hashlib
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser


def read_csv_rows(file_bytes: bytes) -> list[dict]:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if reader.fieldnames and len(reader.fieldnames) == 1:
        reader = csv.DictReader(io.StringIO(text), delimiter=",")
    return list(reader)


def normalize_header(name: str) -> str:
    return re.sub(r"\s+", "_", (name or "").strip().lower())


def normalize_row_keys(row: dict) -> dict:
    return {normalize_header(k): (v or "").strip() for k, v in row.items()}


def row_hash(source_type: str, row: dict) -> str:
    payload = "|".join(f"{k}={row.get(k, '')}" for k in sorted(row.keys()))
    return hashlib.sha256(f"{source_type}:{payload}".encode()).hexdigest()


def parse_decimal(value: str) -> Decimal | None:
    if value is None:
        return None
    cleaned = str(value).strip().replace(" ", "")
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(value: str):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    try:
        return date_parser.parse(value, dayfirst=True).date()
    except (ValueError, OverflowError):
        return None


def convert_to_liters(quantity: Decimal | None, unit: str) -> tuple[Decimal | None, str]:
    if quantity is None:
        return None, ""
    unit = (unit or "").upper()
    if unit in ("L", "LTR", "LT", "LITER", "LITRE"):
        return quantity, "L"
    if unit in ("GAL", "GALLON", "USG"):
        return (quantity * Decimal("3.78541")).quantize(Decimal("0.001")), "L"
    if unit in ("KG", "KGM"):
        return (quantity / Decimal("0.84")).quantize(Decimal("0.001")), "L"
    return quantity, unit


def convert_to_kwh(quantity: Decimal | None, unit: str) -> tuple[Decimal | None, str]:
    if quantity is None:
        return None, ""
    unit = (unit or "").upper()
    if unit in ("KWH", "KW·H"):
        return quantity, "kWh"
    if unit in ("MWH",):
        return (quantity * Decimal("1000")).quantize(Decimal("0.001")), "kWh"
    return quantity, unit
