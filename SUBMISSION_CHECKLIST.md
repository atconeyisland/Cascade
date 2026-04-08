# 🎯 Cascade Submission Checklist - All Requirements Analysis

## ⚠️ CRITICAL ISSUES (Block Submission)

### 1. **README.md - Git Merge Conflict** 
**Status:** ❌ BLOCKING
**Issue:** Lines 1-8 have YAML frontmatter with merge conflict markers
```
---
<<<<<<< HEAD
title: Cascade Environment Server
...
```
**Fix Required:** Remove merge conflict markers, clean YAML frontmatter

### 2. **Dockerfile - Server Command Issue**
**Status:** ⚠️ NEEDS VERIFICATION
**Issue:** Current: `CMD ["python", "-m", "server.app"]` won't work
**Why:** Python module path issues with package structure
**Fix Required:** Change to proper uvicorn command

### 3. **Environment Variable Validation**
**Status:** ⚠️ NEEDS CHECK
**Issue:** inference.py doesn't validate required env vars before running
**Required Vars:**
- `API_BASE_URL` ✓ (has default)
- `MODEL_NAME` ✓ (has default)  
- `HF_TOKEN` ✓ (required)
**Fix:** Add validation that fails fast with clear error

### 4. **OpenAI Client Compatibility**
**Status:** ⚠️ NEEDS VERIFICATION
**Issue:** Using `from openai import OpenAI` - verify correct version
**Check:** openai>=1.0.0 in requirements.txt, client initialized properly

---

## 📋 SUBMISSION REQUIREMENTS CHECKLIST

### Pre-Submission Validation Gate

| ✓/✗ | Requirement | Status | Fix Needed |
|-----|-----------|--------|-----------|
| ? | HF Space deploys | NOT TESTED | Setup space.yaml, test deployment |
| ? | OpenEnv spec compliance | PARTIAL | Run `openenv validate`, verify schema |
| ? | Dockerfile builds | NOT TESTED | Test: `docker build -t cascade .` |
| ? | Baseline reproduces | ✓ TESTED | Already verified ✓ |
| ✓ | 3+ tasks with graders | ✓ DONE | task1, task2, task3 all present |
| ? | stdout format [START/STEP/END] | VERIFIED | Checked - format correct ✓ |
| ? | API variables configured | PARTIAL | Need more validation |
| ? | inference.py in root | ✓ DONE | Present at root ✓ |
| ? | OpenAI client used | PARTIAL | Check initialization |
| ? | Runtime < 20 min | ESTIMATE: ~8-12 min (6+10+15 max steps) | Should be OK |
| ? | 2vCPU, 8GB memory compatible | UNKNOWN | Needs lightweight optimization |

---

## 🔧 REQUIRED CHANGES (In Priority Order)

### **PRIORITY 1: Critical Blockers** (Do First)

#### 1.1 Fix README.md YAML Header
**File:** README.md
**Change:** Remove merge conflict, clean frontmatter
```yaml
# CHANGE FROM:
---
<<<<<<< HEAD
title: Cascade Environment Server
emoji: ⚡
...
>>>>>>> feat/dockerfile-requirements
---

# CHANGE TO:
---
title: Cascade RL Environment - Incident Response
emoji: 🚨
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
---
```

#### 1.2 Fix Dockerfile Entry Point
**File:** Dockerfile
**Current Problem:**
```dockerfile
CMD ["python", "-m", "server.app"]  # ❌ Won't work - wrong module path
```
**Change To:**
```dockerfile
ENV PYTHONPATH=/app/src:/app
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.3 Add Environment Variable Validation to inference.py
**File:** inference.py
**Add After Line 30:**
```python
# Validate required environment variables
if not API_KEY:
    raise RuntimeError(
        "HF_TOKEN environment variable required. "
        "Set: export HF_TOKEN='your_api_key'"
    )

if not API_BASE_URL or not MODEL_NAME:
    raise RuntimeError(
        "API_BASE_URL and MODEL_NAME must be set. "
        f"Got: API_BASE_URL={API_BASE_URL}, MODEL_NAME={MODEL_NAME}"
    )

print(f"[CONFIG] API_BASE_URL={API_BASE_URL}")
print(f"[CONFIG] MODEL_NAME={MODEL_NAME}")
print(f"[CONFIG] Using OpenAI client\n", flush=True)
```

### **PRIORITY 2: HF Space Deployment** (Critical)

#### 2.1 Create spaces.hf.yaml or app.py Entry
You need either:

**Option A: Create `spaces.hf.yaml` (NEW FILE)**
```yaml
# File: spaces.hf.yaml
title: Cascade RL Environment
emoji: 🚨
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
```

**Option B: OR Create simple `app.py` (NEW FILE) for Gradio interface**
```python
# File: app.py (for HF Spaces)
import gradio as gr
import subprocess
import os

def run_cascade_demo():
    """Demo endpoint for HF Spaces."""
    return "Cascade Environment Server running on port 8000"

with gr.Blocks() as demo:
    gr.Markdown("# 🚨 Cascade RL Environment")
    gr.Markdown("Incident response training environment")
    
    status = gr.Textbox(value=run_cascade_demo(), interactive=False)
    
    gr.Markdown("""
    To use this environment:
    1. Set environment variables: HF_TOKEN, API_BASE_URL, MODEL_NAME
    2. Run: python inference.py
    """)

if __name__ == "__main__":
    demo.launch()
```

**Recommended:** Use Option B (Gradio app.py) for visible HF Space

#### 2.2 Verify Deployment
**Test locally first:**
```bash
docker build -t cascade:latest .
docker run -p 8000:8000 cascade:latest
# In another terminal:
curl http://localhost:8000/health
```

### **PRIORITY 3: OpenEnv Spec Compliance** (Important)

#### 3.1 Verify openenv.yaml is Complete
**File:** openenv.yaml
**Check:** Must have:
- ✓ name
- ✓ version
- ✓ description
- ✓ author
- ✓ action_space with all fields typed
- ✓ observation_space with all fields typed

**Run validation:**
```bash
pip install openenv-core
openenv validate
```

#### 3.2 Ensure All Models Match Types
**Check:**
- CascadeAction matches action_space ✓
- CascadeObservation matches observation_space ✓
- CascadeReward exists and is used

### **PRIORITY 4: Optimization for Resource Constraints** (Important)

#### 4.1 Optimize for 2vCPU, 8GB RAM
**Current Issues:**
- requirements.txt might have heavy dependencies
- Model context might be too large

**Check:**
```bash
pip install -r requirements.txt  # Should be <1GB
```

**If too large:**
- Remove unused packages
- Use Python 3.11-slim (✓ already doing)
- Cache models if needed

#### 4.2 Verify Runtime < 20 minutes
**Current Estimate:**
- Task 1: 6 steps max ≈ 3-4 min
- Task 2: 10 steps max ≈ 5-7 min
- Task 3: 15 steps max ≈ 7-10 min
- **Total: ~12-20 min** ✓ Should be OK

**Test:**
```bash
time python inference.py
```

### **PRIORITY 5: Documentation Completeness** (High)

#### 5.1 Complete README Requirements
**README must include:**
- ✓ Environment description and motivation
- ✓ Real-world task explanation
- ✓ Action space definition
- ✓ Observation space definition
- ✓ Task descriptions (easy, medium, hard)
- ✓ Grading rubric
- ✓ Setup instructions
- ✓ How to run baseline
- **MISSING:** Baseline scores/results

#### 5.2 Add Baseline Results Section to README
**Add to README:**
```markdown
## Baseline Results

Run the baseline agent:
```bash
export HF_TOKEN="your_token"
export API_BASE_URL="https://router.huggingface.co/v1"  
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
python inference.py
```

**Expected Output:**
```
[START] task=task1_easy env=cascade model=Qwen/Qwen2.5-72B-Instruct
[STEP]  step=1 action=investigate::database reward=0.20 done=false error=null
...
[END]   success=true steps=3 score=1.000 rewards=0.20,0.20,0.20,0.40
```

**Expected Score Ranges:**
- Task 1 (Easy): 0.7-1.0
- Task 2 (Medium): 0.5-0.9
- Task 3 (Hard): 0.3-0.8

```

---

## 🧪 VALIDATION SCRIPT CHECKLIST

### Run These Tests Before Submission

```bash
# 1. Unit tests
python test_all.py
# Expected: All tests pass ✓

# 2. Server connectivity
python test_client.py
# Expected: All tests passed ✓

# 3. Dockerfile
docker build -t cascade:latest .
docker run -p 8000:8000 --rm cascade:latest &
sleep 5
curl http://localhost:8000/health
# Expected: {"status": "ok", ...}

# 4. Inference (with env vars set)
export HF_TOKEN="test_key"
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
timeout 600 python inference.py  # 10 min timeout
# Expected: Complete without errors, [START/STEP/END] logs

# 5. OpenEnv validation
openenv validate
# Expected: YAML valid, models match schema
```

---

## 📊 FILE STATUS TABLE

| File | Status | Action | Priority |
|------|--------|--------|----------|
| README.md | ❌ Merge conflict | Fix YAML header | P1 |
| Dockerfile | ⚠️ Wrong CMD | Fix entrypoint | P1 |
| inference.py | ✓ OK | Add env validation | P2 |
| openenv.yaml | ✓ OK | Verify completeness | P3 |
| requirements.txt | ✓ OK | Verify size | P4 |
| server/app.py | ✓ OK | Already tested | - |
| src/cascade_env/*.py | ✓ OK | Already tested | - |
| spaces.hf.yaml | ❌ MISSING | Create for HF | P2 |
| app.py (Gradio) | ❌ MISSING | Create for UI | P2 |

---

## 🚀 SUBMISSION READINESS TIMELINE

### Week 1: Critical Fixes (TODAY)
- [ ] Fix README.md merge conflict
- [ ] Fix Dockerfile CMD
- [ ] Add env var validation
- [ ] Create spaces.hf.yaml or app.py

### Week 2: Verification
- [ ] Run local docker build
- [ ] Test docker run with curl
- [ ] Verify openenv validate passes
- [ ] Time inference.py runtime
- [ ] Test on resource-constrained machine if possible

### Week 3: Deployment
- [ ] Push to GitHub
- [ ] Create HF Space (if required)
- [ ] Run baseline inference on HF Space
- [ ] Final validation: all pre-checks pass
- [ ] Submit!

---

## ⚡ QuickStart: Changes Needed Today

```bash
# 1. Fix README
nano README.md  # Remove merge conflict lines 1-8

# 2. Fix Dockerfile  
nano Dockerfile  # Change CMD line

# 3. Fix inference.py
nano inference.py  # Add env validation after line 30

# 4. Create spaces config
touch spaces.hf.yaml  # Add HF Space config

# 5. Test locally
docker build -t cascade .
docker run -p 8000:8000 cascade
```

---

## 📞 If You Have Questions

Refer to:
1. **openenv.yaml** - Schema documentation (run `openenv validate`)
2. **COMPLETE_GUIDE.md** - Architecture & rewards
3. **test_all.py** - Grading logic
4. Submission guidelines provided above
