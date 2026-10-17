"""
Base Adapter class for OmniDesktop-MCP application integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from core.discovery import AppDiscoveryEngine, AppInfo
from core.logger import get_logger

logger = get_logger("BaseAdapter")


class BaseAdapter(ABC):
    """Abstract base class for all application adapters."""

    def __init__(self, discovery: AppDiscoveryEngine) -> None:
        self.discovery = discovery
        self._app_info: AppInfo = self._resolve_app_info()

    @property
    @abstractmethod
    def app_id(self) -> str:
        """Normalized unique identifier for the application."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable application name."""
        pass

    def _resolve_app_info(self) -> AppInfo:
        info = self.discovery.get_app(self.app_id)
        if not info:
            return AppInfo(app_id=self.app_id, name=self.display_name, is_installed=False)
        return info

    def refresh(self) -> None:
        """Refreshes discovery state for this application."""
        self.discovery.discover_all(refresh=True)
        self._app_info = self._resolve_app_info()

    @property
    def is_available(self) -> bool:
        """Returns True if the underlying application executable is detected."""
        return self._app_info.is_installed and bool(self._app_info.exe_path)

    @property
    def exe_path(self) -> str:
        """Returns path to executable, or raises RuntimeError if not installed."""
        if not self.is_available or not self._app_info.exe_path:
            raise RuntimeError(f"{self.display_name} is not installed or executable path not found on this system.")
        return self._app_info.exe_path

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Returns list of features supported by this adapter."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Returns status dictionary for diagnostics."""
        return {
            "app_id": self.app_id,
            "name": self.display_name,
            "installed": self.is_available,
            "version": self._app_info.version,
            "exe_path": self._app_info.exe_path,
            "capabilities": self.get_capabilities(),
        }
