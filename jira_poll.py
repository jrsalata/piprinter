#!/usr/bin/env python3
# Polls jira-cli (https://github.com/ankitpokhrel/jira-cli) for issues assigned
# to the current user and prints only the ones not printed by a previous run.
# Intended to be run periodically (e.g. via a systemd timer, see
# piprinter-jira-poll.timer).
import json
import os
import subprocess
import sys
from datetime import datetime

from printer import load_printer, print_blocks

JIRA_BIN = os.environ.get("JIRA_BIN", "jira")
PRINTER_CONFIG_PATH = os.environ.get("PIPRINTER_CONFIG_PATH", "config.example.yaml")
STATE_PATH = os.environ.get(
    "JIRA_POLL_STATE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "jira_poll_state.json"),
)
COLUMNS = ["key", "summary", "status", "priority"]


def get_current_user():
    result = subprocess.run(
        [JIRA_BIN, "me"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def fetch_assigned_issues(assignee):
    args = [
        JIRA_BIN, "issue", "list",
        f"-a{assignee}",
        "--plain",
        "--columns", ",".join(COLUMNS),
        "--no-headers",
    ]
    result = subprocess.run(args, capture_output=True, text=True, check=True)

    issues = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < len(COLUMNS):
            continue
        issues.append(dict(zip(COLUMNS, fields)))
    return issues


def load_seen_keys():
    if not os.path.exists(STATE_PATH):
        return set()
    with open(STATE_PATH) as f:
        return set(json.load(f))


def save_seen_keys(keys):
    with open(STATE_PATH, "w") as f:
        json.dump(sorted(keys), f)


def build_blocks(issues):
    blocks = [
        {"type": "title", "text": "New Jira Tickets"},
        {"type": "text", "text": datetime.now().strftime("%Y-%m-%d %H:%M")},
        {"type": "divider"},
    ]
    for issue in issues:
        blocks.append({
            "type": "text",
            "text": f"{issue['key']}: {issue['summary']}",
            "style": {"bold": True},
        })
        blocks.append({
            "type": "text",
            "text": f"Status: {issue['status']}  Priority: {issue['priority']}",
        })
        blocks.append({"type": "divider"})
    return blocks


def main():
    try:
        assignee = get_current_user()
        issues = fetch_assigned_issues(assignee)
    except FileNotFoundError:
        print(f"jira-cli binary '{JIRA_BIN}' not found on PATH", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"jira-cli command failed: {e.stderr.strip()}", file=sys.stderr)
        return 1

    seen = load_seen_keys()
    new_issues = [issue for issue in issues if issue["key"] not in seen]

    if not new_issues:
        print("No new tickets assigned.")
        return 0

    load_printer(PRINTER_CONFIG_PATH)
    ok, err = print_blocks(build_blocks(new_issues))
    if not ok:
        print(f"Failed to print tickets: {err}", file=sys.stderr)
        return 1

    seen.update(issue["key"] for issue in new_issues)
    save_seen_keys(seen)
    print(f"Printed {len(new_issues)} new ticket(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
