import pytest

from adres import districts, fold, lookup_postal_code, parse, plate_of, provinces
from adres._data import DISTRICTS, PROVINCES


def test_official_counts():
    assert len(PROVINCES) == 81
    assert len(DISTRICTS) == 973
    assert sorted(PROVINCES) == list(range(1, 82))


def test_every_postal_range_belongs_to_its_province():
    for plate, name, ranges in DISTRICTS:
        for lo, hi in ranges:
            assert lo // 1000 == plate and hi // 1000 == plate and lo <= hi, name


def test_provinces_in_plate_order():
    assert provinces()[:3] == ["Adana", "Adıyaman", "Afyonkarahisar"]
    assert provinces()[33] == "İstanbul"


@pytest.mark.parametrize("name", ["İstanbul", "ISTANBUL", "istanbul", "İSTANBUL", 34])
def test_districts_any_spelling(name):
    assert len(districts(name)) == 39


def test_districts_unknown():
    with pytest.raises(KeyError):
        districts("Atlantis")


@pytest.mark.parametrize(
    "name, plate",
    [("Iğdır", 76), ("IĞDIR", 76), ("igdir", 76), ("Afyon", 3), ("İçel", 33), ("Narnia", None)],
)
def test_plate_of(name, plate):
    assert plate_of(name) == plate


def test_postal_code():
    assert lookup_postal_code("34710") == ("İstanbul", "Kadıköy")
    assert lookup_postal_code(6830) is None  # needs the leading zero
    assert lookup_postal_code("06830") == ("Ankara", None)  # ranges overlap: no guess
    assert lookup_postal_code("82000") is None
    assert lookup_postal_code("3471") is None


def test_fold_turkish_i():
    assert fold("IŞIK") == fold("ışık") == "isik"
    assert fold("İZMİR") == "izmir"


def test_postal_code_conflict_is_reported():
    a = parse("Moda Cad. No:1 06100 Kadıköy İstanbul")
    assert a.province == "İstanbul"
    assert a.warnings and "Ankara" in a.warnings[0]


def test_ambiguous_district_is_reported():
    a = parse("Selimiye Mah. Ereğli")
    assert a.district is None
    assert "Konya" in a.warnings[0] and "Zonguldak" in a.warnings[0]


def test_street_number_is_not_a_postal_code():
    a = parse("Kazım Dirik Mah. 35210 Sokak No:4 Bornova İzmir")
    assert a.postal_code is None
    assert a.street == "35210"


def test_format_round_trip():
    a = parse("ATATÜRK MAH. 1453 SK. NO:7/2 KAT 3 ÇANKAYA/ANKARA 06420")
    assert a.format() == "Atatürk Mah. 1453 Sk. No:7 Kat:3 D:2 06420 Çankaya/Ankara"
    assert parse(a.format()).to_dict() == a.to_dict()


def test_format_keeps_unrecognised_text():
    assert parse("Selimiye Mah. Ereğli").format() == "Selimiye Mah. Ereğli"
    a = parse("Moda Cad. No:5 Kahve Dünyası yanı Kadıköy")
    assert a.format() == "Moda Cad. No:5 Kahve Dünyası yanı Kadıköy/İstanbul"
    assert parse(a.format()).to_dict() == a.to_dict()
