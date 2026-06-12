# Agent Runtime Backup

`.codex` と `.claude` から、再現に必要な自作資産だけを Second Brain に退避する手動バックアップ。

## バックアップ対象

- `~/.codex/skills/`
- `~/.codex/rules/`
- `~/.claude/skills/`
- `~/.claude/agents/`
- `~/.claude/commands/`
- `~/.claude/scripts/`

存在しないフォルダはスキップする。

## バックアップしないもの

認証情報、セッション、ログ、キャッシュ、DB、トークン類は除外する。

## 実行方法

まず安全確認だけする:

```bash
zsh "00_システム/20_Agent_Portable/backup_automation/backup_agent_runtime.sh" --dry-run
```

問題なければ実行:

```bash
zsh "00_システム/20_Agent_Portable/backup_automation/backup_agent_runtime.sh"
```

## 毎日自動実行にする

通常のMacターミナルで1回だけ実行する:

```bash
zsh "00_システム/20_Agent_Portable/backup_automation/register_launchd.sh"
```

これで `~/Library/LaunchAgents/com.yuma.agent-runtime-backup.plist` に登録され、
毎日23:30に自動実行される。

止めたいとき:

```bash
zsh "00_システム/20_Agent_Portable/backup_automation/unregister_launchd.sh"
```

## 保存先

```text
00_システム/20_Agent_Portable/live-backups/
```

## 注意

秘密情報っぽい文字列を検出した場合、バックアップは中止される。
その場合は `live-backups/backup-log.md` を確認する。
