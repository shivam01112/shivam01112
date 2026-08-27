#!/usr/bin/env python3
"""Render a real, verifiable table of automated profile-pulse commits into README.md.

The pulse log (activity/profile-pulse.md) is the source of truth: every line in
it corresponds to a real commit the `Daily Profile Pulse` workflow made. This
script summarizes the most recent days from that log into a small markdown
table so the README shows honest, checkable data instead of a decorative
placeholder.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

START = "<!--START_SECTION:pulse_table-->"
END = "<!--END_SECTION:pulse_table-->"

LINE_RE = re.compile(
    r"^- (?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) UTC - "
    r"automated profile pulse (?P<index>\d+)/(?P<total>\d+)$"
)


def parse_log(text: str) -> list[tuple[str, str, int]]:
    """Return (date, latest_time, pulse_count) tuples, most recent day first."""
    by_date: dict[str, tuple[str, int]] = {}
    for line in text.splitlines():
        match = LINE_RE.match(line.strip())
        if not match:
            continue
        date = match.group("date")
        time = match.group("time")
        total = int(match.group("total"))
        by_date[date] = (time, total)
    return [(date, time, total) for date, (time, total) in sorted(by_date.items(), reverse=True)]


def render_table(rows: list[tuple[str, str, int]], limit: int = 7) -> str:
    if not rows:
        return "_No automated pulses recorded yet._"

    header = "| Date (UTC) | Pulses | Last logged at |\n| --- | --- | --- |"
    lines = [header]
    for date, time, total in rows[:limit]:
        lines.append(f"| {date} | {total} | {time} |")
    return "\n".join(lines)


def update_readme(path: Path, table: str) -> bool:
    original = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    replacement = f"{START}\n{table}\n{END}"
    updated, count = pattern.subn(replacement, original)
    if count != 1:
        raise ValueError(f"Expected exactly one pulse-table section in {path}; found {count}.")
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=Path("activity/profile-pulse.md"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()

    rows = parse_log(args.log.read_text(encoding="utf-8"))
    changed = update_readme(args.readme, render_table(rows))
    print("Updated pulse table." if changed else "Pulse table is already current.")


if __name__ == "__main__":
    main()
