from cascade_env.models import CascadeObservation, PriorityLevel


CORRECT_RUNBOOK = "db-cpu-runbook"
CORRECT_INVESTIGATION = "database"
CORRECT_STEPS = [
    "run explain on slow query",
    "identify missing index",
    "add index"
]
DESTRUCTIVE_ACTIONS = [
    "drop table",
    "delete database",
    "kill all connections",
    "restart database"
]


class Task:

    def __init__(self):
        self.reset()

    def reset(self):
        self.runbook_selected = None
        self.investigation_done = False
        self.resolved = False

    def get_initial_observation(self) -> CascadeObservation:
        return CascadeObservation(
            alert_message=(
                "[ALERT] P2 — Database response time exceeded 10s threshold. "
                "API error rate at 78%. Service: payments-api. Time: 02:14 IST."
            ),
            system_logs=[
                "2026-04-06 02:14:01 ERROR payments-api: timeout waiting for db response (10002ms)",
                "2026-04-06 02:14:02 ERROR payments-api: timeout waiting for db response (10001ms)",
                "2026-04-06 02:14:03 WARN  db-primary: query execution time 9800ms — SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC",
                "2026-04-06 02:14:03 WARN  db-primary: query execution time 9750ms — SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC",
                "2026-04-06 02:14:04 INFO  db-primary: CPU usage 99.8%",
                "2026-04-06 02:14:05 INFO  db-primary: active connections 142/150",
                "2026-04-06 02:14:06 ERROR payments-api: HTTP 503 returned to 1847 users",
            ],
            available_runbooks=[
                "db-cpu-runbook",
                "network-latency-runbook",
                "app-restart-runbook"
            ],
            affected_services=["payments-api", "db-primary"],
            severity_level="high",
            priority_level="P2",
            human_intervention_required=False,
        )

    def get_current_observation(
        self, current_step: int, steps_taken: list, done: bool
    ) -> CascadeObservation:
        return CascadeObservation(
            alert_message=(
                "[ALERT] P2 — Database response time exceeded 10s threshold. "
                "API error rate at 78%. Service: payments-api. Time: 02:14 IST."
            ),
            system_logs=[
                "2026-04-06 02:14:01 ERROR payments-api: timeout waiting for db response (10002ms)",
                "2026-04-06 02:14:02 ERROR payments-api: timeout waiting for db response (10001ms)",
                "2026-04-06 02:14:03 WARN  db-primary: query execution time 9800ms — SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC",
                "2026-04-06 02:14:03 WARN  db-primary: query execution time 9750ms — SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC",
                "2026-04-06 02:14:04 INFO  db-primary: CPU usage 99.8%",
                "2026-04-06 02:14:05 INFO  db-primary: active connections 142/150",
                "2026-04-06 02:14:06 ERROR payments-api: HTTP 503 returned to 1847 users",
            ],
            available_runbooks=[
                "db-cpu-runbook",
                "network-latency-runbook",
                "app-restart-runbook"
            ],
            affected_services=["payments-api", "db-primary"],
            severity_level="high",
            priority_level="P2",
            human_intervention_required=False
        )

    def is_correct_runbook(self, runbook: str) -> bool:
        self.runbook_selected = runbook.lower().strip()
        return self.runbook_selected == CORRECT_RUNBOOK

    def is_correct_investigation(self, value: str) -> bool:
        keywords = ["database", "db", "db-primary", "postgres", "mysql"]
        return any(k in value.lower() for k in keywords)

    def is_correct_step(self, step: str, steps_taken: list) -> bool:
        step_lower = step.lower().strip()
        return any(correct in step_lower for correct in CORRECT_STEPS)

    def is_destructive_action(self, value: str) -> bool:
        value_lower = value.lower().strip()
        return any(d in value_lower for d in DESTRUCTIVE_ACTIONS)

    def should_escalate(self) -> bool:
        return False

    def is_resolved(self, steps_taken: list) -> bool:
        steps_lower = [s.lower() for s in steps_taken]
        has_correct_runbook = any(CORRECT_RUNBOOK in s for s in steps_lower)
        has_investigation = any(
            CORRECT_INVESTIGATION in s for s in steps_lower
        )
        has_fix = any(
            any(correct in s for correct in CORRECT_STEPS)
            for s in steps_lower
        )
        return has_correct_runbook and has_investigation and has_fix