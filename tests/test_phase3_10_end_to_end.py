import json
from pathlib import Path

from scripts.aegis_dataset_quality import (
    generate_quality_report,
)
from scripts.build_aegis_dataset import (
    build_dataset,
    validate_against_schema,
)
from scripts.replay_aegis_dataset import (
    replay_dataset,
)
from scripts.sanitize_aegis_dataset import (
    sanitize_dataset,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "datasets"
    / "aegis_dataset_v1.0.json"
)


def test_phase3_10_end_to_end():
    # 1. Build canonical dataset.
    dataset = build_dataset()

    assert dataset
    assert len(dataset) == 1

    # 2. Validate canonical schema.
    validate_against_schema(dataset)

    # 3. Sanitize dataset.
    sanitized_dataset, sanitization_report = (
        sanitize_dataset(dataset)
    )

    assert len(sanitized_dataset) == len(dataset)
    assert sanitization_report["findings_count"] >= 0

    # 4. Validate sanitized dataset quality.
    quality_report = generate_quality_report(
        sanitized_dataset
    )

    assert quality_report["quality_status"] == "PASS"
    assert all(
        quality_report["checks"].values()
    )

    # 5. Replay sanitized dataset.
    replay_report = replay_dataset(
        sanitized_dataset
    )

    assert replay_report["replay_status"] == "PASS"
    assert replay_report["records_replayed"] == 1

    # 6. Verify the existing production artifact is valid JSON.
    assert DATASET_PATH.exists()

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        persisted_dataset = json.load(file)

    assert isinstance(persisted_dataset, list)
    assert len(persisted_dataset) == 1