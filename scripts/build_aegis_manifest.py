from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "sanitized"
    / "aegis_dataset_v1.0_sanitized.json"
)

MANIFEST_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "sanitized"
    / "dataset_manifest.json"
)


def calculate_sha256(path: Path) -> str:
    """Calculate SHA-256 fingerprint of a file."""

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "Sanitized dataset must be a JSON list."
        )

    sha256 = calculate_sha256(DATASET_PATH)

    manifest = {
        "manifest_version": "1.0",
        "dataset": {
            "file": str(
                DATASET_PATH.relative_to(PROJECT_ROOT)
            ),
            "dataset_version": "1.0",
            "records": len(dataset),
            "sha256": sha256,
        },
        "producer": {
            "builder": "scripts/build_aegis_dataset.py",
            "sanitizer": "scripts/sanitize_aegis_dataset.py",
            "sanitizer_version": "1.0",
        },
    }

    MANIFEST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MANIFEST_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            indent=4,
        )
        file.write("\n")

    print("Phase 3.10 Dataset Manifest")
    print("============================")
    print(f"Records: {len(dataset)}")
    print(f"SHA-256: {sha256}")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()