import pytest

from scripts.sanitize_aegis_dataset import sanitize_dataset


def test_redacts_email():
    dataset = [
        {
            "context": {
                "contact": "admin@example.com"
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert sanitized[0]["context"]["contact"] == "[REDACTED]"
    assert report["findings_count"] == 1
    assert "email" in report["categories"]


def test_redacts_password():
    dataset = [
        {
            "context": {
                "credentials": "password=SuperSecret123"
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert "SuperSecret123" not in str(sanitized)
    assert "[REDACTED]" in sanitized[0]["context"]["credentials"]
    assert "password" in report["categories"]


def test_redacts_api_key():
    dataset = [
        {
            "context": {
                "config": "api_key=abc123SECRET"
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert "abc123SECRET" not in str(sanitized)
    assert "[REDACTED]" in sanitized[0]["context"]["config"]
    assert "api_key" in report["categories"]


def test_redacts_bearer_token():
    dataset = [
        {
            "context": {
                "authorization": "Bearer abc123tokenVALUE"
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert "abc123tokenVALUE" not in str(sanitized)
    assert "[REDACTED]" in sanitized[0]["context"]["authorization"]
    assert "bearer_token" in report["categories"]


def test_redacts_secret():
    dataset = [
        {
            "context": {
                "configuration": "secret=MyDatabaseSecret"
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert "MyDatabaseSecret" not in str(sanitized)
    assert "[REDACTED]" in sanitized[0]["context"]["configuration"]
    assert "secret" in report["categories"]


def test_redacts_private_key():
    private_key = """-----BEGIN PRIVATE KEY-----
FAKE_PRIVATE_KEY_DATA
-----END PRIVATE KEY-----"""

    dataset = [
        {
            "evidence": private_key
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert "FAKE_PRIVATE_KEY_DATA" not in str(sanitized)
    assert "[REDACTED]" in sanitized[0]["evidence"]
    assert "private_key" in report["categories"]


def test_nested_values_are_sanitized():
    dataset = [
        {
            "incident": {
                "metadata": {
                    "owner": {
                        "email": "user@example.com"
                    }
                }
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert (
        sanitized[0]["incident"]["metadata"]["owner"]["email"]
        == "[REDACTED]"
    )

    assert report["findings_count"] == 1


def test_non_sensitive_values_are_preserved():
    dataset = [
        {
            "incident": {
                "incident_id": "INC-001",
                "severity": "critical",
                "confidence": 0.95,
            }
        }
    ]

    sanitized, report = sanitize_dataset(dataset)

    assert sanitized == dataset
    assert report["findings_count"] == 0
def test_validation_rejects_remaining_sensitive_data():
    from scripts.sanitize_aegis_dataset import (
        validate_sanitized_dataset,
    )

    dataset = [
        {
            "context": {
                "credentials": "password=StillSecret123"
            }
        }
    ]

    with pytest.raises(
        ValueError,
        match="still contains detectable sensitive data",
    ):
        validate_sanitized_dataset(dataset)

def test_validation_rejects_remaining_sensitive_data():
    from scripts.sanitize_aegis_dataset import (
        validate_sanitized_dataset,
    )

    dataset = [
        {
            "context": {
                "credentials": "password=StillSecret123"
            }
        }
    ]

    with pytest.raises(
        ValueError,
        match="still contains detectable sensitive data",
    ):
        validate_sanitized_dataset(dataset)
