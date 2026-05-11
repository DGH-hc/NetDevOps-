# Reproducibility Guide — Phase 3.4

## Worker Failure Test

kubectl delete pod <worker-pod> -n app

---

## Database Failure Test

kubectl delete pod postgres-0 -n app

---

## Control Plane Failure Test

docker stop aegis-control-plane
docker start aegis-control-plane

---

## Expected Behavior

* Pods should recreate automatically
* No manual intervention required
* System should return to stable state
