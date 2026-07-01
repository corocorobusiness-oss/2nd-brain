#!/bin/bash
# ============================================================
# run_script_learning.sh — 台本学習ジョブ（毎月1日11:00 launchd）
# ------------------------------------------------------------
# 根本改善(2026-06-28 P14): これまで `claude -p ... | tee` だけで、
#   - claudeが上限/認証/no-opで黙って死んでも検知できない（exit0サイレント故障）
#   - 成果（ルールブック更新）が出たかを誰も確認しない
#   - そもそもログが一度も生成されず「走った形跡が無い」状態だった
# を根治する。claude_run.sh 経由にして上限/認証/no-opを機械検知し、
# さらに「成果物が実際に更新されたか」を実行前後のmtimeで確認、
# 成果ゼロなら #レポートへ自己申告する（沈黙禁止）。
# ============================================================
set -u

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.bun/bin:$(/bin/ls -d /Users/kojinn/.nvm/versions/node/*/bin 2>/dev/null | /usr/bin/sort -V | /usr/bin/tail -1):/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn

SCRIPT_DIR="/Users/kojinn/.claude/scripts"
RUNNER="$SCRIPT_DIR/claude_run.sh"
NOTIFY="$SCRIPT_DIR/discord_notify.sh"
PROMPT_FILE="$SCRIPT_DIR/script_learning.md"
LOG_FILE="$SCRIPT_DIR/script_learning.log"
AGENT_VENDOR_NAME="${SCRIPT_LEARNING_AGENT_VENDOR:-claude}"
DEFAULT_CODEX_DRYRUN="$SCRIPT_DIR/run_script_learning_codex_dryrun.sh"
CODEX_DRYRUN="$DEFAULT_CODEX_DRYRUN"
# 成果物＝台本執筆ルールブック。これが更新されれば「学習が効いた」とみなす。
RULEBOOK="/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md"
LABEL="script-learning"

# --- 通知ヘルパー（失敗しても処理は止めない） ---
notify() {
  if [ -x "$NOTIFY" ]; then
    "$NOTIFY" "$1" >/dev/null 2>&1 || echo "run_script_learning: 通知失敗: $1" >&2
  else
    echo "run_script_learning: discord_notify.sh が無い。通知できず: $1" >&2
  fi
}

case "$AGENT_VENDOR_NAME" in
  claude)
    ;;
  codex)
    if [ "${SCRIPT_LEARNING_CODEX_DRYRUN:-}" != "" ]; then
      if [ "${SCRIPT_LEARNING_ALLOW_CODEX_DRYRUN_OVERRIDE:-}" != "1" ]; then
        notify "🕳️ [${LABEL}] SCRIPT_LEARNING_CODEX_DRYRUN override が未承認のためCodex dry-runを中止（自己申告）。"
        exit 64
      fi
      CODEX_DRYRUN="$SCRIPT_LEARNING_CODEX_DRYRUN"
    fi
    if [ ! -x "$CODEX_DRYRUN" ]; then
      notify "🕳️ [${LABEL}] SCRIPT_LEARNING_AGENT_VENDOR=codex だが dry-run入口($CODEX_DRYRUN)が無い/実行不可。Codex実行を中止（自己申告）。"
      exit 1
    fi
    echo "run_script_learning: SCRIPT_LEARNING_AGENT_VENDOR=codex -> dry-run only ($CODEX_DRYRUN)"
    exec "$CODEX_DRYRUN"
    ;;
  *)
    notify "🕳️ [${LABEL}] 未知の SCRIPT_LEARNING_AGENT_VENDOR='$AGENT_VENDOR_NAME'（claude|codex のみ）。学習ジョブ中止（自己申告）。"
    exit 64
    ;;
esac

# --- Claude本番経路の前提チェック（Codex dry-run経路では使わない） ---
if [ ! -r "$PROMPT_FILE" ]; then
  notify "🕳️ [${LABEL}] プロンプト($PROMPT_FILE)が読めず学習ジョブを開始できなかった（自己申告）。"
  exit 1
fi
PROMPT="$(cat "$PROMPT_FILE")"
if [ -z "$(printf '%s' "$PROMPT" | tr -d '[:space:]')" ]; then
  notify "🕳️ [${LABEL}] プロンプト本文が空だった（$PROMPT_FILE）。学習ジョブ中止（自己申告）。"
  exit 1
fi

if [ ! -x "$RUNNER" ]; then
  notify "🕳️ [${LABEL}] claude_run.sh が無い/実行不可。学習ジョブ中止（自己申告）。"
  exit 1
fi

# --- 実行前の成果物mtimeを記録（更新検知の基準） ---
BEFORE_MTIME=0
[ -f "$RULEBOOK" ] && BEFORE_MTIME="$(/usr/bin/stat -f %m "$RULEBOOK" 2>/dev/null || echo 0)"

# --- claude_run.sh 経由で実行（上限/認証/no-opを機械検知。ログは必ず残す） ---
"$RUNNER" --label "$LABEL" -- -p "$PROMPT" \
  --permission-mode auto \
  --allowedTools "mcp__plugin_discord_discord__reply,Bash,Read,Write,Edit,Glob,Grep" \
  2>&1 | tee "$LOG_FILE"
RC="${PIPESTATUS[0]}"   # claude_run.sh の終了コード（tee=0で潰さない）

# claude_run.sh は 2=上限 / 3=認証 / 4=no-op / その他=claude非0 を返し、
# その時点で #レポートへ自己申告済み。ここでは成果ゼロの追撃確認をする。

# --- 実行後の成果物mtimeで「更新されたか」を判定 ---
AFTER_MTIME=0
[ -f "$RULEBOOK" ] && AFTER_MTIME="$(/usr/bin/stat -f %m "$RULEBOOK" 2>/dev/null || echo 0)"

if [ "$RC" -eq 0 ]; then
  if [ "$AFTER_MTIME" = "$BEFORE_MTIME" ]; then
    # exit0だがルールブックが1文字も更新されていない＝成果ゼロのサイレント故障。
    # （ルール変更なしの正常ケースも有り得るが、その場合でも更新履歴行は追記される設計
    #   なのでmtimeは動く。動いていない＝プロンプト未読込/no-opの疑いとして申告する）
    notify "🕳️ [${LABEL}] 学習ジョブはexit0で終わったが、台本執筆ルール.md が一切更新されていない（成果ゼロの疑い・自己申告）。プロンプト未読込やno-opの可能性。ログ: $LOG_FILE"
    exit 4
  fi
  echo "run_script_learning: OK（ルールブック更新を確認）"
fi

exit "$RC"
