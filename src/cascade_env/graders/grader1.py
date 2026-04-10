from cascade_env.models import CascadeObservation

CORRECT_RUNBOOK = "db-cpu-runbook"
CORRECT_STEPS = [
    "run explain on slow query",
    "identify missing index",
    "add index"
]

INVESTIGATION_KEYWORDS = ["database", "db", "db-primary", "postgres", "mysql"]


def grade(steps_taken: list[str], final_observation: CascadeObservation) -> float:
    score = 0.0
    steps_lower = [s.lower() for s in steps_taken]

    # +0.20 — correct system investigated
    investigated = any(any(k in s for k in INVESTIGATION_KEYWORDS) for s in steps_lower)
    if investigated:
        score += 0.20

    # +0.20 — correct runbook selected
    runbook_done = any(CORRECT_RUNBOOK in s for s in steps_lower)
    if runbook_done:
        score += 0.20

    # +0.15 per correct remediation step (max 3 steps = 0.45)
    steps_found = 0
    for correct in CORRECT_STEPS:
        if any(correct in s for s in steps_lower):
            score += 0.15
            steps_found += 1

    # +0.10 — correct priority identified
    if str(final_observation.priority_level) == "P2":
        score += 0.10

    # +0.25 — incident fully resolved
    # requires runbook + investigation + at least 2 correct steps
    if runbook_done and investigated and steps_found >= 2:
        score += 0.25

    # -0.20 — failed to escalate when human intervention was required
    if final_observation.human_intervention_required:
        escalated = any("escalate_to_human" in s for s in steps_lower)
        if not escalated:
            score -= 0.20

    # clip to 0.0 – 1.0
    return round(min(0.99, max(0.01, score)), 4)