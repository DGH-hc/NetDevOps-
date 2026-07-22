from rules.rule_loader import load_rules


def determine_root_cause(summary):
    """
    Determine the root cause using the rule library.
    """

    incident_type = summary["incident_type"]

    rules = load_rules()

    for rule in rules:

        if rule["id"] == incident_type:

            return {
                  "id": rule["id"],
                  "name": rule["name"],
                  "hint": rule["hint"],
                  "confidence": rule["confidence"]
}

    return {
        "id": "unknown",
        "name": "Unknown",
        "hint": "Unknown",
        "confidence": 0.10
    }


if __name__ == "__main__":

    test_summary = {
        "incident_type": "runtime_compromise"
    }

    result = determine_root_cause(test_summary)

    print(result)