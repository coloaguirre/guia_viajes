"""Geocode place names with Nominatim (OpenStreetMap), with a JSON cache."""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "guia_viajes/0.1 (personal travel guide)"


def _load(cache: Path) -> dict:
    return json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}


def lookup(name: str, hint: str, session: requests.Session | None = None) -> dict | None:
    """Return {'lat','lon','display'} or None. `hint` is e.g. 'Neuquén, Argentina'."""
    s = session or requests.Session()
    q = f"{name}, {hint}" if hint else name
    r = s.get(
        NOMINATIM,
        params={"q": q, "format": "json", "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    r.raise_for_status()
    hits = r.json()
    if not hits:
        return None
    h = hits[0]
    return {"lat": float(h["lat"]), "lon": float(h["lon"]), "display": h.get("display_name", "")}


def geocode_places(
    places: list[dict],
    cache_path: Path,
    hint: str,
    session: requests.Session | None = None,
    pause: float = 1.1,
) -> list[dict]:
    """Add lat/lon to each place dict (in place). Misses are kept with lat/lon None
    and reported, never dropped."""
    cache = _load(cache_path)
    s = session or requests.Session()
    misses = []
    for p in places:
        key = p["slug"]
        if key not in cache:
            cache[key] = lookup(p["nombre"], hint, s)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(pause)  # Nominatim usage policy: max 1 req/s
        hit = cache[key]
        p["lat"] = hit["lat"] if hit else None
        p["lon"] = hit["lon"] if hit else None
        p["geo_display"] = hit["display"] if hit else None
        if not hit:
            misses.append(p["nombre"])
    if misses:
        print(f"WARNING: {len(misses)} place(s) not geocoded: {misses}")
    return places
