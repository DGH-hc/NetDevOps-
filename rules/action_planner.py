"""
Phase 3.9 - Action Planner

Responsible for:
- Extracting actions from a selected playbook
- Resolving action IDs into action definitions
- Organizing actions into execution order
- Returning an ordered action plan

This module does NOT:
- Execute actions
- Simulate actions
- Modify infrastructure
"""

from typing import Any

from rules.action_catalog_loader import ActionCatalogLoader
from rules.decision_engine import DecisionEngine


class ActionPlanner:
    """
    Build ordered action plans
    from Decision Engine output.
    """

    def __init__(self) -> None:
        self.engine = DecisionEngine()
        self.catalog = ActionCatalogLoader()

    def resolve_primary_actions(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Resolve primary action IDs into
        complete action definitions.
        """

        resolved_actions = []

        for action_id in playbook["actions"]["primary"]:

            action = self.catalog.get_action(action_id).copy()

            action["id"] = action_id

            resolved_actions.append(action)

        return resolved_actions

    def resolve_alternative_actions(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Resolve alternative action IDs into
        complete action definitions.
        """

        resolved_actions = []

        for action_id in playbook["actions"]["alternatives"]:

            action = self.catalog.get_action(action_id).copy()

            action["id"] = action_id

            resolved_actions.append(action)

        return resolved_actions

    def resolve_prerequisites(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Resolve prerequisite action IDs into
        complete action definitions.
        """

        resolved_actions = []

        for action_id in playbook["actions"]["prerequisites"]:

            action = self.catalog.get_action(action_id).copy()

            action["id"] = action_id

            resolved_actions.append(action)

        return resolved_actions

    def resolve_post_actions(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Resolve post-action IDs into
        complete action definitions.
        """

        resolved_actions = []

        for action_id in playbook["actions"]["post_actions"]:

            action = self.catalog.get_action(action_id).copy()

            action["id"] = action_id

            resolved_actions.append(action)

        return resolved_actions

    def build_execution_order(
        self,
        primary_actions: list[dict[str, Any]],
        prerequisites: list[dict[str, Any]],
        post_actions: list[dict[str, Any]],
        dependency_graph: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Build the ordered execution plan.
        """

        execution_order = []

        step = 1

        for action in prerequisites:
            execution_order.append(
                {
                    "step": step,
                    "phase": "Prerequisite",
                    "action": action,
                }
            )
            step += 1

        action_map = {
            action["id"]: action
            for action in primary_actions
        }

        ordered_ids = []

        def add_action(action_id: str) -> None:
            if action_id in ordered_ids:
                return

            dependencies = next(
                (
                    item["depends_on"]
                    for item in dependency_graph
                    if item["action"] == action_id
                ),
                [],
            )

            for dependency_id in dependencies:
                add_action(dependency_id)

            ordered_ids.append(action_id)

        for action in primary_actions:
            add_action(action["id"])

        for action_id in ordered_ids:
            execution_order.append(
                {
                    "step": step,
                    "phase": "Primary",
                    "action": action_map[action_id],
                }
            )
            step += 1

        for action in post_actions:
            execution_order.append(
                {
                    "step": step,
                    "phase": "Post Action",
                    "action": action,
                }
            )
            step += 1

        return execution_order

    def build_dependency_graph(
        self,
        playbook: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Build the action dependency graph from playbook dependencies.
        """

        dependencies = playbook["actions"].get(
            "dependencies",
            [],
        )

        graph = []

        for dependency in dependencies:
            graph.append(
                {
                    "action": dependency["action"],
                    "depends_on": dependency["depends_on"],
                }
            )

        return graph


    def build_action_plan(
        self,
        incident: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build an ordered action plan
        from the selected playbook.
        """

        decision = self.engine.select_playbook(
            incident
        )

        playbook = decision["playbook"]

        primary_actions = self.resolve_primary_actions(
            playbook
        )

        alternative_actions = self.resolve_alternative_actions(
            playbook
        )

        prerequisites = self.resolve_prerequisites(
            playbook
        )

        post_actions = self.resolve_post_actions(
            playbook
        )

        dependency_graph = self.build_dependency_graph(
            playbook
        )

        execution_order = self.build_execution_order(
            primary_actions,
            prerequisites,
            post_actions,
            dependency_graph,
        )

        return {
            "incident": {
                "incident_id": incident.get("incident_id"),
                "incident_type": incident.get("incident_type"),
                "severity": incident.get("severity"),
                "confidence": incident.get("confidence"),
                "affected_components": incident.get("affected_components"),
                "root_cause_hint": incident.get("root_cause_hint"),
            },

            "decision": {
                "decision_id": decision.get("decision_id"),
                "playbook_id": playbook.get("playbook_id"),
                "playbook_name": playbook.get("name"),
                "playbook_version": decision["playbook_version"],
                "decision_score": decision.get("total_score"),
                "score_breakdown": decision.get("score_breakdown"),
                "decision_trace": decision.get("decision_trace"),
                "expected_evidence": playbook.get("validation", {}).get("evidence_required", []),
            },

            "action_plan": {
                "primary_actions": primary_actions,
                "alternative_actions": alternative_actions,
                "prerequisites": prerequisites,
                "post_actions": post_actions,
                "execution_order": execution_order,
                "dependency_graph": dependency_graph,
                "expected_evidence": playbook.get("validation", {}).get("evidence_required", []),
            },
        }


if __name__ == "__main__":

    planner = ActionPlanner()

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

    plan = planner.build_action_plan(
        incident
    )

    print(plan)