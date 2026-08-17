#!/usr/bin/env python3
"""Render a user's latest public GitHub events into README.md."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any


START = "<!--START_SECTION:activity-->"
END = "<!--END_SECTION:activity-->"


def markdown_text(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()#+.!|<>])", r"\\\1", value)


def repo_link(event: dict[str, Any]) -> str:
    name = event.get("repo", {}).get("name", "GitHub")
    return f"[`{name}`](https://github.com/{name})"


def describe(event: dict[str, Any]) -> str | None:
    event_type = event.get("type")
    payload = event.get("payload", {})
    repo = repo_link(event)

    if event_type == "PushEvent":
        count = len(payload.get("commits", [])) or payload.get("size", 0)
        if not count:
            return f"Pushed updates to {repo}"
        noun = "commit" if count == 1 else "commits"
        return f"Pushed **{count} {noun}** to {repo}"

    if event_type == "PullRequestEvent":
        pull = payload.get("pull_request", {})
        number = pull.get("number", "")
        title = markdown_text(pull.get("title", "pull request"))
        url = pull.get("html_url", f"https://github.com/{event['repo']['name']}/pull/{number}")
        action = "merged" if pull.get("merged") else payload.get("action", "updated")
        return f"{action.capitalize()} PR [#{number} — {title}]({url}) in {repo}"

    if event_type == "IssuesEvent":
        issue = payload.get("issue", {})
        number = issue.get("number", "")
        title = markdown_text(issue.get("title", "issue"))
        url = issue.get("html_url", f"https://github.com/{event['repo']['name']}/issues/{number}")
        action = payload.get("action", "updated")
        return f"{action.capitalize()} issue [#{number} — {title}]({url}) in {repo}"

    if event_type == "IssueCommentEvent":
        issue = payload.get("issue", {})
        number = issue.get("number", "")
        url = payload.get("comment", {}).get("html_url", issue.get("html_url", ""))
        return f"Commented on [issue #{number}]({url}) in {repo}"

    if event_type == "CreateEvent":
        ref_type = payload.get("ref_type", "repository")
        ref = payload.get("ref")
        suffix = f" `{markdown_text(str(ref))}`" if ref else ""
        return f"Created {ref_type}{suffix} in {repo}"

    if event_type == "ReleaseEvent":
        release = payload.get("release", {})
        name = markdown_text(release.get("name") or release.get("tag_name", "release"))
        return f"Published [{name}]({release.get('html_url', '')}) in {repo}"

    return None


def render(events: list[dict[str, Any]], limit: int = 5) -> str:
    items: list[str] = []
    seen: set[str] = set()
    for event in events:
        description = describe(event)
        if description and description not in seen:
            seen.add(description)
            items.append(f"{len(items) + 1}. {description}")
        if len(items) == limit:
            break
    return "\n".join(items) if items else "_No recent public activity found._"


def fetch_events(owner: str, token: str | None) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        f"https://api.github.com/users/{owner}/events/public?per_page=30",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-readme-activity-updater",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def update_readme(path: Path, activity: str) -> bool:
    original = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    replacement = f"{START}\n{activity}\n{END}"
    updated, count = pattern.subn(replacement, original)
    if count != 1:
        raise ValueError(f"Expected exactly one activity section in {path}; found {count}.")
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default=os.getenv("GITHUB_REPOSITORY_OWNER", "shivam01112"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--events-file", type=Path)
    args = parser.parse_args()

    if args.events_file:
        events = json.loads(args.events_file.read_text(encoding="utf-8"))
    else:
        events = fetch_events(args.owner, os.getenv("GITHUB_TOKEN"))

    changed = update_readme(args.readme, render(events))
    print("Updated recent activity." if changed else "Recent activity is already current.")


if __name__ == "__main__":
    main()
