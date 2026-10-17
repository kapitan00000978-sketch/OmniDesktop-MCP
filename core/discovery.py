"""
OmniDesktop-MCP App Discovery Engine.
Scans Windows system registry, standard Program Files directories, and PATH
to detect installed desktop creative and productivity software.
"""

from __future__ import annotations

import glob
import os
import shutil
import winreg
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.logger import get_logger

logger = get_logger("DiscoveryEngine")


class AppInfo(BaseModel):
    """Represents an application detected on the host system."""
    app_id: str = Field(description="Normalized unique identifier (e.g., 'blender', 'after_effects')")
    name: str = Field(description="Human-readable application name")
    is_installed: bool = Field(default=False, description="Whether the app was located on disk")
    exe_path: Optional[str] = Field(default=None, description="Absolute path to main executable")
    version: Optional[str] = Field(default=None, description="Detected version string")
    extra_tools: Dict[str, str] = Field(default_factory=dict, description="Related tools (e.g. aerender.exe)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional detected attributes")


class AppDiscoveryEngine:
    """Discovers and caches installed desktop application paths."""

    def __init__(self) -> None:
        self._cache: Dict[str, AppInfo] = {}

    def discover_all(self, refresh: bool = False) -> Dict[str, AppInfo]:
        """Discovers all supported key applications and returns their AppInfo records."""
        if self._cache and not refresh:
            return self._cache

        apps: Dict[str, AppInfo] = {}
        apps["blender"] = self._detect_blender()
        apps["after_effects"] = self._detect_after_effects()
        apps["photoshop"] = self._detect_photoshop()
        apps["premiere"] = self._detect_premiere()
        apps["obs"] = self._detect_obs()

        self._cache = apps
        logger.info("Discovery completed: %d apps registered (%d available)",
                    len(apps), sum(1 for a in apps.values() if a.is_installed))
        return apps

    def get_app(self, app_id: str) -> Optional[AppInfo]:
        """Retrieves AppInfo for a specific app ID, discovering if necessary."""
        if not self._cache:
            self.discover_all()
        return self._cache.get(app_id.lower())

    def _check_exe_exists(self, path: Optional[str]) -> bool:
        return bool(path and os.path.isfile(path) and os.access(path, os.X_OK))

    def _find_in_path(self, exe_name: str) -> Optional[str]:
        found = shutil.which(exe_name)
        return os.path.abspath(found) if found else None

    def _read_registry_app_path(self, exe_name: str) -> Optional[str]:
        """Queries HKLM/HKCU App Paths registry for an executable."""
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                sub_key = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe_name}"
                with winreg.OpenKey(root, sub_key) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    if self._check_exe_exists(val):
                        return os.path.abspath(val)
            except OSError:
                continue
        return None

    def _detect_blender(self) -> AppInfo:
        """Locates Blender executable and determines its version."""
        candidates: List[str] = []

        # 1. Check App Paths / PATH
        reg_path = self._read_registry_app_path("blender.exe")
        if reg_path:
            candidates.append(reg_path)
        path_blender = self._find_in_path("blender.exe")
        if path_blender:
            candidates.append(path_blender)

        # 2. Check standard Program Files
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        blender_globs = glob.glob(os.path.join(pf, "Blender Foundation", "Blender *", "blender.exe"))
        # Sort descending so newer versions come first
        blender_globs.sort(reverse=True)
        candidates.extend(blender_globs)

        # 3. Check AppData / Local
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            local_globs = glob.glob(os.path.join(local_app_data, "Programs", "Blender Foundation", "Blender *", "blender.exe"))
            candidates.extend(local_globs)

        for exe in candidates:
            if self._check_exe_exists(exe):
                # Try to extract version from parent folder name
                folder_name = os.path.basename(os.path.dirname(exe))
                version = folder_name.replace("Blender", "").strip() or "Installed"
                return AppInfo(
                    app_id="blender",
                    name="Blender 3D",
                    is_installed=True,
                    exe_path=os.path.abspath(exe),
                    version=version,
                    metadata={"supports_bpy_headless": True, "supports_cycles": True}
                )

        return AppInfo(
            app_id="blender",
            name="Blender 3D",
            is_installed=False,
            exe_path=None,
            version=None,
        )

    def _detect_after_effects(self) -> AppInfo:
        """Locates Adobe After Effects and aerender executables."""
        candidates: List[str] = []

        reg_path = self._read_registry_app_path("AfterFX.exe")
        if reg_path:
            candidates.append(reg_path)

        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        ae_globs = glob.glob(os.path.join(pf, "Adobe", "Adobe After Effects *", "Support Files", "AfterFX.exe"))
        ae_globs.sort(reverse=True)
        candidates.extend(ae_globs)

        for exe in candidates:
            if self._check_exe_exists(exe):
                support_dir = os.path.dirname(exe)
                aerender_path = os.path.join(support_dir, "aerender.exe")
                extra = {}
                if self._check_exe_exists(aerender_path):
                    extra["aerender"] = os.path.abspath(aerender_path)

                parent_dir = os.path.dirname(support_dir)
                version_str = os.path.basename(parent_dir).replace("Adobe After Effects", "").strip() or "Installed"

                return AppInfo(
                    app_id="after_effects",
                    name="Adobe After Effects",
                    is_installed=True,
                    exe_path=os.path.abspath(exe),
                    version=version_str,
                    extra_tools=extra,
                    metadata={"supports_extendscript": True, "has_aerender": bool(extra.get("aerender"))}
                )

        return AppInfo(
            app_id="after_effects",
            name="Adobe After Effects",
            is_installed=False,
            exe_path=None,
            version=None,
        )

    def _detect_photoshop(self) -> AppInfo:
        """Locates Adobe Photoshop executable."""
        candidates: List[str] = []
        reg_path = self._read_registry_app_path("Photoshop.exe")
        if reg_path:
            candidates.append(reg_path)

        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        ps_globs = glob.glob(os.path.join(pf, "Adobe", "Adobe Photoshop *", "Photoshop.exe"))
        ps_globs.sort(reverse=True)
        candidates.extend(ps_globs)

        for exe in candidates:
            if self._check_exe_exists(exe):
                folder = os.path.basename(os.path.dirname(exe))
                ver = folder.replace("Adobe Photoshop", "").strip() or "Installed"
                return AppInfo(
                    app_id="photoshop",
                    name="Adobe Photoshop",
                    is_installed=True,
                    exe_path=os.path.abspath(exe),
                    version=ver,
                    metadata={"supports_extendscript": True}
                )

        return AppInfo(app_id="photoshop", name="Adobe Photoshop", is_installed=False)

    def _detect_premiere(self) -> AppInfo:
        """Locates Adobe Premiere Pro executable."""
        candidates: List[str] = []
        reg_path = self._read_registry_app_path("Adobe Premiere Pro.exe")
        if reg_path:
            candidates.append(reg_path)

        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pr_globs = glob.glob(os.path.join(pf, "Adobe", "Adobe Premiere Pro *", "Adobe Premiere Pro.exe"))
        pr_globs.sort(reverse=True)
        candidates.extend(pr_globs)

        for exe in candidates:
            if self._check_exe_exists(exe):
                folder = os.path.basename(os.path.dirname(exe))
                ver = folder.replace("Adobe Premiere Pro", "").strip() or "Installed"
                return AppInfo(
                    app_id="premiere",
                    name="Adobe Premiere Pro",
                    is_installed=True,
                    exe_path=os.path.abspath(exe),
                    version=ver,
                )

        return AppInfo(app_id="premiere", name="Adobe Premiere Pro", is_installed=False)

    def _detect_obs(self) -> AppInfo:
        """Locates OBS Studio executable."""
        candidates: List[str] = []
        reg_path = self._read_registry_app_path("obs64.exe")
        if reg_path:
            candidates.append(reg_path)

        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        obs_path = os.path.join(pf, "obs-studio", "bin", "64bit", "obs64.exe")
        candidates.append(obs_path)

        for exe in candidates:
            if self._check_exe_exists(exe):
                return AppInfo(
                    app_id="obs",
                    name="OBS Studio",
                    is_installed=True,
                    exe_path=os.path.abspath(exe),
                    version="Installed",
                )

        return AppInfo(app_id="obs", name="OBS Studio", is_installed=False)

    def search_custom_app(self, name_pattern: str) -> List[Dict[str, str]]:
        """Queries Windows Installed Programs registry for any installed desktop software."""
        results: List[Dict[str, str]] = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        pattern_lower = name_pattern.lower()

        for root_key, sub_key in reg_paths:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    count, _, _ = winreg.QueryInfoKey(key)
                    for i in range(count):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                display_name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                                if pattern_lower in display_name.lower():
                                    install_loc, _ = winreg.QueryValueEx(app_key, "InstallLocation") if self._has_val(app_key, "InstallLocation") else ("", None)
                                    version, _ = winreg.QueryValueEx(app_key, "DisplayVersion") if self._has_val(app_key, "DisplayVersion") else ("", None)
                                    results.append({
                                        "name": display_name,
                                        "version": str(version),
                                        "install_location": str(install_loc)
                                    })
                        except (OSError, FileNotFoundError):
                            continue
            except OSError:
                continue

        return results

    @staticmethod
    def _has_val(key: winreg.HKEYType, value_name: str) -> bool:
        try:
            winreg.QueryValueEx(key, value_name)
            return True
        except OSError:
            return False
