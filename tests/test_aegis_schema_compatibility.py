import pytest

from scripts.aegis_schema_compatibility import (
    check_schema_compatibility,
    compare_schema_versions,
    get_dataset_version,
    validate_dataset_against_schema,
)


def schema_with_version(version):
    return {
        "dataset_version": version,
        "items": {
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
            },
        },
    }


def test_matching_versions_are_compatible():
    producer = schema_with_version("1.0")
    consumer = schema_with_version("1.0")

    report = compare_schema_versions(
        producer,
        consumer,
    )

    assert report["compatibility_status"] == "PASS"
    assert report["compatible"] is True


def test_different_versions_are_incompatible():
    producer = schema_with_version("1.0")
    consumer = schema_with_version("2.0")

    report = compare_schema_versions(
        producer,
        consumer,
    )

    assert report["compatibility_status"] == "FAIL"
    assert report["compatible"] is False


def test_missing_version_is_rejected():
    schema = {
        "items": {
            "properties": {},
        },
    }

    with pytest.raises(
        ValueError,
        match="does not define dataset_version",
    ):
        get_dataset_version(schema)


def test_valid_dataset_passes_schema_validation():
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["incident_id"],
            "properties": {
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    dataset = [
        {
            "incident_id": "INC-001",
        }
    ]

    assert validate_dataset_against_schema(
        dataset,
        schema,
    ) is True


def test_invalid_dataset_fails_schema_validation():
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["incident_id"],
            "properties": {
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    dataset = [
        {
            "wrong_field": "INC-001",
        }
    ]

    with pytest.raises(Exception):
        validate_dataset_against_schema(
            dataset,
            schema,
        )


def test_dataset_is_compatible_with_both_schemas():
    producer_schema = {
        "dataset_version": "1.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "dataset_version",
                "incident_id",
            ],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    consumer_schema = {
        "dataset_version": "1.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "dataset_version",
                "incident_id",
            ],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    dataset = [
        {
            "dataset_version": "1.0",
            "incident_id": "INC-001",
        },
    ]

    report = check_schema_compatibility(
        dataset,
        producer_schema,
        consumer_schema,
    )

    assert report["compatibility_status"] == "PASS"
    assert report["producer_valid"] is True
    assert report["consumer_valid"] is True
    assert report["compatible"] is True


def test_dataset_is_incompatible_with_breaking_consumer_schema():
    producer_schema = {
        "dataset_version": "1.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "dataset_version",
                "incident_id",
            ],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    consumer_schema = {
        "dataset_version": "2.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "dataset_version",
                "incident_id",
                "new_required_field",
            ],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
                "incident_id": {
                    "type": "string",
                },
                "new_required_field": {
                    "type": "string",
                },
            },
        },
    }

    dataset = [
        {
            "dataset_version": "1.0",
            "incident_id": "INC-001",
        },
    ]

    report = check_schema_compatibility(
        dataset,
        producer_schema,
        consumer_schema,
    )

    assert report["compatibility_status"] == "FAIL"
    assert report["producer_valid"] is True
    assert report["consumer_valid"] is False
    assert report["compatible"] is False


def test_different_schema_versions_can_still_be_compatible():
    producer_schema = {
        "dataset_version": "1.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "dataset_version",
                "incident_id",
            ],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    consumer_schema = {
        "dataset_version": "2.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "dataset_version",
                "incident_id",
            ],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
                "incident_id": {
                    "type": "string",
                },
            },
        },
    }

    dataset = [
        {
            "dataset_version": "1.0",
            "incident_id": "INC-001",
        },
    ]

    report = check_schema_compatibility(
        dataset,
        producer_schema,
        consumer_schema,
    )

    assert report["version_match"] is False
    assert report["producer_valid"] is True
    assert report["consumer_valid"] is True
    assert report["compatible"] is True
    assert report["compatibility_status"] == "PASS"


def test_version_mismatch_is_reported_even_when_compatible():
    producer_schema = {
        "dataset_version": "1.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": ["dataset_version"],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
            },
        },
    }

    consumer_schema = {
        "dataset_version": "2.0",
        "type": "array",
        "items": {
            "type": "object",
            "required": ["dataset_version"],
            "properties": {
                "dataset_version": {
                    "type": "string",
                },
            },
        },
    }

    dataset = [
        {
            "dataset_version": "1.0",
        }
    ]

    report = check_schema_compatibility(
        dataset,
        producer_schema,
        consumer_schema,
    )

    assert report["version_match"] is False
    assert report["producer_valid"] is True
    assert report["consumer_valid"] is True
    assert report["compatible"] is True
    assert report["compatibility_status"] == "PASS"