# HyperFrames traps

Every one of these cost a wasted render or a wrong-looking deliverable. Read before
writing composition HTML.

## Layout

**`.clip { position: absolute; inset: 0; }` is required.** The runtime stretches a
root-level timed element to the frame only when it has *no computed size of its own*.
A flex container with content has one, so it collapses into the top-left corner and
every bottom-aligned caption rides up to the top. The scaffold's shared rule is what
the docs assume is present — write it yourself.

**Asset paths are root-relative in every composition, including files under
`compositions/`.** They are served with the project root as their base URL, so
`../assets/x.css` resolves outside the project and 404s in preview. Use
`assets/x.css` everywhere. (Inside a *stylesheet*, `@import` resolves relative to the
stylesheet, so a token file next to it is imported by bare filename.)

**Never size an element with a CSS `transform` that GSAP also animates.** A pop-in
tween writing `scale(1)` inline beats the stylesheet's `scale(1.5)` and the element
silently renders at its unscaled size. Put sizing on a wrapper; let the tween own the
element's own transform.

**Do not rely on `min-width` plus shrink-to-fit for a wrapping row.** `max-content`
ignores flex wrapping, so a row that will wrap is measured as one long line and the
container blows past the frame. Set an explicit width on the wrapper.

**`vmin` is 1080px in both 1920×1080 and 1080×1920.** Type sized in vmin is
physically identical in either aspect — that is the whole point — but a card sized to
fill the portrait frame is lost in the landscape one. Scale the whole stack on a
wrapper rather than re-specifying every size.

## Text reveals

**`clip-path` cannot wipe wrapped inline text.** It clips to a single rectangle
derived from the first fragment and swallows every visual line after it — the tail of
a wrapped sentence simply never appears. Reveal per word instead: one span per word,
all present at zero opacity from the first frame (so the column never reflows), then
a staggered opacity tween across the line's spoken duration. It is also more honest
for a transcript: words arrive as they are recognised.

## Media

**`<audio>` without an `id` is never mixed — the render is silent.** `lint` says so;
believe it.

**Video needs `muted`, or `data-has-audio="true"` if its own track should play.**
Generated clips usually carry audio you do not want. An undeclared track fails
`check`.

**Set an audio clip's `data-duration` to the media's real length.** A voice track
that ends before the film does (a silent end card) otherwise raises `clip_media_fit`.

## Checking

**`hyperframes check` measures text contrast, not images.** It will happily pass a
logo that is invisible on its background. Look at a rendered frame.

**Contrast failures are usually a ground problem, not a colour problem.** Dark ink
centred on a blue-to-white gradient sits on the blue half and measures 1.6:1. Decide
the ground first, then let the ink follow it.

**A decorative element that deliberately sweeps outside its parent** (a button sheen)
needs `data-layout-ignore="true"`, or `check` reports it as escaped and overflowing
on every sampled frame.

**Track density warnings are advisory.** Thirty-five captions on one track is what a
caption track looks like; leave it.

## Rendering

**h264 needs even dimensions.** 1365×768 fails to encode; 1366×768 works.

**Concatenated clips gain a frame or two each.** Five 30fps segments cut to exact
seconds came out 0.2s long overall. Measure the assembled file rather than trusting
the sum of the parts.

## Found on the first two-slide card

**A fade that ends on a clip boundary needs a `tl.set` hard kill after it.**
`check` reports `gsap_exit_missing_hard_kill`. A non-linear seek can land past the
fade and restore the stale visible state, so the outgoing slide flashes back over the
incoming one. Write both:

```js
tl.to(".fit1", {opacity:0, duration:0.30}, 8.48);
tl.set(".fit1", {opacity:0}, 8.82);   // the boundary itself
```

**`text-wrap: balance` is not enough for a headline.** It still leaves orphans -
"An AI scheduler for / recruiters". Set the break by hand: one `div` per written
line with `white-space: nowrap`, and let the word spans live inside those. The break
then belongs to the writer, which is also what a card set needs as a per-card
parameter.

**A v3 take's length varies run to run.** The same seven words at the same `--speed`
came back at 3.02s, 3.30s and 3.35s. So the bar grid cannot be planned before the
audio exists - "audio first" is arithmetic, not taste. Generate, measure, then fit.

**Eleven Music is gated.** `POST /v1/music` returns 403 `feature_not_available` until
the account accepts the separate music terms, and it carries its own pricing. Not a
decision to make on the account owner's behalf - use an existing bed, or ask.

## Sound over speech

**Nothing with a tail goes over a voice, and the first syllable is the worst place
of all.** A 0.88s shimmer laid on the opening word of a card was heard as a fault in
the recording, twice, in two different projects — the second time because the fix
was applied to one card and not to its sibling. The rule that survived: the only
audio allowed over a spoken line is texture at −24 dB or below, the kind you notice
only when it is missing. Everything that is meant to be *heard* as an event — a
confirm, a swell, a chime — waits for a beat where nobody is talking. On a
two-slide card that means the beat after the last word, and the cover.

**A card's grid should match the library the beds come from.** Ours was 110 BPM because
the first project happened to be built there. The marketplace we buy from lives at
120 — seven of thirteen candidates, four within 0.2 BPM — so the grid moved to 120,
where the bar is exactly 2.0s. A bed running at its own tempo puts the percussive
effects between its own hits, which reads as slop.

## Animating a supplied asset

**A baked shadow is invisible travel.** A directional reveal spends its ease over the
asset's *box*, not over what you can see in it. One identity SVG carried 61px of bottom
margin for a drop shadow that measures 1/255 against brand blue — 16% of its height, so
on `power2.out` the last third of the tween moved through nothing. Measure the asset's
margins against the actual ground, then trim the viewBox; do not compensate with the
curve.

**`clip-path` is the safe reveal for a box `check` measures.** The obvious
alternative — an `overflow: hidden` wrapper animated from zero height — makes the child's
bounding rect larger than its parent for the whole reveal, which the layout sampler
reports as escaped and overflowing, and it reflows whatever sits below as it grows.
`clip-path` leaves the box alone and only changes paint. Write both endpoints explicitly
with matching component counts (`inset(0% 0% 100% 0%)` → `inset(0% 0% 0% 0%)`) and repeat
the closed state in CSS, so a seek to frame 0 never parses it back out of a computed
style. Use height-on-overflow only when something must stay pinned to the moving edge.

That "matching component counts" is not pedantry. On a second project GSAP **silently
refused to interpolate the same two endpoints** — Chromium serialised them with different
numbers of values — and the panel snapped open in a single frame. No error, no warning,
`check` clean. If a `clip-path` reveal appears to have no duration, that is what happened;
switch it to a transform.

**Two `<img>` nodes with the same src, start and duration raise
`duplicate_media_discovery_risk`.** If the same asset is needed twice — a faint whole and
a bright clipped copy — paint one of them as a CSS `background-image`. Same URL, so the
browser shares one decode, and only one media node exists.

**A heavy embedded raster defeats the renderer's static-frame dedup while it moves.**
Reuse fell from 97% on a held frame to 20% during a reveal. It costs capture time, not
correctness — do not downscale a 7.5 MB asset on suspicion.

## GSAP traps that pass every check

**A `fromTo` whose from-state is visible applies it at build time.** `immediateRender`
defaults to true, so an orange glow written as a from-state sits on the element from
frame one. It appears to work only because HyperFrames seeks per frame and a seek reverts
pre-start tweens — luck, not design. Pass `immediateRender: false`.

**A wrapper at `opacity: 0` hides its children whatever their own opacity is** — and
passes every contrast check, because the text is in the DOM. Put the reveal class on the
word spans themselves, never on a group above them.

**Chained `to()` tweens on one property want a `tl.set` anchor at t=0.** Three steps on
one `height` otherwise let a non-linear seek inherit whatever a previous seek left.

**`power2.out` on a fade spends 75% of the alpha in the first half** — an 0.8s flash is
effectively over in 0.3s. Use `power1.out` for anything meant to be *seen* fading.

**A `box-shadow` with zero blur is a solid band with a hard outer edge.** A spread-only
pulse reads as a focus ring for its first frames. Blur at both ends of the tween. Only
visible in a 1:1 crop, never in a full frame.

## Composing a card around somebody else's graphic

**Namespace the wrapper's CSS or it reaches into the graphic.** A graphic written from
the same reference as the cover uses the same class names — `.fit`, `.sub` — so the
cover's `.fit { transform: scale(1.42) }` also matched the graphic's own stack and blew
it up by 42% until its icons hung off both edges. Nothing in `check` notices: contrast,
layout and motion all pass on a frame whose content is 42% too big. Scope every rule the
wrapper adds under the wrapper's own clip id.

**A parked element flies invisibly.** Sliding a graphic up from below the frame on your
own schedule wastes the movement if the graphic sets its own opacity or crop later — the
travel is spent before anything can be seen. Read the graphic's first non-headline beat
out of its timeline and align the arrival to land exactly there.

**Shift a borrowed timeline with a child, never by rewriting positions.** Put the lifted
statements on `var g = gsap.timeline()` and `tl.add(g, delay)`. The internal tuning — an
ease across a crop, the pitch of a stagger — survives untouched, and there is no
arithmetic to get wrong.

**Splitting a timeline into statements: count brackets, but skip comments and strings.**
A bracket inside a `//` comment throws the depth off and cuts a tween in half, and the
resulting syntax error quotes the comment's own words back at you. Line-based splitting
on a trailing number fails differently — the builders wrap long tweens across four
lines, so it matched four statements of thirteen in one project and none in another.

**A borrowed headline carries the wrong stagger.** Each graphic tuned its headline to
its own duration; the spoken line is usually twice as long, so the words appear at twice
the speed they are said. Discard the graphic's headline statements and write them from
the measured take.

**Audio first has exactly one exception, and it is this.** A graphic tuned by hand to a
duration is a finished thing; refitting it to whatever length a voice came out is
throwing that away. Let slide 1 last the longer of the two and let the graphic hold —
but then give the ground a breath spanning the whole card, or the tail is a genuinely
frozen frame. Everywhere else, the audio still leads.


## Two more, from wiring nine cards

**Do not fade text out — slide it out.** A 0.30s cross-fade at the end of slide 1 puts
the headline at partial opacity, and if a contrast sample lands inside that window the
card fails WCAG. It is luck: the identical fade passed on two sibling cards and failed on
the third. A transform exit never lowers anything's contrast, and the opacity can be
killed hard on the clip boundary, where nothing is measured.

**Finding a borrowed graphic's first beat: skip `tl.set` and skip the ground.** To land a
fly-up exactly where the graphic's own entrance begins you need that time out of its
timeline — but `tl.set` is state initialisation, and the ground's `#glow` breath sits at 0
and spans the whole film. Taking the minimum across all statements finds a 0, the graphic
gets pushed a second and a half late, and the frame sits empty while the voice is already
talking. Match on the stage element's own id, among `to`/`fromTo` only.
