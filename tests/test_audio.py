import json

from guia.audio import audio_key, prune
from guia.relatos import pack


def test_audio_key_depends_on_voice_rate_and_text():
    a = audio_key("hola", "v1", "+0%")
    assert a == audio_key("hola", "v1", "+0%")
    assert a != audio_key("hola", "v2", "+0%") != audio_key("hola", "v1", "-5%")
    assert len(a) == 16


def test_pack_links_existing_audio_and_prune_removes_orphans(tmp_path):
    rel = tmp_path / "relatos"
    rel.mkdir()
    text = " ".join(["palabra"] * 600)
    (rel / "azul.json").write_text(
        json.dumps(
            {
                "lugar": "Azul",
                "relatos": [
                    {
                        "tema": "T",
                        "subtema": "S",
                        "titulo": "A",
                        "texto": text,
                        "tags": ["a", "b", "c"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    key = audio_key(text, "voz", "-5%")
    (audio_dir / f"{key}.opus").write_bytes(b"x")
    (audio_dir / "orphan.opus").write_bytes(b"x")
    out = tmp_path / "app" / "content" / "relatos.json"
    bundle = pack(
        [{"slug": "azul", "nombre": "Azul", "dias": [1]}],
        rel,
        out,
        "P",
        audio={"dir": audio_dir, "voice": "voz", "rate": "-5%", "base_url": "https://x/"},
    )
    assert bundle["audio_base"] == "https://x/"
    assert bundle["lugares"][0]["relatos"][0]["audio"] == f"{key}.opus"
    assert prune(rel, audio_dir, "voz", "-5%") == 1
    assert sorted(f.name for f in audio_dir.glob("*.opus")) == [f"{key}.opus"]
