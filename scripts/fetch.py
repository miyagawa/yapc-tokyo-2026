#!/usr/bin/env python3
"""Fetch the YAPC::Tokyo 2026 timetable from fortee and write data/ + ics/.

Usage: python3 scripts/fetch.py
Only uses the Python standard library.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

SOURCE = "https://fortee.jp/yapc-tokyo-2026/api/timetable"
OFFICIAL = "https://fortee.jp/yapc-tokyo-2026/timetable"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = timezone(timedelta(hours=9))
CAL_NAME = "YAPC::Tokyo 2026 (非公式)"


def fetch():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "yapc-tokyo-2026-mobile-timetable"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["timetable"]


def normalize(items):
    out = []
    for x in items:
        track = x.get("track") or {}
        sp = x.get("speaker") or {}
        e = {
            "id": x["uuid"],
            "type": x["type"],
            "title": x.get("title", "").strip(),
            "track": track.get("name"),
            "track_sort": track.get("sort", 99),
            "start": x.get("starts_at"),
            "length": x.get("length_min"),
            "url": x.get("url"),
            "speaker": sp.get("name"),
            "twitter": sp.get("twitter"),
            "abstract": (x.get("abstract") or "").replace("\r\n", "\n").strip(),
        }
        out.append({k: v for k, v in e.items() if v not in (None, "")})
    out.sort(key=lambda e: (e.get("start") or "9999", e.get("track_sort", 99)))
    return out


# ---------- iCalendar ----------

def ics_escape(s):
    return (s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n"))


def fold(line):
    """Fold to 75 octets per RFC 5545 without splitting UTF-8 sequences."""
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    parts, cur, limit = [], b"", 75
    for ch in line:
        cb = ch.encode("utf-8")
        if len(cur) + len(cb) > limit:
            parts.append(cur.decode("utf-8"))
            cur, limit = b"", 74  # continuation lines start with a space
        cur += cb
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def vevent(e, stamp):
    start = datetime.fromisoformat(e["start"])
    end = start + timedelta(minutes=e.get("length") or 0)
    title = e["title"]
    if e.get("speaker") and e["type"] == "talk":
        title = f"{title} — {e['speaker']}"
    desc = []
    if e.get("speaker"):
        desc.append(f"登壇者: {e['speaker']}")
    if e.get("url"):
        desc.append(e["url"])
    if e.get("abstract"):
        desc.append("")
        desc.append(e["abstract"])
    lines = [
        "BEGIN:VEVENT",
        f"UID:{e['id']}@miyagawa.github.io",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{utc(start)}",
        f"DTEND:{utc(end)}",
        f"SUMMARY:{ics_escape(title)}",
        f"LOCATION:{ics_escape(e.get('track') or '')}",
    ]
    if desc:
        lines.append(f"DESCRIPTION:{ics_escape(chr(10).join(desc))}")
    if e.get("url"):
        lines.append(f"URL:{e['url']}")
    lines.append("END:VEVENT")
    return lines


def calendar(events, stamp, name=CAL_NAME):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//yapc-tokyo-2026 unofficial mobile timetable//JA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(name)}",
        "X-WR-TIMEZONE:Asia/Tokyo",
    ]
    for e in events:
        lines += vevent(e, stamp)
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def main():
    events = normalize(fetch())
    if not events:
        sys.exit("no events fetched; keeping existing data")
    now = datetime.now(JST)
    stamp = utc(now)
    data = {
        "fetched_at": now.isoformat(timespec="seconds"),
        "source": SOURCE,
        "official": OFFICIAL,
        "events": events,
    }
    write("data/timetable.json", json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    scheduled = [e for e in events if e.get("start")]
    talks = [e for e in scheduled if e["type"] == "talk" or e.get("speaker")]
    write("ics/all.ics", calendar(scheduled, stamp))
    write("ics/talks.ics", calendar(talks, stamp, CAL_NAME + " トークのみ"))
    for day in sorted({e["start"][:10] for e in scheduled}):
        write(f"ics/{day}.ics", calendar([e for e in scheduled if e["start"].startswith(day)], stamp,
                                         f"{CAL_NAME} {day}"))
    # one file per event, so each card can offer "カレンダーに追加"
    ev_dir = os.path.join(ROOT, "ics", "events")
    if os.path.isdir(ev_dir):
        for f in os.listdir(ev_dir):
            os.remove(os.path.join(ev_dir, f))
    for e in scheduled:
        write(f"ics/events/{e['id']}.ics", calendar([e], stamp))
    print(f"{len(events)} entries ({len(scheduled)} scheduled), fetched {data['fetched_at']}")


if __name__ == "__main__":
    main()
