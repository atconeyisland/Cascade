from fastapi import FastAPI, HTTPException, Query
from cascade_env.models import CascadeAction, CascadeObservation, StepResult
from cascade_env.environment import CascadeEnvironment
from typing import Dict
import uvicorn

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
def reset(task_id: int = Query(default=1)):
    env = get_env(task_id)
    observation = env.reset()
    return observation


@app.post("/step", response_model=StepResult)
def step(action: CascadeAction, task_id: int = Query(default=1)):
    env = get_env(task_id)
    if env.last_observation is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not reset. Call /reset first."
        )
    result = env.step(action)
    return result


@app.get("/state")
def state(task_id: int = Query(default=1)):
    env = get_env(task_id)
    return {
        "task_id": task_id,
        "current_step": env.current_step,
        "episode_done": env.episode_done,
        "accumulated_reward": env.accumulated_reward,
    }


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()