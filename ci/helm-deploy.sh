#!/usr/bin/env bash
set -euo pipefail

RELEASE_NAME=netdevops
NAMESPACE=netdevops-staging
CHART_PATH=charts

echo "Deploying Helm release ${RELEASE_NAME} to namespace ${NAMESPACE}"

helm upgrade --install \
  ${RELEASE_NAME} \
  ${CHART_PATH} \
  --namespace ${NAMESPACE} \
  --create-namespace

echo "Helm deployment completed successfully"

echo "Running database migrations"

kubectl apply -f ci/k8s/migration-job.yaml

kubectl wait \
  --for=condition=complete \
  job/netdevops-migrate \
  -n ${NAMESPACE} \
  --timeout=300s

echo "Database migrations completed successfully"
