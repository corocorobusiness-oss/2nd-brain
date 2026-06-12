---
name: context-updater
description: Explicitly learns style nuances and updates user context from specified sources (Opt-in only).
input:
  mode: (required) "style" or "context"
  source: (required) Path to the source file to learn from.
---

# Context Updater Skill

ユーザー（池田祐馬）の「文体（Style）」と「コンテキスト（Context）」を、**ユーザーの指示に基づいて明示的に更新する**スキルです。
勝手な学習は行わず、ユーザーが「これを手本にせよ」「これを記録せよ」と指定したファイルのみを解析対象とします。

## Usage

### Command

```bash
# 文体を学習して更新提案を受ける
python .agent/skills/context-updater/scripts/updater.py --mode style --source "path/to/ideal_article.md"

# 状況（コンテキスト）を更新提案を受ける
python .agent/skills/context-updater/scripts/updater.py --mode context --source "path/to/daily_log.md"
```

### Modes

- **`style`**:
  - 指定されたテキスト（完了稿など）を分析し、現在の `Style_Guidelines.md` との差分を抽出します。
  - 新しい「書き癖」や「好みの表現」が見つかった場合、ガイドラインへの追加・修正を提案します。
  
- **`context`**:
  - 指定されたテキスト（日誌、メモなど）を分析し、`Active_Context.md` (現状) と比較します。
  - プロジェクトの完了、新しい関心事、実績などを抽出し、コンテキストの更新を提案します。

## Workflow

1.  **Backup**: 対象ファイル（Style Guide or Active Context）のバックアップを一時作成します。
2.  **Analyze**: LLMがソースファイルと現状ファイルを比較分析します。
3.  **Propose**: 「以下の変更を行いますか？」とユーザーに確認を求めます（Console出力）。
4.  **Update**: ユーザーが承認した場合のみ、ファイルを上書き更新します。
