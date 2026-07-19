#!/usr/bin/env python3
import argparse
import base64
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
    raw = require_env("ATLASSIAN_HOST").rstrip("/")
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return "https://" + raw


def auth_header():
    email = require_env("ATLASSIAN_EMAIL")
    token = require_env("ATLASSIAN_API_TOKEN")
    basic = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {basic}"


def read_json_arg(value):
    if not value:
        return {}
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text())
    return json.loads(value)


def read_body(args):
    if getattr(args, "body_file", None):
        return Path(args.body_file).read_text()
    return getattr(args, "body", None) or ""


def request(method, path, payload=None, query=None):
    if not path.startswith("/"):
        path = "/" + path
    url = host() + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)

    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": auth_header(),
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


def adf_doc(text):
    blocks = []
    for paragraph in (text or "").split("\n\n"):
        content = []
        lines = paragraph.splitlines() or [""]
        for index, line in enumerate(lines):
            if line:
                content.append({"type": "text", "text": line})
            if index != len(lines) - 1:
                content.append({"type": "hardBreak"})
        blocks.append({"type": "paragraph", "content": content})
    return {"type": "doc", "version": 1, "content": blocks}


def issue_url(key):
    return f"{host()}/browse/{key}"


def cmd_whoami(_args):
    return request("GET", "/rest/api/3/myself")


def cmd_jira_create(args):
    fields = read_json_arg(args.fields_json)
    fields.setdefault("project", {"key": args.project_key})
    fields.setdefault("issuetype", {"name": args.issue_type})
    fields["summary"] = args.summary
    if args.description_text is not None:
        fields["description"] = adf_doc(args.description_text)
    result = request("POST", "/rest/api/3/issue", {"fields": fields})
    if "key" in result:
        result["browseUrl"] = issue_url(result["key"])
    return result


def cmd_jira_get(args):
    query = {}
    if args.fields:
        query["fields"] = args.fields
    return request("GET", f"/rest/api/3/issue/{urllib.parse.quote(args.issue, safe='')}", query=query)


def cmd_jira_edit(args):
    fields = read_json_arg(args.fields_json)
    if args.summary is not None:
        fields["summary"] = args.summary
    if args.description_text is not None:
        fields["description"] = adf_doc(args.description_text)
    payload = {"fields": fields} if fields else read_json_arg(args.json)
    if not payload:
        raise SystemExit("Provide --summary, --description-text, --fields-json, or --json")
    return request("PUT", f"/rest/api/3/issue/{urllib.parse.quote(args.issue, safe='')}", payload)


def cmd_jira_delete(args):
    query = {"deleteSubtasks": str(args.delete_subtasks).lower()}
    return request("DELETE", f"/rest/api/3/issue/{urllib.parse.quote(args.issue, safe='')}", query=query)


def cmd_jira_search(args):
    payload = {
        "jql": args.jql,
        "maxResults": args.max_results,
    }
    if args.fields:
        payload["fields"] = [field.strip() for field in args.fields.split(",") if field.strip()]
    if args.next_page_token:
        payload["nextPageToken"] = args.next_page_token
    return request("POST", "/rest/api/3/search/jql", payload)


def resolve_space_id(space_id=None, space_key=None):
    if space_id:
        return space_id
    if not space_key:
        raise SystemExit("Provide --space-id or --space-key")
    result = request("GET", "/wiki/api/v2/spaces", query={"keys": space_key})
    results = result.get("results", [])
    if not results:
        raise SystemExit(f"Space not found for key {space_key}")
    return results[0]["id"]


def cmd_confluence_space_id(args):
    return request("GET", "/wiki/api/v2/spaces", query={"keys": args.space_key})


def page_body(value, representation):
    return {"representation": representation, "value": value}


def cmd_confluence_create_page(args):
    payload = {
        "spaceId": resolve_space_id(args.space_id, args.space_key),
        "status": args.status,
        "title": args.title,
        "body": page_body(read_body(args), args.body_format),
    }
    if args.parent_id:
        payload["parentId"] = args.parent_id
    return request("POST", "/wiki/api/v2/pages", payload)


def cmd_confluence_get_page(args):
    query = {}
    if args.body_format:
        query["body-format"] = args.body_format
    return request("GET", f"/wiki/api/v2/pages/{urllib.parse.quote(args.page_id, safe='')}", query=query)


def cmd_confluence_update_page(args):
    current = cmd_confluence_get_page(argparse.Namespace(page_id=args.page_id, body_format=args.body_format))
    version_number = args.version_number or int(current["version"]["number"]) + 1
    title = args.title or current["title"]
    body_value = read_body(args)
    if not body_value:
        body_value = current.get("body", {}).get(args.body_format, {}).get("value", "")
    if not body_value:
        raise SystemExit("Provide --body or --body-file; current page body was not returned")
    payload = {
        "id": args.page_id,
        "status": args.status,
        "title": title,
        "body": page_body(body_value, args.body_format),
        "version": {"number": version_number, "message": args.version_message},
    }
    return request("PUT", f"/wiki/api/v2/pages/{urllib.parse.quote(args.page_id, safe='')}", payload)


def cmd_confluence_delete_page(args):
    return request("DELETE", f"/wiki/api/v2/pages/{urllib.parse.quote(args.page_id, safe='')}")


def cmd_raw_request(args):
    path = args.path
    if args.product == "jira" and not path.startswith("/rest/"):
        path = "/rest/api/3/" + path.lstrip("/")
    if args.product == "confluence" and not path.startswith("/wiki/"):
        path = "/wiki/api/v2/" + path.lstrip("/")
    payload = read_json_arg(args.json) if args.json else None
    query = read_json_arg(args.query_json) if args.query_json else None
    return request(args.method, path, payload, query)


def build_parser():
    parser = argparse.ArgumentParser(description="Atlassian Cloud REST helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami").set_defaults(func=cmd_whoami)

    p = sub.add_parser("jira-create")
    p.add_argument("--project-key", required=True)
    p.add_argument("--issue-type", default="Story")
    p.add_argument("--summary", required=True)
    p.add_argument("--description-text")
    p.add_argument("--fields-json")
    p.set_defaults(func=cmd_jira_create)

    p = sub.add_parser("jira-get")
    p.add_argument("issue")
    p.add_argument("--fields")
    p.set_defaults(func=cmd_jira_get)

    p = sub.add_parser("jira-edit")
    p.add_argument("issue")
    p.add_argument("--summary")
    p.add_argument("--description-text")
    p.add_argument("--fields-json")
    p.add_argument("--json")
    p.set_defaults(func=cmd_jira_edit)

    p = sub.add_parser("jira-delete")
    p.add_argument("issue")
    p.add_argument("--delete-subtasks", action="store_true")
    p.set_defaults(func=cmd_jira_delete)

    p = sub.add_parser("jira-search")
    p.add_argument("--jql", required=True)
    p.add_argument("--fields")
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--next-page-token")
    p.set_defaults(func=cmd_jira_search)

    p = sub.add_parser("confluence-space-id")
    p.add_argument("--space-key", required=True)
    p.set_defaults(func=cmd_confluence_space_id)

    p = sub.add_parser("confluence-create-page")
    p.add_argument("--space-id")
    p.add_argument("--space-key")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.add_argument("--body-format", default="storage")
    p.add_argument("--parent-id")
    p.add_argument("--status", default="current")
    p.set_defaults(func=cmd_confluence_create_page)

    p = sub.add_parser("confluence-get-page")
    p.add_argument("--page-id", required=True)
    p.add_argument("--body-format", default="storage")
    p.set_defaults(func=cmd_confluence_get_page)

    p = sub.add_parser("confluence-update-page")
    p.add_argument("--page-id", required=True)
    p.add_argument("--title")
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.add_argument("--body-format", default="storage")
    p.add_argument("--status", default="current")
    p.add_argument("--version-number", type=int)
    p.add_argument("--version-message", default="")
    p.set_defaults(func=cmd_confluence_update_page)

    p = sub.add_parser("confluence-delete-page")
    p.add_argument("--page-id", required=True)
    p.set_defaults(func=cmd_confluence_delete_page)

    p = sub.add_parser("request")
    p.add_argument("--product", choices=["jira", "confluence"], required=True)
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
