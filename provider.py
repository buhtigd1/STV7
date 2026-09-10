import json
import requests
from datetime import datetime

# Raw GitHub link for the JSON file
SOURCE_URL = "https://raw.githubusercontent.com/mdjamsad9/dudetvapi/main/public_decrypted/events_with_channels.json"

OUTPUT_FILE = "stv7.m3u"
LOG_FILE    = "stv7.log"

HEADER = "#EXTM3U"

def download(url: str) -> dict:
    """Download and parse JSON from a URL."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"❌ Failed to fetch {url}: {e}")

def build_m3u(data: dict) -> str:
    """Convert events_with_channels JSON into Kodi M3U playlist."""
    lines = [HEADER + "\n"]

    for event in data.get("events", []):
        event_name = event.get("event_name", "General")
        for ch in event.get("channels", []):
            name = ch.get("name", "Unknown")
            logo = ch.get("logo", "")
            stream = ch.get("url") or ch.get("stream_url")
            if not stream:
                continue

            # EXTINF line with grouping by event
            lines.append(
                f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{event_name}",{name}\n'
                f'{stream}\n'
            )
    return "".join(lines)

def main():
    log_entries = [f"Run started at {datetime.now().isoformat()}"]

    try:
        print("Downloading JSON…")
        data = download(SOURCE_URL)
        print("Building playlist…")
        playlist = build_m3u(data)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(playlist)
        log_entries.append(f"✅ Playlist written to {OUTPUT_FILE}")

    except Exception as e:
        log_entries.append(str(e))

    # Always write a log file
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        for entry in log_entries:
            logf.write(entry + "\n")

    print(f"✅ Done: saved to {OUTPUT_FILE}, log written to {LOG_FILE}")

if __name__ == "__main__":
    main()
