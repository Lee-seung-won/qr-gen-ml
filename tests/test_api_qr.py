import base64

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_api_qr_returns_base64_png_and_dimensions() -> None:
    payload = {
        "text": "https://api.example",
        "box_size": 8,
        "border": 2,
        "ecc": "Q",
    }
    response = client.post("/api/qr", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert data["format"] == "png"
    assert data["width"] > 0 and data["height"] > 0
    raw = base64.standard_b64decode(data["image_base64"])
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")


def test_api_qr_rejects_blank_after_strip() -> None:
    response = client.post("/api/qr", json={"text": "   "})
    assert response.status_code == 422


def test_api_qr_rejects_oversized_text() -> None:
    response = client.post("/api/qr", json={"text": "z" * 501})
    assert response.status_code == 422
