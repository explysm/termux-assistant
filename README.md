# Termux AI Assistant

A local, LLM-powered command-line interface (CLI) for Android hardware control via Termux. This project leverages Ollama and the Llama 3.2 1B model to translate natural language into executable Termux:API commands, all running entirely on your Android device.

## Features

-   **Full Local Execution:** Your data remains on your device; no information is sent to external servers.
-   **Intelligent Command Translation:** Translates natural language requests into precise Termux:API bash commands.
-   **Contextual Understanding:** Utilizes a Llama 3.2 1B model via Ollama for robust language processing.
-   **Automatic Scaling:** Seamlessly converts common ranges (e.g., 0-100% volume) to Termux-specific scales (e.g., 0-15).
-   **Output Guard:** A Python-based layer that refines model outputs, correcting typos and preventing irrelevant conversational responses.
-   **Modular Customization:** Easily inject custom rules and context via `extra.md` without requiring model retraining.
-   **Process Stability:** Employs persistent sessions and wake-lock logic to ensure consistent high performance on mobile hardware.

## Installation

### 1. Prerequisites

You must install the following applications from F-Droid:

-   **Termux**: The terminal emulator itself.
-   **Termux:API**: The Android application providing API access to device features (Download it [here](https://f-droid.org/packages/com.termux.api/)).

### 2. Setup Environment

Open Termux on your Android device and run the following installation script:

```bash
curl -sL https://raw.githubusercontent.com/explysm/termux-assistant/refs/heads/master/install.sh | bash
```

This script will set up all necessary components, including Ollama and the Llama 3.2 1B model.

## Usage

After installation, you can interact with the AI assistant directly from your Termux terminal. Simply type your request in natural language.

**Example Interactions:**

```
$ ai raise volume to full
termux-volume music 15

$ ai set brightness to 10 percent and vibrate
termux-brightness 25 && termux-vibrate -d 500

$ ai send sms to (555) 123-4567 saying hello
termux-sms-send -n 5551234567 "hello"
```

The assistant will output the corresponding Termux:API bash command, which you can then execute.

## Rough amount of seconds for initial prompts

initial time / after

>"Turn volume to full" 2.11s / 1.31s
![inital prompt times visual](https://raw.githubusercontent.com/explysm/termux-assistant/refs/heads/master/assets/initialprompt1.png)

