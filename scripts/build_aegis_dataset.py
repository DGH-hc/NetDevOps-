"""
Phase 3.10 - AegisAI Dataset Builder

Combines the validated outputs of Phases 3.8 and 3.9 into the
canonical Phase 3.10 AegisAI dataset.

This module:
- Loads Phase 3.8 Aegis input
- Loads Phase 3.9 integration results
- Matches incidents by incident ID
- Normalizes upstream naming differences
- Builds the canonical Phase 3.10 contract
- Validates the generated dataset against the Phase 3.10 schema
- Writes the validated dataset to the Phase 3.10 evidence directory

This module does NOT:
- Execute response actions
- Modify infrastructure
- Change Phase 3.8 or 3.9 data
- Perform AI reasoning
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def component_name(component):
    if isinstance(component, dict):
        return component.get("name", "")
    return str(component)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PHASE_3_8_INPUT = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.8_root_cause"
    / "aegis_input.json"
)

PHASE_3_7_GRAPH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.7_incidents"
    / "incident_graph.json"
)

PHASE_3_7_SUMMARY = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.7_incidents"
    / "incident_summary.json"
)

PHASE_3_9_RESULTS = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.9_response_simulation"
    / "integration_results.json"
)

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "aegis_dataset_schema.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "datasets"
)

OUTPUT_PATH = OUTPUT_DIR / "aegis_dataset_v1.0.json"

DATASET_VERSION = "1.0"


def load_json(path: Path) -> Any:
    """Load and return JSON data from a file."""

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_incident_id_from_phase38(record: dict[str, Any]) -> str:
    """Extract the canonical incident ID from Phase 3.8 data."""

    incident = record.get("incident", {})

    incident_id = incident.get("id")

    if not incident_id:
        raise ValueError(
            "Phase 3.8 record is missing incident.id"
        )

    return str(incident_id)

def build_phase37_indexes(
    graph_data: list[dict[str, Any]],
    summary_data: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    """Index Phase 3.7 graph and summary data by incident ID."""

    graph_by_id: dict[str, dict[str, Any]] = {}
    summary_by_id: dict[str, dict[str, Any]] = {}

    for record in graph_data:
        incident_id = record.get("incident_id")

        if not incident_id:
            raise ValueError(
                "Phase 3.7 graph record is missing incident_id"
            )

        if incident_id in graph_by_id:
            raise ValueError(
                f"Duplicate Phase 3.7 graph incident ID: {incident_id}"
            )

        graph_by_id[incident_id] = record

    for record in summary_data:
        incident_id = record.get("incident_id")

        if not incident_id:
            raise ValueError(
                "Phase 3.7 summary record is missing incident_id"
            )

        if incident_id in summary_by_id:
            raise ValueError(
                f"Duplicate Phase 3.7 summary incident ID: {incident_id}"
            )

        summary_by_id[incident_id] = record

    return graph_by_id, summary_by_id

def get_incident_id_from_phase39(record: dict[str, Any]) -> str:
    """Extract the canonical incident ID from Phase 3.9 data."""

    incident = record.get("incident", {})

    incident_id = incident.get("incident_id")

    if not incident_id:
        raise ValueError(
            "Phase 3.9 record is missing incident.incident_id"
        )

    return str(incident_id)


def normalize_incident(
    phase38_record: dict[str, Any],
    phase39_record: dict[str, Any],
) -> dict[str, Any]:
    """Create the canonical Phase 3.10 incident object."""

    incident_38 = phase38_record["incident"]
    incident_39 = phase39_record["incident"]

    incident_id_38 = get_incident_id_from_phase38(phase38_record)
    incident_id_39 = get_incident_id_from_phase39(phase39_record)

    if incident_id_38 != incident_id_39:
        raise ValueError(
            "Incident ID mismatch between Phase 3.8 and Phase 3.9: "
            f"{incident_id_38} != {incident_id_39}"
        )

    incident_type_38 = incident_38.get("type")
    incident_type_39 = incident_39.get("incident_type")

    if not incident_type_38 or not incident_type_39:
        raise ValueError(
            f"Missing incident type for {incident_id_38}"
        )

    if incident_type_38 != incident_type_39:
        raise ValueError(
            "Incident type mismatch for "
            f"{incident_id_38}: "
            f"{incident_type_38} != {incident_type_39}"
        )

    severity = str(
        incident_39.get(
            "severity",
            incident_38.get("severity", ""),
        )
    ).lower()

    confidence = incident_39.get(
        "confidence",
        phase38_record.get("root_cause", {}).get(
            "confidence"
        ),
    )

    if confidence is None:
        raise ValueError(
            f"Missing confidence for {incident_id_38}"
        )

    confidence = float(confidence)

    if not 0 <= confidence <= 1:
        raise ValueError(
            f"Confidence outside valid range for "
            f"{incident_id_38}: {confidence}"
        )

    return {
        "incident_id": incident_id_38,
        "incident_type": incident_type_39,
        "severity": severity,
        "confidence": confidence,
        "detected_at": incident_38.get("detected_at"),
    }


def build_canonical_record(
    phase38_record: dict[str, Any],
    phase39_record: dict[str, Any],
    phase37_graph: dict[str, Any],
    phase37_summary: dict[str,Any],
) -> dict[str, Any]:
    """Build one canonical Phase 3.10 incident record."""

    incident = normalize_incident(
        phase38_record,
        phase39_record,
    )

    root_cause = phase38_record.get("root_cause", {})

    decision = phase39_record.get("decision", {})
    action_plan = phase39_record.get("action_plan", {})
    simulation = phase39_record.get("simulation", {})
    validation = phase39_record.get("validation", {})

    record = {
        "dataset_version": DATASET_VERSION,

        "incident": incident,

        "signals": phase38_record.get(
            "signals",
            [],
        ),

        "correlation": {
         "incident_id": incident["incident_id"],
          "related_events": phase37_graph.get(
          "nodes",
          [],
        ),
         "incident_graph": phase37_graph,
         "summary": phase37_summary,
        },

        "timeline": phase38_record.get(
            "timeline",
            [],
        ),

        "root_cause": {
            "id": root_cause.get("id", ""),
            "name": root_cause.get("name", ""),
            "hint": root_cause.get("hint"),
            "confidence": root_cause.get(
                "confidence",
                incident["confidence"],
            ),
        },

        "affected_components": [
            component_name(component)
            for component in phase38_record.get(
                 "affected_components",
                 incident.get("affected_components", []),
            )
        ],

        "evidence": phase38_record.get(
            "evidence",
            [],
        ),

        "context": {
            "package_version": phase38_record.get(
                "package_version"
            ),
            "generated_by": phase38_record.get(
                "generated_by"
            ),
        },

        "decision": {
            "decision_id": decision.get(
                "decision_id",
                "",
            ),
            "playbook_id": decision.get(
                "playbook_id",
                "",
            ),
            "playbook_name": decision.get(
                "playbook_name",
                "",
            ),
            "playbook_version": decision.get(
                "playbook_version",
                "",
            ),
            "decision_score": decision.get(
                "decision_score",
                0,
            ),
            "score_breakdown": decision.get(
                "score_breakdown",
                {},
            ),
            "decision_trace": decision.get(
                "decision_trace",
                [],
            ),
            "expected_evidence": decision.get(
                "expected_evidence",
                [],
            ),
        },

        "response_plan": {
            "primary_actions": action_plan.get(
                "primary_actions",
                [],
            ),
            "alternative_actions": action_plan.get(
                "alternative_actions",
                [],
            ),
            "prerequisites": action_plan.get(
                "prerequisites",
                [],
            ),
            "post_actions": action_plan.get(
                "post_actions",
                [],
            ),
            "execution_order": action_plan.get(
                "execution_order",
                [],
            ),
            "dependency_graph": action_plan.get(
                "dependency_graph",
                [],
            ),
            "expected_evidence": action_plan.get(
                "expected_evidence",
                [],
            ),
        },

        "simulation": simulation,

        "validation": validation,

        "provenance": {
            "source_phases": [
                "3.6",
                "3.7",
                "3.8",
                "3.9",
            ],
            "source_files": [
                    str(
                        PHASE_3_7_GRAPH.relative_to(
                             PROJECT_ROOT
                        )
                    ),
                    str(
                        PHASE_3_7_SUMMARY.relative_to(
                             PROJECT_ROOT
                        )
                    ),
                    str(
                        PHASE_3_8_INPUT.relative_to(
                             PROJECT_ROOT
                        )
                    ),
                    str(
                        PHASE_3_9_RESULTS.relative_to(
                             PROJECT_ROOT
                        )
                    ),
            ],
            "generated_at": datetime.now(
             timezone.utc
            ).isoformat(),
        },
    }

    return record

def validate_cross_phase_consistency(
    phase37_summary: dict[str, Any],
    phase37_graph: dict[str, Any],
    phase38_record: dict[str, Any],
    phase39_record: dict[str, Any],
) -> None:
    """Validate consistency across Phases 3.7, 3.8, and 3.9."""

    incident_id = get_incident_id_from_phase38(
        phase38_record
    )

    # ---- Phase 3.7 graph integrity ----

    if phase37_graph.get("incident_id") != incident_id:
        raise ValueError(
            f"Phase 3.7 graph incident ID mismatch: "
            f"{phase37_graph.get('incident_id')} != {incident_id}"
        )

    if not phase37_graph.get("nodes"):
        raise ValueError(
            f"Phase 3.7 graph has no nodes for {incident_id}"
        )

    if not phase37_graph.get("edges"):
        raise ValueError(
            f"Phase 3.7 graph has no edges for {incident_id}"
        )

    # ---- Phase 3.7 ↔ Phase 3.8 ----

    summary_type = phase37_summary.get("incident_type")
    phase38_type = phase38_record["incident"].get("type")

    if summary_type != phase38_type:
        raise ValueError(
            f"Incident type mismatch for {incident_id}: "
            f"3.7={summary_type}, 3.8={phase38_type}"
        )

    summary_severity = str(
        phase37_summary.get("severity", "")
    ).lower()

    phase38_severity = str(
        phase38_record["incident"].get("severity", "")
    ).lower()

    if summary_severity != phase38_severity:
        raise ValueError(
            f"Severity mismatch for {incident_id}: "
            f"3.7={summary_severity}, "
            f"3.8={phase38_severity}"
        )

    summary_signals = set(
        phase37_summary.get("signals", [])
    )

    phase38_signals = set(
        phase38_record.get("signals", [])
    )

    if summary_signals != phase38_signals:
        raise ValueError(
            f"Signal mismatch for {incident_id}: "
            f"3.7={sorted(summary_signals)}, "
            f"3.8={sorted(phase38_signals)}"
        )

    summary_components = {
         component_name(component)
         for component in phase37_summary.get(
            "affected_components",
            [],
        )
    }

    phase38_components = {
         component_name(component)
         for component in phase38_record.get(
             "affected_components",
            [],
        )
    }

    if summary_components != phase38_components:
        raise ValueError(
            f"Affected component mismatch for {incident_id}: "
            f"3.7={sorted(summary_components)}, "
            f"3.8={sorted(phase38_components)}"
        )

    # ---- Phase 3.8 ↔ Phase 3.9 ----

    phase39_incident = phase39_record["incident"]

    phase39_severity = str(
        phase39_incident.get("severity", "")
    ).lower()

    if phase38_severity != phase39_severity:
        raise ValueError(
            f"Severity mismatch for {incident_id}: "
            f"3.8={phase38_severity}, "
            f"3.9={phase39_severity}"
        )

    phase39_components = {
         component_name(component)
         for component in phase39_record["incident"].get(
            "affected_components",
            [],
        )
    }

    if phase38_components != phase39_components:
        raise ValueError(
            f"Affected component mismatch for {incident_id}: "
            f"3.8={sorted(phase38_components)}, "
            f"3.9={sorted(phase39_components)}"
        )

    confidence = phase39_incident.get("confidence")

    if confidence is None:
        raise ValueError(
            f"Missing confidence for {incident_id}"
        )

    confidence = float(confidence)

    if not 0 <= confidence <= 1:
        raise ValueError(
            f"Confidence outside valid range for "
            f"{incident_id}: {confidence}"
        )

def build_dataset() -> list[dict[str, Any]]:
    """Build the complete canonical Phase 3.10 dataset."""

    phase37_graph_data = load_json(PHASE_3_7_GRAPH)
    phase37_summary_data = load_json(PHASE_3_7_SUMMARY)
    phase38_data = load_json(PHASE_3_8_INPUT)
    phase39_data = load_json(PHASE_3_9_RESULTS)

    graph_by_id, summary_by_id = build_phase37_indexes(
       phase37_graph_data,
       phase37_summary_data,
    )

    if not isinstance(phase38_data, list):
        raise ValueError(
            "Phase 3.8 Aegis input must be a JSON list."
        )

    if not isinstance(phase39_data, list):
        raise ValueError(
            "Phase 3.9 integration results must be a JSON list."
        )

    phase39_by_id: dict[str, dict[str, Any]] = {}

    for record in phase39_data:
        incident_id = get_incident_id_from_phase39(record)

        if incident_id in phase39_by_id:
            raise ValueError(
                f"Duplicate Phase 3.9 incident ID: {incident_id}"
            )

        phase39_by_id[incident_id] = record

    dataset: list[dict[str, Any]] = []

    for phase38_record in phase38_data:
        incident_id = get_incident_id_from_phase38(
            phase38_record
        )

        if incident_id not in phase39_by_id:
            raise ValueError(
                f"Phase 3.9 result missing for incident: "
                f"{incident_id}"
            )

        phase39_record = phase39_by_id[incident_id]

        validate_cross_phase_consistency(
         summary_by_id[incident_id],
         graph_by_id[incident_id],
         phase38_record,
         phase39_record,
        )

        if incident_id not in graph_by_id:
         raise ValueError(
           f"Phase 3.7 graph missing for incident: {incident_id}"
        )

        if incident_id not in summary_by_id:
         raise ValueError(
            f"Phase 3.7 summary missing for incident: {incident_id}"
        )

        canonical_record = build_canonical_record(
           phase38_record,
           phase39_record,
           graph_by_id[incident_id],
           summary_by_id[incident_id],
        )

        dataset.append(canonical_record)

    phase38_ids = {
        get_incident_id_from_phase38(record)
        for record in phase38_data
    }

    phase39_ids = set(phase39_by_id.keys())

    missing_from_phase38 = phase39_ids - phase38_ids

    if missing_from_phase38:
        raise ValueError(
            "Phase 3.9 contains incidents missing from "
            f"Phase 3.8: {sorted(missing_from_phase38)}"
        )

    return dataset


def validate_against_schema(
    dataset: list[dict[str, Any]],
) -> None:
    """Validate the dataset using jsonschema."""

    try:
        from jsonschema import validate
    except ImportError as exc:
        raise RuntimeError(
            "The 'jsonschema' package is required. "
            "Install it with: pip install jsonschema"
        ) from exc

    schema = load_json(SCHEMA_PATH)

    validate(
        instance=dataset,
        schema=schema,
    )


def write_dataset(
    dataset: list[dict[str, Any]],
) -> None:
    """Write the validated dataset to the Phase 3.10 evidence directory."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            dataset,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write("\n")


def main() -> None:
    """Build, validate, and write the Phase 3.10 dataset."""

    print("Phase 3.10 AegisAI Dataset Builder")
    print("=" * 40)

    print("Loading Phase 3.8 data...")
    print(f"  {PHASE_3_8_INPUT}")

    print("Loading Phase 3.9 data...")
    print(f"  {PHASE_3_9_RESULTS}")

    dataset = build_dataset()

    print(
        f"Built {len(dataset)} canonical incident dataset(s)."
    )

    print("Validating against Phase 3.10 schema...")

    validate_against_schema(dataset)

    print("Schema validation: PASS")

    write_dataset(dataset)

    print("Dataset written successfully:")
    print(f"  {OUTPUT_PATH}")

    print()
    print("Phase 3.10 dataset build: PASS")


if __name__ == "__main__":
    main()