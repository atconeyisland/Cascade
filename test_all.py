import sys
sys.path.insert(0, 'src')
from cascade_env.environment import CascadeEnvironment
from cascade_env.models import ActionType, CascadeAction
from cascade_env.graders import grader1, grader2, grader3

PASS = "OK"
FAIL = "FAIL"

def check(condition, message):
    status = PASS if condition else FAIL
    print(f"  [{status}] {message}")
    return condition

all_passed = True

print("\n" + "=" * 55)
print("1. GRADER VARIANCE TEST")
print("=" * 55)

tests = [
    {
        "grader": grader1, "task_id": 1,
        "wrong": ("wrong-service", "wrong-runbook"),
        "partial_investigate": "database",
        "partial_runbook": "db-cpu-runbook",
        "perfect_steps": [
            ("investigate", "database"),
            ("select_runbook", "db-cpu-runbook"),
            ("execute_step", "run explain on slow query"),
            ("execute_step", "identify missing index"),
            ("execute_step", "add index"),
            ("resolve", "done"),
        ]
    },
    {
        "grader": grader2, "task_id": 2,
        "wrong": ("wrong-service", "wrong-runbook"),
        "partial_investigate": "auth-service",
        "partial_runbook": "memory-runbook",
        "perfect_steps": [
            ("investigate", "auth-service"),
            ("select_runbook", "memory-runbook"),
            ("execute_step", "drain connections"),
            ("execute_step", "restart auth-service"),
            ("execute_step", "preserve sessions"),
            ("resolve", "done"),
        ]
    },
    {
        "grader": grader3, "task_id": 3,
        "wrong": ("wrong-service", "wrong-runbook"),
        "partial_investigate": "network",
        "partial_runbook": "network-runbook",
        "perfect_steps": [
            ("investigate", "network"),
            ("select_runbook", "network-runbook"),
            ("execute_step", "failover inventory-service"),
            ("execute_step", "failover order-service"),
            ("execute_step", "failover notification-service"),
            ("escalate_to_human", "P1 incident requires human sign-off"),
            ("resolve", "done"),
        ]
    },
]

action_map = {
    "investigate": ActionType.INVESTIGATE,
    "select_runbook": ActionType.SELECT_RUNBOOK,
    "execute_step": ActionType.EXECUTE_STEP,
    "escalate_to_human": ActionType.ESCALATE_TO_HUMAN,
    "resolve": ActionType.RESOLVE,
    "rollback": ActionType.ROLLBACK,
}

for t in tests:
    grader = t["grader"]
    task_id = t["task_id"]
    print(f"\n  Task {task_id}:")

    env = CascadeEnvironment(task_id=task_id)

    # Run 1 — wrong answer
    env.reset()
    env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value=t["wrong"][0], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.SELECT_RUNBOOK, action_value=t["wrong"][1], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.RESOLVE, action_value="done", reasoning="test"))
    score_wrong = grader.grade(env.steps_taken, env.last_observation)

    # Run 2 — partial answer
    env.reset()
    env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value=t["partial_investigate"], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.SELECT_RUNBOOK, action_value=t["partial_runbook"], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.RESOLVE, action_value="done", reasoning="test"))
    score_partial = grader.grade(env.steps_taken, env.last_observation)

    # Run 3 — perfect answer
    env.reset()
    for atype, aval in t["perfect_steps"]:
        env.step(CascadeAction(action_type=action_map[atype], action_value=aval, reasoning="test"))
    score_perfect = grader.grade(env.steps_taken, env.last_observation)

    # Run 4 — destructive action
    env.reset()
    env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value=t["partial_investigate"], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.EXECUTE_STEP, action_value="drop table", reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.RESOLVE, action_value="done", reasoning="test"))
    score_destructive = grader.grade(env.steps_taken, env.last_observation)

    # Run 5 — rollback used
    env.reset()
    env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value=t["partial_investigate"], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.SELECT_RUNBOOK, action_value=t["partial_runbook"], reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.ROLLBACK, action_value="undo last", reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.RESOLVE, action_value="done", reasoning="test"))
    score_rollback = grader.grade(env.steps_taken, env.last_observation)

    # Run 6 — repeat same action 5 times (thrashing)
    env.reset()
    for _ in range(5):
        env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value="wrong", reasoning="test"))
    env.step(CascadeAction(action_type=ActionType.RESOLVE, action_value="done", reasoning="test"))
    score_thrash = grader.grade(env.steps_taken, env.last_observation)

    print(f"    Wrong:       {score_wrong}")
    print(f"    Partial:     {score_partial}")
    print(f"    Perfect:     {score_perfect}")
    print(f"    Destructive: {score_destructive}")
    print(f"    Rollback:    {score_rollback}")
    print(f"    Thrashing:   {score_thrash}")

    r1 = check(0.0 <= score_wrong <= 1.0, f"Wrong score in 0.0-1.0 range: {score_wrong}")
    r2 = check(0.0 <= score_partial <= 1.0, f"Partial score in 0.0-1.0 range: {score_partial}")
    r3 = check(0.0 <= score_perfect <= 1.0, f"Perfect score in 0.0-1.0 range: {score_perfect}")
    r4 = check(score_wrong != score_partial, f"Wrong != Partial (variance exists)")
    r5 = check(score_partial < score_perfect, f"Partial < Perfect (difficulty gradient)")
    r6 = check(score_destructive <= score_partial, f"Destructive <= Partial (penalty works)")
    all_passed = all_passed and all([r1, r2, r3, r4, r5, r6])


print("\n" + "=" * 55)
print("2. EPISODE BOUNDARY TEST")
print("=" * 55)

for task_id in [1, 2, 3]:
    print(f"\n  Task {task_id}:")
    env = CascadeEnvironment(task_id=task_id)

    obs = env.reset()
    r1 = check(obs.current_step == 0, "reset() current_step == 0")
    r2 = check(obs.steps_taken == [], "reset() steps_taken is empty")
    r3 = check(obs.episode_done == False, "reset() episode_done == False")

    env.reset()
    env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value="test", reasoning="test"))
    result = env.step(CascadeAction(action_type=ActionType.RESOLVE, action_value="done", reasoning="test"))
    r4 = check(result.done == True, "RESOLVE sets done=True")

    env.reset()
    for _ in range(15):
        result = env.step(CascadeAction(action_type=ActionType.INVESTIGATE, action_value="test", reasoning="test"))
    r5 = check(result.done == True, "Max steps sets done=True")

    obs = env.reset()
    r6 = check(obs.current_step == 0, "reset() after done clears current_step")
    r7 = check(obs.steps_taken == [], "reset() after done clears steps_taken")
    r8 = check(env.accumulated_reward == 0.0, "reset() after done clears accumulated_reward")

    all_passed = all_passed and all([r1, r2, r3, r4, r5, r6, r7, r8])


print("\n" + "=" * 55)
print("3. REWARD RANGE TEST")
print("=" * 55)

for task_id in [1, 2, 3]:
    print(f"\n  Task {task_id}:")
    env = CascadeEnvironment(task_id=task_id)
    env.reset()
    rewards = []
    for i in range(10):
        result = env.step(CascadeAction(
            action_type=ActionType.INVESTIGATE,
            action_value=f"service-{i}",
            reasoning="test"
        ))
        rewards.append(result.reward)
    r1 = check(all(0.0 <= r <= 1.0 for r in rewards), f"All step rewards in 0.0-1.0: {rewards[:3]}...")
    all_passed = all_passed and r1

# ─── FINAL RESULT ───
print("\n" + "=" * 55)
if all_passed:
    print("ALL TESTS PASSED — ready for openenv validate")
else:
    print("SOME TESTS FAILED — fix before proceeding")
print("=" * 55)
