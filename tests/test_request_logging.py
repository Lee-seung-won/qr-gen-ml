import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_includes_x_request_id_header() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    rid = response.headers.get("X-Request-Id")
    assert rid is not None
    uuid.UUID(rid)


def test_qr_response_includes_x_request_id_header() -> None:
    response = client.get("/qr", params={"text": "log-check"})
    assert response.status_code == 200
    rid = response.headers.get("X-Request-Id")
    assert rid is not None
    uuid.UUID(rid)
