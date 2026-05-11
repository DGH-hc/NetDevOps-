# Known Limitations — Phase 3.4

## Database High Availability

### Current State

* Single PostgreSQL instance deployed
* No replication or failover mechanism

### Impact

* During database restart, application remains alive
* However, requests depending on DB may fail temporarily

### Risk Level

Medium (acceptable for development, not production)

---

## Why Not Fixed Yet

This phase focuses on resilience testing, not architecture redesign.

---

## Planned Solution

* PostgreSQL replication (Primary + Replica)
* Failover mechanism (Patroni / Operator)
* Connection proxy (PgBouncer)

---

## Target Phase

Phase 3.5 / Phase 4
