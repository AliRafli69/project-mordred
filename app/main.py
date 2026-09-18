from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


APP_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


app = FastAPI(
    title="Mordred Backend",
    version=APP_VERSION,
    description="Shared backend service for Project Mordred.",
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["service"],
    summary="Check backend health",
)
async def health() -> HealthResponse:
    """Report whether the Mordred backend process is operating."""

    return HealthResponse(
        status="ok",
        service="mordred-backend",
        version=APP_VERSION,
    )
