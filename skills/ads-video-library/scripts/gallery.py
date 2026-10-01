#!/usr/bin/env python3
"""A review page for a batch of videos: gallery.html, one file, no dependencies.

    gallery.py catalog.csv --out dist/gallery.html [--media dist] [--title "Motion Cards"]

Every video is a card: poster, play on click, the canonical name, the catalogue
fields, the contact sheet, and three buttons — approve, reject, note. "Copy review"
puts the verdicts on the clipboard as plain text, ready to paste back to the agent,
which updates `status` in the catalogue and republishes. Verdicts are remembered in
the reviewer's browser between visits.

publish.py writes this page automatically; run it by hand to rebuild the page from
an existing catalogue.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import pathlib
from datetime import date

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — review</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#14171c;--muted:#4a5260;--line:#dfe3ea;--accent:#2457d6;--ok:#167a3e;--bad:#b42318;--chip:#eef1f6;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1115;--card:#171a21;--ink:#e9ecf1;--muted:#a9b1bf;--line:#2a2f3a;--accent:#7aa2ff;--ok:#4cc27a;--bad:#ff7a6e;--chip:#222733;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 16px}
h1{font-size:18px;margin:0 0 8px}.sub{color:var(--muted);font-size:13px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.chip{border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:999px;padding:4px 10px;font-size:13px;cursor:pointer}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
input[type=search]{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:6px 10px;min-width:180px;flex:1;max-width:320px}
button.main{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:7px 12px;font-weight:600;cursor:pointer}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:16px;max-width:1500px;margin:0 auto}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.card.approved{outline:2px solid var(--ok)}.card.rejected{outline:2px solid var(--bad)}
video{width:100%;display:block;background:#000;max-height:420px}
.body{padding:12px;display:flex;flex-direction:column;gap:8px}
.file{font:12px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace;word-break:break-all;color:var(--muted)}
dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:0;font-size:13px}dt{color:var(--muted)}dd{margin:0;word-break:break-word}
.acts{display:flex;gap:6px;flex-wrap:wrap}.acts button{border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:8px;padding:5px 10px;cursor:pointer;font-size:13px}
.acts button.on.ok{background:var(--ok);color:#fff;border-color:var(--ok)}.acts button.on.bad{background:var(--bad);color:#fff;border-color:var(--bad)}
textarea{width:100%;min-height:54px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);padding:6px;font:inherit;font-size:13px}
a{color:var(--accent)}.sheet img{width:100%;border-radius:6px;border:1px solid var(--line)}
.toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:8px 14px;border-radius:8px;opacity:0;transition:opacity .2s}.toast.show{opacity:1}
</style></head><body>
<header>
  <h1>__TITLE__</h1>
  <div class="sub" id="count"></div>
  <div class="bar" id="filters"></div>
  <div class="bar"><input type="search" id="q" placeholder="Search name, topic, copy…"><button class="main" id="copy">Copy review</button></div>
</header>
<main id="grid"></main>
<div class="toast" id="toast">Copied — paste it to the agent</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const rows = JSON.parse(document.getElementById('data').textContent);
const KEY = 'review:' + __KEY__;
let state = {}; try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const CORE = new Set(['id','file','created','type','topic','lang','aspect','voice','version','duration_s','status','link','poster','notes','_video','_poster','_sheet']);
const facets = ['lang','aspect','voice','status'];
const active = {}; facets.forEach(f => active[f] = null);
const el = (t, a = {}, ...kids) => { const n = document.createElement(t); for (const [k, v] of Object.entries(a)) { if (k === 'class') n.className = v; else if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v); } kids.forEach(k => n.append(k)); return n; };
function filters() {
  const box = document.getElementById('filters'); box.innerHTML = '';
  facets.forEach(f => { const vals = [...new Set(rows.map(r => r[f]).filter(Boolean))]; if (vals.length < 2) return;
    vals.forEach(v => { const b = el('button', {class: 'chip', 'aria-pressed': String(active[f] === v), onclick: () => { active[f] = active[f] === v ? null : v; filters(); render(); }}, f + ': ' + v); box.append(b); }); });
}
function card(r) {
  const s = state[r.id] || {};
  const c = el('article', {class: 'card ' + (s.v || '')});
  const v = el('video', {controls: '', preload: 'none', playsinline: ''}); if (r._poster) v.poster = r._poster; if (r._video) v.src = r._video;
  c.append(v);
  const b = el('div', {class: 'body'});
  b.append(el('div', {class: 'file'}, r.file));
  const dl = el('dl');
  const add = (k, val) => { if (val !== undefined && val !== '') { dl.append(el('dt', {}, k), el('dd', {}, String(val))); } };
  add('id', r.id); add('length', r.duration_s ? r.duration_s + ' s' : ''); add('voice', r.voice); add('status', r.status);
  Object.keys(r).filter(k => !CORE.has(k)).forEach(k => add(k, r[k])); add('notes', r.notes);
  b.append(dl);
  if (r.link) b.append(el('a', {href: r.link, target: '_blank', rel: 'noopener'}, 'Open in library ↗'));
  if (r._sheet) { const d = el('details', {class: 'sheet'}, el('summary', {}, 'Contact sheet')); d.append(el('img', {src: r._sheet, alt: 'Contact sheet of ' + r.file, loading: 'lazy'})); b.append(d); }
  const note = el('textarea', {placeholder: 'Note for the agent (optional)'}); note.value = s.n || '';
  note.addEventListener('input', () => { state[r.id] = {...(state[r.id] || {}), n: note.value}; save(); });
  const mk = (label, val, cls) => el('button', {class: cls + (s.v === val ? ' on' : ''), onclick: () => { const cur = (state[r.id] || {}).v; state[r.id] = {...(state[r.id] || {}), v: cur === val ? '' : val}; save(); render(); }}, label);
  b.append(el('div', {class: 'acts'}, mk('✓ Approve', 'approved', 'ok'), mk('✕ Reject', 'rejected', 'bad')), note);
  c.append(b); return c;
}
function visible() { const q = document.getElementById('q').value.toLowerCase();
  return rows.filter(r => facets.every(f => !active[f] || r[f] === active[f]) && (!q || JSON.stringify(r).toLowerCase().includes(q))); }
function render() { const g = document.getElementById('grid'); g.innerHTML = ''; const vs = visible(); vs.forEach(r => g.append(card(r)));
  const done = rows.filter(r => (state[r.id] || {}).v).length;
  document.getElementById('count').textContent = `${vs.length} of ${rows.length} videos · ${done} reviewed · __DATE__`; }
document.getElementById('q').addEventListener('input', render);
document.getElementById('copy').addEventListener('click', async () => {
  const lines = ['Review — ' + __KEY__];
  rows.forEach(r => { const s = state[r.id] || {}; if (!s.v && !s.n) return;
    lines.push(`${s.v === 'approved' ? '✓' : s.v === 'rejected' ? '✕' : '•'} ${r.id} (${r.file}) — ${s.v || 'note'}${s.n ? ': ' + s.n.trim() : ''}`); });
  if (lines.length === 1) lines.push('(nothing reviewed yet)');
  const text = lines.join('\\n');
  try { await navigator.clipboard.writeText(text); } catch (e) { const t = el('textarea'); t.value = text; document.body.append(t); t.select(); document.execCommand('copy'); t.remove(); }
  const toast = document.getElementById('toast'); toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 1600);
});
filters(); render();
</script></body></html>
"""


def rel(target, base_dir) -> str:
    return os.path.relpath(target, base_dir).replace(os.sep, "/")


def build(rows: list[dict], out, title: str, media_dir=None) -> pathlib.Path:
    """rows: catalogue rows. media_dir: where <file>, <stem>.jpg and <stem>.sheet.jpg live."""
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    media = pathlib.Path(media_dir) if media_dir else out.parent
    items = []
    for r in rows:
        r = {k: v for k, v in r.items() if not k.startswith("_")}
        # local library: show links relative to the page so they open from disk
        for k in ("link", "poster"):
            if r.get(k, "").startswith("/") and pathlib.Path(r[k]).exists():
                r[k] = rel(r[k], out.parent)
        stem = pathlib.Path(r.get("file", "")).stem
        for key, name in (("_video", r.get("file", "")), ("_poster", f"{stem}.jpg"),
                          ("_sheet", f"{stem}.sheet.jpg")):
            if name and (media / name).exists():
                r[key] = rel(media / name, out.parent)
        items.append(r)
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE.replace("__TITLE__", html.escape(title))
                .replace("__KEY__", json.dumps(title))
                .replace("__DATE__", date.today().isoformat())
                .replace("__DATA__", data))
    out.write_text(page, encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("catalog", help="catalogue CSV written by publish.py")
    ap.add_argument("--out", default="gallery.html")
    ap.add_argument("--media", help="folder with the videos, posters and contact sheets")
    ap.add_argument("--title", default="Video review")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.catalog, encoding="utf-8")))
    print(f"gallery → {build(rows, a.out, a.title, a.media)}  ({len(rows)} videos)")


if __name__ == "__main__":
    main()
