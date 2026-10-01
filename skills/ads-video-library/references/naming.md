# File naming

The name says what the file is without opening it, and every field is parseable, so the catalogue can be rebuilt from a folder listing alone.

```
<type>_<topic>_<lang>_<aspect>_<voice>_<length>_<date>_v<N>.mp4
```

Underscores separate fields, hyphens live inside a field, lowercase throughout.

| Field | What it is | Examples |
|---|---|---|
| `type` | what kind of video this is | `motion` `ugc` `demo` `cutdown` |
| `topic` | the offer, and the audience where that is the point | `hr-interviews` `pricing-panel` |
| `lang` | spoken language of the voiceover | `en` `es` `de` |
| `aspect` | frame | `16x9` `9x16` `1x1` `4x5` |
| `voice` | male or female, not the speaker's name | `female` `male` |
| `length` | rounded seconds | `13s` |
| `date` | the day it was created | `2026-08-26` |
| `v<N>` | version, bumped on a change a viewer would notice | `v1` `v2` |

## Examples

```
motion_hr-interviews_en_16x9_female_13s_2026-08-26_v1.mp4
motion_hr-interviews_en_16x9_male_11s_2026-08-26_v1.mp4
motion_pricing-panel_en_9x16_male_14s_2026-08-26_v1.mp4
```

From the names alone: all three are motion cards in English, two are the same offer read by a woman and a man, the third is a different offer in vertical format, and you know how long each runs before opening anything.

No brand prefix. It carries no information — every file in your library is yours, and the folder says so.

## The type slug is a decision, not a template

`motion` is one precedent. A new format picks its own short lowercase slug with no underscore in it — an underscore inside `type` breaks the parse the whole convention rests on. The human-readable version is the `label`, which names the folder and the Sheet tab: `motion` / "Motion Cards".

## Why the voice is a gender and not a name

The name of a TTS voice tells nobody choosing a creative anything useful. `female` is what an ad reviewer actually compares. The exact voice id belongs in the catalogue (an `extras` column such as `voice_id`).

If you test two female voices on the same offer, the second takes `v2` — a change the viewer notices is exactly what a version is for.

## Why the date in the name doesn't break the ad join

A date in the file name means the name changes when the file is re-rendered, and ad performance joined on a file name would split one creative's history in two.

So the catalogue does **not** join on the file name. It has an immutable `id`:

```
id = <type>_<topic>_<voice>          motion_hr-interviews_female
```

It survives re-renders, new dates, new versions and new lengths. `file` is the human-facing name; `id` is what the numbers hang on. When you name the ad in the ad account, put the `id` in it.

## Other assets

```
<name>.jpg                          poster (same stem as the video)
<name>.sheet.jpg                    contact sheet (stays in dist/, not stored)
bed_<slug>_<bpm>bpm_v<N>.wav        bed_product-tour_120bpm_v1.wav
vo_<topic>_<voice>_<line>_v<N>.wav  vo_hr-interviews_female_a2_v1.wav
sfx_<slug>_v<N>.wav                 sfx_brand-swell_v1.wav
```
