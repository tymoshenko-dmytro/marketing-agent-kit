# Google credentials (Drive mode only)

Local mode needs none of this. For Google Drive and Sheets, `publish.py` needs an identity Google recognises, with permission to write into one shared drive and one spreadsheet. One-time setup, about ten minutes.

## The two kinds of key

**A personal (user) key** logs in as you through a browser; the script then acts with your rights. Drawbacks: it expires and needs a browser login again, and Google's re-check of these tokens can depend on the network you're on — a refresh that worked yesterday can demand a login today.

**A service account** is a separate robot identity with its own email address, like `video-publisher@your-project.iam.gserviceaccount.com`. You give the script its key file once, and it never asks again — no browser, no expiry, no network dependence. It can only reach what you explicitly share with that email.

**Take the service account.** It doesn't break, and it is isolated from every other Google token on your machine.

## Creating the service account

1. Open <https://console.cloud.google.com/iam-admin/serviceaccounts> and pick (or create) a project.
2. **Create service account** → any name, e.g. `video-publisher`. Skip the optional role and access steps: it needs no project roles, only shared files.
3. Open it → **Keys** → **Add key** → **Create new key** → **JSON**. A file downloads.
4. Move it where the script looks, and lock it down:

   ```bash
   mkdir -p ~/.config/marketing-agent-kit
   mv ~/Downloads/<downloaded-key>.json ~/.config/marketing-agent-kit/google-sa.json
   chmod 600 ~/.config/marketing-agent-kit/google-sa.json
   ```

5. Enable two APIs for the project: <https://console.cloud.google.com/apis/library/drive.googleapis.com> and <https://console.cloud.google.com/apis/library/sheets.googleapis.com>.
6. Find the robot's email (the `client_email` field in the JSON):

   ```bash
   python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/marketing-agent-kit/google-sa.json')))['client_email'])"
   ```

7. Share with that email:
   - the **shared drive** → Manage members → add the email as **Content manager**;
   - the **catalogue spreadsheet** (if you use one) → Share → the same email → **Editor**.
8. Put the ids into `library.json` (`drive_id`, `sheet_id`) and run `publish.py --dry-run`, then for real.

The key file is a password. Never commit it, never paste it into a chat.

## The alternative: a separate user token

If you can't create a service account, use a personal token **for this script only**, kept in its own file so other tools' Google tokens are never touched:

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive
cp ~/.config/gcloud/application_default_credentials.json ~/.config/marketing-agent-kit/google-user.json
chmod 600 ~/.config/marketing-agent-kit/google-user.json
```

Then re-run the login that your other tools need (the GA4 / Google Ads MCP servers use the same default file — see `connections/ga4-mcp.md`). `gauth.py` uses `google-user.json` automatically when there is no service-account key. It will need redoing from time to time.

## Walls you may hit

- **`storageQuotaExceeded` when uploading to My Drive.** Not a permissions mistake: a service account has no storage. Use a shared drive (or the user token).
- **A service account can't create a shared drive** (`userCannotCreateTeamDrives`) **or move an existing file into one** (`fileWriterTeamDriveMoveInDisabled`) under many Workspace policies. Both are a drag-and-drop for a human and impossible for the robot — do them once by hand.
- **A shared drive "looks empty" to the script.** Every Drive call against a shared drive needs `supportsAllDrives=true` (searches too: `includeItemsFromAllDrives`, `corpora=drive`, `driveId`). Without them the API answers as though the drive doesn't exist. `publish.py` sends them; your own scripts must too.
- **"This app is blocked"** during `gcloud auth application-default login` — your Workspace blocks gcloud's default OAuth client for these scopes. Create your own OAuth client (Desktop app) in the Cloud Console and pass `--client-id-file=<client_secret.json>` to the login.
