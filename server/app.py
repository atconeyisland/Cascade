from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn

from cascade_env.models import CascadeAction, CascadeObservation
from cascade_env.environment import CascadeEnvironment

# ---------------------------------------------------------------------------
# Response Model (STRICT OpenEnv format)
# ---------------------------------------------------------------------------
class StepResponse(BaseModel):
    observation: CascadeObservation
    reward: Optional[float]
    done: bool


# ---------------------------------------------------------------------------
# App Init
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Cascade",
    description="Train agents to stop failures before they spread.",
    version="1.0.0"
)

# Keep per-task environments
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
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------
@app.post("/reset", response_model=StepResponse)
def reset(task_id: int = Query(default=1)):
    try:
        env = get_env(task_id)
        obs = env.reset()

        return StepResponse(
            observation=obs,
            reward=0.0,
            done=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------
@app.post("/step", response_model=StepResponse)
def step(action: CascadeAction, task_id: int = Query(default=1)):
    env = get_env(task_id)

    if env.last_observation is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not reset. Call /reset first."
        )

    try:
        result = env.step(action)

        return StepResponse(
            observation=result.observation,
            reward=result.reward,
            done=result.done
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# State (optional but useful)
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