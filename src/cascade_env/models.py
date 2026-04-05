from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class PriorityLevel(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ActionType(str, Enum):
    SELECT_RUNBOOK = "select_runbook"
    EXECUTE_STEP = "execute_step"
    INVESTIGATE = "investigate"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    RESOLVE = "resolve"
    ROLLBACK = "rollback"


class CascadeObservation(BaseModel):
    alert_message: str
    system_logs: List[str]
    available_runbooks: List[str]
    current_step: int
    episode_done: bool
    steps_taken: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    severity_level: str = "medium"
    priority_level: PriorityLevel = PriorityLevel.P2
    human_intervention_required: bool = False


class CascadeAction(BaseModel):
    action_type: ActionType
    action_value: str
    reasoning: str


class CascadeReward(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    message: str = ""


class StepResult(BaseModel):
    observation: CascadeObservation
    reward: float
    done: bool
    info: Dict