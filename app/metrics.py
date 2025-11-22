# app/metrics.py
from prometheus_client import Counter, Histogram

# Track number of jobs pushed
jobs_pushed_total = Counter(
    "jobs_pushed_total",
    "Total number of network config push jobs enqueued"
)

# Track job execution duration
job_execution_seconds = Histogram(
    "job_execution_duration_seconds",
    "Time taken for a config job to run"
)

# Track API request latency
request_latency_seconds = Histogram(
    "api_request_latency_seconds",
    "Latency of API endpoints in seconds",
    ["endpoint", "method"]
)
