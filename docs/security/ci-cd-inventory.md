# CI/CD Security Inventory

## Purpose

This document records the repository surfaces that must be protected by the Phase 4.1 CI security foundation.

The purpose is to answer three questions for each major repository surface:

1. What could go wrong?
2. Which CI control detects the problem?
3. Should failure block the pull request?

This inventory is based on the repository as it exists now. It does not create future architecture or assume controls are already implemented.

---
 
## 1. Python Application 

**Repository surface:** `app/`

The repository contains the main Python application, including API, configuration, security, database, models, schemas, utilities, and worker components.

### What could go wrong?

* Unsafe Python operations
* Dangerous subprocess usage
* Hardcoded credentials or passwords
* Weak cryptographic practices
* Unsafe temporary-file handling
* Unsafe deserialization
* General code-quality problems

### CI control

* **Ruff** for code quality and linting
* **Bandit** for Python security analysis
* **Secret scanner** for accidentally committed secrets

### Should failure block the PR?

**Yes.**

Security and quality findings that meet the defined blocking policy must prevent the PR from becoming merge-eligible.

Ruff and Bandit are not currently enforced by the existing CI workflow. They are Phase 4.1 security gates to be added.

---

## 2. Application Tests

**Repository surface:** `tests/`

The repository contains unit, integration, validation, AegisAI, replay, schema, evidence, and failure-path tests.

### What could go wrong?

* Existing functionality could break
* Security-related behavior could regress
* Validation logic could stop working
* Previously working system behavior could be changed by a PR

### CI control

* **pytest**

The existing CI workflow already runs the test suite inside the CI application environment.

### Should failure block the PR?

**Yes.**

A failing test must cause the CI job to fail.

The existing workflow already behaves this way. Actual merge enforcement still depends on branch protection and required status checks, which are handled later in **4.1-J**.

---

## 3. Python Dependencies

**Repository surface:** `requirements.txt`

Dependencies are pinned to specific versions, which improves reproducibility but does not guarantee that the versions are free of known vulnerabilities.

### What could go wrong?

* A dependency may contain a known vulnerability
* A vulnerable transitive dependency may be introduced
* A dependency may become unsafe even though the application code itself appears correct

### CI control

* **pip-audit** or another single approved Python dependency vulnerability scanner

### Should failure block the PR?

**Yes, according to the defined severity policy.**

Initial policy:

* **Critical:** block
* **High:** block unless explicitly risk-accepted
* **Medium:** report and evaluate
* **Low:** informational

The exact policy may evolve, but it must remain explicit.

The dependency security gate is not currently present in the existing CI workflow.

---

## 4. Docker / Container Build

**Repository surface:** `Dockerfile`

The application is packaged into a Python container. The runtime container uses a non-root `appuser`.

### What could go wrong?

* Container build could fail
* Application dependencies could fail to install
* Unsafe container configuration could be introduced
* A PR could modify the container build in a dangerous way
* Supply-chain risk could enter through container dependencies or base images

### CI control

* Existing Docker build/integration execution
* Dependency security scanning
* Existing container configuration review as part of the CI inventory

Container image security scanning is not being added as a separate Phase 4.1 requirement unless required by the defined repository risks.

### Should failure block the PR?

**Build/test failure: Yes.**

The existing CI build must fail when the application container cannot be built or tested.

Additional container security controls are outside the current Phase 4.1 scope unless explicitly required by later evidence.

---

## 5. Docker Compose CI Environment

**Repository surface:** `docker-compose.ci.yml`

The repository uses Docker Compose to create a CI test environment containing the application, worker, PostgreSQL, Redis, and a mock device.

### What could go wrong?

* CI environment may fail to start
* Application integration may fail
* Test dependencies may become unavailable
* External container images may introduce supply-chain risk
* PR-controlled code is executed inside the CI environment

### CI control

* Docker Compose build
* Service startup checks
* Application health check
* pytest
* CI failure log collection

### Should failure block the PR?

**Yes.**

A failed CI environment or failed integration test must fail the CI job.

The existing workflow already performs these checks.

The external `mockdevice:latest` image is recorded as a supply-chain consideration, but this inventory does not redesign it.

---

## 6. Kubernetes Manifests

**Repository surface:** `k8s/`

The repository contains application, worker, PostgreSQL, Redis, storage, ingress, RBAC, monitoring, and network-related Kubernetes manifests.

### What could go wrong?

* Invalid Kubernetes manifests
* Excessive container privileges
* `privileged` containers
* `allowPrivilegeEscalation`
* `hostNetwork`
* `hostPID`
* Dangerous `hostPath` usage
* Incorrect resource or workload configuration
* Unsafe RBAC configuration

### CI control

Phase 4.1 provides basic pre-merge Kubernetes validation.

Obvious dangerous configurations should be detected where practical.

Deeper Kubernetes policy enforcement belongs to **Phase 4.4**.

### Should failure block the PR?

**Yes for defined blocking validation failures.**

The required Kubernetes validation is not yet fully enforced by the existing CI workflow.

Phase 4.1 must remain a cheap pre-merge validation layer rather than becoming the full Kubernetes governance system.

---

## 7. Helm Charts

**Repository surface:** `charts/`

The repository contains the main Helm chart, templates, values files, schema validation, and a legacy chart area.

### What could go wrong?

* Invalid Helm templates
* Invalid values
* Broken chart rendering
* Configuration that produces invalid Kubernetes resources
* Unsafe production configuration
* Hardcoded development secrets

### CI control

* `helm lint`
* Helm template/render validation
* Helm values schema validation where applicable

### Should failure block the PR?

**Yes.**

A broken Helm chart or failed required validation must block the PR.

These checks are not currently enforced by the existing CI workflow.

---

## 8. NetworkPolicy Manifests

**Repository surface:** `k8s/network/` and Helm NetworkPolicy templates

The repository contains default-deny and service-specific network policies.

### What could go wrong?

* Network isolation could accidentally be weakened
* Required traffic could be blocked
* Unauthorized communication paths could be introduced
* A PR could remove or weaken an existing security boundary

### CI control

Phase 4.1 performs basic Kubernetes/IaC validation.

Deeper policy correctness and centralized security policy enforcement belong to **Phase 4.4**.

### Should failure block the PR?

**Yes for defined validation failures.**

Phase 4.1 does not attempt to prove complete network-security correctness.

---

## 9. Vault Configuration

**Repository surface:** `infra/vault/`, `charts/vault/`, and related Vault configuration

The repository contains Vault deployment/configuration material.

### What could go wrong?

* Unsafe configuration could be introduced
* Authentication or access configuration could be weakened
* Sensitive values could accidentally be committed
* Vault-related Kubernetes configuration could become invalid

### CI control

* Secret detection
* Kubernetes/Helm validation where applicable
* Existing repository security review

### Should failure block the PR?

**Yes for blocking secret-detection or validation failures.**

Phase 4.1 does not redesign the Vault architecture. Existing Vault security controls from earlier phases remain outside this inventory's scope.

---

## 10. GitHub Actions Workflows

**Repository surface:** `.github/workflows/`

Current workflows include:

* `ci.yml`
* `cd.yml`
* `deploy.yml`
* `ghcr-test.yml`

### What could go wrong?

* A PR could modify CI behavior
* A workflow could receive excessive permissions
* A workflow could expose sensitive credentials
* A PR-controlled workflow could gain access to production secrets
* A privileged publishing or deployment workflow could be triggered incorrectly

### CI control

Phase 4.1 requires:

* Explicit minimal GitHub Actions permissions
* Separation between PR validation and privileged workflows
* No production credentials available to PR validation jobs
* Required checks before merge
* Review of workflow permission scopes

### Should failure block the PR?

**Yes where the workflow security policy is violated.**

Workflow permission hardening and repository-level enforcement are part of Phase 4.1.

The existing `ci.yml` already uses `contents: read`.

The existing `cd.yml` and `deploy.yml` are higher-trust workflows and require explicit review because they interact with image publishing and deployment credentials.

---

## 11. Repository Secrets and Sensitive Configuration

**Repository surface:** repository files, workflow secrets, configuration files, Helm values, and environment-related files

The repository contains secret-like configuration values, including development values in Helm configuration.

### What could go wrong?

* API keys could be committed
* Passwords could be committed
* Tokens could be committed
* Private keys could be committed
* Sensitive configuration could be exposed through source control

### CI control

* Dedicated secret scanner
* Controlled false-positive suppression/allow mechanism

`.gitignore` is not considered a security control for committed secrets.

### Should failure block the PR?

**Yes.**

Detected secrets must block the PR unless they are explicitly and safely classified as an approved false positive.

Real secrets must never be used for negative testing.

---

## 12. Terraform

**Repository surface:** None identified.

### What could go wrong?

Terraform-specific risks are not currently applicable because no Terraform configuration was identified in the repository.

### CI control

**None required for the current repository.**

### Should failure block the PR?

**Not applicable.**

Terraform validation must not be added merely to satisfy a generic security checklist.

---

# Control Summary

| Repository Surface  | Main Risk                                    | CI Control                          | Blocking?                |
| ------------------- | -------------------------------------------- | ----------------------------------- | ------------------------ |
| Python application  | Unsafe code / quality issues                 | Ruff, Bandit, secret scanner        | Yes                      |
| Tests               | Functional/security regressions              | pytest                              | Yes                      |
| Dependencies        | Known vulnerabilities                        | pip-audit / approved scanner        | Yes by policy            |
| Dockerfile          | Broken/unsafe container build                | Docker build + existing CI          | Yes for build failure    |
| Docker Compose CI   | Integration failure / CI execution risk      | Compose + health checks + pytest    | Yes                      |
| Kubernetes          | Invalid or obviously dangerous configuration | Basic K8s validation                | Yes                      |
| Helm                | Broken templates/configuration               | helm lint + template validation     | Yes                      |
| NetworkPolicy       | Weakened network isolation                   | Basic K8s validation                | Yes for defined failures |
| Vault configuration | Unsafe config / leaked secrets               | Secret scan + applicable validation | Yes                      |
| GitHub Actions      | Excessive permissions / credential exposure  | Permission review + required checks | Yes                      |
| Repository secrets  | Secret leakage                               | Dedicated secret scanner            | Yes                      |
| Terraform           | Not present                                  | None                                | N/A                      |

---

# Current-State Conclusion

The repository contains multiple security-sensitive surfaces that must be included in the Phase 4.1 CI boundary.

The existing CI already provides meaningful test and integration coverage, but it is **not yet a complete security gate**.

The major missing Phase 4.1 controls are:

* Ruff enforcement
* Bandit enforcement
* Dependency vulnerability scanning
* Dedicated secret detection
* Basic Kubernetes validation
* Helm validation
* Explicit workflow permission hardening where required
* Required branch checks
* Security evidence generation
* Negative testing proving the gates actually block unsafe changes

This inventory therefore establishes the scope for the remaining Phase 4.1 work without expanding the project beyond the defined plan.

**Boundary:** Phase 4.1 covers source change → PR validation → security decision → merge eligibility. It does not build or deploy the production artifact.
