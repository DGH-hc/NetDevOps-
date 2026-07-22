import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = PROJECT_ROOT / "signals" / "recent_changes.json"


def collect_recent_changes():

    command = [
        "kubectl",
        "get",
        "deployments",
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
            "deployments": []
        }

    raw = json.loads(result.stdout)

    deployments = []

    for item in raw.get("items", []):

        metadata = item.get("metadata", {})
        spec = item.get("spec", {})

        containers = (
            spec.get("template", {})
            .get("spec", {})
            .get("containers", [])
        )

        images = [
            container.get("image", "")
            for container in containers
        ]

        deployments.append(
            {
                "name": metadata.get("name", ""),
                "generation": metadata.get("generation"),
                "created": metadata.get("creationTimestamp"),
                "replicas": spec.get("replicas"),
                "images": images
            }
        )

    return {
        "status": "collected",
        "deployments": deployments
    }


def main():

    print("----------------------------------------")
    print(" Recent Changes Collector")
    print("----------------------------------------")

    data = collect_recent_changes()

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
        f"✓ Collected {len(data['deployments'])} deployment(s)"
    )

    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()