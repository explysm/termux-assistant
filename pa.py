import threading
import json
import time
import requests
import subprocess

# Function to display a real-time timer
def timer_display(stop_event, start_time):
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        sys.stdout.write(f"\r\033[90mGenerating response... {elapsed:.1f}s\033[0m")
        sys.stdout.flush()
        time.sleep(0.1)
    # Print the final time after the loop exits, to ensure it's on a new line
    elapsed = time.time() - start_time
    sys.stdout.write(f"\r\033[90mResponse generated in {elapsed:.2f}s\033[0m\n")
    sys.stdout.flush()

# Helper for colored output
def _print_message(message, msg_type="info", end='\n', flush=False):
    colors = {
        "info": "\033[0m",         # Reset / Default
        "system": "\033[96m",      # Cyan
        "prompt": "\033[92m",      # Green
        "executing": "\033[94m",   # Blue
        "ai_response": "\033[93m", # Yellow
        "error": "\033[91m",       # Red
        "warning": "\033[93m",     # Yellow (same as AI response for now)
        "timer": "\033[90m",       # Dark Grey
        "bold": "\033[1m",         # Bold
        "reset": "\033[0m"         # Reset
    }
    
    prefix = ""
    suffix = colors["reset"]
    
    if msg_type in colors:
        prefix = colors[msg_type]
    
    # Special handling for timer, which might use \r
    if msg_type == "timer":
        sys.stdout.write(f"{prefix}{message}{suffix}{end}")
    else:
        sys.stdout.write(f"{prefix}{message}{suffix}{end}")
    
    if flush:
        sys.stdout.flush()

# --- CONFIGURATION ---
import sys
import os
import re

# --- CONFIGURATION ---
MODEL_NAME = "android-1b"
OLLAMA_URL = "http://localhost:11434/api/generate"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
session = requests.Session()

def is_ollama_running():
    try:
        # Ollama's API usually responds to a GET request on its base URL when running
        response = session.get(OLLAMA_URL.replace("/api/generate", ""), timeout=1)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False

def start_ollama_background():
    _print_message("Attempting to start Ollama in the background...", msg_type="system")
    try:
        # Use subprocess.Popen with preexec_fn for detaching on Unix-like systems
        # On Termux, 'nohup' might be more robust with '&'
        subprocess.Popen("nohup ollama serve &", shell=True, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         preexec_fn=os.setpgrp # Detach from current process group
                        )
        _print_message("Ollama start command issued. Waiting for it to become ready...", msg_type="system")
        return True
    except Exception as e:
        _print_message(f"ERROR: Could not start Ollama: {e}", msg_type="error")
        return False

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
                        _print_message("[Config: Extra context loaded from extra.md]", msg_type="system")
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
        "stream": True,
        "keep_alive": "1h", # Model stays in RAM
        "options": {
            "temperature": 0.0,
            "num_predict": 50,
            "stop": ["USER REQUEST:", "COMMAND:", "\n", "User:"]
        }
    }

    try:
        # 30s timeout handles the slow disk-to-RAM load on mobile
        response = session.post(OLLAMA_URL, json=payload, timeout=30, stream=True)
        response.raise_for_status()

        full_response_content = ""
        for chunk in response.iter_lines():
            if chunk:
                decoded_chunk = chunk.decode('utf-8')
                try:
                    json_data = json.loads(decoded_chunk)
                    content = json_data.get("response")
                    if content:
                        full_response_content += content
                        yield content
                except json.JSONDecodeError:
                    # Handle cases where a chunk might not be a complete JSON object
                    pass
        # After streaming, sanitize the full response and yield it as the final command
        final_command = sanitize_command(full_response_content)
        yield {"final_command": final_command} # Indicate the final command
    except Exception as e:
        yield {"error": f"ERROR: {e}"}

def main():
    extra_context = load_extra_config()

    # Check and start Ollama if not running
    if not is_ollama_running():
        start_ollama_background()
        ollama_ready = False
        for _ in range(30):  # Wait up to 30 seconds for Ollama to start
            if is_ollama_running():
                ollama_ready = True
                _print_message("Ollama is now running!", msg_type="system")
                break
            _print_message(".", msg_type="timer", end='', flush=True)
            time.sleep(1)
        if not ollama_ready:
            _print_message("ERROR: Ollama did not start in time. Please start it manually.", msg_type="error")
            sys.exit(1)
    
    _print_message("Android AI Controller Active. (Ctrl+D to exit)", msg_type="system")
    
    while True:
        try:
            _print_message("> ", msg_type="prompt", end='', flush=True)
            user_query = input("")
            if not user_query.strip():
                continue
            
            start_time = time.time()
            stop_timer_event = threading.Event()
            timer_thread = threading.Thread(target=timer_display, args=(stop_timer_event, start_time))
            timer_thread.daemon = True
            timer_thread.start()

            full_command_content = ""
            final_command = None
            error_occurred = False

            try:
                for chunk in get_ai_command(user_query, extra_context):
                    if isinstance(chunk, dict):
                        if "final_command" in chunk:
                            final_command = chunk["final_command"]
                            break # Exit the loop, final command received
                        elif "error" in chunk:
                            _print_message(f"{chunk['error']}", msg_type="error")
                            error_occurred = True
                            break
                    else:
                        full_command_content += chunk
                        sys.stdout.write(chunk) # Print partial response
                        sys.stdout.flush()
            finally:
                stop_timer_event.set()
                timer_thread.join()
            
            _print_message("", end='\n', flush=True) # Ensure newline after streamed output

            if error_occurred:
                continue
            if final_command:
                command = final_command
            else:
                command = sanitize_command(full_command_content) # Fallback if final_command not explicitly yielded

            if "termux-" in command and "error" not in command.lower():
                _print_message(f"Executing: {command}", msg_type="executing")
                subprocess.run(command, shell=True)
            else:
                _print_message(f"AI Response: {command}", msg_type="ai_response")
                
        except (EOFError, KeyboardInterrupt):
            _print_message("Shutting down assistant...", msg_type="system")
            break

if __name__ == "__main__":
    main()

