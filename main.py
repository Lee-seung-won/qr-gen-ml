from __future__ import annotations

import base64
import logging
import time
import uuid
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Literal, Self

import qrcode
import qrcode.constants as qr_const
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.middleware.base import BaseHTTPMiddleware

_LOG = logging.getLogger("qr_gen")

_ECC_MAP: dict[str, int] = {
    "L": qr_const.ERROR_CORRECT_L,
    "M": qr_const.ERROR_CORRECT_M,
    "Q": qr_const.ERROR_CORRECT_Q,
    "H": qr_const.ERROR_CORRECT_H,
}


def build_qr_png(text: str, box_size: int, border: int, ecc: str) -> tuple[bytes, tuple[int, int]]:
    qr = qrcode.QRCode(
        version=None,
        error_correction=_ECC_MAP[ecc],
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image()
    w, h = img.size
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue(), (w, h)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    yield


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException:
            duration_ms = int((time.perf_counter() - start) * 1000)
            _LOG.exception(
                "event=request_failed request_id=%s method=%s path=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        _LOG.info(
            "event=request_completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-Id"] = request_id
        return response


app = FastAPI(title="qr-gen-web", lifespan=lifespan)
app.add_middleware(RequestLogMiddleware)


class QrCreateRequest(BaseModel):
    text: str = Field(..., max_length=500)
    box_size: int = Field(10, ge=1, le=30)
    border: int = Field(4, ge=0, le=20)
    ecc: Literal["L", "M", "Q", "H"] = "M"

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def validate_text(self) -> Self:
        if not self.text:
            raise ValueError("text must not be empty")
        if len(self.text) > 500:
            raise ValueError("text too long")
        return self


class QrCreateResponse(BaseModel):
    format: Literal["png"] = "png"
    image_base64: str
    width: int
    height: int


@app.get("/")
def read_root() -> HTMLResponse:
    return HTMLResponse(
        content="""
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>QR 생성기</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg0: #0c0e14;
        --bg1: #12151f;
        --card: rgba(24, 28, 40, 0.85);
        --stroke: rgba(120, 140, 200, 0.22);
        --text: #e8ebf4;
        --muted: #8b93a8;
        --accent: #6c9eff;
        --accent2: #8b5cf6;
        --ok: #34d399;
        --radius: 16px;
        --shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "DM Sans", ui-sans-serif, system-ui, sans-serif;
        color: var(--text);
        background: linear-gradient(165deg, var(--bg0) 0%, #151a28 48%, var(--bg1) 100%),
          radial-gradient(700px 380px at 12% -8%, rgba(108, 158, 255, 0.16), transparent),
          radial-gradient(520px 320px at 92% 4%, rgba(139, 92, 246, 0.12), transparent);
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: clamp(1.25rem, 4vw, 2.5rem);
      }
      .shell {
        width: min(100%, 440px);
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-bottom: 1.25rem;
      }
      .logo {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        display: grid;
        place-items: center;
        font-weight: 700;
        font-size: 0.95rem;
        color: #0c0e14;
        box-shadow: 0 8px 24px rgba(108, 158, 255, 0.35);
      }
      .brand h1 {
        margin: 0;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.02em;
      }
      .brand span {
        display: block;
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--muted);
        margin-top: 0.15rem;
      }
      .card {
        background: var(--card);
        border: 1px solid var(--stroke);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
        padding: clamp(1.25rem, 3vw, 1.75rem);
      }
      .lead {
        margin: 0 0 1.25rem;
        font-size: 0.92rem;
        line-height: 1.55;
        color: var(--muted);
      }
      .api-hint {
        margin: 0 0 1.35rem;
        padding: 0.65rem 0.75rem;
        border-radius: 10px;
        background: rgba(108, 158, 255, 0.08);
        border: 1px solid rgba(108, 158, 255, 0.2);
        font-size: 0.8rem;
        color: var(--muted);
        line-height: 1.45;
      }
      .api-hint code {
        font-size: 0.78rem;
        color: var(--accent);
        background: rgba(0, 0, 0, 0.25);
        padding: 0.12rem 0.35rem;
        border-radius: 6px;
      }
      label {
        display: block;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 0.35rem;
      }
      input[type="text"],
      input[type="number"],
      select {
        width: 100%;
        padding: 0.65rem 0.75rem;
        border-radius: 10px;
        border: 1px solid var(--stroke);
        background: rgba(12, 14, 20, 0.55);
        color: var(--text);
        font-size: 0.95rem;
        outline: none;
        transition: border-color 0.15s, box-shadow 0.15s;
      }
      input:focus,
      select:focus {
        border-color: rgba(108, 158, 255, 0.55);
        box-shadow: 0 0 0 3px rgba(108, 158, 255, 0.2);
      }
      .field {
        margin-bottom: 1rem;
      }
      .row2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
      }
      @media (max-width: 380px) {
        .row2 {
          grid-template-columns: 1fr;
        }
      }
      button[type="submit"] {
        width: 100%;
        margin-top: 0.25rem;
        padding: 0.75rem 1rem;
        border: none;
        border-radius: 12px;
        font-family: inherit;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        color: #0c0e14;
        background: linear-gradient(135deg, var(--accent), #9db9ff);
        box-shadow: 0 10px 28px rgba(108, 158, 255, 0.35);
        transition: transform 0.12s, filter 0.12s;
      }
      button[type="submit"]:hover {
        filter: brightness(1.05);
        transform: translateY(-1px);
      }
      button[type="submit"]:active {
        transform: translateY(0);
      }
      .foot {
        margin-top: 1.25rem;
        text-align: center;
        font-size: 0.75rem;
        color: var(--muted);
      }
      .dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--ok);
        margin-right: 0.35rem;
        vertical-align: middle;
        box-shadow: 0 0 10px var(--ok);
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="brand">
        <div class="logo">QR</div>
        <div>
          <h1>QR 생성기</h1>
          <span>PNG로 즉시보내기</span>
        </div>
      </div>
      <div class="card">
        <p class="lead">
          텍스트나 URL을 입력하고 옵션을 맞춘 뒤 생성하면 PNG QR이 브라우저에 열립니다.
        </p>
        <p class="api-hint">개발 연동은 <code>POST /api/qr</code> JSON API를 사용하세요.</p>
        <form action="/qr" method="get">
          <div class="field">
            <label for="text">내용</label>
            <input id="text" name="text" type="text" minlength="1" maxlength="500" required
              placeholder="https://example.com 또는 메시지" autocomplete="off" />
          </div>
          <div class="row2">
            <div class="field">
              <label for="box_size">모듈 크기</label>
              <input id="box_size" name="box_size" type="number" value="10" min="1" max="30" />
            </div>
            <div class="field">
              <label for="border">여백</label>
              <input id="border" name="border" type="number" value="4" min="0" max="20" />
            </div>
          </div>
          <div class="field">
            <label for="ecc">에러 정정</label>
            <select id="ecc" name="ecc">
              <option value="L">L (약 7%)</option>
              <option value="M" selected>M (약 15%)</option>
              <option value="Q">Q (약 25%)</option>
              <option value="H">H (약 30%)</option>
            </select>
          </div>
          <button type="submit">QR 이미지 생성</button>
        </form>
      </div>
      <p class="foot"><span class="dot" aria-hidden="true"></span>GET /qr · /health</p>
    </div>
  </body>
</html>
"""
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/qr")
def create_qr(
    text: str = Query(..., min_length=1, max_length=500),
    box_size: int = Query(10, ge=1, le=30),
    border: int = Query(4, ge=0, le=20),
    ecc: Literal["L", "M", "Q", "H"] = Query("M"),
) -> Response:
    text = text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="text must not be empty")
    png_bytes, _wh = build_qr_png(text, box_size, border, ecc)
    return Response(content=png_bytes, media_type="image/png")


@app.post("/api/qr", response_model=QrCreateResponse)
def create_qr_json(body: QrCreateRequest) -> QrCreateResponse:
    png_bytes, (w, h) = build_qr_png(body.text, body.box_size, body.border, body.ecc)
    b64 = base64.standard_b64encode(png_bytes).decode("ascii")
    return QrCreateResponse(image_base64=b64, width=w, height=h)
