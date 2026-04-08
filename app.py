#!/usr/bin/env python3
"""
Gradio application for Cascade RL Environment.
Provides a web interface and health check for HF Spaces deployment.

This serves as the entry point when deployed to HuggingFace Spaces.
The actual RL environment runs on the FastAPI server (port 8000).
"""

import gradio as gr
import requests
import os
from typing import Optional

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
API_DOCS_URL = f"{SERVER_URL}/docs"

def check_server_status() -> tuple[str, str]:
    """Check if the Cascade server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return "✅ Server Running", f"Status: {data.get('status')} | Name: {data.get('name')}"
        else:
            return "⚠️ Server Error", f"HTTP {response.status_code}"
    except Exception as e:
        return "❌ Server Offline", str(e)


def format_environment_guide() -> str:
    """Return formatted guide for environment setup."""
    return """
## 📋 Setup Guide

### 1. Set Environment Variables

```bash
export HF_TOKEN="your_huggingface_or_api_token"
export API_BASE_URL="https://api.openai.com/v1"  # or your provider
export MODEL_NAME="gpt-4o"  # or your model
```

**Supported Providers:**
- OpenAI: `API_BASE_URL=https://api.openai.com/v1`, `MODEL_NAME=gpt-4o`
- HuggingFace: `API_BASE_URL=https://router.huggingface.co/v1`, `MODEL_NAME=Qwen/Qwen2.5-72B-Instruct`
- Anthropic: `API_BASE_URL=https://api.anthropic.com/v1`, `MODEL_NAME=claude-3-5-sonnet-20241022`

### 2. Run the Baseline Agent

```bash
python inference.py
```

**Output:**
```
[START] task=task1_easy env=cascade model=gpt-4o
[STEP]  step=1 action=investigate::database reward=0.20 done=false error=null
...
[END]   success=true steps=3 score=1.000 rewards=0.20,0.20,0.20
```

### 3. Expected Performance

- **Task 1 (Easy):** Score 0.7-1.0
- **Task 2 (Medium):** Score 0.5-0.9
- **Task 3 (Hard):** Score 0.3-0.8

## 📚 Learn More

- View API docs: {api_docs_link}
- Check QUICKSTART.md for quick setup
- Read COMPLETE_GUIDE.md for detailed architecture
"""


def get_api_endpoints() -> str:
    """Return documentation for API endpoints."""
    return f"""
## 🔌 API Endpoints

**Base URL:** {SERVER_URL}

### Health Check
```
GET /health
```
Returns: `{{"status": "ok", "name": "cascade"}}`

### Reset Environment
```
POST /reset/{{task_id}}
```
Parameters:
- `task_id`: 1 (easy), 2 (medium), or 3 (hard)

Returns: Initial observation

### Step
```
POST /step/{{task_id}}
```
Body:
```json
{{
  "action_type": "investigate",
  "action_value": "database",
  "reasoning": "High CPU in logs"
}}
```

Returns: Observation, reward, done flag

### Get State
```
GET /state/{{task_id}}
```
Returns: Current episode state

## 📖 Full API Documentation

View interactive docs: {api_docs_link}
"""


def task_description() -> str:
    """Return description of available tasks."""
    return """
## 🎯 Tasks

### Task 1: Single-Service Incident (Easy)
**Scenario:** Database CPU spike causing API timeouts

**Objective:** Investigate database, select correct runbook, execute remediation steps

**Grading:**
- +0.20: Investigate "database"
- +0.20: Select "db-cpu-runbook"
- +0.15 each: Execute 3 correct steps
- +0.10: Identify correct P2 priority
- +0.25: Full resolution

**Expected Score:** 0.7-1.0

---

### Task 2: Multi-Service Cascade (Medium)
**Scenario:** Memory leak in auth-service causing cascading failures

**Objective:** Identify memory issue, drain connections, restart services

**Grading:**
- Similar to Task 1
- Must handle dependencies correctly
- More states to manage

**Expected Score:** 0.5-0.9

---

### Task 3: Cascading Failure (Hard)
**Scenario:** Multi-AZ network partition with red herrings

**Objective:** Identify network issue (not CPU), failover services, escalate to human

**Grading:**
- Must escalate (P1 incident requires human approval)
- Must avoid red herring investigation
- Complex multi-service failover

**Expected Score:** 0.3-0.8
"""


# Create Gradio interface
with gr.Blocks(
    title="Cascade RL Environment",
    theme=gr.themes.Soft(primary_hue="blue")
) as interface:
    
    gr.Markdown("""
    # 🚨 Cascade RL Environment
    
    An OpenEnv environment for training autonomous IT incident response agents.
    
    Agents diagnose and resolve production incidents by:
    - Investigating system logs
    - Selecting remediation runbooks
    - Executing remediation steps
    - Making escalation decisions
    """)
    
    with gr.Tabs():
        
        # Tab 1: Status
        with gr.Tab("Status"):
            gr.Markdown("### Server Status")
            status_text = gr.Textbox(label="Status", max_lines=1)
            status_details = gr.Textbox(label="Details", max_lines=3)
            
            def update_status():
                status, details = check_server_status()
                return status, details
            
            refresh_btn = gr.Button("🔄 Check Server")
            refresh_btn.click(update_status, outputs=[status_text, status_details])
            
            # Auto-check on load
            interface.load(update_status, outputs=[status_text, status_details])
        
        # Tab 2: Setup Guide
        with gr.Tab("Setup Guide"):
            gr.Markdown(format_environment_guide().format(
                api_docs_link=API_DOCS_URL
            ))
        
        # Tab 3: Tasks
        with gr.Tab("Tasks"):
            gr.Markdown(task_description())
        
        # Tab 4: API
        with gr.Tab("API Reference"):
            gr.Markdown(get_api_endpoints().format(
                api_docs_link=API_DOCS_URL
            ))
        
        # Tab 5: Examples
        with gr.Tab("Examples"):
            gr.Markdown("""
            ## Example Usage
            
            ### Python Client
            ```python
            from cascade_env.client import CascadeEnv
            from cascade_env.models import CascadeAction, ActionType
            
            env = CascadeEnv(base_url="http://localhost:8000")
            obs = env.reset(task_id=1)
            
            action = CascadeAction(
                action_type=ActionType.INVESTIGATE,
                action_value="database",
                reasoning="High CPU in logs"
            )
            result = env.step(action, task_id=1)
            print(f"Reward: {result.reward}, Done: {result.done}")
            ```
            
            ### cURL
            ```bash
            # Reset
            curl -X POST http://localhost:8000/reset/1
            
            # Step
            curl -X POST http://localhost:8000/step/1 \\
              -H "Content-Type: application/json" \\
              -d '{
                "action_type": "investigate",
                "action_value": "database",
                "reasoning": "High CPU"
              }'
            
            # State
            curl http://localhost:8000/state/1
            ```
            """)


if __name__ == "__main__":
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
