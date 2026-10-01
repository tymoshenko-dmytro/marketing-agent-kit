# LinkedIn Ad Library — working techniques and traps

Learned on real competitor runs. Read before collecting LinkedIn ads.

## Finding ALL of a company's ads

1. **A search by advertiser name catches namesakes and misses ads.** `search?accountOwner=<name>` returns similar names (one run returned 77 advertisers, one of them real) and still skips most of the company's own ads.
2. **The working path is `companyIds`.** `https://www.linkedin.com/ad-library/search?companyIds=<ID>` returns exactly that company's ads. Take the `companyId` from the "Advertiser" link on the detail page of any one ad you found (a keyword search usually finds the first one).
3. **Thought-leader ads are separate.** They run from a person's profile (the CEO, a founder): search `search?accountOwner=<First+Last>`. "Paid for by <Company>" on the detail page confirms whose ad it is.
4. **A keyword search** (`q=<brand>` via the SearchApi `linkedin_ad_library` engine) also returns OTHER advertisers' ads that mention the brand. That is a valuable signal of its own — who compares themselves to the brand — but never mix it with the company's own advertising.

## What the detail pages disclose (no login)

`https://www.linkedin.com/ad-library/detail/<AD_ID>` — a plain `curl` returns the full HTML:

- **The full ad text**, including the copy of video ads (the headline and text, not the video — the library serves only the cover image).
- **"Ran from X to Y"** — the run period.
- **"Ad Impressions → Estimated Total Impressions"** — an impressions range (for example "500k–1M") plus a split by country in percent.
- **Targeting:** language, geography, audience criteria.

## When impressions are missing

- The "Ran from / Ad Impressions" block is **absent on some ads** — in practice on active thought-leader ads and follow ads, while active job ads sometimes have it. LinkedIn does not document why. Write "LinkedIn does not disclose this" and don't guess.
- For an undated ad you can estimate the date **indirectly from the unix timestamp in the video-cover URL** (`licdn.com/...&t=<unix_ms>...`). Label it as indirect dating.
- Impressions of finished campaigns appear after the fact — re-check after a campaign ends.

## When the library itself is down

The Ad Library periodically breaks entirely on LinkedIn's side: detail pages and search return HTTP 200 with a server-rendered "Failed to load. Please try again" (an ~8 KB shell with no data), and a logged-in browser shows the same. It is not a ban and not a URL change.

Telling an outage from a block: `curl -s <detail-url> | wc -c` returns ~8 KB for EVERY ad, including unrelated brands' ads (try a big advertiser such as Nike) → LinkedIn outage. Large, varied sizes for other ads but not for your targets → something specific to those ads.

During an outage:
1. The SearchApi `linkedin_ad_library` engine usually keeps working — you can still collect texts, advertisers and links, just without the "Ran from / Impressions" block.
2. Do NOT change the links in your report — the URLs are correct and come back when the library does.
3. Re-check in a day or two.

This is why the rule "save the detail HTML the moment you collect it" is mandatory: on one run, data collected five days before an outage survived only because the raw copies were on disk.

## Small things

- An ordinary browser User-Agent is enough; the pages are public.
- The same creative from the company and from its CEO is TWO ads with different ids. A CEO post promoted as a thought-leader ad shows paid and organic engagement on one counter — they cannot be separated, so say so.
- Save detail-page HTML in `raw/` (`li-detail-<id>.html`): the data can disappear after a campaign ends.
