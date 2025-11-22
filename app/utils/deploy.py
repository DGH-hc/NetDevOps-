# app/utils/deploy.py
import os
import traceback
from datetime import datetime
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
from typing import List, Tuple

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def snapshot_filename(device_id: int) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"device_{device_id}_snapshot_{ts}.cfg"

def save_snapshot_to_fs(device_id: int, text: str) -> str:
    fname = snapshot_filename(device_id)
    path = os.path.abspath(os.path.join(SNAPSHOT_DIR, fname))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path

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

def fetch_running_config(device) -> Tuple[int, str]:
    """Return (exit_code, text). exit_code 0=ok, >0 error."""
    try:
        conn_args = build_conn_args(device)
        with ConnectHandler(**conn_args) as conn:
            # common command - may need to vary by platform
            command = "show running-config" if "cisco" in device.platform else "show configuration"
            text = conn.send_command(command, expect_string=None)
            return 0, text
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        return 2, f"netmiko error: {e}"
    except Exception as e:
        return 1, f"error: {e}\n{traceback.format_exc()}"

def apply_config(device, config_lines: List[str]) -> Tuple[int, str]:
    """Apply a set of config lines (send_config_set). Returns (exit_code, output)."""
    try:
        conn_args = build_conn_args(device)
        with ConnectHandler(**conn_args) as conn:
            output = conn.send_config_set(config_lines)
            return 0, output
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        return 2, f"netmiko error: {e}"
    except Exception as e:
        return 1, f"error: {e}\n{traceback.format_exc()}"

def verify_config(device, verify_commands: List[str]) -> Tuple[bool, str]:
    """
    Run verification commands. Return (ok_bool, combined_output).
    Verification commands depend on the job (e.g., show ip interface brief; show bgp summary).
    """
    outputs = []
    try:
        conn_args = build_conn_args(device)
        with ConnectHandler(**conn_args) as conn:
            for cmd in verify_commands:
                out = conn.send_command(cmd)
                outputs.append(f"$ {cmd}\n{out}\n")
        combined = "\n".join(outputs)
        # Simple heuristic: if any line contains "error" or "Invalid" -> fail
        lowered = combined.lower()
        if "error" in lowered or "invalid" in lowered or "% " in combined:
            return False, combined
        return True, combined
    except Exception as e:
        return False, f"verify error: {e}\n{traceback.format_exc()}"

def rollback_from_snapshot(device, snapshot_path: str) -> Tuple[int, str]:
    """Read file and push as config. Returns (exit_code, output)."""
    try:
        with open(snapshot_path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        # Use apply_config to push lines back
        return apply_config(device, lines)
    except Exception as e:
        return 1, f"rollback read error: {e}\n{traceback.format_exc()}"
