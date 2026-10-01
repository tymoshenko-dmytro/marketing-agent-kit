#!/usr/bin/env python3
"""ElevenLabs speech, one file per line, trimmed and levelled.

    gen_voice.py lines.json out_dir [--gate] [--speed 1.12]

lines.json: [{"tag":"en1","voice":"<voice_id>","text":"..."}, ...]

Why per line rather than one long take: a bad line is re-cut for a fraction of a
cent, the gaps belong to the edit rather than the render, and the measured
durations become the picture's timing grid.

Why every line is levelled: two voices from different sources arrive at different
loudness, so a dB offset between buses in the mix would not mean what it says.

Key: env ELEVENLABS_API_KEY -> ~/.config/marketing-agent-kit/.env
"""
import argparse, difflib, json, os, pathlib, re, shutil, subprocess, sys, urllib.error, urllib.request

def key():
    """ELEVENLABS_API_KEY: env var first, then the kit's keys file (connections/elevenlabs-api.md)."""
    if os.environ.get("ELEVENLABS_API_KEY"): return os.environ["ELEVENLABS_API_KEY"]
    p = pathlib.Path(os.path.expanduser(os.environ.get("MARKETING_KIT_ENV", "~/.config/marketing-agent-kit/.env")))
    if p.exists():
        for line in p.read_text().splitlines():
            k, _, v = line.strip().partition("=")
            if k.strip() == "ELEVENLABS_API_KEY" and v.split(" #")[0].strip():
                return v.split(" #")[0].strip().strip('"').strip("'")
    sys.exit("ELEVENLABS_API_KEY not found: add it to ~/.config/marketing-agent-kit/.env "
             "(see connections/elevenlabs-api.md)")

def transcribe(wav, out):
    """Speech-to-text for the gate. mlx-whisper on Apple Silicon (fast, local), else
    openai-whisper. Install one: `pipx install mlx-whisper` or `pipx install openai-whisper`."""
    mlx = shutil.which("mlx_whisper") or str(pathlib.Path.home() / ".local/bin/mlx_whisper")
    if pathlib.Path(mlx).exists():
        cmd = [mlx, str(wav), "--model", "mlx-community/whisper-large-v3-turbo", "--output-dir", str(out),
               "--output-format", "txt", "--verbose", "False"]
    elif shutil.which("whisper"):
        cmd = ["whisper", str(wav), "--model", "turbo", "--output_dir", str(out), "--output_format", "txt"]
    else:
        sys.exit("--gate needs a Whisper CLI: `pipx install mlx-whisper` (Apple Silicon) or `pipx install openai-whisper`")
    subprocess.run(cmd, capture_output=True, check=True)

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",str(p)],capture_output=True,text=True).stdout.strip())

def strip_tags(t):
    """v3 audio tags steer delivery; they must not reach the gate as words."""
    out, d = [], 0
    for ch in t:
        if ch == "[": d += 1
        elif ch == "]": d = max(0, d - 1)
        elif d == 0: out.append(ch)
    return "".join(out).strip()

NUM = {"zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7",
       "eight":"8","nine":"9","ten":"10","twenty":"20","thirty":"30","forty":"40","fifty":"50",
       "sixty":"60","seventy":"70","eighty":"80","ninety":"90","hundred":"00","thousand":"000"}

def canon(t):
    """Whisper reliably rewrites correct audio three ways: numbers as digits,
    currency words as symbols, and no space at a sentence break. Normalise those
    and nothing else - a gate with false positives gets switched off."""
    t = t.lower().replace("’","'").replace("'","")
    t = re.sub(r"\$\s*([\d,.]+)", r"\1 dollars", t)
    t = re.sub(r"[^a-z0-9À-ɏ ]", " ", t)
    return "".join(NUM.get(w, w) for w in t.split())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines"); ap.add_argument("out")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--target", type=float, default=-18.0, help="per-line loudness, LUFS")
    ap.add_argument("--gate", action="store_true", help="transcribe and diff against the script")
    a = ap.parse_args()

    K = key()
    lines = json.loads(pathlib.Path(a.lines).read_text())
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    vs = {"stability": 0.5, "similarity_boost": 0.8}
    if a.speed: vs["speed"] = a.speed

    res, flagged = [], []
    for L in lines:
        mp3, wav = out / f"{L['tag']}.mp3", out / f"{L['tag']}.wav"
        if not mp3.exists():
            body = json.dumps({"text": L["text"], "model_id": a.model,
                               "voice_settings": vs}).encode()
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/text-to-speech/{L['voice']}"
                "?output_format=mp3_44100_128",
                data=body, headers={"xi-api-key": K, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r: mp3.write_bytes(r.read())
            except urllib.error.HTTPError as e:
                print(f"  {L['tag']} FAILED {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
                continue
        if not wav.exists():
            # trim the API's head and tail padding, then level - the padding would
            # otherwise show up as dead air between cuts
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-i",str(mp3),"-af",
                "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
                "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
                f"areverse,loudnorm=I={a.target}:TP=-3:LRA=7",
                "-ar","48000","-ac","1",str(wav),"-y"], check=True)
        d = dur(wav)
        row = {**L, "text": strip_tags(L["text"]), "dur": round(d, 3)}
        if a.gate:
            txt = wav.with_suffix(".txt")
            if not txt.exists():
                transcribe(wav, out)
            heard = txt.read_text().strip() if txt.exists() else ""
            r = difflib.SequenceMatcher(None, canon(row["text"]), canon(heard)).ratio()
            row["heard"], row["match"] = heard, round(r, 3)
            if r < 0.90: flagged.append((L["tag"], row["text"], heard, round(r, 2)))
        res.append(row)
        print(f"  {L['tag']:<6} {d:>5.2f}s  {row['text'][:62]}")

    (out.parent / "lines.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"\n{len(res)}/{len(lines)} lines, {sum(r['dur'] for r in res):.2f}s of speech")
    if flagged:
        print(f"\n{len(flagged)} line(s) differ from the script:")
        for t, w, h, r in flagged:
            print(f"  {t}: ordered {w!r}\n      heard   {h!r}  match={r}")
        sys.exit(1)
    if a.gate: print("gate passed: every line says what was ordered")

main()
