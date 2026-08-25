from rules.response_simulator import ResponseSimulator


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


def test_simulate_response_returns_predicted_success():
    simulator = ResponseSimulator()

    result = simulator.simulate_response(valid_incident())

    assert result["simulation"]["simulation_status"] == "Predicted Success"


def test_simulate_response_returns_expected_outcome():
    simulator = ResponseSimulator()

    result = simulator.simulate_response(valid_incident())

    assert (
        result["simulation"]["predicted_outcome"]
        == "Application pods are recreated and service availability is restored."
    )


def test_simulate_response_returns_success_probability():
    simulator = ResponseSimulator()

    result = simulator.simulate_response(valid_incident())

    assert result["simulation"]["success_probability"] == "95%"


def test_simulate_response_returns_validation_checks():
    simulator = ResponseSimulator()

    result = simulator.simulate_response(valid_incident())

    checks = result["simulation"]["validation_checks"]

    assert len(checks) == 3
    assert "Pods enter Running state" in checks
    assert "Readiness probe passes" in checks
    assert "Health endpoint returns HTTP 200" in checks

def test_simulate_response_returns_recovery_confidence():
    simulator = ResponseSimulator()

    result = simulator.simulate_response(valid_incident())

    assert result["simulation"]["recovery_confidence"]["score"] == 0.95
    assert result["simulation"]["recovery_confidence"]["level"] == "High"
    source = result["simulation"]["recovery_confidence"]["source"]

    assert source["type"] == "root_cause_confidence"
    assert source["value"] == 0.91

def test_simulate_response_returns_recovery_confidence_source():
    simulator = ResponseSimulator()

    result = simulator.simulate_response(valid_incident())

    source = result["simulation"]["recovery_confidence"]["source"]

    assert source["type"] == "root_cause_confidence"
    assert source["value"] == 0.91