# ryu-ai-skills

Public, user-level instructions and skills shared across Claude Code, Codex, Pi,
OpenCode, Cursor, and harnesses using `~/.agents/skills`.

## Structure

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

Harnesses expect a flat `<skill-name>/SKILL.md` view; `skills/` is that view
directly — no separate source directory, no symlink indirection per skill.
`agents/` is the equivalent flat view for subagents reused across skills.

No top-level `commands/` directory anywhere in repo — commands become
skills. See [Commands and subagents](#commands-and-subagents) below.

## Install

Use the skills.sh installer for normal install. It shows a TUI for selecting
skills, target agents, and copy vs symlink:

```bash
npx skills@latest add <github-owner>/ryu-skills
```

Replace `<github-owner>` with the real GitHub owner after publishing this repo.

Useful non-interactive forms:

```bash
npx skills@latest add <github-owner>/ryu-skills --list
npx skills@latest add <github-owner>/ryu-skills -g --agent codex claude-code
npx skills@latest add <github-owner>/ryu-skills -g --skill gitlab-api atlassian-api
npx skills@latest add <github-owner>/ryu-skills -g --copy
npx skills@latest add <github-owner>/ryu-skills -g --all
```

## Local Dev Setup

```bash
bash scripts/setup.sh
```

Script accepts no arguments. Use this for personal local development when you
want whole-directory symlinks into every local harness. For general install,
prefer `npx skills@latest add`.

Local setup links:

```text
~/.agents/skills                     -> repo/skills
~/.claude/skills                    -> repo/skills
~/.cursor/skills                    -> repo/skills
~/.pi/skills                        -> repo/skills
~/.agents/agents                    -> repo/agents
~/.claude/agents                    -> repo/agents
~/.cursor/agents                    -> repo/agents
~/.agents/AGENTS.md                 -> repo/AGENTS.md
~/.codex/AGENTS.md                  -> repo/AGENTS.md
~/.claude/CLAUDE.md                 -> repo/AGENTS.md
~/.pi/agent/AGENTS.md               -> repo/AGENTS.md
~/.config/opencode/AGENTS.md        -> repo/AGENTS.md
~/.cursor/rules/ryu-ai-skills.mdc   -> repo/AGENTS.md
~/.local/bin/cy                     -> repo/scripts/cy
```

Codex and OpenCode read `~/.agents/skills`; Claude Code, Cursor, and Pi use
their native skill paths. Setup never replaces harness root directories,
settings, authentication, sessions, plugins, or caches.

If real file or directory already occupies managed target, setup aborts before
changing links. Move or back up reported path manually, then rerun.

## List Skills

```bash
bash scripts/list-skills.sh
```

## Add Skill

```bash
mkdir -p skills/example-skill
# Create skills/example-skill/SKILL.md
```

Commit directory directly. Skill name must match `name` in `SKILL.md`
frontmatter. All skill names must be unique in `skills/`.

## Add Agent

```bash
mkdir -p agents
# Create agents/example-subagent.md
```

Commit file (or directory, if subagent needs support files) directly under
`agents/`. Use top-level `agents/` when subagent is reusable across more than
one skill. If subagent is specific to a single skill, nest it instead under
`skills/<skill-name>/agents/<subagent>.md`.

## Commands and subagents

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

## Verify

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

Start fresh harness session after initial setup. Ask it to list available skills
and summarize active personal instructions.

`cy` starts a new Codex session with approval prompts and sandboxing disabled.
Use only where unrestricted local execution is intended:

```bash
cy
cy -C /path/to/project
```
