# Secret Detection Policy

## Tool
gitleaks v8.30.1, run against full git history (`--log-opts="--all"`).

## Baseline (established locally, [today's date])
- 56 commits scanned, 0 leaks found by gitleaks default ruleset.
- Manual cross-check grep performed for secret-shaped variable assignments
  (`(secret|password|token|api_key|private_key) = "..."`) across repo code
  (excluding .venv/third-party packages), to cover patterns gitleaks'
  entropy/regex rules might miss (per lesson learned in 4.1-F, where Bandit
  caught a hardcoded SECRET_KEY that a first-pass scan style check could miss).

## Findings reviewed

### charts/templates/statefulset-postgres.yaml:47
Not a finding. Vault templating syntax (`{{ .Data.data.POSTGRES_PASSWORD }}`)
— value is injected from Vault at deploy time, never stored in the manifest.
Confirmed correct pattern.

### app/seed_data.py:27 — password="admin123"
Reviewed, accepted, not a live risk. Script imports `Device`, `Job`, `User`
from `app.models`, but `app/models/__init__.py` exports nothing
(intentionally empty) — the script raises `ImportError` immediately and
cannot execute. Not invoked by CI, Docker, or any Makefile target (confirmed
via repo-wide grep). No path to a live database. Flagged as a follow-up
code-hygiene item (fix or remove the script) — out of scope for 4.1-H.

## Policy going forward
- Any new gitleaks finding on a PR → CI failure, merge blocked.
- False positives suppressed only via `.gitleaks.toml` allowlist, scoped to
  specific rule + path, with a documented reason and date. No blanket
  disables.
- Current `.gitleaks.toml`: none needed yet — baseline is clean.

## Negative test (performed)
- Attempt 1: committed AWS's public documentation example key
  (AKIAIOSFODNN7EXAMPLE) on a disposable branch/PR. Gate passed
  (no leaks found) — confirmed via local isolated test that gitleaks'
  default ruleset specifically excludes this well-known placeholder key.
  Not a gate failure; expected behavior.
- Attempt 2: committed a random, non-public fake credential
  (sk_test_... style string) on the same branch. Gate correctly failed
  (generic-api-key rule match), confirming secret-scan blocks real-looking
  secret patterns as intended. Verified live in GitHub Actions, PR #1,
  commit 2cf5ca7.
 
## Exit criteria for 4.1-H
- [x] Scanner selected (gitleaks) and run locally.
- [x] Baseline established, findings triaged.
- [x] `secret-scan` job wired into `ci.yml`.
- [x] Verified green in live GitHub Actions (clean code).
- [x] Negative test performed — gate correctly blocks a real secret pattern.