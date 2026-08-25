import pytest

from scripts.aegis_dataset_quality import generate_quality_report


def valid_record():
    return {
        "dataset_version": "1.0",
        "incident": {
            "incident_id": "INC-001",
            "severity": "high",
            "confidence": 0.95,
        },
        "signals": [],
        "correlation": {},
        "timeline": [],
        "root_cause": {},
        "affected_components": [],
        "evidence": [
    {
        "source": "test",
        "message": "valid test evidence",
    }
],
        "context": {},
        "decision": {},
        "response_plan": {},
        "simulation": {},
        "provenance": {
            "source_phases": [
                "3.6",
                "3.7",
                "3.8",
                "3.9",
            ]
        },
    }


def test_empty_dataset_fails():
    report = generate_quality_report([])

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["record_count"] is False


def test_duplicate_incident_ids_fail():
    record_a = valid_record()
    record_b = valid_record()

    report = generate_quality_report(
        [record_a, record_b]
    )

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["duplicate_incident_ids"] is False
    assert "INC-001" in report["issues"]["duplicate_incident_ids"]


def test_missing_required_field_fails():
    record = valid_record()
    del record["evidence"]

    report = generate_quality_report([record])

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["required_fields"] is False


def test_invalid_severity_fails():
    record = valid_record()
    record["incident"]["severity"] = "unknown"

    report = generate_quality_report([record])

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["valid_severity"] is False


def test_invalid_confidence_fails():
    record = valid_record()
    record["incident"]["confidence"] = 1.5

    report = generate_quality_report([record])

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["valid_confidence"] is False


def test_missing_source_phase_fails():
    record = valid_record()
    record["provenance"]["source_phases"] = [
        "3.6",
        "3.7",
        "3.8",
    ]

    report = generate_quality_report([record])

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["source_phase_coverage"] is False


def test_valid_dataset_passes():
    record = valid_record()

    report = generate_quality_report([record])

    assert report["quality_status"] == "PASS"
    assert all(report["checks"].values())

def test_complete_record_has_100_percent_completeness():
    record = valid_record()

    report = generate_quality_report([record])

    assert (
        report["metrics"]["completeness_percentage"]
        == 100.0
    )


def test_missing_required_field_reduces_completeness():
    record = valid_record()
    del record["evidence"]

    report = generate_quality_report([record])

    assert (
        report["metrics"]["completeness_percentage"]
        < 100.0
    )


def test_empty_dataset_has_zero_completeness():
    report = generate_quality_report([])

    assert (
        report["metrics"]["completeness_percentage"]
        == 0.0
    )

def test_missing_evidence_fails():
    record = valid_record()
    record["evidence"] = []

    report = generate_quality_report([record])

    assert report["quality_status"] == "FAIL"
    assert report["checks"]["evidence_coverage"] is False
    assert "INC-001" in report["issues"]["missing_evidence"]