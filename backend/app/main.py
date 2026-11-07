"""QRShield API — QR decoding, heuristic analysis and optional ML inference."""

from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.ml.predict import predict_url
from app.services.qr_decoder import QRDecodeError, decode_qr_image
from app.services.url_analyzer import analyze_url, classify_payload

app = FastAPI(
    title="QRShield API",
    description="QR decoding and explainable URL analysis. Destinations are never opened.",
    version="0.3.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class AnalyzeURLRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def strip_and_validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("URL cannot be blank.")
        return value


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "QRShield API", "version": "0.3.0"}


@app.post("/api/scan")
async def scan_qr(file: UploadFile = File(...)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        await file.close()
        raise HTTPException(status_code=415, detail="Please upload an image file.")

    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 5 MB upload limit.")

    try:
        decoded = decode_qr_image(content)
    except QRDecodeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = []
    for item in decoded:
        payload = item["payload"]
        kind = classify_payload(payload)
        results.append({
            "payload_type": kind,
            "payload": payload,
            "risk_assessment": analyze_url(payload) if kind == "url" else None,
            "ml_assessment": predict_url(payload) if kind == "url" else None,
        })
    return {"count": len(results), "results": results}


@app.post("/api/analyze-url")
def analyze_url_endpoint(body: AnalyzeURLRequest) -> dict:
    if classify_payload(body.url) != "url":
        raise HTTPException(status_code=422, detail="The supplied content is not recognised as an HTTP or HTTPS URL.")
    return {
        "payload_type": "url",
        "risk_assessment": analyze_url(body.url),
        "ml_assessment": predict_url(body.url),
    }
