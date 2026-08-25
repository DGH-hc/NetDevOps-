from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CURRENT_DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "sanitized"
    / "aegis_dataset_v1.0_sanitized.json"
)

GOLDEN_DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "golden"
    / "aegis_dataset_v1.0_golden.json"
)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "Dataset must be a JSON list."
        )

    return dataset

def normalize_for_comparison(
    dataset: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove dynamic fields before golden comparison."""

    normalized = json.loads(json.dumps(dataset))

    for record in normalized:
        provenance = record.get("provenance")

        if isinstance(provenance, dict):
            provenance.pop("generated_at", None)

    return normalized

def find_record_differences(
    current: dict[str, Any],
    golden: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    differences = []

    all_keys = sorted(
        set(current.keys()) | set(golden.keys())
    )

    for key in all_keys:
        path = f"{prefix}.{key}" if prefix else key

        if key not in current:
            differences.append(
                f"{path} missing from current record"
            )
            continue

        if key not in golden:
            differences.append(
                f"{path} missing from golden record"
            )
            continue

        current_value = current[key]
        golden_value = golden[key]

        if (
            isinstance(current_value, dict)
            and isinstance(golden_value, dict)
        ):
            differences.extend(
                find_record_differences(
                    current_value,
                    golden_value,
                    path,
                )
            )
        elif current_value != golden_value:
            differences.append(
                f"{path} differs: "
                f"current={current_value!r}, "
                f"golden={golden_value!r}"
            )

    return differences

def find_differences(
    current_dataset: list[dict[str, Any]],
    golden_dataset: list[dict[str, Any]],
) -> list[str]:

    differences = []

    if len(current_dataset) != len(golden_dataset):
        differences.append(
            "Record count differs"
        )

    max_records = max(
        len(current_dataset),
        len(golden_dataset),
    )

    for index in range(max_records):
        if index >= len(current_dataset):
            differences.append(
                f"Record {index} missing from current dataset"
            )
            continue

        if index >= len(golden_dataset):
            differences.append(
                f"Record {index} missing from golden dataset"
            )
            continue

        record_differences = find_record_differences(
           current_dataset[index],
           golden_dataset[index],
        )

        for difference in record_differences:
            differences.append(
            f"Record {index}: {difference}"
        )

    return differences

def compare_datasets(
    current_dataset: list[dict[str, Any]],
    golden_dataset: list[dict[str, Any]],
) -> dict[str, Any]:

    current_dataset = normalize_for_comparison(
    current_dataset
    )

    golden_dataset = normalize_for_comparison(
        golden_dataset
    )

    differences = find_differences(
        current_dataset,
        golden_dataset,
    )

    matches = not differences

    return {
        "golden_status": (
            "PASS"
            if matches
            else "FAIL"
        ),
        "current_records": len(current_dataset),
        "golden_records": len(golden_dataset),
        "datasets_match": matches,
        "differences": differences,
    }

def main() -> None:
    current_dataset = load_dataset(
        CURRENT_DATASET_PATH
    )

    golden_dataset = load_dataset(
        GOLDEN_DATASET_PATH
    )

    report = compare_datasets(
        current_dataset,
        golden_dataset,
    )

    print("Phase 3.10 Golden Dataset Check")
    print("================================")
    print(
        f"Golden status: "
        f"{report['golden_status']}"
    )
    print(
        f"Current records: "
        f"{report['current_records']}"
    )
    print(
        f"Golden records: "
        f"{report['golden_records']}"
    )

    if report["differences"]:
       print("Differences:")
       for difference in report["differences"]:
            print(f"- {difference}")


if __name__ == "__main__":
    main()