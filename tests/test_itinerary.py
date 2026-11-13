import csv

import openpyxl
import pytest

from guia.itinerary import Canon, parse_itinerary, slugify, split_places

ROWS = [
    ["Día", "Fecha", "Día semana", "Tramo / Base", "Kms", "Hs", "Noche en"],
    [1, "2026-12-01", "mar", "Buenos Aires – Azul", 300, 4, "Azul"],
    [2, "2026-12-02", "mié", "Azul a Bahía Blanca", 400, 5, "Bahía Blanca"],
    [3, "2026-12-03", "jue", "Base: Bahía Blanca (día libre)", 0, 0, "Bahía Blanca"],
    [4, "2026-12-04", "vie", "B. Blanca – Excursion", 0, 0, "Casa"],
    [None, None, None, "TOTAL VIAJE", 700, 9, None],
]
CFG = {
    "viaje": {"hoja": "Plan"},
    "alias": {"b. blanca": "Bahía Blanca"},
    "ignorar": ["casa", "excursion"],
    "extra": [{"nombre": "Tandil", "dias": [2]}],
    "fusionar": {"ruta-azul-bahia-blanca": "ruta-buenos-aires-azul"},
}


@pytest.fixture
def xlsx(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumen"
    ws.append(["Presupuesto", 123])  # unrelated first sheet with 2 cells
    ws2 = wb.create_sheet("Plan")
    ws2.append(["Itinerario de prueba"])
    ws2.append(["Velocidad", None, None, None, 90])  # 2-cell row that is NOT the header
    for r in ROWS:
        ws2.append(r)
    p = tmp_path / "it.xlsx"
    wb.save(p)
    return p


@pytest.fixture
def csv_file(tmp_path):
    p = tmp_path / "it.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(ROWS)
    return p


def test_split_places():
    assert split_places("Buenos Aires – Azul") == ["Buenos Aires", "Azul"]
    assert split_places("Base: Bahía Blanca (día libre)") == ["Bahía Blanca"]
    assert split_places("Gregores a PN Perito Moreno") == ["Gregores", "PN Perito Moreno"]
    assert split_places("San Martín de los Andes -> Villa La Angostura") == [
        "San Martín de los Andes",
        "Villa La Angostura",
    ]
    assert split_places("Bahía Bustamante (día completo)") == ["Bahía Bustamante"]
    assert split_places(None) == []


def test_canon_alias_and_ignore():
    c = Canon(CFG)
    assert split_places("B. Blanca – Excursion", c) == ["Bahía Blanca"]
    assert split_places("Casa", c) == []


def test_slugify():
    assert slugify("Bahía Blanca") == "bahia-blanca"


def test_parse_xlsx_places_tramos_and_extras(xlsx):
    places = {p.slug: p for p in parse_itinerary(xlsx, CFG)}
    assert [p for p in places if not p.startswith("ruta-")] == [
        "buenos-aires",
        "azul",
        "bahia-blanca",
        "tandil",
    ]
    assert places["azul"].dias == [1, 2]
    assert places["azul"].roles == {"tramo", "noche"}
    assert places["bahia-blanca"].dias == [2, 3, 4]
    assert places["tandil"].to_dict() == {
        "nombre": "Tandil",
        "slug": "tandil",
        "dias": [2],
        "roles": ["extra"],
        "tipo": "lugar",
    }
    rutas = [p for p in places.values() if p.extremos]
    assert [r.nombre for r in rutas] == ["Ruta Buenos Aires – Azul"]  # the other was merged
    assert rutas[0].extremos == ["buenos-aires", "azul"] and rutas[0].dias == [1, 2]
    assert "casa" not in places and "excursion" not in places


def test_parse_csv_matches_xlsx(xlsx, csv_file):
    a = [p.to_dict() for p in parse_itinerary(xlsx, CFG)]
    b = [p.to_dict() for p in parse_itinerary(csv_file, CFG)]
    assert a == b


def test_parse_without_config_keeps_raw_names(csv_file):
    names = [p.nombre for p in parse_itinerary(csv_file)]
    assert "Casa" in names and "Excursion" in names and "B. Blanca" in names


def test_missing_columns_fail_loud(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Tramo"):
        parse_itinerary(p)
