from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_serves_html_with_form_wiring() -> None:
    response = client.get("/")
    assert response.status_code == 200
    ct = response.headers["content-type"]
    assert ct.startswith("text/html")
    assert "charset=utf-8" in ct.replace(" ", "").lower()
    html = response.text
    assert "POST /api/qr" in html
    assert "<form action=\"/qr\" method=\"get\">" in html
    assert 'name="text"' in html
    assert 'minlength="1"' in html
    assert 'maxlength="500"' in html
    assert "required" in html


def test_health_returns_json_object() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)
    assert data == {"status": "ok"}


def test_qr_png_body_is_valid_png_chunk_stream() -> None:
    response = client.get("/qr", params={"text": "https://example.com/path?q=1&x=y"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    body = response.content
    assert body[:8] == b"\x89PNG\r\n\x1a\n"
    assert b"IHDR" in body[:64]


def test_sequential_root_then_qr_mimics_browser_flow() -> None:
    root = client.get("/")
    assert root.status_code == 200
    qr = client.get("/qr", params={"text": "flow-check"})
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert len(qr.content) > 0
