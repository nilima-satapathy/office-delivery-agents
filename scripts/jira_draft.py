"""Create a JIRA draft issue. Never transitions status.

Reads JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT from the
environment. When any are missing, prints the payload and exits 2.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ALLOWED_TYPES = ("Epic", "Story", "Sub-task", "Bug")
ROLE_LABEL = {
    "Epic": "agent:requirements",
    "Story": "agent:requirements",
    "Sub-task": "agent:requirements",
    "Bug": "agent:qa",
}
ENV_KEYS = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT")


def missing_env(env: dict) -> list[str]:
    return [key for key in ENV_KEYS if not env.get(key)]


def issue_payload(
    project: str,
    issue_type: str,
    summary: str,
    description: str,
    external_id: str,
    parent_key: str | None = None,
    epic_name_field: str | None = None,
) -> dict:
    if issue_type not in ALLOWED_TYPES:
        allowed = ", ".join(ALLOWED_TYPES)
        raise ValueError(f"issue type must be one of: {allowed}")
    if issue_type == "Sub-task" and not parent_key:
        raise ValueError("Sub-task requires parent_key")
    if not external_id.strip():
        raise ValueError("external_id is required")

    fields: dict = {
        "project": {"key": project},
        "summary": summary,
        "description": description,
        "issuetype": {"name": issue_type},
        "labels": [ROLE_LABEL[issue_type], f"agent-ext-{external_id}"],
    }
    if parent_key:
        fields["parent"] = {"key": parent_key}
    if issue_type == "Epic" and epic_name_field:
        fields[epic_name_field] = summary

    payload = {"fields": fields}
    if "transition" in payload or "transition" in fields:
        raise ValueError("draft payload must not transition status")
    return payload


def create_issue(payload: dict, env: dict, opener=None) -> dict:
    missing = missing_env(env)
    if missing:
        return {"created": False, "reason": "JIRA not connected", "missing": missing, "payload": payload}

    base = env["JIRA_BASE_URL"].rstrip("/")
    url = f"{base}/rest/api/2/issue"
    token = base64.b64encode(f"{env['JIRA_EMAIL']}:{env['JIRA_API_TOKEN']}".encode()).decode()
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        open_fn = opener or urllib.request.urlopen
        with open_fn(request, timeout=30) as response:
            body = json.loads(response.read().decode())
            return {"created": True, "key": body.get("key"), "id": body.get("id")}
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        return {"created": False, "reason": f"JIRA HTTP {error.code}", "detail": detail}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a JIRA draft issue")
    parser.add_argument("--type", required=True, choices=ALLOWED_TYPES)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--external-id", required=True)
    parser.add_argument("--parent-key", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    payload = issue_payload(
        project=env.get("JIRA_PROJECT", "UNSET"),
        issue_type=args.type,
        summary=args.summary,
        description=args.description,
        external_id=args.external_id,
        parent_key=args.parent_key or None,
        epic_name_field=env.get("JIRA_EPIC_NAME_FIELD") or None,
    )
    if args.dry_run or missing_env(env):
        result = {
            "created": False,
            "reason": "dry-run" if args.dry_run else "JIRA not connected",
            "payload": payload,
        }
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2

    result = create_issue(payload, env)
    json.dump({k: v for k, v in result.items() if k != "payload"}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("created") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
