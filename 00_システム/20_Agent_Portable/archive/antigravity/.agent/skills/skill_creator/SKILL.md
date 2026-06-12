---
name: skill_creator
description: Interactive tool to design and scaffold new Agent Skills adhering to official structure. Use when the user wants to teach the agent a new capability.
input:
  request: (required) Description of the desired skill or capability.
---

# Skill Creator (Meta-Skill)

ユーザーの要望に基づいて、新しい「エージェントスキル」を設計し、必要なファイル構造（`SKILL.md`, `scripts/`, `prompts/`）を生成するメタスキルです。
公式ガイドラインの **Best Practices**（単一機能、明確な説明、構成の分離）を遵守したスキルを作成します。

## Workflow

### 1. Discovery & Design (ヒアリングと設計)
**重要**: まず最初に `resources/official_guidelines.md` を読み込み、最新のGoogle公式スキル標準（フォルダ構造、ベストプラクティス）を理解してください。
ユーザーの要望（`request`）を分析し、以下の要件を定義します。
- **Skill Name**: 英小文字・ケバブケース (例: `data-analyzer`)。
- **Description**: エージェントが認識するための「3人称・現在形」の英語説明文 (例: "Analyzes CSV files and generates report.")。
    - *Tip*: エージェントはこの文章を見てスキルを使うか決めるため、具体的かつ明確なキーワードを入れること。
- **Scope**: 何をして、何をしないか（単一責任の原則）。
- **Structure**: `official_guidelines.md` の "Skill folder structure" セクションに従い、必要なサブフォルダ (`scripts/`, `examples/`, `resources/`) を決定する。
    - *Note*: `prompts/` フォルダは公式ガイドには明記されていないため、プロンプトファイル等は `resources/` に配置することを推奨する。
- **Checking**: 指示で不足してる部分があれば、ステップバイステップでユーザーに一問一答で確認してから作成すること。
    
### 2. Scaffolding (生成)
定義に基づき、以下のコマンドを実行してスキルを作成します。

1.  **Create Directory**: `.agent/skills/<skill-name>` フォルダを作成。
2.  **Create Resources**: `scripts/`, `resources/`, `examples/` など、ガイドラインに準拠したフォルダを作成。
    - *Note*: プロンプトファイルは `resources/` 内に配置すること。
3.  **Generate SKILL.md**:
    - `resources/SKILL_template.md` を読み込み、内容を埋めて `SKILL.md` を作成する。
    - *重要*: `description` (フロントマター) は必ず **英語** で記述すること。

### 3. Review (確認)
作成したスキルのパスと概要をユーザーに報告し、使い方の例（User Request Example）を提示する。

## Usage Instructions

### User Request Example
> "YouTubeの動画を要約するスキルを作って"
> "新しいスキルを追加したい。名前は `git-manager` で。"

### Execution Steps (Agent)

1.  **Analyze Request**: ユーザーの意図を汲み取り、スキルの仕様を策定する（必要なら質問する）。
2.  **Create Files**: `write_to_file` ツールで `.agent/skills/<name>/SKILL.md` 等を作成する。
    - テンプレート: `.agent/skills/skill_creator/resources/SKILL_template.md` を参照。
3.  **Finalize**: 「スキルを作成しました。次からは『～して』と言うだけで実行できます」と伝える。

## Best Practices for Created Skills
作成するスキルには、以下の基準を適用してください。
- **Keep it Focused**: 1つのスキルがカバーするのは1つのドメインのみ。
- **Clear Inputs**: ユーザーから何を受け取るか（ファイルパス、URL、テキストなど）を明記する。
- **Safe Execution**: スクリプトを含む場合、`--help` での確認や、破壊的変更への警告を含めるよう指示する。
- **Use Scripts as Black Boxes**: エージェントがソースコードを読まずに済むよう、必ず `argparse` でヘルプを実装し、ワークフローの最初に `--help` を実行させる。
