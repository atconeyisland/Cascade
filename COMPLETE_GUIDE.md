# Cascade Project - Complete Guide

## 📋 Project Overview

**Cascade** is a reinforcement learning environment for training autonomous IT incident response agents. It simulates real-world production incidents with three difficulty tiers:
- **Task 1 (Easy)**: Single-service incident (database CPU spike)
- **Task 2 (Medium)**: Multi-system incident with dependencies (memory leak + cascading failures)
- **Task 3 (Hard)**: Cascading multi-service failure with red herrings and human escalation requirement

## ✅ What Was Fixed

1. **Git Merge Conflicts** - Resolved in:
   - `requirements.txt` (merged conflicting dependencies)
   - `pyproject.toml` (consolidated build configs)
   - `server/app.py` (unified server logic)
   - `Dockerfile` (fixed paths and entry point)
   - `__init__.py` (fixed module exports)

2. **Missing Client Implementation**
   - Created `cascade_env/client.py` with `CascadeEnv` HTTP client class
   - Supports both local and remote servers

3. **Directory Structure & Imports**
   - Fixed import paths for cascade_env module
   - Fixed PYTHONPATH issues
   - Updated Dockerfile for correct paths

4. **Dependencies**
   - Cleaned requirements.txt with all necessary packages
   - Added missing transitive dependencies (httpx, starlette, typer)

## 🚀 How to Run

### 1. Install Dependencies
```bash
cd d:\DOCUMENTS\CollegeStuff\Cascade
python -m pip install -r requirements.txt
```

### 2. Run Tests (to validate environment setup)
```bash
python test_all.py
```

Expected output: All 27+ tests should pass ✓

### 3a. Run Server (Standard)
```bash
# Set PYTHONPATH and start uvicorn
$env:PYTHONPATH = "src"
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

### 3b. Run Server (from PowerShell - one-liner)
```powershell
powershell -Command "$env:PYTHONPATH='src'; uvicorn server.app:app --reload --host 0.0.0.0 --port 8000"
```

The server will start at `http://localhost:8000`

#### Health Check:
```bash
curl http://localhost:8000/health
```

## 🤖 Run Inference Agent

Once server is running, in another terminal:

```bash
# Set environment variables for your LLM provider
$env:HF_TOKEN = "your_huggingface_token_or_api_key"
$env:API_BASE_URL = "https://api.openai.com/v1"  # or HF router URL
$env:MODEL_NAME = "gpt-4o"  # or any supported model

python inference.py
```

### Example with Hugging Face Router:
```bash
$env:HF_TOKEN = "hf_xxxxxxxxxxxxx"
$env:API_BASE_URL = "https://router.huggingface.co/v1"
$env:MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

python inference.py
```

Inference script will:
1. Run all 3 tasks sequentially
2. Show [START], [STEP], [END] logs in structured format
3. Report scores for each task
4. Measure agent performance on incident response

## 🧪 Trial Runs with Multiple Models/Keys

### Option 1: Sequential Testing Script
Create a file `run_trials.py`:

```python
import subprocess
import os

TRIALS = [
    {
        "name": "GPT-4 OpenAI",
        "HF_TOKEN": "sk-...",
        "API_BASE_URL": "https://api.openai.com/v1",
        "MODEL_NAME": "gpt-4o",
    },
    {
        "name": "Claude Sonnet",
        "HF_TOKEN": "sk-ant-...",
        "API_BASE_URL": "https://api.anthropic.com/v1",
        "MODEL_NAME": "claude-3-5-sonnet-20241022",
    },
    {
        "name": "Qwen 72B (HF Router)",
        "HF_TOKEN": "hf_xxxxx",
        "API_BASE_URL": "https://router.huggingface.co/v1",
        "MODEL_NAME": "Qwen/Qwen2.5-72B-Instruct",
    },
]

for trial in TRIALS:
    print(f"\n{'='*60}")
    print(f"Running: {trial['name']}")
    print(f"{'='*60}\n")
    
    env = os.environ.copy()
    env.update({
        "HF_TOKEN": trial["HF_TOKEN"],
        "API_BASE_URL": trial["API_BASE_URL"],
        "MODEL_NAME": trial["MODEL_NAME"],
    })
    
    result = subprocess.run(["python", "inference.py"], env=env)
    
    if result.returncode != 0:
        print(f"❌ Trial failed: {trial['name']}")
    else:
        print(f"✅ Trial completed: {trial['name']}")
```

Run it:
```bash
python run_trials.py
```

### Option 2: Parallel Testing (async)
```python
import asyncio
import subprocess
import os

TRIALS = [...]  # Same as above

async def run_trial(trial):
    env = os.environ.copy()
    env.update({
        "HF_TOKEN": trial["HF_TOKEN"],
        "API_BASE_URL": trial["API_BASE_URL"],
        "MODEL_NAME": trial["MODEL_NAME"],
    })
    
    proc = await asyncio.create_subprocess_exec(
        "python", "inference.py",
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return trial["name"], proc.returncode, stdout.decode()

async def main():
    tasks = [run_trial(t) for t in TRIALS]
    results = await asyncio.gather(*tasks)
    
    for name, code, output in results:
        print(f"\n{'='*60}")
        print(f"Result: {name} (code={code})")
        print(output[:500])  # First 500 chars

asyncio.run(main())
```

## 🔌 Using CascadeEnv Client Directly

```python
from cascade_env.client import CascadeEnv
from cascade_env.models import CascadeAction, ActionType

# Connect to local server
env = CascadeEnv(base_url="http://localhost:8000")

# Check health
print(env.health())  # {"status": "ok", "name": "cascade"}

# Run an episode on Task 1
obs = env.reset(task_id=1)
print(f"Alert: {obs.alert_message}")
print(f"Available runbooks: {obs.available_runbooks}")

# Take an action
action = CascadeAction(
    action_type=ActionType.INVESTIGATE,
    action_value="database",
    reasoning="High CPU usage in logs"
)

result = env.step(action, task_id=1)
print(f"Reward: {result.reward}")
print(f"Done: {result.done}")

env.close()
```

## 📊 Understanding Outputs

### Inference Output Format
```
[START] task=task1_easy env=cascade model=gpt-4o
[STEP]  step=1 action=investigate::database reward=0.20 done=false error=null
[STEP]  step=2 action=select_runbook::db-cpu-runbook reward=0.40 done=false error=null
[STEP]  step=3 action=execute_step::run explain on slow query reward=0.55 done=false error=null
[END]   success=true steps=3 score=1.000 rewards=0.20,0.20,0.20,0.40
```

**Fields:**
- `task`: Which task (task1_easy, task2_medium, task3_hard)
- `step`: Current step number
- `action`: Agent's action in format `type::value`
- `reward`: Reward for this step (0.0-1.0)
- `done`: Whether episode ended
- `error`: Error message if action failed
- `success`: Whether task was completed successfully
- `score`: Final task score (0.0-1.0, graded by task-specific grader)
- `rewards`: Comma-separated list of all rewards

### Grading Rubric

**Task 1 (Database CPU):**
- +0.20: Investigate "database" ✓
- +0.20: Select "db-cpu-runbook" ✓
- +0.15 each: Execute correct remediation steps (max 3 steps)
- +0.10: Correct priority identified (P2) ✓
- +0.25: Full resolution (investigate + runbook + 2+ steps) ✓
- Total: 1.0

**Task 2 (Memory Leak):**
- Similar structure to Task 1
- Correct investigation: "auth-service"
- Correct runbook: "memory-runbook"
- Correct steps: "drain connections", "restart auth-service", "preserve sessions"

**Task 3 (Cascading Failure - Hardest):**
- MUST escalate to human (P1 incident)
- -0.20 penalty if fails to escalate
- Correct investigation: "network" (not red herring "recommendation-engine")
- Correct runbook: "network-runbook"
- Correct steps: Failover 3 services

## 🐛 What Still Needs Work

### 1. **Async Python Client Support**
Currently `CascadeEnv` uses synchronous `httpx`. For concurrent trials:
```python
# Future: async version
class CascadeEnvAsync:
    async def step(self, action):
        ...
```

### 2. **Batch Processing**
- Add `/batch/step` endpoint to run multiple actions in parallel
- Useful for testing different agent strategies simultaneously

### 3. **Metrics & Logging**
Missing:
- Structured metrics export (JSON/CSV)
- Agent decision trees / reasoning logs
- Cost tracking (if using paid APIs)
- Latency profiling per step

### 4. **Docker Support**
The Dockerfile exists but hasn't been tested:
```bash
docker build -t cascade:latest .
docker run -p 8000:8000 cascade:latest
```

### 5. **Remote Deployment**
Currently designed for local testing. To deploy to Hugging Face Spaces (mentioned in README):
- Set up Space from template
- Export environment variables
- Connect to remote URL in inference.py

### 6. **Test Coverage**
- No tests for HTTP client (CascadeEnv)
- No tests for concurrent server requests
- No integration tests with actual LLM calls

### 7. **Agent Implementations**
The inference.py is a baseline. Missing:
- Chain-of-thought prompting variants
- Multi-turn reasoning with guardrails
- Fallback strategies (escalate early vs. risky investigation)
- Cost-aware action selection

## 📁 Directory Structure
```
Cascade/
├── src/cascade_env/          # Core environment package
│   ├── environment.py          # CascadeEnvironment class
│   ├── models.py               # Pydantic models
│   ├── server.py               # Old server (deprecated)
│   ├── client.py               # HTTP client (NEW)
│   ├── tasks/
│   │   ├── task1.py            # Single-service incident
│   │   ├── task2.py            # Multi-service incident
│   │   └── task3.py            # Cascading failure
│   └── graders/
│       ├── grader1.py          # Task 1 scoring
│       ├── grader2.py          # Task 2 scoring
│       └── grader3.py          # Task 3 scoring
├── server/                   # FastAPI HTTP server
│   ├── app.py                  # Main endpoint logic
│   └── __init__.py
├── inference.py                # Baseline agent (LLM-based)
├── test_all.py                 # Comprehensive test suite
├── test_concurrency.py         # Concurrency tests
├── requirements.txt            # Dependencies (FIXED)
├── pyproject.toml              # Project config (FIXED)
├── Dockerfile                  # Container config (FIXED)
└── README.md                   # Project overview
```

## 🔧 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'server'`
**Solution:** Set PYTHONPATH before running uvicorn:
```bash
$env:PYTHONPATH = "src"
uvicorn server.app:app ...
```

### Issue: `ModuleNotFoundError: No module named 'cascade_env'`
**Solution:** Same as above - cascade_env is in src/, need it in PYTHONPATH

### Issue: Server crashes when taking step
**Check:**
1. Did you reset() before step()?
2. Is task_id in {1, 2, 3}?
3. Check server logs for tracebacks

### Issue: Agent gets zero reward
**Check:**
1. Is action format correct? Should be `action_type::action_value`
2. Are values exact matches from available_runbooks list?
3. Is investigation targeting the correct service?

## 📚 Resources

- **README.md** - Project motivation and design
- **inference.py** - LLM agent example
- **test_all.py** - Grading rules & episode mechanics
- **openenv.yaml** - Environment specification
