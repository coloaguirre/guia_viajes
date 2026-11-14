# Brief: ordenar los relatos dentro de cada archivo

Tarea de REORDENAMIENTO PURO: cambiar el orden del array `relatos` de
cada `data/relatos/<slug>.json`. PROHIBIDO modificar, resumir, corregir o
borrar cualquier campo (tema, subtema, titulo, texto, tags). Un chequeo
automático compara los textos antes y después; si algo cambió, el trabajo
se descarta.

## Criterio
- Archivos de RUTA (`ruta-*.json`): un único orden geográfico, el de cómo
  se los va encontrando manejando desde el origen hasta el destino, sin
  agrupar por tema. Primero la logística del día (nafta, horarios) si
  existe; después, cada relato en el kilómetro donde "pasa" (los relatos
  suelen mencionar kilómetros aproximados, pueblos o rasgos del camino: usá
  eso para ubicarlos). Los relatos que cubren toda la ruta (fauna de
  banquina, flora, viento, historia del trazado) van al principio, tras la
  logística, o donde mejor acompañen el tramo en que más se ven.
  Si un archivo tiene una "variante" de camino marcada, va al final.
- Archivos de LUGAR: agrupados por tema en este orden exacto:
  1. Historia — en orden CRONOLÓGICO de los hechos que narra cada relato
     (primero pueblos originarios y arqueología, luego exploradores del
     siglo dieciséis, etc., hasta la actualidad). Los relatos
     "panorámicos" que abarcan toda la historia van primero.
  2. Paisaje y geología — de lo más antiguo/general (basamento, formaciones)
     a lo más reciente/local (glaciaciones, costa actual, un rasgo puntual).
  3. Naturaleza y biología — panorama/ecosistema primero; luego grupos en
     este orden: pingüinos, otras aves marinas, aves playeras y acuáticas,
     aves de estepa y rapaces, mamíferos marinos, cetáceos, mamíferos
     terrestres, reptiles/anfibios/peces/insectos, intermareal e
     invertebrados, algas, flora, especies invasoras, conservación y manejo.
  4. Costumbres y gente.
  5. Comidas y bebidas.
  6. Qué ver y qué hacer — consejos prácticos al final.
  Ojo: el tema de cada relato NO se cambia; solo se ordena.

## Cómo hacerlo
Escribí un script Python que lea el JSON, construya la nueva lista a
partir de una lista explícita de índices (todos los índices, sin repetir
ni omitir), y guarde con `json.dump(..., ensure_ascii=False, indent=1)`.
Verificá con `uv run python -m guia validate` y con un chequeo propio de
que `sorted(r["texto"] for r in antes) == sorted(r["texto"] for r in
después)`. No hagas commits. Reportá por archivo: cantidad de relatos y
el orden final como lista de "índice viejo → título" resumida.
