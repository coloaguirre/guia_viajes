"""CLI: uv run python -m guia <parse|geocode|prompts|validate|pack|all> [itinerary]."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from guia.geocode import geocode_places
from guia.itinerary import parse_itinerary
from guia.prompts import build_prompts
from guia.relatos import pack, validate_file

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PLACES = DATA / "lugares.json"
RELATOS = DATA / "relatos"
PROMPTS = DATA / "prompts"
BUNDLE = ROOT / "app" / "content" / "relatos.json"


def load_cfg() -> dict:
    return tomllib.loads((ROOT / "configs" / "viaje.toml").read_text(encoding="utf-8"))


def load_places() -> list[dict]:
    if not PLACES.exists():
        sys.exit(f"{PLACES} not found: run `parse <itinerary>` first")
    return json.loads(PLACES.read_text(encoding="utf-8"))


def save_places(places: list[dict]) -> None:
    PLACES.parent.mkdir(parents=True, exist_ok=True)
    PLACES.write_text(json.dumps(places, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_parse(args) -> None:
    places = [p.to_dict() for p in parse_itinerary(args.itinerary, load_cfg())]
    save_places(places)
    print(f"{len(places)} places -> {PLACES}")
    for p in places:
        print(f"  día {p['dias']}: {p['nombre']} [{p['tipo']}: {'/'.join(p['roles'])}]")


def cmd_geocode(args) -> None:
    cfg = load_cfg()
    v = cfg["viaje"]
    hint = ", ".join(x for x in (v.get("region"), v.get("pais")) if x)
    save_places(
        geocode_places(
            load_places(),
            DATA / "geocache.json",
            hint,
            queries=cfg.get("geo_query"),
            fixes=cfg.get("geo_fix"),
        )
    )
    print(f"geocoded -> {PLACES}")


def cmd_prompts(args) -> None:
    files = build_prompts(load_places(), load_cfg(), PROMPTS)
    print(f"{len(files)} prompts -> {PROMPTS}")


def cmd_validate(args) -> int:
    cfg = load_cfg()["relato"]
    files = sorted(RELATOS.glob("*.json"))
    errs = []
    for f in files:
        errs += validate_file(f, cfg["min_palabras"], cfg["max_palabras"])
    print(f"{len(files)} files checked, {len(errs)} problem(s)")
    for e in errs:
        print("  " + e)
    return 1 if errs else 0


def cmd_pack(args) -> None:
    if cmd_validate(args):
        sys.exit("fix validation problems before packing")
    pack(load_places(), RELATOS, BUNDLE, load_cfg()["viaje"]["nombre"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="guia")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("parse").add_argument("itinerary")
    sub.add_parser("geocode")
    sub.add_parser("prompts")
    sub.add_parser("validate")
    sub.add_parser("pack")
    a = sub.add_parser("all", help="parse + geocode + prompts")
    a.add_argument("itinerary")
    args = ap.parse_args(argv)
    if args.cmd == "all":
        cmd_parse(args)
        cmd_geocode(args)
        cmd_prompts(args)
        return 0
    return {
        "parse": cmd_parse,
        "geocode": cmd_geocode,
        "prompts": cmd_prompts,
        "validate": cmd_validate,
        "pack": cmd_pack,
    }[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
