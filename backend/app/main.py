"""QRShield API — first milestone."""
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.qr_decoder import QRDecodeError, decode_qr_image
from app.services.url_analyzer import analyze_url, classify_payload

app = FastAPI(
    title="QRShield API",
    description="QR decoding and explainable baseline risk analysis. Destinations are never opened.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "QRShield API", "version": "0.1.0"}


@app.post("/api/scan")
async def scan_qr(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image file.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
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
        })
    return {"count": len(results), "results": results}


@app.post("/api/analyze-url")
def analyze_url_endpoint(body: dict):
    value = body.get("url") if isinstance(body, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail="Provide a non-empty URL string.")
    if len(value) > 2048:
        raise HTTPException(status_code=400, detail="URL is too long (maximum 2048 characters).")
    return {"payload_type": classify_payload(value), "risk_assessment": analyze_url(value)}
