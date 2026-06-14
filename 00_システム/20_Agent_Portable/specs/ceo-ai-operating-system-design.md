# AI Agent Operating System Design

この設計書は、個人事業の社長として使うAIエージェント環境の全体設計である。Claude Codeをメイン入口にしながら、将来ほかのAIモデルやアプリに乗り換えても、経営ナレッジを使い続けられるようにする。

## 1. Five Expert Perspectives

この設計は、5つの専門視点で合意する。

### 1. Architect

最優先は「経営ナレッジの正本を1つにする」こと。

AIアプリを正本にしない。Claude、Codex、Gemini、Hermes、OpenClawなどは入口であり、顧客理解、商品設計、売上導線、業務改善、判断履歴はローカルのMarkdownとGitに残す。

### 2. Safety Engineer

最優先は「壊れても戻せる」こと。

自律性を上げる前に、Git履歴、raw保護、承認境界、バックアップを整える。AIの賢さではなく、仕組みで事故を止める。

### 3. Knowledge Curator

最優先は「知識が腐らない」こと。

元資料、整理済み知識、ログを分ける。AIはwikiを育てるが、主張はrawまで遡れるようにする。事業に関する知識は、売上、顧客、商品、発信、業務、財務、判断に分ける。

### 4. Automation Designer

最優先は「最初から完全自動にしない」こと。

半自動のナレッジ蓄積から始める。慣れた処理だけ段階的に自動化する。

### 5. Future Migration Designer

最優先は「将来の乗り換えコストを低くする」こと。

Claudeメインで始めるが、Claude専用の知識形式にしない。Markdown、Git、明示的な入口ファイルを使う。

## 2. Final Direction

採用する型はこれ。

```text
Claudeメインで運用する
でも、正本はClaude専用にしない
```

現時点ではClaude以外のアダプタフォルダは作らない。将来必要になったAIだけ入口を追加する。

## 3. Final Folder Design

最終的な正式配置はホーム直下を想定する。

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

現在の作業フォルダは、この正式配置に移す前の雛形である。

## 4. What Each Folder Means

### `2nd-Brain/`

知識、記憶、運用ルールの正本。Obsidianで開く対象は基本的にここだけ。

個人事業の社長にとっては、経営ナレッジベースとして扱う。

### `2nd-Brain/inbox/`

未整理のメモ、会話ログ、資料、日誌を一時的に入れる場所。AIが最初に確認する入力口。

顧客メモ、売上アイデア、発信案、商品改善案、業務改善メモもここに入れる。

### `2nd-Brain/raw/`

元資料の保管場所。原則としてAIは改変しない。後から検証できる一次情報を残す。

### `2nd-Brain/wiki/`

AIが整理・維持する知識。回答や執筆ではここを主に参照する。

事業運用では、`business-dashboard.md` を経営ナレッジの入口にする。

### `2nd-Brain/outputs/`

AIが出した点検結果、日次レポート、相談ログ、lint結果を置く場所。

### `agent-skills/`

AI共通の作業手順。Claude専用ツール名を書かず、将来のAIでも読めるようにする。

初期の重要スキルは `business-chief-of-staff`、`daily-knowledge-extract`、`knowledge-gardener`。

### `agent-adapters/claude/`

Claude用の薄い入口。正本は置かない。

### `Projects/`

個別プロジェクトの作業場。プロジェクト固有の入口だけを置き、長期知識は `2nd-Brain/wiki/` に昇格する。

## 5. Claude Entry Design

Claudeが実際に読む入口には、最終的にこの内容を置く。

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
- AIは個人事業の社長の右腕として振る舞う。
```

相対パスではなく、正式配置後は絶対パスを使う。

## 6. Knowledge Accumulation Flow

最初に作るべき運用フローは、完全自動ではなく半自動。

```text
inboxにメモや資料を入れる
↓
Claudeがdaily-knowledge-extractを実行
↓
重要な知識候補と事業機会を抽出する
↓
wikiに整理案を書く
↓
indexとlogを更新する
↓
Git差分で人間が確認する
↓
問題なければコミットする
```

## 7. Core Commands

Claudeに頼む作業は、次の名前で固定する。

### `/knowledge-ingest`

`inbox/` と `raw/` の新規内容を読み、wiki更新案を作る。

### `/knowledge-review`

直近のwiki更新を確認し、出典不足、過剰な断定、重複を点検する。

### `/knowledge-lint`

矛盾、孤立ページ、古い情報、未リンクページを点検し、`outputs/` に結果を残す。

### `/daily-capture`

日誌や会話ログから、長期的に残すべき判断、好み、方針、プロジェクト経緯を抽出する。

### `/business-review`

社長目線で、売上、顧客、商品、発信、業務、財務、判断ログを確認し、次の打ち手を提案する。

### `/weekly-garden`

週1回、index、overview、主要ページ、logを整理する。

## 8. Automation Levels

### Level 1: Manual

人間が資料を入れ、Claudeに整理を依頼する。

### Level 2: Semi-Automatic

Claudeが定型コマンドで知識候補を作り、人間がGit差分で確認する。

初期運用はここを目標にする。

### Level 3: Scheduled

毎日または毎週、定期実行で抽出とlintを行う。重要変更は承認制。

### Level 4: Autonomous

通知、予定、外部ツール連携まで含める。これはGit、バックアップ、承認境界が安定してから。

## 9. Permission Matrix

### Automatic

- 要約
- 分類
- wiki下書き
- index更新案
- log追記
- lint結果の保存
- 事業メモの分類
- 打ち手候補の整理

### Requires Approval

- `raw/` の変更
- 重要ページの大幅更新
- フォルダ構造変更
- 予定や通知の作成
- Gitコミット
- 外部サービスへの送信
- 顧客向け文面の送信
- 契約、購入、財務に関わる判断

### Prohibited by Default

- 元資料の削除
- 大量削除
- 購入
- 契約
- 秘密情報の外部共有
- APIキーやパスワードの保存
- AI固有メモリを正本にすること
- 顧客への無承認連絡

## 10. Git Workflow

Gitは安全装置である。

```text
作業前: 状態確認
作業中: 小さく変更
作業後: 差分確認
問題なし: コミット
問題あり: 差分から戻す
```

推奨コミット単位:

- `init knowledge base`
- `add claude adapter`
- `ingest daily notes`
- `garden knowledge index`
- `lint knowledge base`

## 11. Raw Protection

`raw/` は元資料なので、通常は編集しない。

最低限の運用:

- `raw/` の変更がGit差分に出たら必ず確認する。
- `raw/` の削除は承認必須にする。
- AIは `raw/` を読むが、要約や解釈は `wiki/` に書く。

将来の強化:

- pre-commit hookで `raw/` の削除を警告する。
- `raw/` を読み取り専用に近い運用にする。

## 12. Obsidian Design

Obsidianで開くのは `2nd-Brain/` だけ。

Obsidianの役割:

- 日誌を書く
- wikiを見る
- 軽い修正をする
- 知識のつながりを見る

Obsidianで開かないもの:

- `agent-skills/`
- `agent-adapters/`
- `.claude/`
- `.codex/`
- 各AIの設定フォルダ

## 13. Backup Design

最低限のバックアップは3層。

```text
Local canonical files
↓
Private GitHub repository
↓
Time Machine
```

GitHubは同期と履歴。Time Machineはローカル障害や誤削除への保険。

## 14. Future AI Migration

将来ほかのAIを使うときは、フォルダを最初から作らない。必要になった時だけ追加する。

例:

```text
agent-adapters/
├── claude/
│   └── CLAUDE.md
└── codex/
    └── AGENTS.md
```

追加する入口の中身は、正本へのポインタだけにする。

## 15. Next Build Order

次にやる順番はこれ。

1. `2nd-Brain/inbox/` を作る。
2. Gitを初期化する。
3. Claude入口を絶対パス版にする。
4. `knowledge-ingest` の手順をClaude用に明文化する。
5. Obsidianで `2nd-Brain/` を開く。
6. Obsidian Gitまたは手動Git運用を始める。
7. 週次lintを運用する。
8. バックアップを設定する。

## 16. Final Rule

AIを育てるのではなく、AIが読みに来る環境を育てる。

Claudeは主役の入口だが、資産ではない。資産は `2nd-Brain/`、`agent-skills/`、Git履歴に残す。
