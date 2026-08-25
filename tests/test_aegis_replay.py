import pytest

from scripts.replay_aegis_dataset import (
    compare_replayed_dataset,
    load_dataset,
    replay_dataset,
    replay_from_sources,
)


def test_replay_rejects_invalid_schema():
    dataset = [
        {
            "incident": {
                "incident_id": "INC-001",
            }
        }
    ]

    with pytest.raises(Exception):
        replay_dataset(dataset)


def test_replay_rejects_duplicate_incident_ids():
    dataset = [
        {
            "dataset_version": "1.0",
            "incident": {
                "incident_id": "INC-001",
            },
        },
        {
            "dataset_version": "1.0",
            "incident": {
                "incident_id": "INC-001",
            },
        },
    ]

    with pytest.raises(Exception):
        replay_dataset(dataset)


def test_load_dataset_rejects_non_list(tmp_path):
    path = tmp_path / "invalid.json"

    path.write_text(
        '{"dataset_version": "1.0"}',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="must be a JSON list",
    ):
        load_dataset(path)


def test_load_dataset_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.json"

    with pytest.raises(
        FileNotFoundError,
        match="Dataset not found",
    ):
        load_dataset(path)

def test_compare_replayed_dataset_passes_when_datasets_match():
    expected_dataset = [
        {
            "dataset_version": "1.0",
            "incident": {
                "incident_id": "INC-001",
            },
        }
    ]

    replayed_dataset = [
        {
            "dataset_version": "1.0",
            "incident": {
                "incident_id": "INC-001",
            },
        }
    ]

    report = compare_replayed_dataset(
        expected_dataset,
        replayed_dataset,
    )

    assert report["replay_status"] == "PASS"
    assert report["replay_match"] is True
    assert report["differences"] == []

def test_compare_replayed_dataset_detects_difference():
    expected_dataset = [
        {
            "dataset_version": "1.0",
            "incident": {
                "incident_id": "INC-001",
            },
        }
    ]

    replayed_dataset = [
        {
            "dataset_version": "1.0",
            "incident": {
                "incident_id": "INC-002",
            },
        }
    ]

    report = compare_replayed_dataset(
        expected_dataset,
        replayed_dataset,
    )

    assert report["replay_status"] == "FAIL"
    assert report["replay_match"] is False
    assert report["differences"]