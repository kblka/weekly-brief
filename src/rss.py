"""
Phase 4: RSS feed for podcast-style delivery.

Generates feed.xml for private podcast consumption in Spotify.
Add RSS URL in Spotify: Settings → Add podcast by RSS.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from xml.dom import minidom


def _escape_xml(s: str) -> str:
    """Escape special XML characters."""
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_rss_feed(
    episodes: List[Dict],
    output_path: Path,
    base_url: str,
    show_title: str = "My Weekly Brief",
    show_description: str = "A private weekly brief of your upcoming calendar events.",
    image_url: Optional[str] = None,
) -> Path:
    """
    Generate RSS feed XML for podcast episodes.

    Args:
        episodes: List of {"date_str": "YYYY-MM-DD", "mp3_filename": "weekly-brief-YYYY-MM-DD.mp3"}
        output_path: Where to write feed.xml
        base_url: Base URL for MP3 and feed (e.g. https://example.com/brief/)
        show_title: Podcast show title
        show_description: Podcast show description

    Returns:
        Path to feed.xml
    """
    base_url = base_url.rstrip("/")
    now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    rss = ET.Element(
        "rss",
        version="2.0",
        attrib={
            "xmlns:atom": "http://www.w3.org/2005/Atom",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        },
    )
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = show_title
    ET.SubElement(channel, "description").text = show_description
    ET.SubElement(channel, "link").text = base_url
    ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
    if image_url:
        img = ET.SubElement(channel, f"{{{ITUNES_NS}}}image", attrib={"href": image_url})
        # Also add standard image for broader compatibility
        img_elem = ET.SubElement(channel, "image")
        ET.SubElement(img_elem, "url").text = image_url
        ET.SubElement(img_elem, "title").text = show_title
    ET.SubElement(channel, f"{{{ITUNES_NS}}}explicit").text = "no"
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = now
    ET.SubElement(channel, "generator").text = "Sunday Weekly Brief"

    for ep in episodes:
        date_str = ep["date_str"]
        mp3_filename = ep.get("mp3_filename", f"weekly-brief-{date_str}.mp3")
        mp3_url = f"{base_url}/{mp3_filename}"
        title = f"Weekly Brief {date_str}"
        pub_date = _date_to_rfc2822(date_str)

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "description").text = f"Weekly brief for the week of {date_str}."
        ET.SubElement(item, "pubDate").text = pub_date
        ET.SubElement(item, "guid", attrib={"isPermaLink": "false"}).text = f"weekly-brief-{date_str}"
        ET.SubElement(
            item,
            "enclosure",
            attrib={
                "url": mp3_url,
                "type": "audio/mpeg",
                "length": str(ep.get("size_bytes", 0)),
            },
        )

    xml_str = ET.tostring(rss, encoding="unicode", default_namespace="")
    pretty = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding=None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pretty, encoding="utf-8")
    return output_path


def _date_to_rfc2822(date_str: str) -> str:
    """Convert YYYY-MM-DD to RFC 2822 for pubDate."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a, %d %b %Y 00:00:00 GMT")


def append_episode_to_feed(
    date_str: str,
    mp3_path: Path,
    feed_path: Path,
    base_url: str,
    show_title: str = "My Weekly Brief",
    show_description: str = "A private weekly brief of your upcoming calendar events.",
) -> Path:
    """
    Add a new episode to existing feed, or create feed if it doesn't exist.

    Reads existing feed to get episodes, appends new one, writes back.
    """
    episodes = []

    if feed_path.exists():
        tree = ET.parse(feed_path)
        root = tree.getroot()
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item"):
                guid = item.find("guid")
                if guid is not None and guid.text:
                    # Extract date from guid like "weekly-brief-2025-02-03"
                    parts = guid.text.split("-")
                    if len(parts) >= 4:
                        ep_date = f"{parts[-3]}-{parts[-2]}-{parts[-1]}"
                        enc = item.find("enclosure")
                        size = int(enc.get("length", 0)) if enc is not None else 0
                        episodes.append(
                            {
                                "date_str": ep_date,
                                "mp3_filename": f"weekly-brief-{ep_date}.mp3",
                                "size_bytes": size,
                            }
                        )

    # Add new episode
    size_bytes = mp3_path.stat().st_size if mp3_path.exists() else 0
    new_ep = {
        "date_str": date_str,
        "mp3_filename": f"weekly-brief-{date_str}.mp3",
        "size_bytes": size_bytes,
    }
    if not any(e["date_str"] == date_str for e in episodes):
        episodes.append(new_ep)

    # Sort by date descending (newest first)
    episodes.sort(key=lambda e: e["date_str"], reverse=True)

    image_url = f"{base_url.rstrip('/')}/cover.png" if base_url else None
    return generate_rss_feed(
        episodes=episodes,
        output_path=feed_path,
        base_url=base_url,
        show_title=show_title,
        show_description=show_description,
        image_url=image_url,
    )
