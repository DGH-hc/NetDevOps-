from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.build_aegis_dataset import(
     build_dataset,
     validate_against_schema,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "datasets"
    / "aegis_dataset_v1.0.json"
)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load an existing Phase 3.10 dataset."""

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "Phase 3.10 dataset must be a JSON list."
        )

    return dataset


def replay_dataset(
    dataset: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate and replay an existing canonical dataset."""

    validate_against_schema(dataset)

    incident_ids = [
        record["incident"]["incident_id"]
        for record in dataset
    ]

    if len(incident_ids) != len(set(incident_ids)):
        raise ValueError(
            "Replay failed: duplicate incident IDs detected."
        )

    return {
        "replay_status": "PASS",
        "records_replayed": len(dataset),
        "incident_ids": incident_ids,
        "dataset_version": (
            dataset[0]["dataset_version"]
            if dataset
            else None
        ),
    }

def normalize_for_comparison(
    dataset: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove nondeterministic runtime metadata before comparison."""

    normalized_dataset = json.loads(
        json.dumps(dataset)
    )

    for record in normalized_dataset:
        provenance = record.get("provenance")

        if isinstance(provenance, dict):
            provenance.pop("generated_at", None)

    return normalized_dataset

def compare_replayed_dataset(
    expected_dataset: list[dict[str, Any]],
    replayed_dataset: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare a rebuilt dataset against the expected dataset."""

    expected_dataset = normalize_for_comparison(
        expected_dataset
    )

    replayed_dataset = normalize_for_comparison(
        replayed_dataset
    )

    differences: list[str] = []

    if len(expected_dataset) != len(replayed_dataset):
        differences.append(
            "Record count differs: "
            f"expected={len(expected_dataset)}, "
            f"replayed={len(replayed_dataset)}"
        )

    max_records = max(
        len(expected_dataset),
        len(replayed_dataset),
    )

    for index in range(max_records):
        if index >= len(expected_dataset):
            differences.append(
                f"Record {index} missing from expected dataset"
            )
            continue

        if index >= len(replayed_dataset):
            differences.append(
                f"Record {index} missing from replayed dataset"
            )
            continue

        if expected_dataset[index] != replayed_dataset[index]:
            expected_record = expected_dataset[index]
            replayed_record = replayed_dataset[index]

            differing_fields = [
                key
                for key in sorted(
                    set(expected_record)
                    | set(replayed_record)
                )
                if expected_record.get(key)
                != replayed_record.get(key)
            ]

            differences.append(
                f"Record {index} differs in fields: "
                f"{differing_fields}"
            )

    matches = not differences

    return {
        "replay_match": matches,
        "replay_status": (
            "PASS"
            if matches
            else "FAIL"
        ),
        "expected_records": len(expected_dataset),
        "replayed_records": len(replayed_dataset),
        "differences": differences,
    }

def replay_from_sources(
    expected_dataset: list[dict[str, Any]],
) -> dict[str, Any]:
    """Rebuild the dataset from source evidence and compare it."""

    replayed_dataset = build_dataset()

    validate_against_schema(replayed_dataset)

    return compare_replayed_dataset(
        expected_dataset,
        replayed_dataset,
    )

def main() -> None:
    dataset = load_dataset(DATASET_PATH)

    basic_result = replay_dataset(dataset)

    source_result = replay_from_sources(dataset)

    print("Phase 3.10 Dataset Replay")
    print("==========================")

    print(
        f"Replay status: "
        f"{basic_result['replay_status']}"
    )

    print(
        f"Records replayed: "
        f"{basic_result['records_replayed']}"
    )

    print(
        f"Incident IDs: "
        f"{basic_result['incident_ids']}"
    )

    print(
        f"Dataset version: "
        f"{basic_result['dataset_version']}"
    )

    print(
        f"Source reconstruction: "
        f"{source_result['replay_status']}"
    )

    print(
        f"Replay match: "
        f"{source_result['replay_match']}"
    )

    if not source_result["replay_match"]:
        print("Differences:")

        for difference in source_result["differences"]:
            print(f"- {difference}")

        raise SystemExit(1)


if __name__ == "__main__":
    main()