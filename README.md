# Marketing Agent Kit

Skills, a critic agent and connection guides for doing marketing work with [Claude Code](https://code.claude.com): competitor research, ad-library teardowns, funnel screenshots, SEO data, GA4 reports, image generation, motion cards from code, an ad-video library with review pages, and copy that a stranger understands in one read.

Built from real work at a B2B SaaS growth team in 2026, then stripped of everything company-specific. [Русская версия →](README.ru.md)

## What's inside

### Skills

| Skill | What it does | Needs |
|---|---|---|
| [`competitor-research`](skills/competitor-research/SKILL.md) | Full competitor dossier by domain: site, customers, pricing, community, ads, SEO, team, PR — ~17 subagents + deep research → knowledge base and HTML report | Parallel, SearchApi, Ahrefs |
| [`parallel-research`](skills/parallel-research/SKILL.md) | Deep web research with citations (minutes to an hour) and fast sourced search, plus a guide to writing briefs | Parallel |
| [`ads-parser`](skills/ads-parser/SKILL.md) | A company's ads from LinkedIn, Google and Meta ad libraries — exact texts, dates, disclosed impressions, links | SearchApi |
| [`ahrefs-seo`](skills/ahrefs-seo/SKILL.md) | Organic keywords, top pages, backlinks, DR, volumes — with a unit-cost model so pulls don't burn the plan | Ahrefs (paid) |
| [`ga4-reports`](skills/ga4-reports/SKILL.md) | GA4 reports, period comparisons and funnels, the reporting traps, and a REST fallback when the MCP hangs | Google login |
| [`image-gen`](skills/image-gen/SKILL.md) | OpenAI GPT Image generation and editing via a stdlib CLI, quality-by-purpose, art-direction rules | OpenAI key |
| [`funnel-screenshots`](skills/funnel-screenshots/SKILL.md) | Walks a public quiz / onboarding funnel in an emulated iPhone and captures every screen as a retina screenshot, plus the paywall and discount modals — never types payment data | Python, Playwright (installs itself) |
| [`motion-card`](skills/motion-card/SKILL.md) | End cards, title cards, animated CTAs and logo stings built from HTML/CSS/GSAP with HyperFrames, voiced with ElevenLabs; audio-first workflow with a speech-vs-script check | Node 22+, FFmpeg, ElevenLabs |
| [`ads-video-library`](skills/ads-video-library/SKILL.md) | Canonical names, poster frames (baked into frame 0), contact sheets, Month / Language / Type storage (local or Google Drive), CSV catalogue, and a `gallery.html` review page | FFmpeg |
| [`plain-copy`](skills/plain-copy/SKILL.md) | Rules for copy that a stranger understands and that doesn't sound machine-written, with before / after patterns | — |
| [`connect`](skills/connect/SKILL.md) | Sets up keys, Google login and MCP servers step by step; `doctor` tests every key with a free request | — |

### Agent

| Agent | What it does |
|---|---|
| [`copy-critic`](agents/copy-critic.md) | Reads ad copy like a stranger scrolling a feed; returns a verdict and a rewrite per line. [How to train your own on your corrections →](docs/train-your-critic.md) |

### Connections

One guide per service — access, cost, setup, check, safety, gotchas: [connections/](connections/README.md)

Google Ads · GA4 · Ahrefs · Stripe · BigQuery · Playwright · Parallel · SearchApi · ElevenLabs · OpenAI Images · HyperFrames · Higgsfield

## Read before you install

**Don't install skills blindly — this kit included.** Every installed skill adds its description to every conversation and competes for Claude's attention, and a skill written for someone else's workflow quietly does things their way. Treat these as templates:

1. Read the `SKILL.md` of the ones you want. They're short.
2. Install only what you'll use this month.
3. Each skill ends with **"Adapt it"** — do that part. The skills get good when they hold *your* corrections: your report rules, your funnel events, your copy patterns, your brand.

## Install

**As a plugin** (Claude Code terminal or desktop app):

```
/plugin marketplace add tymoshenko-dmytro/marketing-agent-kit
/plugin install marketing-agent-kit@marketing-agent-kit
```

Skills are then available as `/marketing-agent-kit:<skill>`; Claude also picks them up automatically from what you ask.

**Or copy what you want:**

```bash
git clone https://github.com/tymoshenko-dmytro/marketing-agent-kit.git
cp -R marketing-agent-kit/skills/ads-parser ~/.claude/skills/        # one skill, all projects
cp marketing-agent-kit/agents/copy-critic.md ~/.claude/agents/       # the critic
```

Use `<project>/.claude/skills/` instead of `~/.claude/skills/` to scope a skill to one project.

## First run

Ask Claude: **"Set up the kit for competitor research"** (or whatever you want to do). The `connect` skill creates a private keys file, walks you through getting each key, registers MCP servers and runs a health check:

```bash
python3 skills/connect/scripts/kit.py init           # ~/.config/marketing-agent-kit/.env, chmod 600
python3 skills/connect/scripts/kit.py doctor --live  # what works, what's missing
```

## Keys and privacy

- All keys live in **one file outside any repository**: `~/.config/marketing-agent-kit/.env` (template: [.env.example](.env.example)). You type them in yourself.
- **Never paste keys into a chat** — chats are saved to disk. The scripts read the file and never print keys.
- Prefer OAuth where a service offers it, read-only permissions, and spending caps. Each connection guide says how.
- Research outputs (`raw/`, `dist/`, catalogues) are in `.gitignore` — keep client data out of your forks.

## Requirements

- Python 3.9+ (scripts use the standard library only; Google Drive mode of `ads-video-library` needs `pip install google-auth requests`)
- FFmpeg for `ads-video-library` and `motion-card`; Node.js 18+ for Playwright MCP, 22+ for HyperFrames; `gcloud` + `pipx` for Google services; ~400 MB for `funnel-screenshots` (its setup installs Playwright and Chromium)

## What else I use (not included)

Good work by others. Read before installing, same rule as above.

| What | Why |
|---|---|
| [Marketing Skills](https://github.com/coreyhaines31/marketingskills) by Corey Haines (MIT) | `product-marketing` creates a product-context file the other skills (and `copy-critic`) read; also CRO, copywriting, SEO audit, emails, A/B tests |
| Anthropic document skills (`docx`, `pdf`, `pptx`, `xlsx`) | decks, reports and spreadsheets as files — available in Claude apps |
| [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) | videos rendered from HTML/CSS — pairs with `ads-video-library` |
| [Higgsfield skills](https://github.com/higgsfield-ai/skills) (MIT) | generative video and image ads |
| [/brag](https://github.com/latent-spaces/brag) (MIT) | launch videos of what you built; inspired the poster / frame-0 step here |
| [Impeccable](https://github.com/pbakaus/impeccable) | design review commands (audit, polish, critique) for landing pages |
| [Humanizer](https://github.com/blader/humanizer) (MIT) | removing AI-writing patterns from long texts |

## Credits

- Poster selection and the frame-0 technique in `ads-video-library` are adapted from [/brag](https://github.com/latent-spaces/brag) by Shunit Haviv Hakimi (MIT).
- Connection facts checked against vendor documentation on 2026-10-01.

## License

[MIT](LICENSE) © 2026 Dmytro Tymoshenko · [LinkedIn](https://www.linkedin.com/in/tymoshenko-dmytro)
