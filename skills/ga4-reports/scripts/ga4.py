#!/usr/bin/env python3
"""GA4 Data API runReport over REST (stdlib only) — the fallback when the GA4 MCP
server hangs or is not connected.

Accepts the SAME query JSON you would pass to the MCP `run_report` tool (snake_case)
and converts it to the REST shape (camelCase), so one query works on both paths.

Usage:
  ga4.py --property 123456789 query.json            # query from a file
  ga4.py --property 123456789 '{"dimensions":["date"], ...}'
  ga4.py query.json --out raw/ga4/sessions.json     # property from GA4_PROPERTY_ID
  ga4.py --list-properties                          # find your property ids

Auth: a Google access token from Application Default Credentials
(`gcloud auth application-default print-access-token`). Setup: connections/ga4-mcp.md.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

DATA = "https://analyticsdata.googleapis.com/v1beta"
ADMIN = "https://analyticsadmin.googleapis.com/v1beta"


def token() -> str:
    try:
        out = subprocess.run(["gcloud", "auth", "application-default", "print-access-token"],
                             capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        sys.exit("gcloud not found. Install the Google Cloud CLI — see connections/ga4-mcp.md")
    if out.returncode != 0 or not out.stdout.strip():
        sys.exit("No Google credentials. Run the login from connections/ga4-mcp.md, then retry.\n"
                 + out.stderr.strip()[:300])
    return out.stdout.strip()


def camel(s: str) -> str:
    head, *rest = s.split("_")
    return head + "".join(w[:1].upper() + w[1:] for w in rest)


def to_rest(q):
    """MCP-style snake_case query -> REST camelCase body. Plain dimension / metric
    names become {"name": ...} objects, as the REST API expects."""
    if isinstance(q, list):
        return [to_rest(v) for v in q]
    if not isinstance(q, dict):
        return q
    out = {}
    for k, v in q.items():
        ck = camel(k)
        if ck in ("dimensions", "metrics") and isinstance(v, list):
            out[ck] = [{"name": x} if isinstance(x, str) else to_rest(x) for x in v]
        else:
            out[ck] = to_rest(v)
    return out


def call(url: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(url, method="POST" if body is not None else "GET",
                                 headers={"Authorization": f"Bearer {token()}",
                                          "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:600]
        if e.code == 401:
            msg += "\n→ token expired: repeat the login from connections/ga4-mcp.md"
        sys.exit(f"HTTP {e.code}: {msg}")


def table(data: dict) -> str:
    heads = [h["name"] for h in data.get("dimensionHeaders", [])] + \
            [h["name"] for h in data.get("metricHeaders", [])]
    lines = [" | ".join(heads), " | ".join("---" for _ in heads)]
    for row in data.get("rows", []):
        cells = [v["value"] for v in row.get("dimensionValues", [])] + \
                [v["value"] for v in row.get("metricValues", [])]
        lines.append(" | ".join(cells))
    lines.append(f"\n{data.get('rowCount', len(data.get('rows', [])))} rows")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="query JSON or a path to a .json file")
    ap.add_argument("--property", default=os.environ.get("GA4_PROPERTY_ID"),
                    help="GA4 property id (digits); default: env GA4_PROPERTY_ID")
    ap.add_argument("--out", help="save the raw JSON response here")
    ap.add_argument("--list-properties", action="store_true")
    a = ap.parse_args()

    if a.list_properties:
        data = call(f"{ADMIN}/accountSummaries?pageSize=200")
        for acc in data.get("accountSummaries", []):
            print(acc.get("displayName"))
            for p in acc.get("propertySummaries", []):
                print(f"   {p['property'].split('/')[-1]:>12}  {p.get('displayName')}")
        return

    if not a.query:
        ap.error("query is required")
    if not a.property:
        ap.error("no property: pass --property or set GA4_PROPERTY_ID (find it with --list-properties)")
    raw = pathlib.Path(a.query).read_text() if a.query.endswith(".json") and pathlib.Path(a.query).exists() else a.query
    body = to_rest(json.loads(raw))
    data = call(f"{DATA}/properties/{str(a.property).removeprefix('properties/')}:runReport", body)
    if a.out:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"saved {a.out}")
    print(table(data))


if __name__ == "__main__":
    main()
