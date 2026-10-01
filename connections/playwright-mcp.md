# Playwright MCP

**What it gives you:** a real browser the agent drives — open pages, click, fill forms, take screenshots, read rendered content. Useful for checking landing pages, walking competitor funnels, capturing pages that need JavaScript.
**Access:** none — a local program.
**Cost:** free (open-source npm package).
**Needs:** Node.js 18+.
**Setup time:** ~2 minutes

## Do you need it?

Claude Code already has two browsers:

| Browser | Best for |
|---|---|
| Desktop app **Browser pane** (Cmd+Shift+B) | checking your own site and dev servers; clean profile |
| **Claude in Chrome** (extension) | acting on sites where you're already logged in; needs a paid plan and claude.ai sign-in |
| **Playwright MCP** | headless runs, Firefox / WebKit, scripted sessions, API-key auth, parallel isolated browsers |

The `funnel-screenshots` skill doesn't need this MCP: it installs its own Playwright (Python) and creates the browser context at DPR 3. Screenshots taken through the MCP are DPR 1 and can't be made retina afterwards.

## Connect

```bash
python3 skills/connect/scripts/kit.py mcp add playwright
#   = claude mcp add --scope user playwright -- npx @playwright/mcp@latest \
#       --user-data-dir ~/.config/marketing-agent-kit/playwright-profile
```

Useful flags (add after `@latest`): `--headless`, `--browser chrome|firefox|webkit|msedge`, `--isolated` (in-memory profile), `--storage-state <file>` (load saved cookies into an isolated session), `--caps vision,pdf`, `--allowed-origins <list>`.

## Check

Ask Claude: *"Open example.com with Playwright and take a screenshot."*

## Safety

- **A dedicated profile folder, never your main browser profile.** The kit's command uses its own folder, so logins you make there stay there.
- Playwright MCP is not a security boundary, and neither are the allowed / blocked origin lists. Don't point it at accounts you can't afford an agent to click around in.
- File access is limited to the workspace unless you pass `--allow-unrestricted-file-access` (don't).

## Gotchas

- The browser window is visible by default; pass `--headless` for background runs.
- Pass `--user-data-dir` explicitly — the docs disagree on whether the default profile persists.
- One profile can be used by one browser at a time. Parallel agents need separate `--user-data-dir` folders or `--isolated`.
- For coding agents the Playwright team suggests their CLI plus skills uses fewer tokens than the MCP; for marketing tasks the MCP is simpler.

## Links

- <https://github.com/microsoft/playwright-mcp> · npm: `@playwright/mcp`

*Checked 2026-10-01.*
