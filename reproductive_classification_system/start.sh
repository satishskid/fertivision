#!/bin/zsh

echo "Starting AI-Enhanced Reproductive Classification System..."

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
if [ -f requirements_enhanced.txt ]; then
    pip install -r requirements_enhanced.txt
elif [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "No requirements file found!"
    exit 1
fi

# Create necessary directories
mkdir -p uploads
dirname templates 2>/dev/null || mkdir -p templates

# Start Ollama service (if not running)
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Check if DeepSeek model is available
if ! ollama list | grep -q "deepseek"; then
    echo "Installing DeepSeek model..."
    ollama pull deepseek-coder
fi

echo "Starting enhanced web interface..."
echo "Open your browser and go to: http://localhost:5000"
python app.py
