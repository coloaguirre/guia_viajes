import csv

import openpyxl
import pytest

from guia.itinerary import parse_itinerary, slugify, split_places

ROWS = [
    ["Día", "Fecha", "Día semana", "Tramo / Base", "Kms", "Hs", "Noche en"],
    [1, "2026-12-01", "mar", "Buenos Aires – Azul", 300, 4, "Azul"],
    [2, "2026-12-02", "mié", "Azul - Bahía Blanca", 400, 5, "Bahía Blanca"],
    [3, "2026-12-03", "jue", "Base: Bahía Blanca (día libre)", 0, 0, "Bahía Blanca"],
    [None, None, None, None, None, None, None],
]


@pytest.fixture
def xlsx(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Itinerario de prueba"])  # title row above the header
    for r in ROWS:
        ws.append(r)
    p = tmp_path / "it.xlsx"
    wb.save(p)
    return p


@pytest.fixture
def csv_file(tmp_path):
    p = tmp_path / "it.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(ROWS[:-1])
    return p


def test_split_places():
    assert split_places("Buenos Aires – Azul") == ["Buenos Aires", "Azul"]
    assert split_places("Base: Bahía Blanca (día libre)") == ["Bahía Blanca"]
    assert split_places("San Martín de los Andes -> Villa La Angostura") == [
        "San Martín de los Andes",
        "Villa La Angostura",
    ]
    assert split_places(None) == []


def test_slugify():
    assert slugify("Bahía Blanca") == "bahia-blanca"


def test_parse_xlsx_unique_places_with_days_and_roles(xlsx):
    places = {p.nombre: p for p in parse_itinerary(xlsx)}
    assert list(places) == ["Buenos Aires", "Azul", "Bahía Blanca"]
    assert places["Azul"].dias == [1, 2]
    assert places["Azul"].roles == {"tramo", "noche"}
    assert places["Buenos Aires"].roles == {"tramo"}
    assert sorted(set(places["Bahía Blanca"].dias)) == [2, 3]


def test_parse_csv_matches_xlsx(xlsx, csv_file):
    a = [p.to_dict() for p in parse_itinerary(xlsx)]
    b = [p.to_dict() for p in parse_itinerary(csv_file)]
    assert a == b


def test_missing_columns_fail_loud(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Tramo"):
        parse_itinerary(p)
