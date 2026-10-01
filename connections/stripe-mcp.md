# Stripe MCP

**What it gives you:** revenue, subscriptions, trials, invoices, failed payments, customers — read straight from Stripe inside Claude.
**Access:** OAuth (recommended for people) or a restricted key with the **Agent** tag (for unattended agents).
**Cost:** no MCP price stated by Stripe; SQL through `stripe_analytics` needs a Stripe Sigma subscription.
**Setup time:** ~5 minutes

> **From 2026-10-31 Stripe MCP rejects full secret keys and restricted keys without the Agent tag** (401). Old `sk_live_…` / `rk_live_…` setups stop working that day.

## 1. Connect — OAuth (recommended)

Stripe's own route installs the server plus Stripe's skills:

```bash
claude plugin install stripe@claude-plugins-official
```

Or just the server:

```bash
python3 skills/connect/scripts/kit.py mcp add stripe
#   = claude mcp add --scope user --transport http stripe https://mcp.stripe.com
```

Then `/mcp` → stripe → Authenticate. **In Stripe's consent screen grant Read only.** Test against a sandbox first.

**Desktop app / claude.ai:** Settings → Connectors → Stripe.

## 1b. Connect — with an Agent key

For agents that run without you:

1. Dashboard → Developers → API keys → **Create restricted key**.
2. Purpose: **"Authorizing agent access to your account"**.
3. Set every resource to **None** or **Read**. For analytics: Data → Metrics: Read, Reporting: Read.
4. Confirm with two-factor and copy the key (live keys are shown once). It carries an **Agent** badge.
5. Keys file: `STRIPE_AGENT_KEY=...`, then `python3 skills/connect/scripts/kit.py mcp add stripe --key`.

Stripe advises against putting the key on a command line; the kit passes it straight to `claude mcp add` without printing it. In a shared `.mcp.json` use `"Authorization": "Bearer ${STRIPE_AGENT_KEY}"` instead of the key.

## 2. Check

Ask Claude: *"How many active subscriptions do we have, and how many trials started last week?"*

## Safety

- `stripe_api_write` can create refunds and payment links, cancel subscriptions, void invoices. Deny it unless you need it:
  ```json
  {"permissions": {"deny": ["mcp__stripe__stripe_api_write"]}}
  ```
  (Plugin installs name it `mcp__plugin_stripe_stripe__stripe_api_write` — check with `/mcp`.)
- With OAuth, Stripe asks a human to approve refunds and outbound payments through a link (expires in 24 h). With Agent keys the API returns `approval_required` (expires in 14 days).
- Live and sandbox MCP access can be switched off separately: Dashboard → Settings → MCP and CLI access.
- Stripe warns about prompt injection when its MCP runs alongside other servers that read untrusted content (web pages, emails).

## Gotchas

- `npx @stripe/mcp` still exists but only relays to `mcp.stripe.com`; its `--tools` flag was removed — permissions come from the key or the OAuth grant.
- Connected accounts need a key plus a `Stripe-Account: acct_…` header; OAuth doesn't cover them.
- Classifying payments: `billing_reason` tells a first payment (`subscription_create`) from a renewal (`subscription_cycle`) and a plan change (`subscription_update`). Early trial conversions often show up as `subscription_update`.

## Links

- <https://docs.stripe.com/mcp> · Agent keys: <https://docs.stripe.com/keys#agent-keys>
- Plugin: <https://docs.stripe.com/agents/plugin> · Approvals: <https://docs.stripe.com/account/approvals>

*Checked 2026-10-01.*
