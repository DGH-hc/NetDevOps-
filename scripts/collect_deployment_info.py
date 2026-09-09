import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "signals"
    / "deployment_info.json"
)


def collect_deployments():
    """
    Collect deployment information from Kubernetes.
    """

    command = [
        "kubectl",
        "get",
        "deployments",
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

    deployments = json.loads(result.stdout)["items"]

    deployment_data = []

    for deployment in deployments:

        spec = deployment.get("spec", {})
        status = deployment.get("status",{})
        metadata = deployment.get("metadata", {})
        template = spec.get("template", {})
        pod_spec = template.get("spec", {})
        containers = pod_spec.get("containers", [])

    deployment_data.append(
    {
        "deployment_name": metadata.get("name", ""),
        "namespace": metadata.get("namespace", ""),
        "replicas": spec.get("replicas", 0),

        "available_replicas": status.get(
            "availableReplicas",
            0,
        ),

        "ready_replicas": status.get(
            "readyReplicas",
            0,
        ), 

        "updated_replicas": status.get(
            "updatedReplicas",
            0,
        ),

        "image": (
            containers[0].get("image", "")
            if containers else ""
        ),

        "service_account": pod_spec.get(
            "serviceAccountName",
            "default"
        ),

        "timestamp": metadata.get(
            "creationTimestamp"
        ),
    }
)
    return deployment_data


def main():

    print("----------------------------------------")
    print(" Deployment Collector")
    print("----------------------------------------")

    deployments = collect_deployments()

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
            {
                "status": "collected",
                "deployments": deployments,
            },
            file,
            indent=4,
        )

    print(f"✓ Collected {len(deployments)} deployment(s)")
    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()