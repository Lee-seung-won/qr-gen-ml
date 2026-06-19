from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_qr_larger_box_size_increases_image_dimensions() -> None:
    small = client.get("/qr", params={"text": "x", "box_size": 4, "border": 2, "ecc": "L"})
    large = client.get("/qr", params={"text": "x", "box_size": 12, "border": 2, "ecc": "L"})
    assert small.status_code == 200 and large.status_code == 200
    assert len(large.content) > len(small.content)


def test_qr_high_ecc_produces_valid_png() -> None:
    params = {"text": "ecc-test", "ecc": "H", "box_size": 6, "border": 3}
    response = client.get("/qr", params=params)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_qr_invalid_ecc_query_returns_422() -> None:
    response = client.get("/qr", params={"text": "ok", "ecc": "X"})
    assert response.status_code == 422


def test_qr_box_size_below_min_returns_422() -> None:
    response = client.get("/qr", params={"text": "ok", "box_size": 0})
    assert response.status_code == 422


def test_qr_border_above_max_returns_422() -> None:
    response = client.get("/qr", params={"text": "ok", "border": 21})
    assert response.status_code == 422
