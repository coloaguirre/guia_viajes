# Brief de AMPLIACIÓN de los relatos de un lugar

El viajero pidió mucho más detalle: "somos un público muy educado,
académico y con necesidad de conocimiento; no nos afecta la
terminología científica ni la profundidad del texto; no es un relato
de cinco minutos por tema, son tantos como se requiera". Ejemplo que
dio: en Camarones la naturaleza merece relatos separados para cada
especie de pingüino, los mamíferos marinos, el pato vapor cabeza blanca
endémico y no volador, etcétera.

## Proceso
1. Leé `configs/estilo-relatos.md` (nueva versión, obligatoria),
   `data/prompts/<slug>.md` y el archivo EXISTENTE
   `data/relatos/<slug>.json`: conservá sus relatos (podés ampliarlos
   o corregirlos) y agregá los nuevos. No borres relatos salvo que lo
   reemplaces por dos más profundos.
2. INVESTIGÁ a fondo con búsquedas web y lectura de páginas: artículos
   científicos (Scielo, Hornero, Mastozoología Neotropical, Ameghiniana,
   Revista de la Asociación Geológica Argentina), fichas de especies
   (Aves Argentinas, eBird, Unión Internacional para la Conservación
   de la Naturaleza, SIB de Parques Nacionales), planes de manejo de
   áreas protegidas, Servicio Geológico Minero Argentino, historiografía
   (libros, tesis, Wikipedia como índice de fuentes, archivos de
   diarios). Si la cuota de búsquedas se agota, seguí con lecturas
   directas de páginas conocidas.
3. Diseñá el mapa de subtemas ANTES de escribir: listá todo lo que el
   lugar tiene para contar y asigná un relato (o dos) a cada subtema
   sustancioso. Orientación de cantidad total por entidad:
   - Pueblo, ciudad o parque principal: 15 a 25 relatos.
   - Reserva, isla, cabo, estancia, área natural: 8 a 15 relatos.
   - Ruta (entidad "Ruta A – B"): 8 a 12 relatos en orden geográfico,
     con kilómetros aproximados desde el origen.
   - Parada menor de ruta: 5 a 8 relatos.
   Esto es orientativo: si el lugar da para más, escribí más.
4. Para naturaleza, el estándar es un relato por grupo de especies con:
   taxonomía y parentesco, distribución y endemismos, morfología e
   identificación en el campo, dieta y comportamiento, reproducción y
   qué está pasando EXACTAMENTE a fines de noviembre y principios de
   diciembre (cortejo, puesta, incubación, pichones, muda, migración),
   amenazas y categoría de conservación, cifras de población con fuente
   y año, historia de su estudio (quién lo describió, investigaciones
   locales), y dónde y cómo verlo desde el lugar.
   Para historia: un relato por período o episodio, con fuentes
   primarias (diarios de viaje, decretos, censos), nombres, fechas y
   las controversias entre historiadores.
   Para geología: formaciones con nombre y edad, ambiente de depósito,
   fósiles, procesos (tectónica, glaciaciones, nivel del mar, vulcanismo),
   y cómo se lee eso en el paisaje que se ve desde el auto o el sendero.
   Para comida y costumbres: origen de cada producto y plato, técnica,
   economía local, fiestas con su historia, oficios.
5. Guardá `data/relatos/<slug>.json` (misma forma JSON) y corré
   `uv run python -m guia validate`. Corregí hasta que no reporte
   problemas de TU archivo. Límite: 700 a 1500 palabras por relato.
6. Reportá: cantidad final de relatos (antes/después), la lista de
   subtemas cubiertos, y los datos que no pudiste verificar.

## Reglas que no cambian
- Sin siglas, sin dígitos, sin listas ni títulos dentro del texto.
- Verdad por encima de todo; dudas explicitadas en el texto.
- Español rioplatense, voseo, oral.
