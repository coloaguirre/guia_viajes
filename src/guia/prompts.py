"""Build one generation prompt per place for Claude Code to write the relatos."""

from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = """# Relatos para: {nombre}

Lugar: **{nombre}** ({display}). Aparece el/los día(s) {dias} del viaje
"{viaje}", como {roles}.

Escribí los relatos de este lugar siguiendo al pie de la letra la guía
de estilo de `configs/estilo-relatos.md`. Temas a cubrir (omití los que
no tengan sustancia real para este lugar; podés agregar subtemas):

{temas}

Para cada tema, uno o más relatos, cada uno sobre UN subtema. Entre
{min_w} y {max_w} palabras cada uno. Si el lugar es un tramo de ruta
(no una ciudad), hablá del camino: paisajes, pueblos que se cruzan,
qué mirar por la ventanilla y en qué orden.

Guardá el resultado en `data/relatos/{slug}.json` con esta forma exacta:

```json
{{
  "lugar": "{nombre}",
  "relatos": [
    {{
      "tema": "Historia",
      "subtema": "Fundación y primeros colonos",
      "titulo": "Título corto y evocador",
      "texto": "Prosa continua, sin listas ni títulos...",
      "tags": ["fundación", "colonos", "siglo diecinueve"]
    }}
  ]
}}
```

Después validá con `uv run python -m guia validate`.
"""


def build_prompts(places: list[dict], cfg: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    temas = "\n".join(f"- {t}" for t in cfg["relato"]["temas"])
    for p in places:
        text = TEMPLATE.format(
            nombre=p["nombre"],
            display=p.get("geo_display") or "sin geocodificar",
            dias=", ".join(str(d) for d in p.get("dias", [])) or "?",
            viaje=cfg["viaje"]["nombre"],
            roles=" y ".join(p.get("roles", [])) or "lugar",
            temas=temas,
            min_w=cfg["relato"]["min_palabras"],
            max_w=cfg["relato"]["max_palabras"],
            slug=p["slug"],
        )
        f = out_dir / f"{p['slug']}.md"
        f.write_text(text, encoding="utf-8")
        written.append(f)
    (out_dir / "_lugares.json").write_text(
        json.dumps(places, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return written
