# Phase 3.5 Error Budget

## Availability Error Budget

Availability SLO:

99.9%

Allowed Failure:

0.1%

Monthly Downtime Budget:

43.2 minutes

Calculation:

30 days × 24 hours × 60 minutes = 43,200 minutes

43,200 × 0.001 = 43.2 minutes

---

## API Error Budget

Target Error Rate:

< 1%

Allowed Failed Requests:

1 per 100 requests

Examples:

1,000 requests
→ 10 failures allowed

10,000 requests
→ 100 failures allowed

100,000 requests
→ 1,000 failures allowed

---

## Operational Use

If the platform exceeds the error budget:

- Investigate incident
- Pause risky deployments
- Review alert history
- Review reliability trends

---

Evidence:

- Prometheus metrics
- Grafana dashboards
- Alertmanager alerts
