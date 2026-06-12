# Portable Inventory

最終更新: 2026-06-10

## Claude Skills

保存先:

```text
00_システム/20_Agent_Portable/archive/claude/skills/
```

移行済み:

- `automation-architect`
- `daily-knowledge-extract`
- `knowledge-gardener`
- `neta-research`
- `thread-research-planner`
- `uber-earnings`
- `uber-weekly-plan`
- `ymm4-dic-generator`
- `youtube-pipeline`
- `youtube-script-checker`
- `youtube-script-parts`
- `daily-target.md`
- `monthly-report.md`
- `process-receipt.md`
- `record-sales.md`
- `today-start.md`

## Claude Agents

保存先:

```text
00_システム/20_Agent_Portable/archive/claude/agents/
```

移行済み:

- `accounting.md`
- `sales-tracker.md`
- `youtube-advisor.md`

## Legacy Scripts

保存先:

```text
00_システム/20_Agent_Portable/archive/claude/scripts/
```

ログファイル、ロックファイル、キャッシュは除外済み。

## LaunchAgents

保存先:

```text
00_システム/20_Agent_Portable/archive/claude/launchagents/
```

移行済み:

- `com.claude.daily-evening.plist`
- `com.claude.daily-knowledge-extract.plist`
- `com.claude.daily-morning.plist`
- `com.claude.discord-monitor.plist`
- `com.claude.gmail-cleanup.plist`
- `com.claude.knowledge-gardener.plist`
- `com.claude.monthly-accounting.plist`
- `com.claude.neta-retrain.plist`
- `com.claude.sales-reminder.plist`
- `com.claude.script-learning.plist`
- `com.claude.trash-cleanup.plist`
- `com.claude.uber-earnings.plist`
- `com.claude.uber-weekly-plan.plist`
- `com.claude.weekly-accounting.plist`

注意:
- これは有効化用ではなく、再現用の控え
- Mac miniでそのまま有効化しない
- 必要なものだけ新環境のパスに直して再作成する

## Antigravity / .agent

保存先:

```text
00_システム/20_Agent_Portable/archive/antigravity/.agent/
```

旧ローカルバックアップ `/Users/kojinn/2nd-Brain-backup-20260609/.agent/` から完全コピー済み。

含むもの:
- `rules/`
- `skills/`
- `skills/*/resources/`
- `skills/*/scripts/`
- `workflows/`

## Codex

保存先:

```text
00_システム/20_Agent_Portable/archive/codex/
```

移行済み:
- `config.toml`
- `default.rules`

除外:
- `auth.json`
- `*.sqlite`
- `session_index.jsonl`
- `logs_*.sqlite`
- `memories_*.sqlite`
- `state_*.sqlite`
- `browser/sessions/`
- `shell_snapshots/`

## Obsidian

保存先:

```text
00_システム/20_Agent_Portable/archive/obsidian/obsidian.json
```

Vault内設定はSecond Brain直下の `.obsidian/` に保存済み。

除外:
- ObsidianアプリのCache
- Cookies
- Local Storage
- IndexedDB
- Session Storage

## Local Work Archives

ローカルに残っていた制作物をSecond Brainへ退避。

```text
99_アーカイブ/Local_Work/youtube-work/
01_プロジェクト/YouTube/制作アーカイブ/平将門_script/
```

`youtube-work` からは以下を除外:
- `uber_api*.json`
- `uber_daily.json`
- `weather.json`

## YouTube Revenue Automation

保存先:

```text
00_システム/20_Agent_Portable/archive/youtube-revenue/
00_システム/20_Agent_Portable/archive/launchagents/com.kojinn.youtube-revenue.plist
```

移行済み:
- `fetch_daily.py`
- `get_token.py`
- `get_token2.py`
- `get_token3.py`
- `reauth.py`
- `spreadsheet_id.txt`
- `com.kojinn.youtube-revenue.plist`

除外:
- `token*.json`
- `client_secret.json`
- `sheets_token.json`
- `*.log`
- `fetch_error.log`

## Excluded

以下は意図的に除外。

- `~/.claude/channels/discord/.env`
- `~/.claude/channels/discord/inbox/`
- `~/.claude/settings.local.json`
- `~/.claude/history.jsonl`
- `~/.claude/projects/`
- `~/.claude/sessions/`
- `~/.claude/plugins/cache/`
- `~/.claude/telemetry/`
- `~/.claude/file-history/`
- `~/.claude/shell-snapshots/`
- `~/.codex/auth.json`
- `~/.codex/*.sqlite`
- `~/.config/*/token*.json`
- `~/.config/*/client_secret*.json`
- `~/.config/youtube-revenue/sheets_token.json`
- `~/.playwright-mcp/`
