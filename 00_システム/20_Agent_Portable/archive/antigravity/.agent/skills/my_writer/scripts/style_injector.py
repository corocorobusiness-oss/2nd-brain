"""
My Writer Style Injector

Outputs the pure "style context" for My Writer.
This loads the latest User Profile (Values, Style) and Style Examples dynamically.

Usage:
    python style_injector.py --topic "Your Topic"
"""

import argparse
import os
import glob

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
STYLE_EXAMPLES_DIR = os.path.join(RESOURCES_DIR, "style_examples")

# User Profile Path (Relative path to maintain portability)
# 2nd-Brain/.agent/skills/my_writer/scripts/ -> 2nd-Brain/00_システム/00_UserProfile
USER_PROFILE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../00_システム/00_UserProfile"))


def read_file(path):
    """Reads a file and returns its content."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"[File not found: {path}]"
    except Exception as e:
        return f"[Error reading {path}: {e}]"


def load_user_profile():
    """Loads core style files from the user profile."""
    profile_content = "# User Profile Context (Dynamic Load)\n\n"
    
    files_to_load = [
        "01_価値観(Core_Values).md",
        "03_執筆スタイル(Style_Guidelines).md"
    ]
    
    # Try to load Master Context if available, else skip
    master_path = os.path.join(USER_PROFILE_DIR, "00_マスター(Master_Context).md")
    if os.path.exists(master_path):
        files_to_load.insert(0, "00_マスター(Master_Context).md")

    for filename in files_to_load:
        path = os.path.join(USER_PROFILE_DIR, filename)
        content = read_file(path)
        profile_content += f"## From {filename}\n{content}\n\n"
        
    return profile_content


def load_style_examples():
    """Loads all style examples from the style_examples directory."""
    examples_content = "# Style Examples (Few-Shots for Style Mimicry)\n\n"
    examples_content += "Use these examples to understand the writing STYLE (tone, rhythm, word choice). \n"
    examples_content += "Do NOT copy the specific topic content, only the STYLE.\n\n"
    
    if not os.path.exists(STYLE_EXAMPLES_DIR):
        examples_content += "[No style examples directory found]\n"
        return examples_content
    
    md_files = glob.glob(os.path.join(STYLE_EXAMPLES_DIR, "*.md"))
    
    if not md_files:
        examples_content += "No specific style examples found in resources/style_examples.\n"
        examples_content += "Refer to the Style Guidelines above.\n"
        return examples_content
    
    for filepath in md_files:
        filename = os.path.basename(filepath)
        content = read_file(filepath)
        examples_content += f"## Example: {filename}\n{content}\n\n---\n\n"
    
    return examples_content


def main():
    parser = argparse.ArgumentParser(
        description="My Writer Style Injector - Outputs style context for writing"
    )
    parser.add_argument(
        "--topic", 
        required=True, 
        help="The topic to write about"
    )
    
    args = parser.parse_args()
    
    # 1. Load User Profile (Style Rules)
    user_profile = load_user_profile()
    
    # 2. Load Style Examples (Few-Shots)
    style_examples = load_style_examples()
    
    # 3. Assemble Final Output
    final_output = f"""
{user_profile}

{style_examples}

---

# Writing Task

**Topic**: {args.topic}

**Instructions**:
1. Write strictly in the style defined above.
2. Adhere to the 'Vertical Rhythm' and Tone rules found in the User Profile.
3. Use the Vocabulary and Sentence structures seen in the Examples.
4. The STRUCTURE/FORMAT (e.g. valid markdown for Note/X) is determined by the specific workflow or template you are using.
"""
    
    print(final_output)


if __name__ == "__main__":
    main()
