"""Split free-form Turkish addresses into province, district, neighbourhood, street and number."""

from .address import Address, parse
from .places import districts, lookup_postal_code, plate_of, provinces
from .text import fold

__version__ = "0.1.0"

__all__ = [
    "Address",
    "districts",
    "fold",
    "lookup_postal_code",
    "parse",
    "plate_of",
    "provinces",
]
