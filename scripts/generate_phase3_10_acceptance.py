import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_DATASET = (
    PROJECT_ROOT
    / "evidence/phase3.10_ai_dataset/datasets/aegis_dataset_v1.0.json"
)

SANITIZED_DATASET = (
    PROJECT_ROOT
    / "evidence/phase3.10_ai_dataset/sanitized/aegis_dataset_v1.0_sanitized.json"
)

SANITIZATION_REPORT = (
    PROJECT_ROOT
    / "evidence/phase3.10_ai_dataset/sanitized/sanitization_report.json"
)

MANIFEST = (
    PROJECT_ROOT
    / "evidence/phase3.10_ai_dataset/sanitized/dataset_manifest.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "evidence/phase3.10_ai_dataset/final/final_acceptance.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_sha256(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def main():

    canonical = load_json(CANONICAL_DATASET)
    sanitized = load_json(SANITIZED_DATASET)
    sanitization = load_json(SANITIZATION_REPORT)
    manifest = load_json(MANIFEST)

    canonical_ids = [
       record["incident"]["incident_id"]
       for record in canonical
    ]

    sanitized_ids = [
        record["incident"]["incident_id"]
        for record in sanitized
    ]

    actual_hash = calculate_sha256(SANITIZED_DATASET)
    manifest_hash = manifest["dataset"]["sha256"]

    # Strict validation gates
    if len(canonical) != len(sanitized):
        raise ValueError(
            "Acceptance failed: canonical and sanitized record counts differ."
        )

    if canonical_ids != sanitized_ids:
        raise ValueError(
            "Acceptance failed: incident IDs differ between datasets."
        )

    if manifest["dataset"]["records"] != len(sanitized):
        raise ValueError(
            "Acceptance failed: manifest record count mismatch."
        )

    if actual_hash != manifest_hash:
        raise ValueError(
            "Acceptance failed: SHA-256 does not match manifest."
        )

    if sanitization["records_processed"] != len(sanitized):
        raise ValueError(
            "Acceptance failed: sanitization record count mismatch."
        )

    if sanitization["findings_count"] != 0:
        raise ValueError(
            "Acceptance failed: sanitization findings exist."
        )

    acceptance = {
        "phase": "3.10",
        "system": "AegisAI Dataset Pipeline",
        "dataset_version": manifest["dataset"]["dataset_version"],
        "status": "PRODUCTION_ACCEPTANCE_PASS",
        "accepted": True,
        "records": len(sanitized),
        "incident_ids": sanitized_ids,

        "validation_summary": {
            "canonical_dataset": "PASS",
            "sanitization": "PASS",
            "manifest_generation": "PASS",
            "sha256_integrity": "PASS",
            "artifact_consistency": "PASS"
        },

        "integrity": {
            "algorithm": "SHA-256",
            "sanitized_dataset_sha256": actual_hash
        },

        "sanitization": {
            "sanitizer_version": sanitization["sanitizer_version"],
            "records_processed": sanitization["records_processed"],
            "findings_count": sanitization["findings_count"]
        },

        "closure": {
            "phase_complete_for_current_scope": True
        }
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(acceptance, file, indent=2)

    print("Phase 3.10 Final Acceptance")
    print("============================")
    print("Status: PASS")
    print(f"Records: {len(sanitized)}")
    print(f"SHA-256: {actual_hash}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()