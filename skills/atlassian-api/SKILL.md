---
name: atlassian-api
description: Use Jira and Confluence Cloud REST APIs.
---

# Atlassian API

Use this skill for Atlassian Cloud CRUD through the repo-local `.env`.

## Credentials

Read credentials from repo root `.env`:

- `ATLASSIAN_HOST`: Atlassian site host, for example `https://example.atlassian.net`
- `ATLASSIAN_EMAIL`: Atlassian account email
- `ATLASSIAN_API_TOKEN`: API token

Never print token values. If authentication fails, report status and endpoint only.

## Helper

Use the bundled helper when possible:

```bash
skills/atlassian-api/scripts/atlassian_api.py whoami
skills/atlassian-api/scripts/atlassian_api.py jira-create --project-key EX --issue-type Story --summary "Story title" --description-text "Story details"
skills/atlassian-api/scripts/atlassian_api.py jira-edit EX-123 --summary "New title" --description-text "New details"
skills/atlassian-api/scripts/atlassian_api.py jira-search --jql 'project = EX ORDER BY updated DESC' --fields summary,status,assignee --max-results 10
skills/atlassian-api/scripts/atlassian_api.py confluence-space-id --space-key ENG
skills/atlassian-api/scripts/atlassian_api.py confluence-create-page --space-key ENG --title "Runbook" --body-file runbook.html
skills/atlassian-api/scripts/atlassian_api.py confluence-update-page --page-id 123456 --title "Runbook" --body-file runbook.html
```

For unsupported endpoints, use raw request:

```bash
skills/atlassian-api/scripts/atlassian_api.py request --product jira --method GET --path /rest/api/3/project
skills/atlassian-api/scripts/atlassian_api.py request --product confluence --method GET --path /wiki/api/v2/pages
```

## Jira Notes

- Use Jira Cloud REST API v3.
- `description`, comments, environment, and multi-line text fields use Atlassian Document Format. Prefer `--description-text`; helper converts plain text to minimal ADF.
- Use `--fields-json` for custom fields, labels, components, sprint fields, parent, priority, or advanced update payloads.
- JQL search uses `/rest/api/3/search/jql` and `nextPageToken`, not deprecated `/rest/api/3/search`.
- Create issue returns `key`, `id`, and `self`; report key and browser URL.

## Confluence Notes

- Use Confluence Cloud REST API v2 under `/wiki/api/v2`.
- Page creation needs `spaceId`; helper accepts `--space-key` and resolves it.
- Page updates need incremented version numbers; helper fetches current version when `--version-number` omitted.
- Body format defaults to `storage` HTML. Use well-formed storage-compatible XHTML.

## Safety

For destructive calls (`jira-delete`, `confluence-delete-page`, raw `DELETE`), confirm user intent unless user already asked explicitly in same turn.
