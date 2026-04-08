#!/bin/bash
# Startup script for Cascade environment
# Starts both FastAPI server (port 8000) and Gradio UI (port 7860)

set -e

echo "🚀 Starting Cascade RL Environment..."

# Set PYTHONPATH for cascade_env imports
export PYTHONPATH=/app/src:/app

# Start FastAPI server in background
echo "📡 Starting FastAPI server on http://0.0.0.0:8000"
uvicorn server.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Give API a moment to start
sleep 2

# Start Gradio UI (foreground, so container doesn't exit)
echo "🌐 Starting Gradio UI on http://0.0.0.0:7860"
python app.py

# Cleanup on exit
trap "kill $API_PID" EXIT
