import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone 

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = PROJECT_ROOT / "signals" / "security_info.json"


def collect_security():

    command = [
        "kubectl",
        "get",
        "pods",
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
            "pods": []
        }

    raw = json.loads(result.stdout)

    pods = []

    for item in raw.get("items", []):

        spec = item.get("spec", {})

        pod_name = item.get("metadata", {}).get("name", "")
        service_account = spec.get("serviceAccountName", "default")

        containers = []

        for container in spec.get("containers", []):

            security = container.get("securityContext", {})

        containers.append(
            {
               "container": container.get("name", ""),
               "image": container.get("image"),
               "run_as_user": security.get("runAsUser"),
               "run_as_non_root": security.get("runAsNonRoot"),
               "allow_privilege_escalation": security.get("allowPrivilegeEscalation"),
               "read_only_root_filesystem": security.get("readOnlyRootFilesystem"),
               "privileged": security.get("privileged"),
               "capabilities": security.get("capabilities"),
            }
)

        pods.append(
         {
           "pod": pod_name,
            "namespace": item.get("metadata", {}).get("namespace", ""),
            "node": spec.get("nodeName"),
            "phase": item.get("status", {}).get("phase"),
            "service_account": service_account,
            "created_at": item.get("metadata", {}).get("creationTimestamp"),
            "containers": containers
        }
)

    return {
    "status": "collected",
    "collected_at": datetime.now(
        timezone.utc
    ).isoformat(),
    "pod_count": len(pods),
    "pods": pods
}


def main():

    print("----------------------------------------")
    print(" Security Collector")
    print("----------------------------------------")

    data = collect_security()

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

    print(f"✓ Collected {data['pod_count']} pod(s)")
    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()