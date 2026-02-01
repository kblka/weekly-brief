#!/usr/bin/env python3
"""
Sunday Weekly Brief — main entry point.

Pipeline: Calendar → Summary → TTS → Save MP3 → (Optional) Update RSS feed.

Run every Sunday at 8:00 via cron: 0 8 * * 0
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.calendar_client import get_calendar_service, get_next_week_events, list_calendars
from src.rss import append_episode_to_feed
from src.summarizer import generate_summary, save_summary
from src.tts_client import synthesize_to_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def _next_monday_date_str(timezone_str: str) -> str:
    """Return YYYY-MM-DD of next Monday."""
    import zoneinfo
    tz = zoneinfo.ZoneInfo(timezone_str)
    now = datetime.now(tz)
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0 and now.hour >= 0:
        days_until_monday = 7
    next_monday = now + timedelta(days=days_until_monday)
    return next_monday.strftime("%Y-%m-%d")


def run_pipeline(
    list_calendars_only: bool = False,
    skip_rss: bool = False,
) -> str:
    """
    Run full pipeline: fetch events → summarize → TTS → save → (optional) RSS.

    Returns:
        Confirmation message (e.g. path to MP3, or RSS feed URL)
    """
    # Phase 1: Calendar
    log.info("Phase 1: Fetching calendar events")
    service = get_calendar_service(
        credentials_path=config.CREDENTIALS_PATH,
        token_path=config.TOKEN_PATH,
    )

    if list_calendars_only:
        calendars = list_calendars(service)
        log.info("Available calendars:")
        for c in calendars:
            log.info(f"  - {c['id']}: {c['summary']}")
        return "Listed calendars. Set CALENDAR_IDS in .env to choose which to include."

    events = get_next_week_events(
        calendar_ids=config.CALENDAR_IDS,
        service=service,
        timezone_str=config.TIMEZONE,
    )
    log.info(f"Fetched {len(events)} events")

    date_str = _next_monday_date_str(config.TIMEZONE)

    # Phase 2: Summary
    log.info("Phase 2: Generating summary")
    summary = generate_summary(events)
    summary_path = save_summary(summary, config.OUTPUT_DIR, date_str)
    log.info(f"Saved summary to {summary_path}")

    # Phase 3: TTS
    log.info("Phase 3: Converting to speech")
    mp3_path = config.OUTPUT_DIR / f"weekly-brief-{date_str}.mp3"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    synthesize_to_file(summary, mp3_path)
    log.info(f"Saved audio to {mp3_path}")

    # Phase 4: RSS (optional)
    if config.RSS_BASE_URL and not skip_rss:
        log.info("Phase 4: Updating RSS feed")
        feed_path = config.OUTPUT_DIR / "feed.xml"
        append_episode_to_feed(
            date_str=date_str,
            mp3_path=mp3_path,
            feed_path=feed_path,
            base_url=config.RSS_BASE_URL,
            show_title=config.RSS_SHOW_TITLE,
            show_description=config.RSS_SHOW_DESCRIPTION,
        )
        feed_url = f"{config.RSS_BASE_URL}/feed.xml"
        log.info(f"Updated feed at {feed_path}")
        return f"Step 4.5 completed. MP3: {mp3_path}. RSS feed: {feed_url}. Add feed URL in Spotify: Settings → Add podcast by RSS."
    else:
        return f"Step 3.3 completed. MP3 saved to {mp3_path}. For Spotify: upload manually to Spotify for Podcasters, or set RSS_BASE_URL for automated RSS feed."


def main():
    parser = argparse.ArgumentParser(description="Sunday Weekly Brief — calendar to audio")
    parser.add_argument(
        "--list-calendars",
        action="store_true",
        help="List available calendars and exit",
    )
    parser.add_argument(
        "--skip-rss",
        action="store_true",
        help="Skip RSS feed update (only generate MP3)",
    )
    args = parser.parse_args()

    try:
        msg = run_pipeline(
            list_calendars_only=args.list_calendars,
            skip_rss=args.skip_rss,
        )
        print(msg)
        sys.exit(0)
    except FileNotFoundError as e:
        log.error(f"Step 1.2 failed: {e}")
        print("Fix: Download credentials.json from Google Cloud Console and place in project root.")
        sys.exit(1)
    except Exception as e:
        log.exception("Pipeline failed")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
