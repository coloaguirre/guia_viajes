#!/usr/bin/env bash
# Empaqueta los relatos y publica app/ en la rama gh-pages (GitHub Pages).
# Uso: scripts/deploy.sh   (desde la raíz del repo, con el árbol limpio y commiteado)
set -euo pipefail
cd "$(dirname "$0")/.."
# Audio (repo aparte, GitHub Pages): sube lo nuevo si existe la carpeta.
AUDIO_DIR="$(cd "$(dirname "$0")/.." && uv run python -c "import tomllib;print(tomllib.load(open('configs/viaje.toml','rb'))['audio']['carpeta'])")"
if [ -d "$AUDIO_DIR/.git" ]; then
  (cd "$AUDIO_DIR" && git add -A && (git diff --cached --quiet || git commit -q -m "audio: update") && git push -q origin main && echo "audio publicado")
fi
uv run python -m guia pack
if ! git diff --quiet -- app; then
  git add app && git commit -m "chore: repack content" -q
fi
git push origin main
# gh-pages = solo el contenido de app/, como raíz del sitio.
git push origin "$(git subtree split --prefix app main 2>/dev/null | tail -1):refs/heads/gh-pages" --force
echo "publicado: https://$(git remote get-url origin | sed -E 's#.*github.com[:/]([^/]+)/([^/.]+).*#\1.github.io/\2#')/"
