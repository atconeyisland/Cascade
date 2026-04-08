"""
CascadeEnv - HTTP Client for the Cascade RL Environment
========================================================

Provides a Python client to interact with a Cascade environment server.
Supports both local and remote Hugging Face Space deployments.

Usage:
    # Connect to local server
    env = CascadeEnv(base_url="http://localhost:8000")
    
    # Or use Hugging Face Space
    env = CascadeEnv(base_url="https://user-space.hf.space")
    
    # Reset and step through an episode
    obs = env.reset(task_id=1)
    action = CascadeAction(
        action_type=ActionType.INVESTIGATE,
        action_value="database",
        reasoning="high cpu usage in logs"
    )
    result = env.step(action, task_id=1)
"""

import httpx
from typing import Optional
from .models import CascadeAction, CascadeObservation, StepResult


class CascadeEnv:
    """HTTP client for Cascade environment."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        """
        Args:
            base_url: Server URL (e.g., "http://localhost:8000" or "https://space.hf.space")
            timeout: HTTP request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def health(self) -> dict:
        """Check server health."""
        response = self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def reset(self, task_id: int = 1) -> CascadeObservation:
        """
        Reset the environment for a task.
        
        Args:
            task_id: Task ID (1, 2, or 3)
        
        Returns:
            Initial observation
        """
        response = self.client.post(f"{self.base_url}/reset/{task_id}")
        response.raise_for_status()
        data = response.json()
        return CascadeObservation(**data)
    
    def step(self, action: CascadeAction, task_id: int = 1) -> StepResult:
        """
        Execute one step in the environment.
        
        Args:
            action: The action to execute
            task_id: Task ID (1, 2, or 3)
        
        Returns:
            Step result with observation, reward, done flag
        """
        payload = action.model_dump()
        response = self.client.post(f"{self.base_url}/step/{task_id}", json=payload)
        response.raise_for_status()
        data = response.json()
        
        obs_data = data.get("observation", {})
        observation = CascadeObservation(**obs_data)
        
        return StepResult(
            observation=observation,
            reward=data.get("reward", 0.0),
            done=data.get("done", False),
            info=data.get("info", {})
        )
    
    def get_state(self, task_id: int = 1) -> dict:
        """Get current environment state."""
        response = self.client.get(f"{self.base_url}/state/{task_id}")
        response.raise_for_status()
        return response.json()


# For convenience, also export models
__all__ = ["CascadeEnv", "CascadeAction", "CascadeObservation", "StepResult"]
