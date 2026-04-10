---
title: Cascade RL Environment - Incident Response
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
---

# Cascade — Incident Response Commander RL Environment

## Overview

Cascade is an OpenEnv-compatible reinforcement learning environment that simulates real-world IT incident response scenarios. An agent acts as an Incident Response Commander, diagnosing and resolving production incidents by selecting runbooks, executing remediation steps, investigating anomalies, and escalating when necessary.

The environment evaluates whether an LLM-based agent can handle progressively complex SRE (Site Reliability Engineering) tasks — from straightforward single-service incidents to multi-service cascading failures with red herrings.

No existing OpenEnv environment covers production incident response. Cascade fills that gap directly.

---

## Motivation

Current RL benchmarks focus on game-playing and robotics simulation. LLM-based agents now operate at human-expert level on many tasks, yet standardized benchmarks for real-world operational decision-making under uncertainty remain scarce.

Incident response is a genuinely difficult domain. Unlike turn-based games, it requires partial observability (logs are noisy; ground truth is hidden), sequential reasoning under time pressure, cost-aware decisions (escalation is expensive; incorrect fixes carry penalties), and human-in-the-loop judgment around when to escalate.

Cascading failures represent the hardest case — multi-service incidents have exponential complexity, and task-specific agents routinely fail when services interact unexpectedly. Cascade directly tests whether an agent can reason about complex system topology.

Every major cloud provider, SaaS platform, and fintech company faces this problem daily. Existing incident response research relies on proprietary data or toy simulators. Cascade provides an open, reproducible standard for the domain.

---

## Project Structure

```
cascade/
├── inference.py               # Baseline agent script (root — required)
├── openenv.yaml               # OpenEnv spec metadata (root — required)
├── README.md
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── test_all.py
├── server/
│   └── app.py                 # Server entrypoint
└── src/
    └── cascade_env/
        ├── __init__.py
        ├── client.py
        ├── models.py
        ├── environment.py
        ├── server.py
        ├── tasks/
        │   ├── task1.py       # Easy: DB CPU spike
        │   ├── task2.py       # Medium: Memory leak + service dependency
        │   └── task3.py       # Hard: Multi-service cascading failure
        └── graders/
            ├── grader1.py
            ├── grader2.py
            └── grader3.py
```

---

## Environment Design

### Observation Space

Each observation returned by `reset()` and `step()` is a `CascadeObservation` with the following fields:

| Field | Type | Description |
|---|---|---|
| `alert_message` | `str` | PagerDuty-style alert string |
| `system_logs` | `List[str]` | Timestamped log lines from affected services |
| `available_runbooks` | `List[str]` | Runbooks the agent can select from |
| `current_step` | `int` | Current step in the episode |
| `steps_taken` | `List[str]` | History of actions taken so far |
| `episode_done` | `bool` | Whether the episode has ended |
| `affected_services` | `List[str]` | Services impacted by the incident |
| `severity_level` | `str` | `"low"` / `"medium"` / `"high"` / `"critical"` |
| `priority_level` | `str` | `"P1"` / `"P2"` / `"P3"` |
| `human_intervention_required` | `bool` | Whether human escalation is required |

### Action Space

Each action is a `CascadeAction` with the following fields:

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | One of the valid action types below |
| `action_value` | `str` | Free-text value for the action |
| `reasoning` | `str` | Agent's explanation for taking the action |

Valid action types:

| Action | Description |
|---|---|
| `investigate` | Gather more information about a service or log |
| `select_runbook` | Choose a runbook to apply |
| `execute_step` | Execute a specific remediation step |
| `escalate_to_human` | Escalate the incident to a human operator |
| `resolve` | Mark the incident as resolved |
| `rollback` | Roll back a previously executed step |

### Reward Function

Rewards are accumulated across the episode, providing dense signal for RL training.

| Event | Reward |
|---|---|
| Correct system identified | +0.20 |
| Correct runbook selected | +0.20 |
| Correct remediation step | +0.15 each |
| Incident fully resolved | +0.25 |
| Appropriate escalation | +0.15 |
| Correct priority identified | +0.10 |
| Wrong runbook selected | -0.10 |
| Unnecessary escalation | -0.10 |
| Failed to escalate when required | -0.20 |
| Wasted/redundant step | -0.05 |
| Rollback used | -0.05 |

Final score is clipped to `[0.0, 1.0]`.

---

## Tasks

### Task 1 — Easy: DB CPU Spike

**Scenario:** A database service is experiencing a CPU spike caused by a missing index on a high-traffic query.  
**Key challenge:** Identify the correct runbook and execute the fix in the correct order.  
**Priority:** P2 | **Human intervention required:** No | **Max steps:** 6  
**Target scores:** weak model 0.60+, strong model 0.85+

### Task 2 — Medium: Memory Leak + Service Dependency

**Scenario:** A memory leak in a backend service is causing cascading latency in a dependent API gateway.  
**Key challenge:** Identify root cause across two services and prioritize remediation correctly.  
**Priority:** P1 | **Human intervention required:** No | **Max steps:** 10  
**Target scores:** weak model 0.20–0.35, strong model 0.50–0.70

### Task 3 — Hard: Multi-Service Cascading Failure

**Scenario:** A network partition triggers failures across multiple interdependent microservices with a misleading CPU spike as a red herring.  
**Key challenge:** Triage correctly under noisy alerts, ignore the red herring, manage escalation, and restore services in the correct sequence.  
**Priority:** P1 | **Human intervention required:** Yes | **Max steps:** 15  
**Target scores:** weak model 0.05–0.15, strong model 0.20–0.35

---

## Baseline Scores

Baseline agent: `llama-3.3-70b-versatile` via Groq, run against the live HF Space.

| Task         | Model                  | Score | Steps | Success |
|--------------|------------------------|-------|-------|---------|
| task1_easy   | llama-3.3-70b-versatile | 0.650 | 5     | True    |
| task2_medium | llama-3.3-70b-versatile | 1.000 | 10    | True    |
| task3_hard   | llama-3.3-70b-versatile | 0.500 | 6     | True    |

---

## Grading

Each grader evaluates the agent's full action history at episode end and returns a float between `0.0` and `1.0`. Graders are fully deterministic — the same action history always produces the same score.

Grading criteria include correct runbook selection, remediation steps executed in order, appropriate escalation behavior, resolution within the step budget, and priority identification.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode, returns initial observation |
| `/step` | POST | Execute action, returns observation + reward + done + info |
| `/state` | GET | Return current environment state |

All endpoints accept an optional `task_id` query parameter (1, 2, or 3). Defaults to 1.

---

## Setup & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export API_BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=llama-3.3-70b-versatile
export HF_TOKEN=your_api_key_here
export CASCADE_ENV_URL=https://atconeyisland-cascade.hf.space

# Run baseline agent on all tasks
python inference.py

# Run all tasks with grading
python test_all.py

# Start environment server locally
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t cascade .
docker run -p 7860:7860 cascade
```

---

## Future Scope

**Observation space** — A `time_elapsed` field to track minutes since incident start, adding urgency pressure and requiring agents to balance investigation depth against time constraints.

**Action space** — A `request_more_logs` action allowing agents to request additional log data for iterative diagnosis.

**Reward function** — Refined grading logic through empirical evaluation on real incident patterns, improving sensitivity to differences in agent strategy quality.

---

## Team

**Huntrix**

| Member | Responsibility |
|---|---|
| Anvi Trivedi | Environment infrastructure, project setup, OpenEnv spec, state machine, reward function |
| Prachi Bhowal | Task definitions, grader logic, synthetic incident data, inference script |
| Mokshita VP | Dockerfile, Hugging Face Space deployment, pre-submission validator, final submission |
