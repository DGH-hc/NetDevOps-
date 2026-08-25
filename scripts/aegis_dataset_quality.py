from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "sanitized"
    / "aegis_dataset_v1.0_sanitized.json"
)

REQUIRED_FIELDS = {
    "dataset_version",
    "incident",
    "signals",
    "correlation",
    "timeline",
    "root_cause",
    "affected_components",
    "evidence",
    "context",
    "decision",
    "response_plan",
    "simulation",
    "provenance",
}

VALID_SEVERITIES = {
    "critical",
    "high",
    "medium",
    "low",
}

REQUIRED_SOURCE_PHASES = {
    "3.6",
    "3.7",
    "3.8",
    "3.9",
}


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

def percentage(
    passed: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return round(
        (passed / total) * 100,
        2,
    )

def generate_quality_report(
    dataset: list[dict[str, Any]],
) -> dict[str, Any]:

    total_required_field_slots = 0
    present_required_field_slots = 0

    incident_ids = [
        record.get("incident", {}).get("incident_id")
        for record in dataset
    ]

    duplicate_ids = sorted(
        {
            incident_id
            for incident_id in incident_ids
            if incident_ids.count(incident_id) > 1
        }
    )

    missing_required_fields = []

    invalid_severity = []
    invalid_confidence = []
    missing_source_phases = []
    missing_evidence = []

    for record in dataset:
        incident_id = record.get(
            "incident",
            {},
        ).get(
            "incident_id",
            "UNKNOWN",
        )

        missing = sorted(
            REQUIRED_FIELDS - set(record.keys())
        )

        total_required_field_slots += len(REQUIRED_FIELDS)
        present_required_field_slots += (
             len(REQUIRED_FIELDS) - len(missing)
        )

        if missing:
            missing_required_fields.append(
                {
                    "incident_id": incident_id,
                    "fields": missing,
                }
            )

        severity = str(
            record.get(
                "incident",
                {},
            ).get(
                "severity",
                "",
            )
        ).lower()

        if severity not in VALID_SEVERITIES:
            invalid_severity.append(
                {
                    "incident_id": incident_id,
                    "value": severity,
                }
            )

        confidence = record.get(
            "incident",
            {},
        ).get(
            "confidence"
        )

        if (
            not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            invalid_confidence.append(
                {
                    "incident_id": incident_id,
                    "value": confidence,
                }
            )

        source_phases = set(
            record.get(
                "provenance",
                {},
            ).get(
                "source_phases",
                [],
            )
        )

        evidence = record.get("evidence", [])

        if not evidence:
            missing_evidence.append(
            incident_id
        )

        missing_phases = sorted(
            REQUIRED_SOURCE_PHASES - source_phases
        )

        if missing_phases:
            missing_source_phases.append(
                {
                    "incident_id": incident_id,
                    "phases": missing_phases,
                }
            )

    completeness_percentage = percentage(
      present_required_field_slots,
      total_required_field_slots,
    )

    checks = {
        "record_count": len(dataset) > 0,
        "duplicate_incident_ids": not duplicate_ids,
        "required_fields": not missing_required_fields,
        "valid_severity": not invalid_severity,
        "valid_confidence": not invalid_confidence,
        "source_phase_coverage": not missing_source_phases,
        "evidence_coverage": not missing_evidence,
    }

    quality_passed = all(checks.values())

    return {
        "quality_status": (
            "PASS"
            if quality_passed
            else "FAIL"
        ),
        "records": len(dataset),
        "metrics": {
             "completeness_percentage": completeness_percentage,
            },
        "checks": checks,
        "issues": {
            "duplicate_incident_ids": duplicate_ids,
            "missing_required_fields": (
                missing_required_fields
            ),
            "invalid_severity": invalid_severity,
            "invalid_confidence": invalid_confidence,
            "missing_source_phases": (
                missing_source_phases
            ),
            "missing_evidence": missing_evidence,
        },
    }


def main() -> None:
    dataset = load_dataset(DATASET_PATH)

    report = generate_quality_report(dataset)

    print("Phase 3.10 Dataset Quality")
    print("===========================")
    print(f"Quality status: {report['quality_status']}")
    print(f"Records: {report['records']}")
    print(
    "Completeness: "
    f"{report['metrics']['completeness_percentage']}%"
    )

    for name, result in report["checks"].items():
        print(
            f"{name}: "
            f"{'PASS' if result else 'FAIL'}"
        )


if __name__ == "__main__":
    main()