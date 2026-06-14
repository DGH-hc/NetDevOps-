# Phase 3.5 Alert Validation

## PodNotReady

Test Pod:
notready-test

Expected:
Alert fires after pod remains unready >5m

Result:
PASS

Evidence:
01-podnotready-firing-email.png
02-podnotready-resolved-email.png

---

## PodCrashLooping

Test Pod:
crashloop-test

Expected:
Alert fires when restart rate > 0

Result:
PASS

Evidence:
03-podcrashlooping-firing-prometheus.png
04-crashloopbackoff-terminal-watch.png

---

## PodHighRestartRate

Test Pod:
crashloop-test

Expected:
Alert fires when restart count > 3 in 10m

Result:
PASS

Evidence:
05-podhighrestartrate-firing-email.png
06-podhighrestartrate-resolved-email.png
07-promql-restart-metric-validation.png
08-crashloop-current-status-terminal.png