# QRShield training data

The URL-based ML baseline is designed for the **LegitPhish Dataset, Version 2**.

- Dataset page: https://data.mendeley.com/datasets/hx4m73v2sf/2
- DOI: https://doi.org/10.17632/hx4m73v2sf.2
- File: `url_features_extracted1.csv`
- Expected columns: `URL` and `ClassLabel`
- Label convention: `0 = phishing`, `1 = legitimate`
- Dataset page lists 101,219 URLs and 18 fields including the label.
- License shown on the dataset page: Creative Commons Attribution 4.0 International (CC BY 4.0).

## Setup

1. Open the dataset page above and download Version 2.
2. Extract `url_features_extracted1.csv` into this folder's `raw` subfolder so the path is:
   `backend/data/raw/url_features_extracted1.csv`.
3. Install the ML dependencies from the backend folder:
   `pip install -r requirements-ml.txt`.
4. Run the training command in the main README.

The CSV and trained model files are intentionally excluded from Git. Keep the source dataset locally and cite it in reports.

## Attribution

Potpelwar, R., Kulkarni, U., & Waghmare, J. (2025). *LegitPhish Dataset* (Version 2). Mendeley Data. https://doi.org/10.17632/hx4m73v2sf.2

## Scope and limitations

This is a phishing-URL dataset, not a QR-image dataset. QRShield decodes a QR code first and then analyses the URL string with the same URL feature extractor used during model training. The model therefore learns URL-level patterns; it does not learn visual QR-code patterns or prove that a URL is safe. Dataset labels and historical collection dates can become stale as websites change.

The feature extractor derives its own numeric features from the raw URL so training and live inference can use the same code. Its subdomain count and domain-name length are simple hostname-label approximations and do not use a public-suffix database.
