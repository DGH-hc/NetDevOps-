from rules.failure_path_simulator import FailurePathSimulator


def make_incident():
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


def test_failure_path_simulator_returns_failure_path():
    simulator = FailurePathSimulator()

    result = simulator.simulate_failure(
        make_incident()
    )

    assert "failure_path" in result


def test_failure_path_contains_required_fields():
    simulator = FailurePathSimulator()

    result = simulator.simulate_failure(
        make_incident()
    )

    failure_path = result["failure_path"]

    assert "failure_detected" in failure_path
    assert "fallback_actions" in failure_path
    assert "escalation_required" in failure_path
    assert "terminate_simulation" in failure_path


def test_successful_simulation_does_not_detect_failure():
    simulator = FailurePathSimulator()

    result = simulator.simulate_failure(
        make_incident()
    )

    assert result["simulation"]["simulation_status"] == "Predicted Success"
    assert result["failure_path"]["failure_detected"] is False


def test_failure_path_returns_fallback_actions_as_list():
    simulator = FailurePathSimulator()

    result = simulator.simulate_failure(
        make_incident()
    )

    assert isinstance(
        result["failure_path"]["fallback_actions"],
        list,
    )