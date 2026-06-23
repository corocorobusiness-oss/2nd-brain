# Mac mini 移行ランブック（あおい / Claude Code 環境）

このファイルは **Mac mini側で起動したClaude Code** が読んで実行するための手順書。
旧Mac（Intel・ユーザー名 kojinn）から、Discord常駐ボット＋各種自動化を新Mac miniへ
**必要分だけクリーン移植**し、**旧Macは引退**させる。

---

## 0. 大前提（最初に確認）

- **新Mac miniのユーザー名は `kojinn`** であること。全スクリプト・plist・トークンパスが
  `/Users/kojinn` 決め打ち。違う場合は移植が破綻するので、アカウント名を kojinn にするか
  全ファイルのパス一括置換が必要（`restore` スクリプトが HOME を検査して中止する）。
- **アーキテクチャは別物の可能性**（旧=Intel x86_64 / mini=Apple Silicon arm64）。
  → **バイナリは持ち込まない**。bun/node/claude は新機でネイティブ再インストール（restoreが実施）。
- **Discordボットは同時に1ゲートウェイ接続のみ**。旧と新で同時にリスナーを上げると競合する。
  → 新機の疎通を確認する直前に、旧Macのリスナーを停止する（手順5）。

---

## 1. 移行物の全体像

| 区分 | 中身 | 移行方法 |
|---|---|---|
| Claude設定 | `~/.claude/`（settings, skills, scripts, **memory**, plugins, channels） | tar同梱 |
| Claude状態 | `~/.claude.json`（trust, MCP/plugin設定） | tar同梱 |
| 認証情報 | `~/.config/{freee-mcp,youtube-revenue,google-sheets}`, `~/.claude/channels/discord/.env` | tar同梱 |
| シェル | `~/.zshrc`（nvm/bun PATH） | tar同梱 |
| 定期実行 | `~/Library/LaunchAgents/com.claude.*.plist`（14ジョブ） | tar同梱→restoreで再登録 |
| Vault | `~/2nd-Brain` → **Google Driveへのsymlink** | Drive再サインイン＋symlink再作成 |
| ツール | nvm/node24, bun, claude(npm), Python依存 | restoreで再インストール |
| 除外 | inbox画像(56M, Drive済), ログ/キャッシュ/transcripts | 持ち込まない |

---

## 2. 手順（新Mac mini）

```bash
# (旧Macで作成済みの) 移行tarを ~/ に置いてから:
tar -xzf ~/claude-migration.tar.gz -C ~/
bash ~/.claude/scripts/migrate-restore.sh
```

`migrate-restore.sh` が自動でやること:
1. HOME=/Users/kojinn を検査（違えば中止）
2. nvm + node24 / bun / claude(npm) をインストール
3. Python依存（pillow, google-auth, google-auth-oauthlib, google-api-python-client）
4. `~/2nd-Brain` symlink 再作成（Drive同期済みなら）
5. 空の inbox ディレクトリ作成
6. scripts に実行権限付与
7. launchd 14ジョブを bootstrap で再登録

---

## 3. ⚠️ 今回(2026-06)のDiscord無反応バグ＝再発しやすい落とし穴

移植後に **必ず** 効いているか確認すること。詳細は memory `project_discord_listener.md`。

1. **bun が launchd の PATH に必要**
   `~/.claude/scripts/discord-listener.sh` の PATH 先頭に `/Users/kojinn/.bun/bin` が
   入っていること。無いと discord MCP が `bun not found` で起動せず無反応になる。
2. **expect はキーストロークを送らない**
   `~/.claude/scripts/discord-listener.exp` は spawn して `expect eof` で待つだけ。
   旧版は "cancel" 検知で `2\r` を送り、CLI更新後にチャンネル接続をキャンセルしていた。
   （今回のtarには修正済みの版が入っている。CLI更新で確認ダイアログが復活したら都度対応）
3. **`DISABLE_AUTOUPDATER=1`** が `discord-listener.sh` と plist に入っていること
   （起動時の自動アップデート固まり対策）。

---

## 4. 手動が必要な作業（順番が大事）

1. **Google Drive デスクトップアプリにサインイン** → `2nd-Brain` の同期完了を待つ。
   完了後に symlink を確認: `ls -la ~/2nd-Brain`（リンク先が存在すること）
2. **`claude` を一度起動し `/login`**（Claudeアカウント認証）
3. **MCP再認証**: Gmail / Google Calendar / Google Drive コネクタ。
   freee はトークン同梱だが失効していたら memory `reference_freee_token_reauth.md` の手順で再認証
   （Playwright + Googleログインで全自動可）
4. **Uber 再ログイン**: drivers.uber.com に QR/SMS でログイン（memory `reference_uber_earnings_fetch.md`）
5. **旧Macのリスナー停止**（ボット競合回避、Discord疎通テストの直前に）:
   ```bash
   # 旧Macで:
   launchctl bootout gui/$(id -u)/com.claude.discord-monitor
   ```

---

## 5. 検証チェックリスト（移植完了の判定）

```bash
# ツール
claude --version && bun --version && node --version
# discordリスナー稼働
launchctl list | grep discord-monitor
pgrep -fl "claude --channels"          # claude本体
pgrep -f  "bun server.ts"              # discord MCPサーバ本体（これが居れば疎通の核はOK）
# discord MCP がDiscordゲートウェイ(162.159.x:443)に繋がっているか
lsof -nP -p "$(pgrep -f 'bun server.ts'|head -1)" | grep 162.159
# discord MCP接続ログ（"Successfully connected" / "Channel notifications registered"）
ls -t ~/Library/Caches/claude-cli-nodejs/-Users-kojinn/mcp-logs-plugin-discord-discord/*.jsonl | head -1 | xargs tail -5
# memory が移行できているか
ls ~/.claude/projects/-Users-kojinn/memory/ | head
# 定期ジョブ
launchctl list | grep com.claude | wc -l   # 14前後
```

最終テスト: **Discordメインチャンネル(1486946641389817899) にメッセージを送り、ボットが返信**すればOK。

---

## 6. 完了後

- 認証情報を含む `~/claude-migration.tar.gz` を **削除**（旧・新両方）。
- 旧Macの launchd ジョブを全停止（引退）:
  ```bash
  for p in ~/Library/LaunchAgents/com.claude.*.plist; do
    launchctl bootout gui/$(id -u)/"$(basename "$p" .plist)" 2>/dev/null
  done
  ```
- このランブックの結果（うまくいった点・詰まった点）を memory に追記しておくこと。
