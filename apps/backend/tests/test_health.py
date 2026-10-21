from app.main import create_app
from fastapi.testclient import TestClient


def test_liveness_does_not_claim_planner_readiness():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "service": "menuto",
        "status": "ok",
        "stage": "foundation",
        "planner_ready": False,
    }


def test_no_unimplemented_planning_endpoint_is_advertised():
    with TestClient(create_app()) as client:
        paths = client.get("/openapi.json").json()["paths"]
        response = client.post("/api/v1/plans", json={})
    assert set(paths) == {"/api/v1/health"}
    assert response.status_code == 404
