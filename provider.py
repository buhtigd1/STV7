import json
import requests
from datetime import datetime, timedelta, timezone

SOURCE_URL = "https://raw.githubusercontent.com/mdjamsad9/dudetvapi/main/public_decrypted/events_with_channels.json"
OUTPUT_FILE = "stv7.m3u"
LOG_FILE = "stv7.log"

# Jakarta timezone (UTC+7)
JAKARTA_TZ = timezone(timedelta(hours=7))

def download(url: str) -> list:
    """Download and parse JSON from a URL."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def parse_date(date_str: str) -> datetime | None:
    """Parse date string into datetime object (UTC)."""
    try:
        return datetime.strptime(date_str.split(" +")[0], "%Y/%m/%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None

def build_m3u(events: list) -> str:
    """Build Kodi M3U playlist grouped by Jakarta event date (DD-MM-YYYY),
    excluding 'Dude', 'MLB', and 'NFL' channels, with event name and local start/end times in channel title.
    If channel name contains 'TSN', use custom logo."""
    sorted_events = sorted(
        events,
        key=lambda ev: parse_date(ev.get("eventInfo", {}).get("startTime", "")) or datetime.max.replace(tzinfo=timezone.utc)
    )

    lines = ["#EXTM3U\n"]
    for ev in sorted_events:
        start_time = ev.get("eventInfo", {}).get("startTime", "")
        end_time = ev.get("eventInfo", {}).get("endTime", "")
        event_title = ev.get("title", "")

        start_dt = parse_date(start_time)
        end_dt = parse_date(end_time)

        if start_dt:
            jakarta_start = start_dt.astimezone(JAKARTA_TZ)
            group = jakarta_start.strftime("%d-%m-%Y")
            start_str = jakarta_start.strftime("%H:%M")
        else:
            group = "UnknownDate"
            start_str = ""

        if end_dt:
            jakarta_end = end_dt.astimezone(JAKARTA_TZ)
            end_str = jakarta_end.strftime("%H:%M")
        else:
            end_str = ""

        for ch in ev.get("decoded_channels", []):
            channel_name = ch.get("title", "Unknown Channel")
            logo = ch.get("logo", "")
            link = ch.get("link", "")
            api = ch.get("api", "")

            # Skip unwanted channels
            if any(word in channel_name.lower() for word in ["dude", "mlb", "nfl"]):
                continue
            if not link:
                continue

            # Override logo if channel contains TSN
            if "tsn" in channel_name.lower():
                logo = "https://raw.githubusercontent.com/didikc/TV-Logo/main/logos/tsn.png"

            # Format: Start - End - Event - Channel
            if start_str and end_str:
                display_name = f"{start_str} - {end_str} - {event_title} - {channel_name}"
            elif start_str:
                display_name = f"{start_str} - {event_title} - {channel_name}"
            else:
                display_name = f"{event_title} - {channel_name}"

            lines.append(f'#EXTINF:-1 tvg-name="{channel_name}" tvg-logo="{logo}" group-title="{group}",{display_name}\n')

            # Widevine ClearKey properties if api exists
            if api and ".mpd" in link:
                lines.append("#KODIPROP:inputstreamaddon=inputstream.adaptive\n")
                lines.append("#KODIPROP:inputstream.adaptive.manifest_type=dash\n")
                lines.append("#KODIPROP:inputstream.adaptive.license_type=org.w3.clearkey\n")
                lines.append(f"#KODIPROP:inputstream.adaptive.license_key={api}\n")

            lines.append(f"{link}\n")
    return "".join(lines)

def main():
    log_entries = [f"Run started at {datetime.now().isoformat()}"]
    try:
        events = download(SOURCE_URL)
        playlist = build_m3u(events)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(playlist)
        log_entries.append(f"✅ Playlist written to {OUTPUT_FILE}")
    except Exception as e:
        log_entries.append(f"❌ Error: {e}")
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        logf.write("\n".join(log_entries))

if __name__ == "__main__":
    main()
