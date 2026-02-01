# Sunday Weekly Brief

Automated weekly calendar brief delivered as a private audio file you can listen to like a podcast. Runs every Sunday at 8:00.

## What it does

1. **Fetches** events from your Google Calendar(s) for the next 7 days (Monday–Sunday)
2. **Summarizes** them in 2–4 natural spoken sentences (under 150 words). In Czech mode, uses Google Gemini to infer event types (birthday, cinema, doctor, etc.) and phrase naturally.
3. **Converts** the summary to speech (MP3, under 90 seconds) in Czech or English
4. **Delivers** via private RSS feed (add once in Spotify) or manual upload to Spotify for Podcasters

## Quick start

### 1. Prerequisites

- Python 3.10+
- [Google Cloud project](https://console.cloud.google.com) with Calendar API and Text-to-Speech API enabled

### 2. Install

```bash
cd "Sunday Weekly Brief"
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Google Calendar setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable **Google Calendar API** and **Cloud Text-to-Speech API**
4. Create OAuth credentials: APIs & Services → Credentials → Create Credentials → OAuth client ID → Desktop app
5. Download the JSON key and save as `credentials.json` in the project root

### 4. First run

```bash
# List your calendars
./venv/bin/python run_brief.py --list-calendars

# Create .env (copy from .env.example) and set CALENDAR_IDS
cp .env.example .env
# Edit .env: CALENDAR_IDS=primary,work,personal (or IDs from --list-calendars)

# Run the full pipeline (browser opens for OAuth on first run)
./venv/bin/python run_brief.py   # or: source venv/bin/activate && python run_brief.py
```

Output is written to `output/weekly-brief-YYYY-MM-DD.mp3` and `output/weekly-brief-YYYY-MM-DD.txt`.

### 5. Spotify delivery

**Option A: GitHub Actions (fully automated, no manual steps)**

The pipeline can run in the cloud every Sunday: Calendar → Summary → TTS → MP3 + RSS, then commit to the repo. GitHub Pages serves the feed and MP3s. See [GitHub Actions setup](#github-actions-setup) below.

**Option B: RSS feed (manual or cron + upload)**

1. Host the `output/` folder somewhere with a public URL (e.g. GitHub Pages, S3, or your web server)
2. Set `RSS_BASE_URL` in `.env` (e.g. `https://yoursite.com/weekly-brief`)
3. Each run updates `output/feed.xml`
4. In Spotify: Settings → Add podcast by RSS → paste your feed URL (e.g. `https://yoursite.com/weekly-brief/feed.xml`)

**Option B: Spotify for Podcasters (manual upload)**

1. Create a show at [podcasters.spotify.com](https://podcasters.spotify.com)
2. Set show to private/unlisted
3. Each week: upload `output/weekly-brief-YYYY-MM-DD.mp3` as a new episode

### 6. Schedule for Sunday 8:00

```bash
crontab -e
```

Add:

```
0 8 * * 0 cd /Users/YOU/Documents/Sunday\ Weekly\ Brief && ./venv/bin/python run_brief.py >> output/run.log 2>&1
```

Replace `YOU` and `/path/to/venv` with your paths.

## Configuration (.env)

| Variable | Description |
|----------|-------------|
| `CALENDAR_IDS` | Comma-separated calendar IDs (default: `primary`) |
| `TIMEZONE` | Timezone for event display (e.g. `Europe/Prague`) |
| `LANGUAGE` | `cs` (Czech) or `en` (English). Default: `cs`. |
| `GEMINI_API_KEY` | Google Gemini API key for natural Czech summaries. Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Leave empty for template-based summary. |
| `RSS_BASE_URL` | Base URL for RSS/MP3 hosting (optional; leave empty for manual upload only) |

## TTS credentials

Google Cloud Text-to-Speech uses Application Default Credentials:

- **Local dev:** Run `gcloud auth application-default login` (same Google account as Calendar OAuth)
- **Service account:** Set `GOOGLE_APPLICATION_CREDENTIALS` to path of a service account JSON with `roles/cloudtts.user`

## GitHub Actions setup

Run the pipeline automatically every Sunday in the cloud (no need for your Mac to be on). The workflow generates the MP3 and feed, commits them to the repo, and GitHub Pages serves them.

### 1. Create a GitHub repo and push this project

- Create a **new repository** on GitHub (e.g. `weekly-brief`). Do **not** add a README (you already have one).
- In your project folder:
  ```bash
  cd "/Users/Petr/Documents/Sunday Weekly Brief"
  git init
  git remote add origin https://github.com/YOUR_USERNAME/weekly-brief.git
  git add .github config.py run_brief.py requirements.txt src .env.example .gitignore README.md agents.md
  git commit -m "Sunday Weekly Brief"
  git branch -M main
  git push -u origin main
  ```
  (Do **not** add `credentials.json`, `token.json`, `.env`, or `output/` — they stay local.)

### 2. Add repository secrets

In the repo: **Settings → Secrets and variables → Actions → Secrets → New repository secret**. Add:

| Secret name       | Value |
|-------------------|--------|
| `CREDENTIALS_JSON` | Entire contents of your `credentials.json` (Calendar OAuth client). |
| `TOKEN_JSON`       | Entire contents of your `token.json` (from the project root after you’ve run the script once locally). |
| `ADC_JSON`         | Entire contents of your Application Default Credentials file. On Mac: `~/.config/gcloud/application_default_credentials.json`. Copy the whole JSON (for TTS in the cloud). |
| `GEMINI_API_KEY`   | Your Google Gemini API key. Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Required for natural Czech summaries. |

To copy the ADC file:  
`cat ~/.config/gcloud/application_default_credentials.json | pbcopy` (then paste into the secret value).

### 3. Add repository variables

**Settings → Secrets and variables → Actions → Variables → New repository variable**. Add:

| Variable name   | Value |
|-----------------|--------|
| `CALENDAR_IDS` | Your comma-separated calendar IDs (same as in `.env`). |
| `TIMEZONE`     | Your timezone (e.g. `Europe/Prague`). |

### 4. Enable GitHub Pages

**Settings → Pages → Build and deployment**:  
- Source: **Deploy from a branch**.  
- Branch: **main** (or **master**), folder: **/ (root)**.  
- Save.

Your feed URL will be:  
`https://YOUR_USERNAME.github.io/weekly-brief/output/feed.xml`

### 5. Add the feed in Spotify

In Spotify: **Settings → Add podcast by RSS** → paste:  
`https://YOUR_USERNAME.github.io/weekly-brief/output/feed.xml`

### 6. First run

- Go to **Actions** in the repo, open the **Weekly Brief** workflow, click **Run workflow**.
- When it finishes, the new MP3 and updated `feed.xml` will be in the repo and served by Pages. Spotify will show the new episode after a refresh.

The workflow runs automatically every **Sunday at 8:00 UTC** (9:00 CET; adjust the `cron` in `.github/workflows/weekly-brief.yml` if you want a different time).

---

## Troubleshooting

- **Calendar 401/403:** Check OAuth scopes include `calendar.readonly`. Delete `token.json` and re-run to re-authorize.
- **TTS fails:** Ensure Cloud Text-to-Speech API is enabled and ADC or `GOOGLE_APPLICATION_CREDENTIALS` is set.
- **Summary too long:** The summarizer caps at 150 words and 4 sentences; adjust in `src/summarizer.py` if needed.
- **RSS not updating:** Ensure `RSS_BASE_URL` is set and the `output/` folder (including `feed.xml`) is served at that URL.
- **GitHub Action fails:** Check the Actions run log. Common causes: missing or invalid secrets (`CREDENTIALS_JSON`, `TOKEN_JSON`, `ADC_JSON`, `GEMINI_API_KEY`); wrong or empty `CALENDAR_IDS` / `TIMEZONE` variables; Calendar or TTS API not enabled in the Google Cloud project.
