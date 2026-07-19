---
name: gitlab-api
description: Use GitLab REST APIs for projects, branches, and MRs.
---

# GitLab API

Use this skill for GitLab REST API work through the repo-local `.env`.

## Credentials

Read credentials from repo root `.env`:

- `GITLAB_HOST`: GitLab host, for example `https://gitlab.example.com`
- `GITLAB_TOKEN`: personal, project, or group access token

Never print token values. If authentication fails, report status and endpoint only.

## Helper

Use the bundled helper when possible:

```bash
skills/gitlab-api/scripts/gitlab_api.py whoami
skills/gitlab-api/scripts/gitlab_api.py project-get group/project
skills/gitlab-api/scripts/gitlab_api.py project-search "project name"
skills/gitlab-api/scripts/gitlab_api.py branch-create group/project feature/x main
skills/gitlab-api/scripts/gitlab_api.py mr-create group/project --source-branch feature/x --target-branch main --title "MR title" --description "MR details"
skills/gitlab-api/scripts/gitlab_api.py mr-list group/project --state opened
skills/gitlab-api/scripts/gitlab_api.py mr-get group/project 42
skills/gitlab-api/scripts/gitlab_api.py mr-update group/project 42 --title "New title" --description "New details"
```

For unsupported endpoints, use raw request:

```bash
skills/gitlab-api/scripts/gitlab_api.py request --method GET --path /projects
skills/gitlab-api/scripts/gitlab_api.py request --method POST --path /projects/group%2Fproject/merge_requests --json '{"source_branch":"feature/x","target_branch":"main","title":"MR title"}'
```

## GitLab Notes

- Use GitLab REST API v4 under `/api/v4`.
- Project path ids must be URL-encoded (`group/project` becomes `group%2Fproject`); helper encodes project arguments.
- Merge request detail endpoints use project-scoped IID, not global MR id.
- Creating MR requires source branch to exist. Use `branch-create` first when needed.
- `mr-merge` can pass `--sha` to prevent merging a changed HEAD.
- Use `--json` for extra fields the helper does not expose.

## Safety

For destructive or irreversible calls (`mr-delete`, `mr-merge`, raw `DELETE`), confirm user intent unless user already asked explicitly in same turn.
