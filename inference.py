"""
inference.py — Cascade RL Environment
======================================
Baseline agent script for the Cascade incident response environment.
Runs the agent through all 3 tasks and emits [START] [STEP] [END] logs.

Uses heuristic-based action selection (no LLM required).
"""

import os
import sys
import textwrap
import time
from typing import List, Optional

from cascade_env.client import CascadeEnv
from cascade_env.models import CascadeAction

print(f"[CONFIG] Using heuristic-based agent (no LLM)")
print()

BENCHMARK               = "cascade"
SUCCESS_SCORE_THRESHOLD = 0.5

TASK_MAX_STEPS = {
    "task1_easy":   6,
    "task2_medium": 10,
    "task3_hard":   15,
}

TASK_NAME_TO_ID = {
    "task1_easy":   1,
    "task2_medium": 2,
    "task3_hard":   3,
}


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val   = error if error else "null"
    done_val    = str(done).lower()
    action_clean = action.replace("\n", " ").replace("\r", "")
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def get_agent_action(obs, step: int, history: List[str]) -> str:
    """
    Heuristic agent: selects actions based on rules and observation state.
    No LLM required — deterministic and fast.
    """
    # Prefer investigating before selecting runbooks
    if step == 1:
        if obs.affected_services:
            service = obs.affected_services[0]
            return f"investigate::{service}"
        return "investigate::incident"
    
    
    if "select_runbook" not in " ".join(history):
        if obs.available_runbooks:
            runbook = obs.available_runbooks[0]
            return f"select_runbook::{runbook}"
    
    if obs.human_intervention_required and "escalate_to_human" not in " ".join(history):
        return f"escalate_to_human::critical_issue_requires_human_expertise"
    
    if step > 2:
        return "execute_step::apply_selected_remediation_steps"
    
    return "resolve::incident_addressed_by_automation"



def run_task(task_name: str, env: CascadeEnv) -> dict:
    task_id    = TASK_NAME_TO_ID.get(task_name, 1)
    max_steps  = TASK_MAX_STEPS.get(task_name, 10)
    history:   List[str]   = []
    rewards:   List[float] = []
    steps_taken = 0
    score       = 0.0
    success     = False

    log_start(task=task_name, env=BENCHMARK, model="heuristic-agent")

    try:
        obs  = env.reset(task_id=task_id)
        done = False

        for step in range(1, max_steps + 1):
            if done:
                break

            action_str   = get_agent_action(obs, step, history)
            parts        = action_str.split("::", 1)
            action_type  = parts[0].strip()
            action_value = parts[1].strip() if len(parts) > 1 else ""

            result = env.step(
                CascadeAction(
                    action_type=action_type,
                    action_value=action_value,
                    reasoning=f"Step {step}: {action_str}",
                ),
                task_id=task_id,
            )

            obs         = result.observation
            reward      = result.reward or 0.0
            done        = result.done
            steps_taken = step

            rewards.append(reward)
            history.append(f"Step {step}: {action_str}")

            log_step(step=step, action=action_str, reward=reward, done=done, error=None)

            if done:
                break

        # Use final grader score from last result, not sum of step rewards
        score   = float(getattr(result, "score", sum(rewards)))
        score   = round(min(max(score, 0.0), 1.0), 4)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} failed: {exc}", flush=True)
        score   = 0.0
        success = False

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task":    task_name,
        "score":   score,
        "steps":   steps_taken,
        "success": success,
    }


def main() -> None:
    env_url = os.getenv("CASCADE_ENV_URL", "http://localhost:8000")

    print(f"[CONFIG] Connecting to Cascade environment at {env_url}", flush=True)

    # Wait for server to be ready
    max_retries = 30
    env = None
    for attempt in range(max_retries):
        try:
            env = CascadeEnv(base_url=env_url)
            health = env.health()
            print(f"[CONFIG] Environment health check passed: {health}", flush=True)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[DEBUG] Waiting for environment... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(1)
            else:
                print(f"ERROR: Could not connect after {max_retries} attempts: {e}", file=sys.stderr)
                sys.exit(1)

    tasks   = ["task1_easy", "task2_medium", "task3_hard"]
    results = []

    try:
        for task_name in tasks:
            result = run_task(task_name, env)
            results.append(result)
    finally:
        try:
            env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)

    print("\n[DEBUG] === BASELINE SCORES ===", flush=True)
    for r in results:
        print(
            f"[DEBUG] {r['task']}: score={r['score']:.3f} "
            f"steps={r['steps']} success={r['success']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
