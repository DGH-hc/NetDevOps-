import json
import copy 
from pathlib import Path
from datetime import datetime, UTC
import sys 

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rules.rule_engine import determine_root_cause 
from rules.recommendation_engine import get_recommendations 

def load_json(file_path):
    """
    Load and return JSON data from a file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_optional_json(file_path, fallback):
    """ """
    try:
        return load_json(file_path)
    except FileNotFoundError:
        return fallback

def collect_logs(incident):
    """
    Collect relevant application logs for an incident.
    """

    LOG_FILE = (
        PROJECT_ROOT
        / "signals"
        / "application_logs.json"
    )

    if not LOG_FILE.exists():
        return {
            "status": "missing",
            "entries": [],
            "summary": "Application log evidence not found."
        }

    logs = load_json(LOG_FILE)

    matched_logs = []

    for log in logs:
        message = log.get("message", "").lower()
        pod = log.get("pod", "").lower()

        for component in incident["affected_components"]:
            component = component.lower()

            if (
                component in message
                or component in pod
                or component.split("-")[0] in pod
            ):
                matched_logs.append(log)
                break

    return {
        "status": "collected",
        "entries": matched_logs,
        "summary": (
            f"{len(matched_logs)} log entries matched "
            f"affected components."
        )
    }

def collect_deployment(incident):
    """
    Collect deployment information from stored evidence.
    """

    if not DEPLOYMENT_INFO_FILE.exists():
        return {
            "status": "missing",
            "deployment_name": "",
            "namespace": "",
            "replicas": "",
            "image": "",
            "service_account": ""
        }

    deployments = load_json(DEPLOYMENT_INFO_FILE)

    for deployment in deployments:

        deployment_name = deployment.get(
            "deployment_name",
            ""
        ).lower()

        for component in incident["affected_components"]:

            if deployment_name in component.lower():

                deployment["status"] = "collected"
                return deployment

    return {
        "status": "not_found",
        "deployment_name": "",
        "namespace": "",
        "replicas": "",
        "image": "",
        "service_account": ""
    }

def collect_metrics(incident):
    """
    Collect metrics from stored evidence.
    """

    if not METRICS_INFO_FILE.exists():
        return {
            "status": "missing",
            "cpu_usage": "",
            "memory_usage": ""
        }

    metrics = load_json(METRICS_INFO_FILE)

    if metrics["status"] != "collected":
        return metrics

    for pod in metrics["pods"]:

        pod_name = pod["pod"].lower()

        for component in incident["affected_components"]:

            if component.lower() in pod_name:

                return {
                    "status": "collected",
                    "cpu_usage": pod["cpu_usage"],
                    "memory_usage": pod["memory_usage"]
                }

    return {
        "status": "not_found",
        "cpu_usage": "",
        "memory_usage": ""
    }

def collect_events(incident):
    """
    Collect Kubernetes event information from stored evidence.
    """

    return {
        "status": "not_collected",
        "events": [],
        "warnings": [],
        "errors": []
    }

def collect_network(incident):
    """
    Collect network information from stored evidence.
    """

    return load_optional_json(
        NETWORK_INFO_FILE,
        {
            "status": "unavailable",
            "reason": "file_not_found",
            "network_policies": []
        }
    )

def collect_security(incident):
    """
    Collect security information from stored evidence.
    """

    return load_optional_json(
        SECURITY_INFO_FILE,
        {
            "status": "unavailable",
            "reason": "file_not_found",
            "pods": []
        }
    )

def collect_recent_changes(incident):
    """
    Collect recent deployment information from stored evidence.
    """

    return load_optional_json(
        RECENT_CHANGES_FILE,
        {
            "status": "unavailable",
            "reason": "file_not_found",
            "deployments": []
        }
    )


def build_investigation_timeline(timeline):
    """
    Build investigation timeline from Phase 3.7 timeline.
    """

    investigation_timeline = []

    for item in timeline["timeline"]:

        investigation_timeline.append(
            {
                "timestamp": item["timestamp"],
                "event": item["event"],
                "status": "observed"
            }
        )

    return investigation_timeline

def build_evidence(summary, timeline):
    """
    Build structured evidence for an investigation report.
    """

    evidence = []

    for signal in summary["signals"]:

        evidence.append(
            {
                "type": "signal",
                "name": signal,
                "source": "Phase3.7 Correlation Engine",
                "confidence": 0.90
            }
        )

    for item in timeline["timeline"]:

        evidence.append(
            {
                "type": "timeline_event",
                "timestamp": item["timestamp"],
                "event": item["event"],
                "source": "Incident Timeline"
            }
        )

    return evidence

def build_metadata():
    """
    Build metadata for the investigation report.
    """

    return {
        "enriched_at": datetime.now(UTC).isoformat(),
        "schema_version": "1.0",
        "generated_by": "Phase3.8 Investigation Engine"
    }

def build_summary(summary):
    """
    Generate investigation summary.
    """

    incident_type = summary["incident_type"]

    if incident_type == "runtime_compromise":

        title = "Runtime Compromise Detected"

        description = (
            "Sensitive file access followed by an interactive "
            "container shell was correlated into a runtime "
            "compromise incident."
        )

    elif incident_type == "pod_restart_cycle":

        title = "Pod Restart Cycle"

        description = (
            "A Kubernetes pod terminated and restarted. "
            "The investigation recommends checking deployment "
            "history and Kubernetes events."
        )

    elif incident_type == "resource_pressure":

        title = "Resource Pressure"

        description = (
            "Resource utilization likely contributed to workload "
            "instability and pod termination."
        )

    else:

        title = "Unknown Incident"

        description = (
            "No summary available."
        )

    return {
        "title": title,
        "description": description
    }

# ------------------------------------------------------------------
# Project Paths
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUMMARY_FILE = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.7_incidents"
    / "incident_summary.json"
)

GRAPH_FILE = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.7_incidents"
    / "incident_graph.json"
)

TIMELINE_FILE = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.7_incidents"
    / "incident_timeline.json"
)

SCHEMA_FILE = (
    PROJECT_ROOT
    / "schemas"
    / "investigation_ready_incident.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.8_root_cause"
    / "enriched_incidents.json"
)

DEPLOYMENT_INFO_FILE = (
    PROJECT_ROOT
    / "signals"
    / "deployment_info.json"
)

METRICS_INFO_FILE = (
    PROJECT_ROOT
    / "signals"
    / "metrics_info.json"
)

CONTEXT_OUTPUT = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.8_root_cause"
    / "context_collection.json"
)

ROOT_CAUSE_OUTPUT = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.8_root_cause"
    / "root_cause_summary.json"
)

AFFECTED_COMPONENTS_OUTPUT = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.8_root_cause"
    / "affected_components.json"
)

INVESTIGATION_TIMELINE_OUTPUT = (
    PROJECT_ROOT
    / "evidence"
    / "phase3.8_root_cause"
    / "investigation_timeline.json"
)

NETWORK_INFO_FILE = (
    PROJECT_ROOT
    / "signals"
    / "network_info.json"
)

SECURITY_INFO_FILE = (
    PROJECT_ROOT
    / "signals"
    / "security_info.json"
)

RECENT_CHANGES_FILE = (
    PROJECT_ROOT
    / "signals"
    / "recent_changes.json"
)

# ------------------------------------------------------------------
# Load Required Files
# ------------------------------------------------------------------

schema = load_json(SCHEMA_FILE)
summaries = load_json(SUMMARY_FILE)
graphs = load_json(GRAPH_FILE)
timelines = load_json(TIMELINE_FILE)

enriched_incidents = []
context_reports = []
root_cause_reports = []
affected_components_reports = []
investigation_timeline_reports = []

print("✓ Investigation schema loaded successfully")
print(f"✓ Summary incidents loaded : {len(summaries)}")
print(f"✓ Graph incidents loaded   : {len(graphs)}")
print(f"✓ Timeline incidents loaded: {len(timelines)}")

print("\n---------------------------------------------")
print("Loading Incident Packages")
print("---------------------------------------------")


# ------------------------------------------------------------------
# Process Incidents
# ------------------------------------------------------------------

for summary in summaries:

    incident_id = summary["incident_id"]

    graph = next(
        g for g in graphs
        if g["incident_id"] == incident_id
    )

    timeline = next(
        t for t in timelines
        if t["incident_id"] == incident_id
    )

    investigation_report = copy.deepcopy(schema)

    investigation_report["incident"]["incident_id"] = summary["incident_id"]
    investigation_report["incident"]["incident_type"] = summary["incident_type"]
    investigation_report["incident"]["severity"] = summary["severity"]
    investigation_report["incident"]["detected_at"] = summary["start_time"]

    investigation_report["signals"] = summary["signals"]
    investigation_report["affected_components"] = summary["affected_components"]

    investigation_report["phase3_7"]["summary"] = summary
    investigation_report["phase3_7"]["graph"] = graph
    investigation_report["phase3_7"]["timeline"] = timeline
    investigation_report["context"]["logs"] = collect_logs(summary)
    investigation_report["context"]["deployment"] = collect_deployment(summary)
    investigation_report["context"]["metrics"] = collect_metrics(summary)
    investigation_report["context"]["events"] = collect_events(summary)
    investigation_report["context"]["network"] = collect_network(summary)
    investigation_report["context"]["security"] = collect_security(summary)
    investigation_report["context"]["recent_changes"] = collect_recent_changes(summary)
    
    root_cause = determine_root_cause(summary)

    investigation_report["root_cause"] = root_cause

    investigation_report["recommendations"] = get_recommendations(
    root_cause["id"]
)

    investigation_report["timeline"] = build_investigation_timeline(timeline) 
    investigation_timeline_reports.append(
    {
        "incident_id": incident_id,
        "timeline": investigation_report["timeline"]
    }
)
    
    investigation_report["evidence"] = build_evidence(summary, timeline)
    investigation_report["metadata"] = build_metadata()
    investigation_report["summary"] = build_summary(summary)
    
    print(f"\n✓ Investigation Report: {incident_id}")
    print(json.dumps(investigation_report, indent=4))

    enriched_incidents.append(investigation_report)
 
    context_reports.append(
    {
        "incident_id": incident_id,
        "context": investigation_report["context"]
    }
)
    
    root_cause_reports.append(
    {
        "incident_id": incident_id,
        "incident_type": summary["incident_type"],
        "severity": summary["severity"],
        "root_cause": investigation_report["root_cause"]["hint"],
        "confidence": investigation_report["root_cause"]["confidence"]
    }
)
    
    affected_components_reports.append(
    {
        "incident_id": incident_id,
        "incident_type": summary["incident_type"],
        "affected_components": summary["affected_components"]
    }
)


with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(enriched_incidents, file, indent=4)

with open(CONTEXT_OUTPUT, "w", encoding="utf-8") as file:
    json.dump(context_reports, file, indent=4)

print("✓ Context Collection Saved")
print(f"✓ Output: {CONTEXT_OUTPUT}")

with open(ROOT_CAUSE_OUTPUT, "w", encoding="utf-8") as file:
    json.dump(root_cause_reports, file, indent=4)

print("✓ Root Cause Summary Saved")
print(f"✓ Output: {ROOT_CAUSE_OUTPUT}")

with open(AFFECTED_COMPONENTS_OUTPUT, "w", encoding="utf-8") as file:
    json.dump(affected_components_reports, file, indent=4)

print("✓ Affected Components Saved")
print(f"✓ Output: {AFFECTED_COMPONENTS_OUTPUT}")

with open(INVESTIGATION_TIMELINE_OUTPUT, "w", encoding="utf-8") as file:
    json.dump(investigation_timeline_reports, file, indent=4)

print("✓ Investigation Timeline Saved")
print(f"✓ Output: {INVESTIGATION_TIMELINE_OUTPUT}")

print(f"\n✓ Saved {len(enriched_incidents)} investigation reports")
print(f"✓ Output: {OUTPUT_FILE}")

print("\n---------------------------------------------")
print("Incident Loader Completed Successfully")
print("---------------------------------------------")