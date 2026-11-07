"""Optional inference adapter for a locally trained QRShield URL model."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from app.ml.url_features import extract_url_features

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "qrshield_url_model.joblib"


def _model_path() -> Path:
    return Path(os.environ.get("QRSHIELD_MODEL_PATH", str(DEFAULT_MODEL_PATH))).expanduser()


@lru_cache(maxsize=1)
def _load_bundle(path_string: str):
    import joblib
    return joblib.load(path_string)


def predict_url(url: str) -> dict:
    """Return an optional ML signal; never describe a URL as definitely safe."""
    path = _model_path()
    if not path.is_file():
        return {
            "available": False,
            "status": "not_trained",
            "message": "The ML model has not been trained yet. This scan uses the explainable rule-based assessment only.",
        }

    try:
        import pandas as pd
        bundle = _load_bundle(str(path.resolve()))
    except ImportError:
        return {
            "available": False,
            "status": "dependencies_missing",
            "message": "Install the optional ML packages with: pip install -r requirements-ml.txt",
        }

    features = extract_url_features(url)
    columns = bundle["feature_columns"]
    row = pd.DataFrame([{name: features[name] for name in columns}], columns=columns)
    model = bundle["model"]
    probabilities = model.predict_proba(row)[0]
    classes = list(model.classes_)
    if 1 not in classes:
        raise ValueError("The saved model does not include the phishing class (1).")

    phishing_score = float(probabilities[classes.index(1)])
    prediction = "potential_phishing" if phishing_score >= float(bundle.get("threshold", 0.5)) else "no_phishing_signal"
    return {
        "available": True,
        "status": "model_ready",
        "model_name": bundle.get("model_name", "QRShield URL classifier"),
        "prediction": prediction,
        "phishing_score": round(phishing_score * 100, 1),
        "disclaimer": "This score reflects patterns learned from the training dataset. It is not a verified probability of harm and does not guarantee safety.",
    }
