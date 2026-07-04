THIS_IS_NEW_FILE = True 

import json
from pathlib import Path

# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

EVENTS_FILE = BASE_DIR / "evidence" / "phase3.6_signals" / "normalized_events.json"
RULES_FILE = BASE_DIR / "rules" / "correlation_rules.json"

OUTPUT_DIR = BASE_DIR / "evidence" / "phase3.7_incidents"
OUTPUT_FILE = OUTPUT_DIR / "incident_summary.json"

# ---------------------------------------------------------------------
# Load Normalized Events
# ---------------------------------------------------------------------

def load_events():
    with open(EVENTS_FILE, "r", encoding="utf-8") as file:
        events = json.load(file)

    print(f"[INFO] Loaded {len(events)} normalized events.")

    return events


# ---------------------------------------------------------------------
# Load Correlation Rules
# ---------------------------------------------------------------------

def load_rules():

    with open(RULES_FILE, "r", encoding="utf-8") as file:
        rules = json.load(file)

    print(f"[INFO] Loaded {len(rules)} correlation rules.")

    return rules

# ---------------------------------------------------------------------
# Generate Incident
# ---------------------------------------------------------------------

def generate_incident(rule, matched_events, incident_number):

    timestamps = [
        event["timestamp"]
        for event in matched_events
        if event.get("timestamp")
    ]

    entities = sorted({
        event["entity"]
        for event in matched_events
        if event.get("entity")
    })

    incident = {
        "incident_id": f"INC-{incident_number:03d}",
        "incident_type": rule["incident_type"],
        "start_time": min(timestamps) if timestamps else "",
        "end_time": max(timestamps) if timestamps else "",
        "severity": rule["severity"],
        "signals": rule["conditions"],
        "root_cause_hint": rule["root_cause_hint"],
        "affected_components": entities
    }

    return incident


# ---------------------------------------------------------------------
# Save Incidents
# ---------------------------------------------------------------------

def save_incidents(incidents):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(incidents, file, indent=4)

    print(f"[INFO] Saved {len(incidents)} incidents to:")
    print(f"       {OUTPUT_FILE}")



# ==========================================================
# INSERT generate_timeline() HERE
# ==========================================================

def generate_timeline(events, incidents):

    timeline = []

    for incident in incidents:

        incident_events = []

        for event in events:

            if event["event_type"] in incident["signals"]:

                incident_events.append({
                    "timestamp": event["timestamp"],
                    "event": event["event_type"]
                })

        incident_events.sort(key=lambda event: event["timestamp"])

        timeline.append({
            "incident_id": incident["incident_id"],
            "timeline": incident_events
        })

    TIMELINE_FILE = OUTPUT_DIR / "incident_timeline.json"

    with open(TIMELINE_FILE, "w", encoding="utf-8") as file:
        json.dump(timeline, file, indent=4)

    print(f"[INFO] Timeline saved to: {TIMELINE_FILE}")

# ---------------------------------------------------------------------
# Generate Incident Graph
# ---------------------------------------------------------------------

def generate_incident_graph(incidents):

    graph = []

    for incident in incidents:

        nodes = []
        edges = []

        # Add all signals as nodes
        for signal in incident["signals"]:

            nodes.append(signal)

            edges.append({
                "from": signal,
                "to": incident["incident_type"]
            })

        # Add the incident itself as a node
        nodes.append(incident["incident_type"])

        graph.append({
            "incident_id": incident["incident_id"],
            "nodes": nodes,
            "edges": edges
        })

    graph_file = OUTPUT_DIR / "incident_graph.json"

    with open(graph_file, "w", encoding="utf-8") as file:
        json.dump(graph, file, indent=4)

    print(f"[INFO] Graph saved to: {graph_file}")


# ---------------------------------------------------------------------
# Match Rules Against Events
# ---------------------------------------------------------------------

def match_rules(events, rules):

    incidents = []

    event_types = {
        event["event_type"]
        for event in events
    }

    print("\n[INFO] Available Event Types")

    for event in sorted(event_types):
        print(f"  - {event}")

    print()

    for rule in rules:

        required_conditions = set(rule["conditions"])

        if required_conditions.issubset(event_types):

            print(f"[MATCH] {rule['incident_type']}")

            matched_events = [
             event
             for event in events
             if event["event_type"] in required_conditions
            ]

            incident = generate_incident(
             rule,
             matched_events,
             len(incidents) + 1
            )

            incidents.append(incident)

    return incidents


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    events = load_events()

    rules = load_rules()

    incidents = match_rules(events, rules)

    generate_timeline(events, incidents)

    generate_incident_graph(incidents)

    save_incidents(incidents)

    print("\n==============================")
    print("Generated Incidents")
    print("==============================")

    if not incidents:
        print("No incidents detected.")

    else:
        for index, incident in enumerate(incidents, start=1):

            print(f"\nIncident {index}")
            print(f"Type       : {incident['incident_type']}")
            print(f"Severity   : {incident['severity']}")
            print(f"Signals    : {', '.join(incident['signals'])}")
            print(f"Root Cause : {incident['root_cause_hint']}")

    print("\nFinished Incident Correlation.")


# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()