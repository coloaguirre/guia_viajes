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

## Audio
Los relatos se escuchan como archivos Opus con voz neural rioplatense
(generados con `edge-tts` y `ffmpeg`), lo que permite seguir escuchando con
la pantalla apagada o con otra app al frente, con controles en la
notificación. Si un relato no tiene audio, la app usa la voz del celular.
Antes de salir de viaje: en cada lugar, tocar "Guardar audio para usar sin
señal". Voz y velocidad se eligen en `configs/viaje.toml`, sección `[audio]`.
```
uv run python -m guia audio --jobs 3      # renderiza lo que falte en ../guia_viajes_audio
uv run python -m guia audio --prune       # además borra audio de relatos eliminados
```
El audio se publica en https://coloaguirre.github.io/guia_viajes_audio/ (repo aparte).

## Regenerar el contenido
```
uv run python -m guia all data/itinerario/<itinerario>.xlsx   # lugares, geocoding, prompts
# escribir data/relatos/<slug>.json (ver docs/notes/brief-redactor.md)
uv run python -m guia validate
uv run python -m guia audio
scripts/deploy.sh                                              # audio + pack + push + Pages
```

Ver `CLAUDE.md` (arquitectura) y `PLAN.md` (plan y decisiones).
