from app.ml.url_features import FEATURE_COLUMNS, extract_url_features, get_hostname_group


def test_feature_extractor_returns_all_expected_numeric_features():
    features = extract_url_features("https://login.example.com/account?id=123")
    assert list(features) == FEATURE_COLUMNS
    assert all(isinstance(value, (int, float)) for value in features.values())


def test_feature_extractor_handles_bare_domain():
    features = extract_url_features("example.com/login")
    assert features["https_flag"] == 1
    assert features["tld_length"] == 3


def test_feature_extractor_detects_ip_and_suspicious_extension():
    features = extract_url_features("http://192.168.1.8/download/app.apk")
    assert features["has_ip_address"] == 1
    assert features["suspicious_file_extension"] == 1


def test_feature_extractor_counts_query_parameters_and_digits():
    features = extract_url_features("https://example.com/pay?id=123&ref=9")
    assert features["query_param_count"] == 2
    assert features["number_of_digits"] == 4


def test_hostname_group_is_stable():
    assert get_hostname_group("https://login.example.com/path") == "login.example.com"
