"""Parse the trip itinerary (xlsx/csv) into places and road stretches (tramos)."""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# Column aliases, normalized (lowercase, no accents, no spaces).
_COLS = {
    "dia": ("dia", "día", "day"),
    "tramo": ("tramo/base", "tramo", "tramobase", "base", "recorrido"),
    "noche": ("nocheen", "noche", "pernocte"),
}

# Separators between places inside a "Tramo / Base" cell. " a " and " - " only
# when surrounded by spaces, so "Mar del Plata" or "Villa-Lugano" survive.
_SPLIT = re.compile(r"\s*(?:–|—|→|->|>|/|,|;|\s-\s|\sa\s)\s*")
_PREFIX = re.compile(r"^(base|tramo)\s*[:\-]?\s*", re.IGNORECASE)
_PAREN = re.compile(r"\s*\([^)]*\)")
_DEFAULT_IGNORE = {"", "-", "nan", "none", "dia completo", "día completo", "total viaje"}


def normalize(text: str) -> str:
    """Lowercase, strip accents and collapse whitespace. Used for keys and matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", plain).strip().lower()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(text)).strip("-")


@dataclass
class Place:
    nombre: str
    slug: str
    dias: list[int] = field(default_factory=list)
    roles: set[str] = field(default_factory=set)  # "tramo" | "noche" | "extra" | "ruta"
    extremos: list[str] | None = None  # for tramos: [slug_from, slug_to]

    def add(self, day: int, role: str) -> None:
        if day not in self.dias:
            self.dias.append(day)
        self.roles.add(role)

    def to_dict(self) -> dict:
        d = {
            "nombre": self.nombre,
            "slug": self.slug,
            "dias": sorted(self.dias),
            "roles": sorted(self.roles),
            "tipo": "tramo" if self.extremos else "lugar",
        }
        if self.extremos:
            d["extremos"] = self.extremos
        return d


class Canon:
    """Maps raw cell fragments to canonical names using config aliases/ignores."""

    def __init__(self, cfg: dict | None = None):
        cfg = cfg or {}
        self.alias = {normalize(k): v for k, v in cfg.get("alias", {}).items()}
        self.ignore = _DEFAULT_IGNORE | {normalize(x) for x in cfg.get("ignorar", [])}

    def __call__(self, raw: str) -> str | None:
        key = normalize(raw)
        if key in self.ignore:
            return None
        return self.alias.get(key, raw.strip())


def _find_col(headers: list[str], key: str) -> int | None:
    norm = [normalize(h).replace(" ", "") for h in headers]
    for alias in _COLS[key]:
        a = normalize(alias).replace(" ", "")
        for i, h in enumerate(norm):
            if h == a:
                return i
    return None


def split_places(cell: str | None, canon: Canon | None = None) -> list[str]:
    """'Base: Bahía Blanca (día libre)' -> ['Bahía Blanca']; 'A – B' -> ['A', 'B']."""
    canon = canon or Canon()
    if cell is None:
        return []
    text = _PAREN.sub("", str(cell)).strip()
    text = _PREFIX.sub("", text)
    out = []
    for part in _SPLIT.split(text):
        part = _PREFIX.sub("", part.strip(" .-"))
        name = canon(part) if part else None
        if name:
            out.append(name)
    return out


def _is_header(row: list) -> bool:
    cells = ["" if c is None else str(c) for c in row]
    return _find_col(cells, "tramo") is not None


def _read_rows(path: Path, sheet: str | None = None) -> tuple[list[str], list[list]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    else:
        import openpyxl  # local import: keeps csv path dependency-free

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheets = [wb[sheet]] if sheet else wb.worksheets
        rows = None
        for ws in sheets:
            cand = [list(r) for r in ws.iter_rows(values_only=True)]
            if any(_is_header(r) for r in cand):
                rows = cand
                break
        wb.close()
        if rows is None:
            raise ValueError(f"{path}: no sheet with a 'Tramo / Base' column (sheet={sheet!r})")
    for i, r in enumerate(rows):
        if _is_header(r):
            return ["" if c is None else str(c) for c in r], rows[i + 1 :]
    raise ValueError(f"{path}: no header row with 'Tramo / Base' found")


def parse_itinerary(path: str | Path, cfg: dict | None = None) -> list[Place]:
    """Return places (and road tramos) of the itinerary in order of first appearance.

    cfg: the [viaje]/[alias]/ignorar/[[extra]] sections of configs/viaje.toml (optional).
    """
    cfg = cfg or {}
    path = Path(path)
    headers, rows = _read_rows(path, cfg.get("viaje", {}).get("hoja") or None)
    c_dia, c_tramo, c_noche = (_find_col(headers, k) for k in ("dia", "tramo", "noche"))
    canon = Canon(cfg)

    places: dict[str, Place] = {}

    def get(name: str) -> Place:
        return places.setdefault(slugify(name), Place(nombre=name, slug=slugify(name)))

    row_n = 0
    for r in rows:
        if all(c in (None, "") for c in r):
            continue
        day = None
        if c_dia is not None and c_dia < len(r) and r[c_dia] not in (None, ""):
            try:
                day = int(float(r[c_dia]))
            except (TypeError, ValueError):
                day = None
        if day is None:
            if c_dia is not None:
                continue  # footer rows (totals, notes) have no day number
            row_n += 1
            day = row_n
        stops = split_places(r[c_tramo], canon) if c_tramo is not None and c_tramo < len(r) else []
        for name in stops:
            get(name).add(day, "tramo")
        if len(stops) >= 2:  # a driving day: one tramo entity from first to last stop
            a, b = stops[0], stops[-1]
            t = places.setdefault(
                f"ruta-{slugify(a)}-{slugify(b)}",
                Place(
                    nombre=f"Ruta {a} – {b}",
                    slug=f"ruta-{slugify(a)}-{slugify(b)}",
                    extremos=[slugify(a), slugify(b)],
                ),
            )
            t.add(day, "ruta")
        if c_noche is not None and c_noche < len(r):
            for name in split_places(r[c_noche], canon):
                get(name).add(day, "noche")

    for extra in cfg.get("extra", []):
        p = get(extra["nombre"])
        for d in extra.get("dias", []):
            p.add(int(d), "extra")
        if not extra.get("dias"):
            p.roles.add("extra")

    for src, dst in cfg.get("fusionar", {}).items():
        if src in places and dst in places:
            for d in places[src].dias:
                places[dst].add(d, "ruta")
            del places[src]

    if not places:
        raise ValueError(f"{path}: no places found")
    return list(places.values())
