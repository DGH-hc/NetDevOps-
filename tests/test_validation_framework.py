from rules.validation_framework import ValidationFramework


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


def test_validate_response_passes():
    validator = ValidationFramework()

    result = validator.validate_response(INCIDENT)

    assert result["validation"]["validation_passed"] is True
    assert result["validation"]["checks_passed"] is True
    assert result["validation"]["overall_validation"] is True
    assert result["validation"]["validation_status"] == "Validation Passed"


def test_validate_simulation_passes():
    validator = ValidationFramework()

    simulation_report = {
        "simulation": {
            "simulation_status": "Predicted Success",
        }
    }

    assert validator.validate_simulation(simulation_report) is True


def test_validate_simulation_fails():
    validator = ValidationFramework()

    simulation_report = {
        "simulation": {
            "simulation_status": "Predicted Failure",
        }
    }

    assert validator.validate_simulation(simulation_report) is False


def test_validate_checks_requires_checks():
    validator = ValidationFramework()

    simulation_report = {
        "simulation": {
            "validation_checks": [
                "Pods enter Running state",
                "Readiness probe passes",
            ]
        }
    }

    assert validator.validate_checks(simulation_report) is True