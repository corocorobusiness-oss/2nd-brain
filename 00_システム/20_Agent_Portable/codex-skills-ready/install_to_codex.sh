#!/bin/zsh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST_DIR="$HOME/.codex/skills"

mkdir -p "$DEST_DIR"

for skill_dir in "$SRC_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue
  skill_name="$(basename "$skill_dir")"
  [[ "$skill_name" == "." || "$skill_name" == ".." ]] && continue
  rsync -a --delete "$skill_dir/" "$DEST_DIR/$skill_name/"
  echo "installed: $skill_name"
done

echo
echo "Done. Restart Codex or open a new thread so the skills are reloaded."

