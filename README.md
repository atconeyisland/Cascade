# Cascade — Incident Response RL Environment

> Train agents to stop failures before they spread.

Cascade is an OpenEnv-compatible reinforcement learning environment that simulates real-world IT incident response. An agent acts as an Incident Response Commander — diagnosing production failures, selecting runbooks, executing remediation steps, and deciding when to escalate to a human.

No existing OpenEnv environment covers production incident response. Cascade fills that gap.

---

## Motivation

Current RL benchmarks focus on games and robotics. LLM agents now operate at human-expert level on many tasks, yet standardized benchmarks for real-world operational decision-making remain scarce.

Incident response is genuinely hard. Unlike turn-based games, it requires:
- **Partial observability** — logs are noisy; ground truth is hidden
- **Sequential reasoning under time pressure** — wrong order means penalties
- **Cost-aware decisions** — escalation is expensive; incorrect fixes carry penalties
- **Human-in-the-loop judgment** — knowing when *not* to act is a skill

Every major cloud provider, SaaS platform, and fintech company faces this problem daily. Cascade provides an open, reproducible standard for benchmarking agents on it.

---

## Project Structure

```
cascade/
├── inference.py               # Baseline agent script (root — required)
├── openenv.yaml               # OpenEnv spec metadata
├── README.md
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── test_all.py
├── server/
│   └── app.py                 # FastAPI server entrypoint
└── src/
    └── cascade_env/
        ├── models.py          # Pydantic models
        ├── environment.py     # Core RL environment
        ├── tasks/
        │   ├── task1.py       # Easy: DB CPU spike
        │   ├── task2.py       # Medium: Memory leak + cascading failure
        │   └── task3.py       # Hard: Network partition + red herrings
        └── graders/
            ├── grader1.py
            ├── grader2.py
            └── grader3.py
```

---

## Observation Space

Each observation returned by `reset()` and `step()` is a `CascadeObservation`:

| Field | Type | Description |
|---|---|---|
| `alert_message` | `str` | PagerDuty-style alert that triggered the incident |
| `system_logs` | `List[str]` | Timestamped log lines from affected services (may include noise) |
| `available_runbooks` | `List[str]` | Runbooks the agent can select from |
| `current_step` | `int` | Current step number in the episode |
| `steps_taken` | `List[str]` | History of actions taken so far |
| `episode_done` | `bool` | Whether the episode has ended |
| `affected_services` | `List[str]` | Services impacted by the incident |
| `severity_level` | `str` | `low` / `medium` / `high` / `critical` |
| `priority_level` | `str` | `P1` / `P2` / `P3` |
| `human_intervention_required` | `bool` | Whether human escalation is required to resolve |

---

## Action Space

Each action is a `CascadeAction`:

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | One of the valid action types below |
| `action_value` | `str` | Free-text value for the action |
| `reasoning` | `str` | Agent's explanation for taking the action |

Valid `action_type` values:

| Action | Description |
|---|---|
| `investigate` | Inspect a service or log stream for root cause clues |
| `select_runbook` | Choose a runbook to apply to the incident |
| `execute_step` | Execute a specific remediation step |
| `escalate_to_human` | Hand off the incident to a human operator |
| `resolve` | Mark the incident as resolved |
| `rollback` | Roll back a previously executed step |

---

## Reward Function

Rewards accumulate across the episode, providing dense signal for RL training. Final score is clipped to `[0.0, 1.0]`.

| Event | Reward |
|---|---|
| Correct system identified via investigation | +0.20 |
| Correct runbook selected | +0.20 |
| Correct remediation step executed | +0.15 each |
| Incident fully resolved | +0.25 |
| Appropriate escalation to human | +0.15 |
| Correct priority level identified | +0.10 |
| Wrong runbook selected | -0.10 |
| Unnecessary escalation | -0.10 |
| Failed to escalate when required | -0.20 |
| Wasted or redundant step | -0.05 |
| Rollback used | -0.05 |

---

## Tasks

### Task 1 — Easy: DB CPU Spike

**Scenario:** A database service is experiencing a CPU spike caused by a missing index on a high-traffic query. Logs are clean and unambiguous.

**Key challenge:** Identify the correct runbook and execute the fix in the right order.

| Property | Value |
|---|---|
| Priority | P2 |
| Human intervention required | No |
| Max steps | 6 |
| Baseline score (llama-3.3-70b) | 0.650 |

---

### Task 2 — Medium: Memory Leak + Service Dependency

**Scenario:** A memory leak in an auth service is causing cascading 401 errors in a dependent API gateway. The gateway logs superficially suggest a network issue — a deliberate red herring.

**Key challenge:** Identify root cause across two services, prioritize the correct one, and avoid the misleading gateway symptoms.

| Property | Value |
|---|---|
| Priority | P1 |
| Human intervention required | No |
| Max steps | 10 |
| Baseline score (llama-3.3-70b) | 1.000 |

---

### Task 3 — Hard: Multi-Service Cascading Failure

**Scenario:** A network partition triggers failures across three interdependent microservices simultaneously. A high-CPU warning from an unrelated service fires at the same time as a deliberate red herring.

**Key challenge:** Triage correctly under noisy alerts, ignore the red herring, execute failovers in the correct order, and escalate appropriately.

| Property | Value |
|---|---|
| Priority | P1 |
| Human intervention required | Yes |
| Max steps | 15 |
| Baseline score (llama-3.3-70b) | 0.500 |

---

## Baseline Scores

Model: `llama-3.3-70b-versatile` via Groq API, run against the live HF Space.

| Task | Model | Score | Steps | Success |
|---|---|---|---|---|
| task1_easy | llama-3.3-70b-versatile | 0.650 | 5 | True |
| task2_medium | llama-3.3-70b-versatile | 1.000 | 10 | True |
| task3_hard | llama-3.3-70b-versatile | 0.500 | 6 | True |

---

## API Endpoints

All endpoints accept an optional `?task_id=` query parameter (1, 2, or 3). Defaults to 1.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check — returns `{"status": "healthy"}` |
| `/metadata` | GET | Environment name and description |
| `/schema` | GET | Action, observation, and state schemas |
| `/reset` | POST | Start a new episode, returns initial observation |
| `/step` | POST | Execute an action, returns observation + reward + done |
| `/state` | GET | Current environment state |
| `/mcp` | POST | JSON-RPC endpoint for OpenEnv multi-mode deployment |

---

## Setup & Running

### Environment variables

```bash
export API_BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=llama-3.3-70b-versatile
export HF_TOKEN=your_api_key_here
export CASCADE_ENV_URL=https://atconeyisland-cascade.hf.space
```

### Run baseline agent

```bash
pip install -r requirements.txt
python inference.py
```

### Run locally with Docker

```bash
docker build -t cascade .
docker run -p 7860:7860 cascade
```

### Run tests

```bash
python test_all.py
```

---

## Grading

Graders evaluate the agent's full action history at episode end and return a float in `[0.0, 1.0]`. They are fully deterministic — the same action history always produces the same score.

Criteria include: correct runbook selection, remediation steps executed, appropriate escalation, resolution within the step budget, and correct priority identification.

---

## Future Scope

- **`time_elapsed` field** in observations to add urgency pressure and require agents to balance investigation depth against time constraints
- **`request_more_logs` action** to allow iterative log retrieval during diagnosis
- **Refined grading** through empirical evaluation on real incident patterns

---

## Team Huntrix

| Member | Responsibility |
|---|---|
| Anvi Trivedi | Environment infrastructure, OpenEnv spec, state machine, reward function, HF Space debugging, pre-submission validation, final submission |
| Prachi Bhowal | Task definitions, grader logic, synthetic incident data, inference script |
| Mokshita VP | Dockerfile, HF Space deployment, HF Space debugging |
