# app/utils/secrets.py
import os
import requests

# Keep this module free of top-level imports from core.config to avoid circular imports.
# Import core.config.settings only when we actually need it (lazy import).

def _get_vault_settings():
    # lazy import to avoid circular import
    from core.config import settings
    return settings

def get_secret(path: str, key: str | None = None) -> dict | str:
    """
    Fetch a secret from Vault (or return from env if Vault isn't configured).
    - path: vault path (e.g. "secret/data/myapp")
    - key: optional key inside the secret payload
    """
    settings = _get_vault_settings()
    # If Vault isn't configured, fallback to env var
    if not settings.VAULT_URL or not settings.VAULT_TOKEN:
        # fallback: try environment variables with path/key naming
        env_key = (key or path).upper().replace("/", "_").replace(".", "_")
        value = os.getenv(env_key)
        if value is None:
            raise RuntimeError("Vault not configured and env var %s not found" % env_key)
        return value

    # If Vault configured, call it (basic example)
    url = f"{settings.VAULT_URL.rstrip('/')}/v1/{path.lstrip('/')}"
    headers = {"X-Vault-Token": settings.VAULT_TOKEN}
    resp = requests.get(url, headers=headers, timeout=5)
    resp.raise_for_status()
    payload = resp.json()
    # Vault KV v2 stores under data.data
    secret_data = payload.get("data", {}).get("data", {}) or payload.get("data", {}) or {}
    if key:
        return secret_data.get(key)
    return secret_data
