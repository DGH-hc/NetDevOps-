"""
Phase 3.10 - AegisAI Dataset Sanitizer

Detects and redacts common secrets and PII from the canonical dataset.
The sanitizer operates recursively on dictionaries, lists, and strings.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "datasets"
    / "aegis_dataset_v1.0.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "sanitized"
)

OUTPUT_PATH = OUTPUT_DIR / "aegis_dataset_v1.0_sanitized.json"
REPORT_PATH = OUTPUT_DIR / "sanitization_report.json"


PATTERNS = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "bearer_token": re.compile(
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"
    ),
    "api_key": re.compile(
        r"(?i)\b(?:api[_-]?key|apikey)\s*[:=]\s*[^\s,;]+"
    ),
    "password": re.compile(
        r"(?i)\bpassword\s*[:=]\s*[^\s,;]+"
    ),
    "secret": re.compile(
        r"(?i)\bsecret\s*[:=]\s*[^\s,;]+"
    ),
    "private_key": re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?"
        r"-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
}


def redact_string(
    value: str,
    findings: list[dict[str, Any]],
    path: str,
) -> str:
    """Redact secrets and PII from a string."""

    sanitized = value

    for category, pattern in PATTERNS.items():

        def replace(match: re.Match[str]) -> str:
            findings.append(
                {
                    "category": category,
                    "path": path,
                    "redacted_value": "[REDACTED]",
                }
            )
            return "[REDACTED]"

        sanitized = pattern.sub(
            replace,
            sanitized,
        )

    return sanitized


def sanitize_value(
    value: Any,
    findings: list[dict[str, Any]],
    path: str = "$",
) -> Any:
    """Recursively sanitize a JSON-compatible value."""

    if isinstance(value, dict):
        return {
            key: sanitize_value(
                item,
                findings,
                f"{path}.{key}",
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            sanitize_value(
                item,
                findings,
                f"{path}[{index}]",
            )
            for index, item in enumerate(value)
        ]

    if isinstance(value, str):
        return redact_string(
            value,
            findings,
            path,
        )

    return value


def sanitize_dataset(
    dataset: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Sanitize a complete AegisAI dataset."""

    findings: list[dict[str, Any]] = []

    sanitized_dataset = sanitize_value(
        dataset,
        findings,
    )

    report = {
        "sanitizer_version": "1.0",
        "records_processed": len(dataset),
        "findings_count": len(findings),
        "categories": sorted(
            {
                finding["category"]
                for finding in findings
            }
        ),
        "findings": findings,
    }

    return sanitized_dataset, report


def main() -> None:
    """Load, sanitize, and write the dataset."""

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "AegisAI dataset must be a JSON list."
        )

    sanitized_dataset, report = sanitize_dataset(
        dataset
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            sanitized_dataset,
            file,
            indent=4,
            ensure_ascii=False,
        )
        file.write("\n")

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )
        file.write("\n")

    print("Phase 3.10 Dataset Sanitization")
    print("================================")
    print(f"Records processed: {report['records_processed']}")
    print(f"Findings: {report['findings_count']}")
    print(f"Sanitized dataset: {OUTPUT_PATH}")
    print(f"Sanitization report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

def validate_sanitized_dataset(
    dataset: list[dict[str, Any]],
) -> None:
    """Fail if detectable secret/PII patterns remain."""

    findings: list[dict[str, Any]] = []

    sanitize_value(
        dataset,
        findings,
    )

    if findings:
        categories = sorted(
            {
                finding["category"]
                for finding in findings
            }
        )

        raise ValueError(
            "Sanitized dataset still contains "
            f"detectable sensitive data: {categories}"
        )

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