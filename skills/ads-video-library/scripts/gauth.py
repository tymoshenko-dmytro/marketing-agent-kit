#!/usr/bin/env python3
"""One place that answers "who am I to Google" for the publisher.

Order of preference:

1. a service-account key   ~/.config/marketing-agent-kit/google-sa.json
2. a separate user token    ~/.config/marketing-agent-kit/google-user.json

Both paths can be overridden in library.json ("credentials": {"service_account": ...,
"user": ...}). Setup: references/setup.md.

Why a service account first: user tokens expire, and Google's re-check for them can
depend on the network you are on, so a refresh that worked yesterday can ask for a
browser login today. A service-account key never does.

Why a *separate* user token: never reuse the default gcloud credentials file that
other tools (a reporting bot, the GA4 MCP) run on. Re-authenticating it to add Drive
scopes rewrites the token those tools depend on, and a lost scope there is a broken
report nobody notices until morning.
"""
from __future__ import annotations

import json
import pathlib
import sys

KIT = pathlib.Path.home() / ".config" / "marketing-agent-kit"
SA = KIT / "google-sa.json"
USER = KIT / "google-user.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]


def credentials(paths: dict | None = None):
    sa = pathlib.Path((paths or {}).get("service_account", SA)).expanduser()
    user = pathlib.Path((paths or {}).get("user", USER)).expanduser()
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials as UserCreds
        from google.oauth2.service_account import Credentials as SACreds
    except ImportError:
        sys.exit("needs: pip install google-auth requests")

    if sa.exists():
        c = SACreds.from_service_account_file(str(sa), scopes=SCOPES)
        c.refresh(Request())
        return c, {"kind": "service account", "who": json.loads(sa.read_text())["client_email"]}

    if user.exists():
        d = json.loads(user.read_text())
        # no scopes on refresh: a user credential already carries what was granted,
        # and asking for scopes here comes back as invalid_scope
        c = UserCreds(None, refresh_token=d["refresh_token"], client_id=d["client_id"],
                      client_secret=d["client_secret"],
                      token_uri="https://oauth2.googleapis.com/token",
                      quota_project_id=d.get("quota_project_id"))
        c.refresh(Request())
        return c, {"kind": "user oauth", "who": d.get("account", "unknown")}

    sys.exit(f"No Google credentials. Expected one of:\n  {sa}\n  {user}\n"
             "See references/setup.md — or set \"storage\": \"local\" in library.json "
             "to publish without Google.")


def headers(creds):
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
