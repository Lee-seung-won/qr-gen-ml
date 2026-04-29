from io import BytesIO

import qrcode
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response


app = FastAPI(title="qr-gen-web")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "qr-gen-web is running"}


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
