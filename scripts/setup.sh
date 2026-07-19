#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$REPO/skills" "$REPO/agents"

all_agents=(codex claude-code cursor pi opencode)
selected_agents=()
sources=()
targets=()

usage() {
  cat >&2 <<'EOF'
Usage:
  bash scripts/setup.sh
  bash scripts/setup.sh --interactive
  bash scripts/setup.sh --all
  bash scripts/setup.sh --target codex claude-code
  bash scripts/setup.sh --list-targets
EOF
}

list_targets() {
  printf '%s\n' "${all_agents[@]}"
}

select_all_agents() {
  selected_agents=("${all_agents[@]}")
}

append_agent() {
  local agent="$1"
  local selected

  case "$agent" in
    claude)
      agent="claude-code"
      ;;
  esac

  case "$agent" in
    codex|claude-code|cursor|pi|opencode)
      if [ "${#selected_agents[@]}" -gt 0 ]; then
        for selected in "${selected_agents[@]}"; do
          if [ "$selected" = "$agent" ]; then
            return
          fi
        done
      fi
      selected_agents+=("$agent")
      ;;
    *)
      echo "Unknown target: $agent" >&2
      echo "Run 'bash scripts/setup.sh --list-targets' to see supported targets." >&2
      exit 2
      ;;
  esac
}

choose_agents() {
  local answer item

  echo "Available targets:"
  echo "  1) codex"
  echo "  2) claude-code"
  echo "  3) cursor"
  echo "  4) pi"
  echo "  5) opencode"
  printf "Select targets (names or numbers, space-separated; empty=all): "
  IFS= read -r answer

  if [ -z "$answer" ] || [ "$answer" = "all" ]; then
    select_all_agents
    return
  fi

  selected_agents=()
  for item in $answer; do
    case "$item" in
      1) append_agent codex ;;
      2) append_agent claude-code ;;
      3) append_agent cursor ;;
      4) append_agent pi ;;
      5) append_agent opencode ;;
      *) append_agent "$item" ;;
    esac
  done
}

add_target() {
  local source="$1"
  local target="$2"
  local index

  if [ "${#targets[@]}" -gt 0 ]; then
    for index in "${!targets[@]}"; do
      if [ "${targets[$index]}" = "$target" ]; then
        if [ "${sources[$index]}" = "$source" ]; then
          return
        fi

        echo "Internal target conflict: $target" >&2
        exit 1
      fi
    done
  fi

  sources+=("$source")
  targets+=("$target")
}

add_agent_targets() {
  local agent="$1"

  case "$agent" in
    codex)
      add_target "$REPO/skills" "$HOME/.agents/skills"
      add_target "$REPO/agents" "$HOME/.agents/agents"
      add_target "$REPO/AGENTS.md" "$HOME/.agents/AGENTS.md"
      add_target "$REPO/AGENTS.md" "$HOME/.codex/AGENTS.md"
      ;;
    claude-code)
      add_target "$REPO/skills" "$HOME/.claude/skills"
      add_target "$REPO/agents" "$HOME/.claude/agents"
      add_target "$REPO/AGENTS.md" "$HOME/.claude/CLAUDE.md"
      ;;
    cursor)
      add_target "$REPO/skills" "$HOME/.cursor/skills"
      add_target "$REPO/agents" "$HOME/.cursor/agents"
      add_target "$REPO/AGENTS.md" "$HOME/.cursor/rules/agent-instructions.mdc"
      ;;
    pi)
      add_target "$REPO/skills" "$HOME/.pi/skills"
      add_target "$REPO/AGENTS.md" "$HOME/.pi/agent/AGENTS.md"
      ;;
    opencode)
      add_target "$REPO/skills" "$HOME/.agents/skills"
      add_target "$REPO/AGENTS.md" "$HOME/.config/opencode/AGENTS.md"
      ;;
    *)
      echo "Unknown target: $agent" >&2
      exit 2
      ;;
  esac
}

if [ "$#" -eq 0 ]; then
  select_all_agents
else
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --all)
        select_all_agents
        shift
        ;;
      --target)
        shift
        if [ "$#" -eq 0 ] || [[ "$1" == --* ]]; then
          echo "--target requires at least one target name." >&2
          usage
          exit 2
        fi
        while [ "$#" -gt 0 ] && [[ "$1" != --* ]]; do
          append_agent "$1"
          shift
        done
        ;;
      --agent)
        echo "Warning: --agent is deprecated for local setup. Use --target." >&2
        shift
        if [ "$#" -eq 0 ] || [[ "$1" == --* ]]; then
          echo "--target requires at least one target name." >&2
          usage
          exit 2
        fi
        while [ "$#" -gt 0 ] && [[ "$1" != --* ]]; do
          append_agent "$1"
          shift
        done
        ;;
      --interactive|-i)
        choose_agents
        shift
        ;;
      --list-targets)
        list_targets
        exit 0
        ;;
      --list-agents)
        echo "Warning: --list-agents is deprecated for local setup. Use --list-targets." >&2
        list_targets
        exit 0
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 2
        ;;
    esac
  done
fi

if [ "${#selected_agents[@]}" -eq 0 ]; then
  echo "No agents selected." >&2
  usage
  exit 2
fi

for agent in "${selected_agents[@]}"; do
  add_agent_targets "$agent"
done

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

echo "Setup complete for: ${selected_agents[*]}"
echo "Restart active harness sessions."
