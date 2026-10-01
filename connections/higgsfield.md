# Higgsfield

**What it gives you:** generative images and video from many models in one place (text-to-video, image-to-video, product shots, UGC-style ads, character consistency), driven by the agent.
**Access:** browser login (OAuth). The separate REST API uses a key id + secret.
**Cost:** credit-based subscription plans; the API is pay-as-you-go from a balance. **Every generation through the CLI or MCP deducts credits — even for models your plan calls "Unlimited".**
**Setup time:** ~5 minutes

## 1. Install the skills and the CLI

```bash
# skills (pick one)
npx skills add higgsfield-ai/skills
claude plugin marketplace add higgsfield-ai/skills && claude plugin install higgsfield@higgsfield

# CLI (pick one)
brew install higgsfield-ai/tap/higgsfield
npm install -g @higgsfield/cli
```

The official skill installs the CLI itself with `curl … | sh` (into `/usr/local/bin`, with sudo) if it's missing — install it yourself first if you'd rather control that.

## 2. Log in and check

```bash
higgsfield auth login       # opens a browser
higgsfield account status   # "<email> — <plan> plan, <N> credits"
```

Login tokens are short-lived; re-run `auth login` when the CLI says so.

**MCP instead of the CLI** (OAuth; the only official URL):

```bash
python3 skills/connect/scripts/kit.py mcp add higgsfield
#   = claude mcp add --scope user --transport http higgsfield https://mcp.higgsfield.ai/mcp
```

Higgsfield recommends CLI + skills for Claude Code; the MCP suits claude.ai and the desktop chat.

## Safety — this is where money goes

- **Ask for the cost before generating.** The official skill is told not to estimate cost unless asked, so add the rule yourself (in your CLAUDE.md): "Before any Higgsfield generation, run `higgsfield generate cost …` and show me the price."
- Don't set Higgsfield tools to "Always allow".
- In practice most spend goes on model tests and alternate versions, not on the final video. Decide the model on a short test, then generate.
- Download outputs: the API keeps them for at least 7 days, not forever.
- `website publish` / `website contest` make a site public.

## Gotchas

- Upstream skills update often (new default models); update with the same command you installed with.
- Credit packs expire after 90 days; API credits after a year. Failed and NSFW-blocked requests are refunded.
- Higgsfield is for generated footage of people, scenes and products. For exact text, logos and offers, render with code (HyperFrames) — cheaper and repeatable.

## Links

- Skills: <https://github.com/higgsfield-ai/skills> · CLI: <https://github.com/higgsfield-ai/cli>
- MCP: <https://higgsfield.ai/mcp> · API docs: <https://docs.higgsfield.ai>

*Checked 2026-10-01.*
