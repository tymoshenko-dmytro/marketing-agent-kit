# Parallel.ai

**What it gives you:** web research that reads hundreds to thousands of pages and returns a cited report; plus fast sourced web search.
**Used by:** `parallel-research`, `competitor-research`
**Access:** API key (`PARALLEL_API_KEY`). The Search MCP also works without a key.
**Cost:** pay per task run; free credits on signup (up to $80) and $5 a month. Failed runs aren't billed.
**Setup time:** ~5 minutes

## Prices (per run, autumn 2026)

| Processor | Price | | Processor | Price |
|---|---|---|---|---|
| lite | $0.005 | | pro | $0.10 |
| base | $0.01 | | ultra | $0.30 |
| core | $0.025 | | ultra2x | $0.60 |
| core2x | $0.05 | | ultra4x / ultra8x | $1.20 / $2.40 |

Search: $0.001–0.005 per request (10 results).

## 1. Get a key

1. Sign up at <https://platform.parallel.ai>.
2. Create an API key.
3. Put it into the keys file: `PARALLEL_API_KEY=...` (`kit.py open`).

## 2. Connect

The skills call the API directly — the key in the keys file is all they need.

Optional MCP servers, if you want Parallel inside any chat without the skill:

```bash
# Search MCP — free, works without a key (add the key for higher limits)
python3 skills/connect/scripts/kit.py mcp add parallel-search
#   = claude mcp add --scope user --transport http parallel-search https://search.parallel.ai/mcp

# Task MCP — deep research from chat; sign in with /mcp, or the kit sends your key
python3 skills/connect/scripts/kit.py mcp add parallel-task
#   = claude mcp add --scope user --transport http parallel-task https://task-mcp.parallel.ai/mcp
```

## 3. Check

```bash
python3 skills/connect/scripts/kit.py doctor --live      # PARALLEL_API_KEY · accepted
```

Then ask Claude: *"Use parallel-research to find what changed in Notion's pricing this year."*

## Safety

- An agent can start `ultra8x` runs at $2.40 each. Give agents their own key, and watch usage in the dashboard for the first weeks.
- The API reads the public web only; it never logs in anywhere.

## Gotchas

- The Search API moved from `/v1beta/search` to `/v1/search` with a new request format (`search_queries` required, options in `advanced_settings`). The kit's script uses v1.
- Task statuses: `queued`, `action_required`, `running`, `completed`, `failed`, `cancelling`, `cancelled`.
- The result endpoint blocks until the run finishes (408 if it's still running at the timeout). Poll the status instead of waiting on it.
- Keep the raw `result.json`: per-claim citations live in its `basis` array, not in the extracted text.
- Rate limits: Search 600/min, Tasks 2,000/min.

## Links

- Docs: <https://docs.parallel.ai> · Pricing: <https://parallel.ai/pricing>
- MCP: <https://docs.parallel.ai/integrations/mcp/quickstart>
- Search v1 migration: <https://docs.parallel.ai/search/search-migration-guide>

*Checked 2026-10-01.*
