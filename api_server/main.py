import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from api_server.security import api_key_valid

app = FastAPI(
    title="Firsat API",
    description="Trendyol, Hepsiburada, N11, CicekSepeti, MediaMarkt, "
    "Teknosa, Vatan Bilgisayar, Amazon tarama verileri. "
    "Tum isteklerde X-API-Key header'i zorunludur.",
    version="1.0.0",
)

DATA_DIR = Path(os.getenv("DATA_DIR", "docs")) / "api"


def _load(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail="Veri bulunamadi")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Veri okunamadi")


def require_api_key(x_api_key: str = Header(default=None)):
    if not api_key_valid(x_api_key):
        raise HTTPException(
            status_code=403, detail="Gecersiz veya eksik API anahtari"
        )
    return x_api_key


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "firsat-api",
        "endpoints": [
            "/products",
            "/discounts",
            "/errors",
            "/stats",
            "/changes",
            "/history",
            "/stores/{site}",
            "/health",
        ],
        "auth": "X-API-Key header zorunludur",
    }


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/products", dependencies=[Depends(require_api_key)])
def products():
    return _load(DATA_DIR / "products.json")


@app.get("/discounts", dependencies=[Depends(require_api_key)])
def discounts():
    return _load(DATA_DIR / "discounts.json")


@app.get("/errors", dependencies=[Depends(require_api_key)])
def errors():
    return _load(DATA_DIR / "errors.json")


@app.get("/stats", dependencies=[Depends(require_api_key)])
def stats():
    return _load(DATA_DIR / "stats.json")


@app.get("/changes", dependencies=[Depends(require_api_key)])
def changes():
    return _load(DATA_DIR / "changes.json")


@app.get("/history", dependencies=[Depends(require_api_key)])
def history():
    return _load(DATA_DIR / "history.json")


@app.get("/stores/{site}", dependencies=[Depends(require_api_key)])
def store(site: str):
    return _load(DATA_DIR / "stores" / ("%s.json" % site))


@app.exception_handler(HTTPException)
def http_exception_handler(request, exc):
    body = {"detail": exc.detail}
    if exc.status_code == 403:
        body["hint"] = "Gecerli bir X-API-Key header'i gonderin"
    return JSONResponse(status_code=exc.status_code, content=body)
