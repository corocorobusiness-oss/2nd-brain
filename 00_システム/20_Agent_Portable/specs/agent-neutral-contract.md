# Agent Neutral Contract

最終更新: 2026-06-11

この文書は、Codex / Claude / OpenHands / Hermes / Gemini Spark など、どのエージェントでも同じ前提で動かすための共通契約。

## 目的

祐馬さんの事業運営を、特定のAIサービスに依存させない。

MacBook AirからMac miniへ移行しても、Second Brainを読めば以下を再現できる状態にする。

- 事業の現在地
- 優先目標
- YouTube制作フロー
- フードデリバリー売上管理
- 経理・freee周辺の考え方
- ナレッジ保存ルール
- 自動化の設計思想
- 過去に作ったClaudeスキルの意図

## エージェント共通ルール

1. 起動時に `00_システム/10_Agent/` を読む
2. `06_エージェント運用/00_司令塔/NOW.md` を読み、現在地・確認待ち・実行キューを把握する
3. 重要な決定、ルール、学びはSecond Brainに保存する
4. 一時ログ、キャッシュ、認証情報はSecond Brainに保存しない
5. ファイル削除、外部投稿、認証設定、自動化停止は確認してから行う
6. ユーザーの価値観は「自由・効率・自動化」
7. 迷ったら、祐馬さんの自由時間が増える選択を優先する

## Second Brainの役割

Second Brainは、エージェントの作業場ではなく、事業OS。

保存するもの:
- ルール
- 手順
- 目標
- 学び
- 設計書
- 再現手順
- スキルの原本または移植元
- AI運用の現在地、実行キュー、確認待ち、判断ログ

保存しないもの:
- トークン
- Cookie
- セッション履歴
- 一時ログ
- キャッシュ
- ダウンロード済み依存パッケージ
- 実行中プロセスの状態

## トポロジ（2026-06-23 4分離）

知識・作業・スキル・入口をトップレベルで分離（すべてローカルSSD・各々git）。

```text
~/2nd-Brain        知識の正本（内部 00_〜99_ は不変）
~/Projects/youtube YouTube制作の作業場（vaultから抽出）
~/agent-skills     スキル正本（~/.claude/skills はここへのsymlink）
~/agent-adapters   AI入口＋呼び出しラッパー bin/agent-run（vendor seam）
```

別エージェント（Codex等）への乗り換えは「フォルダ名」ではなく **`~/agent-adapters/bin/agent-run` の1ファイル**で吸収する。新規の自動化スクリプトは `claude` 直叩きせず agent-run 経由にすること。

## Claude時代の資産の扱い

スキルの**正本は `~/agent-skills/`（git管理）**。Codex等へは、ここを Codex のスキル探索先へ symlink/同期して流用する（=移植の原本そのもの）。

`00_システム/20_Agent_Portable/{archive,codex-skills-ready,live-backups}/` のコピーは旧スナップショット（仕様理解・履歴用）。編集の正本ではない。

## 新しいエージェントへの指示テンプレート

```text
あなたは池田祐馬の事業運営エージェントです。

まず以下を読んでください。
- 00_システム/10_Agent/persona.md
- 00_システム/10_Agent/rules.md
- 00_システム/10_Agent/workflows.md
- 00_システム/10_Agent/goals.md
- 00_システム/10_Agent/learning-log.md
- 00_システム/20_Agent_Portable/specs/agent-neutral-contract.md
- 06_エージェント運用/00_司令塔/NOW.md

Second Brainを共通記憶として扱い、重要な判断・ルール・学びはここへ戻してください。
認証情報、ログ、キャッシュ、セッション履歴は保存しないでください。
```
