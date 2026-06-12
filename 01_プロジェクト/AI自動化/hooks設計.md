# Hooks設計

作成日: 2026-06-11
対象: 24時間AIエージェント構想

## 結論

Hooksは入れる。

Watchtowerが「毎朝の健康診断」なら、Hooksは「作業中の事故防止」。

24時間動くAIに必要なのは、強いAIより先に、止まれるAI。

## 入れる順番

### 1. Dangerous Action Guard

目的:

削除、外部投稿、会計確定、外部アカウント設定変更などを実行前に止める。

対象:

- `rm`
- ファイル削除
- SNS投稿
- Discord投稿
- freeeや帳簿の確定変更
- launchdジョブの停止・削除
- 外部サービスの設定変更

ルール:

ユーザーの明確な承認がない場合は止める。

### 2. Read Before Write Guard

目的:

共有ファイルの上書き事故を防ぐ。

対象:

- `AGENTS.md`
- `CLAUDE.md`
- `00_システム/10_Agent/`
- `00_システム/00_UserProfile/`
- `00_システム/20_Agent_Portable/specs/`

ルール:

編集前に最新内容を読む。

### 3. Retry Loop Guard

目的:

同じ失敗を繰り返して、時間やクレジットを溶かす事故を防ぐ。

ルール:

同じツール、同じ対象、似たエラーが短時間で3回続いたら停止して報告する。

### 4. Session End Recorder

目的:

会話の中で決まった重要事項をSecond Brainへ戻す。

ルール:

自動保存ではなく、保存候補を出す。

ただし、ユーザーが「保存して」「反映して」と言った場合は保存する。

### 5. Context Refresh Hook

目的:

長時間作業時のコンテキスト腐敗を防ぐ。

ルール:

長い作業では、現在地・未完了・触ったファイル・次の手を短く残す。

## Second Brainに保存するもの

- Hookの目的
- Hookのルール
- 再現手順
- 移植用スクリプト

## Second Brainに保存しないもの

- 認証情報
- セッション
- Cookie
- ランタイムキャッシュ
- エージェント固有の設定丸ごと

## 最初の実装方針

まずは仕様として固定する。

次にClaude Code / Codexの実際のHook設定へ移植する。

最優先は以下の2つ。

1. Dangerous Action Guard
2. Read Before Write Guard

この2つだけで、24時間AIエージェントの事故率はかなり下がる。

