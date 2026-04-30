from io import BytesIO

import qrcode
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response

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
      <label for="text">입력값</label>
      <input id="text" name="text" type="text" minlength="1" maxlength="500" required />
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
def create_qr(text: str = Query(..., min_length=1, max_length=500)) -> Response:
    text = text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="text must not be empty")
    qr_image = qrcode.make(text)
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    return Response(content=buffer.getvalue(), media_type="image/png")
