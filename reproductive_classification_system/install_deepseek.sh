#!/bin/zsh

echo "Installing DeepSeek LLM for local image analysis..."

# Check for Homebrew and install Ollama via brew if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew >/dev/null 2>&1; then
        if ! command -v ollama >/dev/null 2>&1; then
            echo "Installing Ollama via Homebrew..."
            brew install ollama
        else
            echo "Ollama already installed."
        fi
    else
        echo "Homebrew not found. Installing Ollama via curl script..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
else
    # For Linux or other OS
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Pull DeepSeek model if not already present
if ! ollama list | grep -q "deepseek-coder"; then
    echo "Pulling DeepSeek model..."
    ollama pull deepseek-coder
else
    echo "DeepSeek model already present."
fi

echo "DeepSeek installation complete!"
echo "Starting Ollama service..."
# Start Ollama in the background if not already running
if ! pgrep -x "ollama" >/dev/null; then
    ollama serve &
    echo "Ollama service started."
else
    echo "Ollama service already running."
fi

echo "Setup complete! DeepSeek is ready for image analysis."
