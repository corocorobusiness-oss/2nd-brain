# Codex skills use agent-skills as source of truth

Date: 2026-07-02
Status: ready_for_human_approved_apply

## Goal

Use `/Users/kojinn/agent-skills` as the only source of truth for custom skills, while keeping Codex built-in `.system` skills intact.

## Current Problem

- `/Users/kojinn/.claude/skills` is already a symlink to `/Users/kojinn/agent-skills`.
- `/Users/kojinn/.codex/skills/ai-development-flow` is already a symlink.
- The other custom Codex skills are copied directories, so updates to `/Users/kojinn/agent-skills` do not automatically flow into Codex.

## Target Layout

```text
/Users/kojinn/agent-skills
  <custom-skill>/...

/Users/kojinn/.claude/skills
  -> /Users/kojinn/agent-skills

/Users/kojinn/.codex/skills/.system
  kept as Codex built-in skills

/Users/kojinn/.codex/skills/<custom-skill>
  -> /Users/kojinn/agent-skills/<custom-skill>
```

## Migration Script

Script:

```text
00_システム/20_Agent_Portable/scripts/codex_skills_use_agent_skills.sh
```

Dry-run:

```bash
/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/codex_skills_use_agent_skills.sh --dry-run
```

Apply after human approval:

```bash
/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/codex_skills_use_agent_skills.sh --apply
```

Verify:

```bash
/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/codex_skills_use_agent_skills.sh --verify
```

## Safety Design

- Default mode is dry-run.
- `.system` is preserved.
- `.git` under `agent-skills` is ignored.
- A directory is treated as a skill only when it has `SKILL.md`.
- Existing copied Codex skill directories are moved to a timestamped backup before symlinks are created.
- Rollback can restore the backup directory.

Rollback:

```bash
/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/codex_skills_use_agent_skills.sh --rollback /Users/kojinn/.codex/skills/.backup-agent-skills-symlink/<timestamp> --apply
```

## Completion Evidence

Before apply, current verify is expected to fail for copied directories:

```text
SUMMARY total=21 failures=20
```

After apply, expected verify:

```text
SUMMARY total=21 failures=0
```

Codex Desktop may need a new chat or app restart before the available skill list refreshes.

## Test Evidence

Local syntax check:

```bash
bash -n 00_システム/20_Agent_Portable/scripts/codex_skills_use_agent_skills.sh
```

Result: exit 0.

Fixture test in `/private/tmp`:

```text
FIXTURE_PASS /private/tmp/codex-skill-link-test.04M1ZL
SUMMARY total=2 failures=0
SUMMARY total=2 failures=0
ROLLBACK_DONE mode=apply backup=/private/tmp/codex-skill-link-test.04M1ZL/codex/.backup/20260702-060916
```

Current real environment verify before human-approved apply:

```text
PASS ai-development-flow -> /Users/kojinn/agent-skills/ai-development-flow
SUMMARY total=21 failures=20
```

This is expected because 20 Codex custom skills are still copied directories.
