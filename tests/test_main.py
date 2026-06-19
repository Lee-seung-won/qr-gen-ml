from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint_shows_safety_form() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "QR 안전성 검사" in response.text
    assert 'fetch("/classify"' in response.text
    assert 'name="text"' in response.text


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
