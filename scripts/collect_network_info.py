import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "signals"
    / "network_info.json"
)


def collect_network():

    command = [
        "kubectl",
        "get",
        "networkpolicy",
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
            "network_policies": []
        }

    raw = json.loads(result.stdout)

    policies = []

    for item in raw["items"]:

        metadata = item.get("metadata", {})
        spec = item.get("spec", {})

        policies.append(
            {
                "name": metadata.get("name", ""),
                "pod_selector": spec.get("podSelector", {}),
                "policy_types": spec.get("policyTypes", []),
                "ingress_rules": len(spec.get("ingress", [])),
                "egress_rules": len(spec.get("egress", []))
            }
        )

    return {
        "status": "collected",
        "network_policies": policies
    }


def main():

    print("----------------------------------------")
    print(" Network Collector")
    print("----------------------------------------")

    data = collect_network()

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
        f"✓ Collected {len(data['network_policies'])} network policy(s)"
    )

    print(f"✓ Saved : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()