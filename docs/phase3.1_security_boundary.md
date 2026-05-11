# Phase 3.1 – Security Boundary Model

## Secret Flow
Vault → Vault Agent → Rendered Template → /vault/secrets/db → PostgreSQL

## Secret Storage
- No Kubernetes Secret objects used
- No secrets stored in etcd
- No secrets in Helm values
- No plaintext in manifests

## Attack Surface

If Pod Compromised:
- Secret file readable within container
- Vault token scoped to role only
- No wildcard policies
- Namespace isolation enforced

If Vault Compromised:
- All secrets exposed (trusted root system)

## Trust Assumptions
- Vault root credentials secured
- Kubernetes ServiceAccount token scoped
- No cluster-admin privilege granted to application

## Boundary Summary
Application depends on Vault for runtime secrets.
Kubernetes does not store or manage secret material.
Security boundary centered around Vault policy enforcement.