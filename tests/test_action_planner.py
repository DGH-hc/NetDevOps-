from rules.action_planner import ActionPlanner


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


def test_build_action_plan_returns_primary_action():
    planner = ActionPlanner()

    result = planner.build_action_plan(valid_incident())

    assert result["action_plan"]["primary_actions"]
    assert (
        result["action_plan"]["primary_actions"][0]["name"]
        == "Restart API Deployment"
    )


def test_build_action_plan_returns_correct_playbook():
    planner = ActionPlanner()

    result = planner.build_action_plan(valid_incident())

    assert result["decision"]["playbook_id"] == "PB-DB-001"


def test_build_action_plan_builds_execution_order():
    planner = ActionPlanner()

    result = planner.build_action_plan(valid_incident())

    execution_order = result["action_plan"]["execution_order"]

    assert len(execution_order) == 1
    assert execution_order[0]["step"] == 1
    assert execution_order[0]["phase"] == "Primary"


def test_build_action_plan_preserves_action_id():
    planner = ActionPlanner()

    result = planner.build_action_plan(valid_incident())

    action = result["action_plan"]["primary_actions"][0]

    assert action["id"] == "ACT-001"