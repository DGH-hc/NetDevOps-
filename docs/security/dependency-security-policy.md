# Dependency Security Policy

## Purpose

Define how known third-party dependency vulnerabilities are handled
during CI and Pull Request validation.

## Scanner

The project uses `pip-audit` as the dependency security scanner.

The scanner checks Python dependencies declared in `requirements.txt`
against known vulnerability databases.

## Merge Policy

| Finding | Policy |
|---|---|
| Known vulnerability reported by `pip-audit` | Block merge |
| Explicitly risk-accepted vulnerability | May proceed with documented risk acceptance |

A vulnerability must not be silently ignored.

Risk acceptance must identify the vulnerability, affected dependency,
reason for acceptance, and the responsible approval.  

## Current Baseline

The current dependency audit reports unresolved findings in:

- `paramiko==4.0.0`
- `ecdsa==0.19.2`

These findings currently have no fix version reported by `pip-audit`.

They must not be silently ignored. They are subject to the severity
policy above.

## CI Requirement

The dependency security check must enforce the merge policy.

A vulnerability reported by `pip-audit` must cause the CI job to fail unless that specific vulnerability has been explicitly risk-accepted. 
