# Sunday Weekly Brief Automation — Prompt & Checklist

## Master Prompt for the Agent

Use this prompt when setting up or running the automation:

---

**Role:** You are an automation assistant that runs every **Sunday at 8:00**. Your job is to produce a short, listenable “weekly brief” that summarizes the user’s upcoming calendar and delivers it as a private audio file they can play like a podcast.

**Objective:**  
1. **Retrieve** all events from the user’s **Google Calendar(s)** for the **next 7 days** (Monday–Sunday of the coming week). Include every calendar the user has selected (work, personal, etc.).  
2. **Summarize** the events in 2–4 clear sentences: what’s happening and when (e.g. “Monday 9am: Team standup. Tuesday 2pm: Dentist. Wednesday all day: Conference in Berlin.”). Use natural, spoken language.  
3. **Convert** this summary to **speech** and save it as a single **audio file** (e.g. MP3 or WAV), using a clear, calm voice.  
4. **Upload** this audio so the user can listen to it **only on their Spotify account**, in a podcast-like way (private feed or Spotify for Podcasters private show—no public listing).

**Constraints:**  
- Summary must be under 150 words.  
- Audio length: under 90 seconds.  
- No events from other people’s calendars unless explicitly authorized.  
- The final audio must be available only to the user (private).

**Output format:**  
- Summary: plain text (2–4 sentences).  
- Audio: one file, named e.g. `weekly-brief-YYYY-MM-DD.mp3`.  
- Confirmation: “Uploaded to Spotify” or “Available at [private link]” plus the checklist step number completed.

**If something fails:**  
Report which step failed (1–4), what error occurred, and one concrete fix to try. Do not continue to the next step until the current one is verified.

---

## Step-by-Step Checklist (Beginner-Friendly)

Follow this checklist in order. Check off each step only after you’ve verified it works.

---

### Phase 1: Google Calendar access

| # | Step | What to do | How to verify |
|---|------|------------|----------------|
| 1.1 | Enable Google Calendar API | In [Google Cloud Console](https://console.cloud.google.com), create or select a project → APIs & Services → Enable **Google Calendar API**. | You see “Google Calendar API” in “Enabled APIs” and no error when opening it. |
| 1.2 | Create OAuth credentials | APIs & Services → Credentials → Create Credentials → **OAuth client ID**. Choose “Desktop app” (or “Web” if your automation runs on a server). Download the JSON key. | You have a `.json` file (e.g. `credentials.json`) and can open it in a text editor. |
| 1.3 | List your calendars | Run a small script or use the API to **list all calendars** the account can see. | You get a list of calendar names and IDs (e.g. “Work”, “Personal”, “primary”). |
| 1.4 | Fetch next week’s events | For each calendar you want, request events for **the next 7 days** (from next Monday 00:00 to next Sunday 23:59). | You see real event titles, start/end times, and calendar source. No 401/403 errors. |
| 1.5 | Combine and sort events | Merge events from all selected calendars and sort by start time. | One ordered list: Monday first, then Tuesday, etc., with no duplicates. |

**Phase 1 done when:** You can run a script (or manual run) and get a correct list of “next week’s” events from all chosen calendars.

---

### Phase 2: Summarize events

| # | Step | What to do | How to verify |
|---|------|------------|----------------|
| 2.1 | Define summary rules | Decide: include event name, day, time; skip “all-day” details or keep them; max 2–4 sentences. | You have 1–2 example inputs (raw events) and the exact summary you want. |
| 2.2 | Generate summary (LLM or template) | Use an LLM prompt or a simple template to turn the event list into 2–4 spoken sentences. | For a test event list, the output is 2–4 sentences, under 150 words, and sounds natural when read aloud. |
| 2.3 | Save summary to a file | Write the summary to a `.txt` file (e.g. `weekly-brief-YYYY-MM-DD.txt`). | File exists, opens in a text editor, and matches the generated summary. |

**Phase 2 done when:** From “next week’s events” you always get a short, consistent summary in a text file.

---

### Phase 3: Text to speech and audio file

| # | Step | What to do | How to verify |
|---|------|------------|----------------|
| 3.1 | Choose TTS service | Pick one: Google Cloud Text-to-Speech, ElevenLabs, Amazon Polly, or another. Create an account/API key if needed. | You can send a test sentence and receive an audio file or stream. |
| 3.2 | Convert summary to speech | Feed the summary text into the TTS API and request one audio file (e.g. MP3). | You get one file (e.g. `weekly-brief-YYYY-MM-DD.mp3`) that plays correctly and is under ~90 seconds. |
| 3.3 | Save audio in a fixed location | Save the file to a known folder (e.g. `~/weekly-briefs/` or your project folder). | Same path works every run; you can play the file from that folder. |

**Phase 3 done when:** Running “summary → TTS” always produces one playable audio file in the same place.

---

### Phase 4: “Podcast-style” listening on Spotify

| # | Step | What to do | How to verify |
|---|------|------------|----------------|
| 4.1 | Choose Spotify approach | Option A: **Spotify for Podcasters** — create a show, upload the weekly brief as an episode, keep show unlisted/private. Option B: **Private RSS feed** — host the MP3 and an RSS feed, then add the feed in Spotify (“Add podcast by RSS”). | You know which option you use and have the links/accounts. |
| 4.2 | Create show or feed | If Spotify for Podcasters: create one show (e.g. “My Weekly Brief”). If RSS: create an RSS feed that points to your MP3 URL. | You have either a Spotify for Podcasters show URL or an RSS feed URL. |
| 4.3 | Upload first episode manually | Upload one test MP3 (your weekly brief) and publish as one episode. | You can open Spotify (or Spotify for Podcasters) and see/hear the episode. |
| 4.4 | Confirm “only me” | In Spotify for Podcasters: set show to **private/unlisted**. In RSS: don’t submit to directories; only add the RSS URL in your own Spotify. | Only you can access the show/feed; it doesn’t appear in public search. |
| 4.5 | Automate upload (optional) | If your tool supports it: after generating the MP3, automatically upload to Spotify for Podcasters (or update RSS feed and file). | One click or cron run produces the brief and it appears in your Spotify. |

**Phase 4 done when:** You can listen to the weekly brief in Spotify like a podcast, and only you have access.

---

### Phase 5: Schedule and final run

| # | Step | What to do | How to verify |
|---|------|------------|----------------|
| 5.1 | Run full pipeline once | Run: Calendar → Summary → TTS → Save MP3 → Upload (if automated). | You get a new MP3 and a new episode (or updated feed) without errors. |
| 5.2 | Schedule for Sunday 8:00 | Use **cron** (Mac/Linux) or **Task Scheduler** (Windows) or your automation platform to run the pipeline every **Sunday at 8:00**. | Next Sunday at 8:00 the job runs and a new brief appears (or you see logs that it ran). |
| 5.3 | Add error alerts (optional) | If a step fails, get an email or notification. | You receive a message when the run fails. |

**Phase 5 done when:** Every Sunday at 8:00 you have a new weekly brief in Spotify (or in your folder + manual upload) and you can listen to it like a podcast.

---

## Quick reference: what you need

- **Google:** Cloud project, Calendar API enabled, OAuth client (desktop or web), `credentials.json`.
- **Calendars:** List of calendar IDs you want included.
- **Summary:** LLM API key (if using LLM) or a fixed template.
- **TTS:** Account + API key for one TTS provider.
- **Spotify:** Spotify for Podcasters account, or a place to host MP3 + RSS (e.g. your own server or a podcast host that supports private RSS).
- **Schedule:** Cron (e.g. `0 8 * * 0` for 8:00 every Sunday) or equivalent.

---

## If you get stuck

- **Calendar:** “401” or “403” → Check OAuth scopes (include `https://www.googleapis.com/auth/calendar.readonly`) and that you’ve re-authorized after adding new calendars.
- **Summary:** Too long or awkward → Shorten the LLM prompt or add “Maximum 4 sentences, under 150 words.”
- **TTS:** Wrong voice or format → In the TTS API call, set language (e.g. `en-US`) and output format (e.g. MP3).
- **Spotify:** “Can’t add podcast” → For RSS, ensure the feed URL is public (HTTPS) and the feed XML is valid; for Spotify for Podcasters, check that the episode is published (even if show is private).

Work through the checklist from top to bottom, and only move to the next phase when the current one is fully verified.
