---
title: Cascade RL Environment - Incident Response
emoji: 🚨
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
---

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

=======
title: Benchmark Environment Server
emoji: 📠
colorFrom: purple
colorTo: red
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Benchmark Environment

A simple test environment that echoes back messages. Perfect for testing the env APIs as well as demonstrating environment usage patterns.

## Quick Start

The simplest way to use the Benchmark environment is through the `BenchmarkEnv` class:

```python
from benchmark import BenchmarkAction, BenchmarkEnv

try:
    # Create environment from Docker image
    benchmarkenv = BenchmarkEnv.from_docker_image("benchmark-env:latest")

    # Reset
    result = benchmarkenv.reset()
    print(f"Reset: {result.observation.echoed_message}")

    # Send multiple messages
    messages = ["Hello, World!", "Testing echo", "Final message"]

    for msg in messages:
        result = benchmarkenv.step(BenchmarkAction(message=msg))
        print(f"Sent: '{msg}'")
        print(f"  → Echoed: '{result.observation.echoed_message}'")
        print(f"  → Length: {result.observation.message_length}")
        print(f"  → Reward: {result.reward}")

finally:
    # Always clean up
    benchmarkenv.close()
```

That's it! The `BenchmarkEnv.from_docker_image()` method handles:
- Starting the Docker container
- Waiting for the server to be ready
- Connecting to the environment
- Container cleanup when you call `close()`

## Building the Docker Image

Before using the environment, you need to build the Docker image:

```bash
# From project root
docker build -t benchmark-env:latest -f server/Dockerfile .
```

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --namespace my-org --private
```

The `openenv push` command will:
1. Validate that the directory is an OpenEnv environment (checks for `openenv.yaml`)
2. Prepare a custom build for Hugging Face Docker space (enables web interface)
3. Upload to Hugging Face (ensuring you're logged in)

### Prerequisites

- Authenticate with Hugging Face: The command will prompt for login if not already authenticated

### Options

- `--directory`, `-d`: Directory containing the OpenEnv environment (defaults to current directory)
- `--repo-id`, `-r`: Repository ID in format 'username/repo-name' (defaults to 'username/env-name' from openenv.yaml)
- `--base-image`, `-b`: Base Docker image to use (overrides Dockerfile FROM)
- `--private`: Deploy the space as private (default: public)

### Examples

```bash
# Push to your personal namespace (defaults to username/env-name from openenv.yaml)
openenv push

# Push to a specific repository
openenv push --repo-id my-org/my-env

# Push with a custom base image
openenv push --base-image ghcr.io/meta-pytorch/openenv-base:latest

# Push as a private space
openenv push --private

# Combine options
openenv push --repo-id my-org/my-env --base-image custom-base:latest --private
```

After deployment, your space will be available at:
`https://huggingface.co/spaces/<repo-id>`

The deployed space includes:
- **Web Interface** at `/web` - Interactive UI for exploring the environment
- **API Documentation** at `/docs` - Full OpenAPI/Swagger interface
- **Health Check** at `/health` - Container health monitoring

## Environment Details

### Action
**BenchmarkAction**: Contains a single field
- `message` (str) - The message to echo back

### Observation
**BenchmarkObservation**: Contains the echo response and metadata
- `echoed_message` (str) - The message echoed back
- `message_length` (int) - Length of the message
- `reward` (float) - Reward based on message length (length × 0.1)
- `done` (bool) - Always False for echo environment
- `metadata` (dict) - Additional info like step count

### Reward
The reward is calculated as: `message_length × 0.1`
- "Hi" → reward: 0.2
- "Hello, World!" → reward: 1.3
- Empty message → reward: 0.0

## Advanced Usage

### Connecting to an Existing Server

If you already have a Benchmark environment server running, you can connect directly:

```python
from benchmark import BenchmarkEnv

# Connect to existing server
benchmarkenv = BenchmarkEnv(base_url="<ENV_HTTP_URL_HERE>")

# Use as normal
result = benchmarkenv.reset()
result = benchmarkenv.step(BenchmarkAction(message="Hello!"))
```

Note: When connecting to an existing server, `benchmarkenv.close()` will NOT stop the server.

## Development & Testing

### Direct Environment Testing

Test the environment logic directly without starting the HTTP server:

```bash
# From the server directory
python3 server/benchmark_environment.py
```

This verifies that:
- Environment resets correctly
- Step executes actions properly
- State tracking works
- Rewards are calculated correctly

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

## Project Structure

```
benchmark/
├── .dockerignore         # Docker build exclusions
├── __init__.py            # Module exports
├── README.md              # This file
├── openenv.yaml           # OpenEnv manifest
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependencies (generated)
├── client.py              # BenchmarkEnv client implementation
├── models.py              # Action and Observation models
└── server/
    ├── __init__.py        # Server module exports
    ├── benchmark_environment.py  # Core environment logic
    ├── app.py             # FastAPI application
    └── Dockerfile         # Container image definition
```
>>>>>>> feat/dockerfile-requirements
