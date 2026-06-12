#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORTABLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST_ROOT="$PORTABLE_DIR/live-backups"
LOG_FILE="$DEST_ROOT/backup-log.md"
EXCLUDE_FILE="$SCRIPT_DIR/exclude_patterns.txt"
SECRET_PATTERNS_FILE="$SCRIPT_DIR/secret_scan_patterns.txt"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
stamp="$(date '+%Y%m%d_%H%M%S')"
STAGING="${TMPDIR:-/tmp}/agent-runtime-backup-$stamp"

mkdir -p "$DEST_ROOT"
mkdir -p "$STAGING"

log() {
  print -- "$1"
}

append_log() {
  {
    print ""
    print "## $timestamp"
    print ""
    print "$1"
  } >> "$LOG_FILE"
}

copy_if_exists() {
  local src="$1"
  local dest="$2"
  local label="$3"

  if [[ -d "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    rsync -a --delete --exclude-from="$EXCLUDE_FILE" "$src/" "$dest/"
    log "copied: $label"
  else
    log "skipped: $label (not found)"
  fi
}

scan_for_secrets() {
  local scan_dir="$1"
  local hits_file="$2"

  : > "$hits_file"
  while IFS= read -r pattern; do
    [[ -z "$pattern" ]] && continue
    rg -i --fixed-strings --glob '!*.md' --glob '!*.txt' --glob '!*.json' "$pattern" "$scan_dir" >> "$hits_file" 2>/dev/null || true
    rg -i --fixed-strings --glob '*.md' --glob '*.txt' "$pattern" "$scan_dir" >> "$hits_file" 2>/dev/null || true
  done < "$SECRET_PATTERNS_FILE"

  [[ -s "$hits_file" ]]
}

write_manifest() {
  local target_dir="$1"
  local name="$2"
  local manifest="$target_dir/manifest.md"
  local file_count
  file_count="$(find "$target_dir" -type f ! -name 'manifest.md' | wc -l | tr -d ' ')"

  {
    print "# $name Runtime Backup"
    print ""
    print "Last backup: $timestamp"
    print "File count: $file_count"
    print ""
    print "Excluded patterns: see \`backup_automation/exclude_patterns.txt\`"
    print "Secret scan patterns: see \`backup_automation/secret_scan_patterns.txt\`"
  } > "$manifest"
}

cleanup() {
  rm -rf "$STAGING"
}
trap cleanup EXIT

log "Agent runtime backup started: $timestamp"
log "mode: $([[ "$DRY_RUN" == "1" ]] && print dry-run || print write)"

copy_if_exists "$HOME/.codex/skills" "$STAGING/codex/skills" "codex skills"
copy_if_exists "$HOME/.codex/rules" "$STAGING/codex/rules" "codex rules"
copy_if_exists "$HOME/.claude/skills" "$STAGING/claude/skills" "claude skills"
copy_if_exists "$HOME/.claude/agents" "$STAGING/claude/agents" "claude agents"
copy_if_exists "$HOME/.claude/commands" "$STAGING/claude/commands" "claude commands"
copy_if_exists "$HOME/.claude/scripts" "$STAGING/claude/scripts" "claude scripts"

HITS_FILE="$STAGING/secret-scan-hits.txt"
if scan_for_secrets "$STAGING" "$HITS_FILE"; then
  safe_hits="$DEST_ROOT/secret-scan-hits-$stamp.txt"
  sed -E 's/(refresh_token|access_token|client_secret|authorization:|authorization =|bearer |api_key|apikey|private_key|session_token|id_token|oauth|cookie:|set-cookie|discord_token|bot_token).*/[REDACTED MATCH]/Ig' "$HITS_FILE" > "$safe_hits"
  append_log "❌ Backup stopped. Secret-like text was detected. Redacted hit list: \`secret-scan-hits-$stamp.txt\`"
  log "STOPPED: secret-like text detected. See $safe_hits"
  exit 2
fi

if [[ "$DRY_RUN" == "1" ]]; then
  append_log "✅ Dry run passed. No secret-like text detected. Nothing was written to live backup folders."
  log "DRY RUN PASSED: no live backup written."
  exit 0
fi

mkdir -p "$DEST_ROOT/codex" "$DEST_ROOT/claude"
rsync -a --delete "$STAGING/codex/" "$DEST_ROOT/codex/"
rsync -a --delete "$STAGING/claude/" "$DEST_ROOT/claude/"

write_manifest "$DEST_ROOT/codex" "Codex"
write_manifest "$DEST_ROOT/claude" "Claude"

append_log "✅ Backup completed. Codex and Claude runtime assets were updated."
log "DONE: backup completed at $DEST_ROOT"

