"""Lookups over the official list of 81 provinces and 973 districts."""

from __future__ import annotations

from ._data import DISTRICTS, PROVINCES
from .text import fold

# Colloquial or former names that still appear in addresses.
PROVINCE_ALIASES = {
    "afyon": 3,
    "antep": 27,
    "icel": 33,
    "ist": 34,
    "maras": 46,
    "k maras": 46,
    "kmaras": 46,
    "urfa": 63,
}
DISTRICT_ALIASES = {
    "eyup": (34, "Eyüpsultan"),
    "kazan": (6, "Kahramankazan"),
    "karadeniz eregli": (67, "Ereğli"),
    "karadeniz ereglisi": (67, "Ereğli"),
    "ondokuz mayis": (55, "19 Mayıs"),
}

_PROVINCE_BY_KEY: dict[str, int] = {fold(name): plate for plate, name in PROVINCES.items()}
_PROVINCE_BY_KEY.update(PROVINCE_ALIASES)

_DISTRICTS_BY_KEY: dict[str, list[tuple[int, str]]] = {}
for _plate, _name, _ in DISTRICTS:
    _DISTRICTS_BY_KEY.setdefault(fold(_name), []).append((_plate, _name))
for _key, _value in DISTRICT_ALIASES.items():
    _DISTRICTS_BY_KEY.setdefault(fold(_key), []).append(_value)

_POSTAL: dict[int, list[tuple[str, int, int]]] = {}
for _plate, _name, _ranges in DISTRICTS:
    for _lo, _hi in _ranges:
        _POSTAL.setdefault(_plate, []).append((_name, _lo, _hi))

MAX_WORDS = 2
"""Longest name, in words, that a lookup can match ("19 Mayıs", "K. Maraş")."""


def provinces() -> list[str]:
    """All 81 provinces, in plate-number order."""
    return list(PROVINCES.values())


def districts(province: str | int) -> list[str]:
    """Districts of a province, given by name (any spelling) or plate number.

    >>> districts("istanbul")[:3]
    ['Adalar', 'Arnavutköy', 'Ataşehir']
    """
    plate = province if isinstance(province, int) else find_province(province)
    if plate is None or plate not in PROVINCES:
        raise KeyError(province)
    return [name for p, name, _ in DISTRICTS if p == plate]


def plate_of(province: str) -> int | None:
    """Plate number of a province name, or ``None``.

    >>> plate_of("Kahramanmaraş"), plate_of("K.Maraş"), plate_of("ANTEP")
    (46, 46, 27)
    """
    return find_province(province)


def find_province(text: str) -> int | None:
    return _PROVINCE_BY_KEY.get(fold(text.replace(".", ". ")))


def find_districts(text: str) -> list[tuple[int, str]]:
    """Every (plate, district) the text can name; several for shared names."""
    return list(_DISTRICTS_BY_KEY.get(fold(text), []))


def lookup_postal_code(code: str | int) -> tuple[str, str | None] | None:
    """Province and, when only one district's range holds it, the district.

    The first two digits of a Turkish postal code are the plate number, so the
    province is always known. District ranges overlap in places; then the
    district is ``None`` rather than a guess.

    >>> lookup_postal_code("34710")
    ('İstanbul', 'Kadıköy')
    >>> lookup_postal_code("99000") is None
    True
    """
    s = str(code).strip()
    if not (len(s) == 5 and s.isdigit()):
        return None
    plate = int(s[:2])
    if plate not in PROVINCES:
        return None
    n = int(s)
    hits = {name for name, lo, hi in _POSTAL.get(plate, []) if lo <= n <= hi}
    return PROVINCES[plate], (hits.pop() if len(hits) == 1 else None)
