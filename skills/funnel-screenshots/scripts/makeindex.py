#!/usr/bin/env python3
"""Build INDEX.md for a captured funnel: one line per screenshot, with pixel size.

    python3 makeindex.py --out ~/example-quiz --title "Example — quiz_v1" \
        --notes "Female · 170 cm / 75 kg · goal 65 kg · email me@example.com"

Descriptions come from log.json (the heading of each screen). Paywall files produced
by paywall.py are labelled from their filename. Also flags anything that is not the
expected retina size so you can eyeball those files before shipping.
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def dims(path):
    try:
        if os.uname().sysname == "Darwin":
            o = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                               capture_output=True, text=True).stdout.split()
            return int(o[-3]), int(o[-1])
        o = subprocess.run(["identify", "-format", "%w %h", str(path)],
                           capture_output=True, text=True).stdout.split()
        return int(o[0]), int(o[1])
    except Exception:
        return 0, 0


PAYWALL_LABELS = [
    (re.compile(r"-paywall-discounted-(\d+)\.png$"), "Paywall after the discount, tile {0}"),
    (re.compile(r"-paywall-discounted-fullpage\.png$"), "Discounted paywall, whole page in one image"),
    (re.compile(r"-paywall-(\d+)\.png$"), "Paywall, tile {0}"),
    (re.compile(r"-paywall-fullpage\.png$"), "Paywall, whole page in one image"),
    (re.compile(r"-discount-modal\.png$"), "Discount / gift modal"),
    (re.compile(r"-plan-(\d+)-selected\.png$"), "Plan option {0} selected"),
    (re.compile(r"-payment-step\.png$"), "Payment step after the main CTA"),
    (re.compile(r"-card-form-empty-full\.png$"), "Empty card form, whole page"),
    (re.compile(r"-card-form-empty\.png$"), "Empty card form — capture stops here"),
]


def label_for(name):
    for rx, tpl in PAYWALL_LABELS:
        m = rx.search(name)
        if m:
            return tpl.format(*m.groups()) if m.groups() else tpl
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="funnel directory (the one holding shots/)")
    ap.add_argument("--title", default=None)
    ap.add_argument("--notes", default=None, help="one line about the answers used")
    ap.add_argument("--expect", default="1179x2556", help="expected retina size")
    a = ap.parse_args()

    base = Path(os.path.expanduser(a.out))
    shots = base / "shots"
    ew, eh = (int(x) for x in a.expect.split("x"))

    desc = {}
    log_f = base / "log.json"
    if log_f.exists():
        for e in json.loads(log_f.read_text()):
            if e.get("new") and e["file"] and e["file"] not in desc:
                head = (e["heads"][0] if e.get("heads") else e.get("text", "")[:60]).replace("\n", " ")
                step = e.get("url", "").split("?")[0].rstrip("/").split("/")[-1]
                desc[e["file"]] = f"{head} · /{step}" if step else head

    lines = [f"# {a.title or base.name}", ""]
    if a.notes:
        lines += [a.notes, ""]
    lines += [f"Mobile retina capture, expected {a.expect} px per screenshot.", ""]

    odd, n = [], 0
    for f in sorted(shots.glob("*.png")):
        n += 1
        w, h = dims(f)
        if (w, h) != (ew, eh):
            odd.append((f.name, w, h))
        key = f.name.replace("-scrolled.png", ".png")
        d = label_for(f.name) or desc.get(key) or re.sub(r"^\d+-", "", f.stem).replace("-", " ")
        if f.name.endswith("-scrolled.png"):
            d += " [rest of a list that scrolls inside its container]"
        lines.append(f"- `{f.name}` ({w}×{h}) — {d}")

    if odd:
        lines += ["", "## Not the standard size (full-page shots — check these by eye)", ""]
        lines += [f"- `{nm}` — {w}×{h}" for nm, w, h in odd]

    (base / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(f"{n} files indexed -> {base / 'INDEX.md'}")
    if odd:
        print(f"{len(odd)} non-standard sizes (expected for full-page captures):")
        for nm, w, h in odd:
            print(f"  {nm} {w}x{h}")


if __name__ == "__main__":
    main()
