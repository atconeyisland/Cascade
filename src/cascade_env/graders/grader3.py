from cascade_env.models import CascadeObservation

CORRECT_RUNBOOK = "network-runbook"
CORRECT_INVESTIGATION = "network"
CORRECT_STEPS = [
    "failover inventory-service",
    "failover order-service",
    "failover notification-service"
]
RED_HERRING_SERVICE = "recommendation-engine"


def grade(steps_taken: list[str], final_observation: CascadeObservation) -> float:
    score = 0.0
    steps_lower = [s.lower() for s in steps_taken]

    # +0.20 — correct system investigated (network/AZ partition)
    if any(CORRECT_INVESTIGATION in s for s in steps_lower):
        score += 0.20

    # +0.20 — correct runbook selected
    if any(CORRECT_RUNBOOK in s for s in steps_lower):
        score += 0.20

    # +0.15 per correct remediation step (max 3 steps = 0.45)
    steps_found = 0
    for correct in CORRECT_STEPS:
        if any(correct in s for s in steps_lower):
            score += 0.15
            steps_found += 1

    # +0.10 — correct priority identified
    if final_observation.priority_level.value == "P1":
        score += 0.10

    # +0.25 — incident fully resolved
    # requires runbook + investigation + at least 2 correct steps + escalation
    runbook_done = any(CORRECT_RUNBOOK in s for s in steps_lower)
    investigation_done = any(CORRECT_INVESTIGATION in s for s in steps_lower)
    escalated = any("escalate_to_human" in s for s in steps_lower)
    if runbook_done and investigation_done and steps_found >= 2 and escalated:
        score += 0.25

    # -0.20 — failed to escalate when human intervention was required
    # Task 3 always has human_intervention_required=True
    if final_observation.human_intervention_required:
        if not escalated:
            score -= 0.20

    # -0.15 — chased red herring (recommendation-engine has error_rate=0%)
    if any(RED_HERRING_SERVICE in s for s in steps_lower[:3]):
        score -= 0.15

    # clip to 0.0 – 1.0
    return round(min(1.0, max(0.0, score)), 4)
