"""
Phase 2: Summarize events.

Turns event list into 2–4 spoken sentences, under 150 words.
Uses Google Gemini for natural Czech sentences when API key is set;
otherwise falls back to template-based Czech summary.
"""

import logging
from collections import defaultdict

log = logging.getLogger(__name__)
from datetime import datetime
from pathlib import Path

DAY_NAMES_EN = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]
DAY_NAMES_CS = [
    "Pondělí", "Úterý", "Středa", "Čtvrtek",
    "Pátek", "Sobota", "Neděle",
]

MAX_WORDS = 450
MAX_SENTENCES = 18  # Allow more sentences for natural flow


def _format_time_czech(dt: datetime, is_all_day: bool) -> str:
    """Czech time format: 10:00 or celý den."""
    if is_all_day:
        return "celý den"
    return f"{dt.hour}:{dt.minute:02d}"


def _format_time_simple(dt: datetime) -> str:
    """e.g. 9am, 2pm (English fallback)."""
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


def group_events_by_day(events, day_names=None):
    """Group events by day of week."""
    day_names = day_names or DAY_NAMES_EN
    by_day = defaultdict(list)
    for ev in events:
        start = ev["start"]
        if hasattr(start, "weekday"):
            weekday = start.weekday()
        else:
            weekday = start.to_pydatetime().weekday() if hasattr(start, "to_pydatetime") else 0
        day_name = day_names[weekday]
        by_day[day_name].append(ev)
    return dict(by_day)


def _events_to_prompt_text(events, day_names, time_fmt_czech=True):
    """Build structured event list for Gemini prompt."""
    by_day = group_events_by_day(events, day_names)
    lines = []
    for day in day_names:
        if day not in by_day:
            continue
        for ev in by_day[day]:
            time_str = (
                _format_time_czech(ev["start"], ev.get("is_all_day", False))
                if time_fmt_czech
                else ("celý den" if ev.get("is_all_day", False) else _format_time_simple(ev["start"]))
            )
            title = ev.get("summary", "(bez názvu)")
            creator_email = ev.get("creator_email", "")
            creator_info = f" [založeno: {creator_email}]" if creator_email else ""
            lines.append(f"- {day} {time_str}: {title}{creator_info}")
    return "\n".join(lines) if lines else ""


def _generate_summary_gemini(events: list, api_key: str) -> str:
    """Use Google Gemini to generate natural Czech sentences."""
    try:
        import google.generativeai as genai
    except ImportError:
        return _generate_summary_fallback_czech(events)

    genai.configure(api_key=api_key)
    # Use lite model for better free-tier quota (gemini-2.5-flash-lite or gemini-2.0-flash-lite)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    event_text = _events_to_prompt_text(events, DAY_NAMES_CS)
    if not event_text:
        return "Tento týden nemáte naplánované žádné události."

    prompt = f"""Převeď tento seznam událostí z kalendáře do přirozených vět v češtině. Výstup musí být PLNÉ VĚTY, ne výčet ani seznam.

PRAVIDLA:
1. Piš výhradně plné věty (např. "V pondělí vás v 10 hodin čeká návštěva u lékaře." místo "Pondělí 10:00: Lékař").
2. Odhadni typ události z názvu a vyjádři přirozeně: narozeniny → "máte narozeninovou oslavu", kino → "jdete do kina", lékař/doktor → "návštěva u lékaře", pub quiz → "jdete na pub quiz", rodina → "rodinná akce" atd.
3. Časy: "v 10 hodin", "odpoledne ve 2", "celý den" – českým mluveným stylem.
4. Začněte větami jako "V pondělí…", "V úterý…", "Ve středu vás čeká…", "V pátek máte…".
5. U každé události VŽDY uveď, kdo ji založil, ale jazykově to obměňuj:
   - Pokud [založeno: kabelkape@gmail.com] → zmíň Kabise (např. "to si tam dal Kabis", "Kabis si to naplánoval", "podle Kabise", "Kabis to založil")
   - Pokud [založeno: mariana.smidova1@gmail.com] → zmíň Mari (např. "to si tam dala Mari", "Mari to naplánovala", "podle Mari", "Mari to založila")
   - Obměňuj formulace, aby to znělo přirozeně a neopakovalo se
   - U ostatních emailů tvůrce nevypisuj
6. Max 450 slov, 12–18 vět. Piš plynule, jako by vám někdo vyprávěl o vašem týdnu.
7. Vygeneruj POUZE text (žádné uvozovky, žádný úvod ani závěr).

PŘÍKLAD dobrého výstupu:
V pondělí vás v 10 hodin čeká návštěva u lékaře, to si tam dal Kabis. V úterý odpoledne jdete do kina podle Mari. Ve středu máte celý den rodinnou oslavu narozenin, Mari to naplánovala.

Události:
{event_text}
"""

    response = model.generate_content(prompt)
    text = (response.text or "").strip()
    if not text:
        log.warning("Gemini returned empty response, using fallback")
        return _generate_summary_fallback_czech(events)
    log.info("Summary generated by Gemini (gemini-2.5-flash-lite)")

    # Trim to max words and sentences
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
        last_period = text.rfind(".")
        if last_period > 0:
            text = text[: last_period + 1]
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    if len(sentences) > MAX_SENTENCES:
        sentences = sentences[:MAX_SENTENCES]
        text = ". ".join(sentences) + ("." if sentences else "")
    return text


def _event_to_sentence(day: str, ev: dict) -> str:
    """Turn one event into a natural Czech sentence."""
    title = (ev.get("summary") or "").strip() or "(bez názvu)"
    tl = title.lower()
    is_all_day = ev.get("is_all_day", False)

    day_prep = {"Pondělí": "V pondělí", "Úterý": "V úterý", "Středa": "Ve středu",
                "Čtvrtek": "Ve čtvrtek", "Pátek": "V pátek", "Sobota": "V sobotu",
                "Neděle": "V neděli"}.get(day, f"V {day.lower()}")

    if is_all_day:
        time_phrase = "celý den"
    else:
        h, m = ev["start"].hour, ev["start"].minute
        prep = "ve" if h in (18, 19, 20) else "v"
        time_phrase = f"{prep} {h}:{m:02d}" if m else f"{prep} {h} hodin"

    # Infer event type and build natural phrase
    if any(k in tl for k in ["narozky", "narozeniny"]):
        phrase = f"slavíte {title}" if len(title) < 30 else "máte narozeninovou oslavu"
    elif any(k in tl for k in ["mudr", "lékař", "doktor", "dr."]):
        phrase = f"máte návštěvu u lékaře {title}"
    elif any(k in tl for k in ["kvíz", "quiz"]):
        phrase = f"jdete na {title}"
    elif "ples" in tl:
        # "Ples Honzík" -> "jdete na ples Honzík"
        rest = title.replace("Ples ", "").replace("ples ", "").strip()
        phrase = f"jdete na ples {rest}" if rest else "jdete na ples"
    elif any(k in tl for k in ["kino"]):
        phrase = "jdete do kina"
    else:
        phrase = f"máte {title}"

    if is_all_day:
        return f"{day_prep} {time_phrase} {phrase}."
    return f"{day_prep} v {time_phrase} {phrase}."


def _generate_summary_fallback_czech(events: list) -> str:
    """Template-based Czech summary in natural sentences when Gemini is not available."""
    if not events:
        return "Tento týden nemáte naplánované žádné události."

    by_day = group_events_by_day(events, DAY_NAMES_CS)
    parts = []
    for day in DAY_NAMES_CS:
        if day not in by_day:
            continue
        for ev in by_day[day]:
            parts.append(_event_to_sentence(day, ev))

    text = " ".join(parts)
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
        last_period = text.rfind(".")
        if last_period > 0:
            text = text[: last_period + 1]
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    if len(sentences) > MAX_SENTENCES:
        sentences = sentences[:MAX_SENTENCES]
        text = ". ".join(sentences) + ("." if sentences else "")
    return text


def generate_summary(
    events: list,
    max_words: int = MAX_WORDS,
    gemini_api_key: str = "",
    language: str = "cs",
) -> str:
    """
    Convert event list to 2–4 spoken sentences.

    If gemini_api_key is set and language is cs, uses Gemini for natural Czech.
    Otherwise uses template-based Czech (or English if language != cs).
    """
    if not events and language == "cs":
        return "Tento týden nemáte naplánované žádné události."
    if not events:
        return "You have no events scheduled for the coming week."

    if language == "cs" and gemini_api_key:
        try:
            return _generate_summary_gemini(events, gemini_api_key)
        except Exception as e:
            log.warning("Gemini failed, using fallback: %s", e)
            return _generate_summary_fallback_czech(events)
    if language == "cs":
        log.info("GEMINI_API_KEY not set, using template fallback")
        return _generate_summary_fallback_czech(events)

    # English fallback (original logic)
    by_day = group_events_by_day(events, DAY_NAMES_EN)
    parts = []
    for day in DAY_NAMES_EN:
        if day not in by_day:
            continue
        for ev in by_day[day]:
            time_str = (
                "all day"
                if ev.get("is_all_day", False)
                else _format_time_simple(ev["start"])
            )
            parts.append(f"{day} {time_str}: {ev.get('summary', '(No title)')}.")
    text = " ".join(parts)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
        last_period = text.rfind(".")
        if last_period > 0:
            text = text[: last_period + 1]
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
