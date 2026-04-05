from fastapi import FastAPI, HTTPException
from .models import CascadeAction, CascadeObservation, StepResult
from .environment import CascadeEnvironment
from typing import Dict

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


@app.get("/health")
def health():
    return {"status": "ok", "name": "cascade"}


@app.post("/reset", response_model=CascadeObservation)
def reset(task_id: int = 1):
    env = get_env(task_id)
    observation = env.reset()
    return observation


@app.post("/step", response_model=StepResult)
def step(action: CascadeAction, task_id: int = 1):
    env = get_env(task_id)
    if env.last_observation is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not reset. Call /reset first."
        )
    result = env.step(action)
    return result


@app.get("/state")
def state(task_id: int = 1):
    env = get_env(task_id)
    return env.state()