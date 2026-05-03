from io import BytesIO
from typing import Literal

import qrcode
import qrcode.constants as qr_const
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response

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


app = FastAPI(title="qr-gen-web")


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
