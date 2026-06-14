# Claude Code Build Instructions

このファイルは、Claude Codeで個人事業の社長向けAIエージェント運用環境を作っていくための実装指示書です。

目的は、Claude Codeをメイン入口にしつつ、経営ナレッジ、スキル、履歴をClaude専用に閉じ込めず、将来ほかのAIにも移行できるローカル環境を作ることです。

## 0. 最重要方針

```text
Claudeを主役にする。
でも、正本はClaudeの外に置く。
AIは個人事業の社長の右腕として振る舞う。
```

Claude Codeは入口であり、長期資産ではありません。

長期資産は以下に残します。

- `2nd-Brain/`: 経営ナレッジ、記憶、運用ルール
- `agent-skills/`: AIに任せる作業手順
- Git履歴: 事故防止、差分確認、巻き戻し

## 1. Claude Codeに最初に読ませるもの

Claude Codeは作業開始時に、必ず次の順番で読む。

1. `AI_AGENT_OPERATING_SYSTEM_DESIGN.md`
2. `README.md`
3. `2nd-Brain/AGENTS.md`
4. `2nd-Brain/wiki/index.md`
5. `2nd-Brain/wiki/business-dashboard.md`
6. 必要に応じて `agent-skills/`

## 2. 作る最終構造

最終的にはホーム直下にこの形で置く。

```text
/Users/kojinn/
├── 2nd-Brain/
│   ├── AGENTS.md
│   ├── inbox/
│   ├── raw/
│   │   ├── business/
│   │   ├── clients/
│   │   ├── finance/
│   │   └── projects/
│   ├── wiki/
│   │   ├── business-dashboard.md
│   │   ├── business-principles.md
│   │   ├── customers.md
│   │   ├── decision-log.md
│   │   ├── finance.md
│   │   ├── index.md
│   │   ├── log.md
│   │   ├── offers.md
│   │   ├── operations.md
│   │   ├── overview.md
│   │   └── sales-and-marketing.md
│   └── outputs/
│
├── agent-skills/
│   ├── business-chief-of-staff/
│   │   └── SKILL.md
│   ├── daily-knowledge-extract/
│   │   └── SKILL.md
│   └── knowledge-gardener/
│       └── SKILL.md
│
├── agent-adapters/
│   └── claude/
│       └── CLAUDE.md
│
└── Projects/
    └── AIエージェント構想/
        └── AGENTS.md
```

現時点でClaude以外のAI用フォルダは作らない。

## 3. Claude入口の完成形

正式配置後、Claudeが実際に読む場所に `CLAUDE.md` を置く。

候補:

- `/Users/kojinn/.claude/CLAUDE.md`
- `/Users/kojinn/Projects/AIエージェント構想/CLAUDE.md`

内容はこれにする。

```md
# Claude Entry

このClaude環境は入口にすぎない。

## Read First

1. `/Users/kojinn/2nd-Brain/AGENTS.md`
2. `/Users/kojinn/2nd-Brain/wiki/index.md`
3. `/Users/kojinn/2nd-Brain/wiki/business-dashboard.md`
4. 必要な `/Users/kojinn/agent-skills/`

## Rules

- 正本は `/Users/kojinn/2nd-Brain/` と `/Users/kojinn/agent-skills/` にある。
- Claude固有の記憶を正本にしない。
- `/Users/kojinn/2nd-Brain/raw/` は改変禁止。
- 重要変更はGit差分で確認する。
- 外部送信、削除、大量変更、購入、契約は人間の承認なしに行わない。
- AIは個人事業の社長の右腕として、売上、時間、リスク、資産性の観点で考える。
```

正式配置後の入口では、相対パスではなく絶対パスを使う。

## 4. 最初に実装する順番

Claude Codeは、次の順番で作業する。

### Step 1: inboxを作る

`2nd-Brain/inbox/` を作成する。

用途:

- 未整理メモ
- 会話ログ
- 日誌の下書き
- 資料の一時置き場
- AIに取り込ませたいもの
- 顧客メモ
- 商品・サービス案
- 売上、集客、発信、業務改善の気づき

`2nd-Brain/inbox/README.md` も作成し、次を書く。

- inboxは未整理の入力口
- rawに保存するものとwikiに整理するものを分ける
- inboxの内容は処理後も勝手に削除しない

### Step 2: Git管理を始める

この環境はGit履歴を安全装置にする。

Claude Codeは以下を行う。

```text
git init
git status
初回コミット候補の確認
```

ただし、コミット実行は人間確認後にする。

### Step 3: Claude入口を正式化する

`agent-adapters/claude/CLAUDE.md` を絶対パス版に更新する。

可能なら、実際にClaudeが読む場所にも同内容の入口を配置する。

ホーム直下や `.claude/` への書き込み権限がない場合は、配置手順だけを明記する。

### Step 4: knowledge-ingest手順を作る

`agent-skills/daily-knowledge-extract/SKILL.md` を強化し、Claudeが以下をできるようにする。

```text
inboxを見る
rawに保存すべきものを判断する
wikiに整理すべき知識候補を作る
index.mdを更新する
log.mdに記録する
Git差分で確認する
```

### Step 5: business-chief-of-staff手順を作る

`agent-skills/business-chief-of-staff/SKILL.md` を作成または強化し、Claudeが以下をできるようにする。

```text
事業メモを売上、顧客、商品、発信、業務、財務、判断に分類する
次の打ち手を提案する
社長がやるべきこととAI/外注/仕組みに任せることを分ける
重要判断をdecision-log.mdへ記録する案を作る
```

### Step 6: knowledge-lint手順を作る

`agent-skills/knowledge-gardener/SKILL.md` を強化し、Claudeが以下を点検できるようにする。

```text
出典不明の主張
古い情報
矛盾
孤立ページ
未リンクページ
重複ページ
confidenceが低いページ
```

結果は `2nd-Brain/outputs/` に保存する。

### Step 7: Obsidian連携を明文化する

Obsidianで開く対象は `2nd-Brain/` のみ。

`agent-skills/`、`agent-adapters/`、`.claude/` はObsidianで開かない。

### Step 8: バックアップ運用を明文化する

最低限、以下を使う。

```text
ローカル正本
Private GitHub repository
Time Machine
```

GitHubは履歴と同期。
Time Machineは誤削除やマシン故障への保険。

## 5. ナレッジ蓄積の運用

最初は完全自動にしない。

採用する初期レベル:

```text
半自動
```

流れ:

```text
ユーザーがinboxに入れる
↓
Claudeが知識候補と事業機会を抽出する
↓
wiki更新案を作る
↓
indexとlogを更新する
↓
Git差分で人間が確認する
↓
問題なければコミットする
```

## 6. Claudeに固定するコマンド名

Claude Codeとの会話では、以下の名前で作業を依頼する。

### `/knowledge-ingest`

`2nd-Brain/inbox/` と `2nd-Brain/raw/` の新規内容を読み、wiki更新案を作る。

### `/knowledge-review`

直近のwiki更新を確認し、出典不足、過剰な断定、重複を点検する。

### `/knowledge-lint`

矛盾、孤立ページ、古い情報、未リンクページを点検し、結果を `2nd-Brain/outputs/` に保存する。

### `/daily-capture`

日誌や会話ログから、長期的に残すべき判断、好み、方針、プロジェクト経緯を抽出する。

### `/business-review`

社長目線で、売上、顧客、商品、発信、業務、財務、判断ログを確認し、次の打ち手を提案する。

### `/weekly-garden`

週1回、index、overview、主要ページ、logを整理する。

## 7. やってはいけないこと

Claude Codeは以下をしない。

- Claude専用メモリを正本にする
- `.claude/` に知識本体を置く
- `raw/` を勝手に編集・削除する
- 大量変更を人間確認なしに行う
- 外部送信、購入、契約を行う
- 顧客へ無承認で連絡する
- APIキーやパスワードをMarkdownに保存する
- Codex、Gemini、Hermes、OpenClaw用フォルダを先回りで作る

## 8. 完了条件

最初の実装完了条件は以下。

- `2nd-Brain/inbox/` がある
- `2nd-Brain/raw/`、`wiki/`、`outputs/` の役割が明文化されている
- Claude入口が絶対パスで正本を指している
- `daily-knowledge-extract` が実運用できる手順になっている
- `business-chief-of-staff` が社長補佐として使える手順になっている
- `knowledge-gardener` が点検手順になっている
- Git管理が始まっている
- Obsidianで開く対象が `2nd-Brain/` に固定されている

## 9. Claude Codeへの最初の依頼文

Claude Codeには、次の文章を渡す。

```md
このリポジトリは、Claude Codeをメイン入口にした個人事業の社長向けAIエージェント環境です。

まず以下を読んでください。

1. `AI_AGENT_OPERATING_SYSTEM_DESIGN.md`
2. `CLAUDE_CODE_BUILD_INSTRUCTIONS.md`
3. `README.md`
4. `2nd-Brain/AGENTS.md`
5. `2nd-Brain/wiki/index.md`
6. `2nd-Brain/wiki/business-dashboard.md`

方針は「Claudeメイン。ただし正本はClaude専用にしない」です。
AIは個人事業の社長の右腕として、売上、時間、リスク、資産性の観点で考えてください。

最初にやることは以下です。

1. `2nd-Brain/inbox/` を作る
2. `agent-adapters/claude/CLAUDE.md` を正式配置向けの絶対パス版にする
3. `daily-knowledge-extract`、`business-chief-of-staff`、`knowledge-gardener` の手順を実運用向けに強化する
4. Git管理を始める準備をする

`raw/` は改変禁止です。
削除、大量変更、外部送信、購入、契約は人間承認なしにしないでください。
```
