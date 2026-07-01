#!/usr/bin/env bash
set -euo pipefail

AGENT_SKILLS="${AGENT_SKILLS:-/Users/kojinn/agent-skills}"
CODEX_SKILLS="${CODEX_SKILLS:-/Users/kojinn/.codex/skills}"
BACKUP_ROOT="${BACKUP_ROOT:-$CODEX_SKILLS/.backup-agent-skills-symlink}"

ACTION="link"
APPLY=0
ROLLBACK_DIR=""

usage() {
  cat <<'USAGE'
Usage:
  codex_skills_use_agent_skills.sh [--dry-run]
  codex_skills_use_agent_skills.sh --apply
  codex_skills_use_agent_skills.sh --verify
  codex_skills_use_agent_skills.sh --rollback <backup_dir> --apply

Purpose:
  Make /Users/kojinn/agent-skills the single source of truth for custom Codex skills.
  .system is preserved. Existing copied custom skill directories are moved to a backup
  directory before symlinks are created.

Environment overrides:
  AGENT_SKILLS=/path/to/agent-skills
  CODEX_SKILLS=/path/to/.codex/skills
  BACKUP_ROOT=/path/to/backups
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      APPLY=0
      shift
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    --verify)
      ACTION="verify"
      shift
      ;;
    --rollback)
      ROLLBACK_DIR="${2:-}"
      if [[ -z "$ROLLBACK_DIR" ]]; then
        echo "ERROR: --rollback requires a backup directory" >&2
        exit 2
      fi
      ACTION="rollback"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

timestamp() {
  date '+%Y%m%d-%H%M%S'
}

say() {
  printf '%s\n' "$*"
}

require_dir() {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "ERROR: directory not found: $path" >&2
    exit 1
  fi
}

skill_names() {
  find "$AGENT_SKILLS" -mindepth 1 -maxdepth 1 -type d -name '*' -print |
    while IFS= read -r skill_dir; do
      local name
      name="$(basename "$skill_dir")"
      [[ "$name" == ".git" ]] && continue
      [[ "$name" == ".system" ]] && continue
      [[ -f "$skill_dir/SKILL.md" ]] || continue
      printf '%s\n' "$name"
    done |
    sort
}

ensure_safe_layout() {
  require_dir "$AGENT_SKILLS"
  require_dir "$CODEX_SKILLS"

  if [[ ! -d "$CODEX_SKILLS/.system" ]]; then
    echo "ERROR: Codex .system skill directory missing: $CODEX_SKILLS/.system" >&2
    exit 1
  fi
}

verify_links() {
  ensure_safe_layout

  local failures=0
  local total=0
  while IFS= read -r name; do
    total=$((total + 1))
    local expected="$AGENT_SKILLS/$name"
    local target="$CODEX_SKILLS/$name"

    if [[ ! -L "$target" ]]; then
      say "FAIL not_symlink $target"
      failures=$((failures + 1))
      continue
    fi

    local actual
    actual="$(readlink "$target")"
    if [[ "$actual" != "$expected" ]]; then
      say "FAIL wrong_target $target -> $actual expected $expected"
      failures=$((failures + 1))
      continue
    fi

    if [[ ! -f "$target/SKILL.md" ]]; then
      say "FAIL missing_skill_md $target/SKILL.md"
      failures=$((failures + 1))
      continue
    fi

    say "PASS $name -> $expected"
  done < <(skill_names)

  say "SUMMARY total=$total failures=$failures"
  [[ "$failures" -eq 0 ]]
}

apply_links() {
  ensure_safe_layout

  local backup_dir="$BACKUP_ROOT/$(timestamp)"
  say "BACKUP_DIR=$backup_dir"

  if [[ "$APPLY" -eq 1 ]]; then
    mkdir -p "$backup_dir"
  else
    say "DRY-RUN mkdir -p '$backup_dir'"
  fi

  while IFS= read -r name; do
    local source="$AGENT_SKILLS/$name"
    local target="$CODEX_SKILLS/$name"

    if [[ -L "$target" ]]; then
      local current
      current="$(readlink "$target")"
      if [[ "$current" == "$source" ]]; then
        say "SKIP already_linked $name"
        continue
      fi
    fi

    if [[ -e "$target" || -L "$target" ]]; then
      say "MOVE $target -> $backup_dir/$name"
      if [[ "$APPLY" -eq 1 ]]; then
        mv "$target" "$backup_dir/$name"
      fi
    fi

    say "LINK $target -> $source"
    if [[ "$APPLY" -eq 1 ]]; then
      ln -s "$source" "$target"
    fi
  done < <(skill_names)

  if [[ "$APPLY" -eq 1 ]]; then
    say "DONE action=link mode=apply"
    verify_links
  else
    say "DONE action=link mode=dry-run"
    say "DRY-RUN only. Re-run with --apply after human approval."
  fi
}

rollback_links() {
  ensure_safe_layout

  if [[ -z "$ROLLBACK_DIR" || ! -d "$ROLLBACK_DIR" ]]; then
    echo "ERROR: rollback backup directory not found: $ROLLBACK_DIR" >&2
    exit 1
  fi

  while IFS= read -r backup_item; do
    local name
    name="$(basename "$backup_item")"
    local target="$CODEX_SKILLS/$name"

    say "ROLLBACK $target <- $backup_item"
    if [[ "$APPLY" -eq 1 ]]; then
      if [[ -L "$target" ]]; then
        rm "$target"
      elif [[ -e "$target" ]]; then
        echo "ERROR: target exists and is not symlink: $target" >&2
        exit 1
      fi
      mv "$backup_item" "$target"
    fi
  done < <(find "$ROLLBACK_DIR" -mindepth 1 -maxdepth 1 -print | sort)

  if [[ "$APPLY" -eq 1 ]]; then
    say "ROLLBACK_DONE mode=apply backup=$ROLLBACK_DIR"
  else
    say "ROLLBACK_DONE mode=dry-run backup=$ROLLBACK_DIR"
    say "DRY-RUN only. Re-run with --rollback <backup_dir> --apply after human approval."
  fi
}

case "$ACTION" in
  link)
    apply_links
    ;;
  verify)
    verify_links
    ;;
  rollback)
    rollback_links
    ;;
  *)
    echo "ERROR: invalid action: $ACTION" >&2
    exit 2
    ;;
esac
