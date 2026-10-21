"""ASGI entrypoint. Business endpoints are intentionally not implemented yet."""

from fastapi import FastAPI

from app.shared.health import HealthResponse


def create_app() -> FastAPI:
    application = FastAPI(title="Menuto", version="0.1.0")

    @application.get("/api/v1/health", response_model=HealthResponse, tags=["operations"])
    def health() -> HealthResponse:
        """Process liveness only; does not certify database or planner readiness."""
        return HealthResponse()

    return application


app = create_app()
