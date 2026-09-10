import json
import requests
import base64
from datetime import datetime

SOURCE_URL = "https://raw.githubusercontent.com/mdjamsad9/dudetvapi/main/public_decrypted/events_with_channels.json"
OUTPUT_FILE = "stv7.m3u"
LOG_FILE = "stv7.log"

def download(url: str) -> list:
    """Download and parse JSON from a URL."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def parse_api(api_str: str) -> str | None:
    """Decode base64 api field into kid:key format for Kodi ClearKey."""
    if not api_str:
        return None
    try:
        decoded = base64.b64decode(api_str).decode("utf-8")
        if ":" in decoded:
            kid, key = decoded.split(":", 1)
            return f"{kid}:{key}"
    except Exception:
        return None
    return None

def build_m3u(events: list) -> str:
    """Build Kodi M3U playlist with Widevine ClearKey when available."""
    lines = ["#EXTM3U\n"]
    for ev in events:
        group = ev.get("title", "General")
        for ch in ev.get("decoded_channels", []):
            name = ch.get("title", "Unknown Channel")
            logo = ch.get("logo", "")
            link = ch.get("link", "")
            api = parse_api(ch.get("api", ""))

            if not link:
                continue

            # EXTINF line
            lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')

            # Widevine ClearKey properties if api exists
            if api and link.endswith(".mpd"):
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
