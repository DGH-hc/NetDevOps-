import pytest

from rules.decision_engine import DecisionEngine


def valid_incident():
    return {
        "incident_id": "INC-001",
        "incident_type": "database_failure",
        "confidence": 0.91,
        "severity": "high",
        "affected_components": [
            "PostgreSQL",
            "API",
        ],
        "root_cause_hint": "Database connection saturation",
    }


def test_validate_incident_accepts_valid_incident():
    engine = DecisionEngine()

    engine.validate_incident(valid_incident())


def test_validate_incident_rejects_missing_required_field():
    engine = DecisionEngine()

    incident = valid_incident()
    del incident["confidence"]

    with pytest.raises(
        ValueError,
        match="Missing required incident field: 'confidence'",
    ):
        engine.validate_incident(incident)


def test_select_playbook_returns_database_recovery_playbook():
    engine = DecisionEngine()

    result = engine.select_playbook(valid_incident())

    assert result["playbook_id"] == "PB-DB-001"
    assert result["playbook_name"] == "Database Recovery Playbook"


def test_select_playbook_returns_expected_score():
    engine = DecisionEngine()

    result = engine.select_playbook(valid_incident())

    assert result["total_score"] == 100
