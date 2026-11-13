/* Guía de viaje — app vanilla. Estado, navegación, reproductor, geo y voz. */
"use strict";

const $ = (id) => document.getElementById(id);
const state = { data: null, stack: [], pos: null, nearest: null, speaking: null, queue: [] };

// ---------- utilidades de texto ----------
const norm = (s) =>
  (s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9ñ\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
const STOP = new Set(
  "que hay para contar de donde estamos deci decime contame hablame sobre del la el los las un una unos unas por aca aqui ahora este esta lugar algo me podes queres quiero saber cual cuales como es son en y o a al lo le se su sus mas".split(" ")
);
const tokens = (s) => norm(s).split(" ").filter((t) => t.length >= 3 && !STOP.has(t));
// Sinónimos coloquiales -> palabra canónica que suele estar en tags/temas.
const SYN = {
  pajaro: "aves", pajaros: "aves", ave: "aves", nidifican: "aves", nidos: "aves",
  come: "comida", comer: "comida", comidas: "comida", comen: "comida", plato: "comida", platos: "comida", gastronomia: "comida", tomar: "bebidas", vino: "bebidas",
  bicho: "fauna", bichos: "fauna", animal: "fauna", animales: "fauna",
  planta: "flora", plantas: "flora", arbol: "flora", arboles: "flora", bosque: "flora",
  piedra: "geologia", piedras: "geologia", roca: "geologia", rocas: "geologia", cerro: "paisaje", montaña: "paisaje", sierra: "paisaje", sierras: "paisaje",
  paso: "historia", antes: "historia", antiguamente: "historia", fundo: "historia", fundaron: "historia",
  gente: "costumbres", viven: "costumbres", fiesta: "costumbres", fiestas: "costumbres", tradicion: "costumbres", tradiciones: "costumbres",
  ver: "que ver", visitar: "que ver", hacer: "que ver", recorrer: "que ver",
};
const expand = (ts) => [...new Set(ts.flatMap((t) => (SYN[t] ? [t, ...SYN[t].split(" ")] : [t])))];
// Coincidencia por prefijo común (>= 4 letras) para absorber plurales y derivados.
const hit = (q, k) => q === k || (q.length >= 4 && k.length >= 4 && (k.startsWith(q) || q.startsWith(k)));
const HERE = /\b(aca|aqui|donde estamos|donde estoy|este lugar|por aca|cerca)\b/;

// ---------- datos ----------
async function load() {
  const r = await fetch("content/relatos.json", { cache: "no-cache" }).catch(() => fetch("content/relatos.json"));
  state.data = await r.json();
  state.data.lugares.forEach((l) =>
    l.relatos.forEach((x) => {
      x.lugar = l;
      x.keys = [...new Set([...x.tags.flatMap(tokens), ...tokens(x.titulo), ...tokens(x.subtema), ...tokens(x.tema)])];
    })
  );
  $("title").textContent = state.data.viaje || "Guía de viaje";
  showPlaces();
  setStatus(`${state.data.lugares.length} lugares · generado ${state.data.generado}`);
}

// ---------- navegación ----------
function render(title, html, { back = true } = {}) {
  $("title").textContent = title;
  $("screen").innerHTML = html;
  $("back").hidden = !back;
}
function push(fn) { state.stack.push(fn); fn(); }
$("back").onclick = () => { state.stack.pop(); (state.stack[state.stack.length - 1] || showPlaces)(); };

function showPlaces() {
  state.stack = [showPlaces];
  const items = state.data.lugares
    .map((l) => {
      const near = state.nearest && state.nearest.slug === l.slug ? " near" : "";
      const dist = l.km != null ? ` · ${l.km.toFixed(0)} km` : "";
      return `<button class="item${near}" data-slug="${l.slug}">${l.nombre}<small>${l.relatos.length} relatos · día ${l.dias.join(", ")}${dist}</small></button>`;
    })
    .join("");
  render(state.data.viaje || "Guía de viaje", `<div class="hint">Elegí un lugar, o tocá el micrófono y pedilo.</div><div class="list">${items}</div>`, { back: false });
  $("screen").querySelectorAll("[data-slug]").forEach((b) => (b.onclick = () => push(() => showPlace(b.dataset.slug))));
}

function showPlace(slug) {
  const l = state.data.lugares.find((x) => x.slug === slug);
  const temas = [...new Set(l.relatos.map((r) => r.tema))];
  const items = temas
    .map((t) => `<button class="item" data-tema="${t}">${t}<small>${l.relatos.filter((r) => r.tema === t).length} relatos</small></button>`)
    .join("");
  render(l.nombre, `<div class="list">${items || "<div class='hint'>Todavía no hay relatos de este lugar.</div>"}</div>`);
  $("screen").querySelectorAll("[data-tema]").forEach((b) => (b.onclick = () => push(() => showTema(l, b.dataset.tema))));
}

function showTema(l, tema) {
  showList(`${l.nombre} · ${tema}`, l.relatos.filter((r) => r.tema === tema));
}

function showList(title, relatos) {
  const total = relatos.reduce((a, r) => a + r.minutos, 0);
  const items = relatos
    .map((r) => `<button class="item" data-id="${r.id}">${r.titulo}<small>${r.lugar.nombre} · ${r.subtema} · ${r.minutos} min</small></button>`)
    .join("");
  const all = relatos.length > 1 ? `<button class="item all" id="play-all">▶ Escuchar todos en orden<small>${relatos.length} relatos · ${Math.round(total)} min</small></button>` : "";
  render(title, `<div class="list">${all}${items}</div>`);
  $("screen").querySelectorAll("[data-id]").forEach((b) => (b.onclick = () => {
    const i = relatos.findIndex((r) => r.id === b.dataset.id);
    state.queue = relatos.slice(i + 1); // lo que sigue en la lista, para "siguiente"
    play(relatos[i]);
  }));
  const pa = $("play-all");
  if (pa) pa.onclick = () => { state.queue = relatos.slice(1); play(relatos[0]); };
}
const findRelato = (id) => state.data.lugares.flatMap((l) => l.relatos).find((r) => r.id === id);

// ---------- reproductor (speechSynthesis por frases) ----------
const synth = window.speechSynthesis;
let voice = null;
function pickVoice() {
  const vs = synth.getVoices();
  const pref = ["es-AR", "es-UY", "es-419", "es-US", "es-MX", "es-ES", "es"];
  for (const p of pref) {
    const v = vs.find((v) => v.lang.replace("_", "-").toLowerCase().startsWith(p.toLowerCase()) && !/eSpeak/i.test(v.name));
    if (v) return v;
  }
  return vs.find((v) => v.lang.startsWith("es")) || null;
}
synth.onvoiceschanged = () => (voice = pickVoice());

function sentences(text) {
  return text.replace(/\s+/g, " ").match(/[^.!?…]+[.!?…]+["»)]?|[^.!?…]+$/g).map((s) => s.trim()).filter(Boolean);
}

function play(relato) {
  stop();
  if (!voice) voice = pickVoice();
  const parts = sentences(relato.texto);
  const job = { relato, parts, i: 0, paused: false, canceled: false };
  state.speaking = job;
  $("player").hidden = false;
  $("player-title").textContent = relato.titulo;
  $("player-meta").textContent = `${relato.lugar.nombre} · ${relato.tema} · ${relato.subtema} · ${relato.minutos} min` + (voice ? ` · voz ${voice.name}` : " · sin voz en español") + (state.queue.length ? ` · quedan ${state.queue.length}` : "");
  $("p-next").disabled = !state.queue.length;
  $("p-toggle").textContent = "❚❚";
  speakNext(job);
}
function speakNext(job) {
  if (job.canceled) return;
  if (job.i >= job.parts.length) {
    $("p-progress").value = 1;
    $("p-toggle").textContent = "▶";
    if (state.queue.length) setTimeout(() => { if (state.speaking === job && !job.canceled) playNext(); }, 1200);
    return;
  }
  const u = new SpeechSynthesisUtterance(job.parts[job.i]);
  if (voice) u.voice = voice;
  u.lang = voice ? voice.lang : "es-AR";
  u.rate = 1.0;
  u.pitch = 1.0;
  u.onend = () => { job.i += 1; $("p-progress").value = job.i / job.parts.length; speakNext(job); };
  u.onerror = (e) => { if (e.error !== "interrupted" && e.error !== "canceled") { setStatus("Error de voz: " + e.error); } };
  synth.speak(u);
}
function stop() {
  if (state.speaking) state.speaking.canceled = true;
  synth.cancel();
}
function playNext() {
  const next = state.queue.shift();
  if (next) play(next);
}
$("p-next").onclick = playNext;
$("p-stop").onclick = () => { stop(); state.queue = []; $("player").hidden = true; };
$("p-restart").onclick = () => state.speaking && play(state.speaking.relato);
$("p-toggle").onclick = () => {
  const job = state.speaking;
  if (!job) return;
  if (job.i >= job.parts.length) return play(job.relato);
  // pause()/resume() es poco confiable en Android: cancelamos y retomamos en la frase actual.
  if (job.paused) { job.paused = false; job.canceled = false; $("p-toggle").textContent = "❚❚"; speakNext(job); }
  else { job.paused = true; job.canceled = true; synth.cancel(); $("p-toggle").textContent = "▶"; }
};

// ---------- geolocalización ----------
function haversine(a, b, c, d) {
  const R = 6371, t = Math.PI / 180;
  const x = Math.sin(((c - a) * t) / 2) ** 2 + Math.cos(a * t) * Math.cos(c * t) * Math.sin(((d - b) * t) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}
function locate() {
  return new Promise((res) => {
    if (!navigator.geolocation) return res(null);
    navigator.geolocation.getCurrentPosition(
      (p) => {
        state.pos = { lat: p.coords.latitude, lon: p.coords.longitude };
        let best = null;
        state.data.lugares.forEach((l) => {
          if (l.lat == null) return;
          l.km = haversine(state.pos.lat, state.pos.lon, l.lat, l.lon);
          if (!best || l.km < best.km) best = l;
        });
        state.nearest = best;
        setStatus(best ? `Estás cerca de ${best.nombre} (${best.km.toFixed(0)} km)` : "Sin lugares geolocalizados");
        res(best);
      },
      (e) => { setStatus("No pude ubicarte: " + e.message); res(null); },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
    );
  });
}
$("locate").onclick = async () => { await locate(); if (state.stack.length <= 1) showPlaces(); };

// ---------- búsqueda por texto / voz ----------
function search(query) {
  const q = norm(query);
  const here = HERE.test(q);
  const qs = expand(tokens(q));
  const all = state.data.lugares.flatMap((l) => l.relatos);
  // ¿Nombra un lugar explícitamente?
  const named = state.data.lugares.filter((l) => q.includes(norm(l.nombre)));
  let pool = named.length ? named.flatMap((l) => l.relatos) : all;
  if (!named.length && here && state.nearest) pool = state.nearest.relatos;
  const scored = pool
    .map((r) => {
      let s = qs.filter((t) => r.keys.some((k) => hit(t, k))).length;
      if (state.nearest && r.lugar === state.nearest) s += 0.5;
      return { r, s };
    })
    .filter((x) => x.s > 0 || qs.length === 0)
    .sort((a, b) => b.s - a.s);
  return { results: scored.map((x) => x.r), scored, here, named };
}

async function handleQuery(text) {
  setStatus(`Escuché: “${text}”`);
  if (HERE.test(norm(text)) && !state.nearest) await locate();
  const { results, scored } = search(text);
  if (!results.length) { say("No encontré ningún relato sobre eso."); return; }
  const top = scored[0].s, second = scored[1] ? scored[1].s : 0;
  if (results.length === 1 || (top >= 1 && top > second + 0.5)) {
    say(`Te cuento: ${results[0].titulo}.`, () => play(results[0]));
    return;
  }
  const shown = results.slice(0, 6);
  state.stack.push(() => showList("Elegí un relato", shown));
  showList("Elegí un relato", shown);
  say(`Encontré ${shown.length} relatos. Elegí uno en pantalla.`);
}

function say(text, done) {
  stop();
  if (!voice) voice = pickVoice();
  const u = new SpeechSynthesisUtterance(text);
  if (voice) u.voice = voice;
  u.lang = "es-AR";
  u.onend = () => done && done();
  u.onerror = () => done && done();
  synth.speak(u);
}

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
$("mic").onclick = () => {
  if (!SR) {
    const t = prompt("Este navegador no reconoce voz. Escribí lo que querés escuchar:");
    if (t) handleQuery(t);
    return;
  }
  stop();
  const rec = new SR();
  rec.lang = "es-AR";
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  $("mic").classList.add("listening");
  setStatus("Escuchando…");
  rec.onresult = (e) => handleQuery(e.results[0][0].transcript);
  rec.onerror = (e) => setStatus("No te escuché (" + e.error + ")");
  rec.onend = () => $("mic").classList.remove("listening");
  rec.start();
};

function setStatus(t) { $("status").textContent = t; }

// ---------- arranque ----------
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
load().catch((e) => setStatus("No pude cargar el contenido: " + e.message));
