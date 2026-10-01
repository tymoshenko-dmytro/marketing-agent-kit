#!/usr/bin/env python3
"""Ahrefs API v3 caller (stdlib only) — for scripted pulls with an API v3 key.

The MCP server is the default way to use Ahrefs from Claude. Use this script when you
have an API v3 key (Ahrefs Enterprise) and want repeatable, cached pulls. Do NOT point
custom scripts at the MCP endpoint: Ahrefs' MCP terms don't permit standalone
JSON-RPC clients — scripted access goes through API v3.

Usage:
  ahrefs_api.py site-explorer/domain-rating target=example.com date=2026-09-30
  ahrefs_api.py site-explorer/organic-keywords target=example.com date=2026-09-30 select=keyword,sum_traffic,best_position limit=100 order_by=sum_traffic:desc --out raw/seo/kw.json
  ahrefs_api.py keywords-explorer/overview country=us keywords="crm,crm software" select=keyword,volume
  ahrefs_api.py subscription-info/limits-and-usage

The endpoint path is the MCP tool name with the first dash turned into a slash
(site-explorer-organic-keywords → site-explorer/organic-keywords). Every k=v pair is
passed as a query parameter. Reference: https://docs.ahrefs.com/docs/api/reference
Key: AHREFS_API_KEY (env or ~/.config/marketing-agent-kit/.env).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.ahrefs.com/v3/"


def _key() -> str:
    """AHREFS_API_KEY: env var first, then the kit's env file (see connections/ahrefs-mcp.md)."""
    v = os.environ.get("AHREFS_API_KEY")
    if v:
        return v
    envp = os.path.expanduser(os.environ.get("MARKETING_KIT_ENV", "~/.config/marketing-agent-kit/.env"))
    if os.path.exists(envp):
        for line in open(envp):
            k, _, val = line.strip().partition("=")
            val = re.split(r"(?:^|\s)#", val.strip(), maxsplit=1)[0].strip().strip('"').strip("'")   # same rule as kit.py
            if k.strip() == "AHREFS_API_KEY" and val:
                return val
    raise SystemExit("AHREFS_API_KEY not found. API v3 keys come with Ahrefs Enterprise; "
                     "otherwise use the Ahrefs MCP server (see connections/ahrefs-mcp.md).")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    endpoint, out, params = args[0].strip("/"), None, {}
    i = 1
    while i < len(args):
        if args[i] == "--out":
            out = args[i + 1]
            i += 2
        elif "=" in args[i]:
            k, v = args[i].split("=", 1)
            params[k] = v
            i += 1
        else:
            sys.exit(f"unrecognized arg: {args[i]}")
    url = BASE + endpoint + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_key()}",
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:600]
        hint = ""
        if e.code == 401:
            hint = "\n→ 401: wrong key type? MCP keys don't work on API v3, and vice versa."
        sys.exit(f"HTTP {e.code}: {body}{hint}")
    blob = json.dumps(data, ensure_ascii=False, indent=2)
    if out:
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(out).write_text(blob)
        rows = next((len(v) for v in data.values() if isinstance(v, list)), None)
        print(f"saved {out}" + (f" | {rows} rows" if rows is not None else ""))
    else:
        print(blob[:8000])


if __name__ == "__main__":
    main()
