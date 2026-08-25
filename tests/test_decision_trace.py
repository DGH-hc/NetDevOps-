from rules.decision_engine import DecisionEngine


def test_decision_trace_is_generated():
    engine = DecisionEngine()

    incident = {
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

    decision = engine.select_playbook(incident)

    assert "decision_trace" in decision
    assert len(decision["decision_trace"]) == 5

    criteria = [
        item["criterion"]
        for item in decision["decision_trace"]
    ]

    assert criteria == [
        "incident_type",
        "root_cause",
        "components",
        "severity",
        "confidence",
    ]

    assert decision["total_score"] == 75

def test_playbook_version_is_preserved():
    from rules.action_planner import ActionPlanner

    planner = ActionPlanner()

    incident = {
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

    result = planner.build_action_plan(incident)

    assert result["decision"]["playbook_version"] == "1.0"

def test_expected_evidence_is_preserved():
    from rules.action_planner import ActionPlanner

    planner = ActionPlanner()

    incident = {
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

    result = planner.build_action_plan(incident)

    assert result["action_plan"]["expected_evidence"] == [
        "Container logs",
        "Runtime events",
        "Kubernetes audit logs",
    ]

def test_score_breakdown_is_preserved():
    from rules.decision_engine import DecisionEngine

    engine = DecisionEngine()

    incident = {
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

    result = engine.select_playbook(incident)

    assert result["total_score"] == 75
    assert result["score_breakdown"] == {
        "incident_type": 40,
        "root_cause": 0,
        "components": 20,
        "severity": 10,
        "confidence": 5,
    }

def test_decision_id_is_generated():
    from rules.decision_engine import DecisionEngine

    incident = {
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

    decision = DecisionEngine().select_playbook(incident)

    assert "decision_id" in decision
    assert decision["decision_id"].startswith("DEC-")
    assert len(decision["decision_id"]) == 12

def test_decision_id_propagates_through_evidence_generator():
    from rules.evidence_generator import EvidenceGenerator

    incident = {
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

    result = EvidenceGenerator().generate_evidence(incident)

    decision_id = result["decision"]["decision_id"]

    assert decision_id.startswith("DEC-")
    assert len(decision_id) == 12