#!/bin/sh

# 1. Setup Directories
echo "Creating assistant directory structure..."
mkdir -p $HOME/termuxassistant/examples
echo "----- Done -----"

# 2. Download Files
REPO_URL="https://raw.githubusercontent.com/explysm/termux-assistant/refs/heads/master"

echo "Downloading script and model configuration..."
curl -L -o $HOME/termuxassistant/pa.py "$REPO_URL/pa.py"
curl -L -o $HOME/termuxassistant/Modelfile "$REPO_URL/Modelfile"

echo "Downloading configuration templates..."
curl -L -o $HOME/termuxassistant/examples/settings.conf.example "$REPO_URL/examples/settings.conf.example"
curl -L -o $HOME/termuxassistant/examples/extra.md.example "$REPO_URL/examples/extra.md.example"
echo "----- Done -----"

# 3. Model Building
echo "Pulling base Llama 3.2 1B weights..."
ollama pull llama3.2:1b

echo "Building custom android-1b model..."
cd $HOME/termuxassistant && ollama create android-1b -f Modelfile
echo "----- Done -----"

# 4. Environment Setup
echo "Adding 'tassist' alias to .bashrc..."
touch $HOME/.bashrc
if ! grep -q "alias tassist=" "$HOME/.bashrc"; then
    echo "alias tassist='python $HOME/termuxassistant/pa.py'" >> $HOME/.bashrc
fi
echo "OK"
echo "Installing dependencies..."
pkg update
pkg install ollama python
pip install requests
echo "----- Done -----"

echo "-------------------------------------------------------"
echo "Installation Successful!"
echo "1. Run: source ~/.bashrc"
echo "2. Run: tassist"
echo "-------------------------------------------------------"

