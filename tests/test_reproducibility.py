from copy import deepcopy

from scripts.build_aegis_dataset import build_dataset

DYNAMIC_KEYS = {
    "generated_at",
    "dataset_id",
    "decision_id",
    "scan_timestamp",
}


def strip_dynamic_metadata(data):
    """Remove fields that are intentionally non-deterministic."""

    if isinstance(data, dict):
        return {
            key: strip_dynamic_metadata(value)
            for key, value in data.items()
            if key not in DYNAMIC_KEYS
        }

    if isinstance(data, list):
        return [
            strip_dynamic_metadata(item)
            for item in data
        ]

    return data


def test_dataset_reproducibility():
    """Verify identical inputs produce identical canonical datasets."""

    dataset_a = build_dataset()
    dataset_b = build_dataset()

    normalized_a = strip_dynamic_metadata(
        deepcopy(dataset_a)
    )

    normalized_b = strip_dynamic_metadata(
        deepcopy(dataset_b)
    )

    assert normalized_a == normalized_b