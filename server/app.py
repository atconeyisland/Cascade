from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn

from cascade_env.models import CascadeAction, CascadeObservation
from cascade_env.environment import CascadeEnvironment

class StepResponse(BaseModel):
    observation: CascadeObservation
    reward: Optional[float]
    done: bool


app = FastAPI(
    title="Cascade",
    description="Train agents to stop failures before they spread.",
    version="1.0.0"
)

environments: Dict[str, CascadeEnvironment] = {}


def get_env(task_id: int = 1) -> CascadeEnvironment:
    key = str(task_id)
    if key not in environments:
        environments[key] = CascadeEnvironment(task_id=task_id)
    return environments[key]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "healthy", "name": "cascade"}


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
@app.get("/metadata")
def metadata():
    return {
        "name": "cascade",
        "description": "A reinforcement learning environment for production incident response. Train agents to diagnose and resolve cascading failures across 3 difficulty tiers."
    }


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
@app.get("/schema")
def schema():
    return {
        "action": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["select_runbook", "execute_step", "investigate", "escalate_to_human", "resolve", "rollback"]
                },
                "action_value": {"type": "string"},
                "reasoning": {"type": "string"}
            }
        },
        "observation": {
            "type": "object",
            "properties": {
                "alert_message": {"type": "string"},
                "system_logs": {"type": "array", "items": {"type": "string"}},
                "available_runbooks": {"type": "array", "items": {"type": "string"}},
                "current_step": {"type": "integer"},
                "episode_done": {"type": "boolean"},
                "steps_taken": {"type": "array", "items": {"type": "string"}},
                "affected_services": {"type": "array", "items": {"type": "string"}},
                "severity_level": {"type": "string"},
                "priority_level": {"type": "string"},
                "human_intervention_required": {"type": "boolean"}
            }
        },
        "state": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "episode_id": {"type": "string"},
                "current_step": {"type": "integer"},
                "done": {"type": "boolean"}
            }
        }
    }


# ---------------------------------------------------------------------------
# MCP
# ---------------------------------------------------------------------------
@app.post("/mcp")
async def mcp(request: dict):
    return {
        "jsonrpc": "2.0",
        "id": request.get("id", 1),
        "result": {
            "name": "cascade",
            "description": "OpenEnv environment for production incident response"
        }
    }


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------
@app.post("/reset", response_model=StepResponse)
def reset(task_id: int = Query(default=1)):
    try:
        env = get_env(task_id)
        obs = env.reset()
        return StepResponse(observation=obs, reward=0.0, done=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------
@app.post("/step", response_model=StepResponse)
def step(action: CascadeAction, task_id: int = Query(default=1)):
    env = get_env(task_id)
    if env.last_observation is None:
        raise HTTPException(status_code=400, detail="Environment not reset. Call /reset first.")
    try:
        result = env.step(action)
        return StepResponse(observation=result.observation, reward=result.reward, done=result.done)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
@app.get("/state")
def state(task_id: int = Query(default=1)):
    env = get_env(task_id)
    return {
        "task_id": task_id,
        "current_step": env.current_step,
        "episode_done": env.episode_done,
        "accumulated_reward": env.accumulated_reward,
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()