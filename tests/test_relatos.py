import json

import pytest

from guia.relatos import pack, spoken_minutes, validate_file, validate_relato, word_count

GOOD_TEXT = " ".join(["palabra"] * 600)


def relato(**over):
    r = {
        "tema": "Historia",
        "subtema": "Fundación",
        "titulo": "Un pueblo nace",
        "texto": GOOD_TEXT,
        "tags": ["fundación", "colonos", "historia"],
    }
    r.update(over)
    return r


def test_word_count_and_minutes():
    assert word_count("hola  mundo\ncruel") == 3
    assert spoken_minutes(GOOD_TEXT, wpm=150) == 4.0


def test_valid_relato():
    assert validate_relato(relato(), 500, 780) == []


@pytest.mark.parametrize(
    "over, msg",
    [
        ({"texto": "corto"}, "too short"),
        ({"texto": " ".join(["x"] * 900)}, "too long"),
        ({"texto": GOOD_TEXT + "\n- item"}, "bullets"),
        ({"texto": GOOD_TEXT + "\n# Título"}, "heading"),
        ({"texto": GOOD_TEXT + " INTA"}, "acronym"),
        ({"tags": ["a"]}, "tags"),
        ({"titulo": ""}, "missing 'titulo'"),
    ],
)
def test_invalid_relato(over, msg):
    errs = validate_relato(relato(**over), 500, 780)
    assert any(msg in e for e in errs), errs


def test_validate_file_reports_index_and_title(tmp_path):
    f = tmp_path / "azul.json"
    f.write_text(json.dumps({"lugar": "Azul", "relatos": [relato(texto="x")]}), encoding="utf-8")
    errs = validate_file(f, 500, 780)
    assert len(errs) == 1 and "azul.json#0 (Un pueblo nace)" in errs[0]


def test_pack_builds_bundle_and_keeps_places_without_relatos(tmp_path, capsys):
    rel = tmp_path / "relatos"
    rel.mkdir()
    (rel / "azul.json").write_text(
        json.dumps({"lugar": "Azul", "relatos": [relato(tags=["Colonos", "fundación", "x"])]}),
        encoding="utf-8",
    )
    places = [
        {"slug": "azul", "nombre": "Azul", "dias": [1], "lat": -36.7, "lon": -59.8},
        {"slug": "tandil", "nombre": "Tandil", "dias": [2], "lat": None, "lon": None},
    ]
    out = tmp_path / "app" / "content" / "relatos.json"
    out.parent.mkdir(parents=True)
    sw = tmp_path / "app" / "sw.js"
    sw.write_text('const VERSION = "v1";\nconst X = 1;', encoding="utf-8")
    bundle = pack(places, rel, out, "Prueba")
    assert out.exists()
    assert sw.read_text(encoding="utf-8").startswith('const VERSION = "v2')
    assert "const X = 1;" in sw.read_text(encoding="utf-8")
    assert [p["slug"] for p in bundle["lugares"]] == ["azul", "tandil"]
    r = bundle["lugares"][0]["relatos"][0]
    assert r["id"] == "azul-fundacion-0"
    assert r["tags"] == ["colonos", "fundacion", "x"]
    assert r["minutos"] > 0
    assert bundle["lugares"][1]["relatos"] == []
    assert "without relatos: ['Tandil']" in capsys.readouterr().out


def test_pack_fails_on_orphan_relato_file(tmp_path):
    rel = tmp_path / "relatos"
    rel.mkdir()
    (rel / "marte.json").write_text(json.dumps({"lugar": "Marte", "relatos": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="marte"):
        pack([], rel, tmp_path / "out.json", "Prueba")


def test_order_places_by_day_and_route_position():
    from guia.relatos import order_places

    a = {"slug": "a", "nombre": "A", "dias": [1], "lat": 0.0, "lon": 0.0}
    b = {"slug": "b", "nombre": "B", "dias": [1, 2], "lat": 0.0, "lon": 2.0}
    ruta = {
        "slug": "ruta-a-b",
        "nombre": "Ruta",
        "dias": [1],
        "extremos": ["a", "b"],
        "lat": 0.0,
        "lon": 1.0,
    }
    mid = {"slug": "mid", "nombre": "Parada", "dias": [1], "lat": 0.0, "lon": 1.2}
    near = {"slug": "near", "nombre": "Cerca del origen", "dias": [1], "lat": 0.0, "lon": 0.3}
    side = {
        "slug": "side",
        "nombre": "Excursión antes de salir",
        "dias": [1],
        "lat": 0.0,
        "lon": -1.0,
    }
    c = {"slug": "c", "nombre": "C", "dias": [2], "lat": 0.0, "lon": 3.0}
    out = order_places([c, b, mid, side, a, ruta, near])
    assert [p["slug"] for p in out] == ["side", "a", "ruta-a-b", "near", "mid", "b", "c"]
