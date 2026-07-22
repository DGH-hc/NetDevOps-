import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RECOMMENDATIONS_FILE = (
    PROJECT_ROOT
    / "rules"
    / "investigation_recommendations.json"
)


def load_recommendation_rules():
    """
    Load investigation recommendation rules.
    """

    with open(RECOMMENDATIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_recommendations(root_cause_id):
    """
    Return investigation recommendations for a root cause.
    """

    rules = load_recommendation_rules()

    if root_cause_id in rules:
        return rules[root_cause_id]["recommendations"]

    return rules["default"]["recommendations"]