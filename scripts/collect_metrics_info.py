import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "signals"
    / "metrics_info.json"
)


def collect_metrics():
    """
    Collect live Kubernetes pod metrics.
    """

    command = [
        "kubectl",
        "top",
        "pods",
        "-n",
        "app",
        "--no-headers"
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
            "reason": "metrics-server unavailable",
            "pods": []
        }

    metrics = []

    for line in result.stdout.splitlines():

        parts = line.split()

        if len(parts) < 3:
            continue

        metrics.append(
            {
                "pod": parts[0],
                "cpu_usage": parts[1],
                "memory_usage": parts[2]
            }
        )

    return {
        "status": "collected",
        "pods": metrics
    }


def main():

    print("----------------------------------------")
    print(" Metrics Collector")
    print("----------------------------------------")

    metrics = collect_metrics()

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
            metrics,
            file,
            indent=4
        )

    if metrics["status"] == "collected":

        print(
            f"✓ Collected metrics for {len(metrics['pods'])} pod(s)"
        )

    else:

        print("✓ Metrics unavailable")

    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()