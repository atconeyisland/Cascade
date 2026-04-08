from fastapi import FastAPI, HTTPException
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


@app.post("/reset/{task_id}", response_model=CascadeObservation)
def reset(task_id: int = 1):
    env = get_env(task_id)
    observation = env.reset()
    return observation


@app.post("/step/{task_id}", response_model=StepResult)
def step(action: CascadeAction, task_id: int = 1):
    env = get_env(task_id)
    if env.last_observation is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not reset. Call /reset first."
        )
    result = env.step(action)
    return result


@app.get("/state/{task_id}")
def state(task_id: int = 1):
    env = get_env(task_id)
    return {
        "task_id": task_id,
        "current_step": env.current_step,
        "episode_done": env.episode_done,
        "accumulated_reward": env.accumulated_reward,
    }


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for running the server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()
    main(host=args.host, port=args.port)
