"""
OmniDesktop-MCP Core components.
"""

from core.logger import get_logger
from core.discovery import AppDiscoveryEngine, AppInfo
from core.executor import ScriptExecutor, ExecutionResult

__all__ = ["get_logger", "AppDiscoveryEngine", "AppInfo", "ScriptExecutor", "ExecutionResult"]
