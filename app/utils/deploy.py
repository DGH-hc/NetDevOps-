# app/utils/deploy.py

import os
import logging
import traceback
from datetime import datetime
from typing import List, Tuple

from netmiko import (
    ConnectHandler,
    NetMikoTimeoutException,
    NetMikoAuthenticationException,
)

# ============================
# Logging
# ============================
logger = logging.getLogger("netdevops.deploy")

# ============================
# Snapshot Config
# ============================
SNAPSHOT_DIR = "/tmp/snapshots"
MAX_SNAPSHOT_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ============================
# Snapshot Helpers
# ============================
def snapshot_filename(device_id: int) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"device_{device_id}_snapshot_{ts}.cfg"


def save_snapshot_to_fs(device_id: int, text: str) -> str:
    try:
        size = len(text.encode("utf-8"))
        if size > MAX_SNAPSHOT_SIZE:
            raise ValueError(f"Snapshot too large: {size} bytes")

        fname = snapshot_filename(device_id)
        path = os.path.abspath(os.path.join(SNAPSHOT_DIR, fname))

        # Atomic write
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(text)

        os.replace(tmp_path, path)

        logger.info(f"Snapshot saved: {path}")
        return path

    except Exception as e:
        logger.error(f"Snapshot save failed: {e}")
        raise


# ============================
# Connection Builder
# ============================
def build_conn_args(device) -> dict:
    args = {
        "host": device.ip,
        "username": device.username,
        "password": device.password,
        "port": device.port or 22,
        "device_type": device.platform,
        "timeout": 60,
    }

    if getattr(device, "private_key_path", None):
        args["use_keys"] = True
        args["key_file"] = device.private_key_path

    return args


# ============================
# Fetch Config
# ============================
def fetch_running_config(device) -> Tuple[int, str]:
    try:
        conn_args = build_conn_args(device)

        with ConnectHandler(**conn_args) as conn:
            command = (
                "show running-config"
                if "cisco" in device.platform.lower()
                else "show configuration"
            )

            text = conn.send_command(command)
            logger.info(f"Fetched config for device {device.id}")

            return 0, text

    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        logger.warning(f"Netmiko error: {e}")
        return 2, str(e)

    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return 1, traceback.format_exc()


# ============================
# Apply Config
# ============================
def apply_config(device, config_lines: List[str]) -> Tuple[int, str]:
    try:
        conn_args = build_conn_args(device)

        with ConnectHandler(**conn_args) as conn:
            output = conn.send_config_set(config_lines)

        logger.info(f"Config applied to device {device.id}")
        return 0, output

    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        logger.warning(f"Netmiko error: {e}")
        return 2, str(e)

    except Exception as e:
        logger.error(f"Apply config failed: {e}")
        return 1, traceback.format_exc()


# ============================
# Verify Config
# ============================
def verify_config(device, verify_commands: List[str]) -> Tuple[bool, str]:
    outputs = []

    try:
        conn_args = build_conn_args(device)

        with ConnectHandler(**conn_args) as conn:
            for cmd in verify_commands:
                out = conn.send_command(cmd)
                outputs.append(f"$ {cmd}\n{out}\n")

        combined = "\n".join(outputs)

        lowered = combined.lower()
        if "error" in lowered or "invalid" in lowered or "% " in combined:
            logger.warning(f"Verification failed for device {device.id}")
            return False, combined

        logger.info(f"Verification passed for device {device.id}")
        return True, combined

    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False, traceback.format_exc()


# ============================
# Rollback
# ============================
def rollback_from_snapshot(device, snapshot_path: str) -> Tuple[int, str]:
    try:
        if not os.path.exists(snapshot_path):
            raise FileNotFoundError(snapshot_path)

        with open(snapshot_path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()

        logger.warning(f"Rollback triggered for device {device.id}")

        return apply_config(device, lines)

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return 1, traceback.format_exc()