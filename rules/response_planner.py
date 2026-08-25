"""
Phase 3.9 - Response Planner

Responsible for:
- Building response plans
- Producing structured response recommendations
- Building the high-level response chain

This module does NOT:
- Execute infrastructure changes
- Simulate responses
- Modify Kubernetes
"""

from typing import Any

from decision_engine import DecisionEngine


class ResponsePlanner:
    """
    Build operational response plans from
    Decision Engine output.
    """

    def __init__(self) -> None:
        self.engine = DecisionEngine()

    def build_response_plan(
        self,
        incident: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build a complete response plan
        from the selected playbook.
        """

        decision = self.engine.select_playbook(
            incident
        )

        playbook = decision["playbook"]

        response_chain = self.build_response_chain(
         playbook
        )

        response_sequence = self.build_response_sequence(
         response_chain
        )

        primary_actions = self.get_primary_actions(
            playbook
        )

        return {
    "incident": {
        "incident_id": incident["incident_id"],
        "incident_type": incident["incident_type"],
        "severity": incident["severity"],
        "confidence": incident["confidence"],
        "affected_components": incident["affected_components"],
        "root_cause_hint": incident["root_cause_hint"],
    },

     "decision": {
     "playbook_id": decision["playbook_id"],
     "playbook_name": decision["playbook_name"],
     "decision_score": decision["total_score"],
     "selection_criteria": decision["criteria"],
     "decision_trace": decision["decision_trace"],
    },

    "response_plan": {
        "primary_actions": primary_actions,
        "response_chain": response_chain,
        "response_sequence": response_sequence,
    },
}

    def build_response_chain(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Build the high-level response chain
        for the selected playbook.
        """

        return [
            {
                "phase": "Investigation",
                "description": (
                    "Verify incident conditions before recovery."
                ),
            },
            {
                "phase": "Recovery",
                "description": (
                    "Perform recommended recovery actions."
                ),
            },
            {
                "phase": "Validation",
                "description": (
                    "Confirm system health has been restored."
                ),
            },
            {
                "phase": "Monitoring",
                "description": (
                    "Observe the system for recurring issues."
                ),
            },
            {
                "phase": "Closure",
                "description": (
                    "Collect evidence and close the incident."
                ),
            },
        ]

    def build_response_sequence(
        self,
        response_chain: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Build the execution sequence for
        the response chain.
        """

        sequence = []

        for step_number, phase in enumerate(
            response_chain,
            start=1,
        ):
            sequence.append(
                {
                    "step": step_number,
                    "phase": phase["phase"],
                    "description": phase["description"],
                }
            )

        return sequence

    def get_primary_actions(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Return the primary actions defined
        in the selected playbook.
        """

        return playbook["actions"]["primary"]


if __name__ == "__main__":

    planner = ResponsePlanner()

    incident = {
        "incident_id": "INC-001",
        "incident_type": "database_failure",
        "confidence": 0.91,
        "severity": "high",
        "affected_components": [
            "PostgreSQL",
            "API",
        ],
        "root_cause_hint": (
            "Database connection saturation"
        ),
    }

    response_plan = planner.build_response_plan(
        incident
    )

    print(response_plan)