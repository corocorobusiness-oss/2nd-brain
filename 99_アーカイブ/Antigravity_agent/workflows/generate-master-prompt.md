---
description: Automated Prompt Generation Pipeline (Interviewer -> Architect -> Auditor -> Refiner Loop -> Gatekeeper)
---

# Master Prompt Generation Workflow

Run this workflow to generate high-quality prompts using the "6-Agent System". This workflow uses a Human-in-the-Loop approach: interactive at the start, autonomous in the middle (with a refinement loop), and human confirmation at the end.

## Phase 1: Interview & Requirements (Interactive)
1. **Read Prompt**: Read `.\00_システム\01_Prompts\プロンプト生成\01_interviewer.md`.
2. **Conduct Interview**: Act as the "Requirements Specialist" defined in the prompt.
   - Ask the user what they want to build.
   - deeply explore the requirements (Goal, Persona, Input, Constraints, Scenario).
   - Continue until you have a complete specification.
3. **Save Output**: When the interview is complete, output the "Prompt Specification Document" and save it as an artifact named `01_requirements.md` in the current artifact directory.

## Phase 2: Design & Initial Audit (Auto-Pilot)
4. **Drafting**:
   - Read `.\00_システム\01_Prompts\プロンプト生成\02_architect.md`.
   - Read the created `01_requirements.md`.
   - Act as the "Master Prompt Architect" to generate the initial structured prompt.
   - Save the result as `02_draft_prompt.md`.
5. **Auditing**:
   - Read `.\00_システム\01_Prompts\プロンプト生成\03_auditor.md`.
   - Read `02_draft_prompt.md`.
   - Act as the "Lead Prompt Auditor" to grade the prompt (Rank S/A/B/C) and list issues.
   - Save the report as `03_audit_report.md`.

## Phase 3: Refinement Loop (Auto-Pilot / Max 5 Cycles)
6. **Autonomous Refinement**:
   - Check `03_audit_report.md`. If Rank is "S" and perfect, skip to Phase 4.
   - If not perfect, enter a **Refinement Loop** (maximum 5 iterations).
   - **For each iteration (N=1 to 5):**
     1. **Refine**: Run `.\00_システム\01_Prompts\プロンプト生成\04_Prompt Refiner.md`. Input the latest prompt and the latest audit/gatekeeper report. Save output as `04_refined_prompt_v{N}.md`.
     2. **Simulate**: Run `.\00_システム\01_Prompts\プロンプト生成\05_Simulation Runner.md`. Load `04_refined_prompt_v{N}.md` and generating 3 test cases (Golden Path, Ambiguity Trap, Stress Test). Record the INPUTS and OUTPUS. Save as `05_simulation_log_v{N}.md`.
     3. **Gatekeep (Zero Tolerance Assessment)**: 
        - Run `.\00_システム\01_Prompts\プロンプト生成\06_Quality Gatekeeper.md`.
        - **Input 1**: `04_refined_prompt_v{N}.md` (Target Prompt).
        - **Input 2**: `05_simulation_log_v{N}.md` (Simulation Log).
        - **Action**: Act as the "Lead Quality Assurance Director". Strictly audit the results against the 4 criteria. **Do not approve unless 100% perfect.**
        - Save report as `06_gatekeeper_report_v{N}.md`.
     4. **Check Decision**:
        - If **APPROVE**: Stop loop. Define `Final_Master_Prompt.md` as the content of `04_refined_prompt_v{N}.md`. Proceed to Phase 4.
        - If **REJECT**: Increment N. Use the feedback in `06_gatekeeper_report_v{N}.md` as input for the next Refinement step.
        - If N reaches 5: Stop loop. Use the last refined prompt as the tentative final result.

## Phase 4: Final Handover
7. **Final Presentation**:
   - Present the `Final_Master_Prompt.md` (or the latest v5) to the user.
   - If the loop reached 5 iterations without approval, explicitly warn the user and summarize the remaining issues from the last Gatekeeper report.
   - Ask for user confirmation.

