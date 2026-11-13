"""Generate one Opus audio file per relato with a neural voice (edge-tts + ffmpeg).

Files are named by a hash of (voice, rate, text), so re-running only renders what
changed. The packer links each relato to its file through that same hash.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


def audio_key(text: str, voice: str, rate: str) -> str:
    return hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]


def iter_relatos(relatos_dir: Path):
    for f in sorted(relatos_dir.glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        for r in doc["relatos"]:
            yield f.stem, r


async def _render_one(text: str, voice: str, rate: str, out: Path, bitrate: str, sem) -> None:
    import edge_tts  # local import: optional dependency at runtime

    async with sem:
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = Path(tmp) / "a.mp3"
            await edge_tts.Communicate(text, voice, rate=rate).save(str(mp3))
            out.parent.mkdir(parents=True, exist_ok=True)
            proc = await asyncio.create_subprocess_exec(
                *[
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(mp3),
                    "-ac",
                    "1",
                    "-c:a",
                    "libopus",
                    "-b:a",
                    bitrate,
                    "-application",
                    "voip",
                    str(out),
                ]
            )
            if await proc.wait() != 0:
                raise RuntimeError(f"ffmpeg failed for {out}")


async def _render_all(jobs, voice, rate, bitrate, concurrency):
    sem = asyncio.Semaphore(concurrency)
    tasks = [_render_one(t, voice, rate, o, bitrate, sem) for t, o in jobs]
    for done, coro in enumerate(asyncio.as_completed(tasks), start=1):
        await coro
        if done % 10 == 0 or done == len(tasks):
            print(f"  {done}/{len(tasks)}")


def render(
    relatos_dir: Path,
    out_dir: Path,
    voice: str,
    rate: str,
    bitrate: str,
    concurrency: int = 4,
    only_slug: str | None = None,
) -> dict:
    """Render missing audio files. Returns {'rendered': n, 'skipped': n, 'files': n}."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found")
    jobs, skipped = [], 0
    for slug, r in iter_relatos(relatos_dir):
        if only_slug and slug != only_slug:
            continue
        out = out_dir / f"{audio_key(r['texto'], voice, rate)}.opus"
        if out.exists() and out.stat().st_size > 0:
            skipped += 1
        else:
            jobs.append((r["texto"], out))
    print(f"{len(jobs)} to render, {skipped} already done")
    if jobs:
        asyncio.run(_render_all(jobs, voice, rate, bitrate, concurrency))
    return {"rendered": len(jobs), "skipped": skipped, "files": len(list(out_dir.glob("*.opus")))}


def prune(relatos_dir: Path, out_dir: Path, voice: str, rate: str) -> int:
    """Delete audio files that no current relato references. Returns count removed."""
    keep = {audio_key(r["texto"], voice, rate) for _, r in iter_relatos(relatos_dir)}
    removed = 0
    for f in out_dir.glob("*.opus"):
        if f.stem not in keep:
            f.unlink()
            removed += 1
    return removed
