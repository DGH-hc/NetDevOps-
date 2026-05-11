# Phase 3.1 – Secret Rotation Validation

## Objective
Validate runtime secret lifecycle without pod restart.

## Initial Secret State
POSTGRES_PASSWORD="securepassword"

## Rotation Action
Vault KV updated:
vault kv put secret/netdevops/db POSTGRES_PASSWORD=rotatedpassword123

Secret Version: 2

## Vault Agent Behavior
Agent log:
rendered "(dynamic)" => "/vault/secrets/db"

## Post-Rotation File State
POSTGRES_PASSWORD="rotatedpassword123"

## Pod Status
No restart occurred.
State remained: 2/2 Running

## Conclusion
Vault → Agent → Template → File pipeline successfully supports dynamic secret re-rendering without container restart.