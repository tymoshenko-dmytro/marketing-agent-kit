# Google Ads MCP

**What it gives you:** read-only access to your Google Ads accounts — campaigns, ad groups, keywords, search terms, spend, conversions, change history — through GAQL queries.
**Used by:** ad-hoc analysis ("why did CPA jump?", "which search terms waste money?"); pairs with `ga4-reports`.
**Access:** your Google account through a `gcloud` login. **No developer token any more** — Google sunset them on 2026-09-09; access is now tied to a Google Cloud project.
**Cost:** free.
**Setup time:** ~20 minutes (most of it in the Cloud console).

## Access levels

| Level | Operations per day | Notes |
|---|---|---|
| Test | 15,000 | test accounts only (granted automatically) |
| Explorer | 2,880 | real accounts — enough for analysis |
| Basic | 15,000 | needs brand verification, then an automated review |
| Standard | no daily cap | per-service limits apply |

Explorer blocks Keyword Planner, Audience Insights, Reach Planner, billing and user management.

## 1. Prepare the Cloud project

Use the same project and OAuth client as for GA4 (see [ga4-mcp.md](ga4-mcp.md), step 2). Then:

1. Enable the **Google Ads API** in the project.
2. Cloud console → Google Ads API → Overview → **Upgrade access level → Explorer**. You need Owner, Editor, Quota Administrator or Service Usage Admin on the project. Explorer is often approved automatically.
3. The access level belongs to the project that owns the OAuth client — create the client in this same project.

Free-trial billing on the project makes Explorer / Basic applications fail; switch the project to paid billing (the API itself stays free).

## 2. Log in (with the Ads scope)

```bash
gcloud auth application-default login \
  --client-id-file="$HOME/.config/gcloud/client_secret.json" \
  --scopes="https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform"
```

If you also use GA4 or BigQuery, use the combined login from [ga4-mcp.md](ga4-mcp.md#one-login-for-all-google-services) — each login replaces the previous one.

Keys file: `GOOGLE_CLOUD_PROJECT=<project id>`; if you access client accounts through a manager (MCC) account, also `GOOGLE_ADS_LOGIN_CUSTOMER_ID=<manager id, digits only>`.

## 3. Register the MCP server

```bash
python3 skills/connect/scripts/kit.py mcp add google-ads
#   = claude mcp add --scope user google-ads -e GOOGLE_APPLICATION_CREDENTIALS=<adc json> -e GOOGLE_PROJECT_ID=<project id> \
#       -e GOOGLE_CLOUD_PROJECT=<project id> [-e GOOGLE_ADS_LOGIN_CUSTOMER_ID=<mcc>] \
#       -- pipx run --spec google-ads-mcp==0.0.4 google-ads-mcp
```

Pinning the version matters: older installs still ask for a developer token.

## 4. Check

Ask Claude: *"List my accessible Google Ads accounts, then spend and conversions by campaign for the last 7 days."*

Tools (current names): `customers_list_accessible_customers`, `search_search` (GAQL), `metadata_get_resource_metadata`.

## Safety

The server is **read-only**: it can't change bids, pause campaigns or create assets. The `adwords` scope itself is full access, so the limit lives in the server — don't reuse this login in other tools that write.

## Gotchas

- Google's README still shows a developer-token step; the developer guide (newer) doesn't. Follow the guide.
- gcloud's built-in OAuth client gets "This app is blocked" with the Ads scope — use your own client.
- `CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION` (or `ACTION_NOT_PERMITTED` on older API versions): the project still has Test access only. Apply for Explorer.
- Some projects upgraded right after the change still get `AUTHORIZATION_ERROR`; applying from a fresh project helps.
- Google Ads and GA4 disagree by ±1–2 conversions a day: Ads attributes to the click date, GA4 to the event date.

## Links

- Developer guide: <https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server>
- Repo: <https://github.com/googleads/google-ads-mcp>
- Developer token sunset: <https://developers.google.com/google-ads/api/docs/api-policy/developer-token>
- Access levels: <https://developers.google.com/google-ads/api/docs/api-policy/access-levels>

*Checked 2026-10-01.*
