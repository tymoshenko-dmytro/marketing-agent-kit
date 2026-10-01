# How app funnels are usually built

Patterns seen across long consumer-app funnels (health, diet, fitness, lifestyle) captured with this skill. Use them as a sanity check: if your capture looks very different, either the funnel is unusual or something was mishandled.

## Length and structure

- **30–120 screens** is normal. The longest ones span several domains or path families (survey → payment-survey → checkout).
- A typical order: age / gender gate → goals → body profile → activity and preferences → lifestyle (energy, water, sleep, diet, habits) → measurements → health and safety → motivation → **"analysing your answers" loader** → email gate → name → personalised plan → paywall.
- Some funnels are single-page apps with hash routing: every screen fixed to viewport height, alternative branches reachable only by URL hash.

## Things that stop a naive walker

- **Consent checkboxes** ("I consent to the processing of my health data") under an input that silently keep Continue disabled until ticked.
- **Fake loaders with questions embedded mid-animation.** A walker that quits on "no clickable elements" stops here.
- **Multi-select screens** where Continue stays disabled until something is picked.
- **Unit toggles**: ft / in and lb by default with separate inputs; metric values typed into imperial fields produce invalid answers.
- **Email gates** before the plan in most funnels.
- **Password account creation** before the card form in some — capture ends there by design. In some funnels, without an account the trial button fails inline and never creates a checkout session, so the card form is genuinely unreachable.
- **Bot detection by request headers** (a headless client hint) that redirects automation into a tarpit of generated pages.

## Paywalls

- Countdown timers, three plans with a "most popular" middle option, a weekly price breakdown.
- **Discount and gift modals** on load or after a delay ("you unlocked the highest discount") that must be claimed before prices change — sometimes leading to a **second paywall** with lower prices.
- Exit-intent and back-navigation screens; many of them carry no real offer.
- Checkout as a modal, an inline payment element near the bottom of the paywall (scroll it into view), a separate page, or a separate domain.
- Trial mechanics vary: a free trial with auto-renew, a paid intro period, or a trial whose price the user chooses.
- What to record for every paywall: plans and prices before and after any discount, trial length and price, auto-renew price and period, cancellation terms, money-back guarantee (or its absence), payment methods offered.

## Cross-funnel questions worth answering in a teardown

- Where does the funnel ask for the email, and what does it promise in exchange?
- How many screens before the first price?
- Which answers visibly change the plan or the price?
- Is the discount real (prices change) or decorative (always the same "discount")?
- What happens when you try to leave?
