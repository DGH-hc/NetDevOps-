#!/usr/bin/env bash
set -euo pipefail

echo "🛑 Running DB backup BEFORE migrations"

NAMESPACE="netdevops-staging"
BACKUP_FILE="db-backup-$(date +%Y%m%d%H%M%S).sql"

kubectl run db-backup \
  -n "$NAMESPACE" \
  --rm -i \
  --image=postgres:16 \
  --restart=Never \
  --env="PGPASSWORD=$(kubectl get secret netdevops-db -n $NAMESPACE -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)" \
  -- bash -c "
    pg_dump \
      -h netdevops-postgres \
      -U $(kubectl get secret netdevops-db -n $NAMESPACE -o jsonpath='{.data.POSTGRES_USER}' | base64 -d) \
      $(kubectl get secret netdevops-db -n $NAMESPACE -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)
  " > "$BACKUP_FILE"

echo "✅ Database backup completed: $BACKUP_FILE"
