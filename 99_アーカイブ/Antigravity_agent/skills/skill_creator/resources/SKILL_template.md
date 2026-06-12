---
name: {{skill_name_kebab_case}}
description: {{description_english_3rd_person}}
input:
  input_variable: (required/optional) Description of input
---

# {{Skill Name Title}}

{{japanese_description_of_purpose}}

## When to use this skill (使いどころ)
- **Situation**: {{situation_description}} (例: ～したい時)
- **Benefit**: {{benefit_description}} (例: ～が楽になる)

## Workflow
1.  **Usage Check**:
    - **Crucial**: If using a script, ALWAYS run it with `--help` first to understand arguments without reading source code.
    - Example: `python scripts/my_script.py --help`
2.  **Step 1**: {{action_verb}} ...
3.  **Step 2**: {{action_verb}} ...

## Usage Instructions
### User Request Example
> "{{example_trigger_phrase}}"

### Execution Steps (Agent)
1.  **Preparation**:
    - Check inputs...
2.  **Execution**:
    - Run script `scripts/{{script_name}}`...
    - Or use prompt `prompts/{{prompt_name}}`...
3.  **Report**:
    - Show results to user...

## Tips
- **Best Practice**: {{tip_content}}
