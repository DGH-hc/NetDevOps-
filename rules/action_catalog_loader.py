"""
Phase 3.9 - Action Catalog Loader

Responsible for:
- Loading the action catalog
- Looking up actions by ID
- Returning action definitions

This module does NOT:
- Execute actions
- Plan responses
- Simulate responses
"""

from pathlib import Path
from typing import Any

import yaml

ACTION_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "action_catalog"
    / "actions_v1.yaml"
)

class ActionCatalogLoader:
    """
    Load the action catalog.
    """

    def __init__(self) -> None:
        with open(
            ACTION_CATALOG_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            self.catalog = yaml.safe_load(file)
    def get_action(self, action_id: str) -> dict[str, Any]:
        """Return a single action definition."""

        return self.catalog["actions"][action_id]

if __name__ == "__main__":

    loader = ActionCatalogLoader()

    print(loader.get_action("ACT-001"))