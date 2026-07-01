---
name: ai-development-flow
description: Use when the user asks Codex to build, design, automate, or improve a mechanism, service, workflow, tool, script, or AI-agent system, especially when they say "仕組みを作る", "開発して", "自動化して", "スキル化して", "ちゃんと設計して", or want development to proceed from planning through implementation, verification, maintenance, and completion judgment. This skill routes the work through the user's Obsidian source-of-truth AI development flow with risk classification, evidence gates, independent review, and human approval for dangerous operations.
---

# AI Development Flow

Use this skill to run software, automation, service, workflow, or skill-building requests through the user's local AI development operating model.

This is a thin entry skill. Do not duplicate the full workflow here. Treat the Obsidian files below as the source of truth.

## Source Of Truth

Read these files before planning non-trivial work:

1. `/Users/kojinn/2nd-Brain-master/01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md`
2. `/Users/kojinn/2nd-Brain-master/01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md`
3. `/Users/kojinn/2nd-Brain-master/01_プロジェクト/AI自動化/AIエージェント編成ルール_天才会議_2026-07-01.md`

If any file is missing or appears stale, say so and continue with the available files.

## Operating Rules

Start by classifying the request:

- `軽い`: typo fixes, small display changes, one-off note cleanup.
- `通常`: small features, simple scripts, improvements to existing processing.
- `重要`: long-lived mechanisms, repeated automation, business workflow changes, reusable skills.
- `危険`: accounting, authentication, external posting/sending, deletion, scheduled/background jobs, source-of-truth rules, personal/secret data, production writes, or double-run damage.

Use the lightest workflow that fits the risk. Do not run a heavy multi-agent process for every small task.

For normal or higher-risk work, establish a one-sentence goal before implementation. The goal should state what successful completion means, not just what to build. For important or dangerous work, this goal is mandatory, and goal changes require a reason, impact check, and approval decision.

Use repair loops only as bounded fix-test cycles. One cycle is: implement or fix, test, inspect failure evidence, and record the next hypothesis. Stop after 3 cycles for the same failure/test/target and report `未完成` or `要確認` if it still does not pass. Do not use loops to bypass human approval, independent review, or dangerous-operation gates.

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

If the work is clearly light and safe, keep this short and proceed.

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
