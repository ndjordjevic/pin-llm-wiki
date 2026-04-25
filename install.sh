#!/usr/bin/env bash
# install pin-llm-wiki skill
# usage:
#   ./install.sh              — user-global (Claude Code, GitHub Copilot, Cursor)
#   ./install.sh project      — project-local (.claude, .copilot, .cursor skills in cwd)
#   ./install.sh /some/path   — explicit target directory (append /pin-llm-wiki)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/skill" && pwd)"
SKILL_NAME="pin-llm-wiki"

install_symlink() {
  local target="$1"
  echo "Installing $SKILL_NAME → $target (symlink)"
  mkdir -p "$(dirname "$target")"
  rm -rf "$target"
  ln -sf "$SKILL_DIR" "$target"
}

case "${1:-}" in
  project)
    install_symlink ".claude/skills/$SKILL_NAME"
    install_symlink ".copilot/skills/$SKILL_NAME"
    install_symlink ".cursor/skills/$SKILL_NAME"
    ;;
  "")
    install_symlink "$HOME/.claude/skills/$SKILL_NAME"
    install_symlink "$HOME/.copilot/skills/$SKILL_NAME"
    install_symlink "$HOME/.cursor/skills/$SKILL_NAME"
    ;;
  *)
    install_symlink "$1/$SKILL_NAME"
    ;;
esac

echo "Done."
