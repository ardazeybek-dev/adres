"""Messy, real-world style addresses and what each one must parse into.

Only the listed fields are checked, so a case says exactly what it is about.
"""

import pytest

from adres import parse

CASES = [
    # --- the common shapes -------------------------------------------------
    (
        "Caferağa Mah. Moda Cad. No:12 D:3 34710 Kadıköy/İstanbul",
        dict(
            neighbourhood="Caferağa",
            avenue="Moda",
            building_no="12",
            apartment="3",
            postal_code="34710",
            district="Kadıköy",
            province="İstanbul",
            plate=34,
        ),
    ),
    (
        "Kazımdirik Mahallesi 372/8 Sokak No: 5 Kat: 2 Daire: 4 Bornova - İzmir",
        dict(
            neighbourhood="Kazımdirik",
            street="372/8",
            building_no="5",
            floor="2",
            apartment="4",
            district="Bornova",
            province="İzmir",
        ),
    ),
    (
        "ATATÜRK MAH. 1453 SK. NO:7/2 ÇANKAYA/ANKARA",
        dict(
            neighbourhood="Atatürk",
            street="1453",
            building_no="7",
            apartment="2",
            district="Çankaya",
            province="Ankara",
        ),
    ),
    (
        "kızılay mh. atatürk blv. no 45 çankaya ankara",
        dict(
            neighbourhood="Kızılay",
            boulevard="Atatürk",
            building_no="45",
            district="Çankaya",
            province="Ankara",
        ),
    ),
    (
        "Cumhuriyet Mah. Gazi Cd. No:3 Merkez/Kütahya",
        dict(
            neighbourhood="Cumhuriyet",
            avenue="Gazi",
            building_no="3",
            district="Kütahya",
            province="Kütahya",
        ),
    ),
    # --- no diacritics / wrong case ------------------------------------------
    (
        "bostanci mah. mehmet sevki pasa cad. no:21 kadikoy istanbul",
        dict(
            neighbourhood="Bostanci",
            avenue="Mehmet Sevki Pasa",
            building_no="21",
            district="Kadıköy",
            province="İstanbul",
        ),
    ),
    (
        "Merkez Mah. Kagithane Cad. No 8 Kagithane / ISTANBUL",
        dict(
            neighbourhood="Merkez",
            avenue="Kagithane",
            building_no="8",
            district="Kâğıthane",
            province="İstanbul",
        ),
    ),
    (
        "SAKARYA CAD. NO:10 ESKİŞEHİR",
        dict(avenue="Sakarya", building_no="10", province="Eskişehir", district=None),
    ),
    # --- floor, flat, block, site, apartment building --------------------------
    (
        "Yeşilyurt Mah. Lale Sok. Gül Apt. No:4 Kat 3 Daire 6 Yeşilyurt/Malatya",
        dict(
            neighbourhood="Yeşilyurt",
            street="Lale",
            building="Gül",
            building_no="4",
            floor="3",
            apartment="6",
            district="Yeşilyurt",
            province="Malatya",
        ),
    ),
    (
        "Ataşehir Mah. Ihlamur Sitesi B Blok Kat:5 D:18 Ataşehir İstanbul",
        dict(
            neighbourhood="Ataşehir",
            site="Ihlamur",
            block="B",
            floor="5",
            apartment="18",
            district="Ataşehir",
            province="İstanbul",
        ),
    ),
    (
        "Bahçelievler Mah. 2. Cadde Blok A No:3 Zemin Kat Elazığ",
        dict(
            neighbourhood="Bahçelievler",
            avenue="2.",
            block="A",
            building_no="3",
            floor="0",
            province="Elazığ",
        ),
    ),
    (
        "Fatih Mah. 12. Sokak No:5 2. Kat Daire 4 Esenyurt İstanbul",
        dict(
            neighbourhood="Fatih",
            street="12.",
            building_no="5",
            floor="2",
            apartment="4",
            district="Esenyurt",
            province="İstanbul",
        ),
    ),
    (
        "Barbaros Mah. Begonya Sk. No:3A İç Kapı No:12 Ataşehir/İstanbul",
        dict(
            neighbourhood="Barbaros",
            street="Begonya",
            building_no="3A",
            apartment="12",
            district="Ataşehir",
            province="İstanbul",
        ),
    ),
    # --- separators and glued punctuation --------------------------------------
    (
        "Konak Mah.,Cumhuriyet Blv.,No:15/7,35250,Konak,İzmir",
        dict(
            neighbourhood="Konak",
            boulevard="Cumhuriyet",
            building_no="15",
            apartment="7",
            postal_code="35250",
            district="Konak",
            province="İzmir",
        ),
    ),
    (
        "Alsancak Mah.Kıbrıs Şehitleri Cad.No:140 Konak-İzmir",
        dict(
            neighbourhood="Alsancak",
            avenue="Kıbrıs Şehitleri",
            building_no="140",
            district="Konak",
            province="İzmir",
        ),
    ),
    (
        "Kocatepe Mahallesi\nMithatpaşa Caddesi No:30\nÇankaya / ANKARA",
        dict(
            neighbourhood="Kocatepe",
            avenue="Mithatpaşa",
            building_no="30",
            district="Çankaya",
            province="Ankara",
        ),
    ),
    # --- province / district resolution ----------------------------------------
    (
        "Selimiye Mah. Ereğli",
        dict(neighbourhood="Selimiye", district=None, province=None),
    ),
    (
        "Selimiye Mah. Ereğli/Konya",
        dict(neighbourhood="Selimiye", district="Ereğli", province="Konya"),
    ),
    (
        "Müftü Mah. Ereğli Zonguldak",
        dict(neighbourhood="Müftü", district="Ereğli", province="Zonguldak"),
    ),
    (
        "Yalı Mah. Bodrum",
        dict(neighbourhood="Yalı", district="Bodrum", province="Muğla"),
    ),
    (
        "Cumhuriyet Mah. İnönü Cad. No:5 Eyüp İstanbul",
        dict(avenue="İnönü", district="Eyüpsultan", province="İstanbul"),
    ),
    (
        "Saray Mah. Kazan / Ankara",
        dict(neighbourhood="Saray", district="Kahramankazan", province="Ankara"),
    ),
    (
        "Pazar Mah. Gölbaşı",
        dict(neighbourhood="Pazar", district=None, province=None),
    ),
    (
        "Hürriyet Mah. 06830 Gölbaşı",
        dict(postal_code="06830", district="Gölbaşı", province="Ankara"),
    ),
    (
        "Atatürk Cad. No:1 Antep",
        dict(avenue="Atatürk", building_no="1", province="Gaziantep"),
    ),
    (
        "Cumhuriyet Mah. No:9 Afyon",
        dict(neighbourhood="Cumhuriyet", building_no="9", province="Afyonkarahisar"),
    ),
    (
        "Haliliye / Urfa",
        dict(district="Haliliye", province="Şanlıurfa"),
    ),
    (
        "Kurtuluş Mah. 19 Mayıs Samsun",
        dict(neighbourhood="Kurtuluş", district="19 Mayıs", province="Samsun"),
    ),
    (
        "Hakkari merkez",
        dict(district="Hakkâri", province="Hakkâri"),
    ),
    (
        "Atatürk Mah. Kadıköy",
        dict(district="Kadıköy", province="İstanbul"),
    ),
    # --- a district-like name that is really the neighbourhood or street --------
    (
        "Bornova Mah. İzmir Cad. No:3 Buca İzmir",
        dict(neighbourhood="Bornova", avenue="İzmir", district="Buca", province="İzmir"),
    ),
    (
        "Ankara Cad. No:12 Fatih İstanbul",
        dict(avenue="Ankara", building_no="12", district="Fatih", province="İstanbul"),
    ),
    # --- postal code only tells the province ------------------------------------
    (
        "Mimar Sinan Mah. 75. Yıl Cad. No:44 16000",
        dict(
            neighbourhood="Mimar Sinan",
            avenue="75. Yıl",
            building_no="44",
            postal_code="16000",
            province="Bursa",
        ),
    ),
    (
        "Esentepe Mah. Büyükdere Cad. No:199 34394 Şişli",
        dict(postal_code="34394", district="Şişli", province="İstanbul"),
    ),
    # --- villages ----------------------------------------------------------------
    (
        "Karaağaç Köyü No:12 Gönen/Balıkesir",
        dict(village="Karaağaç", building_no="12", district="Gönen", province="Balıkesir"),
    ),
    (
        "Kılıçlar köyü Ayvacık Çanakkale",
        dict(village="Kılıçlar", district="Ayvacık", province="Çanakkale"),
    ),
    # --- leftovers are kept, not lost --------------------------------------------
    (
        "Moda Cad. No:5 Kahve Dünyası yanı Kadıköy İstanbul",
        dict(avenue="Moda", building_no="5", district="Kadıköy", rest="Kahve Dünyası yanı"),
    ),
    (
        "",
        dict(province=None, district=None, neighbourhood=None, rest=None),
    ),
    (
        "Kadıköy İstanbul",
        dict(district="Kadıköy", province="İstanbul", neighbourhood=None),
    ),
    (
        "İstanbul Kadıköy Caferağa Mah. Moda Cad. No:12",
        dict(
            province="İstanbul",
            district="Kadıköy",
            neighbourhood="Caferağa",
            avenue="Moda",
            building_no="12",
        ),
    ),
    # --- found while testing unseen addresses ----------------------------------
    (
        "Org. Nafiz Gürman Cad. No:8 K:3 D:7 Bakırköy İST.",
        dict(avenue="Org. Nafiz Gürman", floor="3", apartment="7", province="İstanbul", rest=None),
    ),
    (
        "Yeni Mah. Sanayi Sitesi 5. Blok No:22 Merkez / Aksaray",
        dict(site="Sanayi", block="5", building_no="22", district="Aksaray", rest=None),
    ),
    (
        "Sahrayıcedit Mah. Atatürk Cad. 36/1 Kadıköy",
        dict(avenue="Atatürk", building_no="36", apartment="1", province="İstanbul"),
    ),
    (
        "Atatürk Cad. 1453 Sk. No:2 Buca İzmir",
        dict(avenue="Atatürk", street="1453", building_no="2", district="Buca"),
    ),
    (
        "K.Maraş Onikişubat Hayrullah Mah.",
        dict(province="Kahramanmaraş", district="Onikişubat", neighbourhood="Hayrullah", rest=None),
    ),
    (
        "Bağlarbaşı Mah. 1. Sk. No:3 Daire:1 Maltepe İstanbul TÜRKİYE",
        dict(street="1.", district="Maltepe", province="İstanbul", rest=None),
    ),
    (
        "Adres: Merkez Mh. Okul Sk. No:2 Aksu Antalya",
        dict(neighbourhood="Merkez", street="Okul", district="Aksu", province="Antalya"),
    ),
    (
        "Fatih Sultan Mehmet Mah. Balkan Cad. No:62 Ümraniye/İstanbul",
        dict(neighbourhood="Fatih Sultan Mehmet", district="Ümraniye"),
    ),
    (
        "Mersin Yenişehir Pozcu Mah. 1601 Sk. No:4",
        dict(province="Mersin", district="Yenişehir", neighbourhood="Pozcu", street="1601"),
    ),
    (
        "Gazi Mustafa Kemal Bulvarı No:120/5 Maltepe Çankaya Ankara",
        dict(boulevard="Gazi Mustafa Kemal", district="Çankaya", rest="Maltepe"),
    ),
]


@pytest.mark.parametrize("text, expected", CASES, ids=[c[0][:45] or "empty" for c in CASES])
def test_golden(text, expected):
    got = parse(text).to_dict()
    assert {k: got[k] for k in expected} == expected
