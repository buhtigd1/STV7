import json
import requests
from datetime import datetime

SOURCE_URL = "https://raw.githubusercontent.com/mdjamsad9/dudetvapi/main/public_decrypted/events_with_channels.json"
OUTPUT_FILE = "stv7.m3u"
LOG_FILE = "stv7.log"

def download(url: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def extract_stream(ch: dict) -> str | None:
    """Try multiple possible keys for stream URL."""
    for key in ["url", "stream_url", "link", "play_url"]:
        if key in ch and ch[key]:
            return ch[key]
    # Example of nested source list
    if "sources" in ch and isinstance(ch["sources"], list) and ch["sources"]:
        return ch["sources"][0].get("url")
    return None

def build_m3u(data: dict) -> str:
    lines = ["#EXTM3U\n"]
    for event in data.get("events", []):
        event_name = event.get("event_name", "General")
        for ch in event.get("channels", []):
            name = ch.get("name", "Unknown")
            logo = ch.get("logo", "")
            stream = extract_stream(ch)
            if not stream:
                continue
            lines.append(
                f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{event_name}",{name}\n'
                f'{stream}\n'
            )
    return "".join(lines)

def main():
    log_entries = [f"Run started at {datetime.now().isoformat()}"]
    try:
        data = download(SOURCE_URL)
        playlist = build_m3u(data)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(playlist)
        log_entries.append(f"✅ Playlist written to {OUTPUT_FILE}")
    except Exception as e:
        log_entries.append(f"❌ Error: {e}")
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        logf.write("\n".join(log_entries))

if __name__ == "__main__":
    main()
