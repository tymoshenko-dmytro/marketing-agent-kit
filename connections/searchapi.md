# SearchApi.io

**What it gives you:** structured data from search engines and the public ad libraries — LinkedIn Ad Library, Google Ads Transparency Center, Meta Ad Library (and TikTok via the MCP).
**Used by:** `ads-parser`, `competitor-research`
**Access:** API key (`SEARCHAPI_KEY`), or OAuth for the MCP server.
**Cost:** 100 free requests to start, no card. Paid plans from $40 for 10,000 requests. Only successful (HTTP 200) requests are billed.
**Setup time:** ~3 minutes

## 1. Get a key

1. Sign up at <https://www.searchapi.io>.
2. Copy the API key from the dashboard.
3. Put it into the keys file: `SEARCHAPI_KEY=...` (`kit.py open`).

## 2. Connect

The `ads-parser` script sends the key in an `Authorization: Bearer` header — nothing else to set up.

Optional MCP server (each tool call counts as one request):

```bash
python3 skills/connect/scripts/kit.py mcp add searchapi          # sends the key as X-MCP-Token
python3 skills/connect/scripts/kit.py mcp add searchapi --oauth  # or sign in with /mcp instead
#   = claude mcp add --scope user --transport http searchapi https://www.searchapi.io/mcp
```

## 3. Check

```bash
python3 skills/connect/scripts/kit.py doctor --live    # SEARCHAPI_KEY · accepted, remaining credits: N
```

Then ask Claude: *"Use ads-parser to collect the Google ads of hubspot.com."*

## Engines the kit uses

| Engine | Gives |
|---|---|
| `linkedin_ad_library` | LinkedIn ads by keyword or advertiser |
| `linkedin_ad_library_ad_details` | one ad: impressions, run dates, targeting (EU ads only) |
| `google_ads_transparency_center_advertiser_search` | find a Google advertiser id |
| `google_ads_transparency_center` | an advertiser's creatives |
| `meta_ad_library_page_search` | find a Facebook / Instagram page id |
| `meta_ad_library` | ads by keyword or page |
| `meta_ad_library_page_info` | confirm a page's identity |

## Gotchas

- **Send the key in a header, not the URL.** `api_key=` in a URL ends up in logs and shell history. The kit's script uses the header; the MCP takes `X-MCP-Token`.
- LinkedIn discloses impressions, run dates and targeting only for ads shown in the EU.
- Meta sorts by impressions and returns only active ads by default.
- Meta responses have spend fields; in practice they are filled for political and social-issue ads. Don't estimate commercial budgets from them.
- Watch the credit counter (`doctor --live` shows it). A full competitor run uses a few dozen requests.

## Links

- Docs: <https://www.searchapi.io/docs> · Pricing: <https://www.searchapi.io/pricing>
- MCP: <https://www.searchapi.io/integrations/mcp>

*Checked 2026-10-01.*
