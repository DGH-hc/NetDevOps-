import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "signals"
    / "events_info.json"
)


def collect_events():
    """
    Collect Kubernetes events.
    """

    command = [
        "kubectl",
        "get",
        "events",
        "-n",
        "app",
        "-o",
        "json"
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

    except subprocess.CalledProcessError:

        return {
            "status": "not_collected",
            "events": []
        }

    raw = json.loads(result.stdout)

    events = []

    for item in raw["items"]:

        involved = item.get("involvedObject", {})

        events.append(
            {
                "pod": involved.get("name", ""),
                "reason": item.get("reason", ""),
                "type": item.get("type", ""),
                "message": item.get("message", ""),
                "timestamp": (
                    item.get("eventTime")
                 or item.get("lastTimestamp")
                 or item.get("firstTimestamp")
                 or item.get("metadata", {}).get("creationTimestamp", "")
                )
            }
        )

    return {
        "status": "collected",
        "events": events
    }


def main():

    print("----------------------------------------")
    print(" Kubernetes Events Collector")
    print("----------------------------------------")

    data = collect_events()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )

    print(
        f"✓ Collected {len(data['events'])} event(s)"
    )

    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()