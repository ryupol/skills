#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 0 ]; then
  echo "Usage: bash scripts/setup.sh" >&2
  exit 2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$REPO/skills" "$REPO/agents"

sources=(
  "$REPO/skills"
  "$REPO/skills"
  "$REPO/skills"
  "$REPO/skills"
  "$REPO/agents"
  "$REPO/agents"
  "$REPO/agents"
  "$REPO/AGENTS.md"
  "$REPO/AGENTS.md"
  "$REPO/AGENTS.md"
  "$REPO/AGENTS.md"
  "$REPO/AGENTS.md"
  "$REPO/AGENTS.md"
)

targets=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.cursor/skills"
  "$HOME/.pi/skills"
  "$HOME/.agents/agents"
  "$HOME/.claude/agents"
  "$HOME/.cursor/agents"
  "$HOME/.agents/AGENTS.md"
  "$HOME/.codex/AGENTS.md"
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.pi/agent/AGENTS.md"
  "$HOME/.config/opencode/AGENTS.md"
  "$HOME/.cursor/rules/ryu-ai-skills.mdc"
)

conflicts=0
for target in "${targets[@]}"; do
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "Conflict: $target exists and is not a symlink" >&2
    conflicts=1
  fi
done

if [ "$conflicts" -ne 0 ]; then
  echo "Setup aborted. Move or back up conflicting paths, then rerun." >&2
  exit 1
fi

link_path() {
  local source="$1"
  local target="$2"

  mkdir -p "$(dirname "$target")"

  if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
    echo "ok  $target"
    return
  fi

  if [ -L "$target" ]; then
    rm "$target"
  fi

  ln -s "$source" "$target"
  echo "link $target -> $source"
}

for index in "${!targets[@]}"; do
  link_path "${sources[$index]}" "${targets[$index]}"
done

for index in "${!targets[@]}"; do
  target="${targets[$index]}"
  expected="${sources[$index]}"
  if [ ! -L "$target" ] || [ "$(readlink "$target")" != "$expected" ]; then
    echo "Verification failed: $target" >&2
    exit 1
  fi
done

echo "Setup complete. Restart active harness sessions."
