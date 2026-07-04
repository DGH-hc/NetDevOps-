import json
import yaml
from datetime import datetime, timezone  
from pathlib import Path
from prometheus_client import (
    get_cpu_metrics,
    get_memory_available,
    get_memory_total
)

# -------------------------
# Event IDs
# -------------------------

event_counter = 1
 
# -------------------------
# Timestamp Normalization
# -------------------------

def normalize_timestamp(timestamp):

    if not timestamp:
        return ""

    # Kubernetes timestamps are already ISO-8601
    if isinstance(timestamp, str) and "T" in timestamp:
        return timestamp

    # Prometheus UNIX timestamp
    try:
        ts = float(timestamp)

        return datetime.fromtimestamp(
            ts,
            tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

    except (TypeError, ValueError):
        pass

    return str(timestamp)

def next_event_id():
    global event_counter
    event_id = f"evt-{event_counter:06d}"
    event_counter += 1
    return event_id


# -------------------------
# Severity Scores
# -------------------------

SEVERITY_SCORES = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}


# -------------------------
# Load Detection Rules
# -------------------------

with open("config/detection_rules.yaml", "r") as f:
    RULES = yaml.safe_load(f)


Path("signals").mkdir(exist_ok=True)
Path("evidence/phase3.6_signals").mkdir(
    parents=True,
    exist_ok=True
)


# =====================================================
# FALCO
# =====================================================

falco_events = []

with open("signals/falco_raw.log", "r") as f:

    for line in f:

        try:
              event = json.loads(line)
        except json.JSONDecodeError:
          continue

        matched_rule = None

        for rule in RULES["falco"]:
            if rule["match"] in event["output"]:
                matched_rule = rule
                break

        if not matched_rule:
            continue

        
        entity = "unknown"

        if matched_rule["event_type"] == "sensitive_file_access":
            entity = "pg_isready"

        elif matched_rule["event_type"] == "container_shell":
            entity = "netdevops-app"

        falco_events.append(
            {
                "event_id": next_event_id(),
                "timestamp": normalize_timestamp(event["time"]),
                "source": "falco",
                "severity": matched_rule["severity"],
                "severity_score": SEVERITY_SCORES[
                    matched_rule["severity"]
                ],
                "event_type": matched_rule["event_type"],
                "entity": entity,
                "raw": event 
            }
        )

with open("signals/falco_events.json", "w") as f:
    json.dump(falco_events, f, indent=2)

print(f"Generated {len(falco_events)} events")


# =====================================================
# K8S
# =====================================================

k8s_events = []

with open("signals/k8s_events_raw.json", "r") as f:
    data = json.load(f)

for item in data["items"]:

    reason = item.get("reason", "")

    matched_rule = None

    for rule in RULES["k8s"]:

        if rule["match"] == reason:
            matched_rule = rule
            break

    if not matched_rule:
        continue

    k8s_events.append(
        {
            "event_id": next_event_id(),
            "timestamp": normalize_timestamp(
                item.get("lastTimestamp", "")
            ),
            "source": "k8s",
            "severity": matched_rule["severity"],
            "severity_score": SEVERITY_SCORES[
                matched_rule["severity"]
            ],
            "event_type": matched_rule["event_type"],
            "entity": item.get(
                "involvedObject",
                {}
            ).get(
                "name",
                ""
            ),
            "raw": {
                "reason": reason
            }
        }
    )

with open("signals/k8s_events.json", "w") as f:
    json.dump(k8s_events, f, indent=2)

print(f"Generated {len(k8s_events)} k8s events")


# =====================================================
# PROMETHEUS
# =====================================================

prom_events = []

cpu_metrics = get_cpu_metrics()

memory_available = get_memory_available()

memory_total = get_memory_total()


# -----------------------------------------------------
# DEBUG
# -----------------------------------------------------

print(f"CPU Samples: {len(cpu_metrics['data']['result'])}")
print(f"Memory Available Samples: {len(memory_available['data']['result'])}")
print(f"Memory Total Samples: {len(memory_total['data']['result'])}")



# -----------------------------------------------------
# CPU Utilization
# -----------------------------------------------------

cpu_result = cpu_metrics["data"]["result"]

if cpu_result:

    cpu_usage = float(cpu_result[0]["value"][1])

    print(f"CPU Usage: {cpu_usage:.2f}%")

    # -----------------------------------------------------
    # CPU Threshold
    # -----------------------------------------------------

    if cpu_usage >= 80:

        prom_events.append(
            {
                "event_id": next_event_id(),
                "timestamp": normalize_timestamp(
                  cpu_result[0]["value"][0]
                ),
                "source": "prometheus",
                "severity": "medium",
                "severity_score": SEVERITY_SCORES["medium"],
                "event_type": "cpu_metric_detected",
                "entity": "cluster",
                "raw": {
                    "cpu_usage": cpu_usage
                }
            }
        )

with open(
    "signals/prometheus_anomalies.json",
    "w"
) as f:
    json.dump(prom_events, f, indent=2)

print(
    f"Generated {len(prom_events)} prometheus events"
)


# =====================================================
# AGGREGATION
# =====================================================

all_events = (
    falco_events
    + k8s_events
    + prom_events
)

# =====================================================
# DEDUPLICATION
# =====================================================

unique_events = []
seen = set()

for event in all_events:

    key = (
        event["source"],
        event["event_type"],
        event["entity"]
    )

    if key not in seen:
        seen.add(key)
        unique_events.append(event)

all_events = unique_events

with open(
    "evidence/phase3.6_signals/normalized_events.json",
    "w"
) as f:
    json.dump(all_events, f, indent=2)

print(
    f"Generated {len(all_events)} total normalized events"
)


# =====================================================
# SOURCE STATISTICS
# =====================================================

stats = {
    "falco": len(falco_events),
    "k8s": len(k8s_events),
    "prometheus": len(prom_events),
    "total_raw": (
        len(falco_events)
        + len(k8s_events)
        + len(prom_events)
    ),
    "total_unique": len(all_events)
}

with open(
    "evidence/phase3.6_signals/source_statistics.json",
    "w"
) as f:
    json.dump(stats, f, indent=2)

print("Generated source statistics")