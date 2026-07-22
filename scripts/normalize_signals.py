import json
import hashlib
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
# MITRE Enrichment
# -------------------------

def extract_mitre(tags):

    mitre = {
        "technique": None,
        "tactic": None
    }

    if not tags:
        return mitre

    for tag in tags:

        if tag.startswith("T"):
            mitre["technique"] = tag

        elif tag.startswith("mitre_"):
            mitre["tactic"] = (
                tag
                .replace("mitre_", "")
                .replace("_", " ")
                .title()
            )

    return mitre


# -------------------------
# Confidence Scoring
# -------------------------

def calculate_confidence(severity, source):

    score = 0.50

    # Severity contribution
    severity_bonus = {
        "low": 0.10,
        "medium": 0.20,
        "high": 0.30,
        "critical": 0.40
    }

    score += severity_bonus.get(
        severity,
        0.0
    )

    # Source reliability contribution
    source_bonus = {
        "falco": 0.10,
        "k8s": 0.05,
        "prometheus": 0.05
    }

    score += source_bonus.get(
        source,
        0.0
    )

    return round(
        min(score, 1.0),
        2
    )

# -------------------------
# Event Fingerprinting
# -------------------------

def generate_fingerprint(
    source,
    event_type,
    entity
):

    fingerprint_source = (
        f"{source}|"
        f"{event_type}|"
        f"{json.dumps(entity, sort_keys=True)}"
    )

    return hashlib.sha256(
        fingerprint_source.encode("utf-8")
    ).hexdigest()

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

        
        entity = {
            "process": event["output_fields"].get("proc.name"),
            "container_id": event["output_fields"].get("container.id"),
            "container_name": event["output_fields"].get("container.name"),
            "pod_name": event["output_fields"].get("k8s.pod.name"),
            "namespace": event["output_fields"].get("k8s.ns.name"),
            "host": event.get("hostname"),
            "user": event["output_fields"].get("user.name")
}

        falco_events.append(
            {
                "event_id": next_event_id(),
                "timestamp": normalize_timestamp(event["time"]),
                "source": "falco",
                "severity": matched_rule["severity"],
                "severity_score": SEVERITY_SCORES[
                    matched_rule["severity"]
                ],
                "confidence": calculate_confidence(
                    matched_rule["severity"],
                    "falco"
                ),
                "event_type": matched_rule["event_type"],
                "entity": entity,
                "fingerprint": generate_fingerprint(
                    "falco",
                    matched_rule["event_type"],
                    entity 
                ),
                "mitre": extract_mitre(
                    event.get("tags", [])
                ),
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

    entity = {
        "name": item.get(
            "involvedObject",
            {}
        ).get(
            "name",
            ""
        ),
        "kind": item.get(
            "involvedObject",
            {}
        ).get(
            "kind",
            ""
        ),
        "namespace": item.get(
            "metadata",
            {}
        ).get(
            "namespace",
            ""
        )
    }

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
            "confidence": calculate_confidence(
                matched_rule["severity"],
                "k8s"
            ),
            "event_type": matched_rule["event_type"],
            "entity": entity,
            "fingerprint": generate_fingerprint(
                "k8s",
                matched_rule["event_type"],
                entity
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
        entity = {
            "name": "cluster",
            "metric": "cpu_usage",
            "collector": "prometheus",
            "resource_type": "cluster"
         }

        prom_events.append(
            {
                "event_id": next_event_id(),
                "timestamp": normalize_timestamp(
                  cpu_result[0]["value"][0]
                ),
                "source": "prometheus",
                "severity": "medium",
                "severity_score": SEVERITY_SCORES["medium"],
                "confidence": calculate_confidence(
                  "medium",
                  "prometheus"
                ),
                "event_type": "cpu_metric_detected",
                "entity": entity,
                "fingerprint": generate_fingerprint(
                    "prometheus",
                    "cpu_metric_detected",
                    entity 
                ),
                "raw": {
                       "metric": "cpu_usage",
                       "value": cpu_usage,
                       "unit": "%",
                       "threshold": 80,
                       "comparison": ">=",
                       "status": "threshold_exceeded"
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

    entity = event["entity"]

    key = (
        event["source"],
        event["event_type"],
        json.dumps(
            entity,
            sort_keys=True
        )
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