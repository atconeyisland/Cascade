"""
inference.py — Cascade RL Environment
======================================
Baseline agent script for the Cascade incident response environment.
Runs the agent through all 3 tasks and emits [START] [STEP] [END] logs.

Environment variables (never hardcoded):
    API_BASE_URL   The LLM API endpoint
    MODEL_NAME     The model identifier
    HF_TOKEN       Hugging Face / API key

Stdout format (exact — do not modify field names or ordering):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import asyncio
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from cascade_env.client import CascadeEnv, CascadeAction

# ---------------------------------------------------------------------------
# Environment variables — never hardcoded
# ---------------------------------------------------------------------------
API_KEY       = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL  = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME    = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
IMAGE_NAME    = os.getenv("LOCAL_IMAGE_NAME")

# ---------------------------------------------------------------------------
# Validate required environment variables
# ---------------------------------------------------------------------------
if not API_KEY:
    print(
        "ERROR: HF_TOKEN environment variable is required.\n"
        "Set your API key: export HF_TOKEN='your_api_key_here'\n"
        "Alternatives: export API_KEY='your_api_key_here'",
        file=__import__('sys').stderr
    )
    __import__('sys').exit(1)

if not API_BASE_URL:
    print(
        "ERROR: API_BASE_URL environment variable is required.\n"
        "Example: export API_BASE_URL='https://api.openai.com/v1'",
        file=__import__('sys').stderr
    )
    __import__('sys').exit(1)

if not MODEL_NAME:
    print(
        "ERROR: MODEL_NAME environment variable is required.\n"
        "Example: export MODEL_NAME='gpt-4o'",
        file=__import__('sys').stderr
    )
    __import__('sys').exit(1)

print(f"[CONFIG] API_BASE_URL={API_BASE_URL}")
print(f"[CONFIG] MODEL_NAME={MODEL_NAME}")
print(f"[CONFIG] Using OpenAI client")
print()

BENCHMARK     = "cascade"
SUCCESS_SCORE_THRESHOLD = 0.5  # episode is a success if score >= 0.5

# Max steps per task — kept low to stay under 20 min total
TASK_MAX_STEPS = {
    "task1_easy":   6,
    "task2_medium": 10,
    "task3_hard":   15,
}

TEMPERATURE = 0.3   # lower = more deterministic = better for incident response
MAX_TOKENS  = 300

# ---------------------------------------------------------------------------
# Stdout log functions — exact field names, exact ordering, do not change
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    # Sanitise action string — no newlines allowed on a single [STEP] line
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
# System prompt — tells the model how to respond for Cascade tasks
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
        rollback          — roll back a change. action_value = what to roll back (use sparingly)

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


# ---------------------------------------------------------------------------
# Prompt builder — constructs user message from current observation
# ---------------------------------------------------------------------------
def build_user_prompt(obs, step: int, history: List[str]) -> str:
    logs_block    = "\n".join(obs.system_logs) if obs.system_logs else "No logs available."
    runbooks_list = ", ".join(obs.available_runbooks) if obs.available_runbooks else "None"
    history_block = "\n".join(history[-5:]) if history else "None"

    human_note = (
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
# LLM call — uses OpenAI client with env var credentials
# ---------------------------------------------------------------------------
def get_agent_action(
    client: OpenAI,
    obs,
    step: int,
    history: List[str],
) -> str:
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
        # Validate format — must contain "::"
        if "::" not in text:
            return f"investigate::{text}"
        # Take only the first line in case model adds extra text
        return text.split("\n")[0].strip()
    except Exception as exc:
        print(f"[DEBUG] Model request failed at step {step}: {exc}", flush=True)
        return "investigate::unknown"


# ---------------------------------------------------------------------------
# Single task runner
# ---------------------------------------------------------------------------
async def run_task(client: OpenAI, task_name: str, env: CascadeEnv) -> dict:
    max_steps = TASK_MAX_STEPS.get(task_name, 10)
    history:  List[str]  = []
    rewards:  List[float] = []
    steps_taken = 0
    score   = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset environment for this task
        result = await env.reset(task=task_name)
        obs    = result.observation

        for step in range(1, max_steps + 1):
            if result.done:
                break

            # Get action from LLM agent
            action_str = get_agent_action(client, obs, step, history)

            # Parse action_type and action_value
            parts        = action_str.split("::", 1)
            action_type  = parts[0].strip()
            action_value = parts[1].strip() if len(parts) > 1 else ""

            # Step the environment
            result = await env.step(CascadeAction(
                action_type=action_type,
                action_value=action_value,
                reasoning=f"Step {step}: {action_str}",
            ))

            obs    = result.observation
            reward = result.reward or 0.0
            done   = result.done
            error  = getattr(result, "error", None)

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(f"Step {step}: {action_str}")

            if done:
                break

        # Final score comes from the grader via env
        score   = getattr(result, "score", sum(rewards))
        score   = round(min(max(float(score), 0.0), 1.0), 4)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} failed with exception: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {"task": task_name, "score": score, "steps": steps_taken, "success": success}


# ---------------------------------------------------------------------------
# Main — runs all 3 tasks sequentially
# ---------------------------------------------------------------------------
async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Connect to the Cascade environment running on HF Spaces
    env = await CascadeEnv.from_docker_image(IMAGE_NAME)

    tasks = ["task1_easy", "task2_medium", "task3_hard"]
    results = []

    try:
        for task_name in tasks:
            result = await run_task(client, task_name, env)
            results.append(result)
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)

    # Summary
    print("\n[DEBUG] === BASELINE SCORES (save these for README) ===", flush=True)
    for r in results:
        print(
            f"[DEBUG] {r['task']}: score={r['score']:.3f} "
            f"steps={r['steps']} success={r['success']}",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
