# PLAN — guia_viajes

Objetivo: tener la app funcionando en el celular con los relatos del
itinerario real en 2-3 días (meta: 2026-11-15/16).

## Decisiones
- PWA vanilla + contenido pregenerado (ver CLAUDE.md). Sin backend.
- Voz y TTS del dispositivo (Web Speech API). Si la voz es-AR del
  celular resulta mala, plan B: pregenerar mp3 con un TTS en la nube.
- Geocoding con Nominatim (OpenStreetMap), con cache en data/.
- Matching de comandos de voz por palabras clave + lugar más cercano.

## Fase 1 — Pipeline de contenido (src/guia)
- [x] 1.1 Parser de itinerario (xlsx/csv) → lista de lugares únicos
      (de "Tramo / Base" y "Noche en"), con el día en que se visitan.
- [x] 1.2 Geocoding de lugares → lat/lon, con cache JSON en data/.
- [x] 1.3 Esquema de relato + validador (duración, campos, tags).
- [x] 1.4 Generador de prompts por lugar (temas: historia, naturaleza,
      geología/paisaje, comida, costumbres, personajes, qué ver) y
      guía de estilo para redactar los relatos.
- [x] 1.5 Empaquetador: data/relatos/*.json → app/content/relatos.json.

## Fase 2 — App (app/)
- [x] 2.1 Menú lugares → temas → relatos; reproducción con
      speechSynthesis (pausa/continuar/detener, selección de voz es-AR).
- [x] 2.2 Geolocalización + lugar más cercano + "¿qué hay para contar
      de acá?".
- [x] 2.3 Comando de voz: reconocimiento, matching, lista de candidatos
      si hay varios, reproducción.
- [x] 2.4 PWA: manifest, service worker, instalación en el celular.

## Fase 3 — Contenido real y prueba en ruta
- [x] 3.1 Cargar el itinerario real (ampliado a profundidad académica el 2026-11-13: 580 relatos) y generar los relatos de todos los
      lugares (Claude Code ejecuta el pipeline).
- [ ] 3.2 Probar en el celular: voz, geo, offline. Ajustes.

## Decisiones de la Fase 3 (2026-11-13)
- Celular: Android (Chrome: reconocimiento de voz y voces es-AR de Google).
- Itinerario: hoja "Plan B" del Excel (la que tiene reservas). El Excel
  queda en `data/itinerario/` (gitignorado: tiene teléfonos y códigos).
- Publicación: GitHub Pages en https://coloaguirre.github.io/guia_viajes/
  desde la rama `gh-pages` (solo `app/`). Repo público porque el plan
  gratuito no permite Pages en privados; no contiene datos sensibles.
  Publicar con `scripts/deploy.sh`.
- Rutas de vuelta por la misma RN3 fusionadas con las de ida.
- Redacción: un agente por grupo geográfico, con investigación web y
  validación automática (`uv run python -m guia validate`).

- Día 17 (La Oriental → Comodoro): por ruta nacional 40 al norte (Bajo
  Caracoles, Perito Moreno, Río Mayo), ruta nacional 26 por Sarmiento,
  lagos Musters y Colhué Huapi y Bosque Petrificado José Ormachea.
  Confirmado por el usuario 2026-11-13.
- Día 10 (Piedrabuena → Gregores): camino directo por ruta nacional 288 y
  provincial 27 (valle del río Chico), 242 km. Confirmado 2026-11-13.
- Voz del audio: es-AR-ElenaNeural, velocidad -5 %. Confirmado 2026-11-13.
