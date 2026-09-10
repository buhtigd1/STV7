import json
import requests
from datetime import datetime

SOURCE_URL = "https://raw.githubusercontent.com/mdjamsad9/dudetvapi/main/public_decrypted/events_with_channels.json"
OUTPUT_FILE = "stv7.m3u"
LOG_FILE = "stv7.log"

def download(url: str) -> list:
    """Download and parse JSON from a URL."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def parse_date(date_str: str) -> datetime | None:
    """Parse startTime string into datetime object."""
    try:
        return datetime.strptime(date_str.split(" +")[0], "%Y/%m/%d %H:%M:%S")
    except Exception:
        return None

def build_m3u(events: list) -> str:
    """Build Kodi M3U playlist grouped by event date (DD-MM-YYYY), excluding 'Dude' channels."""
    # Sort events by startTime ascending
    sorted_events = sorted(
        events,
        key=lambda ev: parse_date(ev.get("eventInfo", {}).get("startTime", "")) or datetime.max
    )

    lines = ["#EXTM3U\n"]
    for ev in sorted_events:
        start_time = ev.get("eventInfo", {}).get("startTime", "")
        date_obj = parse_date(start_time)
        group = date_obj.strftime("%d-%m-%Y") if date_obj else "UnknownDate"

        for ch in ev.get("decoded_channels", []):
            name = ch.get("title", "Unknown Channel")
            logo = ch.get("logo", "")
            link = ch.get("link", "")
            api = ch.get("api", "")

            # Skip channels containing "Dude" (case-insensitive)
            if "dude" in name.lower():
                continue

            if not link:
                continue

            # EXTINF line
            lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')

            # Widevine ClearKey properties if api exists
            if api and ".mpd" in link:
                lines.append("#KODIPROP:inputstreamaddon=inputstream.adaptive\n")
                lines.append("#KODIPROP:inputstream.adaptive.manifest_type=dash\n")
                lines.append("#KODIPROP:inputstream.adaptive.license_type=org.w3.clearkey\n")
                lines.append(f"#KODIPROP:inputstream.adaptive.license_key={api}\n")

            # Stream URL
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
