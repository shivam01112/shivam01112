#!/usr/bin/env python3
"""Render a real weekly-contribution bar chart (SVG) from the GitHub GraphQL API.

Unlike the hand-drawn decorative charts elsewhere in assets/, this SVG is
generated from the account's actual public contribution calendar, so the bars
reflect real GitHub activity rather than an illustration.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_calendar(login: str, token: str) -> dict[str, Any]:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "profile-readme-contribution-chart",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def weekly_totals(calendar: dict[str, Any], weeks: int = 12) -> list[tuple[str, int]]:
    """Return the last `weeks` (week_end_date, total_contributions) pairs, oldest first."""
    all_weeks = calendar.get("weeks", [])
    totals: list[tuple[str, int]] = []
    for week in all_weeks:
        days = week.get("contributionDays", [])
        if not days:
            continue
        total = sum(day.get("contributionCount", 0) for day in days)
        end_date = days[-1].get("date", "")
        totals.append((end_date, total))
    return totals[-weeks:]


def render_svg(totals: list[tuple[str, int]], total_contributions: int) -> str:
    width, height = 1280, 320
    pad_left, pad_right, pad_top, pad_bottom = 60, 40, 70, 50
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    max_value = max((v for _, v in totals), default=0) or 1
    bar_count = max(len(totals), 1)
    gap = 10
    bar_w = (plot_w - gap * (bar_count - 1)) / bar_count

    bars = []
    labels = []
    for index, (end_date, value) in enumerate(totals):
        bar_h = (value / max_value) * (plot_h - 20)
        x = pad_left + index * (bar_w + gap)
        y = pad_top + (plot_h - bar_h)
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'rx="4" fill="url(#barGradient)" filter="url(#barGlow)">'
            f'<title>{end_date}: {value} contributions</title>'
            f'<animate attributeName="height" from="0" to="{bar_h:.1f}" dur="1s" fill="freeze" />'
            f'<animate attributeName="y" from="{pad_top + plot_h:.1f}" to="{y:.1f}" dur="1s" fill="freeze" />'
            f"</rect>"
        )
        if index % 2 == 0 or index == bar_count - 1:
            short_date = end_date[5:] if end_date else ""
            labels.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{height - pad_bottom + 20}" '
                f'fill="#94A3B8" font-family="Consolas, monospace" font-size="10" '
                f'text-anchor="middle">{short_date}</text>'
            )

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="rcTitle rcDesc">
  <title id="rcTitle">Real weekly contribution activity</title>
  <desc id="rcDesc">Bar chart of real GitHub contributions for the last {bar_count} weeks, sourced live from the GitHub GraphQL API.</desc>
  <defs>
    <linearGradient id="rcBg" x1="0" y1="0" x2="{width}" y2="{height}" gradientUnits="userSpaceOnUse">
      <stop stop-color="#020617"/>
      <stop offset=".5" stop-color="#0B3B5C"/>
      <stop offset="1" stop-color="#04342F"/>
    </linearGradient>
    <linearGradient id="barGradient" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#0EA5E9"/>
      <stop offset=".6" stop-color="#67E8F9"/>
      <stop offset="1" stop-color="#A78BFA"/>
    </linearGradient>
    <filter id="barGlow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="rcClip"><rect width="{width}" height="{height}" rx="28"/></clipPath>
  </defs>
  <g clip-path="url(#rcClip)">
    <rect width="{width}" height="{height}" fill="url(#rcBg)"/>
  </g>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="27" stroke="#164E63" stroke-width="2"/>
  <text x="48" y="38" fill="#67E8F9" font-family="Consolas, monospace" font-size="14" font-weight="800" letter-spacing="2">REAL WEEKLY CONTRIBUTIONS · LIVE FROM GITHUB API</text>
  <text x="{width - 48}" y="38" fill="#A78BFA" font-family="Consolas, monospace" font-size="12" text-anchor="end">{total_contributions} total (last year)</text>
  {''.join(bars)}
  {''.join(labels)}
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default=os.getenv("GITHUB_REPOSITORY_OWNER", "shivam01112"))
    parser.add_argument("--out", type=Path, default=Path("assets/weekly-activity-real.svg"))
    parser.add_argument("--weeks", type=int, default=12)
    parser.add_argument("--calendar-file", type=Path, help="Skip the network call and use this JSON file instead.")
    args = parser.parse_args()

    if args.calendar_file:
        calendar = json.loads(args.calendar_file.read_text(encoding="utf-8"))
    else:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is required to fetch the contribution calendar.")
        calendar = fetch_calendar(args.login, token)

    totals = weekly_totals(calendar, weeks=args.weeks)
    svg = render_svg(totals, calendar.get("totalContributions", 0))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
