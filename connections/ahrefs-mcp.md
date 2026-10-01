# Ahrefs MCP

**What it gives you:** Ahrefs data inside Claude — organic keywords, top pages, backlinks, Domain Rating, traffic history, keyword volumes, SERPs.
**Used by:** `ahrefs-seo`, `competitor-research`
**Access:** OAuth (recommended) or an MCP key (`AHREFS_MCP_KEY`).
**Cost:** needs a paid Ahrefs plan, **Lite or higher**. No extra charge for MCP; calls spend API units from the plan.
**Setup time:** ~5 minutes

| Plan | Price | API units / month |
|---|---|---|
| Lite | $129/mo | 200k |
| Standard | $249/mo | 800k |
| Advanced | $449/mo | 2M |
| Enterprise | $1,499/mo (annual) | 4M+ |

Starter and Free plans have no MCP access. Units are shared between MCP, API v3 and Ahrefs Connect.

## 1. Connect — OAuth (recommended)

```bash
python3 skills/connect/scripts/kit.py mcp add ahrefs --oauth
#   = claude mcp add --scope user --transport http ahrefs https://api.ahrefs.com/mcp/mcp
```

Then in Claude Code: `/mcp` → ahrefs → Authenticate → pick the workspace → Allow. Ahrefs creates a dedicated MCP key for this connection; no key is stored on your machine.

**Desktop app / claude.ai:** Settings → Connectors → search "Ahrefs" → Connect.

## 1b. Connect — with an MCP key

1. Ahrefs → Account settings → API keys → **Generate MCP key**.
2. Put it into the keys file: `AHREFS_MCP_KEY=...`
3. `python3 skills/connect/scripts/kit.py mcp add ahrefs` — sends it as `Authorization: Bearer`.

To load fewer tools, append `?tools=essentials` to the URL.

## 2. Check

In Claude: *"Use ahrefs-seo: Domain Rating and top 10 organic pages of example.com."* The first call should be the free `subscription-info-limits-and-usage`.

## Safety

- **Set a monthly unit cap on the key** (Account settings → API keys). An agent pulling raw backlinks can burn thousands of units in one call.
- The tools behave as lookups, but Ahrefs doesn't document the MCP as read-only. Keep an eye on tool calls the first time.

## Gotchas

- **Don't write your own scripts against the MCP endpoint.** Ahrefs' terms say custom scripts, bridges and standalone JSON-RPC clients calling the MCP endpoint are not permitted. For scripted pulls use API v3 with an API v3 key (Enterprise) — the `ahrefs-seo` skill has `scripts/ahrefs_api.py` for that.
- MCP keys and API v3 keys are not interchangeable — the wrong one returns 401.
- Each call costs at least 50 units: cost = max(50, per-row cost × rows). Some fields cost 5–10 units per row. Details: `skills/ahrefs-seo/references/unit-costs.md`.
- Money values come back in USD cents.
- Paid-traffic and ad-cost estimates are unreliable — don't put them in reports.

## Links

- MCP docs: <https://docs.ahrefs.com/en/mcp/docs/introduction> (Claude Code page: `/claude-code`)
- Units: <https://docs.ahrefs.com/en/api/docs/limits-consumption>
- Pricing: <https://ahrefs.com/pricing> · Keys: <https://app.ahrefs.com/account/api-keys>

*Checked 2026-10-01.*
