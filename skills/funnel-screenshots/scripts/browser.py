#!/usr/bin/env python3
"""Shared browser factory for funnel screenshotting.

Two things here matter and are the result of painful trial and error:

1. Retina screenshots. The context MUST be created with device_scale_factor=3 and
   is_mobile=True. Never call page.set_viewport_size() afterwards — Playwright
   re-applies its own device metrics and silently drops the DPR back to 1, which
   turns 1179x2556 retina shots into blurry 393x852 ones.

2. Bot traps. Some funnels sniff the `sec-ch-ua` client hint,
   see "HeadlessChrome" and 302 you into a tarpit (Nepenthes) that serves endless
   generated garbage. Overriding the three sec-ch-ua headers is enough to pass.
"""
import glob
import os
import re
import sys

IPHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")
DESKTOP_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

# iPhone 15 Pro / iPhone 16: 393x852 CSS px at DPR 3 -> 1179x2556 png
DEVICES = {
    "iphone":  dict(viewport={"width": 393, "height": 852}, device_scale_factor=3,
                    is_mobile=True, has_touch=True, user_agent=IPHONE_UA),
    "android": dict(viewport={"width": 412, "height": 915}, device_scale_factor=3,
                    is_mobile=True, has_touch=True,
                    user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"),
    "desktop": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=2,
                    is_mobile=False, has_touch=False, user_agent=DESKTOP_UA),
}

CLIENT_HINTS = {
    "sec-ch-ua": '"Chromium";v="152", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"iOS"',
}


def cache_dirs():
    home = os.path.expanduser("~")
    return [os.path.join(home, "Library", "Caches", "ms-playwright"),   # macOS
            os.path.join(home, ".cache", "ms-playwright")]              # Linux


def resolve_chromium():
    """Return an executable_path for Chromium, or None to use Playwright's default.

    The Python playwright package pins one browser build number; a browser
    installed by a different playwright version (or by the Node package) lives in
    a differently numbered folder and the default launch fails with
    "Executable doesn't exist". Picking the newest build present fixes it.
    """
    override = os.environ.get("FUNNELSHOT_CHROMIUM")
    if override and os.path.exists(override):
        return override

    candidates = []
    for base in cache_dirs():
        candidates += glob.glob(os.path.join(base, "chromium_headless_shell-*",
                                             "chrome-headless-shell-*", "chrome-headless-shell"))
        candidates += glob.glob(os.path.join(base, "chromium-*", "chrome-mac*", "Chromium.app",
                                             "Contents", "MacOS", "Chromium"))
        candidates += glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome"))
    if not candidates:
        return None

    def build_no(path):
        m = re.search(r"-(\d+)/", path)
        return int(m.group(1)) if m else 0

    return sorted(candidates, key=build_no)[-1]


def launch(playwright, headed=False):
    """Launch Chromium, falling back to a cached build if the pinned one is missing."""
    exe = resolve_chromium()
    headless = not headed
    # A headless-shell binary cannot run headed; fall back to real Chrome for that.
    if headed and exe and "headless-shell" in exe:
        exe = None
        try:
            return playwright.chromium.launch(headless=False, channel="chrome")
        except Exception:
            pass
    try:
        return playwright.chromium.launch(headless=headless, executable_path=exe) if exe \
            else playwright.chromium.launch(headless=headless)
    except Exception as first:
        try:
            return playwright.chromium.launch(headless=headless)
        except Exception:
            print(f"could not launch chromium: {first}\n"
                  f"run the skill's scripts/setup.sh to install the browser", file=sys.stderr)
            raise


def new_context(browser, device="iphone", locale="en-US", storage_state=None, spoof_hints=True):
    cfg = dict(DEVICES[device])
    cfg["locale"] = locale
    if storage_state and os.path.exists(storage_state):
        cfg["storage_state"] = storage_state
    if spoof_hints:
        hints = dict(CLIENT_HINTS)
        if device == "desktop":
            hints["sec-ch-ua-mobile"] = "?0"
            hints["sec-ch-ua-platform"] = '"macOS"'
        cfg["extra_http_headers"] = hints
    return browser.new_context(**cfg)


PRIVATE = ["state.json", "log.json", "last_url.txt"]


def keep_private(base):
    """state.json holds the funnel's cookies and localStorage; log.json and last_url.txt
    can carry a typed email in field values and URLs. A .gitignore in the output folder
    keeps the three out of git wherever --out points, so shots/ and INDEX.md stay
    shareable. Existing lines are left alone; missing ones are appended."""
    gi = os.path.join(str(base), ".gitignore")
    text = open(gi, encoding="utf-8").read() if os.path.exists(gi) else ""
    missing = [p for p in PRIVATE if p not in text.splitlines()]
    if missing:
        with open(gi, "a", encoding="utf-8") as f:
            if text and not text.endswith("\n"):
                f.write("\n")
            if not text:
                f.write("# funnel-screenshots: browser session and typed values, never commit\n")
            f.write("".join(p + "\n" for p in missing))
