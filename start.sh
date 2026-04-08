#!/bin/bash
set -e

echo "Starting Cascade environment"

export PYTHONPATH=/app/src:/app

echo "Starting FastAPI server on port 8000"
uvicorn server.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

sleep 2

echo "Starting Gradio UI on port 7860"
python app.py
