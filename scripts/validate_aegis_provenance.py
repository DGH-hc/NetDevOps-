import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]

PHASE36_PATH = (
    BASE_DIR
    / "evidence/phase3.6_signals/normalized_events.json"
)

PHASE37_GRAPH_PATH = (
    BASE_DIR
    / "evidence/phase3.7_incidents/incident_graph.json"
)

PHASE37_SUMMARY_PATH = (
    BASE_DIR
    / "evidence/phase3.7_incidents/incident_summary.json"
)

PHASE38_PATH = (
    BASE_DIR
    / "evidence/phase3.8_root_cause/aegis_input.json"
)

PHASE39_PATH = (
    BASE_DIR
    / "evidence/phase3.9_response_simulation/integration_results.json"
)

DATASET_PATH = (
    BASE_DIR
    / "evidence/phase3.10_ai_dataset/datasets/"
    / "aegis_dataset_v1.0.json"
)

REPORT_PATH = (
    BASE_DIR
    / "evidence/phase3.10_ai_dataset/provenance/"
    / "provenance_report.json"
)


def load_json(path: Path) -> Any:
    """Load JSON data from an artifact path."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def get_phase38_incident_id(record: dict[str, Any]) -> str:
    """Return the incident ID from a Phase 3.8 record."""
    incident = record.get("incident", {})
    return incident.get("id") or incident.get("incident_id")


def get_phase39_incident_id(record: dict[str, Any]) -> str:
    """Return the incident ID from a Phase 3.9 record."""
    incident = record.get("incident", {})
    return incident.get("incident_id") or incident.get("id")


def get_dataset_incident_id(record: dict[str, Any]) -> str:
    """Return the incident ID from a Phase 3.10 dataset record."""
    incident = record.get("incident", {})
    return incident.get("incident_id") or incident.get("id")


def build_index(
    records: list[dict[str, Any]],
    id_getter,
) -> dict[str, dict[str, Any]]:
    """Build an incident ID index."""
    index = {}

    for record in records:
        incident_id = id_getter(record)

        if incident_id:
            index[incident_id] = record

    return index


def validate_provenance() -> dict[str, Any]:
    """Validate lineage from Phase 3.6 through Phase 3.10."""

    phase36 = load_json(PHASE36_PATH)
    phase37_graph = load_json(PHASE37_GRAPH_PATH)
    phase37_summary = load_json(PHASE37_SUMMARY_PATH)
    phase38 = load_json(PHASE38_PATH)
    phase39 = load_json(PHASE39_PATH)
    dataset = load_json(DATASET_PATH)

    phase36_event_types = {
        record.get("event_type")
        for record in phase36
        if record.get("event_type")
    }

    phase37_graph_index = build_index(
        phase37_graph,
        lambda record: record.get("incident_id"),
    )

    phase37_summary_index = build_index(
        phase37_summary,
        lambda record: record.get("incident_id"),
    )

    phase38_index = build_index(
        phase38,
        get_phase38_incident_id,
    )

    phase39_index = build_index(
        phase39,
        get_phase39_incident_id,
    )

    results = []
    failures = []

    for record in dataset:
        incident_id = get_dataset_incident_id(record)

        checks = {
            "phase37_summary_exists":
                incident_id in phase37_summary_index,
            "phase37_graph_exists":
                incident_id in phase37_graph_index,
            "phase38_exists":
                incident_id in phase38_index,
            "phase39_exists":
                incident_id in phase39_index,
        }

        dataset_correlation = record.get("correlation", {})

        if incident_id in phase37_graph_index:
            checks["correlation_incident_id_matches"] = (
                dataset_correlation.get("incident_id")
                == incident_id
            )
        else:
            checks["correlation_incident_id_matches"] = False

        dataset_signals = set(record.get("signals", []))

        if incident_id in phase37_summary_index:
            phase37_signals = set(
                phase37_summary_index[incident_id].get(
                    "signals",
                    [],
                )
            )
            checks["phase37_signal_consistency"] = (
                dataset_signals == phase37_signals
            )
        else:
            checks["phase37_signal_consistency"] = False

        if incident_id in phase38_index:
            phase38_signals = set(
                phase38_index[incident_id].get(
                    "signals",
                    [],
                )
            )
            checks["phase38_signal_consistency"] = (
                dataset_signals == phase38_signals
            )
        else:
            checks["phase38_signal_consistency"] = False

        checks["phase36_signal_coverage"] = all(
            signal in phase36_event_types
            for signal in dataset_signals
        )

        status = (
            "PASS"
            if all(checks.values())
            else "FAIL"
        )

        if status == "FAIL":
            failed_checks = [
                name
                for name, passed in checks.items()
                if not passed
            ]

            failures.append(
                {
                    "incident_id": incident_id,
                    "failed_checks": failed_checks,
                }
            )

        results.append(
            {
                "incident_id": incident_id,
                "status": status,
                "checks": checks,
            }
        )

    dataset_ids = {
        get_dataset_incident_id(record)
        for record in dataset
    }

    source_ids = {
        "phase37_summary": set(
            phase37_summary_index
        ),
        "phase37_graph": set(
            phase37_graph_index
        ),
        "phase38": set(
            phase38_index
        ),
        "phase39": set(
            phase39_index
        ),
    }

    orphan_records = {}

    for source_name, source_incident_ids in source_ids.items():
        orphans = sorted(
            source_incident_ids - dataset_ids
        )

        if orphans:
            orphan_records[source_name] = orphans

    status = (
        "PASS"
        if not failures and not orphan_records
        else "FAIL"
    )

    return {
        "validator_version": "1.0",
        "status": status,
        "records_checked": len(dataset),
        "phase36_event_types": sorted(
            phase36_event_types
        ),
        "results": results,
        "failures": failures,
        "orphan_records": orphan_records,
    }


def write_report(report: dict[str, Any]) -> None:
    """Write the provenance validation report."""
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )
        file.write("\n")


def main() -> None:
    """Run provenance validation."""
    print("Aegis Provenance & Lineage Validation")
    print("=" * 40)

    report = validate_provenance()

    write_report(report)

    print(f"Status: {report['status']}")
    print(
        f"Records checked: "
        f"{report['records_checked']}"
    )
    print(f"Report: {REPORT_PATH}")

    if report["status"] != "PASS":
        raise SystemExit(
            "Provenance validation failed."
        )


if __name__ == "__main__":
    main()