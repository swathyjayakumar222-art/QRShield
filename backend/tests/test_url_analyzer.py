from app.services.url_analyzer import analyze_url, classify_payload


def test_classifies_http_url():
    assert classify_payload("https://example.com/login") == "url"


def test_classifies_bare_domain_as_url():
    assert classify_payload("example.com/account") == "url"


def test_classifies_www_domain_as_url():
    assert classify_payload("www.example.com") == "url"


def test_classifies_wifi_payload():
    assert classify_payload("WIFI:T:WPA;S:CampusWiFi;P:samplepass;;") == "wifi"


def test_classifies_plain_text():
    assert classify_payload("Welcome to the campus fest") == "text"


def test_http_url_gets_transport_warning():
    result = analyze_url("http://example.com")
    assert result["risk_score"] >= 15
    assert any(item["code"] == "http_scheme" for item in result["findings"])


def test_private_ip_gets_high_risk_indicator():
    result = analyze_url("http://192.168.1.10/login")
    assert result["risk_level"] == "high"
    assert any(item["code"] == "non_global_ip" for item in result["findings"])


def test_shortened_url_is_flagged_without_following_it():
    result = analyze_url("https://bit.ly/example")
    assert any(item["code"] == "shortener" for item in result["findings"])
    assert "has not been checked" in result["findings"][0]["message"] or any(
        "final destination has not been checked" in item["message"] for item in result["findings"]
    )


def test_low_score_is_not_presented_as_a_safety_guarantee():
    result = analyze_url("https://example.com")
    assert result["risk_level"] == "low"
    assert "does not prove safety" in result["disclaimer"]


def test_malformed_url_is_reported_as_invalid():
    result = analyze_url("https://[::1")
    assert any(item["code"] == "invalid_url" for item in result["findings"])
