#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]


def load_env():
    paths = [Path.cwd() / ".env", REPO_ROOT / ".env"]
    seen = set()
    for path in paths:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing {name}. Add it to {REPO_ROOT / '.env'}")
    return value


def host():
    raw = require_env("GITLAB_HOST").rstrip("/")
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return "https://" + raw


def project_id(value):
    if value.isdigit():
        return value
    return urllib.parse.quote(value, safe="")


def read_json_arg(value):
    if not value:
        return {}
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text())
    return json.loads(value)


def request(method, path, payload=None, query=None):
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith("/api/v4/"):
        path = "/api/v4" + path
    url = host() + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)

    data = None
    headers = {
        "Accept": "application/json",
        "PRIVATE-TOKEN": require_env("GITLAB_TOKEN"),
    }
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            if not body:
                return {"status": resp.status}
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"status": resp.status, "body": body}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        raise SystemExit(json.dumps({"status": exc.code, "reason": exc.reason, "body": parsed}, indent=2))


def cmd_whoami(_args):
    return request("GET", "/user")


def cmd_project_get(args):
    return request("GET", f"/projects/{project_id(args.project)}")


def cmd_project_search(args):
    return request("GET", "/projects", query={"search": args.query, "simple": str(args.simple).lower(), "per_page": args.per_page})


def cmd_branch_create(args):
    payload = {"branch": args.branch, "ref": args.ref}
    return request("POST", f"/projects/{project_id(args.project)}/repository/branches", payload)


def cmd_mr_create(args):
    payload = read_json_arg(args.json)
    payload.update({
        "source_branch": args.source_branch,
        "target_branch": args.target_branch,
        "title": args.title,
    })
    if args.description is not None:
        payload["description"] = args.description
    if args.remove_source_branch:
        payload["remove_source_branch"] = True
    if args.squash:
        payload["squash"] = True
    if args.assignee_id:
        payload["assignee_id"] = args.assignee_id
    if args.reviewer_ids:
        payload["reviewer_ids"] = [int(value) for value in args.reviewer_ids.split(",") if value.strip()]
    return request("POST", f"/projects/{project_id(args.project)}/merge_requests", payload)


def cmd_mr_get(args):
    return request("GET", f"/projects/{project_id(args.project)}/merge_requests/{args.iid}")


def cmd_mr_list(args):
    query = {"state": args.state, "per_page": args.per_page}
    if args.source_branch:
        query["source_branch"] = args.source_branch
    if args.target_branch:
        query["target_branch"] = args.target_branch
    return request("GET", f"/projects/{project_id(args.project)}/merge_requests", query=query)


def cmd_mr_update(args):
    payload = read_json_arg(args.json)
    if args.title is not None:
        payload["title"] = args.title
    if args.description is not None:
        payload["description"] = args.description
    if args.state_event is not None:
        payload["state_event"] = args.state_event
    if not payload:
        raise SystemExit("Provide --title, --description, --state-event, or --json")
    return request("PUT", f"/projects/{project_id(args.project)}/merge_requests/{args.iid}", payload)


def cmd_mr_close(args):
    return request("PUT", f"/projects/{project_id(args.project)}/merge_requests/{args.iid}", {"state_event": "close"})


def cmd_mr_merge(args):
    payload = read_json_arg(args.json)
    if args.sha:
        payload["sha"] = args.sha
    if args.squash:
        payload["squash"] = True
    if args.should_remove_source_branch:
        payload["should_remove_source_branch"] = True
    if args.auto_merge:
        payload["auto_merge"] = True
    return request("PUT", f"/projects/{project_id(args.project)}/merge_requests/{args.iid}/merge", payload)


def cmd_mr_delete(args):
    return request("DELETE", f"/projects/{project_id(args.project)}/merge_requests/{args.iid}")


def cmd_raw_request(args):
    payload = read_json_arg(args.json) if args.json else None
    query = read_json_arg(args.query_json) if args.query_json else None
    return request(args.method, args.path, payload, query)


def build_parser():
    parser = argparse.ArgumentParser(description="GitLab REST helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami").set_defaults(func=cmd_whoami)

    p = sub.add_parser("project-get")
    p.add_argument("project")
    p.set_defaults(func=cmd_project_get)

    p = sub.add_parser("project-search")
    p.add_argument("query")
    p.add_argument("--per-page", type=int, default=20)
    p.add_argument("--simple", action="store_true")
    p.set_defaults(func=cmd_project_search)

    p = sub.add_parser("branch-create")
    p.add_argument("project")
    p.add_argument("branch")
    p.add_argument("ref")
    p.set_defaults(func=cmd_branch_create)

    p = sub.add_parser("mr-create")
    p.add_argument("project")
    p.add_argument("--source-branch", required=True)
    p.add_argument("--target-branch", default="main")
    p.add_argument("--title", required=True)
    p.add_argument("--description")
    p.add_argument("--remove-source-branch", action="store_true")
    p.add_argument("--squash", action="store_true")
    p.add_argument("--assignee-id", type=int)
    p.add_argument("--reviewer-ids")
    p.add_argument("--json")
    p.set_defaults(func=cmd_mr_create)

    p = sub.add_parser("mr-get")
    p.add_argument("project")
    p.add_argument("iid", type=int)
    p.set_defaults(func=cmd_mr_get)

    p = sub.add_parser("mr-list")
    p.add_argument("project")
    p.add_argument("--state", default="opened")
    p.add_argument("--source-branch")
    p.add_argument("--target-branch")
    p.add_argument("--per-page", type=int, default=20)
    p.set_defaults(func=cmd_mr_list)

    p = sub.add_parser("mr-update")
    p.add_argument("project")
    p.add_argument("iid", type=int)
    p.add_argument("--title")
    p.add_argument("--description")
    p.add_argument("--state-event", choices=["close", "reopen"])
    p.add_argument("--json")
    p.set_defaults(func=cmd_mr_update)

    p = sub.add_parser("mr-close")
    p.add_argument("project")
    p.add_argument("iid", type=int)
    p.set_defaults(func=cmd_mr_close)

    p = sub.add_parser("mr-merge")
    p.add_argument("project")
    p.add_argument("iid", type=int)
    p.add_argument("--sha")
    p.add_argument("--squash", action="store_true")
    p.add_argument("--should-remove-source-branch", action="store_true")
    p.add_argument("--auto-merge", action="store_true")
    p.add_argument("--json")
    p.set_defaults(func=cmd_mr_merge)

    p = sub.add_parser("mr-delete")
    p.add_argument("project")
    p.add_argument("iid", type=int)
    p.set_defaults(func=cmd_mr_delete)

    p = sub.add_parser("request")
    p.add_argument("--method", default="GET")
    p.add_argument("--path", required=True)
    p.add_argument("--json")
    p.add_argument("--query-json")
    p.set_defaults(func=cmd_raw_request)
    return parser


def main():
    load_env()
    args = build_parser().parse_args()
    result = args.func(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
