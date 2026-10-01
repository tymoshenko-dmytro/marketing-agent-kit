# Posters, frame 0 and contact sheets

The poster is the still people see before a video plays — in the ad account, in a feed, in Slack, in the gallery. It is often the first and only frame anyone sees, so it is chosen, not left to chance.

Adapted from the delivery step of [/brag](https://github.com/latent-spaces/brag) (MIT), which solved the same problem for launch videos.

## Picking the frame

`scripts/frames.py pick <video>` prints the chosen time; `publish.py` uses it automatically.

It samples the video five times a second and scores every frame in the middle 70%:

- **settled** — little motion against the neighbouring frames, so text is fully in and nothing is mid-transition;
- **contentful** — high contrast, so there is text or UI on screen;
- blank, near-uniform frames (fades, empty backgrounds) are skipped, whatever their colour.

It is deterministic: the same render always gets the same poster. It is also a heuristic. **Look at the posters.** If one lands on the wrong beat — the logo instead of the offer, the setup instead of the payoff — set `poster_at` on that item. You usually know the strongest moment from the storyboard: the hook line, the product reveal, the end card.

## Baking the poster into frame 0

A bare `.mp4` has no poster attribute. Every player and platform picks its own idle thumbnail, and almost all of them grab **frame 0** — which in an ad is usually a fade-in, a blank background or half-drawn text. Slack, X and Discord regenerate thumbnails on their servers and ignore embedded cover-art metadata, so the only reliable way to control the idle image everywhere is to make frame 0 *be* the poster.

`publish.py --bake-poster` (or `frames.py bake <video> <poster.jpg>`) replaces **only frame 0's pixels** with the poster. Every other frame and all timing stay the same: same duration, same frame count, audio copied through. At 30 fps the poster shows for 1/30 s before the intro — invisible on playback, but it's what every thumbnail grabber sees.

The cost is one re-encode of the video stream (H.264, CRF 18). Use it for files that go to feeds, chats and landing pages. Skip it if the ad platform lets you upload a thumbnail and you prefer to keep the render untouched.

## Custom thumbnails

Keep the `.jpg` next to the video: it is the custom-thumbnail upload for the platforms that accept one (Meta, TikTok, YouTube, the LinkedIn post editor) and the `poster="…"` image for any `<video>` that embeds the creative on a site.

## Contact sheets

`<name>.sheet.jpg` — six stills spread across the video, written to `dist/`. Use them for QA before anyone else sees the batch:

- text overflowing or colliding with other elements,
- low contrast (dark text on a background that changed mid-video),
- a logo invisible on its background (automated checks measure text, not images),
- a plain crossfade between two busy layouts that turns into a muddy double exposure mid-transition.

The agent can read the sheets as images — ask it to look at every sheet and list problems before you open a single video.
