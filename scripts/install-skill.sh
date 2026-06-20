#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$ROOT/skills/repo-first-base-selection/SKILL.md"

install_one() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  cp "$SKILL_SRC" "$target_dir/SKILL.md"
  printf 'Installed repo-first-base-selection skill to %s\n' "$target_dir"
}

if [[ ! -f "$SKILL_SRC" ]]; then
  echo "Missing $SKILL_SRC" >&2
  exit 1
fi

INSTALL_HERMES=1
INSTALL_OPENCLAW=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hermes-only) INSTALL_OPENCLAW=0 ;;
    --openclaw-only) INSTALL_HERMES=0 ;;
    --help|-h)
      cat <<'HELP'
Usage: scripts/install-skill.sh [--hermes-only|--openclaw-only]

Installs the repo-first-base-selection SKILL.md into common local skill folders:
  Hermes:   ${HERMES_HOME:-$HOME/.hermes}/skills/software-development/repo-first-base-selection
  OpenClaw: ${OPENCLAW_HOME:-$HOME/.openclaw}/skills/repo-first-base-selection
HELP
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

if [[ "$INSTALL_HERMES" == "1" ]]; then
  HERMES_BASE="${HERMES_HOME:-$HOME/.hermes}"
  install_one "$HERMES_BASE/skills/software-development/repo-first-base-selection"
fi

if [[ "$INSTALL_OPENCLAW" == "1" ]]; then
  OPENCLAW_BASE="${OPENCLAW_HOME:-$HOME/.openclaw}"
  install_one "$OPENCLAW_BASE/skills/repo-first-base-selection"
fi
