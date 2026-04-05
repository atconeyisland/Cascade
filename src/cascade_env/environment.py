from .models import (
    CascadeObservation, CascadeAction, CascadeReward,
    StepResult, ActionType, PriorityLevel
)
from typing import Dict, Any
import importlib


class CascadeEnvironment:

    MAX_STEPS = 15

    def __init__(self, task_id: int = 1):
        self.task_id = task_id
        self.current_step = 0
        self.steps_taken = []
        self.episode_done = False
        self.accumulated_reward = 0.0
        self.last_observation = None
        self._task = self._load_task(task_id)
        self._reward_breakdown = {}

    def _load_task(self, task_id: int):
        module = importlib.import_module(
            f".tasks.task{task_id}", package="cascade_env"
        )
        return module.Task()

    def reset(self) -> CascadeObservation:
        self.current_step = 0
        self.steps_taken = []
        self.episode_done = False
        self.accumulated_reward = 0.0
        self._reward_breakdown = {}
        self._task.reset()
        self.last_observation = self._task.get_initial_observation()
        return self.last_observation

    def step(self, action: CascadeAction) -> StepResult:
        if self.episode_done:
            return StepResult(
                observation=self.last_observation,
                reward=0.0,
                done=True,
                info={"message": "Episode already done. Call reset()."}
            )

        step_str = f"{action.action_type.value}::{action.action_value}"
        self.steps_taken.append(step_str)
        self.current_step += 1

        step_reward, reward_info = self._calculate_reward(action)
        self.accumulated_reward = min(
            1.0, max(0.0, self.accumulated_reward + step_reward)
        )

        done = self._check_done(action)
        self.episode_done = done

        if done:
            grader_module = importlib.import_module(
                f".graders.grader{self.task_id}", package="cascade_env"
            )
            final_score = grader_module.grade(
                steps_taken=self.steps_taken,
                final_observation=self._task.get_current_observation(
                    self.current_step, self.steps_taken, done
                )
            )
            self.accumulated_reward = final_score

        observation = self._task.get_current_observation(
            self.current_step, self.steps_taken, done
        )
        self.last_observation = observation

        return StepResult(
            observation=observation,
            reward=self.accumulated_reward,
            done=done,
            info={
                "step_reward": step_reward,
                "accumulated_reward": self.accumulated_reward,
                "reward_breakdown": self._reward_breakdown,
                **reward_info
            }
        )

    def _calculate_reward(self, action: CascadeAction):
        reward = 0.0
        info = {}

        if action.action_type == ActionType.SELECT_RUNBOOK:
            if self._task.is_correct_runbook(action.action_value):
                reward += 0.20
                self._reward_breakdown["correct_runbook"] = 0.20
                info["runbook_correct"] = True
            else:
                reward -= 0.10
                self._reward_breakdown["wrong_runbook"] = -0.10
                info["runbook_correct"] = False

        elif action.action_type == ActionType.EXECUTE_STEP:
            if self._task.is_correct_step(action.action_value, self.steps_taken):
                reward += 0.15
                self._reward_breakdown[f"correct_step_{self.current_step}"] = 0.15
                info["step_correct"] = True
            else:
                reward -= 0.05
                self._reward_breakdown[f"wasted_step_{self.current_step}"] = -0.05
                info["step_correct"] = False

        elif action.action_type == ActionType.INVESTIGATE:
            if self._task.is_correct_investigation(action.action_value):
                reward += 0.20
                self._reward_breakdown["correct_system_identified"] = 0.20
                info["investigation_correct"] = True
            else:
                reward -= 0.05
                self._reward_breakdown[f"wasted_investigation_{self.current_step}"] = -0.05
                info["investigation_correct"] = False

        elif action.action_type == ActionType.ESCALATE_TO_HUMAN:
            if self._task.should_escalate():
                reward += 0.15
                self._reward_breakdown["correct_escalation"] = 0.15
                info["escalation_correct"] = True
            else:
                reward -= 0.10
                self._reward_breakdown["unnecessary_escalation"] = -0.10
                info["escalation_correct"] = False

        elif action.action_type == ActionType.RESOLVE:
            if self._task.is_resolved(self.steps_taken):
                reward += 0.25
                self._reward_breakdown["incident_resolved"] = 0.25
                info["resolved"] = True
            else:
                reward -= 0.15
                self._reward_breakdown["premature_resolve"] = -0.15
                info["resolved"] = False

        elif action.action_type == ActionType.ROLLBACK:
            reward -= 0.05
            self._reward_breakdown[f"rollback_{self.current_step}"] = -0.05
            info["rolled_back"] = True
            self.steps_taken.pop() if len(self.steps_taken) > 1 else None

        if self._task.is_destructive_action(action.action_value):
            reward -= 0.15
            self._reward_breakdown["destructive_action"] = -0.15
            info["destructive"] = True

        return reward, info

    def _check_done(self, action: CascadeAction) -> bool:
        if self.current_step >= self.MAX_STEPS:
            return True
        if action.action_type == ActionType.RESOLVE:
            return True
        if action.action_type == ActionType.ESCALATE_TO_HUMAN:
            return True
        return False

    def state(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "current_step": self.current_step,
            "steps_taken": self.steps_taken,
            "episode_done": self.episode_done,
            "accumulated_reward": self.accumulated_reward,
            "reward_breakdown": self._reward_breakdown,
            "max_steps": self.MAX_STEPS
        }