#!/usr/bin/env bash
# One-time setup for the funnel-screenshots skill.
#
#   bash <skill folder>/scripts/setup.sh
#
# Idempotent: safe to re-run. Prints the python interpreter to use at the end.
# Installs into its own venv so it cannot break a system python (Homebrew/Debian
# pythons refuse global pip installs — PEP 668). The venv lives outside the skill
# folder, so plugin updates don't wipe it:
#   ~/.cache/marketing-agent-kit/funnelshot-venv   (override with FUNNELSHOT_VENV)
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${FUNNELSHOT_VENV:-$HOME/.cache/marketing-agent-kit/funnelshot-venv}"
mkdir -p "$(dirname "$VENV")"
say() { printf '\n== %s\n' "$*"; }

say "Looking for python3"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$(command -v "$c")"; break; fi
done
if [ -z "$PY" ]; then
  echo "No python3 found."
  echo "  macOS:  brew install python   (or install Xcode command line tools)"
  echo "  Ubuntu: sudo apt install python3 python3-venv"
  exit 1
fi
echo "using $PY ($("$PY" --version 2>&1))"

# 1. Is playwright already importable somewhere usable?
INTERP=""
if "$PY" -c "import playwright" >/dev/null 2>&1; then
  echo "playwright already importable with $PY"
  INTERP="$PY"
elif [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c "import playwright" >/dev/null 2>&1; then
  echo "playwright already installed in $VENV"
  INTERP="$VENV/bin/python"
fi

# 2. Otherwise create the venv and install it there.
if [ -z "$INTERP" ]; then
  say "Installing playwright into $VENV"
  if [ ! -x "$VENV/bin/python" ]; then
    "$PY" -m venv "$VENV" || {
      echo "venv creation failed — on Debian/Ubuntu: sudo apt install python3-venv"; exit 1; }
  fi
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet playwright || { echo "pip install playwright failed"; exit 1; }
  INTERP="$VENV/bin/python"
fi

# 3. Browser binary. Any recent Chromium build in the ms-playwright cache works —
#    browser.py picks the newest one, which sidesteps the classic
#    "Executable doesn't exist at .../chromium_headless_shell-1208/..." mismatch.
say "Checking for a Chromium build"
CACHE_MAC="$HOME/Library/Caches/ms-playwright"
CACHE_LNX="$HOME/.cache/ms-playwright"
if ls -d "$CACHE_MAC"/chromium* >/dev/null 2>&1 || ls -d "$CACHE_LNX"/chromium* >/dev/null 2>&1; then
  echo "found:"
  ls -d "$CACHE_MAC"/chromium* "$CACHE_LNX"/chromium* 2>/dev/null | sed 's/^/  /'
else
  echo "none found, downloading (~150 MB)"
  "$INTERP" -m playwright install chromium || { echo "browser download failed"; exit 1; }
fi

# 4. Smoke test: render a known page and assert the screenshot is retina-sized.
say "Smoke test (retina screenshot + client-hint spoofing)"
"$INTERP" - "$SKILL_DIR" <<'PY'
import sys, os, pathlib, tempfile
sys.path.insert(0, os.path.join(sys.argv[1], "scripts"))
import browser as B
from playwright.sync_api import sync_playwright

out = pathlib.Path(tempfile.gettempdir()) / "funnelshot-smoketest.png"
with sync_playwright() as p:
    b = B.launch(p)
    ctx = B.new_context(b)
    page = ctx.new_page()
    page.set_content("<h1 style='font:700 40px -apple-system'>funnel-screenshots ok</h1>")
    page.screenshot(path=str(out))
    dpr, w = page.evaluate("() => [devicePixelRatio, innerWidth]")
    hints = page.evaluate("() => navigator.userAgent")
    b.close()

size = out.stat().st_size
print(f"chromium: {B.resolve_chromium() or 'playwright default'}")
print(f"viewport {w} css px @ DPR {dpr} -> screenshot {out.name} ({size} bytes)")
out.unlink(missing_ok=True)
if dpr != 3:
    print("WARNING: DPR is not 3 — screenshots will not be retina. Check browser.py.")
    sys.exit(1)
print("iPhone UA:", hints[:60], "...")
PY
rc=$?

say "Result"
if [ $rc -eq 0 ]; then
  echo "Setup OK. Use this interpreter for the skill's scripts:"
  echo "  $INTERP"
  echo
  echo "Example:"
  echo "  $INTERP $SKILL_DIR/scripts/funnelshot.py --url https://example.com/quiz --out ~/example-quiz"
else
  echo "Smoke test failed — see the output above."
  exit 1
fi
