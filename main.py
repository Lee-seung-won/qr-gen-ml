from fastapi import FastAPI


app = FastAPI(title="qr-gen-web")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "qr-gen-web is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
