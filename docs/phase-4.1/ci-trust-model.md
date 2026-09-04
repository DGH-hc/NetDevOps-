# Phase 4.1-B — CI Trust Model

| Workflow | Trigger | Trust Class | Privileged? | Reason |
|---|---|---|---|---|
| ci.yml | push / pull_request | Untrusted → Trusted CI | No | Validation and testing only; no publishing or deployment |
| cd.yml | push to main | Privileged | Yes | Builds and publishes application/worker images to GHCR using credentials |
| deploy.yml | push to main / manual | Privileged | Yes | Deploys to the server using SSH credentials and Docker Compose |
| ghcr-test.yml | manual | Privileged | Yes | Manually publishes a test image to GHCR using GitHub package write permission | 

## Trust Boundaries

### Boundary 1 — Untrusted Code
Pull requests may contain untrusted code.
CI may execute this code for validation, but it must not receive privileged credentials or perform privileged publishing/deployment actions.

### Boundary 2 — Trusted Main 
Code becomes trusted only after it is merged into `main`.
Workflows triggered from `main` may perform trusted project operations.

### Boundary 3 — Privileged Operations
Image publishing and deployment are privileged operations.
They must only be reachable through explicitly authorized workflows and credentials.

### Trust Flow

Untrusted PR
    ↓
Validation CI
    ↓
Merge to main
    ↓
Trusted main
    ↓
Privileged workflows
    ↓
Publish / Deploy

## PR-to-Privileged Path Analysis

CI (`ci.yml`) executes on pull requests but does not reference privileged secrets or perform image publishing.

CD (`cd.yml`) executes on pushes to `main` and uses GHCR credentials to publish images.

No direct pull-request-to-privileged-credential path was identified.

However, `main` currently has no branch protection or repository ruleset. Therefore, the transition from untrusted code to trusted `main` is not currently enforced by a repository-level protection mechanism.

### Finding

The trust model is defined, but the trust boundary at `main` is not yet enforced. 

## Privileged Workflow Authorization Model

Privileged workflows are authorized only from trusted execution paths.

- `cd.yml` may publish images only when triggered by a push to `main`.
- `deploy.yml` may perform deployment only when triggered by `main` or an explicitly authorized manual execution.
- `ghcr-test.yml` is manually triggered and may publish only its designated test image.
- Pull-request workflows must not receive privileged publishing or deployment credentials.
- Privileged credentials must not be exposed to PR validation jobs.

### Authorization Boundary

PR validation → no privileged credentials

Merged `main` → authorized privileged workflows 

Privileged workflow → publish/deploy operation 

## CI Trust Model Decision

The repository uses three trust levels:

1. **Untrusted** — pull-request-controlled code. It is permitted to execute validation CI but must not receive privileged credentials.
2. **Trusted** — code merged into `main`. This is the boundary at which code may enter privileged workflows.
3. **Privileged** — workflows that publish images or perform deployments.

The current workflows follow this trust model:

- `ci.yml` → validation
- `cd.yml` → privileged image publishing
- `deploy.yml` → privileged deployment
- `ghcr-test.yml` → privileged test-image publishing

The trust boundary is logically defined, and no direct PR-to-privileged-secret path was identified.

However, the `main` branch currently has no branch protection or repository ruleset. Therefore, the transition into the trusted state is **defined but not enforced**.

Branch protection enforcement is a separate requirement and is addressed later in Phase 4.1.  