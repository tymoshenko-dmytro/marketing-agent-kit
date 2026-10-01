# BigQuery

**What it gives you:** SQL over large data — the GA4 BigQuery export (every event, user-level), backend events, ad cost exports — joined in one query. This is where "which channel brings paying users" gets answered.
**Access:** Google account. Two ways: the official remote MCP server, or plain SQL over REST with your `gcloud` login.
**Cost:** no charge for MCP itself; queries are billed to your project at on-demand rates ($6.25 per TiB scanned, first 1 TiB a month free). The BigQuery sandbox works without billing.
**Setup time:** REST: 5 minutes after the GA4 login. MCP: ~20 minutes.

## Option A — SQL over REST (simplest)

Uses the same `gcloud` login as GA4 (add the `bigquery.readonly` scope — see [ga4-mcp.md](ga4-mcp.md#one-login-for-all-google-services)). No server to register: the agent runs queries with `curl`.

```bash
curl -s -X POST "https://bigquery.googleapis.com/bigquery/v2/projects/<PROJECT_ID>/queries" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT event_name, COUNT(*) n FROM `<PROJECT_ID>.analytics_<PROPERTY_ID>.events_*` WHERE _TABLE_SUFFIX >= FORMAT_DATE(\"%Y%m%d\", DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) GROUP BY 1 ORDER BY 2 DESC LIMIT 20", "useLegacySql": false}'
```

- Always send `"useLegacySql": false` — the default is legacy SQL.
- `timeoutMs` defaults to 10 s; long queries return a job id to poll. Responses cap at 10 MB.
- With the `bigquery.readonly` scope the token can't write anything.

## Option B — the remote MCP server

Endpoint `https://bigquery.googleapis.com/mcp` (generally available since April 2026). It switches on automatically when the BigQuery API is enabled in the project.

1. Grant your account `roles/mcp.toolUser`, `roles/bigquery.jobUser`, `roles/bigquery.dataViewer` on the project.
2. Google's MCP servers need **your own OAuth client** (no dynamic registration). Create a **Web application** OAuth client in the Cloud console.
   - For a **claude.ai custom connector**: redirect URI `https://claude.ai/api/mcp/auth_callback`, then Settings → Connectors → Add custom connector → URL above, client id and secret under Advanced settings. This is the path Google documents.
   - For the **Claude Code CLI**: redirect URI `http://localhost:8080/callback`, then
     ```bash
     claude mcp add --transport http --scope user --client-id <CLIENT_ID> --client-secret \
       --callback-port 8080 bigquery https://bigquery.googleapis.com/mcp
     ```
     (it prompts for the secret), then `/mcp` → bigquery → Authenticate. Built from Claude Code's generic OAuth options; Google doesn't document this path yet.

Tools: `list_dataset_ids`, `get_dataset_info`, `list_table_ids`, `get_table_info`, `execute_sql_readonly`, `get_query_results`, `get_job` (read-only) — plus `execute_sql` and `cancel_job`, which can change things.

## Safety: keep it read-only

- Give the agent's account only **Data Viewer + Job User**, so DDL / DML fails on permissions.
- Deny the write tools in Claude Code settings: `mcp__bigquery__execute_sql`, `mcp__bigquery__cancel_job` (see [README](README.md#keep-agents-read-only)).
- For a whole organisation: an IAM deny policy on `mcp.googleapis.com/tools.call` where the tool isn't read-only (Google documents the condition `mcp.googleapis.com/tool.isReadOnly`).
- Watch scanned bytes: a `SELECT *` over months of GA4 export is the expensive mistake. Ask for a dry run first on big tables.

## Gotchas

- MCP queries are capped at 3 minutes and 3,000 rows; aggregate in SQL.
- The MCP scope is full `auth/bigquery` — the read-only limit has to come from IAM and deny rules.
- The GA4 export lags 1–2 days and has no intraday table unless you enabled streaming export. Yesterday's numbers in BigQuery are often incomplete.
- Google Drive–backed external tables aren't supported through the MCP.

## Links

- MCP guide: <https://cloud.google.com/bigquery/docs/use-bigquery-mcp> · Reference: <https://cloud.google.com/bigquery/docs/reference/mcp>
- Connecting AI apps: <https://cloud.google.com/mcp/configure-mcp-ai-application>
- IAM controls: <https://cloud.google.com/mcp/control-mcp-use-iam>
- REST `jobs.query`: <https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query> · Pricing: <https://cloud.google.com/bigquery/pricing>

*Checked 2026-10-01.*
