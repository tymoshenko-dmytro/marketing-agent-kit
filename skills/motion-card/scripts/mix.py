#!/usr/bin/env python3
"""Lay voices and effects on a timeline and mix down.

    mix.py timeline.json out.wav [--duck fg_bus bg_bus]

timeline.json:
{
  "total": 5.114,
  "events": [
    {"file": "audio/lines/en1.wav", "at": 0.20, "gain": -10, "bus": "bg"},
    {"file": "audio/lines/es1.wav", "at": 0.70, "gain":   0, "bus": "fg"},
    {"file": "../sfx/lib/typing.wav", "at": 0.20, "gain": -15}
  ],
  "loudness": -16
}

`--duck fg bg` sidechain-compresses the bg bus keyed by the fg bus, which is how
voice-over and film dubbing are mixed: the background dips only
while the foreground is actually speaking. Setting the background quieter instead
leaves two voices competing - it is the duck that makes one of them the voice and
the other the room.

Events with no "bus" are mixed flat and are never ducked.
"""
import argparse, json, pathlib, subprocess, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline"); ap.add_argument("out")
    ap.add_argument("--duck", nargs=2, metavar=("FG","BG"))
    a = ap.parse_args()

    T = json.loads(pathlib.Path(a.timeline).read_text())
    total, ev = T["total"], T["events"]
    if not ev: sys.exit("no events")
    loud = T.get("loudness", -16)

    ins, filt, buses = [], [], {}
    for n, e in enumerate(ev):
        ins += ["-i", e["file"]]
        ms = int(round(e["at"] * 1000))
        filt.append(f"[{n}:a]volume={e.get('gain',0)}dB,adelay={ms}|{ms}[v{n}]")
        buses.setdefault(e.get("bus", "_flat"), []).append(f"[v{n}]")

    def bus(name):
        lbl = buses[name]
        tag = f"B{name}"
        filt.append("".join(lbl) + f"amix=inputs={len(lbl)}:normalize=0:dropout_transition=0,"
                    f"apad,atrim=0:{total}[{tag}]")
        return f"[{tag}]"

    parts = []
    if a.duck and all(b in buses for b in a.duck):
        fg, bg = bus(a.duck[0]), bus(a.duck[1])
        # the foreground keys the compressor on the background
        filt.append(f"{fg}asplit=2[FGmix][FGkey]")
        filt.append(f"{bg}[FGkey]sidechaincompress=threshold=0.015:ratio=20:attack=6:"
                    f"release=300:makeup=1[BGduck]")
        parts += ["[FGmix]", "[BGduck]"]
        rest = [k for k in buses if k not in a.duck]
    else:
        rest = list(buses)
    for k in rest:
        parts.append(bus(k))

    if len(parts) > 1:
        filt.append("".join(parts) + f"amix=inputs={len(parts)}:normalize=0:dropout_transition=0[m]")
        src = "[m]"
    else:
        src = parts[0]
    filt.append(f"{src}alimiter=limit=0.95,loudnorm=I={loud}:TP=-1.5:LRA=9,apad[out]")

    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",*ins,
        "-filter_complex",";".join(filt),"-map","[out]","-t",str(total),
        "-ar","48000","-ac","1",a.out,"-y"], check=True)
    print(f"  {a.out}  {total}s  {len(ev)} events, buses {sorted(buses)}"
          + (f", ducked {a.duck[1]} under {a.duck[0]}" if a.duck else ""))

    # report the balance, because a mix that reads right on paper can be inverted
    for label, x, y in [("first 25%", 0, total*0.25), ("middle", total*0.35, total*0.65)]:
        r = subprocess.run(["ffmpeg","-hide_banner","-ss",str(round(x,2)),"-t",str(round(y-x,2)),
            "-i",a.out,"-af","volumedetect","-f","null","-"],capture_output=True,text=True).stderr
        m = [l.split(":")[-1].strip() for l in r.splitlines() if "mean_volume" in l]
        if m: print(f"    {label}: {m[0]}")

main()
