import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rules.evidence_generator import EvidenceGenerator


INPUT_FILE = (
    PROJECT_ROOT
    / "evidence/phase3.8_root_cause/enriched_incidents.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "evidence/phase3.9_response_simulation/integration_results.json"
)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Phase 3.8 output not found: {INPUT_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        incidents = json.load(file)

    if not isinstance(incidents, list):
        raise ValueError(
            "Phase 3.8 output must contain a list of incidents."
        )

    generator = EvidenceGenerator()

    results = []

    for package in incidents:
        incident = {
            "incident_id": package["incident"]["incident_id"],
            "incident_type": package["incident"]["incident_type"],
            "confidence": package["root_cause"]["confidence"],
            "severity": package["incident"]["severity"].lower(),
            "affected_components": [
                       component["name"]
                       if isinstance(component, dict)
                       else component
                       for component in package["affected_components"]
                    ],
            "root_cause_hint": package["root_cause"]["hint"],
        }

        result = generator.generate_evidence(incident)
        results.append(result)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    print(
        f"Integrated {len(results)} Phase 3.8 incident(s) into Phase 3.9."
    )
    print(f"Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()