# 🚨 Cascade — Incident Response Commander RL Environment

> A reinforcement learning environment for training autonomous IT incident response agents, built for Hackathon Round 1.

---

## 📌 Overview

**Cascade** is an OpenEnv-compatible RL environment that simulates real-world IT incident response scenarios. An agent acts as an *Incident Response Commander*, diagnosing and resolving production incidents by selecting runbooks, executing remediation steps, investigating anomalies, and escalating when necessary.

The environment is designed to evaluate whether an LLM-based agent can handle progressively complex SRE (Site Reliability Engineering) tasks — from straightforward single-service incidents to multi-service cascading failures.

---

## 🎯 Motivation: Why This Benchmark Exists

**The gap:** Current RL benchmarks are dominated by game-playing (Atari, Dota 2, StarCraft) and robotics simulation. LLM-based agents now operate at human expert level on many tasks, yet we lack standardized benchmarks for **real-world operational decision-making under uncertainty**.

**Why it matters:**

1. **Incident response is genuinely hard.** Unlike turn-based games, incident response requires:
   - Partial observability (logs are noisy; ground truth is hidden)  
   - Sequential reasoning under time pressure  
   - Cost-aware decisions (escalation is expensive; wrong fixes are costly)  
   - Human-in-the-loop judgment (knowing *when* to escalate, not just *if*)

2. **Production AI is now feasible.** LLM agents can parse alerts, reason about dependencies, and execute remediation. But we have no standard way to measure agent performance on real operational tasks at scale.

3. **Cascading failures are the hard case.** Multi-service incidents have exponential complexity. Existing task-specific agents fail when services interact unexpectedly. This benchmark directly tests whether an agent can reason about complex system topology.

4. **Impact & scale.** Incident response touches billions of users. Every major cloud provider, SaaS platform, and fintech company faces this problem daily. A 5% improvement in MTTR (Mean Time To Resolution) translates to millions in downtime costs prevented.

5. **Reproducibility gap.** Existing incident response research uses proprietary incident data or toy simulators. Cascade provides an **open, fair, reproducible standard** for measuring agent performance on this domain.

---

## 🗂️ Project Structure

```
cascade/
├── src/
│   └── cascade_env/
│       ├── __init__.py
│       ├── environment.py            # Core environment (step, reset, render)
│       ├── models.py                 # Pydantic models for observations, actions, rewards
│       ├── server.py                 # Environment server
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── task1.py              # DB CPU spike (single service)
│       │   ├── task2.py              # Memory leak + service dependency
│       │   └── task3.py              # Multi-service cascading failure
│       └── graders/
│           ├── __init__.py
│           ├── grader1.py            # Grader for Task 1
│           ├── grader2.py            # Grader for Task 2
│           └── grader3.py            # Grader for Task 3
├── server/
│   └── app.py                        # Server entrypoint
├── inference.py                      # Baseline agent script
├── pyproject.toml
├── openenv.yaml
├── README.md
└── test_all.py
```

---

## 🧠 Environment Design

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

**Note:** The `StepResult` also includes `info` (a dict) containing additional metadata.

### Action Space

Each action is a dict with the following fields:

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | One of the valid action types below |
| `action_value` | `str` | Free-text value for the action |
| `reasoning` | `str` | Agent's explanation for taking the action |

**Valid action types:**

- `select_runbook` — Choose a runbook to apply
- `execute_step` — Execute a specific remediation step
- `investigate` — Gather more information
- `escalate_to_human` — Escalate the incident to a human operator
- `resolve` — Mark the incident as resolved
- `rollback` — Rollback a previously executed step

---

## 📋 Tasks

### Task 1 — Easy: DB CPU Spike
**Scenario:** A database service is experiencing a CPU spike caused by a missing index on a high-traffic query.  
**Key challenge:** Identify the correct runbook and execute the fix in the right order.  
**Max steps:** 6

### Task 2 — Medium: Memory Leak + Service Dependency
**Scenario:** A memory leak in a backend service is causing cascading latency in a dependent API gateway.  
**Key challenge:** Identify root cause across two services and prioritize remediation correctly.  
**Max steps:** 10

### Task 3 — Hard: Multi-Service Cascading Failure
**Scenario:** A network partition triggers failures across multiple interdependent microservices with conflicting alerts.  
**Key challenge:** Triage correctly under noisy alerts, manage escalation, and restore services in the right sequence.  
**Max steps:** 15

---

## 📊 Baseline Scores

These are the baseline scores achieved on all three tasks:

| Task | Score |
|---|---|
| `task1_easy` | **1.000** |
| `task2_medium` | **1.000** |
| `task3_hard` | **1.000** |

> All three tasks achieved a perfect score of **1.0** at baseline. ✅

---

## 🏆 Grading

Each grader evaluates the agent's action history at the end of an episode and returns a float score between `0.0` and `1.0`.

Grading criteria (applied across all tasks, weighted by difficulty):

| Criterion | Description |
|---|---|
| **Correct runbook selected** | Agent chose the right runbook for the incident type |
| **Steps executed in order** | Remediation steps were taken in the correct sequence |
| **No unnecessary escalation** | Agent did not escalate when it could self-resolve |
| **Resolution within step budget** | Incident resolved before hitting `max_steps` |
| **Accurate reasoning** | `reasoning` fields reflect understanding of the incident |

> ⚠️ **Graders are fully deterministic** — same action history always produces the same score.

---

## 🚀 Setup & Running

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
## � Future Scope

We plan to enhance Cascade with the following improvements:

### Observation Space Enhancements
- **`time_elapsed`** — Track minutes elapsed since incident start to add urgency pressure. Agents will need to balance thorough investigation with time constraints, making decisions more realistic and challenging.

### Action Space Extensions
- **`request_more_logs`** — Allow agents to request additional log data for deeper investigation. This enables iterative diagnosis and more nuanced decision-making around information gathering vs. action execution.

### Reward Function Optimization
- **Intensive training & calibration** — Refine grading logic through extensive empirical evaluation on real incident patterns. This will improve accuracy of the reward signal and make the benchmark more sensitive to subtle differences in agent strategy quality.

---

## 👥 Team: Huntrix

| Member | Responsibility |
|---|---|
| Anvi Trivedi | Environment infrastructure, project setup, OpenEnv spec, state machine, reward function, git |
| Prachi Bhowal | 3 task definitions, all grader logic, synthetic incident data, inference.py |
| Mokshita VP | Dockerfile, HF Space, deployment, pre-submission validator, final submission |

---

