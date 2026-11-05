# QRShield

**QRShield: An Explainable Multi-Layer Framework for Context-Aware QR Code Fraud Detection and Safe Destination Verification**

QRShield is an academic research prototype that helps users inspect QR-code contents before visiting a destination. The first milestone decodes QR images, identifies payload types, extracts basic URL indicators, and presents an explainable heuristic assessment.

> **Important:** A low-risk result is not proof that a destination is safe. QRShield never automatically opens decoded URLs.

## Planned layers
1. QR image upload and decoding.
2. Payload-type recognition (URL, text, email, telephone, Wi-Fi and other URI types).
3. Explainable URL feature analysis.
4. Later: controlled redirect inspection and reputation signals.
5. Later: a trained phishing classifier and optional OCR-based context comparison.

## Stack
- Backend: Python, FastAPI
- Frontend: React, Vite
- QR decoding: OpenCV, pyzbar
- Planned ML: scikit-learn after dataset selection and evaluation design

## Run locally

Backend (Python 3.10+):
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

Frontend (second terminal):
```bash
cd frontend
npm install
npm run dev
```

## Current milestone
QR decoding + local, transparent baseline URL analysis. No trained ML model, live reputation check, DNS lookup, redirect inspection, or webpage fetching is implemented yet.

## Security principles
- Never automatically navigate to scanned URLs.
- Do not fetch user-provided URLs from the API in this milestone.
- Treat QR payloads and any future OCR text as untrusted.
- Future redirect inspection must use strict egress controls, block private/loopback/link-local/reserved IPs, limit protocols, ports, redirects, timeouts and response sizes, and defend against SSRF and DNS rebinding.
- HTTPS alone does not establish legitimacy.

## Evaluation plan
For a future classifier, report precision, recall, F1, false-positive rate, confusion matrix and inference time. Prevent data leakage by separating duplicate and near-duplicate URLs across train/test sets. Record each dataset's source, date, license and label provenance.

**Status:** Milestone 1 scaffold and baseline implementation.
