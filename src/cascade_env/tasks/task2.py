from cascade_env.models import CascadeObservation, PriorityLevel


CORRECT_RUNBOOK = "memory-runbook"
CORRECT_INVESTIGATION = "auth-service"
CORRECT_STEPS = [
    "drain connections",
    "restart auth-service",
    "preserve sessions"
]
DESTRUCTIVE_ACTIONS = [
    "kill process",
    "force restart",
    "delete session",
    "drop connections",
    "hard reboot"
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
                "[ALERT] P1 — auth-service heap memory at 96% and rising. "
                "api-gateway 401 error rate at 38%. Services: auth-service, api-gateway. "
                "Time: 04:11 IST."
            ),
            system_logs=[
                "2026-04-06 04:11:20 WARN  auth-service: unclosed DB connection detected in pool (count=847 max=100) — connection leak in progress",
                "2026-04-06 04:11:25 INFO  auth-service: mem_pct=96 heap_used=3891MB heap_max=4096MB gc_pause_ms=2341",
                "2026-04-06 04:11:28 WARN  api-gateway: connection reset by peer — host=auth-service port=8080",
                "2026-04-06 04:11:30 ERROR api-gateway: 401 Unauthorized — upstream token validation failed host=auth-service (rate: 2847/min)",
                "2026-04-06 04:11:31 ERROR auth-service: OutOfMemoryError: Java heap space in TokenValidator.validate(line 247)",
                "2026-04-06 04:11:33 ERROR auth-service: GC overhead limit exceeded — heap usage 96% (3891MB / 4096MB)",
            ],
            available_runbooks=[
                "memory-runbook",
                "timeout-runbook",
                "network-runbook",
                "restart-runbook"
            ],
            affected_services=["auth-service", "api-gateway"],
            severity_level="critical",
            priority_level="P1",
            human_intervention_required=False
        )

    def get_current_observation(
        self, current_step: int, steps_taken: list, done: bool
    ) -> CascadeObservation:
        return CascadeObservation(
            alert_message=(
                "[ALERT] P1 — auth-service heap memory at 96% and rising. "
                "api-gateway 401 error rate at 38%. Services: auth-service, api-gateway. "
                "Time: 04:11 IST."
            ),
            system_logs=[
                "2026-04-06 04:11:20 WARN  auth-service: unclosed DB connection detected in pool (count=847 max=100) — connection leak in progress",
                "2026-04-06 04:11:25 INFO  auth-service: mem_pct=96 heap_used=3891MB heap_max=4096MB gc_pause_ms=2341",
                "2026-04-06 04:11:28 WARN  api-gateway: connection reset by peer — host=auth-service port=8080",
                "2026-04-06 04:11:30 ERROR api-gateway: 401 Unauthorized — upstream token validation failed host=auth-service (rate: 2847/min)",
                "2026-04-06 04:11:31 ERROR auth-service: OutOfMemoryError: Java heap space in TokenValidator.validate(line 247)",
                "2026-04-06 04:11:33 ERROR auth-service: GC overhead limit exceeded — heap usage 96% (3891MB / 4096MB)",
            ],
            available_runbooks=[
                "memory-runbook",
                "timeout-runbook",
                "network-runbook",
                "restart-runbook"
            ],
            affected_services=["auth-service", "api-gateway"],
            severity_level="critical",
            priority_level="P1",
            human_intervention_required=False
        )

    def is_correct_runbook(self, runbook: str) -> bool:
        self.runbook_selected = runbook.lower().strip()
        return self.runbook_selected == CORRECT_RUNBOOK

    def is_correct_investigation(self, value: str) -> bool:
        self.investigation_done = True
        return CORRECT_INVESTIGATION in value.lower()

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
