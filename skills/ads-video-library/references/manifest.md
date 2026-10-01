# The manifest

What a generating agent writes. It is the whole interface: the file name, the folder, the tab, the poster and the sweep of what a re-render replaced are all derived from it.

```json
{
  "type": "motion",
  "label": "Motion Cards",
  "tab": "Cards",
  "lang": "en",
  "extras": ["headline", "sub", "cta", "caption", "voice_id"],
  "items": [
    {
      "topic": "hr-interviews",
      "src": "renders/hr.mp4",
      "voice": "female",
      "aspect": "16x9",
      "version": 1,
      "status": "review",
      "created": "2026-08-31",
      "poster_at": 3.2,
      "notes": "HR & recruiters",
      "headline": "An AI scheduler for recruiters",
      "sub": "Candidates book themselves, in their time zone.",
      "cta": "Try for free",
      "caption": "Candidates pick an interview slot in their own time zone. No back-and-forth emails.",
      "voice_id": "<tts voice id>"
    }
  ]
}
```

## Batch fields

| Field | Required | What it is |
|---|---|---|
| `type` | yes | the slug in every file name. Lowercase, no underscores |
| `label` | yes | the folder, and the Sheet tab unless `tab` says otherwise |
| `tab` | no | the Sheet tab, when it should differ from the label |
| `lang` | yes | spoken language of the voiceover, two letters. Folder names come from `langs` (built-in list + `library.json`); an unknown code gets an upper-case folder name |
| `extras` | no | columns this type carries beyond the core set, in display order |
| `items` | yes | one entry per video |

## Item fields

| Field | Default | Notes |
|---|---|---|
| `topic` | — | the offer, and the audience where that is the point. Hyphens inside, never underscores |
| `src` | — | path to the rendered mp4, relative to the manifest or absolute |
| `voice` | — | `male` or `female`, never the speaker's name |
| `aspect` | `16x9` | |
| `version` | `1` | bump on a change a viewer would notice |
| `status` | `review` | `review`, `approved`, `rejected`, `live`, `retired` are what get used |
| `created` | today | **ignored for an id already in the catalogue** — see below |
| `poster_at` | auto | seconds; set it when the automatic poster lands on the wrong moment |
| `notes` | `""` | |
| anything in `extras` | `""` | written into that column |

## Core columns, always present

`id`, `file`, `created`, `type`, `topic`, `lang`, `aspect`, `voice`, `version`, `duration_s`, `status`, `link`, `poster`, `notes` — then whatever `extras` adds.

`duration_s` is measured with ffprobe, never taken from the manifest: a manifest that disagrees with the file is a manifest that is wrong. `link` and `poster` are the stored locations (a local path or a Drive link).

## Captions

A `caption` extra is worth having for every type: the 1–3 sentences that go with the video as the ad's primary text or the post copy. Rules that work:

- Specific to this video — its own claim, its own audience. No "excited to share", no generic SaaS language.
- Clear to a stranger in one read: what it is, who it's for.
- Matches the tone of the video.
- Postable as-is.

## Two things to know before writing a generator

**`created` is remembered, not asserted.** With `--catalog` the publisher reads existing rows; for an id it already knows, the stored `created` wins. The date is part of the name, so re-stamping it would store a second copy of an unchanged video. Without `--catalog` every run stamps today.

**The month folder follows `created`, not the calendar.** One batch can land in two month folders, and the sweep runs per month folder. A video made in August stays in `August/` when it is republished in September.
