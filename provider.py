import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

SOURCE_URL = "https://raw.githubusercontent.com/mdjamsad9/dudetvapi/main/public_decrypted/events_with_channels.json"
OUTPUT_FILE = "stv7.m3u"
LOG_FILE = "stv7.log"

# Jakarta timezone (UTC+7)
JAKARTA_TZ = timezone(timedelta(hours=7))


def download(url: str) -> list:
    """Download and parse JSON."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_date(date_str: str):
    """Parse source datetime into UTC."""
    try:
        return datetime.strptime(
            date_str.split(" +")[0],
            "%Y/%m/%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def split_url_headers(url: str):
    """
    Split IPTV-style URL headers:

    https://stream.m3u8|Referer=https://site.com&Origin=https://site.com

    Returns:
        base_url, headers_dict
    """
    if "|" not in url:
        return url.strip(), {}

    base_url, header_string = url.split("|", 1)

    headers = {}

    for item in header_string.split("&"):
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        key = key.strip().lower()
        value = unquote(value.strip())

        headers[key] = value

    return base_url.strip(), headers


def write_headers(lines: list, headers: dict):
    """Convert IPTV headers into Kodi properties."""

    referer = headers.get("referer")
    origin = headers.get("origin")
    user_agent = headers.get("user-agent")

    if referer:
        lines.append(f"#KODIPROP:http-referer={referer}\n")

    if origin:
        lines.append(f"#KODIPROP:http-origin={origin}\n")

    if user_agent:
        lines.append(f"#EXTVLCOPT:http-user-agent={user_agent}\n")


def build_m3u(events: list) -> str:
    """
    Build Kodi-compatible M3U playlist.

    Features:
    - Group by Jakarta date.
    - Display local start/end times.
    - Remove Dude / MLB / NFL channels.
    - Convert URL headers into Kodi properties.
    - Preserve Widevine ClearKey settings.
    """

    sorted_events = sorted(
        events,
        key=lambda ev: (
            parse_date(
                ev.get("eventInfo", {}).get("startTime", "")
            )
            or datetime.max.replace(tzinfo=timezone.utc)
        )
    )

    lines = ["#EXTM3U\n"]

    for ev in sorted_events:

        event_title = ev.get("title", "")

        start_dt = parse_date(
            ev.get("eventInfo", {}).get("startTime", "")
        )

        end_dt = parse_date(
            ev.get("eventInfo", {}).get("endTime", "")
        )

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

            if not link:
                continue

            # Skip unwanted channels
            if any(
                x in channel_name.lower()
                for x in ["dude", "mlb", "nfl"]
            ):
                continue

            if start_str and end_str:
                display_name = (
                    f"{start_str} - {end_str} - "
                    f"{event_title} - {channel_name}"
                )
            elif start_str:
                display_name = (
                    f"{start_str} - "
                    f"{event_title} - {channel_name}"
                )
            else:
                display_name = (
                    f"{event_title} - {channel_name}"
                )

            lines.append(
                f'#EXTINF:-1 tvg-name="{channel_name}" '
                f'tvg-logo="{logo}" '
                f'group-title="{group}",'
                f'{display_name}\n'
            )

            # Parse IPTV URL headers
            base_url, headers = split_url_headers(link)

            # Kodi-compatible headers
            write_headers(lines, headers)

            # DASH / Widevine ClearKey
            if api and ".mpd" in base_url.lower():

                lines.append(
                    "#KODIPROP:inputstreamaddon=inputstream.adaptive\n"
                )

                lines.append(
                    "#KODIPROP:inputstream.adaptive.manifest_type=dash\n"
                )

                lines.append(
                    "#KODIPROP:inputstream.adaptive.license_type=org.w3.clearkey\n"
                )

                lines.append(
                    f"#KODIPROP:inputstream.adaptive.license_key={api}\n"
                )

            lines.append(f"{base_url}\n")

    return "".join(lines)


def main():

    log_entries = [
        f"Run started at {datetime.now().isoformat()}"
    ]

    try:

        events = download(SOURCE_URL)

        playlist = build_m3u(events)

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(playlist)

        log_entries.append(
            f"✅ Playlist written to {OUTPUT_FILE}"
        )

    except Exception as e:

        log_entries.append(
            f"❌ Error: {str(e)}"
        )

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8"
    ) as logf:
        logf.write("\n".join(log_entries))


if __name__ == "__main__":
    main()
