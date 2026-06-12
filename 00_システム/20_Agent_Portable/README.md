# Agent Portable Pack

最終更新: 2026-06-11

このフォルダは、Claude Codeをメイン司令塔、Codexを実行補助、Obsidianを正本として運用するための共通移行パック。

想定する利用先:
- Codex
- Claude Code / Claude Desktop
- OpenHands / OpenClode 系の汎用エージェント
- Hermes Agent
- 将来の Gemini Spark など

## 方針

Second Brainを唯一の共通記憶にする。

各エージェントには、このフォルダ、`00_システム/10_Agent/`、`06_エージェント運用/00_司令塔/NOW.md` を読ませる。エージェント固有の設定、キャッシュ、ログ、セッション履歴はSecond Brainへ混ぜない。

現在の主運用:

```text
Claude Code = メイン司令塔
Codex = 実行補助
Obsidian = 正本・共通記憶
06_エージェント運用 = AI管制塔
Claude Code Channels = 受付・通知・軽い指示
```

## 入れたもの

```text
archive/claude/skills/       Claude時代の事業スキル
archive/claude/agents/       Claude時代のエージェント定義
archive/claude/scripts/      自動化スクリプトの安全なアーカイブ
archive/claude/launchagents/ macOS自動実行設定の控え
specs/                       汎用エージェント用の仕様書
```

## 入れないもの

```text
~/.claude/channels/discord/.env
~/.claude/settings.local.json
~/.claude/history.jsonl
~/.claude/projects/
~/.claude/sessions/
~/.claude/plugins/cache/
~/.claude/telemetry/
~/.claude/file-history/
~/.claude/shell-snapshots/
```

理由:
- トークン、認証情報、PC固有パス、セッション履歴、キャッシュが混ざるため
- Google Drive同期に向かないため
- 新しいMac miniで再現する時のノイズになるため

## 新しいエージェントに最初に読ませるもの

1. `00_システム/10_Agent/persona.md`
2. `00_システム/10_Agent/rules.md`
3. `00_システム/10_Agent/workflows.md`
4. `00_システム/10_Agent/goals.md`
5. `00_システム/10_Agent/learning-log.md`
6. `00_システム/20_Agent_Portable/specs/agent-neutral-contract.md`
7. `00_システム/20_Agent_Portable/specs/claude-code-codex-obsidian-operation.md`
8. `00_システム/20_Agent_Portable/specs/mac-mini-migration-checklist.md`
9. `06_エージェント運用/00_司令塔/NOW.md`

## 判断ルール

エージェント固有機能は使ってよい。ただし、事業ルール、目標、ワークフロー、学びはSecond Brainに戻す。

つまり:

```text
実行環境 = 各エージェント
共通記憶 = Second Brain
再現手順 = Agent Portable Pack
```
