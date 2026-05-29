from .sap import parse_sap_csv
from .travel import parse_travel_csv
from .utility import parse_utility_csv

PARSERS = {
    "sap": parse_sap_csv,
    "utility": parse_utility_csv,
    "travel": parse_travel_csv,
}
