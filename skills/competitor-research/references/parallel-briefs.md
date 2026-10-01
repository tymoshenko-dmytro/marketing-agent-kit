# Parallel `ultra` brief templates for company research

Substitution: `{ANCHOR}` = "{COMPANY} ({DOMAIN}), the <city/country> <category> company founded by <founders>" — the full anchor in EVERY brief (protection against namesakes). Writing rules: the parallel-research skill → `references/brief-writing.md`.

Each template below is the list of blocks to cover. Wrap it like this:

```
Research <theme> of {ANCHOR}.

Cover exhaustively:
1. ...

Today is <Month Year>. Cite a source URL for every material claim.
Output: a thorough structured markdown report in English <+ format: tables / timeline>.
```

**t1 — history and pivots:** founding story and founders' backgrounds; the full product timeline with dates (every release and what it added); strategic pivots and changes in how the company describes itself (archive.org snapshots of the homepage by year); open-source vs closed decisions; acquisitions, killed products, deprecations; how the stated vision evolved (interviews, blog).

**t2 — finances and investors:** every round (date, amount, lead, participants, valuation, sources); total raised; board and observers; angels and corporate VCs; revenue / ARR / customer-count signals; headcount and job-posting growth; offices; M&A and IPO rumours; secondary market (Forge / EquityZen — prices and orders); investor theses; fundraising pace vs peers.

**t3 — media map:** who writes about them (outlets, newsletters, analysts, YouTube, podcasts) — specific pieces with dates and angle; founders' talks and their key points; PR narratives by audience; launch coverage; awards and rankings; share of voice vs competitors; events and sponsorships; their own content engine (blog, X, LinkedIn, Discord).

**t4 — partnerships and distribution:** cloud / platform partners and marketplaces; integrations into frameworks and tools (first-party vs community, default status); enterprise platforms and resellers; channel / SI / startup programmes; which partnerships carry real volume vs logo-only; lost or quiet partnerships.

**t5 — customers outside their website:** named customers from news, podcasts, job posts ("we use X"), engineering blogs, builder showcases; for each — company, what it does, which product it uses, use case, scale hints, why they chose it (quotes); migration stories TO and FROM them (with reasons); pilots from the press and their status.

**t6 — team:** founders and executives (titles, backgrounds, dates); the GTM organisation by name; research names and their papers; engineering leadership; headcount and split by function; notable departures; where they hire from; open roles and what they signal; advisors. Format: roster table Name | Title | Function | Background | Source.

**t7 — product and pricing:** full inventory of products / APIs / SDKs with versions and dates; claimed metrics per product (with claim dates); independent benchmarks vs competitors; full pricing (tiers, credits, overage, rate limits, usage limits, commercial rights) and its history (archive.org /pricing); enterprise packaging (SLA, compliance, self-hosting signals); effective rates vs competitors.

**t8 — criticism and risks:** recurring complaints (quality, reliability, docs, support, real-world performance) from Reddit / HN / X / GitHub issues / communities; pricing complaints; deprecations and breaking changes; incident history (status page); lost benchmarks; misuse, safety and legal issues; strategic vulnerabilities from public discussion; what customers who left or chose a competitor say.

**t9 — PR inventory** (deeper than t3, on request): every significant press piece (outlet, tier, date, author, URL, type, angle) — with an explicit tier-1 checklist and "no coverage found"; every team interview (show, date, points); patterns (clusters around events, exclusives / embargoes — who got the scoop on each round, recurring journalists, signs of an agency); press narratives and where they come from (the company vs independent); gaps vs peers; awards.

## Post-processing

`output.content` is sometimes a JSON string with structured fields — keep both the `.json` and the extracted `.md`. When dates conflict between tasks, keep both versions, mark them, and choose by the primary source (tell the synthesis agent this explicitly).
