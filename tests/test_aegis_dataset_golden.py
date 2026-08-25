from scripts.aegis_dataset_golden import compare_datasets


def valid_record():
    return {
        "dataset_version": "1.0",
        "incident": {
            "incident_id": "INC-001",
            "severity": "medium",
            "confidence": 0.75,
        },
    }


def test_matching_datasets_pass():
    current_dataset = [valid_record()]
    golden_dataset = [valid_record()]

    report = compare_datasets(
        current_dataset,
        golden_dataset,
    )

    assert report["golden_status"] == "PASS"
    assert report["datasets_match"] is True
    assert report["current_records"] == 1
    assert report["golden_records"] == 1
    assert report["differences"] == []


def test_different_datasets_fail():
    current_record = valid_record()
    golden_record = valid_record()

    current_record["incident"]["severity"] = "high"

    report = compare_datasets(
        [current_record],
        [golden_record],
    )

    assert report["golden_status"] == "FAIL"
    assert report["datasets_match"] is False
    assert len(report["differences"]) == 1
    assert (
          "Record 0: incident.severity differs: "
          "current='high', golden='medium'"
          in report["differences"]
        )