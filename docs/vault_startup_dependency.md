# Vault Startup Dependency Control

## Purpose

This document describes how the NetDevOps platform ensures that PostgreSQL workloads do not start until Vault is available and capable of providing secrets.

The system relies on Vault Agent injection and the `vault-agent-init` init container to enforce deterministic secret availability before database startup.

---

## Architecture

Pod startup sequence:

```
Pod Creation
     ↓
vault-agent-init container starts
     ↓
Vault authentication using Kubernetes service account
     ↓
Secret retrieval from Vault KV
     ↓
Template rendering to /vault/secrets/db
     ↓
Init container exits
     ↓
Postgres container starts
```

Vault Agent uses the Kubernetes authentication method:

```
auth/kubernetes/login
```

Authentication uses the service account token mounted at:

```
/var/run/secrets/kubernetes.io/serviceaccount/token
```

---

## Failure Scenario: Vault Sealed

Observed behavior during testing:

```
Vault Agent Init
     ↓
Vault sealed
     ↓
Authentication fails
     ↓
Agent retries with exponential backoff
     ↓
Pod remains in Init state
```

Example log evidence:

```
Error making API request
Code: 503
Vault is sealed
```

This behavior prevents the database from starting with missing credentials.

---

## Recovery Behavior

When Vault becomes unsealed:

```
Vault Agent authenticates
     ↓
Vault token issued
     ↓
Secret template rendered
     ↓
/vault/secrets/db created
     ↓
Init container exits
```

The PostgreSQL container then starts using the injected environment variables.

If the pod started while Vault was sealed, a pod restart may be required to rerun the initialization sequence.

Example recovery command:

```
kubectl delete pod netdevops-postgres-0 -n app
```

Kubernetes recreates the pod and the initialization process executes successfully.

---

## Security Impact

This design ensures:

* Secrets are never stored in Kubernetes Secrets
* Database credentials are delivered only at runtime
* Workloads cannot start without Vault
* Secret lifecycle is fully controlled by Vault

Attack surface reduction:

```
No static secrets
No environment variable persistence
No etcd secret storage
```

---

## Production Considerations

In production environments, Vault should be configured with auto-unseal using a cloud KMS provider.

Examples:

* AWS KMS
* GCP KMS
* Azure Key Vault

Auto-unseal eliminates the manual unseal dependency and allows pods to recover automatically during cluster restarts.

---

## Validation Evidence

The following artifacts demonstrate correct dependency behavior:

```
evidence/phase3.1_failures/vault_sealed_failure.log
docs/secret_rotation_proof.md
docs/restart_recovery_metrics.json
```

These artifacts confirm:

* Vault dependency enforcement
* Secret rendering
* Pod restart recovery
