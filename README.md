# guia_viajes

Guía turística hablada para un viaje en auto. Los relatos se generan
antes del viaje y la app funciona sin señal.

App publicada: https://coloaguirre.github.io/guia_viajes/

## En el celular (Android, Chrome)
1. Abrir la URL en Chrome y aceptar los permisos de ubicación y micrófono.
2. Menú ⋮ → "Agregar a pantalla de inicio" (o "Instalar app").
3. Abrir una vez con señal para que se guarde todo; después anda offline.
4. Para pedir por voz: tocar el micrófono y hablar ("qué hay para contar
   de acá", "qué aves hay por acá", "contame de Puerto Deseado").
   Si el celular no tiene voz en español argentino: Ajustes → Sistema →
   Idiomas → Salida de texto a voz → Google → instalar "Español (Argentina)".

## Regenerar el contenido
```
uv run python -m guia all data/itinerario/<itinerario>.xlsx   # lugares, geocoding, prompts
# escribir data/relatos/<slug>.json (ver docs/notes/brief-redactor.md)
uv run python -m guia validate
scripts/deploy.sh                                              # pack + push + Pages
```

Ver `CLAUDE.md` (arquitectura) y `PLAN.md` (plan y decisiones).
