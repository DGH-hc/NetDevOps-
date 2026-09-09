# CI Trust Model

## Purpose

This document defines the trust boundaries for the CI/CD system used by the
NetDevOps repository.

The central assumption is that code submitted through a pull request is
untrusted and must not automatically receive access to trusted resources.

## Trust Zones 

| Zone | Trust Level | Description |
|---|---|---|
| Developer workstation | Low | Source code is created and modified here. |
| Pull request code | Untrusted | Proposed repository changes must be treated as hostile or compromised. |
| GitHub Actions PR runner | Temporary execution | Executes untrusted PR-controlled code and must receive only the minimum required permissions. |
| GitHub repository / main | Trusted after validation | Changes become trusted only after required validation and merge controls succeed. |
| Artifact registry | Privileged | Stores build artifacts/images and must not be writable by untrusted PR validation jobs. |
| Staging | High | Environment used for controlled deployment/testing. |
| Production | Highest trust | Contains production systems and credentials and must not be directly accessible from untrusted PR validation. |

## Current CI Workflow

The existing `.github/workflows/ci.yml` runs for pull requests targeting
`main` or `master`.

It currently grants:

- `contents: read`

The workflow does not directly reference repository secrets.

The workflow executes repository-controlled code inside the CI environment,
including Docker Compose builds and pytest execution.

Therefore, the workflow must be treated as an untrusted execution boundary
even though it has read-only GitHub repository permissions.

## Privileged Workflows

The repository currently contains workflows with higher trust requirements:

- `.github/workflows/cd.yml` publishes images to GHCR and uses repository secrets.
- `.github/workflows/deploy.yml` uses production deployment SSH credentials.
- `.github/workflows/ghcr-test.yml` has `packages: write` permission.

These workflows must remain separated from untrusted pull-request validation.

## Trust Transition

The intended trust transition is:

Developer change
→ Pull request
→ Untrusted CI validation
→ Required checks pass
→ Pull request review/approval
→ Merge to `main`
→ Trusted post-merge workflows

A pull request must not receive production credentials merely because the
pull request originated inside this repository.

## Threat Assumptions

The CI security model assumes that:

- A contributor may accidentally commit a secret.
- A contributor may intentionally submit malicious code.
- A pull request may modify GitHub Actions workflow files.
- A dependency may contain a known vulnerability or become compromised.
- Kubernetes or infrastructure changes may introduce excessive privilege.
- A CI workflow may be abused if excessive permissions are granted.
- Production credentials must not be exposed to pull-request validation.

## Required Controls

The following controls are implemented or will be implemented in Phase 4.1:

| Threat | Required control |
|---|---|
| Unsafe code | Python SAST |
| Failed tests | Unit-test gate |
| Poor code quality | Lint/code-quality gate |
| Vulnerable dependency | Dependency security scan |
| Committed secret | Dedicated secret scanner |
| Dangerous Kubernetes/IaC change | Pre-validation gate |
| Excessive CI permissions | GitHub Actions permission hardening |
| Bypass of failed validation | Required status checks and branch protection |
| Production credential exposure | Separation of PR validation from privileged workflows |

## Trust Boundary Rule

No pull request is considered trusted merely because it originates from the
repository.

Trust is increased only after the required validation, review, and branch
protection controls have succeeded.