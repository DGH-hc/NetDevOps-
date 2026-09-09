import json
from pathlib import Path

from kubernetes import client, config

OUTPUT_FILE = Path("signals/events_info.json")


def collect_events():
    config.load_kube_config()

    v1 = client.CoreV1Api()

    events = v1.list_event_for_all_namespaces().items

    collected_events = []

    for event in events:
        timestamp = None

        if event.event_time:
            timestamp = event.event_time.isoformat()

        elif event.last_timestamp:
            timestamp = event.last_timestamp.isoformat()

        elif event.first_timestamp:
            timestamp = event.first_timestamp.isoformat()

        collected_events.append(
            {
                "namespace": event.metadata.namespace,
                "pod": (
                    event.involved_object.name
                    if event.involved_object
                    else None
                ),
                "reason": event.reason,
                "type": event.type,
                "message": event.message,
                "timestamp": timestamp,
            }
        )

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
                "status": "collected",
                "events": collected_events,
            },
            f,
            indent=4,
        )

    print(
        f"Collected {len(collected_events)} Kubernetes event(s)"
    )

    print(
        f"Output written to: {OUTPUT_FILE}"
    )


def main():
    collect_events()


if __name__ == "__main__":
    main()