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
  </head>
  <body>
    <h1>QR 생성기</h1>
    <p>텍스트 또는 URL을 입력하면 QR 이미지(PNG)를 생성합니다.</p>
    <p>프로그램 연동은 <code>POST /api/qr</code> JSON API를 사용하세요.</p>
    <form action="/qr" method="get">
      <p>
        <label for="text">입력값</label>
        <input id="text" name="text" type="text" minlength="1" maxlength="500" required />
      </p>
      <p>
        <label for="box_size">모듈 픽셀(box_size)</label>
        <input id="box_size" name="box_size" type="number" value="10" min="1" max="30" />
      </p>
      <p>
        <label for="border">여백 모듈 수(border)</label>
        <input id="border" name="border" type="number" value="4" min="0" max="20" />
      </p>
      <p>
        <label for="ecc">에러 정정</label>
        <select id="ecc" name="ecc">
          <option value="L">L (약 7%)</option>
          <option value="M" selected>M (약 15%)</option>
          <option value="Q">Q (약 25%)</option>
          <option value="H">H (약 30%)</option>
        </select>
      </p>
      <button type="submit">QR 생성</button>
    </form>
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
