import argparse
import os
import shutil
import sys
from datetime import datetime

# Mocking LLM interaction for the script structure. 
# In a real agent scenario, this might call an internal API or stand-in.
# Since I (the agent) run this, I will use "step-by-step" logic:
# The script will output the prompt to be run by the agent, or 
# if this script is intended to be run BY the agent using tools, it should facilitate that.
# However, the user wants a skill "agent can use".
# Ideally, this script encapsulates the logic so the agent just runs it.
# BUT, the agent IS the one running python. 
# The standard pattern for skills is:
# 1. Script prepares prompt/context.
# 2. Script sends request to LLM (or Agent calls LLM).
#
# Given the limitations of "script running LLM" without an API key inside the script usually,
# a common pattern in this environment is:
# The script does the file handling and prints the "Prompt" for the Agent to read and execute,
# OR the Agent manually does the steps. 
# 
# HOWEVER, looking at `writer`, it uses `composer.py` to GENERATE the prompt.
# So I will follow that pattern: This script generates the PROMPT for the agent to execute.
# Wait, the user wants the SKILL to "update".
# If I make a script that just prints a prompt, the Agent (me) has to run the prompt.
#
# Let's design `updater.py` to:
# 1. Read files.
# 2. Construct a prompt for the LLM (which I, the Agent, will see and then likely run as a next step, or the script is just a helper).
# 
# Actually, the user asked for a skill "like ritsuto writer".
# The writer skill's `composer.py` prints a prompt.
# So I will make `updater.py` print the ANALYSIS PROMPT.
# Then the Agent (me) will run that prompt with `model` tool? 
# No, `writer` usage says: "run composer.py ... then execute that prompt".
# So the workflow is: User/Agent runs script -> Script outputs Prompt -> Agent reads Prompt -> Agent runs Promp -> Agent gets result -> Agent updates file.
#
# But for "context-updater", it might be better if I (the Agent) can just run one command.
# But I don't have a `python_llm_client` in the environment usually.
# So I will stick to the "Generate Prompt" pattern which is robust here.
# I will output the prompt that *I* (the agent) should use to perform the analysis.

def main():
    parser = argparse.ArgumentParser(description="Context Updater: Generates prompts to update Style or Context.")
    parser.add_argument("--mode", choices=["style", "context"], required=True, help="Mode of operation")
    parser.add_argument("--source", required=True, help="Path to the source file (new content)")
    
    args = parser.parse_args()
    
    source_path = os.path.abspath(args.source)
    if not os.path.exists(source_path):
        print(f"Error: Source file not found: {source_path}")
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_dir = os.path.join(base_dir, "resources")
    
    # Calculate Project Root (Antigravity/Brain root)
    # Structure: [Root]/.agent/skills/context-updater/[base_dir]
    project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))

    if args.mode == "style":
        target_file = os.path.join(project_root, "00_システム", "00_UserProfile", "03_執筆スタイル(Style_Guidelines).md")
        prompt_file = os.path.join(resource_dir, "prompt_style.md")
    else:
        target_file = os.path.join(project_root, "00_システム", "00_UserProfile", "02_最新コンテキスト(Active_Context).md")
        prompt_file = os.path.join(resource_dir, "prompt_context.md")

    if not os.path.exists(prompt_file):
        print(f"Error: Prompt resource not found: {prompt_file}")
        # Fallback partial prompt if file missing
        prompt_template = "Analyze {source} and update {target}."
    else:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

    # Read Source Content
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            source_content = f.read()
    except Exception as e:
        print(f"Error reading source: {e}")
        return

    # Read Target Content
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            target_content = f.read()
    except Exception as e:
        print(f"Error reading target: {e}")
        return

    # Replace placeholders
    final_prompt = prompt_template.replace("{{SOURCE_CONTENT}}", source_content).replace("{{TARGET_CONTENT}}", target_content).replace("{{TARGET_FILE_PATH}}", target_file)

    print("--- [GENERATED PROMPT] ---")
    print(final_prompt)
    print("--------------------------")
    print("\n[INSTRUCTIONS FOR AGENT]")
    print(f"1. Execute the prompt above using your reasoning model.")
    print(f"2. Review the proposed changes.")
    print(f"3. If approved, use `write_to_file` or `replace_file_content` to apply changes to: {target_file}")

if __name__ == "__main__":
    main()
