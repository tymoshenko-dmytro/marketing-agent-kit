#!/usr/bin/env python3
"""Name, store and catalogue a batch of finished ad videos.

    publish.py manifest.json [--config library.json] [--catalog catalog.csv]
                             [--stage dist] [--dry-run] [--bake-poster]
                             [--no-poster] [--no-contact] [--no-gallery]
                             [--no-sheet] [--no-sweep]

One call does what every video type needs and nobody should implement twice:

  1. give each file its canonical name           <type>_<topic>_<lang>_<aspect>_<voice>_<length>_<date>_v<N>.mp4
  2. pull a poster (strongest settled frame)     <name>.jpg   — optionally baked in as frame 0
  3. make a contact sheet for QA                 <name>.sheet.jpg
  4. store it: a local library folder, or a Google shared drive, under Month / Language / Type
  5. write the catalogue: CSV (source of truth) + optionally one Google Sheet tab per type
  6. write gallery.html — a review page with approve / reject / notes

The manifest is what a generating agent writes; see references/manifest.md.
Storage settings live in library.json; see references/storage.md.
Nothing here knows how a video was made — motion cards, cut footage and talking-head
renders all publish the same way.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import shutil
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import frames   # noqa: E402
import gallery  # noqa: E402

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
# folder name per language; override or extend with "langs" in library.json
LANGS = {"en": "EN 🇬🇧", "es": "ES 🇪🇸", "pt": "PT 🇧🇷", "de": "DE 🇩🇪", "fr": "FR 🇫🇷",
         "it": "IT 🇮🇹", "nl": "NL 🇳🇱", "pl": "PL 🇵🇱", "uk": "UK 🇺🇦", "tr": "TR 🇹🇷",
         "ja": "JA 🇯🇵", "ko": "KO 🇰🇷", "zh": "ZH 🇨🇳", "ar": "AR 🇸🇦", "hi": "HI 🇮🇳"}
CORE = ["id", "file", "created", "type", "topic", "lang", "aspect", "voice",
        "version", "duration_s", "status", "link", "poster", "notes"]
CONFIG_PATHS = [pathlib.Path("library.json"),
                pathlib.Path.home() / ".config" / "marketing-agent-kit" / "video-library.json"]


# ---------------------------------------------------------------- config ------
def load_config(path):
    for p in ([pathlib.Path(path)] if path else CONFIG_PATHS):
        if p.exists():
            cfg = json.loads(p.read_text(encoding="utf-8"))
            cfg["_path"] = str(p)
            break
    else:
        if path:
            sys.exit(f"  no config at {path}")
        cfg = {"storage": "local", "_path": "(defaults)"}
    cfg.setdefault("storage", "local")
    cfg.setdefault("local_root", "~/Ads Video Library")
    cfg["langs"] = {**LANGS, **cfg.get("langs", {})}
    if cfg["storage"] == "gdrive" and not cfg.get("drive_id"):
        sys.exit("  storage is gdrive but library.json has no drive_id — see references/setup.md")
    return cfg


# ---------------------------------------------------------------- naming ------
def canonical(item, mtype, lang):
    """Every field is parseable, so the catalogue can be rebuilt from a folder listing
    alone. The length in the name is why stale files must be retired on republish: a
    re-render that comes out a second shorter is a different name, and the old one
    would otherwise sit in the folder looking equally current."""
    return (f'{mtype}_{item["topic"]}_{lang}_{item["aspect"]}_{item["voice"]}_'
            f'{round(item["duration_s"])}s_{item["created"]}_v{item["version"]}.mp4')


def read_manifest(path):
    m = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for k in ("type", "label", "lang", "items"):
        if k not in m:
            sys.exit(f"  manifest is missing {k!r}")
    if "_" in m["type"]:
        sys.exit(f"  type {m['type']!r} contains an underscore — underscores separate name fields")
    base = pathlib.Path(path).parent
    today = date.today().isoformat()
    for it in m["items"]:
        for k in ("topic", "src", "voice"):
            if k not in it:
                sys.exit(f"  item {it.get('topic', '?')!r} is missing {k!r}")
        if "_" in it["topic"]:
            sys.exit(f"  topic {it['topic']!r} contains an underscore — use hyphens inside a field")
        it.setdefault("aspect", "16x9")
        it.setdefault("version", 1)
        it.setdefault("status", "review")
        it.setdefault("notes", "")
        it.setdefault("created", today)
        src = pathlib.Path(it["src"])
        it["src"] = src if src.is_absolute() else (base / src).resolve()
        if not it["src"].exists():
            sys.exit(f"  {it['topic']}: no file at {it['src']}")
    return m


def plan(m, old):
    """Every file's id, name and month, worked out before anything is touched.

    `created` comes from the catalogue for an id already in it: it is part of the
    name, so re-stamping it every run would store a second copy of a video that has
    not changed and leave the first one behind."""
    rows, seen_id, seen_name = [], {}, {}
    for it in m["items"]:
        it["duration_s"] = round(frames.duration(it["src"]), 2)
        cid = f'{m["type"]}_{it["topic"]}_{it["voice"]}'
        it["created"] = old.get(cid, {}).get("created") or it["created"]
        name = canonical(it, m["type"], m["lang"])
        # Two items answering to one id or one name is a silent overwrite: two renders
        # with the same basename, and the publisher picks whichever the filesystem
        # listed last. Refuse instead.
        if cid in seen_id:
            sys.exit(f"  two items share the id {cid!r}: {seen_id[cid]!r} and {it['topic']!r}")
        if name in seen_name:
            sys.exit(f"  two items produce the name {name!r}")
        seen_id[cid], seen_name[name] = it["topic"], it["topic"]
        rows.append({
            "id": cid, "file": name, "created": it["created"], "type": m["type"],
            "topic": it["topic"], "lang": m["lang"], "aspect": it["aspect"],
            "voice": it["voice"], "version": it["version"],
            "duration_s": it["duration_s"], "status": it["status"],
            "link": old.get(cid, {}).get("link", ""), "poster": old.get(cid, {}).get("poster", ""),
            "notes": it["notes"],
            **{k: it.get(k, "") for k in m.get("extras", [])},
            "_src": it["src"], "_poster_at": it.get("poster_at"),
            "_month": MONTHS[int(it["created"][5:7]) - 1],
        })
    return rows


# ----------------------------------------------------------------- stage ------
def stage(rows, st, mtype, poster=True, contact=True, bake=False):
    """Renamed copies + posters + contact sheets in one folder. Only this type's files
    are cleared from it, so one stage folder can hold several types."""
    st.mkdir(parents=True, exist_ok=True)
    for f in st.glob(f"{mtype}_*"):
        if f.suffix in (".mp4", ".jpg"):
            f.unlink()
    for r in rows:
        dst = st / r["file"]
        shutil.copy2(r["_src"], dst)
        stem = dst.with_suffix("")
        if poster:
            t = frames.poster(dst, f"{stem}.jpg", r["_poster_at"])
            print(f"    poster {t:>6.2f}s  {r['file']}")
            if bake:
                frames.bake(dst, f"{stem}.jpg")
        if contact:
            frames.sheet(dst, f"{stem}.sheet.jpg")


# ----------------------------------------------------------- local store ------
def store_local(cfg, rows, label, lang_folder, st, sweep=True):
    root = pathlib.Path(cfg["local_root"]).expanduser()
    for month in sorted({r["_month"] for r in rows}):
        folder = root / month / lang_folder / label
        folder.mkdir(parents=True, exist_ok=True)
        keep = set()
        for r in [r for r in rows if r["_month"] == month]:
            stem = pathlib.Path(r["file"]).stem
            for name in (r["file"], f"{stem}.jpg"):
                if (st / name).exists():
                    shutil.copy2(st / name, folder / name)
                    keep.add(name)
            r["link"] = str(folder / r["file"])
            r["poster"] = str(folder / f"{stem}.jpg") if f"{stem}.jpg" in keep else ""
            print(f"    stored   {folder.relative_to(root)}/{r['file']}")
        if sweep:
            # retire, don't delete: stale renders move to _retired/ inside the folder
            stale = [f for f in folder.iterdir() if f.is_file() and f.name not in keep
                     and f.suffix in (".mp4", ".jpg")]
            if stale:
                (folder / "_retired").mkdir(exist_ok=True)
                for f in stale:
                    f.replace(folder / "_retired" / f.name)
                print(f"    retired {len(stale)} stale file(s) → {month}/{lang_folder}/{label}/_retired/")


# ----------------------------------------------------------- gdrive store -----
def store_gdrive(cfg, rows, label, lang_folder, st, sweep=True):
    import requests
    from gauth import credentials, headers
    drive = cfg["drive_id"]
    # Every call against a shared drive needs these, the searches included. Without
    # them the API answers as though the drive does not exist.
    ALL = {"supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
    FILES = "https://www.googleapis.com/drive/v3/files"
    UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
    c, who = credentials(cfg.get("credentials"))
    print(f"  auth: {who['kind']} ({who['who']})")
    H = headers(c)

    def child(parent, name):
        r = requests.get(FILES, headers=H, timeout=30, params={
            "q": f"'{parent}' in parents and name = '{name}' and trashed = false",
            "fields": "files(id,name)", "corpora": "drive", "driveId": drive, **ALL})
        r.raise_for_status()
        f = r.json().get("files", [])
        return f[0] if f else None

    def ensure_folder(parent, name):
        got = child(parent, name)
        if got:
            return got["id"]
        r = requests.post(FILES, headers=H, timeout=30, params=ALL, json={
            "name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent]})
        r.raise_for_status()
        print(f"    created folder {name!r}")
        return r.json()["id"]

    def put(folder, path, mime):
        """Resumable upload straight from disk. Re-uploading a name that is already
        there replaces its content, so links already in the catalogue stay valid."""
        existing = child(folder, path.name)
        meta = {"name": path.name}
        if existing:
            url, method = f"{UPLOAD}/{existing['id']}", requests.patch
        else:
            url, method, meta["parents"] = UPLOAD, requests.post, [folder]
        r = method(url, headers=H, timeout=60, params={"uploadType": "resumable", **ALL}, json=meta)
        r.raise_for_status()
        data = path.read_bytes()
        r = requests.put(r.headers["Location"], timeout=600, data=data,
                         headers={"Content-Type": mime, "Content-Length": str(len(data))})
        r.raise_for_status()
        return f"https://drive.google.com/file/d/{r.json()['id']}/view", "replaced" if existing else "new"

    def trash_stale(folder, keep):
        r = requests.get(FILES, headers=H, timeout=30, params={
            "q": f"'{folder}' in parents and trashed = false", "fields": "files(id,name)",
            "pageSize": 1000, "corpora": "drive", "driveId": drive, **ALL})
        r.raise_for_status()
        n = 0
        for f in r.json().get("files", []):
            if f["name"] not in keep:
                requests.patch(f"{FILES}/{f['id']}", headers=H, timeout=30,
                               params={"supportsAllDrives": "true"}, json={"trashed": True})
                n += 1
        return n

    for month in sorted({r["_month"] for r in rows}):
        folder = ensure_folder(ensure_folder(ensure_folder(drive, month), lang_folder), label)
        keep = set()
        for r in [r for r in rows if r["_month"] == month]:
            r["link"], how = put(folder, st / r["file"], "video/mp4")
            keep.add(r["file"])
            jpg = st / f"{pathlib.Path(r['file']).stem}.jpg"
            if jpg.exists():
                r["poster"], _ = put(folder, jpg, "image/jpeg")
                keep.add(jpg.name)
            print(f"    {how:<8} {r['file']}")
        if sweep:
            n = trash_stale(folder, keep)
            if n:
                print(f"    moved {n} stale file(s) to the Drive trash")
    return H


def push_tab(H, sheet, tab, cols, rows):
    """A tab is overwritten wholesale from the CSV: the CSV is the source of truth."""
    import requests
    S = "https://sheets.googleapis.com/v4/spreadsheets"
    meta = requests.get(f"{S}/{sheet}", headers=H, timeout=30,
                        params={"fields": "sheets(properties(title))"})
    meta.raise_for_status()
    if tab not in {s["properties"]["title"] for s in meta.json()["sheets"]}:
        requests.post(f"{S}/{sheet}:batchUpdate", headers=H, timeout=30, json={
            "requests": [{"addSheet": {"properties": {"title": tab}}}]}).raise_for_status()
        print(f"    created tab {tab!r}")
    requests.post(f"{S}/{sheet}/values/{tab}:clear", headers=H, timeout=30, json={}).raise_for_status()
    body = [cols] + [[str(r.get(c, "")) for c in cols] for r in rows]
    requests.put(f"{S}/{sheet}/values/{tab}!A1", headers=H, timeout=60,
                 params={"valueInputOption": "RAW"}, json={"values": body}).raise_for_status()
    return len(rows), len(cols)


# ------------------------------------------------------------------ main ------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--config", help="library.json (default: ./library.json, then ~/.config/marketing-agent-kit/video-library.json)")
    ap.add_argument("--catalog", help="catalogue CSV — read for memory, rewritten after publishing")
    ap.add_argument("--stage", help="working folder for renamed files, posters, sheets, gallery (default: dist/ next to the manifest)")
    ap.add_argument("--dry-run", action="store_true", help="print names, folders and poster times; touch nothing")
    ap.add_argument("--bake-poster", action="store_true", help="replace frame 0 with the poster (re-encodes once)")
    ap.add_argument("--no-poster", action="store_true")
    ap.add_argument("--no-contact", action="store_true", help="skip contact sheets")
    ap.add_argument("--no-gallery", action="store_true")
    ap.add_argument("--no-sheet", action="store_true", help="don't write the Google Sheet tab")
    ap.add_argument("--no-sweep", action="store_true", help="leave files in the folder that aren't in this batch")
    a = ap.parse_args()

    cfg = load_config(a.config)
    m = read_manifest(a.manifest)
    cat = pathlib.Path(a.catalog) if a.catalog else None
    old = {r["id"]: r for r in csv.DictReader(cat.open(encoding="utf-8"))} if cat and cat.exists() else {}
    rows = plan(m, old)
    cols = CORE + [c for c in m.get("extras", []) if c not in CORE]
    label, tab = m["label"], m.get("tab", m["label"])
    lang_folder = cfg["langs"].get(m["lang"], m["lang"].upper())
    st = pathlib.Path(a.stage) if a.stage else pathlib.Path(a.manifest).parent / "dist"

    print(f'  {m["type"]}  {len(rows)} video(s)  →  {cfg["storage"]}: '
          f'{sorted({r["_month"] for r in rows})} / {lang_folder} / {label}   config: {cfg["_path"]}')
    if a.dry_run:
        for r in rows:
            at = r["_poster_at"] if r["_poster_at"] is not None else frames.pick(r["_src"])
            print(f'    {r["_month"]:<10} {r["file"]}   poster @ {at}s')
        return

    stage(rows, st, m["type"], poster=not a.no_poster, contact=not a.no_contact, bake=a.bake_poster)

    H = None
    if cfg["storage"] == "gdrive":
        H = store_gdrive(cfg, rows, label, lang_folder, st, sweep=not a.no_sweep)
    else:
        store_local(cfg, rows, label, lang_folder, st, sweep=not a.no_sweep)

    ordered = sorted(rows, key=lambda r: r["id"])
    if cat:
        with cat.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(ordered)
        print(f"  {cat}: {len(rows)} row(s)")

    if cfg.get("sheet_id") and not a.no_sheet:
        if H is None:
            from gauth import credentials, headers
            H = headers(credentials(cfg.get("credentials"))[0])
        n, k = push_tab(H, cfg["sheet_id"], tab, cols, ordered)
        print(f"  sheet tab {tab!r}: {n} rows × {k} columns")

    if not a.no_gallery:
        page = gallery.build([{c: r.get(c, "") for c in cols} for r in ordered],
                             st / "gallery.html", f"{label} · {m['lang']}", st)
        print(f"  review page: {page}")


if __name__ == "__main__":
    main()
