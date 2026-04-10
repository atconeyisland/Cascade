---
title: Cascade RL Environment - Incident Response
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# Cascade — Incident Response Commander RL Environment

## Overview

Cascade is an OpenEnv-compatible reinforcement learning environment that simulates real-world IT incident response scenarios. An agent acts as an Incident Response Commander, diagnosing and resolving production incidents by selecting runbooks, executing remediation steps, investigating anomalies, and escalating when necessary.

The environment is designed to evaluate whether an LLM-based agent can handle progressively complex SRE (Site Reliability Engineering) tasks — from straightforward single-service incidents to multi-service cascading failures.

---

## Motivation

Current RL benchmarks are dominated by game-playing (Atari, Dota 2, StarCraft) and robotics simulation. LLM-based agents now operate at human-expert level on many tasks, yet standardized benchmarks for real-world operational decision-making under uncertainty remain scarce. Cascade addresses this gap.

**Why incident response?**

Incident response is a genuinely difficult domain. Unlike turn-based games, it requires partial observability (logs are noisy; ground truth is hidden), sequential reasoning under time pressure, cost-aware decisions (escalation is expensive; incorrect fixes carry penalties), and human-in-the-loop judgment around when to escalate.

Cascading failures represent the hardest case — multi-service incidents have exponential complexity, and task-specific agents routinely fail when services interact unexpectedly. Cascade directly tests whether an agent can reason about complex system topology.

Beyond research, incident response has significant practical impact. Every major cloud provider, SaaS platform, and fintech company faces this problem daily. A measurable improvement in Mean Time To Resolution (MTTR) translates directly to reduced downtime costs at scale.

Cascade also addresses a reproducibility gap: existing incident response research relies on proprietary data or toy simulators. This benchmark provides an open, fair, and reproducible standard for the domain.

---

## Project Structure

```
Directory structure:
└── Cascade/
    ├── build/
    │   └── lib/
    │       └── benchmark/
    │           ├── client.py
    │           ├── models.py
    │           ├── server/
    │           │   ├── app.py
    │           │   ├── benchmark_environment.py
    │           │   └── __init__.py
    │           └── __init__.py
    ├── Dockerfile
    ├── inference.py
    ├── models.py
    ├── openenv.yaml
    ├── openenv_benchmark.egg-info/
    │   ├── dependency_links.txt
    │   ├── entry_points.txt
    │   ├── PKG-INFO
    │   ├── requires.txt
    │   ├── SOURCES.txt
    │   └── top_level.txt
    ├── pyproject.toml
    ├── README.md
    ├── requirements.txt
    ├── run_server.py
    ├── server/
    │   ├── app.py
    │   ├── benchmark_environment.py
    │   ├── requirements.txt
    │   ├── __init__.py
    │   └── __pycache__/
    │       ├── app.cpython-313.pyc
    │       ├── benchmark_environment.cpython-313.pyc
    │       └── __init__.cpython-313.pyc
    ├── spaces.hf.yaml
    ├── src/
    │   ├── cascade_env/
    │   │   ├── client.py
    │   │   ├── environment.py
    │   │   ├── graders/
    │   │   │   ├── grader1.py
    │   │   │   ├── grader2.py
    │   │   │   ├── grader3.py
    │   │   │   ├── __init__.py
    │   │   │   └── __pycache__/
    │   │   │       ├── grader1.cpython-313.pyc
    │   │   │       ├── grader2.cpython-313.pyc
    │   │   │       ├── grader3.cpython-313.pyc
    │   │   │       └── __init__.cpython-313.pyc
    │   │   ├── models.py
    │   │   ├── server.py
    │   │   ├── tasks/
    │   │   │   ├── task1.py
    │   │   │   ├── task2.py
    │   │   │   ├── task3.py
    │   │   │   ├── __init__.py
    │   │   │   └── __pycache__/
    │   │   │       ├── task1.cpython-313.pyc
    │   │   │       ├── task2.cpython-313.pyc
    │   │   │       ├── task3.cpython-313.pyc
    │   │   │       └── __init__.cpython-313.pyc
    │   │   ├── __init__.py
    │   │   └── __pycache__/
    │   │       ├── client.cpython-313.pyc
    │   │       ├── environment.cpython-313.pyc
    │   │       ├── models.cpython-313.pyc
    │   │       └── __init__.cpython-313.pyc
    │   └── cascade_env.egg-info/
    │       ├── dependency_links.txt
    │       ├── entry_points.txt
    │       ├── PKG-INFO
    │       ├── requires.txt
    │       ├── SOURCES.txt
    │       └── top_level.txt
    ├── test_all.py
    ├── test_client.py
    ├── test_concurrency.py
    ├── uv.lock
    ├── validate_local.py
    └── __init__.py
```

---

## Environment Design

### Observation Space

Each observation returned by `step()` is a `StepResult` containing a `CascadeObservation` dict with the following fields:

| Field | Type | Description |
|---|---|---|
| `alert_message` | `str` | PagerDuty-style alert string |
| `system_logs` | `List[str]` | Relevant log lines |
| `available_runbooks` | `List[str]` | Runbooks available for this incident |
| `current_step` | `int` | Current step in the episode |
| `steps_taken` | `List[str]` | JSON-encoded history of past actions |
| `episode_done` | `bool` | Whether the episode has ended |
| `affected_services` | `List[str]` | Services impacted by the incident |
| `severity_level` | `str` | `"low"` / `"medium"` / `"high"` / `"critical"` |
| `priority_level` | `str` | `"P1"` – `"P3"` |
| `human_intervention_required` | `bool` | Whether human escalation is needed |

The `StepResult` also includes an `info` dict containing additional metadata.

### Action Space

Each action is a dict with the following fields:

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | One of the valid action types listed below |
| `action_value` | `str` | Free-text value for the action |
| `reasoning` | `str` | Agent's explanation for taking the action |

**Valid action types:**

| Action | Description |
|---|---|
| `select_runbook` | Choose a runbook to apply |
| `execute_step` | Execute a specific remediation step |
| `investigate` | Gather more information |
| `escalate_to_human` | Escalate the incident to a human operator |
| `resolve` | Mark the incident as resolved |
| `rollback` | Rollback a previously executed step |

---

## Tasks

### Task 1 — Easy: DB CPU Spike

**Scenario:** A database service is experiencing a CPU spike caused by a missing index on a high-traffic query.  
**Key challenge:** Identify the correct runbook and execute the fix in the correct order.  
**Max steps:** 6

### Task 2 — Medium: Memory Leak + Service Dependency

**Scenario:** A memory leak in a backend service is causing cascading latency in a dependent API gateway.  
**Key challenge:** Identify root cause across two services and prioritize remediation correctly.  
**Max steps:** 10

### Task 3 — Hard: Multi-Service Cascading Failure

**Scenario:** A network partition triggers failures across multiple interdependent microservices with conflicting alerts.  
**Key challenge:** Triage correctly under noisy alerts, manage escalation, and restore services in the correct sequence.  
**Max steps:** 15

---

## Baseline Scores

| Task | Score |
|---|---|
| `task1_easy` | 1.000 |
| `task2_medium` | 1.000 |
| `task3_hard` | 1.000 |

All three tasks achieved a perfect score of 1.0 at baseline.

---

## Grading

Each grader evaluates the agent's action history at the end of an episode and returns a float score between `0.0` and `1.0`. Graders are fully deterministic — the same action history always produces the same score.

| Criterion | Description |
|---|---|
| Correct runbook selected | Agent chose the appropriate runbook for the incident type |
| Steps executed in order | Remediation steps were taken in the correct sequence |
| No unnecessary escalation | Agent did not escalate when self-resolution was possible |
| Resolution within step budget | Incident resolved before reaching `max_steps` |
| Accurate reasoning | `reasoning` fields reflect genuine understanding of the incident |

---

## Setup & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run baseline agent on all tasks
python inference.py

# Run all tasks with grading
python test_all.py

# Start environment server
python -m uvicorn server.app:app --reload
```

---

## Future Scope

The following enhancements are planned for subsequent iterations:

**Observation space** — A `time_elapsed` field to track minutes since incident start, adding urgency pressure and requiring agents to balance investigation depth against time constraints.

**Action space** — A `request_more_logs` action allowing agents to request additional log data for iterative diagnosis, enabling more nuanced decision-making around information gathering.

**Reward function** — Refined grading logic through empirical evaluation on real incident patterns, improving the accuracy of the reward signal and making the benchmark more sensitive to differences in agent strategy quality.

---

## Team

**Huntrix**

| Member | Responsibility |
|---|---|
| Anvi Trivedi | Environment infrastructure, project setup, OpenEnv spec, state machine, reward function |
| Prachi Bhowal | Task definitions, grader logic, synthetic incident data, inference script |
| Mokshita VP | Dockerfile, Hugging Face Space deployment, pre-submission validator, final submission |
