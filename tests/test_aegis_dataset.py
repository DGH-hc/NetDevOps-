"""
Phase 3.10 - AegisAI Dataset Tests

Tests the canonical dataset builder and its core integrity gates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from scripts.build_aegis_dataset import (
    SCHEMA_PATH,
    build_dataset,
    build_phase37_indexes,
    get_incident_id_from_phase38,
    get_incident_id_from_phase39,
    normalize_incident,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.10_ai_dataset"
    / "datasets"
    / "aegis_dataset_v1.0.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_schema_file_exists():
    assert SCHEMA_PATH.exists()


def test_schema_is_valid_json():
    schema = load_json(SCHEMA_PATH)

    assert isinstance(schema, dict)
    assert schema["title"] == "AegisAI Canonical Dataset"


def test_schema_accepts_generated_dataset():
    schema = load_json(SCHEMA_PATH)
    dataset = load_json(DATASET_PATH)

    validate(
        instance=dataset,
        schema=schema,
    )


def test_dataset_contains_three_incidents():
    dataset = load_json(DATASET_PATH)

    assert len(dataset) == 3


def test_dataset_contains_unique_incident_ids():
    dataset = load_json(DATASET_PATH)

    incident_ids = [
        record["incident"]["incident_id"]
        for record in dataset
    ]

    assert len(incident_ids) == len(set(incident_ids))


def test_dataset_has_expected_incidents():
    dataset = load_json(DATASET_PATH)

    incident_ids = {
        record["incident"]["incident_id"]
        for record in dataset
    }

    assert incident_ids == {
        "INC-001",
        "INC-002",
        "INC-003",
    }


def test_phase37_indexes_reject_duplicate_graph_ids():
    graph_data = [
        {"incident_id": "INC-001"},
        {"incident_id": "INC-001"},
    ]

    summary_data = [
        {"incident_id": "INC-001"},
    ]

    with pytest.raises(ValueError, match="Duplicate Phase 3.7 graph"):
        build_phase37_indexes(
            graph_data,
            summary_data,
        )


def test_phase37_indexes_reject_duplicate_summary_ids():
    graph_data = [
        {"incident_id": "INC-001"},
    ]

    summary_data = [
        {"incident_id": "INC-001"},
        {"incident_id": "INC-001"},
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate Phase 3.7 summary",
    ):
        build_phase37_indexes(
            graph_data,
            summary_data,
        )


def test_phase38_incident_id_is_required():
    record = {
        "incident": {}
    }

    with pytest.raises(
        ValueError,
        match="missing incident.id",
    ):
        get_incident_id_from_phase38(record)


def test_phase39_incident_id_is_required():
    record = {
        "incident": {}
    }

    with pytest.raises(
        ValueError,
        match="missing incident.incident_id",
    ):
        get_incident_id_from_phase39(record)


def test_incident_id_mismatch_is_rejected():
    phase38_record = {
        "incident": {
            "id": "INC-001",
            "type": "runtime_compromise",
            "severity": "CRITICAL",
        }
    }

    phase39_record = {
        "incident": {
            "incident_id": "INC-999",
            "incident_type": "runtime_compromise",
            "severity": "critical",
            "confidence": 0.95,
        }
    }

    with pytest.raises(
        ValueError,
        match="Incident ID mismatch",
    ):
        normalize_incident(
            phase38_record,
            phase39_record,
        )


def test_incident_type_mismatch_is_rejected():
    phase38_record = {
        "incident": {
            "id": "INC-001",
            "type": "runtime_compromise",
            "severity": "CRITICAL",
        }
    }

    phase39_record = {
        "incident": {
            "incident_id": "INC-001",
            "incident_type": "database_failure",
            "severity": "critical",
            "confidence": 0.95,
        }
    }

    with pytest.raises(
        ValueError,
        match="Incident type mismatch",
    ):
        normalize_incident(
            phase38_record,
            phase39_record,
        )


def test_confidence_must_be_between_zero_and_one():
    phase38_record = {
        "incident": {
            "id": "INC-001",
            "type": "runtime_compromise",
            "severity": "CRITICAL",
        }
    }

    phase39_record = {
        "incident": {
            "incident_id": "INC-001",
            "incident_type": "runtime_compromise",
            "severity": "critical",
            "confidence": 1.5,
        }
    }

    with pytest.raises(
        ValueError,
        match="Confidence outside valid range",
    ):
        normalize_incident(
            phase38_record,
            phase39_record,
        )


def test_severity_is_normalized_to_lowercase():
    phase38_record = {
        "incident": {
            "id": "INC-001",
            "type": "runtime_compromise",
            "severity": "CRITICAL",
        }
    }

    phase39_record = {
        "incident": {
            "incident_id": "INC-001",
            "incident_type": "runtime_compromise",
            "severity": "CRITICAL",
            "confidence": 0.95,
        }
    }

    result = normalize_incident(
        phase38_record,
        phase39_record,
    )

    assert result["severity"] == "critical"


def test_real_dataset_build_succeeds():
    dataset = build_dataset()

    assert len(dataset) == 3

    for record in dataset:
        assert record["dataset_version"] == "1.0"
        assert record["incident"]["incident_id"]
        assert record["decision"]["decision_id"]
        assert record["response_plan"]["primary_actions"]
        assert record["simulation"]
        assert record["validation"]
        assert record["provenance"]["source_phases"] == [
            "3.6",
            "3.7",
            "3.8",
            "3.9",
        ]


def test_correlation_data_is_populated():
    dataset = load_json(DATASET_PATH)

    for record in dataset:
        correlation = record["correlation"]

        assert correlation["incident_id"]
        assert correlation["related_events"]
        assert correlation["incident_graph"]
        assert correlation["summary"]


def test_provenance_contains_all_current_sources():
    dataset = load_json(DATASET_PATH)

    expected_sources = {
        "evidence/phase3.7_incidents/incident_graph.json",
        "evidence/phase3.7_incidents/incident_summary.json",
        "evidence/phase3.8_root_cause/aegis_input.json",
        "evidence/phase3.9_response_simulation/integration_results.json",
    }

    for record in dataset:
        sources = set(
            record["provenance"]["source_files"]
        )

        assert expected_sources.issubset(sources)


def test_generated_at_is_present():
    dataset = load_json(DATASET_PATH)

    for record in dataset:
        assert record["provenance"]["generated_at"]

def test_cross_phase_rejects_graph_incident_id_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Phase 3.7 graph incident ID mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-999",
                "nodes": ["container_shell"],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )


def test_cross_phase_rejects_empty_graph_nodes():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Phase 3.7 graph has no nodes",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )


def test_cross_phase_rejects_empty_graph_edges():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Phase 3.7 graph has no edges",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "edges": [],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )

def test_cross_phase_rejects_incident_type_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Incident type mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "database_failure",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                    "runtime_compromise",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )


def test_cross_phase_rejects_severity_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Severity mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "HIGH",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                    "runtime_compromise",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )


def test_cross_phase_rejects_signal_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Signal mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                    "runtime_compromise",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "unexpected_signal",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )

def test_cross_phase_rejects_component_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Affected component mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                    "runtime_compromise",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "wrong-component",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "wrong-component",
                    ],
                }
            },
        )

def test_cross_phase_rejects_phase38_phase39_severity_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Severity mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "medium",
                    "confidence": 0.95,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )

def test_cross_phase_rejects_phase38_phase39_component_mismatch():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Affected component mismatch",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 0.95,
                    "affected_components": [
                        "wrong-component",
                    ],
                }
            },
        )

def test_cross_phase_rejects_invalid_confidence():
    from scripts.build_aegis_dataset import (
        validate_cross_phase_consistency,
    )

    with pytest.raises(
        ValueError,
        match="Confidence outside valid range",
    ):
        validate_cross_phase_consistency(
            phase37_summary={
                "incident_id": "INC-001",
                "incident_type": "runtime_compromise",
                "severity": "CRITICAL",
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase37_graph={
                "incident_id": "INC-001",
                "nodes": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "edges": [
                    {
                        "from": "container_shell",
                        "to": "runtime_compromise",
                    }
                ],
            },
            phase38_record={
                "incident": {
                    "id": "INC-001",
                    "type": "runtime_compromise",
                    "severity": "CRITICAL",
                },
                "signals": [
                    "container_shell",
                    "sensitive_file_access",
                ],
                "affected_components": [
                    "netdevops-app",
                    "pg_isready",
                ],
            },
            phase39_record={
                "incident": {
                    "incident_id": "INC-001",
                    "incident_type": "runtime_compromise",
                    "severity": "critical",
                    "confidence": 1.5,
                    "affected_components": [
                        "netdevops-app",
                        "pg_isready",
                    ],
                }
            },
        )