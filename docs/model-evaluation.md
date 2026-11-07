# QRShield — URL model training report

## Dataset

**LegitPhish Dataset, Version 2**  
Dataset DOI: [10.17632/hx4m73v2sf.2](https://doi.org/10.17632/hx4m73v2sf.2)  
Data article: Potpelwar, R. S., Kulkarni, U. V., & Waghmare, J. M. (2025). *LegitPhish: A large-scale annotated dataset for URL-based phishing detection*. Data in Brief, 63, 111972. [https://doi.org/10.1016/j.dib.2025.111972](https://doi.org/10.1016/j.dib.2025.111972).

The supplied CSV contains 101,219 rows. Its source label convention is CLASSLABEL 0 for phishing and CLASSLABEL 1 for legitimate URLs.

## Cleaning

| Check | Result |
|---|---:|
| Rows supplied | 101,219 |
| Rows removed for missing URL/label | 1 |
| Duplicate URL rows removed | 346 |
| Unique rows used | 100,872 |
| Phishing URLs used | 63,492 |
| Legitimate URLs used | 37,380 |

The model target was mapped so that 1 = phishing and 0 = legitimate.

## Feature handling

The CSV also provides engineered feature columns. QRShield uses the raw URL and ClassLabel columns, then derives its own 16 features through app/ml/url_features.py. The same function is used at inference time. This avoids training on one set of precomputed feature definitions and silently using a different calculation on a QR code scanned later.

Features include URL length, IP-literal host, dot count, HTTPS, Shannon entropy, token count, approximate subdomain count, query parameters, TLD length, path length, hyphens, digits, TLD popularity, suspicious file extension, approximate domain-label length, and numeric-character percentage.

These are lexical/structural indicators only. The pipeline makes no DNS lookups and does not fetch URLs.

## Evaluation method

- Splitter: StratifiedGroupKFold with 5 folds, shuffle enabled and random seed 42.
- The first fold was used as the holdout (approximately 80% training / 20% test).
- Rows were grouped by exact hostname to keep the same exact hostname out of both partitions.
- Training rows: 80,697.
- Test rows: 20,175.
- Exact hostname overlap: 0.
- The selected classifier was then refitted on all 100,872 cleaned rows for the downloadable application model.

**Grouping limitation:** grouping uses the complete hostname. Different subdomains under the same registrable domain can still appear in separate partitions. A future evaluation should group by registrable domain using a maintained Public Suffix List and should include a separate time-based or external test set.

## Holdout results

Phishing is the positive class.

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Accuracy | 99.46% | **99.70%** |
| Precision (phishing) | 99.90% | 99.57% |
| Recall (phishing) | 99.24% | **99.96%** |
| F1-score (phishing) | 99.57% | **99.76%** |
| ROC-AUC | 99.947% | **99.997%** |

Random Forest was selected by phishing-class F1-score.

### Random Forest confusion matrix

Rows are actual labels; columns are predicted labels. Label order is [legitimate, phishing].

|  | Predicted legitimate | Predicted phishing |
|---|---:|---:|
| Actual legitimate | 7,421 | 55 |
| Actual phishing | 5 | 12,694 |

This corresponds to 55 legitimate URLs flagged as potential phishing and 5 phishing URLs missed in this holdout. Even a small number of false negatives matters in a security application.

## Interpretation and limitations

The scores are high on this dataset's holdout but must not be described as QRShield's real-world accuracy. The dataset's collection sources and patterns may be easier to separate than current, unseen phishing campaigns. Labels can become stale, and URL structure alone cannot establish whether a website is safe.

The model output is therefore presented as a **phishing-pattern signal**, not a definitive verdict or verified probability of harm. QRShield should be evaluated later on an independent, time-separated dataset and on URLs gathered from QR-code use cases.

## Reproducing the run

From the backend directory:

    pip install -r requirements-ml.txt
    python -m app.ml.train_model --dataset data/raw/url_features_extracted1.csv --seed 42

The CSV should be stored locally at backend/data/raw/url_features_extracted1.csv. Raw datasets and generated model files are not committed to this repository.

## Attribution

The dataset is distributed under CC BY 4.0 according to its Mendeley Data record. Cite the dataset and article when using it in a report or presentation.

## Small manual sanity check outside the holdout

A few common, manually selected URLs were passed through the saved Random Forest model as a smoke check. The model did not consistently treat familiar legitimate services as low-risk: examples such as Stack Overflow, Amazon, example.com and a Microsoft sign-in URL received phishing-pattern scores above the 0.5 decision threshold. This was not a labelled benchmark and is not included in the metrics above, but it exposes an important generalisation weakness. The model should be used as a research signal only until it has been evaluated on a larger, independently labelled and time-separated set of legitimate and phishing URLs.
