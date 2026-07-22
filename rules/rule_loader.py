import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RULES_FILE = (
    PROJECT_ROOT
    / "rules"
    / "root_cause_rules.json"
)


REQUIRED_FIELDS = {
    "id",
    "name",
    "priority",
    "required_signals",
    "optional_signals",
    "hint",
    "confidence",
}


def validate_rules(rules):
    """
    Validate root cause rule schema.
    """

    if not isinstance(rules, list):
        raise ValueError("Root cause rules must be a list.")

    seen_ids = set()

    for index, rule in enumerate(rules):

        missing = REQUIRED_FIELDS - rule.keys()

        if missing:
            raise ValueError(
                f"Rule #{index} missing fields: {sorted(missing)}"
            )

        if rule["id"] in seen_ids:
            raise ValueError(
                f"Duplicate rule id: {rule['id']}"
            )

        seen_ids.add(rule["id"])

        if not isinstance(rule["confidence"], (int, float)):
            raise ValueError(
                f"Invalid confidence in rule: {rule['id']}"
            )


def load_rules():
    """
    Load and validate root cause rules.
    """

    if not RULES_FILE.exists():
        raise FileNotFoundError(
            f"Rule file not found: {RULES_FILE}"
        )

    with open(RULES_FILE, "r", encoding="utf-8") as file:
        rules = json.load(file)

    validate_rules(rules)

    return rules


if __name__ == "__main__":

    rules = load_rules()

    print(f"✓ Loaded {len(rules)} root cause rules")

    for rule in rules:
        print(f"- {rule['id']}")