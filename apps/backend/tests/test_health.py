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


def test_health_contract_requires_every_field_always_sent_on_the_wire():
    with TestClient(create_app()) as client:
        document = client.get("/openapi.json").json()
        actual_keys = set(client.get("/api/v1/health").json())
    schema = document["components"]["schemas"]["HealthResponse"]
    assert set(schema["required"]) == actual_keys
