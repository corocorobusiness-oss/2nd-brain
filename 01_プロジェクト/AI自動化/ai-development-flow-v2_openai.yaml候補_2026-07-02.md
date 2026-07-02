# ai-development-flow V2 agents/openai.yaml 候補 2026-07-02

> 候補ファイル。現行 `/Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml` にはまだ反映しない。

```yaml
interface:
  display_name: "AI Development Flow"
  short_description: "Risk-based AI development flow with plan-only intake"
  default_prompt: "Use $ai-development-flow to turn explicit requests for a development brief into a plan-only brief, then run risk classification, fixed goal, bounded repair loops, evidence gates, independent review, and completion checks. Ambiguous automation requests remain consultation unless the user explicitly asks for a development brief or implementation flow. Plan-only approval never permits implementation, production writes, external sending, deletion, automation enablement, or dangerous operations."
```
