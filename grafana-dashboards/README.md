# Grafana Dashboards

## Available Dashboards

### postgresql-observability-dashboard.json
PostgreSQL metrics and alerts:
- Active DB connections
- Transactions/sec
- Rollbacks/sec
- Deadlocks
- Database size

### infrastructure-dashboard.json
Kubernetes infrastructure metrics:
- Node CPU usage
- Node memory usage
- Disk usage
- Pod restart count
- Running pods per namespace

## Import Instructions

1. Open Grafana
2. Dashboards → Import
3. Upload JSON dashboard file
4. Select Prometheus datasource
5. Save dashboard