from rules.decision_report import DecisionReport

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


def test_build_report_returns_report():
    report = DecisionReport()

    result = report.build_report(INCIDENT)

    assert "incident" in result
    assert "decision" in result
    assert "action_plan" in result
    assert "simulation" in result
    assert "failure_path" in result
    assert "validation" in result
    assert "report" in result


def test_report_is_ready():
    report = DecisionReport()

    result = report.build_report(INCIDENT)

    assert result["report"]["status"] == "Ready"
    assert result["report"]["overall_recommendation"] == "Proceed with Execution"


def test_report_contains_decision_information():
    report = DecisionReport()

    result = report.build_report(INCIDENT)

    assert result["report"]["playbook"] == "Database Recovery Playbook"
    assert result["report"]["decision_score"] == 100
    assert result["report"]["recommended_action"] == "Restart API Deployment"


def test_report_contains_simulation_information():
    report = DecisionReport()

    result = report.build_report(INCIDENT)

    assert result["report"]["estimated_recovery"] == "30 seconds"
    assert result["report"]["operational_risk"] == "Low"
    assert result["report"]["business_risk"] == "Medium"
    assert result["report"]["success_probability"] == "95%"
    assert result["report"]["simulation_status"] == "Predicted Success"