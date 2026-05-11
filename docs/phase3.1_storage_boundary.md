# Phase 3.1 – Storage Boundary Documentation

## Context
Environment uses Kind (single-node) with hostPath-backed volumes.

## Observed Issue
fsGroup did not correctly propagate permissions on hostPath volumes.
PostgreSQL container encountered permission errors when running as non-root.

## Resolution Strategy
Pod-level securityContext removed.
Container-level securityContext applied:
runAsUser: 0

PVC deleted and recreated.

## Risk Acknowledgement
Running container as root increases attack surface.
Acceptable in controlled local lab environment only.

## Production Consideration
In production:
- Use CSI-backed storage (e.g., EBS, Ceph, GKE PD)
- fsGroup properly enforced
- Container runs as non-root
- PodSecurity policies applied

## Engineering Judgment
Root usage limited strictly to lab constraints.
Documented deviation from production security baseline.