"""Split a free-form Turkish address into its parts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from . import places
from ._data import PROVINCES
from .text import fold, title

# Word that ends a named part -> the field that part goes into.
_KEYWORDS = {
    "neighbourhood": ("mah", "mh", "mahalle", "mahallesi", "mahal"),
    "village": ("koy", "koyu"),
    "boulevard": ("blv", "bulv", "bul", "bulvar", "bulvari"),
    "avenue": ("cad", "cd", "cadde", "caddesi", "cadd"),
    "street": ("sk", "sok", "sokak", "sokagi", "skk"),
    "site": ("sit", "site", "sitesi"),
    "building": ("ap", "apt", "apart", "apartman", "apartmani"),
}
_FIELD_OF = {word: name for name, words in _KEYWORDS.items() for word in words}

_LETTER = r"[^\W\d_]"
_I = "[İIiı]"
_NUM = r"\d+[A-Za-zÇĞİÖŞÜçğıöşü]?"

# Labelled parts, removed from the text before the named parts are read.
# Order matters: "İç Kapı No:3" must go before plain "No:3".
_LABELS: list[tuple[str, re.Pattern[str]]] = [
    ("apartment", re.compile(rf"\b{_I}ç\s*Kap{_I}\s*(?:No|Numara)?\s*[:.]?\s*({_NUM})\b", re.I)),
    (
        "building_no",
        re.compile(rf"\b(?:No|Numara|Nu)\b\s*[:.]?\s*({_NUM})(?:\s*/\s*({_NUM}))?\b", re.I),
    ),
    ("apartment", re.compile(r"\b(?:Daire|D)\s*[:.]\s*(\d+)\b", re.I)),
    ("apartment", re.compile(rf"\bDa{_I}re\s+(\d+)\b", re.I)),
    ("floor", re.compile(r"\b(\d+)\s*\.\s*Kat\b", re.I)),
    ("floor", re.compile(r"\b(?:Kat|K)\s*[:.]\s*(-?\d+)\b", re.I)),
    ("floor", re.compile(r"\bKat\s+(-?\d+)\b", re.I)),
    ("floor_ground", re.compile(r"\bZem[iİ]n\s*Kat\b", re.I)),
    ("floor_basement", re.compile(r"\bBodrum\s*Kat\b", re.I)),
    ("block", re.compile(r"\b([A-ZÇĞİÖŞÜ0-9]{1,2})\s*[-.]?\s*Blo(?:k|ğu|ku)\b", re.I)),
    ("block", re.compile(r"\bBlok\s*[:.]?\s*(?!No\b|D\b|K\b)([A-ZÇĞİÖŞÜ0-9]{1,2})\b", re.I)),
]

_STREETISH = r"(?:sk|sok|sokak|cad|cd|cadde|caddesi|blv|bulvar|bulvarı|mah|mh)\b"
_POSTAL = re.compile(
    rf"(?<![\d/.:])\b((?:0[1-9]|[1-7]\d|8[01])\d{{3}})\b(?![/.]?\d)(?!\s*\.?\s*{_STREETISH})",
    re.I,
)
_BREAK = "\x00"
_BARE_NUMBER = re.compile(r"^(\d+[A-Za-z]?)(?:/(\d+))?$")
_COUNTRY = {"turkiye", "turkey", "tr"}
_ROAD = {"boulevard", "avenue", "street", "building"}


@dataclass
class Address:
    """The parts of an address. A part that was not found is ``None``.

    ``rest`` keeps whatever was not recognised ("Kahve Dünyası yanı"), so no
    text is silently dropped. ``warnings`` explains doubts, such as a district
    name that exists in more than one province.
    """

    province: str | None = None
    district: str | None = None
    neighbourhood: str | None = None
    village: str | None = None
    boulevard: str | None = None
    avenue: str | None = None
    street: str | None = None
    site: str | None = None
    building: str | None = None
    block: str | None = None
    building_no: str | None = None
    floor: str | None = None
    apartment: str | None = None
    postal_code: str | None = None
    plate: int | None = None
    rest: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def format(self) -> str:
        """One-line address in the usual written order.

        >>> parse("caferağa mh moda cd no 12 d:3 kadıköy istanbul").format()
        'Caferağa Mah. Moda Cad. No:12 D:3 Kadıköy/İstanbul'
        """
        parts = []
        for value, suffix in (
            (self.neighbourhood, "Mah."),
            (self.village, "Köyü"),
            (self.boulevard, "Blv."),
            (self.avenue, "Cad."),
            (self.street, "Sk."),
            (self.site, "Sitesi"),
            (self.building, "Apt."),
        ):
            if value:
                parts.append(f"{value} {suffix}")
        if self.block:
            parts.append(f"{self.block} Blok")
        if self.building_no:
            parts.append(f"No:{self.building_no}")
        if self.floor:
            parts.append(f"Kat:{self.floor}")
        if self.apartment:
            parts.append(f"D:{self.apartment}")
        if self.rest:
            parts.append(self.rest)
        if self.postal_code:
            parts.append(self.postal_code)
        place = "/".join(p for p in (self.district, self.province) if p)
        if place:
            parts.append(place)
        return " ".join(parts)

    def __str__(self) -> str:
        return self.format()


def _prepare(text: str) -> str:
    s = text.replace("\r", "\n").replace("\n", ",").replace("\xa0", " ")
    s = re.sub(r"^\s*(?:açık adres|adres|address)\s*:\s*", "", s, flags=re.I)
    s = re.sub(rf"(?<={_LETTER})\.(?={_LETTER})", ". ", s)  # "Mah.Moda" -> "Mah. Moda"
    return " ".join(s.split())


def _take_labels(s: str, out: Address) -> str:
    for name, pattern in _LABELS:
        match = pattern.search(s)
        if not match:
            continue
        if name == "building_no":
            out.building_no = match.group(1).upper()
            if match.group(2) and out.apartment is None:
                out.apartment = match.group(2).upper()
        elif name == "floor_ground":
            out.floor = out.floor or "0"
        elif name == "floor_basement":
            out.floor = out.floor or "-1"
        elif getattr(out, name) is None:
            setattr(out, name, match.group(1).upper())
        s = s[: match.start()] + f" {_BREAK} " + s[match.end() :]
    match = _POSTAL.search(s)
    if match:
        out.postal_code = match.group(1)
        s = s[: match.start()] + f" {_BREAK} " + s[match.end() :]
    return s


def _tokens(s: str) -> list[str]:
    """Words, with ``_BREAK`` wherever a separator splits the address."""
    s = s.replace(",", f" {_BREAK} ").replace(";", f" {_BREAK} ")
    s = re.sub(r"(?<!\d)\s*/\s*|\s*/\s*(?!\d)", f" {_BREAK} ", s)
    s = re.sub(rf"(?<={_LETTER})-(?={_LETTER})|\s+-+\s+|^-+\s+|\s+-+$", f" {_BREAK} ", s)
    return [w for w in s.split() if w not in ("-", "–")]


def _peel(words: list[str], kind: str) -> tuple[list[str], list[str]]:
    """Split "İstanbul Kadıköy Caferağa" before "Mah." into place + name.

    Only a leading province (with an optional district of it) is taken off,
    and at least one word is always left as the name.
    """
    plate = None
    for n in range(min(places.MAX_WORDS, len(words) - 1), 0, -1):
        plate = places.find_province(" ".join(words[:n]))
        if plate:
            break
    if not plate:
        return [], words
    rest = words[n:]
    for m in range(min(places.MAX_WORDS, len(rest) - 1), 0, -1):
        if any(p == plate for p, _ in places.find_districts(" ".join(rest[:m]))):
            return words[: n + m], rest[m:]
    if kind in ("neighbourhood", "village"):
        return words[:n], rest
    return [], words


def _read_named(words: list[str], out: Address) -> list[list[str]]:
    """Fill the keyword-ended parts; return the leftover word groups."""
    leftovers: list[list[str]] = []
    extra: list[str] = []
    buffer: list[str] = []
    words = [*words, _BREAK]
    skip = False
    for at, word in enumerate(words):
        if skip:
            skip = False
            continue
        if word == _BREAK:
            if buffer:
                leftovers.append(buffer)
            buffer = []
            continue
        kind = _FIELD_OF.get(fold(word))
        if kind is None or not buffer:
            buffer.append(word)
            continue
        place, name = _peel(buffer, kind)
        if place:
            leftovers.append(place)
        value = " ".join(name).strip(" ,")
        if value.endswith(".") and not value[-2:-1].isdigit():  # keep "12." in "12. Sokak"
            value = value[:-1]
        value = title(value)
        if getattr(out, kind) is None:
            setattr(out, kind, value)
        else:
            extra.append(f"{value} {word}")
        buffer = []
        # "Atatürk Cad. 36/1": a bare number right after the road is the door number,
        # unless it starts the next road's name ("Atatürk Cad. 1453 Sk.").
        number = _BARE_NUMBER.match(words[at + 1])
        if kind in _ROAD and number and out.building_no is None:
            following = words[at + 2] if at + 2 < len(words) else _BREAK
            if _FIELD_OF.get(fold(following)) is None:
                out.building_no = number.group(1).upper()
                if number.group(2) and out.apartment is None:
                    out.apartment = number.group(2)
                skip = True
    if extra:
        leftovers.append(extra)
    return leftovers


def _find_place(groups: list[list[str]], out: Address) -> None:
    """Pick the province and district out of the leftover words."""
    groups = [[w for w in words if fold(w) not in _COUNTRY] for words in groups]
    flat = [(g, i) for g, words in enumerate(groups) for i in range(len(words))]
    used: set[tuple[int, int]] = set()

    def spans():
        # Later text wins ("... Kadıköy İstanbul"); longer names first ("K. Maraş").
        for g, end in reversed(flat):
            for n in range(places.MAX_WORDS, 0, -1):
                start = end - n + 1
                if start >= 0:
                    cells = [(g, j) for j in range(start, end + 1)]
                    if not used.intersection(cells):
                        yield " ".join(groups[g][start : end + 1]), cells

    plate = None
    for text, cells in spans():
        plate = places.find_province(text)
        if plate:
            used.update(cells)
            break

    postal_plate = int(out.postal_code[:2]) if out.postal_code else None
    if plate and postal_plate and plate != postal_plate:
        out.warnings.append(
            f"postal code {out.postal_code} belongs to {PROVINCES[postal_plate]}, "
            f"not {PROVINCES[plate]}"
        )

    district = None
    for text, cells in spans():
        if fold(text) == "merkez":
            if plate and PROVINCES[plate] in places.districts(plate):
                district = PROVINCES[plate]
                used.update(cells)
                break
            continue
        found = places.find_districts(text)
        if not found:
            continue
        if plate:
            found = [f for f in found if f[0] == plate]
        elif postal_plate:
            found = [f for f in found if f[0] == postal_plate] or found
        if len(found) == 1:
            district = found[0][1]
            plate = plate or found[0][0]
            used.update(cells)
            break
        if len(found) > 1:
            names = ", ".join(PROVINCES[p] for p, _ in found)
            out.warnings.append(f"district {found[0][1]!r} exists in {names}; province needed")
            break

    plate = plate or postal_plate
    if plate and plate in PROVINCES:
        out.province = PROVINCES[plate]
        out.plate = plate
        if district is None and out.postal_code and postal_plate == plate:
            district = (places.lookup_postal_code(out.postal_code) or (None, None))[1]
    out.district = district

    rest = []
    for g, words in enumerate(groups):
        kept = [w for i, w in enumerate(words) if (g, i) not in used]
        text = " ".join(kept).strip(" .,-")
        if text:
            rest.append(text)
    out.rest = ", ".join(rest) or None


def parse(text: str | None) -> Address:
    """Split an address written any common way into its parts.

    >>> a = parse("Caferağa Mah. Moda Cad. No:12/3 34710 Kadıköy/İSTANBUL")
    >>> a.neighbourhood, a.avenue, a.building_no, a.apartment, a.district, a.province
    ('Caferağa', 'Moda', '12', '3', 'Kadıköy', 'İstanbul')
    """
    out = Address()
    if not text or not text.strip():
        return out
    s = _take_labels(_prepare(text), out)
    groups = _read_named(_tokens(s), out)
    _find_place(groups, out)
    return out
