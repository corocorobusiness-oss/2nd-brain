---
name: my_writer
description: Generates content (Blog, X, Mail) Strictly adhering to My persona and writing style.
input:
  topic: (required) The topic or theme to write about.
---

# My Writer Skill (Style Injector)

**"自分"の文体を含むコンテキストを注入するスキル。**

このスキルは、あなたの価値観・トーン・語彙・リズムといった「書き方のスタイル」をAIに注入します。
**「型（構造・フォーマット）」はワークフローが決定するため、このスキルでは扱いません。**

## 責務の分離

| レイヤー | 責務 |
|---|---|
| **このスキル** | 文体（トーン、リズム、禁止ワード、語彙）、価値観 |
| **ワークフロー** | 型（構造テンプレート、媒体固有ルール） |

## When to Use (使いどころ)

- **Situation**: ワークフロー内で「自分の文体で書く」必要がある時
- **Benefit**: `00_UserProfile` の最新値を常に参照し、スタイルの一貫性を保証

## Workflow

1.  **Load Style Context**:
    - Run the style injector script to retrieve My style context.
    - Command: `python .agent/skills/my_writer/scripts/style_injector.py --topic "Your Topic"`

2.  **Write with Style**:
    - The script outputs:
      - User Profile (Master Context, Core Values, Style Guidelines)
      - Style Examples (Dynamic few-shots from `resources/style_examples`)
      - Writing Task with the topic
    - **Apply these style rules when writing.** The structure/format comes from the workflow.

## Usage Example

**In a workflow** (e.g., `note-and-gen.md`):

```markdown
1. **文体コンテキスト取得**:
   - `python .agent/skills/my_writer/scripts/style_injector.py --topic "[トピック]"` を実行
   - 出力された文体ルールを理解する

2. **型フューショット参照**:
   - `00_システム/01_Prompts/Note記事作成ワークフロー/few_shots/` 内の記事を参照
   - 構造とフォーマットを学習する

3. **執筆**:
   - 文体（スキルから）と型（フューショットから）を組み合わせて記事を執筆
```

## Files Loaded

The script automatically loads:
- `00_UserProfile/00_マスター(Master_Context).md` (if exists)
- `00_UserProfile/01_価値観(Core_Values).md`
- `00_UserProfile/03_執筆スタイル(Style_Guidelines).md`
- `resources/style_examples/*.md` (Specific style examples provided by user)

## Tips

- **Single Source of Truth**: This skill pulls directly from `00_UserProfile`, so you always use the latest persona.
