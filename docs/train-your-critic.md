# Train a critic on your own corrections

`agents/copy-critic.md` started as a critic trained on one founder's comments on ad copy. It caught the same problems the founder kept catching, before the founder saw the copy. This guide shows how to build one for your own taste — for ads, emails, landing pages, slides, anything you review repeatedly.

## Why a critic is a separate agent

- **The writer can't see its own blind spots.** The model that wrote a line is the worst judge of it. A separate agent with a different brief reads it fresh.
- **Read-only on purpose.** The critic gets `tools: Read, Grep, Glob` and nothing else. It judges and returns rewrites; the writer (or you) applies them. That separation keeps the loop honest.
- **A strong model for judging.** Generation can run on a cheaper model; the critic is where the expensive one pays off.

## Step 1 — collect your corrections

You already have them; they are scattered. Gather 20–50:

- comments you left on drafts (docs, Figma, Slack threads, review calls);
- before / after pairs where you rewrote a line yourself;
- the memory files Claude Code wrote from your feedback (`~/.claude/projects/<project>/memory/feedback_*.md`) — these are corrections already written down;
- lines you approved without changes (they matter too: they show what "good" is).

Keep your exact words. "Imagine a random person who has never heard of us hears this" is a better test than any rule you would write from scratch.

## Step 2 — turn each correction into a rule

For each correction, write:

1. **What was rejected** — the line.
2. **Your words** — the reaction, verbatim.
3. **Why** — one sentence about the reader, not about style ("the viewer doesn't know the product yet, so a fact about it lands on nothing").
4. **What shipped instead.**

Then group the rules. The structure that works:

| Section | What goes there |
|---|---|
| The one or two questions | the tests you apply to every line ("Would a stranger understand this?", "So what?") |
| Reject on sight | patterns that always fail, each with one real example |
| Accept | what good looks like, with examples |
| Leave alone | what the critic must NOT flag (see pitfalls) |
| How to answer | the exact output format: verdict per line + the rewrite, three worst, ready or not |

## Step 3 — write the agent file

Copy `agents/copy-critic.md` and replace the sections with your rules. Keep:

- the instruction to read the product brief first and never judge copy for a product it can't describe;
- "the rewrite, not advice about the rewrite";
- "don't soften".

Put it in `~/.claude/agents/` (all projects) or `<project>/.claude/agents/` (one project). Give it a name you'll remember — naming it after the person whose taste it encodes makes it easy to call: "run Dima on these cards".

## Step 4 — calibrate

Take a set of lines you have already reviewed by hand. Run the critic on them without your verdicts. Compare:

- **It passed something you rejected** → a missing rule. Add it with the example.
- **It rejected something you approved** → a rule that's too broad. Narrow it, or add the case to "Leave alone".

Two or three rounds usually get it to agree with you on most lines.

## Step 5 — keep it learning

After every real review round, add what you corrected as a dated block at the end ("Round 4 additions — learned from corrections"). The critic gets better exactly where your taste is specific.

## Using it in a loop

```
writer agent → drafts 20 lines
copy-critic  → verdict + rewrite per line
writer       → applies rewrites, regenerates the failures
copy-critic  → second pass
(stop when everything passes or after 3 rounds)
you          → final read of what survived
```

The loop saves your time on the obvious failures; your read is still the last step.

## Pitfalls seen in practice

- **The critic flattens the voice.** Reviewers love flagging generalisations ("teams usually…") as unsupported. If that's your voice, say so in "Leave alone", and limit source demands to specific, checkable claims (numbers, prices, dates, named companies, rankings, legal statements).
- **One-off feedback becomes a global rule.** You removed an eyebrow label on one banner because the headline was better without it; the critic removes it everywhere. Record the context with each rule.
- **Metrics replace judgement.** For video, a critic that counts cuts per second will push pieces to hit numbers and miss that they feel wrong. Judge by watching (or by the contact sheet), then confirm with a metric — never the other way round.
- **Same agents, same answers.** Five copies of one critic agree with each other. If you want a panel, give each critic a different role and a different checklist.
