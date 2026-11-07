"""Deterministic URL features shared by model training and inference.

This module is offline-only: it never resolves DNS or contacts a URL.
"""
from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import parse_qsl, urlsplit

FEATURE_COLUMNS = [
    "url_length",
    "has_ip_address",
    "dot_count",
    "https_flag",
    "url_entropy",
    "token_count",
    "subdomain_count",
    "query_param_count",
    "tld_length",
    "path_length",
    "has_hyphen_in_domain",
    "number_of_digits",
    "tld_popularity",
    "suspicious_file_extension",
    "domain_name_length",
    "percentage_numeric_chars",
]

POPULAR_TLDS = {
    "com", "org", "net", "edu", "gov", "in", "uk", "us", "io", "co", "info"
}
SUSPICIOUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".msi", ".apk", ".zip", ".rar", ".js"
}


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _parse_url(value: str):
    raw = value.strip()
    candidate = raw if "://" in raw else "https://" + raw
    try:
        return urlsplit(candidate)
    except ValueError:
        return urlsplit("")


def extract_url_features(url: str) -> dict[str, int | float]:
    """Extract the 16 lexical/structural features used by QRShield's baseline ML model."""
    raw = str(url).strip()
    parsed = _parse_url(raw)
    host = (parsed.hostname or "").lower().rstrip(".")
    labels = host.split(".") if host else []

    try:
        ipaddress.ip_address(host)
        has_ip = 1
    except ValueError:
        has_ip = 0

    tld = labels[-1] if len(labels) >= 2 else ""
    domain_label = labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")
    digits = sum(character.isdigit() for character in raw)
    path_extension = PurePosixPath(parsed.path.lower()).suffix
    try:
        query_count = len(parse_qsl(parsed.query, keep_blank_values=True))
    except ValueError:
        query_count = 0

    return {
        "url_length": len(raw),
        "has_ip_address": has_ip,
        "dot_count": raw.count("."),
        "https_flag": int(parsed.scheme.lower() == "https"),
        "url_entropy": _entropy(raw),
        "token_count": len(re.findall(r"[A-Za-z0-9]+", raw)),
        # Approximation based on hostname labels; this avoids online public-suffix lookups.
        "subdomain_count": max(len(labels) - 2, 0),
        "query_param_count": query_count,
        "tld_length": len(tld),
        "path_length": len(parsed.path),
        "has_hyphen_in_domain": int("-" in host),
        "number_of_digits": digits,
        "tld_popularity": int(tld in POPULAR_TLDS),
        "suspicious_file_extension": int(path_extension in SUSPICIOUS_EXTENSIONS),
        "domain_name_length": len(domain_label),
        "percentage_numeric_chars": (digits / len(raw) * 100.0) if raw else 0.0,
    }


def get_hostname_group(url: str) -> str:
    """Return the hostname used to keep a host in one data split."""
    parsed = _parse_url(str(url))
    return (parsed.hostname or str(url).strip().lower()).lower()
