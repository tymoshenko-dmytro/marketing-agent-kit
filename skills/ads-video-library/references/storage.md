# Storage and the catalogue

## Layout

Month, then language, then video type — the same in both storage modes:

```
<library root>/
  October/
    EN 🇬🇧/
      Motion Cards/
        motion_hr-interviews_en_16x9_female_13s_2026-10-01_v1.mp4
        motion_hr-interviews_en_16x9_female_13s_2026-10-01_v1.jpg     ← poster
        _retired/                                                       ← local mode: older renders
    ES 🇪🇸/
      Motion Cards/
```

A new month is a new folder; a new language is a new folder inside it; a new format — UGC, cut footage, product demos — is a new folder beside `Motion Cards`.

**Finished videos and their posters only.** Music beds, voice takes, sound effects and project sources stay in the render project: they are build inputs, they change, and they are useless without the project around them. The library holds what someone would hand to an ad account.

## `library.json`

```json
{
  "storage": "local",
  "local_root": "~/Ads Video Library",
  "langs": {"sv": "SV 🇸🇪"}
}
```

```json
{
  "storage": "gdrive",
  "drive_id": "<shared drive id — the part after /folders/ in its URL>",
  "sheet_id": "<optional: catalogue spreadsheet id — the part after /d/ in its URL>",
  "credentials": {"service_account": "~/.config/marketing-agent-kit/google-sa.json"}
}
```

Looked up in this order: `--config`, `./library.json`, `~/.config/marketing-agent-kit/video-library.json`. Keep `library.json` out of public repositories if it contains drive or sheet ids.

### Local mode

Files are copied into the folder tree; stale files of the same type and month are moved into `_retired/`, never deleted. Put `local_root` inside a synced folder (Google Drive for desktop, Dropbox, OneDrive) and the team gets the library without any API setup.

### Google Drive mode

Uploads go into a **shared drive** — not a folder in someone's My Drive. The creatives belong to the company and survive any one person's account; and a service account (the recommended identity, see `setup.md`) owns no storage, so it can only write where the storage belongs to the organisation.

Uploads are resumable and go straight from disk to Google. Re-uploading a name that already exists replaces its content, so links already in the catalogue stay valid. Stale files in the type's folder go to the Drive trash.

## The catalogue

A CSV is the source of truth — in the repo, diffable, survives a storage accident. One CSV holds every type and language: each run replaces the rows of its batch, keeps everything else, and marks rows whose files the sweep retired as `retired`. The Sheet, if configured, is a publication of it: one tab per video type, overwritten wholesale on every run.

| Group | Columns |
|---|---|
| core, every type | `id` `file` `created` `type` `topic` `lang` `aspect` `voice` `version` `duration_s` `status` `link` `poster` `notes` |
| what the type carries | declared in the manifest's `extras`, e.g. `headline` `sub` `cta` `caption` `voice_id` `audience` |

`id` (`<type>_<topic>_<lang>_<aspect>_<voice>`) is the join key and never changes. Numbers that need to live next to the creatives (spend, CTR, CPA) belong in the CSV as extra columns, pulled from the ad account and joined on `id`; the publisher keeps columns it doesn't own. Anything typed into the Sheet by hand is gone on the next run.
