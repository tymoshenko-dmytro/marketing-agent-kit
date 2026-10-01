#!/usr/bin/env python3
"""SearchApi.io generic caller (stdlib only).

Usage:
  searchapi.py --engine google --out out.json q="acme analytics" num=10
  searchapi.py --engine google_ads_transparency_center --out ads.json advertiser_id=AR...
  searchapi.py --engine linkedin_ad_library --out li.json q=acme
  searchapi.py --engine meta_ad_library --out meta.json q=acme
  searchapi.py --engine youtube --out yt.json q="acme product demo"

Any k=v pairs after flags are passed as engine params verbatim.
Docs per engine: https://www.searchapi.io/docs/<engine-with-dashes>
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.searchapi.io/api/v1/search"


def _key() -> str:
    """SEARCHAPI_KEY: env var first, then the kit's env file (see connections/searchapi.md)."""
    v = os.environ.get("SEARCHAPI_KEY")
    if v:
        return v
    envp = os.path.expanduser(os.environ.get("MARKETING_KIT_ENV", "~/.config/marketing-agent-kit/.env"))
    if os.path.exists(envp):
        for line in open(envp):
            k, _, val = line.strip().partition("=")
            if k.strip() == "SEARCHAPI_KEY" and val.strip():
                return val.strip().strip('"').strip("'")
    raise SystemExit("SEARCHAPI_KEY not found. Add it to ~/.config/marketing-agent-kit/.env "
                     "(see connections/searchapi.md) or export it as an env var.")


def main() -> None:
    args = sys.argv[1:]
    engine, out = None, None
    params: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i] == "--engine":
            engine = args[i + 1]
            i += 2
        elif args[i] == "--out":
            out = args[i + 1]
            i += 2
        elif "=" in args[i]:
            k, v = args[i].split("=", 1)
            params[k] = v
            i += 1
        else:
            sys.stderr.write(f"unrecognized arg: {args[i]}\n")
            sys.exit(2)
    if not engine:
        sys.stderr.write("--engine required\n")
        sys.exit(2)

    params["engine"] = engine
    url = BASE + "?" + urllib.parse.urlencode(params)
    # the key goes in a header, not the URL, so it never lands in logs or shell history
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_key()}"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:500]}")

    blob = json.dumps(data, ensure_ascii=False, indent=2)
    if out:
        open(out, "w").write(blob)
        # print a small summary so callers can sanity-check without re-reading
        keys = [k for k in data.keys() if k not in ("search_metadata", "search_parameters")]
        print(f"saved {out} | top-level keys: {keys}")
    else:
        print(blob)


if __name__ == "__main__":
    main()
