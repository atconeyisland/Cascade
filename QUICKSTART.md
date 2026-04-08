# Cascade RL Environment - Quick Start Guide

## 🎯 What is Cascade?

An **RL environment for training autonomous IT incident response agents**. Agents receive alerts, system logs, and available runbooks, then must diagnose and resolve production incidents.

## ⚡ Quick Start (5 min)

### Step 1: Install Dependencies
```bash
cd folder/of/choice
python -m pip install -r requirements.txt
```

### Step 2: Validate Installation
```bash
python test_all.py
```
Expected: **All tests pass** ✅

### Step 3: Start the Server (Terminal 1)
```powershell
powershell -Command "$env:PYTHONPATH='src'; uvicorn server.app:app --reload --host 0.0.0.0 --port 8000"
```

### Step 4: Test Server (Terminal 2)
```bash
python test_client.py
```
Expected: `✅ All tests passed!`

### Step 5: Run Inference Agent (Terminal 2)
```bash
# Set your LLM credentials
$env:HF_TOKEN = "your_api_key"
$env:API_BASE_URL = "https://api.openai.com/v1"    # OpenAI or HF router
$env:MODEL_NAME = "gpt-4o"                          # or your model

python inference.py
```

Expected output:
```
[START] task=task1_easy env=cascade model=gpt-4o
[STEP]  step=1 action=investigate::database reward=0.20 done=false error=null
[STEP]  step=2 action=select_runbook::db-cpu-runbook reward=0.40 done=false error=null
...
[END]   success=true steps=N score=1.000 rewards=...
```

## 📊 Three Tasks

| Task | Scenario | Difficulty | Key | Grading |
|------|----------|-----------|-----|---------|
| **Task 1** | Database CPU spike | Easy | Investigate "database", select "db-cpu-runbook" | Max 1.0 |
| **Task 2** | Memory leak cascade | Medium | More steps, harder dependencies | Max 1.0 |
| **Task 3** | Multi-AZ failure | Hard | Must escalate, avoid red herrings | Max 1.0 |

## 🔑 Environment Variables

| Var | Example | Notes |
|-----|---------|-------|
| `HF_TOKEN` | `hf_xxxxx` or `sk-...` | Your API key (OpenAI, HF, Anthropic, etc) |
| `API_BASE_URL` | `https://api.openai.com/v1` | LLM provider URL |
| `MODEL_NAME` | `gpt-4o` | Model identifier |

### Example Setups

**OpenAI:**
```bash
$env:HF_TOKEN = "sk-proj-xxxx"
$env:API_BASE_URL = "https://api.openai.com/v1"
$env:MODEL_NAME = "gpt-4o"
```

**Hugging Face (Open-source models):**
```bash
$env:HF_TOKEN = "hf_xxxxx"
$env:API_BASE_URL = "https://router.huggingface.co/v1"
$env:MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
```

**Anthropic:**
```bash
$env:HF_TOKEN = "sk-ant-xxxxx"
$env:API_BASE_URL = "https://api.anthropic.com/v1"
$env:MODEL_NAME = "claude-3-5-sonnet-20241022"
```

## 🚀 Run Multiple Models (Trial Run)

Create file `run_trials.ps1`:
```powershell
$trials = @(
    @{ name = "GPT-4"; token = "sk-..."; model = "gpt-4o" },
    @{ name = "Qwen"; token = "hf_..."; model = "Qwen/Qwen2.5-72B-Instruct" }
)

foreach ($trial in $trials) {
    Write-Host "===== Testing: $($trial.name) ====="
    $env:HF_TOKEN = $trial.token
    $env:MODEL_NAME = $trial.model
    python inference.py
    Write-Host ""
}
```

Run it:
```bash
powershell -ExecutionPolicy Bypass -File run_trials.ps1
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/cascade_env/environment.py` | Core RL environment logic |
| `src/cascade_env/client.py` | HTTP client for agents |
| `src/cascade_env/tasks/*.py` | 3 incident scenarios |
| `src/cascade_env/graders/*.py` | Scoring logic |
| `server/app.py` | FastAPI HTTP server |
| `inference.py` | Baseline LLM agent |
| `test_all.py` | Unit tests (27+ tests) |
| `test_client.py` | Server connectivity check |

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: cascade_env` | Set `$env:PYTHONPATH = "src"` |
| `Connection refused` | Server not running on port 8000 |
| `404 error` | Wrong endpoint (use `/reset/{task_id}`, `/step/{task_id}`) |
| `reward=0.0` | Action didn't match available options or correct answer |
| Server crashes | Check logs, ensure Python 3.10+ |

## 📈 Typical Agent Performance

- **Random actions**: ~0.1 score
- **Rule-based**: ~0.5 score
- **LLM baseline**: ~0.7-0.8 score
- **Optimized LLM**: ~0.95+ score

## 🔗 API Endpoints

```
GET  /health                     # Server status
POST /reset/{task_id}            # Reset episode
POST /step/{task_id}             # Execute action
GET  /state/{task_id}            # Get current state
```

## 📚 Learn More

See **COMPLETE_GUIDE.md** for:
- Detailed grading rubric
- Client library examples
- Async test patterns
- Docker deployment
- What still needs work

## 🎓 Expected Workflow

1. ✅ Install & test → `test_all.py` passes
2. ✅ Start server → `test_client.py` passes  
3. ✅ Configure LLM credentials → env vars set
4. 🔄 Run inference → `python inference.py`
5. 📊 Parse output → Check [STEP] logs for accuracy
6. 🔧 Iterate → Adjust prompt, try different models

---

**Ready to test?** Start with Step 1 above! 🚀
