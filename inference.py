"""
inference.py — Cascade RL Environment
======================================
Baseline agent script for the Cascade incident response environment.
Runs the agent through all 3 tasks and emits [START] [STEP] [END] logs.

Environment variables (never hardcoded):
    API_BASE_URL   The LLM API endpoint (injected by validator)
    MODEL_NAME     The model identifier
    API_KEY        API key (injected by validator)
    HF_TOKEN       Fallback API key

Stdout format (exact — do not modify field names or ordering):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
import time
from typing import List, Optional

from openai import OpenAI

from cascade_env.client import CascadeEnv
from cascade_env.models import CascadeAction

# ---------------------------------------------------------------------------
# Environment variables — no hardcoded defaults for API_BASE_URL or API_KEY
# ---------------------------------------------------------------------------
API_KEY      = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.environ["API_BASE_URL"]
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

if not API_KEY:
    print("ERROR: API_KEY or HF_TOKEN environment variable is required.", file=sys.stderr)
    sys.exit(1)

print(f"[CONFIG] API_BASE_URL={API_BASE_URL}")
print(f"[CONFIG] MODEL_NAME={MODEL_NAME}")
print(f"[CONFIG] Using OpenAI client")
print()

BENCHMARK               = "cascade"
SUCCESS_SCORE_THRESHOLD = 0.5
TEMPERATURE             = 0.3
MAX_TOKENS              = 300

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
    error_val    = error if error else "null"
    done_val     = str(done).lower()
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


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert on-call Site Reliability Engineer responding to a production incident.
    You will receive an alert message, system logs, and a list of available runbooks.

    At each step you must respond with EXACTLY this format (one line, no extra text):
        action_type::action_value

    Valid action_type values:
        investigate       — investigate a service or log. action_value = service name or keyword
        select_runbook    — select a runbook. action_value = exact runbook name from available_runbooks
        execute_step      — execute a remediation step. action_value = description of the step
        escalate_to_human — escalate to a human. action_value = reason for escalation
        resolve           — declare the incident resolved. action_value = brief resolution summary
        rollback          — roll back a change. action_value = what to roll back

    Rules:
        - Always investigate before selecting a runbook.
        - Select ONLY runbooks from the available_runbooks list.
        - If human_intervention_required is True, you MUST use escalate_to_human before resolve.
        - Do not repeat the same action twice.
        - Be decisive — do not waste steps.
        - Respond with ONLY the action line. No explanations, no extra text.

    Example responses:
        investigate::db-primary
        select_runbook::db-cpu-runbook
        execute_step::run explain on slow query
        execute_step::add missing index on transactions table
        resolve::missing index added, db-primary CPU returned to normal
""").strip()


def build_user_prompt(obs, step: int, history: List[str]) -> str:
    logs_block    = "\n".join(obs.system_logs) if obs.system_logs else "No logs available."
    runbooks_list = ", ".join(obs.available_runbooks) if obs.available_runbooks else "None"
    history_block = "\n".join(history[-5:]) if history else "None"
    human_note    = (
        "YES — you MUST use escalate_to_human before resolve."
        if obs.human_intervention_required
        else "No — resolve autonomously."
    )
    return textwrap.dedent(f"""
        INCIDENT ALERT:
        {obs.alert_message}

        AFFECTED SERVICES: {", ".join(obs.affected_services)}
        SEVERITY: {obs.severity_level}  |  PRIORITY: {obs.priority_level}
        HUMAN INTERVENTION REQUIRED: {human_note}

        SYSTEM LOGS:
        {logs_block}

        AVAILABLE RUNBOOKS: {runbooks_list}

        STEP: {step}
        PREVIOUS ACTIONS:
        {history_block}

        What is your next action? (respond with action_type::action_value only)
    """).strip()


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def get_agent_action(client: OpenAI, obs, step: int, history: List[str]) -> str:
    user_prompt = build_user_prompt(obs, step, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        if "::" not in text:
            return f"investigate::{text}"
        return text.split("\n")[0].strip()
    except Exception as exc:
        print(f"[DEBUG] Model request failed at step {step}: {exc}", flush=True)
        return "investigate::unknown"


# ---------------------------------------------------------------------------
# Single task runner
# ---------------------------------------------------------------------------
def run_task(client: OpenAI, task_name: str, env: CascadeEnv) -> dict:
    task_id     = TASK_NAME_TO_ID.get(task_name, 1)
    max_steps   = TASK_MAX_STEPS.get(task_name, 10)
    history:    List[str]   = []
    rewards:    List[float] = []
    steps_taken = 0
    score       = 0.0
    success     = False
    result      = None

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs  = env.reset(task_id=task_id)
        done = False

        for step in range(1, max_steps + 1):
            if done:
                break

            action_str   = get_agent_action(client, obs, step, history)
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
            reward      = result.reward or 0.01
            reward      = round(min(0.99, max(0.01, reward)), 4)
            done        = result.done
            steps_taken = step

            rewards.append(reward)
            history.append(f"Step {step}: {action_str}")

            log_step(step=step, action=action_str, reward=reward, done=done, error=None)

            if done:
                break

        score = result.reward if result else 0.01
        score = round(min(0.99, max(0.01, score)), 4)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} failed: {exc}", flush=True)
        score   = 0.01
        success = False

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task":    task_name,
        "score":   score,
        "steps":   steps_taken,
        "success": success,
    }


def main() -> None:
    client = OpenAI(
        base_url=os.environ["API_BASE_URL"],
        api_key=API_KEY
    )

    env_url = os.getenv("CASCADE_ENV_URL", "https://atconeyisland-cascade.hf.space")
    print(f"[CONFIG] Connecting to Cascade environment at {env_url}", flush=True)

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
            result = run_task(client, task_name, env)
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