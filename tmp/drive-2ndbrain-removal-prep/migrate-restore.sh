#!/bin/bash
# ============================================================
# Mac mini 移行用リストア（新Mac mini で tar 展開後に実行）
# 前提: ユーザー名が kojinn / tar.gz を ~/ に展開済み
#   tar -xzf ~/claude-migration.tar.gz -C ~/
# ============================================================
set -e
echo "🔧 新Mac miniセットアップ開始..."

# ---- 0. ユーザー名チェック（パスが /Users/kojinn 決め打ちのため致命的） ----
if [ "$HOME" != "/Users/kojinn" ]; then
  echo "❌ HOME=$HOME。このキットは /Users/kojinn 前提。"
  echo "   ユーザー名を kojinn にするか、全スクリプト内のパスを置換する必要あり。中止。"
  exit 1
fi

# ---- 1. nvm + node v24 ----
export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "📥 nvm入れる..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
# shellcheck disable=SC1090
\. "$NVM_DIR/nvm.sh"
nvm install 24 >/dev/null 2>&1 || true
nvm use 24 >/dev/null 2>&1 || true

# ---- 2. bun ----
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
if ! command -v bun >/dev/null 2>&1; then
  echo "📥 bun入れる..."
  curl -fsSL https://bun.sh/install | bash
fi

# ---- 3. Claude Code（npm版） ----
if ! command -v claude >/dev/null 2>&1; then
  echo "📥 Claude Code入れる..."
  npm install -g @anthropic-ai/claude-code
fi

# ---- 4. Python依存（収益取得・シート系スクリプト用） ----
echo "🐍 Python依存を入れる..."
python3 -m pip install --user --quiet --upgrade \
  pillow google-auth google-auth-oauthlib google-api-python-client 2>/dev/null \
  || echo "⚠️ pip失敗。手動で: python3 -m pip install --user pillow google-auth google-auth-oauthlib google-api-python-client"

# ---- 5. 2nd-Brain 復元（2026-07-02〜 ローカル正本＋snapshot/SSD構成） ----
# 正本はローカル ~/2nd-Brain-master（gitリポジトリ）。復元の優先順:
#   ①GitHubクローン ②vault-snapshotのtar（~/claude-backups または SSD）
MASTER="$HOME/2nd-Brain-master"
restore_from_snapshot() {
  local snapshot tmp_root
  snapshot="$(ls -1t "$HOME"/claude-backups/vault-snapshot-*.tar.gz /Volumes/SSD/claude-backups/vault-snapshot-*.tar.gz 2>/dev/null | head -1 || true)"
  if [ -z "$snapshot" ]; then
    return 1
  fi

  tmp_root="$(mktemp -d)"
  if ! tar -xzf "$snapshot" -C "$tmp_root" "2nd-Brain" 2>/dev/null; then
    rm -rf "$tmp_root"
    return 1
  fi
  if [ ! -s "$tmp_root/2nd-Brain/CLAUDE.md" ]; then
    rm -rf "$tmp_root"
    return 1
  fi

  mkdir -p "$MASTER"
  rsync -a --exclude '.DS_Store' "$tmp_root/2nd-Brain/" "$MASTER/"
  rm -rf "$tmp_root"
  (
    cd "$MASTER"
    git init -q
    git add -A
    git commit -q -m "restore: vault-snapshotから復元 $(date '+%F')" \
      || echo "⚠️ git初期コミットに失敗。$MASTER で手動確認して"
  )
  echo "🔗 vault-snapshotから正本を復元した: $snapshot"
}
if [ ! -d "$MASTER" ]; then
  if git clone -q "git@github.com:corocorobusiness-oss/2nd-brain.git" "$MASTER" 2>/dev/null; then
    echo "🔗 GitHubから正本を復元した"
  elif restore_from_snapshot; then
    :
  else
    echo "⚠️ 正本を復元できない。GitHub認証と vault-snapshot tar（~/claude-backups/ or SSD）を確認して"
  fi
fi
ln -sfh "$MASTER" "$HOME/2nd-Brain" 2>/dev/null || { rm -f "$HOME/2nd-Brain"; ln -s "$MASTER" "$HOME/2nd-Brain"; }
echo "🔗 ~/2nd-Brain → ローカル正本 リンクOK"

# ---- 6. inbox ディレクトリ復元（tarから除外したので空で作る） ----
mkdir -p "$HOME/.claude/channels/discord/inbox"

# ---- 7. スクリプトに実行権限 ----
chmod +x "$HOME"/.claude/scripts/*.sh 2>/dev/null || true

# ---- 8. launchd 再登録（discord-monitor は最後・Drive同期後が無難なので一旦スキップ可） ----
echo "⏰ launchd登録..."
UID_NUM=$(id -u)
for plist in "$HOME"/Library/LaunchAgents/com.claude.*.plist; do
  [ -e "$plist" ] || continue
  launchctl bootout "gui/$UID_NUM/$(basename "$plist" .plist)" 2>/dev/null || true
  launchctl bootstrap "gui/$UID_NUM" "$plist" 2>/dev/null \
    && echo "  ✅ $(basename "$plist")" \
    || echo "  ⚠️ $(basename "$plist") 失敗"
done

echo ""
echo "🎉 自動セットアップ完了！残りの手動作業（順番大事）:"
echo "  1. 旧Mac: Discordリスナーを停止（ボットは1接続のみ）"
echo "       launchctl bootout gui/\$(id -u)/com.claude.discord-monitor"
echo "  2. Google Drive デスクトップアプリにサインイン → 2nd-Brain 同期完了を待つ"
echo "  3. 'claude' を一度起動して /login（Claudeアカウント認証）"
echo "  4. MCP再認証: Gmail/Calendar/Drive コネクタ、必要なら freee 再認証"
echo "  5. Uber: drivers.uber.com に再ログイン（QR/SMS）"
echo "  6. 検証: pgrep -f 'bun server.ts' と discord MCPログで疎通確認"
echo "     （詳細は ~/.claude/scripts/MIGRATION.md のチェックリスト参照）"
