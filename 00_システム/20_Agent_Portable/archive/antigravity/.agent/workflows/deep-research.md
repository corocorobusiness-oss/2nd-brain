---
description: Deep Research（自律型深層調査）を実行する
---

1. 調査したいテーマや質問を考える。
2. 以下のマスタープロンプトを読み込む。
   `.\00_システム\01_Prompts\調査\Deep_Research_Master_Prompt.md`
3. プロンプトの指示に従い、`search_web` と `browser_subagent` を駆使して調査を開始する。
4. 最終的に「Deep Research Report」を出力する。

**Command Usage:**
`/deep-research [調査したいテーマ]`
