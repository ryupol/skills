# ryupol-skills

Personal agent skills I use across Codex, Claude Code, Cursor, Pi, and other
agent harnesses. Some skills are original; some are copied or adapted from
others for my own workflow.

## Quick Start

Use the interactive installer for normal setup:

```bash
npx skills@latest add ryupol/skills
```

Then choose:

- skills to install
- agent harnesses to install into
- copy or symlink mode

For a new project, install the skills your agent needs, then start a fresh
agent session in that project. To add more skills later, rerun the same command
and select only the extra skills.

## Install Choices

Same installer handles full setup and selected-skill installs. Only options
change.

| Goal | Recommended command | What it does |
| --- | --- | --- |
| Choose in prompts | `npx skills@latest add ryupol/skills` | Opens interactive selection. |
| Install everything | `npx skills@latest add ryupol/skills -g --all` | Installs all skills globally for supported agents. |
| Install specific skills only | `npx skills@latest add ryupol/skills -g --skill gitlab-api atlassian-api` | Installs only named skills. |
| Install for specific agents only | `npx skills@latest add ryupol/skills -g --agent codex claude-code` | Targets only selected agent harnesses. |
| Copy instead of symlink | `npx skills@latest add ryupol/skills -g --copy` | Copies files into target directories. |
| List available skills | `npx skills@latest add ryupol/skills --list` | Shows skills without installing. |

Use `npx skills@latest add` for normal install. Use local dev setup only when
working from this cloned repo.

Note: `npx skills@latest add` uses `--agent`; `scripts/setup.sh` uses
`--target` because it selects local symlink targets.

## Local Dev Setup

Local dev setup symlinks this repo into local harness directories. Changes in
this repo take effect without reinstalling.

Choose targets interactively:

```bash
bash scripts/setup.sh --interactive
```

Link every supported local target:

```bash
bash scripts/setup.sh --all
```

Link only selected local targets:

```bash
bash scripts/setup.sh --target codex claude-code
```

List supported local targets:

```bash
bash scripts/setup.sh --list-targets
```

`bash scripts/setup.sh` still defaults to `--all` for backward compatibility.
For general install outside local repo development, prefer
`npx skills@latest add ryupol/skills`.

Setup aborts if a real file or directory already exists at a managed target.
Move or back up the reported path, then rerun.

## Local Targets

`setup.sh` can link these targets:

| Target | Links |
| --- | --- |
| `codex` | `~/.agents/skills`, `~/.agents/agents`, `~/.agents/AGENTS.md`, `~/.codex/AGENTS.md` |
| `claude-code` | `~/.claude/skills`, `~/.claude/agents`, `~/.claude/CLAUDE.md` |
| `cursor` | `~/.cursor/skills`, `~/.cursor/agents`, `~/.cursor/rules/agent-instructions.mdc` |
| `pi` | `~/.pi/skills`, `~/.pi/agent/AGENTS.md` |
| `opencode` | `~/.agents/skills`, `~/.config/opencode/AGENTS.md` |

Codex and OpenCode share `~/.agents/skills`. Claude Code, Cursor, and Pi use
their native skill paths.

Setup never replaces harness root directories, settings, authentication,
sessions, plugins, or caches.

## Verify

Check only targets you selected:

```bash
readlink ~/.agents/skills
readlink ~/.claude/skills
readlink ~/.cursor/skills
readlink ~/.pi/skills
readlink ~/.agents/agents
readlink ~/.claude/agents
readlink ~/.cursor/agents
readlink ~/.codex/AGENTS.md
find skills -maxdepth 2 -name SKILL.md -print
```

Start fresh harness session after setup. Ask it to list available skills and
summarize active personal instructions.

## Repo Layout

```text
skills/
├── skills/                         # flat harness-facing skill index
│   └── <skill-name>/
│       ├── SKILL.md                # required
│       └── agents/                 # optional, skill-specific subagent only
│           └── <subagent>.md
├── agents/                         # flat harness-facing shared-agent index
│   └── <subagent-name>.md          # or <subagent-name>/ with support files
├── AGENTS.md                       # canonical user instructions
└── scripts/
    ├── list-skills.sh              # list repo skills
    └── setup.sh                    # local dev symlink wiring
```

Harnesses expect a flat `<skill-name>/SKILL.md` view. `skills/` is that view
directly: no separate source directory, no symlink indirection per skill.
`agents/` is the equivalent flat view for shared subagents.

## Commands And Subagents

No top-level `commands/` directory. Commands become skills; `agents/` stays
a real top-level directory since subagents are often shared across skills.

**Agents.** "Create an agent" → default to top-level `agents/<subagent>.md`.
Only nest under `skills/<skill-name>/agents/` when the agent is genuinely
specific to that one skill and unlikely to be reused. Define a same-context
fallback for harnesses without subagent support.

**Commands.** "Create a command" → build a skill, not a repo-root `commands/`
entry. Mark it explicit-trigger-only in `SKILL.md` frontmatter: state the
skill has no proactive/auto trigger and only fires when invoked by name
(`/skill-name`). That reproduces command behavior using the skill mechanism.
