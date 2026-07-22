import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PHASE38 = PROJECT_ROOT / "evidence" / "phase3.8_root_cause"

REQUIRED_FILES = [
    "enriched_incidents.json",
    "context_collection.json",
    "root_cause_summary.json",
    "affected_components.json",
    "investigation_timeline.json"
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


print("----------------------------------------")
print(" Phase 3.8 Validation")
print("----------------------------------------")

# -------------------------------------------------------
# Check required files
# -------------------------------------------------------

for filename in REQUIRED_FILES:

    file_path = PHASE38 / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Missing evidence file: {filename}")

print("✓ All evidence artifacts exist")

# -------------------------------------------------------
# Load artifacts
# -------------------------------------------------------

enriched = load_json(PHASE38 / "enriched_incidents.json")
context = load_json(PHASE38 / "context_collection.json")
root_causes = load_json(PHASE38 / "root_cause_summary.json")
affected = load_json(PHASE38 / "affected_components.json")
timeline = load_json(PHASE38 / "investigation_timeline.json")

print("✓ All JSON artifacts loaded")

# -------------------------------------------------------
# Count validation
# -------------------------------------------------------

expected = len(enriched)

assert len(context) == expected
assert len(root_causes) == expected
assert len(affected) == expected
assert len(timeline) == expected

print(f"✓ Incident count validated ({expected})")

# -------------------------------------------------------
# Investigation validation
# -------------------------------------------------------

for report in enriched:

    assert report["incident"]["incident_id"]

    assert report["context"]

    assert report["root_cause"]["hint"]

    assert report["timeline"]

    assert report["evidence"]

    assert report["metadata"]

print("✓ Investigation reports validated")

# -------------------------------------------------------
# Phase Gate
# -------------------------------------------------------

print()
print("----------------------------------------")
print(" PHASE 3.8 GATE")
print("----------------------------------------")

print("✓ Enriched incidents generated")
print("✓ Context collection generated")
print("✓ Root cause summary generated")
print("✓ Affected components generated")
print("✓ Investigation timeline generated")
print("✓ Investigation reports validated")

print()
print("PHASE 3.8 STATUS : PASS")
print("----------------------------------------")