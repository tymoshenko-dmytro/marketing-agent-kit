# Troubleshooting

Every one of these was hit for real while capturing long app funnels. The scripts already
handle them; this is here for when a new funnel behaves differently.

## Screenshots come out blurry / 393×852 instead of 1179×2556

The context must be created with `device_scale_factor=3`. Two ways to lose it:

- calling `page.set_viewport_size()` after the context exists — Playwright re-applies
  its own device metrics and resets DPR to 1
- driving the page through the Playwright **MCP server** instead of these scripts —
  its context is DPR 1 and `browser_take_screenshot(scale: "device")` cannot fix that.
  A CDP `Emulation.setDeviceMetricsOverride` also does not survive: Playwright
  re-applies metrics at screenshot time. Use the scripts.

Sanity check: the PNG width must be exactly 3× the CSS viewport width (393 → 1179).

## The site redirects to garbage pages / screenshots hang on "waiting for fonts"

Some funnels detect automation from request headers alone and 302 you into a tarpit
(one sent bots to a Nepenthes demo — an infinite maze of generated text). The tell is `sec-ch-ua: "HeadlessChrome"`. `browser.py` overrides the
three `sec-ch-ua*` hints, which is enough. Check with `curl -A "<iPhone UA>" -o /dev/null
-w "%{http_code} %{redirect_url}\n" <url>`: if curl gets 200 and Playwright gets 302,
it is header sniffing, not JS fingerprinting.

If hints are not enough, next escalations: `--headed` (real Chrome, `channel="chrome"`),
then a real Chrome profile.

## "Executable doesn't exist at .../chromium_headless_shell-1208/..."

The installed `playwright` pip package pins one browser build; a different build is in
the cache. `browser.resolve_chromium()` picks the newest build present. To force one:
`export FUNNELSHOT_CHROMIUM=/path/to/chrome-headless-shell`. Or just install the pinned
build: `~/.cache/marketing-agent-kit/funnelshot-venv/bin/python -m playwright install chromium`.

## Clicks time out: "Locator.click: Timeout ... waiting for element to be stable"

Decorative overlays (a `div.discount-gift` over the button), animated countdowns and
sticky footers make Playwright's actionability checks fail forever. Coordinate taps hit
the overlay instead of the button.

Fix: click in JS — `page.evaluate("() => el.click()")`. That is what `paywall.py`'s
`JSCLICK` does. Verify the click worked by checking state (modal gone, prices changed),
not by assuming.

## Continue is greyed out and nothing advances

Three causes, in order of likelihood:

1. **A consent checkbox** below the input ("I consent to … processing my health data").
   `funnelshot.py` ticks only consent-worded checkboxes, never answer options.
2. **`fill()` did not trigger the framework's validation.** Type instead:
   `locator.press_sequentially(value, delay=90)` then Tab. This is why the scripts type.
3. **Wrong value for the unit.** See below.

## Height/weight get nonsense values

Funnels default to ft/lbs and expose separate `Height (ft)` / `Height (in)` inputs.
Filling 170 into "ft" gives an invalid value and a permanently disabled Continue.
`funnelshot.py` clicks a `cm / kg` toggle when it sees imperial placeholders; for funnels
with no toggle use `--units imperial`. Order of the preset rules matters — goal weight
before weight, ft/in before cm.

## "STOP: nothing left to click" in the middle of the funnel

The screen's CTA is worded in a way the `CONT` regex does not know. Real examples that
had to be added: "Save my preferences", "Let's finish this", "All done!", "Grab my plan
to hit 65 kg!", "Sounds good", "Got it". Add the wording to `CONT` in `funnelshot.py`
and re-run with `--resume`.

Also check `log.json`'s last entry: its `cands` list shows exactly what was on screen.

## It clicks 30 options on one multi-select screen

Expected on "choose as many as you like" screens where the CTA stays disabled until
something is picked. The walker caps this at 3 option clicks, then prefers the CTA.
Screens are deduplicated by body-text signature, so those iterations do not produce
duplicate screenshots.

## Options are cut off at the bottom of a screenshot

The list scrolls inside a container, so `document.scrollHeight` equals the viewport and
`full_page=True` changes nothing. The walker finds the container
(`scrollHeight - clientHeight > 40`, `overflow-y: auto|scroll`), scrolls it to the bottom
and saves a `-scrolled.png` companion. Paywalls do the same thing — `paywall.py` tiles the
container, not the window.

## Loaders / "analyzing your answers" screens end the run early

They have no clickable elements. The walker waits 5 s up to 10 times before giving up,
and those loaders often hide a question mid-animation (several long funnels do this),
which is why it keeps screenshotting while waiting.

## Full-page screenshots come out absurdly tall (15 000+ px)

Lazy-loaded blocks and carousels expand during a full-page capture, so the single image
is both huge and not what a user sees. Keep it as a bonus artifact but rely on the
viewport tiles for "what the user actually sees".

## The paywall shows a gift/discount modal on load

Then the first tiles are of the *blocked* paywall. Claim the discount first (JS click),
confirm prices changed, then tile again. `paywall.py` does this and labels both sets;
just check its printed "plans after claim" line to confirm the discount applied.

## The capture stops at "account creation with a password"

Not a bug and not something to work around — that is the guardrail. Some funnels gate
the card form behind a password account. Some additionally refuse to create a checkout
session without a logged-in account: the trial button returns an inline "Something went
wrong" and never contacts the payment provider. The paywall itself can often still be
reached by navigating to the paywall route directly.
