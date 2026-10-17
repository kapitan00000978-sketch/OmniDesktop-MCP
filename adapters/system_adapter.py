"""
OmniDesktop-MCP System & PowerShell Adapter.
Provides system diagnostics, disk/memory queries, and powershell automation.
"""

from __future__ import annotations

import platform
import shutil
from typing import Any, Dict
import psutil

from core.executor import ExecutionResult, ScriptExecutor
from core.logger import get_logger

logger = get_logger("SystemAdapter")


class SystemAdapter:
    """Manages system-level tasks and PowerShell command executions."""

    @staticmethod
    def get_system_specs() -> Dict[str, Any]:
        """Returns hardware and OS specifications."""
        mem = psutil.virtual_memory()
        disk = shutil.disk_usage("C:\\")

        return {
            "os": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "ram_available_gb": round(mem.available / (1024 ** 3), 2),
            "disk_c_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_c_free_gb": round(disk.free / (1024 ** 3), 2)
        }

    @staticmethod
    def run_powershell(command: str, timeout: float = 60.0) -> ExecutionResult:
        """Executes a PowerShell script or command."""
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command", command
        ]
        return ScriptExecutor.run_sync(cmd, timeout=timeout)
