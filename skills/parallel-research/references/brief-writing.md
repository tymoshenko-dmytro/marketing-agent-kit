# Writing deep-research briefs

A brief is an assignment for an autonomous research engine. It cannot ask a follow-up question, so everything it needs has to be in the text.

## A structure that works

```
<One sentence: research X about Y, with a full entity anchor.>

Cover exhaustively:
1. <Numbered question block — one theme, 3–6 concrete sub-questions.>
2. ...
(5–8 blocks)

Today is <Month Year>. Cite a source URL for every material claim.
Prefer primary sources and dated coverage. Output: a thorough structured
markdown report in English with <tables / timeline / roster — whatever fits>.
```

## Rules learned from production runs

1. **Anchor the entity in every brief.** "Acme Voice (acmevoice.ai), the San Francisco speech-AI company founded by Jane Park and Sam Lee" — not "Acme". Without the anchor the engine mixes in every company with a similar name.
2. **Numbered, decomposed questions beat an open prompt.** Each block is one theme with concrete sub-questions.
3. **State today's date.** Otherwise the engine may present two-year-old coverage as current.
4. **Demand citations explicitly** — "Cite a source URL for every material claim". It changes the output noticeably.
5. **Ask it to report absence.** List the concrete outlets or sources to check and require "report findings, including 'no coverage found'". You get verifiable negatives, not only positives. Example: "Explicitly check and report findings (including 'no coverage found') for: TechCrunch, Forbes, Bloomberg, WSJ, The Information."
6. **Specify the output format** — tables, timeline, roster columns. Deep processors follow format specs well.
7. **Ask for confidence metadata:** the date of each claim, who reported it first, primary or secondary source.
8. **One brief, one theme.** Eight focused briefs outperform one brief that asks everything.
9. **Put a date floor on fast-moving fields.** "Today is …" stops old coverage being presented as current, but not old *advice* being repeated after a new product version made it wrong. For anything that churns — AI models, ad platforms, tooling — add three things:
   - name the **current version** of every product ("Kling 3.0", not "Kling");
   - demand a **publication date** next to every URL;
   - state the floor: "Every claim must rest on a source published this year. Where the only source is older, give its date and say whether it still holds. A report that repeats old advice without dating it is a failed report."

   Then ask for an **obsolescence table**: technique · when it was standard · still valid now? · what replaced it. A separate "what changed this year and what is now obsolete" task makes a good ruler for checking the other reports.

## Worked example — a funding brief

```
Research the complete funding and financial picture of Acme Voice (acmevoice.ai),
the San Francisco speech-AI company founded by Jane Park and Sam Lee.

Cover exhaustively:
1. Every funding round: date, amount, lead investor, all participating
   investors, valuation (reported or rumoured), source articles.
2. Total raised to date; cap-table signals; board members and observers.
3. Notable angel investors and strategic (corporate) investors.
4. Revenue / ARR signals: reported revenue, growth rates, customer counts,
   usage metrics from interviews or press.
5. Headcount growth over time (headcount history, job-posting velocity),
   office locations.
6. Acquisition interest, IPO rumours, secondary-market sales.
7. Investor theses: what did the lead investors publicly say about why they invested?
8. Their fundraising pace compared with named peers: <Peer A>, <Peer B>, <Peer C>.

Today is <Month Year>. Cite a source URL with a date for every material claim.
Output: a thorough structured markdown report in English.
```

## Themed templates for company research

The `competitor-research` skill ships nine ready templates (history and pivots, funding, media map, partnerships, customers in the wild, team roster, product and pricing teardown, criticism and risks, PR inventory) in its `references/parallel-briefs.md`.
