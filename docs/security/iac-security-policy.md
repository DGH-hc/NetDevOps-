# IaC / Kubernetes Security Policy

## Scope
Phase 4.1-I performs cheap pre-merge checks only (fmt/validate/lint/template
+ obvious dangerous-flag detection). Deep policy enforcement (OPA/Conftest,
CIS benchmarking) is deferred to Phase 4.4.

## Findings reviewed

### charts/templates/statefulset-postgres.yaml:62 — runAsUser: 0
Accepted risk, not fixed in 4.1-I. Root cause: stock `postgres:16` image's
entrypoint requires root to chown the mounted data volume before dropping
to the `postgres` user internally via gosu — this is the image's standard
documented behavior, not a misconfiguration introduced in this repo.
However, running the container itself as root (rather than isolating the
chown step) is not best practice.
Planned fix (tracked, not yet scheduled): move volume chown into a
dedicated initContainer running as root; change main container to
`runAsUser: 999` (non-root `postgres` user). Requires testing against
live StatefulSet volume before merge — deferred to a follow-up
task / Phase 4.4.

## Dangerous-flag CI gate
`ci.yml`'s `iac-validate` job scans rendered manifests for: privileged,
allowPrivilegeEscalation, hostNetwork, hostPID, and hostPath. `runAsUser: 0`
is deliberately NOT included in this blocking pattern yet, because the one
known instance above (Postgres) would fail the gate on a finding already
reviewed and accepted. This is a conscious scoping decision, not an
oversight. If `runAsUser: 0` appears elsewhere in the chart in the future,
it will currently pass CI silently — this doc is the tracking mechanism
until the gate is tightened (see Phase 4.4 or a dedicated follow-up).

## Terraform — not yet present in this repo
No `.tf` files exist in this repository as of 4.1-I (confirmed via local
`find` scan). Terraform is planned for a future phase per the AegisAI Omega
manual — specifically an S3 Object Lock (WORM) audit-log bucket defined in
`terraform/logging.tf`. The `iac-validate` CI job currently covers Helm
only (`helm lint` / `helm template`).

**Action required when `terraform/` is first added to this repo:** revisit
`iac-validate` and add `terraform fmt -check` and `terraform validate`
steps. Do not assume the existing job auto-covers Terraform once it
appears — it will not.
