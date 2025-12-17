# Termux AI Assistant
A local, LLM-powered CLI for controlling Android hardware through Termux. This project uses Ollama and the Llama 3.2 1B model to translate natural language into valid Termux:API commands.

## Features
- Full Local Execution: No data is sent to external servers.
- Automatic Scaling: Converts 0-100% requests to the Termux-specific 0-15 volume scale.
- Hallucination Sanitizer: A Python-based cleanup layer that corrects model typos and prevents conversational rambling.
- Modular Context: Inject custom rules via `extra.md` without rebuilding the core model.
- Process Stability: Uses persistent sessions and wake-lock logic to ensure high performance on mobile hardware.

## Installation

### 1. Prerequisites
You must install the following from F-Droid:
- Termux
- Termux:API (The Android application: Download it [here](https://f-droid.org/packages/com.termux.api/)) 

### 2. Setup Environment
Open Termux and run the install script:
```bash
curl -sL https://raw.githubusercontent.com/explysm/termux-assistant/refs/heads/master/install.sh | bash
```
