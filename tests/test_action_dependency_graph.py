from rules.action_planner import ActionPlanner


def runtime_compromise_incident():
    return {
        "incident_id": "INC-001",
        "incident_type": "runtime_compromise",
        "confidence": 0.95,
        "severity": "critical",
        "affected_components": [
            "netdevops-app",
            "pg_isready",
        ],
        "root_cause_hint": (
            "Likely runtime compromise caused by "
            "interactive shell activity and sensitive file access."
        ),
    }


def test_runtime_compromise_dependency_graph():
    planner = ActionPlanner()

    playbook = next(
        p
        for p in planner.engine.playbooks
        if p["playbook_id"] == "PB-SEC-002"
    )

    graph = planner.build_dependency_graph(playbook)

    assert graph == [
        {"action": "ACT-006", "depends_on": []},
        {"action": "ACT-007", "depends_on": ["ACT-006"]},
        {"action": "ACT-008", "depends_on": ["ACT-007"]},
        {"action": "ACT-009", "depends_on": ["ACT-008"]},
    ]


def test_runtime_compromise_execution_order_respects_dependencies():
    planner = ActionPlanner()

    result = planner.build_action_plan(
        runtime_compromise_incident()
    )

    execution_ids = [
        item["action"]["id"]
        for item in result["action_plan"]["execution_order"]
    ]

    assert execution_ids == [
        "ACT-006",
        "ACT-007",
        "ACT-008",
        "ACT-009",
    ]

def test_execution_actions_include_risk_dimensions():
    from rules.action_planner import ActionPlanner

    incident = {
        "incident_id": "INC-001",
        "incident_type": "runtime_compromise",
        "confidence": 0.95,
        "severity": "critical",
        "affected_components": ["netdevops-app", "pg_isready"],
        "root_cause_hint": (
            "Likely runtime compromise caused by "
            "interactive shell activity and sensitive file access."
        ),
    }

    result = ActionPlanner().build_action_plan(incident)

    for step in result["action_plan"]["execution_order"]:
        action = step["action"]

        assert "operational_risk" in action
        assert "business_risk" in action
        assert action["operational_risk"] in {
            "Low", "Medium", "High", "Critical"
        }
        assert action["business_risk"] in {
            "Low", "Medium", "High", "Critical"
        }