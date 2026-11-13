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
- [ ] 3.1 Cargar el itinerario real y generar los relatos de todos los
      lugares (Claude Code ejecuta el pipeline).
- [ ] 3.2 Probar en el celular: voz, geo, offline. Ajustes.

## Pendiente de confirmar con el usuario
- Celular Android o iPhone (afecta reconocimiento de voz y voces TTS).
- Itinerario real (Excel) para arrancar la Fase 3.
- Dónde se sirve la app: GitHub Pages (HTTPS gratis) o solo local.
