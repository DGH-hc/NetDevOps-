# PostgreSQL Observability Stack

## Overview

This setup provides PostgreSQL observability using:

- PostgreSQL Exporter
- Prometheus
- Grafana
- Alertmanager

The stack monitors PostgreSQL health, availability, activity, and storage metrics inside Kubernetes.

---

# Components

| Component | Purpose |
|---|---|
| PostgreSQL Exporter | Exposes PostgreSQL metrics |
| Prometheus | Scrapes and stores metrics |
| Grafana | Visualization dashboards |
| Alertmanager | Alert routing and notifications |

---

# Kubernetes Namespace

Application namespace:

```bash
app