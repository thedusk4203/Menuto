from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    service: Literal["menuto"] = "menuto"
    status: Literal["ok"] = "ok"
    stage: Literal["foundation"] = "foundation"
    planner_ready: Literal[False] = False
