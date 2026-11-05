"""Local URL indicators. No DNS, redirects, or network requests are performed."""
import ipaddress
import re
from urllib.parse import urlsplit

SHORTENER_HOSTS = {"bit.ly", "tinyurl.com", "t.co", "ow.ly", "is.gd", "buff.ly", "rb.gy"}


def classify_payload(payload: str) -> str:
    value = payload.strip()
    lower = value.lower()
    if lower.startswith(("https://", "http://", "www.")):
        return "url"
    if lower.startswith("mailto:"):
        return "email"
    if lower.startswith("tel:"):
        return "telephone"
    if lower.startswith("wifi:"):
        return "wifi"
    if lower.startswith(("bitcoin:", "ethereum:")):
        return "payment_or_crypto_uri"
    if re.match(r"^[a-z][a-z0-9+.-]*:", lower):
        return "other_uri"
    return "text"


def analyze_url(value: str) -> dict:
    raw = value.strip()
    candidate = raw if "://" in raw else "https://" + raw
    parsed = urlsplit(candidate)
    findings = []
    score = 0
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().rstrip(".")

    if scheme not in {"http", "https"}:
        findings.append({"severity": "high", "code": "unsupported_scheme", "message": "The URL does not use HTTP or HTTPS."})
        score += 45
    elif scheme == "http":
        findings.append({"severity": "medium", "code": "http_scheme", "message": "The URL uses unencrypted HTTP."})
        score += 15

    if not host:
        findings.append({"severity": "high", "code": "missing_hostname", "message": "A valid hostname could not be identified."})
        score += 45
    else:
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                findings.append({"severity": "high", "code": "non_global_ip", "message": "The destination uses a non-public IP address."})
                score += 45
            else:
                findings.append({"severity": "medium", "code": "ip_literal_host", "message": "The URL uses an IP address instead of a domain name."})
                score += 20
        except ValueError:
            if host in SHORTENER_HOSTS:
                findings.append({"severity": "medium", "code": "shortener", "message": "This is a known URL-shortening host; its final destination has not been checked."})
                score += 15
        if host.startswith("xn--") or ".xn--" in host:
            findings.append({"severity": "medium", "code": "punycode_hostname", "message": "The hostname contains an internationalized Punycode label."})
            score += 15
        if len(host) > 60:
            findings.append({"severity": "low", "code": "long_hostname", "message": "The hostname is unusually long."})
            score += 5

    if parsed.username is not None or parsed.password is not None:
        findings.append({"severity": "high", "code": "userinfo", "message": "The URL contains user-information fields before the hostname."})
        score += 25
    if "@" in raw:
        findings.append({"severity": "medium", "code": "at_symbol", "message": "The URL contains an @ symbol that can make its structure confusing."})
        score += 10
    if len(raw) > 180:
        findings.append({"severity": "low", "code": "long_url", "message": "The URL is unusually long."})
        score += 5

    score = min(score, 100)
    level = "high" if score >= 50 else "medium" if score >= 20 else "low"
    if not findings:
        findings.append({"severity": "info", "code": "no_basic_indicators", "message": "No indicators in this limited baseline rule set were detected."})
    return {
        "risk_score": score,
        "risk_level": level,
        "findings": findings,
        "hostname": host or None,
        "scheme": scheme or None,
        "disclaimer": "Heuristic only. A low score does not prove safety. No reputation lookup, DNS request, redirect check, or webpage inspection was performed."
    }
