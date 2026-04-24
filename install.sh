#!/usr/bin/env bash
# install pin-llm-wiki skill
# usage:
#   ./install.sh              — user-global (~/.claude/skills/)
#   ./install.sh project      — project-local (.claude/skills/ in cwd)
#   ./install.sh /some/path   — explicit target directory

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/skill" && pwd)"
SKILL_NAME="pin-llm-wiki"

case "${1:-}" in
  project)
    TARGET=".claude/skills/$SKILL_NAME"
    ;;
  "")
    TARGET="$HOME/.claude/skills/$SKILL_NAME"
    ;;
  *)
    TARGET="$1/$SKILL_NAME"
    ;;
esac

echo "Installing $SKILL_NAME → $TARGET"

mkdir -p "$(dirname "$TARGET")"
rm -rf "$TARGET"
cp -r "$SKILL_DIR" "$TARGET"

echo "Done."
