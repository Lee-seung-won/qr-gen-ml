from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_qr_missing_text_returns_422() -> None:
    response = client.get("/qr")
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "missing"
    assert body["detail"][0]["loc"] == ["query", "text"]


def test_qr_empty_query_string_returns_422() -> None:
    response = client.get("/qr", params={"text": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "string_too_short"


def test_qr_over_max_length_returns_422() -> None:
    response = client.get("/qr", params={"text": "x" * 501})
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "string_too_long"


def test_qr_exactly_max_length_returns_png() -> None:
    payload = "y" * 500
    response = client.get("/qr", params={"text": payload})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_qr_single_non_whitespace_char_returns_png() -> None:
    response = client.get("/qr", params={"text": "a"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 100


def test_qr_tab_only_stripped_to_empty_returns_422() -> None:
    response = client.get("/qr", params={"text": "\t"})
    assert response.status_code == 422
    assert response.json()["detail"] == "text must not be empty"


def test_qr_newline_only_stripped_to_empty_returns_422() -> None:
    response = client.get("/qr", params={"text": "\n"})
    assert response.status_code == 422
    assert response.json()["detail"] == "text must not be empty"


def test_qr_unicode_within_limit_returns_png() -> None:
    text = "가" * 500
    assert len(text) == 500
    response = client.get("/qr", params={"text": text})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
