from rules.evidence_generator import EvidenceGenerator


INCIDENT = {
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


def test_generate_evidence_returns_expected_sections():
    generator = EvidenceGenerator()

    result = generator.generate_evidence(INCIDENT)

    assert "incident" in result
    assert "decision" in result
    assert "simulation" in result
    assert "validation" in result


def test_evidence_contains_incident():
    generator = EvidenceGenerator()

    result = generator.generate_evidence(INCIDENT)

    assert result["incident"]["incident_id"] == "INC-001"
    assert result["incident"]["incident_type"] == "database_failure"
    assert result["incident"]["confidence"] == 0.91


def test_evidence_contains_decision_and_simulation():
    generator = EvidenceGenerator()

    result = generator.generate_evidence(INCIDENT)

    assert result["decision"]["playbook_id"] == "PB-DB-001"
    assert result["decision"]["decision_score"] == 100
    assert result["simulation"]["simulation_status"] == "Predicted Success"
    assert result["simulation"]["success_probability"] == "95%"


def test_evidence_generation_records_audit_event():
    generator = EvidenceGenerator()

    generator.generate_evidence(INCIDENT)

    events = generator.audit_trail.get_events()

    assert len(events) == 1
    assert events[0]["event_type"] == "Evidence Generated"
    assert events[0]["details"]["incident_id"] == "INC-001"
    assert events[0]["details"]["validation_status"] == "Validation Passed"