# ai-development-flow V2 reflect 20260702-112042

## 目的

`ai-development-flow` の現行入口へ、Vault内のV2候補本文を反映した証跡。

この記録はV2反映の記録であり、V2正式採用・5回試用完了・外部送信・自動化ONの記録ではない。

## 承認

```text
危険操作承認:
承認者: 池田祐馬
承認日時: 2026-07-02
対象操作: ai-development-flow の現行入口へV2候補を反映し、hash一致とsymlink維持を確認する
対象ファイル/対象サービス: /Users/kojinn/agent-skills/ai-development-flow/SKILL.md, /Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml
差分: Vault内のV2候補本文を抽出し、現行SKILL.mdとagents/openai.yamlへ反映する。V2正式採用・5回試用完了・外部送信・自動化ONはしない
影響範囲: ai-development-flow の入口挙動。会話から開発依頼ブリーフを作るplan-only受付が追加される
戻し方: /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/ のSKILL.mdとagents/openai.yamlを現行へ戻す
実行タイミング: 承認後すぐ
二重実行防止: 反映前に候補本文hashを固定し、反映後hashと一致確認する。既にV2反映済みなら上書き実行しない
```

## V1退避

V2反映前に、V1退避hash PASSを人間確認済み。

```text
V1退避先: /Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/
V1 snapshot: 01_プロジェクト/AI自動化/ai-development-flow-v2-v1-snapshot_20260702-110614.md
```

## 候補本文hash

候補Markdownの説明文ではなく、最外周コードフェンス内だけを抽出した本文hash。

```text
3232b68b511a6a1d6fc6446943a6459f505dc0f1c21325ec4abed251f58104a8  /tmp/ai-development-flow-v2-reflect-20260702-approval/SKILL.md
07de9f9ceff398dc8bb9d493274889a4d3ef28bb075e7af282e75b220d0c2a8d  /tmp/ai-development-flow-v2-reflect-20260702-approval/openai.yaml
```

## 反映後hash

```text
3232b68b511a6a1d6fc6446943a6459f505dc0f1c21325ec4abed251f58104a8  /Users/kojinn/agent-skills/ai-development-flow/SKILL.md
07de9f9ceff398dc8bb9d493274889a4d3ef28bb075e7af282e75b220d0c2a8d  /Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml
```

判定:

```text
候補本文hash一致: PASS
V2固有文言確認: PASS
```

確認したV2固有文言:
- `Phase -1: Plan-Only Intake`
- `handoff_mode: plan_only（設計まで。実装・書き込みなし）`
- `Ambiguous automation wording`
- `今回承認された実装開始: なし`
- `危険操作は含まない: YESのみ有効`

## symlink

```text
/Users/kojinn/.codex/skills/ai-development-flow -> /Users/kojinn/agent-skills/ai-development-flow
SYMLINK_OK
```

## 現時点

```text
V2反映済み
runtime / dry-run gate待ち
V2試用開始: 未実施
V2正式採用: 未実施
外部送信: 未実施
自動化ON: 未実施
```

次に進むには、runtime / dry-run gate を通す。
