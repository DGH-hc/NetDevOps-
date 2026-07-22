import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "signals"
    / "application_logs.json"
)


def get_app_pod():
    """
    Return the first NetDevOps application pod.
    """

    command = [
        "kubectl",
        "get",
        "pods",
        "-n",
        "app",
        "-o",
        "json"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    pods = json.loads(result.stdout)["items"]

    for pod in pods:

        pod_name = pod["metadata"]["name"]

        if "netdevops-app" in pod_name:
            return pod_name

    raise RuntimeError("No NetDevOps application pod found.")


def collect_logs(pod_name):
    """
    Collect logs from the application pod.
    """

    command = [
        "kubectl",
        "logs",
        "-n",
        "app",
        pod_name
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout.splitlines()


def main():

    print("----------------------------------------")
    print(" Application Log Collector")
    print("----------------------------------------")

    pod_name = get_app_pod()

    print(f"✓ Pod Found : {pod_name}")

    logs = collect_logs(pod_name)

    structured_logs = []

    for line in logs:

        structured_logs.append(
            {
                "pod": pod_name,
                "message": line
            }
        )

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
            structured_logs,
            file,
            indent=4
        )

    print(f"✓ Collected {len(structured_logs)} log entries")
    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()