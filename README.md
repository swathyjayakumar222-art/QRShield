# QRShield

**QRShield: An Explainable Multi-Layer Framework for Context-Aware QR Code Fraud Detection and Safe Destination Verification**

QRShield is an academic research prototype that helps users inspect QR-code contents before visiting a destination. The first milestone accepts a QR image, decodes its content, identifies the payload type, and displays basic URL indicators with an explainable heuristic assessment.

> **Important:** A low-risk result is not proof that a destination is safe. QRShield does not automatically open or contact decoded URLs.

## Current features

- Upload a QR-code image from the React interface.
- Validate the upload and enforce a 5 MB limit.
- Decode QR content using OpenCV.
- Identify URL, email, telephone, Wi-Fi, payment/crypto URI, other URI, and plain-text payloads.
- Recognise both full URLs and bare domains such as `example.com`.
- Analyse basic URL indicators locally: HTTP scheme, IP-literal host, known URL-shortening host, Punycode hostname, user-information fields, unusual URL length, and malformed URL/port formats.
- Show the heuristic score, risk level, reasons, and a caution message.
- Never follow redirects, perform DNS lookups, fetch webpages, or automatically open scanned destinations.

## Technology

- **Frontend:** React 19 + Vite
- **Backend:** Python + FastAPI
- **QR decoding:** OpenCV
- **Image handling:** Pillow + NumPy
- **Validation:** Pydantic
- **Tests:** pytest + FastAPI TestClient

## Project structure

```
QRShield/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── qr_decoder.py
│   │       └── url_analyzer.py
│   ├── tests/
│   │   ├── test_api.py
│   │   └── test_url_analyzer.py
│   ├── requirements.txt
│   └── requirements-dev.txt
└── frontend/
    ├── .env.example
    ├── package.json
    └── src/
```

## Run locally on Windows

Open a terminal in the repository folder.

### 1. Start the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.  
Interactive API documentation: `http://127.0.0.1:8000/docs`.

If PowerShell blocks virtual-environment activation, use Command Prompt and run:

```bat
.venv\Scripts\activate.bat
```

### 2. Start the frontend

Open a **second terminal** at the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local address printed by Vite (normally `http://localhost:5173`).

The frontend uses `http://127.0.0.1:8000` by default. To change it, copy `.env.example` to `.env` and edit `VITE_API_BASE_URL`.

## Run backend tests

From the `backend` folder, install the development dependencies:

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

The tests cover payload classification, common URL indicators, malformed input, the health endpoint, and API validation.

## Train the URL-based ML baseline

The ML training pipeline uses the LegitPhish Dataset, Version 2. Download instructions, label meanings, license details and attribution are documented in [backend/data/README.md](backend/data/README.md).

1. Download Version 2 from https://data.mendeley.com/datasets/hx4m73v2sf/2.
2. Extract `url_features_extracted1.csv` to `backend/data/raw/url_features_extracted1.csv`.
3. From the `backend` folder, install the optional ML dependencies and train:

```powershell
pip install -r requirements-ml.txt
python -m app.ml.train_model
```

The script derives the same 16 URL features used by QRShield, removes exact duplicate URLs, creates a five-fold stratified hostname-grouped holdout split, compares Logistic Regression and Random Forest, and writes the best model to `backend/models/qrshield_url_model.joblib` with a metrics report beside it. The dataset and generated model are not committed to Git.

**Important:** The scan API checks for a saved model automatically. Before a model exists, it clearly reports that ML is not trained and continues to use the rule-based assessment. After training, restart the backend; the ML panel will show the model's phishing-pattern score. Install the ML dependencies in the same Python environment used to run the backend.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check that the API is running |
| POST | `/api/scan` | Upload and analyse a QR-code image |
| POST | `/api/analyze-url` | Analyse a URL supplied as JSON |

Example request for `/api/analyze-url`:

```json
{
  "url": "https://example.com/login"
}
```

## How to interpret the score

The score is produced by a small, transparent set of rules. It is **not** a trained machine-learning prediction and is not a verified probability of fraud. A low score means only that this limited rule set did not find many indicators. A malicious page can still use a normal-looking HTTPS URL, and a warning indicator can sometimes appear on a legitimate site.

## Security principles

- Treat QR payloads as untrusted input.
- Never automatically navigate to scanned destinations.
- Do not fetch user-provided URLs from the API in this milestone.
- Do not treat HTTPS or the absence of a warning as proof of trust.
- Keep uploaded images and decoded personal data out of persistent storage by default.
- Any future redirect inspection must be isolated and must block loopback, private, link-local and reserved IP ranges; restrict protocols and ports; limit redirects, response sizes and timeouts; and defend against SSRF and DNS rebinding.

## Roadmap

1. **Milestone 1 — QR decode + baseline rules:** implemented in this repository.
2. **Milestone 2 — dataset preparation + ML model:** select a documented, legally usable dataset; establish a leakage-resistant train/test split; train and compare baseline classifiers; evaluate precision, recall, F1, false-positive rate and confusion matrix.
3. **Milestone 3 — contextual enrichment:** consider carefully isolated redirect/reputation checks and OCR-based comparison between surrounding poster text and the decoded destination.

Future features will be labelled clearly and will not be presented as implemented until they are working and evaluated.
