"""
Phase 3.9 - Evidence Generator

Responsible for:
- Collecting decision evidence
- Building an evidence package
- Producing an evidence report

This module does NOT:
- Execute actions
- Modify infrastructure
- Restart Kubernetes resources
"""

from typing import Any

from rules.decision_report import DecisionReport

from rules.audit_trail import AuditTrail


class EvidenceGenerator:
    """
    Generate supporting evidence
    for the selected response plan.
    """

    def __init__(self) -> None:
        self.report = DecisionReport()
        self.audit_trail = AuditTrail()
        print("Evidence Generator initialized successfully.")

    def generate_evidence(self, incident: dict[str, Any],) -> dict[str, Any]:
        decision_report = self.report.build_report(
           incident
        )

        evidence = {
            "incident": decision_report["incident"],
            "decision": decision_report["decision"],
            "action_plan": decision_report["action_plan"],
            "simulation": decision_report["simulation"],
            "validation": decision_report["validation"],
        }

        self.audit_trail.record_event(
            "Evidence Generated",
         {
            "incident_id": incident["incident_id"],
           "validation_status": evidence["validation"]["validation_status"],
            "action_plan": evidence["action_plan"]
         },
        )

        return evidence

if __name__ == "__main__":
    generator = EvidenceGenerator()

    incident = {
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

    result = generator.generate_evidence(
     incident
    )

    print(result)
    print(generator.audit_trail.get_events())