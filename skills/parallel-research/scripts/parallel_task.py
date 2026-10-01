#!/usr/bin/env python3
"""Parallel.ai Task API wrapper (stdlib only).

Usage:
  parallel_task.py submit --input-file brief.txt --processor ultra   -> prints run_id
  parallel_task.py status RUN_ID                                     -> prints status
  parallel_task.py result RUN_ID --out result.json                   -> saves result JSON
  parallel_task.py search --objective "..." --query "q1" --query "q2" [--max 10] [--mode fast]

Statuses: queued, action_required, running, completed, failed, cancelling, cancelled.
Docs: https://docs.parallel.ai
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = "https://api.parallel.ai"


def _key() -> str:
    """PARALLEL_API_KEY: env var first, then the kit's env file (see connections/parallel-api.md)."""
    v = os.environ.get("PARALLEL_API_KEY")
    if v:
        return v
    envp = os.path.expanduser(os.environ.get("MARKETING_KIT_ENV", "~/.config/marketing-agent-kit/.env"))
    if os.path.exists(envp):
        for line in open(envp):
            k, _, val = line.strip().partition("=")
            val = re.split(r"(?:^|\s)#", val.strip(), maxsplit=1)[0].strip().strip('"').strip("'")   # same rule as kit.py
            if k.strip() == "PARALLEL_API_KEY" and val:
                return val
    raise SystemExit("PARALLEL_API_KEY not found. Add it to ~/.config/marketing-agent-kit/.env "
                     "(see connections/parallel-api.md) or export it as an env var.")


def _req(method: str, path: str, body: dict | None = None, timeout: int = 120):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        headers={"x-api-key": _key(), "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}: {e.read().decode()[:500]}\n")
        raise


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("submit")
    s.add_argument("--input-file", required=True)
    s.add_argument("--processor", default="pro")

    st = sub.add_parser("status")
    st.add_argument("run_id")

    r = sub.add_parser("result")
    r.add_argument("run_id")
    r.add_argument("--out")

    se = sub.add_parser("search")
    se.add_argument("--objective", required=True)
    se.add_argument("--query", action="append", default=[])
    se.add_argument("--max", type=int, default=10)
    se.add_argument("--mode", choices=["turbo", "fast", "basic", "advanced"],
                    help="search depth; server default is advanced")

    a = ap.parse_args()

    if a.cmd == "submit":
        text = open(a.input_file).read()
        out = _req("POST", "/v1/tasks/runs", {"input": text, "processor": a.processor})
        print(out["run_id"])
    elif a.cmd == "status":
        out = _req("GET", f"/v1/tasks/runs/{a.run_id}")
        print(out.get("status"))
    elif a.cmd == "result":
        out = _req("GET", f"/v1/tasks/runs/{a.run_id}/result?timeout=280", timeout=300)
        blob = json.dumps(out, ensure_ascii=False, indent=2)
        if a.out:
            open(a.out, "w").write(blob)
            print(f"saved {a.out}")
        else:
            print(blob)
    elif a.cmd == "search":
        body = {
            "objective": a.objective,
            # v1 requires at least one query; fall back to the objective itself
            "search_queries": a.query or [a.objective],
            "advanced_settings": {"max_results": a.max},
        }
        if a.mode:
            body["mode"] = a.mode
        out = _req("POST", "/v1/search", body)
        print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
