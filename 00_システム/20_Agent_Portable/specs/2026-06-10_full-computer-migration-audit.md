# Full Computer Migration Audit

実施日: 2026-06-10

## 結論

重大な移行漏れは修正済み。

追加で見つけて保存したもの:
- 旧バックアップ内の `.agent` 完全版
- Codex設定控え
- Obsidian Vault一覧
- `youtube-work` の制作・リサーチ素材
- デスクトップの `平将門` 台本一式

## 修正済み

### 1. Antigravity `.agent`

旧バックアップ:

```text
/Users/kojinn/2nd-Brain-backup-20260609/.agent/
```

保存先:

```text
00_システム/20_Agent_Portable/archive/antigravity/.agent/
```

`resources/` と `scripts/` までコピー済み。

### 2. Local youtube-work

元:

```text
/Users/kojinn/youtube-work/
```

保存先:

```text
99_アーカイブ/Local_Work/youtube-work/
```

除外:
- `uber_api*.json`
- `uber_daily.json`
- `weather.json`

### 3. 平将門 台本一式

元:

```text
/Users/kojinn/Desktop/masakado_script/
```

保存先:

```text
01_プロジェクト/YouTube/制作アーカイブ/平将門_script/
```

### 4. Codex設定

元:

```text
/Users/kojinn/.codex/config.toml
/Users/kojinn/.codex/rules/default.rules
```

保存先:

```text
00_システム/20_Agent_Portable/archive/codex/
```

### 5. Obsidian Vault一覧

元:

```text
/Users/kojinn/Library/Application Support/obsidian/obsidian.json
```

保存先:

```text
00_システム/20_Agent_Portable/archive/obsidian/obsidian.json
```

### 6. YouTube収益取得 自動化

元:

```text
/Users/kojinn/Library/LaunchAgents/com.kojinn.youtube-revenue.plist
/Users/kojinn/.config/youtube-revenue/
```

保存先:

```text
00_システム/20_Agent_Portable/archive/launchagents/com.kojinn.youtube-revenue.plist
00_システム/20_Agent_Portable/archive/youtube-revenue/
```

保存したもの:
- Pythonスクリプト
- `spreadsheet_id.txt`
- LaunchAgent定義

除外:
- `token*.json`
- `client_secret.json`
- `sheets_token.json`
- `*.log`

## 確認済みでコピーしないもの

### 認証・秘密情報

```text
/Users/kojinn/.config/freee-mcp/tokens.json
/Users/kojinn/.config/google-sheets/token.json
/Users/kojinn/.config/youtube-revenue/token*.json
/Users/kojinn/.config/youtube-revenue/client_secret.json
/Users/kojinn/.codex/auth.json
/Users/kojinn/.claude/channels/discord/.env
```

Mac miniでは再ログイン・再認証する。

### セッション・キャッシュ・ログ

```text
/Users/kojinn/.codex/*.sqlite
/Users/kojinn/.claude/history.jsonl
/Users/kojinn/.claude/projects/
/Users/kojinn/.claude/sessions/
/Users/kojinn/.playwright-mcp/
/Users/kojinn/Library/Application Support/obsidian/Cache/
```

Second Brainへ入れない。

## 残課題

### Downloads

```text
/Users/kojinn/Downloads/skills.zip
/Users/kojinn/Downloads/b10eb237-f6dd-57bf-9a7a-424990456fca_34eb5268-217f-55ba-af2a-08a3e40b70ed.pdf
```

用途未確定。必要なら後で中身を確認する。
