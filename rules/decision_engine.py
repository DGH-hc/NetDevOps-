"""
Phase 3.9 - Decision Engine

Responsible for:
- Selecting the best matching playbook
- Evaluating incident conditions
- Returning the recommended playbook

This module does NOT:
- Execute actions
- Simulate responses
- Modify infrastructure
- Generate reports
"""
import uuid
from typing import Any

from rules.playbook_loader import load_all_playbooks

REQUIRED_INCIDENT_FIELDS = [
    "incident_id",
    "incident_type",
    "confidence",
    "severity",
    "affected_components",
    "root_cause_hint",
]

SCORING_WEIGHTS = {
    "incident_type": 40,
    "root_cause": 25,
    "components": 20,
    "severity": 10,
    "confidence": 5,
}

class DecisionEngine:
    """
    Decision Engine for selecting response playbooks.
    """

    def __init__(self) -> None:
        self.playbooks = load_all_playbooks()

    def validate_incident(
        self,
        incident: dict[str, Any],
    ) -> None:
        """
        Validate the required incident structure.
        """

        for field in REQUIRED_INCIDENT_FIELDS:
            if field not in incident:
                raise ValueError(
                    f"Missing required incident field: '{field}'"
                )

    def score_incident_type(
        self,
        incident: dict[str, Any],
        playbook: dict[str, Any],
    ) -> int:
        """
        Score the incident type match.

        Returns:
            int:
                Match score.
        """

        if (
            incident["incident_type"]
            == playbook["incident_type"]
        ):
            return SCORING_WEIGHTS["incident_type"]

        return 0

    def score_root_cause(
        self,
        incident: dict[str, Any],
        playbook: dict[str, Any],
    ) -> int:
        """
        Score the root cause match.

        Returns:
            int:
                Match score.
        """

        root_cause = incident["root_cause_hint"]

        supported_root_causes = playbook["conditions"][
            "required_root_causes"
        ]

        if root_cause in supported_root_causes:

            return SCORING_WEIGHTS["root_cause"]

        return 0

    def score_components(
        self,
        incident: dict[str, Any],
        playbook: dict[str, Any],
    ) -> int:
        """
        Score affected component matches.

        Returns:
            int:
               Match score.
        """

        incident_components = set(
            incident["affected_components"]
        )

        required_components = set(
            playbook["conditions"]["required_components"]
        )

        if required_components.issubset(incident_components):
            return SCORING_WEIGHTS["components"]

        return 0

    def score_severity(
        self,
        incident: dict[str, Any],
        playbook: dict[str, Any],
    ) -> int:
        """
        Score incident severity.

        Returns:
            int:
                Match score.
        """

        severity = incident["severity"]

        supported_levels = playbook["conditions"][
            "severity_levels"
        ]

        if severity in supported_levels:
            return SCORING_WEIGHTS["severity"]

        return 0

    def score_confidence(
        self,
        incident: dict[str, Any],
        playbook: dict[str, Any],
    ) -> int:
        """
        Score incident confidence.

        Returns:
            int:
                Match score.
        """

        confidence = incident["confidence"]

        minimum_confidence = playbook["conditions"][
            "minimum_confidence"
        ]

        if confidence >= minimum_confidence:
            return SCORING_WEIGHTS["confidence"]

        return 0

    def score_playbook(
        self,
        incident: dict[str, Any],
        playbook: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate a detailed score for a playbook.
        """

        incident_type_score = self.score_incident_type(
            incident,
            playbook,
        )

        root_cause_score = self.score_root_cause(
            incident,
            playbook,
        )

        component_score = self.score_components(
            incident,
            playbook,
        )

        severity_score = self.score_severity(
            incident,
            playbook,
        )

        confidence_score = self.score_confidence(
            incident,
            playbook,
        )

        total_score = (
            incident_type_score
            + root_cause_score
            + component_score
            + severity_score
            + confidence_score
        )

        decision_trace = [
            {
                "criterion": "incident_type",
                "matched": incident_type_score > 0,
                "score": incident_type_score,
                "weight": SCORING_WEIGHTS["incident_type"],
                "reason": (
                    "Incident type matches playbook"
                    if incident_type_score > 0
                    else "Incident type does not match playbook"
                ),
            },
            {
                "criterion": "root_cause",
                "matched": root_cause_score > 0,
                "score": root_cause_score,
                "weight": SCORING_WEIGHTS["root_cause"],
                "reason": (
                    "Root cause matches playbook"
                    if root_cause_score > 0
                    else "Root cause does not match playbook"
                ),
            },
            {
                "criterion": "components",
                "matched": component_score > 0,
                "score": component_score,
                "weight": SCORING_WEIGHTS["components"],
                "reason": (
                    "Affected components match playbook"
                    if component_score > 0
                    else "Affected components do not match playbook"
                ),
            },
            {
                "criterion": "severity",
                "matched": severity_score > 0,
                "score": severity_score,
                "weight": SCORING_WEIGHTS["severity"],
                "reason": (
                    "Severity matches playbook"
                    if severity_score > 0
                    else "Severity does not match playbook"
                ),
            },
            {
                "criterion": "confidence",
                "matched": confidence_score > 0,
                "score": confidence_score,
                "weight": SCORING_WEIGHTS["confidence"],
                "reason": (
                    "Confidence meets playbook threshold"
                    if confidence_score > 0
                    else "Confidence is below playbook threshold"
                ),
            },
        ]

        return {
            "decision_id": f"DEC-{uuid.uuid4().hex[:8].upper()}",
            "playbook_id": playbook["playbook_id"],
            "playbook_name": playbook["name"],
            "playbook_version": playbook["version"],
            "incident_type": playbook["incident_type"],
            "total_score": total_score,
            "score_breakdown": {
                "incident_type": incident_type_score,
                "root_cause": root_cause_score,
                "components": component_score,
                "severity": severity_score,
                "confidence": confidence_score,
            },
            "criteria": {
                "incident_type": incident_type_score,
                "root_cause": root_cause_score,
                "components": component_score,
                "severity": severity_score,
                "confidence": confidence_score,
            },
            "decision_trace": decision_trace,
            "playbook": playbook,
        }

    def select_playbook(
        self,
        incident: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Select the highest-scoring matching playbook for an incident.
        """

        self.validate_incident(incident)

        best_result = None

        for playbook in self.playbooks:

            result = self.score_playbook(
                incident,
                playbook,
            )

            # A playbook must match the incident type.
            if result["criteria"]["incident_type"] == 0:
                continue

            if (
                best_result is None
                or result["total_score"] > best_result["total_score"]
            ):
                best_result = result

        if best_result is None:
            raise ValueError(
                f"No matching playbook found for incident type: "
                f"'{incident['incident_type']}'"
            )

        return best_result


if __name__ == "__main__":

    engine = DecisionEngine()

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

    engine.validate_incident(incident)
    selected = engine.select_playbook(
        incident,
    )

    print(selected)