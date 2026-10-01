#!/usr/bin/env python3
"""Stills from a finished video: the poster, the frame-0 bake, the contact sheet.

    frames.py poster   in.mp4 out.jpg [--at 3.2]
    frames.py bake     in.mp4 poster.jpg            # replaces frame 0 in place
    frames.py sheet    in.mp4 out.jpg [--cols 3 --rows 2]
    frames.py pick     in.mp4                       # print the chosen poster time

Needs ffmpeg and ffprobe on PATH. Python stdlib only.

Why a poster at all: almost every player and platform shows frame 0 as the idle
thumbnail, and frame 0 of an ad is usually a fade, a blank background or half-drawn
text. Slack, X and Discord regenerate thumbnails server-side and ignore cover-art
metadata, so the only reliable way to control that image everywhere is to make
frame 0 *be* the poster (`bake`). Platforms that accept a custom thumbnail upload
(Meta, TikTok, YouTube, the LinkedIn editor) get the .jpg itself.
The poster + frame-0 technique is adapted from /brag (github.com/latent-spaces/brag, MIT).
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

W, H, FPS = 32, 18, 5          # tiny grayscale frames are enough to judge motion


def need(tool: str) -> None:
    if not shutil.which(tool):
        sys.exit(f"{tool} not found on PATH — install FFmpeg (macOS: brew install ffmpeg)")


def duration(p) -> float:
    need("ffprobe")
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
    if not out:
        sys.exit(f"not a readable video: {p}")
    return float(out)


def tiny_frames(p) -> list[bytes]:
    need("ffmpeg")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf",
                          f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    n = W * H
    return [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]


def pick(p) -> float:
    """The strongest *settled* moment: text fully in, nothing mid-transition.

    Scores every sampled frame in the middle 70% of the video: low motion against its
    neighbours (settled) and high contrast (there is text or UI on screen). Blank,
    near-uniform frames — fades, empty backgrounds — are skipped whatever their colour,
    so dark-themed ads work too. Deterministic: the same render gets the same poster."""
    dur = duration(p)
    fr = tiny_frames(p)

    def std(f):
        m = sum(f) / len(f)
        return (sum((b - m) ** 2 for b in f) / len(f)) ** 0.5

    best_t, best_s = None, None
    for i in range(1, len(fr) - 1):
        t = i / FPS
        if t < dur * 0.15 or t > dur * 0.85:
            continue
        s = std(fr[i])
        if s < 3:                                       # blank frame: a fade or an empty background
            continue
        motion = (sum(abs(a - b) for a, b in zip(fr[i], fr[i - 1])) +
                  sum(abs(a - b) for a, b in zip(fr[i], fr[i + 1]))) / (2 * len(fr[i]))
        score = motion - 0.3 * s
        if best_s is None or score < best_s:
            best_t, best_s = t, score
    if best_t is None and fr:                           # nothing settled: take the busiest frame
        best_t = max(range(len(fr)), key=lambda i: std(fr[i])) / FPS
    return round(best_t if best_t is not None else dur * 0.5, 2)


def poster(p, out, at: float | None = None) -> float:
    t = pick(p) if at is None else at
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(p),
                    "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    return t


def bake(p, jpg) -> None:
    """Replace ONLY frame 0's pixels with the poster. Same duration, same frame count,
    audio copied through. At 30 fps the poster shows for 1/30 s — invisible on
    playback, but it is what every thumbnail grabber sees. Re-encodes the video
    stream once (crf 18)."""
    need("ffmpeg")
    p = pathlib.Path(p)
    tmp = p.with_suffix(".poster.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-i", str(jpg),
                    "-filter_complex", "[1:v][0:v]scale2ref[pv][base];[base][pv]overlay=0:0:enable='eq(n,0)'[v]",
                    "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)],
                   check=True)
    tmp.replace(p)


def sheet(p, out, cols: int = 3, rows: int = 2) -> None:
    """A contact sheet: cols×rows stills spread over the video. Lets a reviewer (or the
    agent) check every scene for overflow, collisions and low contrast without
    opening the file."""
    n = cols * rows
    dur = duration(p)
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(dur / (n * 2)), "-i", str(p), "-vf",
                    f"fps={n}/{dur:.3f},scale=480:-2,tile={cols}x{rows}:padding=6:margin=6",
                    "-frames:v", "1", "-q:v", "3", str(out)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("poster"); a1.add_argument("video"); a1.add_argument("out")
    a1.add_argument("--at", type=float, help="timestamp in seconds; default: auto-pick")
    a2 = sub.add_parser("bake"); a2.add_argument("video"); a2.add_argument("poster")
    a3 = sub.add_parser("sheet"); a3.add_argument("video"); a3.add_argument("out")
    a3.add_argument("--cols", type=int, default=3); a3.add_argument("--rows", type=int, default=2)
    a4 = sub.add_parser("pick"); a4.add_argument("video")
    a = ap.parse_args()
    if a.cmd == "poster":
        print(f"poster at {poster(a.video, a.out, a.at)}s → {a.out}")
    elif a.cmd == "bake":
        bake(a.video, a.poster); print(f"frame 0 of {a.video} is now the poster")
    elif a.cmd == "sheet":
        sheet(a.video, a.out, a.cols, a.rows); print(f"contact sheet → {a.out}")
    else:
        print(pick(a.video))


if __name__ == "__main__":
    main()
