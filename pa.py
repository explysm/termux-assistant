import requests
import subprocess
import sys
import os
import re

# --- CONFIGURATION ---
MODEL_NAME = "android-1b"
OLLAMA_URL = "http://localhost:11434/api/generate"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
session = requests.Session()

def load_extra_config():
    """Reads settings.conf and extra.md if 'extra=yes' is set."""
    config_path = os.path.join(BASE_DIR, "settings.conf")
    extra_path = os.path.join(BASE_DIR, "extra.md")
    extra_context = ""

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_data = f.read().lower()
            if "extra=yes" in config_data:
                if os.path.exists(extra_path):
                    with open(extra_path, "r") as ef:
                        extra_context = ef.read().strip()
                        print("\033[90m[Config: Extra context loaded from extra.md]\033[0m")
    return extra_context

def sanitize_command(cmd):
    """Strips markdown, handles scaling, and fixes 1B model hallucinations."""
    # 1. Remove markdown backticks and code blocks
    cmd = re.sub(r'```[a-z]*', '', cmd)
    cmd = cmd.replace('```', '').replace('`', '').strip()

    # 2. Cut off rambling (Stop phrases)
    stop_phrases = ["user request:", "output:", "user:", "assistant:", "\n"]
    cmd_lower = cmd.lower()
    for phrase in stop_phrases:
        if phrase in cmd_lower:
            cmd = cmd[:cmd_lower.find(phrase)]
            break
    
    cmd = cmd.strip()

    # 3. Spelling & Syntax Auto-Corrections
    typo_map = {
        "termuxvolume": "termux-volume",
        "termuxolume": "termux-volume",
        "termuxbright": "termux-brightness",
        "termuxvibrate": "termux-vibrate"
    }
    for typo, fix in typo_map.items():
        cmd = cmd.replace(typo, fix)

    # 4. Smart Volume Scaling (0-100% logic)
    if "termux-volume" in cmd:
        nums = re.findall(r'\d+', cmd)
        for n in nums:
            val = int(n)
            # If AI outputs a percentage (like 8 or 100), scale it to 0-15
            if val > 15 or "%" in cmd:
                new_val = 15 if val >= 95 else max(0, round((val / 100) * 15))
                cmd = cmd.replace(n, str(new_val), 1)
        
        # Ensure audio stream is specified (default to music)
        if not any(s in cmd for s in ["music", "alarm", "ring", "system", "notification"]):
            cmd = cmd.replace("termux-volume", "termux-volume music")

    return cmd.strip()

def get_ai_command(user_input, extra_context):
    """Sends the request to Ollama with the combined context."""
    full_prompt = f"""REFERENCE DATA:
{extra_context}

TASK: Convert the following request into a raw Termux command. Output ONLY the command.
USER REQUEST: {user_input}
COMMAND:"""

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "keep_alive": "1h", # Model stays in RAM
        "options": {
            "temperature": 0.0,
            "num_predict": 50,
            "stop": ["USER REQUEST:", "COMMAND:", "\n", "User:"]
        }
    }

    try:
        # 30s timeout handles the slow disk-to-RAM load on mobile
        response = session.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        raw_response = response.json().get("response", "").strip()
        return sanitize_command(raw_response)
    except Exception as e:
        return f"ERROR: {e}"

def main():
    extra_context = load_extra_config()
    print("\033[96mAndroid AI Controller Active. (Ctrl+D to exit)\033[0m")
    
    while True:
        try:
            user_query = input("\033[92m> \033[0m")
            if not user_query.strip():
                continue
            
            command = get_ai_command(user_query, extra_context)
            
            if "termux-" in command and "error" not in command.lower():
                print(f"\033[94mExecuting:\033[0m {command}")
                subprocess.run(command, shell=True)
            else:
                # If the AI responded with text or an error instead of a command
                print(f"\033[93mAI Response:\033[0m {command}")
                
        except (EOFError, KeyboardInterrupt):
            print("\n\033[91mShutting down assistant...\033[0m")
            break

if __name__ == "__main__":
    main()

