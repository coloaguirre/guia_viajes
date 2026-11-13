"""Parse the trip itinerary (xlsx/csv) into a list of unique places."""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# Column aliases, normalized (lowercase, no accents, no spaces).
_COLS = {
    "dia": ("dia", "día", "day"),
    "fecha": ("fecha", "date"),
    "tramo": ("tramo/base", "tramo", "tramobase", "base", "recorrido"),
    "noche": ("nocheen", "noche", "pernocte", "alojamiento"),
}

# Separators between places inside a "Tramo / Base" cell.
_SPLIT = re.compile(r"\s*(?:–|—|→|->|>|/|\s-\s|,|;)\s*")
_PREFIX = re.compile(r"^(base|tramo|día de base|dia de base|descanso)\s*[:\-]?\s*", re.IGNORECASE)
_PAREN = re.compile(r"\s*\([^)]*\)")


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
    roles: set[str] = field(default_factory=set)  # "tramo" | "noche"

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "slug": self.slug,
            "dias": sorted(set(self.dias)),
            "roles": sorted(self.roles),
        }


def _find_col(headers: list[str], key: str) -> int | None:
    norm = [normalize(h).replace(" ", "") for h in headers]
    for alias in _COLS[key]:
        a = normalize(alias).replace(" ", "")
        for i, h in enumerate(norm):
            if h == a:
                return i
    return None


def split_places(cell: str | None) -> list[str]:
    """'Base: Bariloche (día libre)' -> ['Bariloche']; 'A – B' -> ['A', 'B']."""
    if cell is None:
        return []
    text = _PAREN.sub("", str(cell)).strip()
    text = _PREFIX.sub("", text)
    out = []
    for part in _SPLIT.split(text):
        part = _PREFIX.sub("", part.strip(" .-"))
        if part and normalize(part) not in ("", "-", "nan", "none"):
            out.append(part)
    return out


def _read_rows(path: Path) -> tuple[list[str], list[list]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        return rows[0], rows[1:]
    import openpyxl  # local import: keeps csv path dependency-free

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    # First row with at least two non-empty cells is the header.
    for i, r in enumerate(rows):
        if sum(1 for c in r if c not in (None, "")) >= 2:
            headers = ["" if c is None else str(c) for c in r]
            return headers, rows[i + 1 :]
    raise ValueError(f"{path}: no header row found")


def parse_itinerary(path: str | Path) -> list[Place]:
    """Return the unique places of the itinerary in order of first appearance."""
    path = Path(path)
    headers, rows = _read_rows(path)
    c_dia, c_tramo, c_noche = (_find_col(headers, k) for k in ("dia", "tramo", "noche"))
    if c_tramo is None and c_noche is None:
        raise ValueError(f"{path}: need a 'Tramo / Base' or 'Noche en' column, got {headers}")

    places: dict[str, Place] = {}
    row_n = 0
    for r in rows:
        if all(c in (None, "") for c in r):
            continue
        row_n += 1
        day = row_n
        if c_dia is not None and c_dia < len(r) and r[c_dia] not in (None, ""):
            try:
                day = int(float(r[c_dia]))
            except (TypeError, ValueError):
                pass
        for col, role in ((c_tramo, "tramo"), (c_noche, "noche")):
            if col is None or col >= len(r):
                continue
            for name in split_places(r[col]):
                key = normalize(name)
                p = places.setdefault(key, Place(nombre=name, slug=slugify(name)))
                if day not in p.dias:
                    p.dias.append(day)
                p.roles.add(role)
    if not places:
        raise ValueError(f"{path}: no places found in {row_n} rows")
    return list(places.values())
