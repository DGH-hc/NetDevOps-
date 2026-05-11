# app/metrics.py 

from prometheus_client import (
    Counter,
    Histogram,
    CollectorRegistry,
    multiprocess,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Response
import os

# ----------------------------------------
# CRITICAL: multiprocess safety
# ----------------------------------------
# 🔧 FIX: do NOT hard crash outside strict environments
if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
    print("⚠️ PROMETHEUS_MULTIPROC_DIR not set — multiprocess metrics may break")

# ----------------------------------------
# LAZY METRIC FACTORY (CRITICAL FIX)
# ----------------------------------------

_jobs_pushed_total = None
_jobs_success_total = None
_jobs_failed_total = None
_job_execution_duration_seconds = None


def get_metrics(scope: str = "all"):
    global _jobs_pushed_total
    global _jobs_success_total
    global _jobs_failed_total
    global _job_execution_duration_seconds

    if _jobs_pushed_total is None:
        _jobs_pushed_total = Counter(
            "jobs_pushed_total",
            "Total number of network config push jobs enqueued",
        )

    if _jobs_success_total is None:
        _jobs_success_total = Counter(
            "jobs_success_total",
            "Total number of successful jobs",
        )

    if _jobs_failed_total is None:
        _jobs_failed_total = Counter(
            "jobs_failed_total",
            "Total number of failed jobs",
        )

    if _job_execution_duration_seconds is None:
        _job_execution_duration_seconds = Histogram(
            "job_execution_duration_seconds",
            "Time taken for a config job",
        )

    # ----------------------------------------
    # 🔒 ENFORCEMENT LAYER (CRITICAL FIX)
    # ----------------------------------------
    metrics = {
        "pushed": _jobs_pushed_total,
        "success": _jobs_success_total,
        "failed": _jobs_failed_total,
        "duration": _job_execution_duration_seconds,
    }

    if scope == "api":
        return {
            "pushed": metrics["pushed"],
        }

    elif scope == "worker":
        return {
            "success": metrics["success"],
            "failed": metrics["failed"],
            "duration": metrics["duration"],
        }

    return metrics 


# ----------------------------------------
# Metrics endpoint
# ----------------------------------------

def setup_metrics(app):

    @app.get("/metrics")
    def metrics():
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

        return Response(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST,
        )