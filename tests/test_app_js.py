"""Runs the node-based test of the app's voice search against app/content/relatos.json."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_app_search_logic() -> None:
    for f in ("app/app.js", "app/sw.js"):
        subprocess.run(["node", "--check", str(ROOT / f)], check=True)
    r = subprocess.run(
        ["node", str(ROOT / "tests" / "js" / "test_search.mjs")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
