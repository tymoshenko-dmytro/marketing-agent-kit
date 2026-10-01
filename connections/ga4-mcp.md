# Google Analytics 4 MCP

**What it gives you:** GA4 reports inside Claude — traffic, sources, conversions, funnels, realtime.
**Used by:** `ga4-reports`
**Access:** your Google account, through a `gcloud` login (no API key). The server is **read-only**.
**Cost:** free; limited by GA4 quotas (standard property: 200k tokens a day, 40k an hour, 10 concurrent requests).
**Setup time:** 15–20 minutes the first time — most of it is the Google Cloud console.

This login also serves Google Ads and BigQuery. If you'll use them, read "One login for all Google services" below before step 3.

## 1. Install the tools

```bash
brew install --cask google-cloud-sdk     # gcloud  (or: https://cloud.google.com/sdk/docs/install)
brew install pipx && pipx ensurepath     # pipx runs the MCP server
```

## 2. Prepare a Google Cloud project (one time)

1. Open <https://console.cloud.google.com> and create a project (or pick one). Note its **project id**.
2. Enable two APIs in it: **Google Analytics Admin API** and **Google Analytics Data API** (APIs & Services → Library → search → Enable).
3. **Create your own OAuth client** — gcloud's built-in one is often blocked ("This app is blocked"):
   - APIs & Services → OAuth consent screen → set it up (Internal if you're on Google Workspace, otherwise External and add yourself as a test user).
   - APIs & Services → Credentials → Create credentials → OAuth client ID → **Desktop app** → Create → **Download JSON**.
   - Save it as `~/.config/gcloud/client_secret.json`.
4. Make sure your Google account has at least **Viewer** on the GA4 property (GA4 → Admin → Property access management).

## 3. Log in

```bash
gcloud auth application-default login \
  --client-id-file="$HOME/.config/gcloud/client_secret.json" \
  --scopes="https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform"
```

A browser opens; sign in with the account that has GA4 access. This writes `~/.config/gcloud/application_default_credentials.json`.

Put your project id into the keys file: `GOOGLE_CLOUD_PROJECT=<project id>`.

## 4. Register the MCP server

```bash
python3 skills/connect/scripts/kit.py mcp add ga4
#   = claude mcp add --scope user ga4 -e GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud/application_default_credentials.json \
#       -e GOOGLE_PROJECT_ID=<project id> -- pipx run --spec "analytics-mcp>=0.7.0" analytics-mcp
```

Restart the session. Tools: `get_account_summaries`, `get_property_details`, `run_report`, `run_realtime_report`, `run_funnel_report`, `run_conversions_report`, `get_custom_dimensions_and_metrics`, `list_google_ads_links`, `list_property_annotations`.

## 5. Check

Ask Claude: *"List my GA4 properties."* — then *"Sessions by source for the last 7 days."*
Without the MCP: `python3 skills/ga4-reports/scripts/ga4.py --list-properties`.

## One login for all Google services

GA4, Google Ads and BigQuery all read the same credentials file, and **every new `gcloud auth application-default login` replaces it**. Logging in again with only the GA4 scope silently breaks Google Ads. Log in once with every scope you need:

```bash
gcloud auth application-default login \
  --client-id-file="$HOME/.config/gcloud/client_secret.json" \
  --scopes="https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/bigquery.readonly,https://www.googleapis.com/auth/cloud-platform"
```

`kit.py doctor` shows which scopes your current login has.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "This app is blocked" in the browser | You logged in without `--client-id-file`. Use your own OAuth client (step 2.3). |
| `Reauthentication is needed`, `invalid_grant`, 401 | The login expired. Repeat step 3 (the agent can run it in the background — you sign in in the browser). |
| `403 PERMISSION_DENIED` | Your account has no access to that property. |
| Server "Failed to connect" right after start | Run the server by hand to see the error: `pipx run --spec "analytics-mcp>=0.7.0" analytics-mcp`. Two known causes: **pipx refuses an old `uv`** ("pipx needs uv>=0.9.17" → `uv self update`), and **a stale cached version** that crashes after the MCP SDK 2.0 change (pin `>=0.7.0` as above, or `pipx run --no-cache analytics-mcp`). Then reconnect with `/mcp`. |
| `run_report` times out (504) while other tools work | Don't debug — use the REST fallback in `ga4-reports` (`scripts/ga4.py`). Same login, 1–2 s per query. |
| Desktop app doesn't see the server | Quit the app fully (Cmd+Q) and reopen; check `claude mcp list`. |

## Links

- Official server: <https://github.com/googleanalytics/google-analytics-mcp> · Guide: <https://developers.google.com/analytics/devguides/MCP>
- Quotas: <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas>
- Login troubleshooting: <https://cloud.google.com/docs/authentication/troubleshoot-adc>

*Checked 2026-10-01.*
