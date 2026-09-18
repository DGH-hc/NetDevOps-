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

## Accepted Risk Exceptions

The following findings are explicitly risk-accepted and suppressed in CI
via `--ignore-vuln`. They are not silently ignored: each is named here,
with the reason for acceptance and a review date.

| Vulnerability ID | Package | Reason | Review by |
|---|---|---|---|
| PYSEC-2026-2858 | paramiko==4.0.0 | No fix version available upstream at time of review. Finding relates to SHA-1 algorithm support in rsakey.py. | Recheck each time paramiko or this policy doc is revisited |
| PYSEC-2026-1325 | ecdsa==0.19.2 | No fix version available upstream at time of review. Minerva timing-attack risk; requires local/high-precision timing access to exploit, and the app\'s JWT flow uses HS256 (symmetric), not ECDSA signing. | Recheck each time ecdsa or this policy doc is revisited |

Any new finding on either package (a different vulnerability ID) is
NOT covered by this exception and will correctly fail the CI gate.

## CI Requirement

The dependency security check must enforce the merge policy.

A vulnerability reported by `pip-audit` must cause the CI job to fail unless that specific vulnerability has been explicitly risk-accepted. 
