from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_url_accepts_bare_domain():
    response = client.post("/api/analyze-url", json={"url": "example.com"})
    assert response.status_code == 200
    assert response.json()["payload_type"] == "url"
    assert response.json()["risk_assessment"]["hostname"] == "example.com"


def test_analyze_url_rejects_plain_text():
    response = client.post("/api/analyze-url", json={"url": "this is just a sentence"})
    assert response.status_code == 422


def test_analyze_url_rejects_blank_value():
    response = client.post("/api/analyze-url", json={"url": "   "})
    assert response.status_code == 422


def test_scan_rejects_non_image_upload():
    response = client.post(
        "/api/scan",
        files={"file": ("note.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415
