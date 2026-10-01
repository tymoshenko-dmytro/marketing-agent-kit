# Funnel map — fill this in once

The skill reads this file before every funnel report. Replace the template with your own events. Keep it to facts the agent must know: which events exist, which one is canonical, which ones lie.

## Properties

| Site / app | GA4 property id | Notes |
|---|---|---|
| <your site> | <digits> | main marketing site + app in one property? |

(Find ids with `python3 scripts/ga4.py --list-properties`. If you'd rather not keep ids in a file, set the env var `GA4_PROPERTY_ID` instead.)

## Conversion events (the headline numbers)

| Event | What it means | Matches in the ad platform |
|---|---|---|
| `<form_submitted>` | lead | Google Ads conversion "<name>" |
| `<meeting_scheduled>` | booked call | |
| `<purchase>` | first payment | |

## Self-serve funnel, in order

1. `<signup_cta_clicked>` — click on the signup button on the marketing site
2. `<signup_page_viewed>` — the signup page opened
3. `<signup_completed>` — **canonical signup event** (prefer a server-side event: client-side ones get lost to ad blockers and reloads)
4. `<onboarding_completed>`
5. `<trial_started>`

## Events that look right but aren't

- `<generic_cta_clicked>` — fires on EVERY button, inflates the top of the funnel. Don't use for signup.
- `<old_event_name>` — renamed on <date>; history before that date is under the old name.

## Report format the team expects

Metrics in this order: Sessions → step 1 → conversion → step 2 → conversion → … Usually four tables: all traffic (total), paid traffic (total), all traffic by day, paid traffic by day. Unique users (`totalUsers`), not event counts.
