---
name: prompt_engineer
description: Helps the user create high-quality, structured prompts for LLMs using the "Master Prompt Generation Pipeline" (Interview -> Architect -> Auditor -> Simulation Loop -> Gatekeeper).
---

# Prompt Engineer Skill (Ultimate Edition)

This skill allows the agent to orchestrate the **"Master Prompt Generation Pipeline"**. It is identical to the `/generate-master-prompt` workflow but executed interactively.

## Usage

User requests:
- "Create a prompt for writing a marketing email."
- "I need a prompt to act as a Python coding assistant."
- "Help me design a system prompt for my new agent."

## Workflow

Follow these steps sequentially. You must **READ the specified system prompt file** for each step.

### Step 1: The Interview (Phase 1)

**Action**:
1.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/01_Prompts\プロンプト生成/01_interviewer.md`
2.  **Act**: Adopt the **Interviewer** persona.
3.  **Goal**: Define the "6 Core Variables". Confirm with the user when complete.

### Step 2: Design & Initial Audit (Phase 2)

**Action**:
1.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/.agent/skills/prompt_engineer/resources/examples.md`
    - **Goal**: Understand the "Gold Standard" quality and structure (Few-Shot Learning).
2.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/01_Prompts\プロンプト生成/02_architect.md`
    - Create **Draft Prompt**.
3.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/01_Prompts\プロンプト生成/03_auditor.md`
    - Create **Audit Report**.

### Step 3: Self-Correction Loop (The "Master" Logic)

**Action**:
If the Audit Rank is NOT "S", enter the loop (Max 3 iterations for interactive speed).

1.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/01_Prompts\プロンプト生成/04_Prompt Refiner.md`
    - **Act**: Refine the prompt based on the previous audit/feedback.
2.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/01_Prompts\プロンプト生成/05_Simulation Runner.md`
    - **Act**: Simulate 3 test cases (Standard, Missing Info, Stress).
3.  **Read File**: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/00_システム/01_Prompts\プロンプト生成/06_Quality Gatekeeper.md`
    - **Act**: Decide GO / NO-GO based on simulation logs.
    - If **NO-GO**: Repeat Step 3.1 with new feedback.
    - If **GO**: Proceed to Step 4.

### Step 4: Final Handover

**Action**:
- Present the **Final Master Prompt** to the user.
- Highlight any remaining edge cases or warnings from the Gatekeeper.

---
**Note**: This is a resource-intensive process. Inform the user you are "Entering the simulation loop" so they know you are thinking deeply.
