"""
Phase 1: Google Calendar access.

Fetches events from selected calendars for the next 7 days
(Monday 00:00 to Sunday 23:59).
"""

from datetime import datetime, timedelta
from pathlib import Path
import zoneinfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Default paths (can be overridden)
_CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials.json"
_TOKEN_PATH = Path(__file__).resolve().parent.parent / "token.json"


def get_calendar_service(credentials_path=None, token_path=None):
    """
    Build an authenticated Google Calendar API service.

    On first run, opens browser for OAuth consent and stores token.
    """
    creds_path = credentials_path or _CREDENTIALS_PATH
    tok_path = token_path or _TOKEN_PATH

    if not creds_path.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {creds_path}. "
            "Download OAuth client credentials from Google Cloud Console "
            "(APIs & Services → Credentials → Create OAuth client ID → Desktop app)."
        )

    creds = None
    if tok_path.exists():
        creds = Credentials.from_authorized_user_file(str(tok_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        tok_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tok_path, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def list_calendars(service=None):
    """
    List all calendars the authenticated user can access.

    Returns:
        list[dict]: [{"id": "...", "summary": "..."}, ...]
    """
    svc = service or get_calendar_service()
    result = svc.calendarList().list().execute()
    items = result.get("items", [])
    return [{"id": c["id"], "summary": c.get("summary", c["id"])} for c in items]


def _next_week_range(timezone_str="America/New_York"):
    """Return (start, end) datetimes for next Monday 00:00 and next Sunday 23:59."""
    tz = zoneinfo.ZoneInfo(timezone_str)
    now = datetime.now(tz)
    # Find next Monday
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0 and now.hour >= 0:
        days_until_monday = 7  # Already past Sunday, go to next week
    next_monday = (now + timedelta(days=days_until_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    next_sunday = next_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return next_monday, next_sunday


def get_next_week_events(
    calendar_ids,
    service=None,
    timezone_str="America/New_York",
):
    """
    Fetch events from the next 7 days (Monday 00:00 to Sunday 23:59).

    Args:
        calendar_ids: list of calendar IDs to fetch from
        service: optional Calendar API service (built if not provided)
        timezone_str: timezone for date range (e.g. America/New_York)

    Returns:
        list[dict]: Merged, sorted events. Each has:
            - summary (str)
            - start (datetime)
            - end (datetime)
            - calendar_id (str)
            - is_all_day (bool)
    """
    svc = service or get_calendar_service()
    start_dt, end_dt = _next_week_range(timezone_str)
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    all_events = []
    for cal_id in calendar_ids:
        try:
            result = (
                svc.events()
                .list(
                    calendarId=cal_id,
                    timeMin=start_iso,
                    timeMax=end_iso,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch events from calendar {cal_id}: {e}") from e

        for ev in result.get("items", []):
            if ev.get("status") == "cancelled":
                continue
            start_info = ev.get("start", {})
            end_info = ev.get("end", {})
            if "dateTime" in start_info:
                start_str = start_info["dateTime"]
                end_str = end_info.get("dateTime", start_str)
                start_parsed = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_parsed = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                is_all_day = False
            else:
                start_str = start_info.get("date", "")
                end_str = end_info.get("date", start_str)
                start_parsed = datetime.fromisoformat(start_str)
                end_parsed = datetime.fromisoformat(end_str)
                # Make all-day datetimes timezone-aware so we can sort with timed events
                tz = zoneinfo.ZoneInfo(timezone_str)
                start_parsed = start_parsed.replace(tzinfo=tz)
                end_parsed = end_parsed.replace(tzinfo=tz)
                is_all_day = True

            all_events.append(
                {
                    "summary": ev.get("summary", "(No title)"),
                    "start": start_parsed,
                    "end": end_parsed,
                    "calendar_id": cal_id,
                    "is_all_day": is_all_day,
                }
            )

    # Sort by start time (all datetimes are now comparable)
    all_events.sort(key=lambda e: e["start"])

    # Deduplicate by (start, summary) in case of overlapping calendars
    seen = set()
    deduped = []
    for e in all_events:
        key = (e["start"], e["summary"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    return deduped
