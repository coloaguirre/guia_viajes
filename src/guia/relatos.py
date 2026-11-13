"""Relato schema, validation and packing into the app bundle."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

from guia.itinerary import normalize, slugify

REQUIRED = ("tema", "subtema", "titulo", "texto", "tags")
_BULLET = re.compile(r"^\s*([-*•]|\d+[.)])\s", re.MULTILINE)
_HEADING = re.compile(r"^\s*#", re.MULTILINE)
_ACRONYM = re.compile(r"\b[A-ZÁÉÍÓÚ]{3,}\b")


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def spoken_minutes(text: str, wpm: int = 140) -> float:
    return round(word_count(text) / wpm, 1)


def validate_relato(r: dict, min_words: int, max_words: int) -> list[str]:
    """Return a list of problems (empty = valid)."""
    errs = []
    for k in REQUIRED:
        if not r.get(k):
            errs.append(f"missing '{k}'")
    if errs:
        return errs
    n = word_count(r["texto"])
    if n < min_words:
        errs.append(f"too short: {n} words (< {min_words})")
    if n > max_words:
        errs.append(f"too long: {n} words (> {max_words})")
    if _BULLET.search(r["texto"]):
        errs.append("bullets/numbered list in texto (must be prose)")
    if _HEADING.search(r["texto"]):
        errs.append("markdown heading in texto")
    if _ACRONYM.search(r["texto"]):
        errs.append(f"acronym in texto: {_ACRONYM.search(r['texto']).group()}")
    if not isinstance(r["tags"], list) or len(r["tags"]) < 3:
        errs.append("tags must be a list of >= 3 keywords")
    return errs


def validate_file(path: Path, min_words: int, max_words: int) -> list[str]:
    """Validate one data/relatos/<slug>.json file: {'lugar':..., 'relatos':[...]}."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    errs = []
    if not doc.get("lugar") or not isinstance(doc.get("relatos"), list):
        return [f"{path.name}: expected {{'lugar': str, 'relatos': [...]}}"]
    if not doc["relatos"]:
        return [f"{path.name}: no relatos"]
    for i, r in enumerate(doc["relatos"]):
        for e in validate_relato(r, min_words, max_words):
            errs.append(f"{path.name}#{i} ({r.get('titulo', '?')}): {e}")
    return errs


def pack(places: list[dict], relatos_dir: Path, out: Path, nombre_viaje: str) -> dict:
    """Join geocoded places with their relatos into app/content/relatos.json.
    Places without relatos are kept (menu shows them empty) and counted."""
    by_slug = {p["slug"]: p for p in places}
    bundle_places = []
    without = []
    for p in places:
        f = relatos_dir / f"{p['slug']}.json"
        relatos = []
        if f.exists():
            doc = json.loads(f.read_text(encoding="utf-8"))
            for i, r in enumerate(doc["relatos"]):
                relatos.append(
                    {
                        "id": f"{p['slug']}-{slugify(r['subtema'])}-{i}",
                        "tema": r["tema"],
                        "subtema": r["subtema"],
                        "titulo": r["titulo"],
                        "texto": r["texto"],
                        "tags": sorted({normalize(t) for t in r["tags"]}),
                        "minutos": spoken_minutes(r["texto"]),
                    }
                )
        else:
            without.append(p["nombre"])
        bundle_places.append(
            {
                "slug": p["slug"],
                "nombre": p["nombre"],
                "dias": p.get("dias", []),
                "lat": p.get("lat"),
                "lon": p.get("lon"),
                "relatos": relatos,
            }
        )
    # Relato files for places not in the itinerary are an error, not silently dropped.
    orphans = [f.stem for f in relatos_dir.glob("*.json") if f.stem not in by_slug]
    if orphans:
        raise ValueError(f"relatos for places not in itinerary: {orphans}")
    bundle = {
        "viaje": nombre_viaje,
        "generado": date.today().isoformat(),
        "lugares": bundle_places,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, ensure_ascii=False, indent=1)
    out.write_text(payload, encoding="utf-8")
    bump_sw_version(out.parent.parent / "sw.js", payload)
    total = sum(len(p["relatos"]) for p in bundle_places)
    print(f"packed {total} relatos for {len(bundle_places)} places -> {out}")
    if without:
        print(f"WARNING: {len(without)} place(s) without relatos: {without}")
    return bundle


_SW_VERSION = re.compile(r'const VERSION = "[^"]*";')


def bump_sw_version(sw: Path, content: str) -> str | None:
    """Rewrite the service worker's VERSION with a content hash so phones refetch
    the bundle after a republish. Returns the new version, or None if sw.js is absent."""
    if not sw.exists():
        return None
    version = f"v{date.today():%Y%m%d}-{hashlib.sha1(content.encode()).hexdigest()[:8]}"
    sw.write_text(
        _SW_VERSION.sub(f'const VERSION = "{version}";', sw.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return version
