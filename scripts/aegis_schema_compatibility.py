from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "aegis_dataset_schema.json"
)


def load_schema(path: Path) -> dict[str, Any]:
    """Load a JSON schema."""

    if not path.exists():
        raise FileNotFoundError(
            f"Schema not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        schema = json.load(file)

    if not isinstance(schema, dict):
        raise ValueError(
            "Schema must be a JSON object."
        )

    return schema

def get_dataset_version(
    schema: dict[str, Any],
) -> str:
    """Extract the declared dataset version from a schema."""

    version = schema.get("dataset_version")

    if version:
        return version

    items = schema.get("items", {})
    properties = items.get("properties", {})
    dataset_version = properties.get(
        "dataset_version",
        {},
    )

    version = dataset_version.get("const")

    if version:
        return version

    raise ValueError(
        "Schema does not define dataset_version."
    )

def compare_schema_versions(
    producer_schema: dict[str, Any],
    consumer_schema: dict[str, Any],
) -> dict[str, Any]:
    """Check whether producer and consumer schemas are compatible."""

    producer_version = get_dataset_version(
        producer_schema
    )

    consumer_version = get_dataset_version(
        consumer_schema
    )

    version_match = (
        producer_version == consumer_version
    )

    return {
        "producer_version": producer_version,
        "consumer_version": consumer_version,
        "compatible": version_match,
        "compatibility_status": (
            "PASS"
            if version_match
            else "FAIL"
        ),
    }

def validate_dataset_against_schema(
    dataset: list[dict[str, Any]],
    schema: dict[str, Any],
) -> bool:
    """Validate a dataset against a supplied schema."""

    try:
        from jsonschema import validate
    except ImportError as exc:
        raise RuntimeError(
            "The 'jsonschema' package is required."
        ) from exc

    validate(
        instance=dataset,
        schema=schema,
    )

    return True

def check_schema_compatibility(
    dataset: list[dict[str, Any]],
    producer_schema: dict[str, Any],
    consumer_schema: dict[str, Any],
) -> dict[str, Any]:
    """Check whether a producer dataset is accepted by a consumer schema."""

    version_report = compare_schema_versions(
        producer_schema,
        consumer_schema,
    )

    producer_valid = True
    consumer_valid = True

    try:
        validate_dataset_against_schema(
            dataset,
            producer_schema,
        )
    except Exception:
        producer_valid = False

    try:
        validate_dataset_against_schema(
            dataset,
            consumer_schema,
        )
    except Exception:
        consumer_valid = False

    compatible = (
        producer_valid
        and consumer_valid
    )

    version_match = (
        version_report["producer_version"]
        == version_report["consumer_version"]
    )

    return {
        "producer_version": (
            version_report["producer_version"]
        ),
        "consumer_version": (
            version_report["consumer_version"]
        ),
        "version_match": version_match,
        "producer_valid": producer_valid,
        "consumer_valid": consumer_valid,
        "compatible": compatible,
        "compatibility_status": (
            "PASS"
            if compatible
            else "FAIL"
        ),
    }

def main() -> None:
    schema = load_schema(SCHEMA_PATH)

    version = get_dataset_version(schema)

    print("Phase 3.10 Schema Compatibility")
    print("================================")
    print(f"Schema version: {version}")


if __name__ == "__main__":
    main()