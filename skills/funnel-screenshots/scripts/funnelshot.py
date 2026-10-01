#!/usr/bin/env python3
"""Walk a marketing quiz / onboarding funnel and screenshot every screen at retina resolution.

    python3 funnelshot.py --url https://example.com/quiz --out ~/example-quiz

Writes into --out:
    shots/NN-slug.png     one file per unique screen (plus NN-slug-scrolled.png
                          when a screen's option list scrolls inside a container)
    log.json              every iteration: url, headings, clickables, inputs
    state.json            cookies + localStorage, for --resume
    last_url.txt          where the run ended, for --resume and paywall.py
    .gitignore            keeps the three files above out of git (they can hold
                          session cookies and the typed email)

It answers questions with the first plausible option, fills numeric inputs from
--height/--weight/--goal/--age, and stops when a real payment form appears.
It never types payment data and never clicks a pay button.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import browser as B  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# Never click these: navigation chrome, language switchers, unit toggles, legal links,
# and — most importantly — anything that would actually take money.
SKIP = re.compile(
    r"(^back$|^en$|^english|^\(en\)$|select your language|privacy|terms|log ?in|sign ?in"
    r"|cookie|policy|refund|contact|about us|\bmenu\b|faq|@|restore"
    r"|^cm$|^ft$|^in$|^kg$|^lb$|^lbs$|^ft in$|^cm in$"
    r"|apple pay|google pay|paypal|pay now|pay \$|buy now|place order|complete purchase"
    r"|continue securely|card number|add card|credit card)", re.I)

# Anything that advances the screen. Funnels are creative here: "Save my preferences",
# "Let's finish this", "All done!", "Grab my plan" are all real CTAs seen in the wild.
CONT = re.compile(
    r"(continue|next|proceed|get (my|started)|^start|submit|let'?s|got it|i'?m ready|sounds good"
    r"|save my|apply|show my|see my|finish|all done|build my|claim my|grab my|^done$|^ok$)", re.I)

UNITS_METRIC = re.compile(r"cm\s*/\s*kg|metric", re.I)

DESCRIBE = """() => {
  const vis = el => {
    const r = el.getBoundingClientRect(), st = getComputedStyle(el);
    return r.width > 20 && r.height > 14 && st.visibility !== 'hidden'
           && st.display !== 'none' && +st.opacity > 0.05;
  };
  document.querySelectorAll('[data-wk]').forEach(e => e.removeAttribute('data-wk'));
  const cands = [];
  for (const el of [...document.querySelectorAll('body *')].filter(vis)) {
    const st = getComputedStyle(el), tag = el.tagName.toLowerCase();
    const clickable = tag === 'button' || tag === 'a' || tag === 'label' || tag === 'select'
      || el.getAttribute('role') === 'button' || st.cursor === 'pointer' || el.hasAttribute('onclick');
    if (!clickable) continue;
    const txt = (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
    if (!txt) continue;
    const r = el.getBoundingClientRect();
    cands.push({ el, tag, txt: txt.slice(0, 80), y: r.top + scrollY, x: r.left, w: r.width, h: r.height });
  }
  // keep the innermost clickable of each nest, so we click the option and not its wrapper
  const keep = cands.filter(c => !cands.some(o => o.el !== c.el && c.el.contains(o.el)));
  keep.sort((a, b) => a.y - b.y || a.x - b.x);
  keep.forEach((c, i) => c.el.setAttribute('data-wk', String(i)));
  const heads = [...document.querySelectorAll('h1,h2,h3')].filter(vis)
    .map(e => e.innerText.trim()).filter(Boolean);
  const inputs = [...document.querySelectorAll(
      'input:not([type=radio]):not([type=checkbox]):not([type=hidden]):not([type=submit]), textarea')]
    .filter(vis).map((e, i) => { e.setAttribute('data-wki', String(i));
      return { i, type: e.type || '', name: e.name || '', ph: e.placeholder || '', val: e.value || '' }; });
  return { url: location.href, heads: heads.slice(0, 4),
           cands: keep.map((c, i) => ({ i, tag: c.tag, txt: c.txt })),
           inputs, bodyText: document.body.innerText.replace(/\\s+/g, ' ').slice(0, 700),
           scrollH: document.documentElement.scrollHeight, innerH: innerHeight };
}"""

# A real payment form, not a page that merely mentions payment. Kept tight on purpose:
# a loose test ("number", "checkout") fires on the very first quiz screen.
PAY_CHECK = """() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 10; };
  const fields = [...document.querySelectorAll('input')].filter(vis).some(i => {
    const hay = (i.name||'') + ' ' + (i.id||'') + ' ' + (i.autocomplete||'') + ' ' + (i.placeholder||'');
    return /card ?number|cardnumber|cc-num|cc-number|\\bcvc\\b|\\bcvv\\b|exp(iry|-date|month|year)/i.test(hay);
  });
  const frames = [...document.querySelectorAll('iframe')].filter(vis).some(f =>
    /(js\\.stripe\\.com\\/v3\\/elements-inner-card|paypal\\.com\\/webapps|braintree|sdk\\.primer\\.io\\/web\\/.*hosted-input|adyen|solidgate|checkout\\.com)/i.test(f.src || ''));
  const pat = /\\b(card number|cvv|cvc|expiry date|mm\\s*\\/\\s*yy)\\b/i.test(document.body.innerText);
  return fields || frames || pat;
}"""

INNER_SCROLL = """() => {
  let best = null;
  for (const el of document.querySelectorAll('body *')) {
    const d = el.scrollHeight - el.clientHeight;
    if (d > 40 && el.clientHeight > 250 && /auto|scroll/.test(getComputedStyle(el).overflowY)) {
      if (!best || d > best.d) best = { d, el };
    }
  }
  if (!best) return 0;
  best.el.setAttribute('data-wkscroll', '1');
  return best.d;
}"""

# Consent checkboxes only. Answer-option checkboxes must never be auto-ticked.
CONSENT = """() => {
  const out = [];
  document.querySelectorAll('input[type=checkbox]').forEach(cb => {
    if (cb.checked) return;
    const lbl = cb.closest('label') || (cb.id && document.querySelector('label[for="' + cb.id + '"]'));
    const holder = lbl || cb.parentElement;
    const txt = (holder ? holder.innerText : '').trim();
    if (/consent|i agree|privacy policy|terms/i.test(txt)) {
      (lbl || cb).click();
      if (!cb.checked) cb.click();
      out.push(txt.slice(0, 60));
    }
  });
  return out;
}"""


def slug(s, n=42):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip().lower()).strip("-")
    return s[:n] or "screen"


def build_presets(a):
    """Placeholder/label -> value. Order matters: goal weight before weight, ft/in before cm."""
    if a.units == "imperial":
        h_ft, h_in, w, goal = "5", "7", "165", "145"
    else:
        h_ft, h_in, w, goal = "5", "7", a.weight, a.goal
    return [
        (re.compile(r"(email|mail)", re.I), a.email),               # None unless --email given
        (re.compile(r"name", re.I), a.name),
        (re.compile(r"height.*\(ft\)|\bft\b", re.I), h_ft),
        (re.compile(r"height.*\(in\)|\binch|\bin\)", re.I), h_in),
        (re.compile(r"height|how tall|\bcm\b", re.I), a.height),
        (re.compile(r"(goal|target|dream|desired).*lbs?", re.I), "145"),
        (re.compile(r"(goal|target|dream|desired)", re.I), goal),
        (re.compile(r"weight.*lbs?|\blbs?\b", re.I), "165"),
        (re.compile(r"weight|\bkg\b", re.I), w),
        (re.compile(r"(how old|your age|age|year|birth)", re.I), a.age),
    ]


def value_for(inp, presets, context=""):
    hay = f"{inp['ph']} {inp['name']} {inp['type']} {context}"
    for rx, val in presets:
        if rx.search(hay):
            return val
    return "35" if inp["type"] in ("number", "tel") else "Alex"


def act(page, info, already, presets, prefer_continue=False, opt_counter=None):
    """One step: switch units, tick consent, fill inputs, click something. True if we acted."""
    ctx_text = " ".join(info["heads"]) + " " + info["bodyText"][:200]

    # Prefer metric: a screen offering both usually defaults to ft/lbs.
    if any(re.search(r"\((ft|in|lbs?)\)", (i["ph"] or ""), re.I) for i in info["inputs"]):
        tog = next((c for c in info["cands"] if UNITS_METRIC.search(c["txt"])), None)
        if tog and tog["txt"] not in already:
            try:
                page.locator(f'[data-wk="{tog["i"]}"]').click(timeout=4000)
                already.add(tog["txt"])
                print(f'  units -> "{tog["txt"]}"', flush=True)
                page.wait_for_timeout(1200)
                return True
            except Exception as e:
                print("  unit switch failed:", str(e)[:60], flush=True)

    filled = False
    for inp in info["inputs"]:
        if inp["val"]:
            continue
        val = value_for(inp, presets, ctx_text)
        if val is None:                      # e.g. email with no --email: leave it, stop soon after
            continue
        try:
            sel = f'[data-wki="{inp["i"]}"]'
            page.click(sel)
            page.fill(sel, "")
            page.locator(sel).press_sequentially(val, delay=90)   # fill() often skips React validation
            page.keyboard.press("Tab")
            filled = True
            print(f'  filled "{inp["ph"] or inp["name"] or inp["type"]}" = {val}', flush=True)
            page.wait_for_timeout(600)
        except Exception as e:
            print("  fill failed:", str(e)[:70], flush=True)

    try:
        ticked = page.evaluate(CONSENT)
        if ticked:
            print("  consent ticked:", ticked, flush=True)
            page.wait_for_timeout(700)
    except Exception as e:
        print("  consent tick failed:", str(e)[:60], flush=True)

    opts, conts = [], []
    for c in info["cands"]:
        if SKIP.search(c["txt"]) or c["txt"] in already:
            continue
        (conts if CONT.search(c["txt"]) else opts).append(c)

    # On a multi-select, pick a few options then go for the CTA instead of ticking all 30.
    many = opt_counter is not None and opt_counter.get("n", 0) >= 3
    order = (conts + opts) if (prefer_continue or filled or many) else (opts + conts)

    for c in order:
        try:
            el = page.locator(f'[data-wk="{c["i"]}"]')
            el.scroll_into_view_if_needed(timeout=3000)
            el.click(timeout=4000)
            already.add(c["txt"])
            if opt_counter is not None and not CONT.search(c["txt"]):
                opt_counter["n"] = opt_counter.get("n", 0) + 1
            print(f'  clicked -> "{c["txt"][:55]}"', flush=True)
            page.wait_for_timeout(1500)
            return True
        except Exception as e:
            print(f'  click "{c["txt"][:28]}" failed: {str(e)[:60]}', flush=True)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="funnel entry URL (required unless --resume)")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--email", default=None, help="email to type into an email gate (omit to stop there)")
    ap.add_argument("--name", default="Alex")
    ap.add_argument("--height", default="170")
    ap.add_argument("--weight", default="75")
    ap.add_argument("--goal", default="65")
    ap.add_argument("--age", default="35")
    ap.add_argument("--units", choices=["metric", "imperial"], default="metric")
    ap.add_argument("--device", choices=list(B.DEVICES), default="iphone")
    ap.add_argument("--locale", default="en-US")
    ap.add_argument("--max-steps", type=int, default=260, help="iteration cap; long funnels need 250+")
    ap.add_argument("--start", type=int, default=0, help="first screenshot number (for --resume)")
    ap.add_argument("--resume", action="store_true", help="reuse state.json + last_url.txt")
    ap.add_argument("--headed", action="store_true", help="visible browser (needs real Chrome)")
    a = ap.parse_args()

    base = Path(os.path.expanduser(a.out))
    out = base / "shots"
    out.mkdir(parents=True, exist_ok=True)
    B.keep_private(base)
    state_f, url_f, log_f = base / "state.json", base / "last_url.txt", base / "log.json"
    if not a.url and not a.resume:
        ap.error("--url is required unless --resume")

    presets = build_presets(a)
    # keep earlier iterations when resuming, otherwise INDEX.md loses their descriptions
    log = json.loads(log_f.read_text()) if (a.resume and log_f.exists()) else []
    n, saved, waits = 0, a.start, 0
    seen, tried, opt_clicks = {}, defaultdict(set), defaultdict(dict)

    with sync_playwright() as p:
        brw = B.launch(p, headed=a.headed)
        ctx = B.new_context(brw, device=a.device, locale=a.locale,
                            storage_state=str(state_f) if a.resume else None)
        page = ctx.new_page()
        start_url = url_f.read_text().strip() if (a.resume and url_f.exists()) else a.url
        print("start:", start_url, flush=True)
        page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        prev_sig = None
        while n < a.max_steps:
            page.wait_for_timeout(1400)
            try:
                info = page.evaluate(DESCRIBE)
            except Exception as e:
                print("describe failed:", str(e)[:80], flush=True)
                break
            n += 1
            sig = re.sub(r"\d+", "#", info["bodyText"][:250])   # ignore timers/counters
            fname, new = seen.get(sig), False
            if fname is None:
                saved += 1
                new = True
                title = info["heads"][0] if info["heads"] else info["bodyText"][:45]
                fname = f"{saved:02d}-{slug(title)}.png"
                page.screenshot(path=str(out / fname),
                                full_page=info["scrollH"] > info["innerH"] + 24)
                seen[sig] = fname
                try:
                    over = page.evaluate(INNER_SCROLL)
                    if over and over > 40:
                        page.evaluate("() => { document.querySelector('[data-wkscroll]').scrollTop = 1e6 }")
                        page.wait_for_timeout(800)
                        page.screenshot(path=str(out / fname.replace(".png", "-scrolled.png")))
                        print(f"  + inner scroll {int(over)}px -> {fname.replace('.png', '-scrolled.png')}",
                              flush=True)
                        page.evaluate("() => { const e = document.querySelector('[data-wkscroll]');"
                                      " if (e) { e.scrollTop = 0; e.removeAttribute('data-wkscroll'); } }")
                        page.wait_for_timeout(400)
                except Exception as e:
                    print("  inner-scroll capture failed:", str(e)[:70], flush=True)

            log.append({"n": n, "file": fname, "new": new, "url": info["url"], "heads": info["heads"],
                        "inputs": info["inputs"], "cands": [c["txt"] for c in info["cands"]],
                        "text": info["bodyText"][:250]})
            log_f.write_text(json.dumps(log, indent=2, ensure_ascii=False))
            print(f'[{n}] {"NEW " if new else "rep "}{fname} :: {info["url"][:80]} :: '
                  f'{info["heads"][:2]} :: {[c["txt"][:26] for c in info["cands"]][:8]}', flush=True)

            try:
                if page.evaluate(PAY_CHECK):
                    print("STOP: payment form on screen — nothing typed. "
                          "Use paywall.py to document the paywall and card form.", flush=True)
                    break
            except Exception:
                pass
            if any(i["type"] == "email" for i in info["inputs"]) and not a.email:
                print("STOP: email gate and no --email given", flush=True)
                break
            if re.search(r"(password|confirm password)", info["bodyText"], re.I) and \
               any(i["type"] == "password" for i in info["inputs"]):
                print("STOP: account creation with a password — not doing that", flush=True)
                break

            prefer_cont = (sig == prev_sig)
            prev_sig = sig
            if not act(page, info, tried[sig], presets, prefer_cont, opt_clicks[sig]):
                if not info["cands"] and waits < 10:
                    waits += 1
                    print(f"  ...loading screen, waiting ({waits})", flush=True)
                    page.wait_for_timeout(5000)
                    continue
                print("STOP: nothing left to click", flush=True)
                break

        try:
            ctx.storage_state(path=str(state_f))
            url_f.write_text(page.url)
        except Exception as e:
            print("state save failed:", str(e)[:60], flush=True)
        brw.close()

    print(f"\ndone: {saved - a.start} new screens ({saved} total), {n} iterations -> {out}", flush=True)
    print(f"resume with: --resume --start {saved}", flush=True)


if __name__ == "__main__":
    main()
