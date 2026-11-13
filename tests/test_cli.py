import csv
import json

from guia import __main__ as cli


def test_cli_parse_and_prompts_end_to_end(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "DATA", tmp_path)
    monkeypatch.setattr(cli, "PLACES", tmp_path / "lugares.json")
    monkeypatch.setattr(cli, "PROMPTS", tmp_path / "prompts")
    it = tmp_path / "it.csv"
    with it.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(
            [["Día", "Tramo / Base", "Noche en"], [1, "Azul – Tandil", "Tandil"]]
        )
    assert cli.main(["parse", str(it)]) == 0
    places = json.loads((tmp_path / "lugares.json").read_text(encoding="utf-8"))
    assert [p["slug"] for p in places] == ["azul", "tandil"]

    assert cli.main(["prompts"]) == 0
    prompt = (tmp_path / "prompts" / "tandil.md").read_text(encoding="utf-8")
    assert "data/relatos/tandil.json" in prompt
    assert "Historia" in prompt
