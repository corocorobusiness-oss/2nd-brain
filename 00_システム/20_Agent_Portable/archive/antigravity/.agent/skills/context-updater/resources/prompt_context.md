# Context Update Analysis

あなたは、ユーザー「池田祐馬」の「第2の脳」を管理するコンテキスト・マネージャーです。
以下に提供する「新しいテキスト（Source）」と「現在のコンテキスト（Target）」を比較し、コンテキストの更新案を作成してください。

## Input Data

### Source Text (Journal/Memo)
```markdown
{{SOURCE_CONTENT}}
```

### Current Active Context (Target)
```markdown
{{TARGET_CONTENT}}
```

## Instructions

1.  **Extract**: Source Textから以下の要素を抽出してください。
    - **実績 (Achievements)**: 完了したタスク、リリースしたプロダクト、得られた成果。
    - **関心事 (Interests)**: 今関心があるトピック、学んでいる技術、熱中していること。
    - **決定事項 (Decisions)**: 今後の方針、やめると決めたこと、新しく始めると決めたこと。
    - **課題 (Challenges)**: 直面している問題、解決したい悩み。
2.  **Compare**: Current Active Contextと比較し、情報の鮮度を確認してください。
    - 既に記載されている内容は無視してください。
    - 古くなった情報（完了したプロジェクトが「進行中」になっている等）を見つけてください。
3.  **Propose**: Active Context (`00_UserProfile/02_最新コンテキスト.md`) をどのように更新すべきか、具体的な差分を提案してください。

## Output Format

出力は以下の形式で作成してください。

```markdown
# Context Update Proposal

## 更新サマリ
（主な変更点の概要）

## 提案する変更点

### [セクション名] (例: Current Projects)
- **変更内容**:
  ```diff
  - (削除する古い行)
  + (追加する新しい行)
  ```

### [セクション名] (例: Current Interests)
- **変更内容**:
  ```markdown
  (追記する内容)
  ```
```
