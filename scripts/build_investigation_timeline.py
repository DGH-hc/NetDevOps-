import json
from datetime import datetime, timezone
from pathlib import Path

PHASE37_TIMELINE = Path(
    "evidence/phase3.7_correlation/incident_timeline.json"
)

EVENTS_FILE = Path(
    "signals/events_info.json"
)

DEPLOYMENT_FILE = Path(
    "signals/deployment_info.json"
)

METRICS_FILE = Path(
    "signals/metrics_info.json"
)

NETWORK_FILE = Path(
    "signals/network_info.json"
)

SECURITY_FILE = Path(
    "signals/security_info.json"
)

RECENT_CHANGES_FILE = Path(
    "signals/recent_changes.json"
)

OUTPUT_FILE = Path(
    "evidence/phase3.8_root_cause/investigation_timeline.json"
)


def load_json(path):
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if "events" in data:
        return data["events"]

    if "pods" in data:
        return data["pods"]

    if "network_policies" in data:
        return data["network_policies"]

    if "changes" in data:
        return data["changes"]

    return []


def normalize_phase37(events, incident_id):
    normalized = []

    if isinstance(events, dict):
        events = [events]

    for event in events:
        normalized.append(
            {
                "timestamp": event.get("timestamp"),
                "source": "Phase3.7",
                "event": event.get("event", "unknown"),
                "status": event.get("status", "observed"),
                "details": event,
                "incident_id": incident_id, 
            }
        )

    return normalized


def normalize_generic(events, source_name, incident_id):
    normalized = []

    if isinstance(events, dict):
        events = [events]

    for event in events:
        normalized.append(
            {
                "timestamp": event.get("timestamp"),
                "source": source_name,
                "event": event.get(
                    "event",
                    event.get(
                        "type",
                        "unknown",
                    ),
                ),
                "status": event.get(
                    "status",
                    "observed",
                ),
                "details": event,
                "incident_id": incident_id,
            }
        )

    return normalized

def sort_key(event):
    timestamp = event.get("timestamp")

    if timestamp is None:
        return datetime.max.replace(tzinfo=timezone.utc)

    timestamp = str(timestamp).replace("Z", "+00:00")

    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%H:%M:%S.%f",
        "%H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return datetime.max.replace(tzinfo=timezone.utc)

def validate_event(event):
    # Event name is mandatory
    if not event.get("event"):
        return False

    # Source is mandatory
    if not event.get("source"):
        return False

    # Status is mandatory
    if not event.get("status"):
        event["status"] = "observed"

    # Missing timestamp is allowed for inventory/configuration snapshots
    if not event.get("timestamp"):
        event["timestamp"] = None

    return True

def remove_duplicates(events):
    unique = []
    seen = set()

    for event in events:
        key = (
            event.get("timestamp"),
            event.get("source"),
            event.get("event"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(event)

    return unique

def build_summary(events):
    timestamps = [
        event["timestamp"]
        for event in events
        if event.get("timestamp")
    ]

    return {
        "total_events": len(events),
        "first_event": timestamps[0] if timestamps else None,
        "last_event": timestamps[-1] if timestamps else None,
        "sources": sorted(
            list(
                {
                    event["source"]
                    for event in events
                }
            )
        ),
    }

def build_timeline(incident_id="GLOBAL"):

    merged = []

    merged.extend(
        normalize_phase37(
            load_json(PHASE37_TIMELINE),
            incident_id,
        )
    )

    merged.extend(
        normalize_generic(
            load_json(EVENTS_FILE),
            "Kubernetes Events",
            incident_id,
        )
    )

    merged.extend(
        normalize_generic(
            load_json(DEPLOYMENT_FILE),
            "Deployment",
            incident_id,
        )
    )

    merged.extend(
        normalize_generic(
            load_json(METRICS_FILE),
            "Metrics",
            incident_id,
        )
    )

    merged.extend(
        normalize_generic(
            load_json(NETWORK_FILE),
            "Network",
            incident_id,
        )
    )

    merged.extend(
        normalize_generic(
            load_json(SECURITY_FILE),
            "Falco",
            incident_id,
        )
    )

    merged.extend(
        normalize_generic(
            load_json(RECENT_CHANGES_FILE),
            "Recent Changes",
            incident_id,
        )
    )

    valid_events = []
    invalid_events = 0

    for event in merged:
        if validate_event(event):
          valid_events.append(event)
        else:
             invalid_events += 1

    valid_events = remove_duplicates(valid_events)

    valid_events.sort(key=sort_key)

    merged = valid_events

    summary = build_summary(merged)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
             {
               "summary": summary,
               "timeline": merged,
            },
            f,
            indent=4,
        )

    print(
      f"Generated {summary['total_events']} investigation timeline event(s)"
)

    print(
      f"Sources: {len(summary['sources'])}"
)

    print(
       f"Skipped {invalid_events} invalid event(s)"
)

    print(
       f"Output written to: {OUTPUT_FILE}"
)


if __name__ == "__main__":
    build_timeline()