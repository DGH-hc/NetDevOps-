#!/usr/bin/env python3

import requests

# --------------------------------------------------------
# Prometheus Configuration
# --------------------------------------------------------

PROMETHEUS_URL = "http://localhost:9090"

# --------------------------------------------------------
# Query Prometheus
# --------------------------------------------------------

def query_prometheus(query):

    try:

        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        print(f"[WARNING] Prometheus unavailable: {e}")

        return {
            "status": "error",
            "data": {
                "result": []
            }
        }

# --------------------------------------------------------
# Convenience Query Functions
# --------------------------------------------------------

def get_up_metrics():
    return query_prometheus("up")


def get_cpu_metrics():
    return query_prometheus(
        '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])))'
    )


def get_memory_available():
    return query_prometheus("node_memory_MemAvailable_bytes")


def get_memory_total():
    return query_prometheus("node_memory_MemTotal_bytes") 

# --------------------------------------------------------
# Test
# --------------------------------------------------------

if __name__ == "__main__":

    print("Testing Prometheus Client...\n")

    print("UP Metrics")
    print(get_up_metrics())

    print("\nCPU Metrics")
    print(get_cpu_metrics())

    print("\nMemory Available")
    print(get_memory_available())

    print("\nMemory Total")
    print(get_memory_total())
