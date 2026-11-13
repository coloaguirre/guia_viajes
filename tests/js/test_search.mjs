// Prueba de la búsqueda por voz con stubs mínimos del navegador.
// Correr: node tests/js/test_search.mjs
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import vm from "node:vm";

const data = JSON.parse(readFileSync(new URL("../../app/content/relatos.json", import.meta.url), "utf8"));
const el = () => ({ hidden: false, textContent: "", innerHTML: "", value: 0, classList: { add() {}, remove() {} }, querySelectorAll: () => [], set onclick(f) {} });
const ctx = {
  document: { getElementById: el },
  window: { speechSynthesis: { getVoices: () => [], cancel() {}, speak() {} } },
  navigator: {},
  fetch: async () => ({ json: async () => data }),
  prompt: () => null,
  console,
};
ctx.window.SpeechRecognition = undefined;
ctx.speechSynthesis = ctx.window.speechSynthesis;
vm.createContext(ctx);
vm.runInContext(readFileSync(new URL("../../app/app.js", import.meta.url), "utf8") + "\n;globalThis.__t = { state, search, sentences, norm };", ctx);
await new Promise((r) => setTimeout(r, 20)); // load() es async
const { state, search, sentences } = ctx.__t;
assert.equal(state.data.lugares.length, 2);

let r = search("Decime qué aves nidifican por acá");
assert.equal(r.results[0].id, "azul-aves-1", "aves -> relato de aves");
assert.equal(r.results.length, 1);

r = search("contame de la piedra movediza");
assert.equal(r.results[0].id, "tandil-piedra-0");

r = search("qué se come en Tandil");
assert.ok(r.named.length === 1 && r.named[0].slug === "tandil", "lugar nombrado");
assert.equal(r.results[0].id, "tandil-queso-1");

// "de dónde estamos" con lugar más cercano fijado: devuelve todo lo del lugar.
state.nearest = state.data.lugares[0];
r = search("Qué hay para contar de donde estamos?");
assert.ok(r.here);
assert.deepEqual(r.results.map((x) => x.lugar.slug), ["azul", "azul"]);

assert.equal(sentences("Hola. ¿Cómo va? Bien… y vos").length, 4);
console.log("search tests ok");
