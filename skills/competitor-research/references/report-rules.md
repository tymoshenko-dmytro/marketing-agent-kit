# Style contract for research reports

Paste this file verbatim into the prompt of every agent that writes report text. Breaking any rule means a rewrite.

These rules come from real review rounds: each one is a correction a reader made to a draft. Add your own corrections at the end — that is how the next report comes out right the first time.

## Text

1. **Full, readable sentences**, understandable to people who are not engineers. Don't save words: longer and clear beats short and cryptic. No telegraphic fragments ("SSM instead of transformers → sub-100 ms, cheap inference" is bad). Explain every term at first use.
2. **Plain language first.** Reports are read by non-technical people first. Unexplained jargon and abbreviations are banned as-is. Add a mini glossary when a report needs more than a few terms.
3. **Informative headings, no drama or metaphors.** "SEO: heavy domain, light yield" is bad; "SEO: brand traffic plus programmatic language pages" is good.
4. **No snide evaluations** of the competitor ("their only case study, stretched over 27 pages" is bad). Assessments go in a separate block, with arguments, apart from the facts.
5. **Neutral tone, no personal address.** No "this confirms your scepticism" — the report is shown to a team. Write "the hypothesis was confirmed".
6. **The executive summary is a connected narrative** (5–8 full paragraphs), not a list of bullets. A set of disconnected bullets confuses more than it helps.

## Facts and links

7. **Links at every level.** Every fact, post, article, thread, case and ad has a URL. Papers link to arXiv. Numbers with unusual methodology explain where they come from and how to check them.
8. **No unattributed numbers.** If the source is a transparency library, a screenshot or a secondary-market price feed, name it and link it.
9. **Separate company claims from independent data**, explicitly. Label founder quotes from podcasts and interviews as self-reported.
10. **Verification labels** on key claims: ✓ verified live / ~ estimate / ⚠ self-reported.
11. **Explain financial terms** or drop them (for example: what a secondary-market price is, what it means and what it does not).

## What not to do

12. **No salaries** from job postings.
13. **No Ahrefs paid-traffic or ad-budget estimates**, and no other surrogate spend estimates. Libraries don't disclose budgets — say exactly that.
14. **No ad-volume comparisons between competitors** unless explicitly asked.
15. **No comparisons with the reader's own company** and no "what this means for us" sections — the report is entirely about the competitor, unless explicitly asked.
16. **KPI tiles only for numbers that carry value on their own.** No "clever" tiles with long captions — those facts live in the section text.
17. **Flag risky tactics as risky.** If the report describes a tactic the reader might copy (for example aggressive programmatic SEO), add the platform-policy risk (Google's scaled-content-abuse policy) and what a careful version looks like.

## Structures

18. **Customer cases as a table:** Customer | What they do | Which product they used | What problem they solved | Why they need this product | Claimed results | Link to the case.
19. **The team as a full table** with LinkedIn links — every person found, not the top five — plus cards for founders and executives. A confirming source for each.
20. **Rank GTM channels by contribution to revenue**, naming the main source of money explicitly. Launches and media stunts are attention support, if that is what the data shows.
21. **Treat launch posts and engagement mechanics with scepticism:** real engagement numbers, what is measurable and what is not (pipeline from launches is not publicly measurable — say so), comment-gating inflates comments.
22. **Key teardowns as separate satellite pages** (ads, PR, launches, community, tutorials) with visible card buttons from the main report — never as references to markdown files in `raw/`.

## Freshness

23. **Date floor for fast-moving fields.** In AI models, ad platforms and tooling, sources must be from the current year. Name current product versions, give a publication date next to every link, and never present older material as current practice — if no newer source exists, give the date and say whether the claim still holds.

## Page format

24. Standalone HTML: all styles inline, no external dependencies, the right `lang` attribute, a light theme (`color-scheme: light`), tables inside `overflow-x: auto` containers, an anchored table of contents. Satellite pages inherit the main report's CSS (one visual family), carry the line "Satellite of the main research on <Company> · <month year>" and a link back to the main report.
25. After edits, validate tag balance and check the table-of-contents anchors.
