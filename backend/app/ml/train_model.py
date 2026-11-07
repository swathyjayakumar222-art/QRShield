"""Train and compare QRShield URL-phishing baseline models.

Expected CSV columns: URL and ClassLabel (0=phishing, 1=legitimate).
Run from the backend directory: python -m app.ml.train_model --dataset data/raw/url_features_extracted1.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.url_features import FEATURE_COLUMNS, extract_url_features, get_hostname_group


def train(dataset_path: Path, model_path: Path, random_state: int = 42) -> dict:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}. Download the CSV described in backend/data/README.md."
        )

    frame = pd.read_csv(dataset_path)
    required = {"URL", "ClassLabel"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            "Dataset is missing required column(s): " + ", ".join(sorted(missing))
            + ". Expected URL and ClassLabel."
        )

    frame = frame[["URL", "ClassLabel"]].copy()
    frame = frame.dropna(subset=["URL", "ClassLabel"])
    frame["URL"] = frame["URL"].astype(str).str.strip()
    frame["ClassLabel"] = pd.to_numeric(frame["ClassLabel"], errors="coerce")
    frame = frame.dropna(subset=["ClassLabel"])
    frame = frame[frame["URL"].str.len() > 0]
    frame = frame[frame["ClassLabel"].isin([0, 1])]
    frame = frame.drop_duplicates(subset=["URL"]).reset_index(drop=True)

    if len(frame) < 100:
        raise ValueError(f"Only {len(frame)} usable unique rows were found; at least 100 are required.")
    if frame["ClassLabel"].nunique() != 2:
        raise ValueError("The dataset must contain both ClassLabel values 0 and 1.")

    # Source labels: 0=phishing, 1=legitimate. Our positive class is phishing (1).
    y = (frame["ClassLabel"].astype(int) == 0).astype(int)
    feature_frame = pd.DataFrame(
        [extract_url_features(value) for value in frame["URL"]],
        columns=FEATURE_COLUMNS,
    )
    groups = frame["URL"].map(get_hostname_group)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=random_state)
    train_indices, test_indices = next(splitter.split(feature_frame, y, groups=groups))

    x_train = feature_frame.iloc[train_indices]
    x_test = feature_frame.iloc[test_indices]
    y_train = y.iloc[train_indices]
    y_test = y.iloc[test_indices]
    train_hosts = set(groups.iloc[train_indices])
    test_hosts = set(groups.iloc[test_indices])
    if train_hosts.intersection(test_hosts):
        raise RuntimeError("Host leakage detected between training and test sets.")

    candidates = {
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=random_state),
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=180,
            max_depth=18,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        ),
    }

    evaluations = {}
    best_name = None
    best_model = None
    best_f1 = -1.0
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, list(model.classes_).index(1)]
        f1 = f1_score(y_test, predictions, zero_division=0)
        evaluations[name] = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision_phishing": float(precision_score(y_test, predictions, zero_division=0)),
            "recall_phishing": float(recall_score(y_test, predictions, zero_division=0)),
            "f1_phishing": float(f1),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
            "confusion_matrix_labels_0_legitimate_1_phishing": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
            "classification_report": classification_report(
                y_test, predictions, labels=[0, 1], target_names=["legitimate", "phishing"],
                output_dict=True, zero_division=0,
            ),
        }
        if f1 > best_f1:
            best_f1 = f1
            best_name = name
            best_model = model

    model_path.parent.mkdir(parents=True, exist_ok=True)
    # After holdout evaluation is complete, refit the selected model on all cleaned rows
    # so the deployed artifact can use every labelled training example.
    final_model = clone(candidates[best_name])
    final_model.fit(feature_frame, y)

    bundle = {
        "model": final_model,
        "model_name": best_name,
        "feature_columns": FEATURE_COLUMNS,
        "positive_class": 1,
        "positive_class_name": "phishing",
        "label_mapping": {"0": "legitimate", "1": "phishing"},
    }
    joblib.dump(bundle, model_path)

    summary = {
        "dataset_file": dataset_path.name,
        "rows_used_after_cleaning": int(len(frame)),
        "training_rows": int(len(train_indices)),
        "test_rows": int(len(test_indices)),
        "training_hosts": int(len(train_hosts)),
        "test_hosts": int(len(test_hosts)),
        "host_overlap": int(len(train_hosts.intersection(test_hosts))),
        "positive_class": "phishing",
        "selected_model": best_name,
        "models": evaluations,
        "model_artifact": str(model_path),
        "warning": "Evaluation is dataset-specific. It is not proof of real-world detection performance or a safety guarantee.",
    }
    metrics_path = model_path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train QRShield URL-phishing classifiers.")
    parser.add_argument("--dataset", type=Path, default=Path("data/raw/url_features_extracted1.csv"))
    parser.add_argument("--output", type=Path, default=Path("models/qrshield_url_model.joblib"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    summary = train(args.dataset, args.output, args.seed)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
