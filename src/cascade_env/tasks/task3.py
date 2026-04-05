from cascade_env.models import CascadeObservation, PriorityLevel


CORRECT_RUNBOOK = "network-runbook"
CORRECT_INVESTIGATION = "network"
CORRECT_STEPS = [
    "failover inventory-service",
    "failover order-service",
    "failover notification-service"
]
DESTRUCTIVE_ACTIONS = [
    "delete route",
    "force shutdown",
    "drop all traffic",
    "disable load balancer",
    "wipe network config"
]
RED_HERRING_SERVICE = "recommendation-engine"


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
                "[ALERT] P1 — Multiple simultaneous failures. "
                "order-service, inventory-service, notification-service all unreachable. "
                "Time: 02:17 IST."
            ),
            system_logs=[
                "2026-04-06 02:17:44 WARN  recommendation-engine: CPU 91% — recomputing feature matrix for A/B test variant 7 (error_rate=0%)",
                "2026-04-06 02:17:38 CRIT  network-monitor: AZ us-east-1b health check FAILED — packet loss 100% cross-AZ traffic dropped",
                "2026-04-06 02:17:40 ERROR order-service: DB connection pool exhausted host=inventory-db",
                "2026-04-06 02:17:41 ERROR notification-service: request timeout 30000ms — upstream unavailable",
                "2026-04-06 02:17:42 ERROR inventory-service: network unreachable — AZ us-east-1b isolated from us-east-1a",
                "2026-04-06 02:17:43 ERROR order-service: cannot connect to inventory-service — connection refused (AZ: us-east-1b)",
            ],
            available_runbooks=[
                "network-runbook",
                "cpu-runbook",
                "db-failover-runbook",
                "service-restart-runbook",
                "load-balancer-runbook"
            ],
            affected_services=[
                "order-service",
                "inventory-service",
                "notification-service"
            ],
            severity_level="critical",
            priority_level=PriorityLevel.P1,
            human_intervention_required=True,
            current_step=0,
            episode_done=False,
            steps_taken=[]
        )

    def get_current_observation(
        self, current_step: int, steps_taken: list, done: bool
    ) -> CascadeObservation:
        return CascadeObservation(
            alert_message=(
                "[ALERT] P1 — Multiple simultaneous failures. "
                "order-service, inventory-service, notification-service all unreachable. "
                "Time: 02:17 IST."
            ),
            system_logs=[
                "2026-04-06 02:17:44 WARN  recommendation-engine: CPU 91% — recomputing feature matrix for A/B test variant 7 (error_rate=0%)",
                "2026-04-06 02:17:38 CRIT  network-monitor: AZ us-east-1b health check FAILED — packet loss 100% cross-AZ traffic dropped",
                "2026-04-06 02:17:40 ERROR order-service: DB connection pool exhausted host=inventory-db",
                "2026-04-06 02:17:41 ERROR notification-service: request timeout 30000ms — upstream unavailable",
                "2026-04-06 02:17:42 ERROR inventory-service: network unreachable — AZ us-east-1b isolated from us-east-1a",
                "2026-04-06 02:17:43 ERROR order-service: cannot connect to inventory-service — connection refused (AZ: us-east-1b)",
            ],
            available_runbooks=[
                "network-runbook",
                "cpu-runbook",
                "db-failover-runbook",
                "service-restart-runbook",
                "load-balancer-runbook"
            ],
            affected_services=[
                "order-service",
                "inventory-service",
                "notification-service"
            ],
            severity_level="critical",
            priority_level=PriorityLevel.P1,
            human_intervention_required=True,
            current_step=current_step,
            episode_done=done,
            steps_taken=steps_taken
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
        # Task 3 always requires human escalation
        return True

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
        has_escalation = any("escalate_to_human" in s for s in steps_lower)
        return has_correct_runbook and has_investigation and has_fix and has_escalation
