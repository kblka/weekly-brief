"""
Phase 2: Summarize events.

Turns event list into 2–4 spoken sentences, under 150 words,
natural language style.
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

MAX_WORDS = 150
MAX_SENTENCES = 4


def _format_time(dt: datetime, is_all_day: bool) -> str:
    if is_all_day:
        return "all day"
    return dt.strftime("%-I%p").lower().replace("am", "am").replace("pm", "pm")


def _format_time_12h(dt: datetime) -> str:
    """e.g. 9am, 2pm (no leading zero)."""
    h = dt.hour
    m = dt.minute
    if m == 0:
        return f"{h if h <= 12 else h - 12}{'am' if h < 12 else 'pm'}"
    return f"{h if h <= 12 else h - 12}:{m:02d}{'am' if h < 12 else 'pm'}"


def _format_time_simple(dt: datetime) -> str:
    """e.g. 9am, 2pm."""
    hour = dt.hour
    minute = dt.minute
    if hour == 0:
        suffix = "am"
        hour_12 = 12
    elif hour < 12:
        suffix = "am"
        hour_12 = hour
    elif hour == 12:
        suffix = "pm"
        hour_12 = 12
    else:
        suffix = "pm"
        hour_12 = hour - 12
    if minute == 0:
        return f"{hour_12}{suffix}"
    return f"{hour_12}:{minute:02d}{suffix}"


def group_events_by_day(events):
    """Group events by day of week."""
    by_day = defaultdict(list)
    for ev in events:
        # Handle both datetime and date
        start = ev["start"]
        if hasattr(start, "weekday"):
            weekday = start.weekday()  # 0=Monday, 6=Sunday
        else:
            weekday = start.to_pydatetime().weekday() if hasattr(start, "to_pydatetime") else 0
        day_name = DAY_NAMES[weekday]
        by_day[day_name].append(ev)
    return dict(by_day)


def generate_summary(events: list, max_words: int = MAX_WORDS) -> str:
    """
    Convert event list to 2–4 spoken sentences.

    Format: "Monday 9am: Team standup. Tuesday 2pm: Dentist. Wednesday all day: Conference."

    Enforces max 150 words and max 4 sentences.
    """
    if not events:
        return "You have no events scheduled for the coming week."

    by_day = group_events_by_day(events)
    parts = []

    for day in DAY_NAMES:
        if day not in by_day:
            continue
        day_events = by_day[day]
        for ev in day_events:
            time_str = (
                "all day"
                if ev.get("is_all_day", False)
                else _format_time_simple(ev["start"])
            )
            summary = ev.get("summary", "(No title)")
            parts.append(f"{day} {time_str}: {summary}.")

    text = " ".join(parts)

    # Trim to max words
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
        # End at last sentence boundary
        last_period = text.rfind(".")
        if last_period > 0:
            text = text[: last_period + 1]

    # Limit to 4 sentences
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    if len(sentences) > MAX_SENTENCES:
        sentences = sentences[:MAX_SENTENCES]
        text = ". ".join(sentences) + ("." if sentences else "")

    return text


def save_summary(summary: str, output_dir: Path, date_str: str) -> Path:
    """Write summary to weekly-brief-YYYY-MM-DD.txt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"weekly-brief-{date_str}.txt"
    path.write_text(summary, encoding="utf-8")
    return path
