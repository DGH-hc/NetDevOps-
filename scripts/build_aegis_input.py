import json
from pathlib import Path
from jsonschema import validate 

INPUT_FILE = Path("evidence/phase3.8_root_cause/enriched_incidents.json")
OUTPUT_FILE = Path("evidence/phase3.8_root_cause/aegis_input.json")
SCHEMA_FILE = Path("schemas/aegis_input_schema.json")

REQUIRED_FIELDS = {
    "incident": [
        "incident_id",
        "incident_type",
    ],
    "root_cause": [
        "id",
        "name",
    ],
}

ALLOWED_SEVERITIES = {
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
}


def validate_timeline(incident_id: str, timeline: list):
    if not isinstance(timeline, list):
        raise ValueError(f"[{incident_id}] timeline must be a list")

    for index, entry in enumerate(timeline):
        if not isinstance(entry, dict):
            raise ValueError(
                f"[{incident_id}] timeline[{index}] must be an object"
            )

        for field in ("timestamp", "event", "status"):
            value = entry.get(field)

            if value is None or str(value).strip() == "":
                raise ValueError(
                    f"[{incident_id}] timeline[{index}] missing required field: {field}"
                )


def validate_evidence(incident_id: str, evidence: list):
    if not isinstance(evidence, list):
        raise ValueError(f"[{incident_id}] evidence must be a list")

    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ValueError(
                f"[{incident_id}] evidence[{index}] must be an object"
            )

        evidence_type = item.get("type")
        source = item.get("source")

        if not evidence_type:
            raise ValueError(
                f"[{incident_id}] evidence[{index}] missing required field: type"
            )

        if not source:
            raise ValueError(
                f"[{incident_id}] evidence[{index}] missing required field: source"
            )

        if evidence_type == "signal":
            for field in ("name", "confidence"):
                if field not in item:
                    raise ValueError(
                        f"[{incident_id}] evidence[{index}] missing required field: {field}"
                    )

        elif evidence_type == "timeline_event":
            for field in ("timestamp", "event"):
                value = item.get(field)

                if value is None or str(value).strip() == "":
                    raise ValueError(
                        f"[{incident_id}] evidence[{index}] missing required field: {field}"
                    )


def validate_incident(incident: dict):
    incident_info = incident.get("incident", {})
    root_cause = incident.get("root_cause", {})

    incident_id = incident_info.get("incident_id", "UNKNOWN")

    # Required incident fields
    for field in REQUIRED_FIELDS["incident"]:
        if not incident_info.get(field):
            raise ValueError(
                f"[{incident_id}] Missing required field: incident.{field}"
            )

    # Required root cause fields
    for field in REQUIRED_FIELDS["root_cause"]:
        if not root_cause.get(field):
            raise ValueError(
                f"[{incident_id}] Missing required field: root_cause.{field}"
            )

    # Severity validation
    severity = incident_info.get("severity")

    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(
            f"[{incident_id}] Invalid severity: {severity}"
        )

    # Confidence validation
    confidence = root_cause.get("confidence")

    if confidence is None:
        raise ValueError(
            f"[{incident_id}] Missing root_cause.confidence"
        )

    if not isinstance(confidence, (int, float)):
        raise ValueError(
            f"[{incident_id}] confidence must be numeric"
        )

    if confidence < 0 or confidence > 1:
        raise ValueError(
            f"[{incident_id}] confidence must be between 0.0 and 1.0"
        )

    # Required list fields
    list_fields = [
        "signals",
        "affected_components",
        "timeline",
        "evidence",
        "recommendations",
    ]

    for field in list_fields:
        value = incident.get(field)

        if value is None:
            raise ValueError(
                f"[{incident_id}] Missing required field: {field}"
            )

        if not isinstance(value, list):
            raise ValueError(
                f"[{incident_id}] {field} must be a list"
            )

    # Reject empty signals
    if len(incident["signals"]) == 0:
        raise ValueError(
            f"[{incident_id}] signals cannot be empty"
        )

    # Reject empty recommendations
    if len(incident["recommendations"]) == 0:
        raise ValueError(
            f"[{incident_id}] recommendations cannot be empty"
        )

    # Metadata validation
    metadata = incident.get("metadata")

    if metadata is None:
        raise ValueError(
            f"[{incident_id}] Missing required field: metadata"
        )

    if not isinstance(metadata, dict):
        raise ValueError(
            f"[{incident_id}] metadata must be an object"
        )

    validate_timeline(
        incident_id,
        incident["timeline"],
    )

    validate_evidence(
        incident_id,
        incident["evidence"],
    )


def build_aegis_package(incident: dict):
    incident_info = incident["incident"]
    root_cause = incident["root_cause"]

    return {
        "package_version": "1.0",
        "generated_by": "Phase3.8 AegisAI Package Builder",
        "incident": {
            "id": incident_info["incident_id"],
            "type": incident_info["incident_type"],
            "severity": incident_info.get("severity"),
            "detected_at": incident_info.get("detected_at"),
        },
        "root_cause": {
            "id": root_cause["id"],
            "name": root_cause["name"],
            "hint": root_cause.get("hint"),
            "confidence": root_cause.get("confidence"),
        },
        "signals": incident["signals"],
        "affected_components": incident["affected_components"],
        "timeline": incident["timeline"],
        "evidence": incident["evidence"],
        "recommendations": incident["recommendations"],
    }

def validate_package_schema(packages):
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    with SCHEMA_FILE.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validate(
        instance=packages,
        schema=schema,
    )

    print("AegisAI schema validation passed.")
    

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        incidents = json.load(f)

    aegis_packages = []

    for incident in incidents:
        validate_incident(incident)
        aegis_packages.append(build_aegis_package(incident))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(aegis_packages, f, indent=4)

    validate_package_schema(aegis_packages)

    print("AegisAI package validation passed.")
    print(f"Generated {len(aegis_packages)} AegisAI package(s)")
    print(f"Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()