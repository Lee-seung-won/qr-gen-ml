from __future__ import annotations

import base64
import logging
import time
import uuid
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Literal, Self

import qrcode
import qrcode.constants as qr_const
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.middleware.base import BaseHTTPMiddleware

from app.model_loader import get_model_info
from app.safety import check_safety_ml

_LOG = logging.getLogger("qr_gen")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

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
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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


class ClassifyRequest(BaseModel):
    text: str = Field(..., max_length=500)

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class ModelInfoResponse(BaseModel):
    run_id: str
    model_type: str
    test_accuracy: float


class ClassifyResponse(BaseModel):
    label: str
    score: float
    model_info: ModelInfoResponse


@app.get("/")
def read_root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html; charset=utf-8")


@app.post("/classify", response_model=ClassifyResponse)
def classify(body: ClassifyRequest) -> ClassifyResponse:
    label, score = check_safety_ml(body.text)
    info = get_model_info()
    return ClassifyResponse(
        label=label,
        score=score,
        model_info=ModelInfoResponse(
            run_id=info["run_id"],
            model_type=info["model_type"],
            test_accuracy=info["test_accuracy"],
        ),
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
