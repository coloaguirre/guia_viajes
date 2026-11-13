# guia_viajes — guía turística hablada para un viaje en ruta

Proyecto PERSONAL (no es de un cliente). Reglas globales de consultoría
que NO aplican acá: SQL, carpeta de credenciales, data contracts,
code-reviewer obligatorio, MR a dev, Gantt. Se mantiene: uv, ruff,
pytest, data/ gitignorado, conventional commits en inglés, español
para hablar con el usuario.

## Qué es
El usuario carga un itinerario (Excel con columnas Día, Fecha,
Tramo / Base, Kms, Hs, Noche en). Para cada lugar mencionado se
generan relatos de ≤5 minutos hablados (historia, naturaleza, comida,
costumbres...) organizados por tema y subtema. En el viaje, una app en
el celular los reproduce en voz rioplatense, elegidos desde un menú o
por comando de voz con geolocalización.

## Arquitectura (decisión 2026-11-13)
- **El contenido se genera ANTES del viaje**, no en runtime. La
  suscripción Pro no da API key; el LLM es Claude Code en esta sesión,
  que ejecuta el pipeline y escribe los relatos. En ruta la app
  funciona offline con el contenido empaquetado.
- **`src/guia/`**: pipeline Python (uv). Lee el itinerario, extrae
  lugares, geocodifica (Nominatim), arma los prompts de generación y
  valida/empaqueta los relatos a `app/content/relatos.json`.
- **`app/`**: PWA en HTML/JS vanilla, sin framework ni build. Se abre
  en el navegador del celular y se instala a la pantalla de inicio.
  Voz: Web Speech API (reconocimiento es-AR) y speechSynthesis con voz
  es-AR del dispositivo. Geo: navigator.geolocation. Service worker
  para offline.
- **`data/`**: el itinerario (`data/itinerario/`, con teléfonos y códigos)
  está gitignorado. `data/relatos/`, `data/lugares.json` y
  `data/geocache.json` SÍ se versionan. **`app/content/`** también: es
  el producto empaquetado.

## Convenciones
- Relato: 600-750 palabras (≈5 min a 130-150 ppm). Un test lo valida.
- Un relato = {lugar, tema, subtema, titulo, texto, tags}. El matching
  por voz es por palabras clave sobre tema/subtema/tags/título, sin LLM.
- Texto de los relatos en español rioplatense (voseo), escrito para ser
  escuchado: frases cortas, sin listas ni siglas.
- Correr: `uv run pytest`, `uv run ruff check src tests`.
- Probar la app: `uv run python -m http.server -d app 8000`. La voz y
  la geo exigen HTTPS o localhost; para el celular usar un túnel o
  GitHub Pages.
