#!/usr/bin/env python3
"""Document a funnel's paywall and payment step, screenshots only.

    python3 paywall.py --out ~/example-quiz --prefix 51

Runs, in order:
  1. tiles of the paywall, viewport by viewport (+ one full-page image)
  2. any discount / gift modal, then claims it and re-tiles the discounted paywall
  3. one screenshot per plan option selected
  4. the main CTA, then the payment step: billing modal, expanded card accordion,
     or an inline Stripe/Primer element scrolled into view

It never types into a payment field and never clicks a pay button
(Pay / Continue Securely / Google Pay / Apple Pay / PayPal are all excluded).
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import browser as B  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# Paywalls often scroll inside a container rather than the window; find whichever it is.
SCROLLER = """() => {
  document.querySelectorAll('[data-tile]').forEach(e => e.removeAttribute('data-tile'));
  let best = null;
  for (const el of document.querySelectorAll('body *')) {
    const d = el.scrollHeight - el.clientHeight;
    if (d > 100 && el.clientHeight > 300 && /auto|scroll/.test(getComputedStyle(el).overflowY)) {
      if (!best || d > best.d) best = { d, el };
    }
  }
  if (best) { best.el.setAttribute('data-tile', '1'); return { inner: true, d: best.d, h: best.el.clientHeight }; }
  return { inner: false, d: document.documentElement.scrollHeight - innerHeight, h: innerHeight };
}"""

DISCOUNT = r"claim my|claim your|unlock|jackpot|special offer|here'?s something|gift|spin|reveal"
PAY_BUTTON = r"apple pay|google pay|paypal|pay now|continue securely|place order|buy now|complete purchase"

# JS .click() beats Playwright .click()/.tap() on these funnels: modal overlays
# (a decorative div over the button) swallow real pointer events and time out.
JSCLICK = r"""([pattern, avoid]) => {
  const rx = new RegExp(pattern, 'i'), bad = new RegExp(avoid, 'i');
  const pool = [...document.querySelectorAll('button, .btn, a, [role=button], [class*=plan], [class*=tab]')];
  const el = pool.filter(e => rx.test(e.innerText || '') && !bad.test(e.innerText || '')
                              && e.getBoundingClientRect().height > 20)
                 .sort((a, b) => a.innerText.length - b.innerText.length)[0];
  if (!el) return null;
  el.scrollIntoView({ block: 'center' });
  el.click();
  return (el.className || '').slice(0, 50) + ' :: ' + el.innerText.replace(/\s+/g, ' ').slice(0, 40);
}"""


def tiles(page, out, prefix, limit=20):
    info = page.evaluate(SCROLLER)
    step, total = info["h"] - 40, info["d"] + info["h"]
    i, y = 0, 0
    while y < total - 60 and i < limit:
        if info["inner"]:
            page.evaluate(f"() => {{ document.querySelector('[data-tile]').scrollTop = {y}; }}")
        else:
            page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(1200)
        i += 1
        page.screenshot(path=str(out / f"{prefix}-{i:02d}.png"))
        y += step
        total = (page.evaluate("() => document.documentElement.scrollHeight") if not info["inner"]
                 else total)
    page.screenshot(path=str(out / f"{prefix}-fullpage.png"), full_page=True)
    print(f"  {prefix}: {i} tiles + fullpage (scroll {info['d']}px, inner={info['inner']})", flush=True)
    if info["inner"]:
        page.evaluate("() => { const e = document.querySelector('[data-tile]'); if (e) e.scrollTop = 0; }")
    else:
        page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(600)


def prices(page):
    return page.evaluate("""() => [...document.querySelectorAll('[class*=plan]')]
        .map(e => e.innerText.replace(/\\s+/g, ' ').trim())
        .filter(t => t.length > 15 && /\\$|€|£/.test(t)).slice(0, 4)""")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", help="paywall URL (default: last_url.txt from the walk)")
    ap.add_argument("--prefix", default="90", help="number prefix continuing the walk's numbering")
    ap.add_argument("--device", choices=list(B.DEVICES), default="iphone")
    ap.add_argument("--locale", default="en-US")
    ap.add_argument("--no-claim", action="store_true", help="do not claim discount offers")
    ap.add_argument("--wait-modal", type=int, default=30,
                    help="seconds to wait for a delayed discount popup (0 to skip)")
    ap.add_argument("--headed", action="store_true")
    a = ap.parse_args()

    base = Path(os.path.expanduser(a.out))
    out = base / "shots"
    out.mkdir(parents=True, exist_ok=True)
    B.keep_private(base)
    url = a.url or (base / "last_url.txt").read_text().strip()
    pfx = int(a.prefix)

    with sync_playwright() as p:
        brw = B.launch(p, headed=a.headed)
        ctx = B.new_context(brw, device=a.device, locale=a.locale,
                            storage_state=str(base / "state.json"))
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        print("paywall:", page.url, flush=True)
        print("  plans:", prices(page), flush=True)

        tiles(page, out, f"{pfx}-paywall")

        # a discount modal may be there on load or pop up after a delay
        claimed = False
        for _ in range(max(1, a.wait_modal // 3)):
            has = page.evaluate(f"""() => [...document.querySelectorAll('*')].some(e =>
                /{DISCOUNT}/i.test(e.innerText || '') && e.getBoundingClientRect().height > 20)""")
            if has:
                page.screenshot(path=str(out / f"{pfx + 1}-discount-modal.png"))
                print(f"  discount modal -> {pfx + 1}-discount-modal.png", flush=True)
                if not a.no_claim:
                    r = page.evaluate(JSCLICK, [DISCOUNT, PAY_BUTTON])
                    print("  claimed:", r, flush=True)
                    page.wait_for_timeout(5000)
                    claimed = True
                break
            if a.wait_modal == 0:
                break
            page.wait_for_timeout(3000)

        if claimed:
            print("  plans after claim:", prices(page), flush=True)
            tiles(page, out, f"{pfx + 2}-paywall-discounted")

        # one screenshot per plan option
        plans = page.evaluate("""() => {
          const els = [...document.querySelectorAll('[class*=plan-picker__item], [class*=plan]')]
            .filter(e => { const r = e.getBoundingClientRect();
                           return r.height > 40 && r.height < 280 && /\\$|€|£/.test(e.innerText || ''); });
          const seen = new Set(), out = [];
          els.forEach(e => { const k = (e.innerText || '').slice(0, 20); if (seen.has(k)) return; seen.add(k);
            e.setAttribute('data-plan', String(out.length));
            out.push(e.innerText.replace(/\\s+/g, ' ').slice(0, 45)); });
          return out;
        }""")
        print("  plan options:", plans, flush=True)
        for idx, label in enumerate(plans[:5]):
            try:
                page.evaluate(f"""() => {{ const e = document.querySelector('[data-plan="{idx}"]');
                                          e.scrollIntoView({{block:'center'}}); e.click(); }}""")
                page.wait_for_timeout(1500)
                page.screenshot(path=str(out / f"{pfx + 3}-plan-{idx + 1}-selected.png"))
                print(f"    plan {idx + 1} '{label}'", flush=True)
            except Exception as e:
                print(f"    plan {idx} failed: {str(e)[:60]}", flush=True)

        # main CTA -> payment step
        r = page.evaluate(JSCLICK, ["continue|get my plan|start|grab my|checkout|subscribe", PAY_BUTTON])
        print("  CTA:", r, flush=True)
        for _ in range(8):
            page.wait_for_timeout(3000)
            st = page.evaluate("""() => ({
              modal: [...document.querySelectorAll('[class*=billing-modal],[class*=checkout],[role=dialog]')]
                       .filter(e => e.getBoundingClientRect().height > 150).map(e => e.className.slice(0, 35)),
              element: !!document.querySelector('.StripeElement, [class*=__PrivateStripeElement]'),
              url: location.pathname })""")
            if st["modal"] or st["element"]:
                print("  payment step:", st, flush=True)
                break
        page.screenshot(path=str(out / f"{pfx + 4}-payment-step.png"))

        # expand a collapsed card accordion, or scroll an inline element into view
        r = page.evaluate(JSCLICK, ["credit card|card|pay by card", PAY_BUTTON])
        if r:
            print("  card row:", r, flush=True)
            page.wait_for_timeout(3500)
        el = page.evaluate("""() => {
          const e = document.querySelector('.StripeElement, [class*=__PrivateStripeElement], iframe[src*="hosted-input"]');
          if (!e) return null; e.scrollIntoView({ block: 'center' });
          return Math.round(e.getBoundingClientRect().height); }""")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(out / f"{pfx + 5}-card-form-empty.png"))
        print(f"  card form element height: {el} -> {pfx + 5}-card-form-empty.png", flush=True)
        if page.evaluate("() => document.documentElement.scrollHeight > 900"):
            page.screenshot(path=str(out / f"{pfx + 5}-card-form-empty-full.png"), full_page=True)

        (base / "last_url.txt").write_text(page.url)
        ctx.storage_state(path=str(base / "state.json"))
        brw.close()
    print("done ->", out, flush=True)


if __name__ == "__main__":
    main()
