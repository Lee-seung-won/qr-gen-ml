from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint_shows_qr_form() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<form action=\"/qr\" method=\"get\">" in response.text


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_qr_endpoint_returns_png() -> None:
    response = client.get("/qr", params={"text": "https://example.com"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_qr_endpoint_rejects_whitespace_input() -> None:
    response = client.get("/qr", params={"text": "   "})
    assert response.status_code == 422
    assert response.json()["detail"] == "text must not be empty"
