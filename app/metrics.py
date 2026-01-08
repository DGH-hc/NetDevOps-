# app/metrics.py
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# -----------------------------
# Business / Domain Metrics
# -----------------------------

jobs_pushed_total = Counter(
    "jobs_pushed_total",
    "Total number of network config push jobs enqueued"
)

job_execution_seconds = Histogram(
    "job_execution_duration_seconds",
    "Time taken for a config job to run"
)

# -----------------------------
# HTTP Metrics (FastAPI)
# -----------------------------

def setup_metrics(app):
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/health/live", "/health/ready"],
    ).instrument(app).expose(app, endpoint="/metrics")
