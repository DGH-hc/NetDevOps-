"""
Phase 3.9 - Playbook Loader

Responsible for:
- Loading decision playbooks
- Loading the action catalog
- Validating YAML structure
- Returning structured Python objects

This module does NOT:
- Select playbooks
- Execute decisions
- Run simulations
- Score actions
"""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PLAYBOOK_DIR = PROJECT_ROOT / "decision_playbooks"

ACTION_CATALOG = PROJECT_ROOT / "action_catalog" / "actions_v1.yaml"

def verify_playbook_directory() -> Path:
    """
    Verify that the decision playbook directory exists.

    Returns:
        Path: Path to the decision playbook directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """

    if not PLAYBOOK_DIR.exists():
        raise FileNotFoundError(
            f"Decision playbook directory not found: {PLAYBOOK_DIR}"
        )

    return PLAYBOOK_DIR

def discover_playbooks() -> list[Path]:
    """
    Discover all decision playbook YAML files.

    Returns:
        list[Path]: Sorted list of playbook file paths.
    """

    playbook_dir = verify_playbook_directory()

    playbooks = sorted(playbook_dir.glob("*.yaml"))

    return playbooks

def load_playbook(playbook_path: Path) -> dict:
    """
    Load a single decision playbook.

    Args:
        playbook_path (Path):
            Path to the playbook YAML file.

    Returns:
        dict:
            Parsed playbook data.
    """

    with playbook_path.open("r", encoding="utf-8") as file:
        playbook = yaml.safe_load(file)

    return playbook

def validate_playbook(playbook: dict) -> None:
    """
    Validate the required structure of a decision playbook.

    Args:
        playbook (dict):
            Parsed playbook dictionary.

    Raises:
        ValueError:
            If any required top-level field is missing.
    """

    required_fields = [
        "version",
        "playbook_id",
        "incident_type",
        "name",
        "description",
        "priority",
        "enabled",
        "conditions",
        "actions",
        "validation",
        "failure_path",
        "metadata",
    ]

    for field in required_fields:
        if field not in playbook:
            raise ValueError(
                f"Missing required playbook field: '{field}'"
            )

def load_all_playbooks() -> list[dict]:
    """
    Load and validate all decision playbooks.

    Returns:
        list[dict]:
            List of validated playbooks.
    """

    loaded_playbooks = []

    playbook_files = discover_playbooks()

    for playbook_file in playbook_files:

        playbook = load_playbook(playbook_file)

        validate_playbook(playbook)

        loaded_playbooks.append(playbook)

    return loaded_playbooks

def verify_action_catalog() -> Path:
    """
    Verify that the action catalog exists.

    Returns:
        Path: Path to the action catalog.

    Raises:
        FileNotFoundError:
            If the catalog file does not exist.
    """

    if not ACTION_CATALOG.exists():
        raise FileNotFoundError(
            f"Action catalog not found: {ACTION_CATALOG}"
        )

    return ACTION_CATALOG

def load_action_catalog() -> dict:
    """
    Load the action catalog.

    Returns:
        dict:
            Parsed action catalog.
    """

    catalog_path = verify_action_catalog()

    with catalog_path.open("r", encoding="utf-8") as file:
        catalog = yaml.safe_load(file)

    return catalog

def resolve_action_references(
    playbook: dict,
    action_catalog: dict,
) -> dict:
    """
    Resolve action IDs inside a playbook into full action definitions.

    Args:
        playbook (dict):
            Loaded playbook.

        action_catalog (dict):
            Loaded action catalog.

    Returns:
        dict:
            Playbook with enriched action definitions.
    """

    resolved_actions = []

    catalog_actions = action_catalog["actions"]

    for action_id in playbook["actions"]["primary"]:

        if action_id not in catalog_actions:
            raise ValueError(
                f"Unknown action ID: {action_id}"
            )

        action = catalog_actions[action_id].copy()

        action["id"] = action_id

        resolved_actions.append(action)

    playbook["actions"]["primary"] = resolved_actions

    return playbook

if __name__ == "__main__":

    playbooks = load_all_playbooks()

    catalog = load_action_catalog()

    print(f"\nLoaded {len(playbooks)} playbook(s)\n")

    for playbook in playbooks:

        enriched = resolve_action_references(
            playbook,
            catalog,
        )

        print(enriched)