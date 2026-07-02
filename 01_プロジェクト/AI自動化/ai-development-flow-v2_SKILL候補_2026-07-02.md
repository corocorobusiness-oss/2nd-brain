# ai-development-flow V2 SKILL.md 候補 2026-07-02

> 候補ファイル。現行 `/Users/kojinn/agent-skills/ai-development-flow/SKILL.md` にはまだ反映しない。

````markdown
---
name: ai-development-flow
description: Use when the user explicitly asks Codex to turn a conversation into a development brief, says "これ開発依頼にして", "この話を開発テンプレに落として", or "ai-development-flowに回して", or asks to run a defined mechanism, service, workflow, tool, script, skill, or AI-agent project through the user's AI development flow. Ambiguous automation requests such as "自動化したい", "仕組み化したい", or "automate this" remain consultation / automation-architect routing unless the user explicitly asks for a development brief or implementation flow. The first brief is plan-only and never permits implementation or dangerous operations.
---

# AI Development Flow

Use this skill to run software, automation, service, workflow, or skill-building requests through the user's local AI development operating model.

This is a thin entry skill. Do not duplicate the full workflow here. Treat the Obsidian files below as the source of truth.

## Source Of Truth

Read these files before planning non-trivial work:

1. `/Users/kojinn/2nd-Brain-master/01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md`
2. `/Users/kojinn/2nd-Brain-master/01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md`
3. `/Users/kojinn/2nd-Brain-master/01_プロジェクト/AI自動化/AIエージェント編成ルール_天才会議_2026-07-01.md`

The Phase -1 intake source of truth is section `2.1 AI開発依頼ヒアリング補助MVP` in file 1.

If any file is missing or appears stale, say so. Continue only for consultation or plan-only intake; do not implement, reflect source-of-truth changes, or perform dangerous operations until the source files are available and current.

## Phase -1: Plan-Only Intake

When the user explicitly asks to turn a conversation into a development request, create a short development brief before the main flow.

Immediate triggers:
- 「これ開発依頼にして」
- 「この話を開発テンプレに落として」
- 「ai-development-flowに回して」

Ambiguous automation wording such as 「自動化したい」 or 「仕組み化したい」 should first stay on the `automation-architect` consultation route. Ask once whether to keep consulting or turn it into a development brief for `ai-development-flow`.

The intake brief must:
- compress the conversation into a brief
- ask only decision-critical questions
- keep unknowns as `未確認`
- split unknowns into `ブロッカー / 後で確認 / 対象外`
- preserve field evidence states: `ユーザー確認済み / AI要約・最終確認待ち / 未確認 / 対象外`
- surface dangerous trigger candidates
- end with `handoff_mode: plan_only（設計まで。実装・書き込みなし）`

Do not infer safety items. Do not treat this intake as classification, Goal fixing, implementation permission, or dangerous-operation approval.

After the user approves the brief, respond:

```text
受け取った承認: 依頼文承認のみ
今回承認された実装開始: なし
今回承認された危険操作: なし
危険トリガー候補: あり（具体名）/ なし / 未確認
次に出すもの: 案件分類、Goal、設計、実装計画
```

Then run only classification, Goal fixing, design, and implementation planning. If `handoff_mode: plan_only` is present, do not implement even when the work looks light and safe. Stop before implementation unless a separate implementation-start approval is given.

## Operating Rules

Start by classifying the request:

- `軽い`: typo fixes, small display changes, one-off note cleanup.
- `通常`: small features, simple scripts, improvements to existing processing.
- `重要`: long-lived mechanisms, repeated automation, business workflow changes, reusable skills.
- `危険`: accounting, authentication, external posting/sending, deletion, scheduled/background jobs, source-of-truth rules, personal/secret data, production writes, or double-run damage.

Use the lightest workflow that fits the risk. Do not run a heavy multi-agent process for every small task.

For normal or higher-risk work, establish a one-sentence goal before implementation. The goal should state what successful completion means, not just what to build. For important or dangerous work, this goal is mandatory, and goal changes require a reason, impact check, and approval decision.

## Approval Boundaries

Keep these approvals separate:

1. `依頼文承認`: approve sending the plan-only brief into the main flow. This never allows implementation, production writes, external sending, deletion, automation enablement, or source-of-truth rule changes.
2. `実装開始承認`: approve implementation after design, allowed paths, disallowed paths, verification, and rollback are shown.
3. `危険操作承認`: approve one specific dangerous operation.

Valid implementation-start approval should identify:

```text
実装開始承認:
対象範囲:
触ってよい場所:
触ってはいけない場所:
検証方法:
戻し方:
危険操作は含まない: YESのみ有効（NOの場合、危険操作は別途「危険操作承認」が必要）
```

`OK`, `いいよ`, or `承認` alone never counts as dangerous-operation approval.

Valid dangerous-operation approval must identify:

```text
危険操作承認:
承認者:
承認日時:
対象操作:
対象ファイル/対象サービス:
差分:
影響範囲:
戻し方:
実行タイミング:
二重実行防止:
```

If any required item is missing, the dangerous-operation approval is invalid.

If the approval text is ambiguous, treat it as the least-powerful approval that fits the immediate prompt.

## Required First Output

Before implementation, produce:

1. 案件分類 and reason.
2. Required agent/review setup.
3. One-sentence goal and completion conditions.
4. Non-goals.
5. Research scope and stopping condition.
6. Main risks and stop conditions.
7. Implementation plan.
8. Verification evidence to collect.

If the work is clearly light and safe, keep this short and proceed. This does not apply to `handoff_mode: plan_only`; plan-only always stops before implementation.

## Step Execution Policy

Do not allocate maximum time or many agents by default.

- Start with a small first pass.
- Deepen only when unresolved uncertainty affects the decision.
- Use separate QA/review/completion judgment for important work.
- Require human approval before dangerous operations.

For research, start with a short first pass. Continue deeper only when decision-critical gaps remain.

For implementation failures, run bounded repair loops only:

- Record the loop count, failed evidence, change made, command, exit code, retest result, and next hypothesis.
- If the same failure repeats twice, pause for root-cause analysis before continuing.
- Stop after 3 failed cycles for the same failure/test/target and report `未完成` or `要確認`.
- Never loop dangerous operations that require human approval.

## Completion Gate

Do not mark the task complete when any applicable item remains:

- missing evidence
- unrun verification
- unknown exit code
- unresolved FAIL
- unexplained WARN
- unconfirmed requirement
- missing independent review for important/dangerous work
- unresolved major review finding
- missing human approval for dangerous work
- possible secret/personal-data leakage

Report incomplete work as `未完成` or `要確認`, not as done.

## External AI Rule

Use external agents mainly for independent review, contradiction, and risk checks, not as trusted implementers.

Before sending anything externally, remove secrets, tokens, cookies, raw logs, unmasked personal data, unmasked API responses, and authenticated URLs. If decontamination is not confirmed, the review is invalid.

## First Real-Use Review

When this skill is used as the first real case for the new AI development flow, record:

- stuck points
- parts that were too heavy
- parts that were too light
- missed items
- improvements for the template or skill

Store durable process changes in the Obsidian source files, not only in this skill.
````
