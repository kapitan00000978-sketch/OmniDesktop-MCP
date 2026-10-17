"""
OmniDesktop-MCP Universal GUI & Windows Desktop Application Adapter.
Controls any Windows desktop application using win32gui, psutil, Pillow, and PyAutoGUI.
Allows listing running windows, launching programs, focusing windows, taking screenshots,
and sending keyboard/mouse interactions.
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

import psutil
from PIL import ImageGrab

from core.executor import ExecutionResult
from core.logger import get_logger

logger = get_logger("UniversalGUIAdapter")

try:
    import win32gui
    import win32con
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("pywin32 not loaded. Window manipulation may be limited.")

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    HAS_PYAUTOGUI = True
except Exception:
    HAS_PYAUTOGUI = False


class WindowInfo(BaseModel):
    """Information about an active desktop window."""
    hwnd: int
    title: str
    pid: int
    process_name: str
    is_visible: bool


class UniversalGUIAdapter:
    """Universal controller for Windows desktop applications."""

    def list_running_apps(self) -> List[Dict[str, Any]]:
        """Lists active desktop applications with visible user windows or running processes."""
        windows: List[Dict[str, Any]] = []

        if HAS_WIN32:
            try:
                def enum_cb(hwnd: int, extra: Any) -> bool:
                    try:
                        if not win32gui.IsWindowVisible(hwnd):
                            return True
                        title = win32gui.GetWindowText(hwnd).strip()
                        if not title:
                            return True
                        # Filter out common background utility windows
                        if title in ("Program Manager", "Settings", "Windows Input Experience"):
                            return True

                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            proc = psutil.Process(pid)
                            proc_name = proc.name()
                            mem_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
                        except Exception:
                            proc_name = "Unknown"
                            mem_mb = 0.0

                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "pid": pid,
                            "process_name": proc_name,
                            "memory_mb": mem_mb
                        })
                    except Exception:
                        pass
                    return True

                win32gui.EnumWindows(enum_cb, None)
            except Exception as ex:
                logger.debug("EnumWindows failed (possibly non-interactive desktop session): %s", ex)
                windows = []

        if windows:
            return windows

        # Fallback to psutil processes (works reliably across all environments)
        results: List[Dict[str, Any]] = []
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                pinfo = proc.info
                mem_rss = pinfo.get("memory_info").rss if pinfo.get("memory_info") else 0
                results.append({
                    "hwnd": 0,
                    "title": pinfo.get("name") or "Process",
                    "pid": pinfo.get("pid"),
                    "process_name": pinfo.get("name") or "Unknown",
                    "memory_mb": round(mem_rss / (1024 * 1024), 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return results[:50]

    def find_window_by_title(self, pattern: str) -> Optional[int]:
        """Finds the window handle (hwnd) matching a title pattern."""
        if not HAS_WIN32:
            return None

        pattern_lower = pattern.lower()
        found_hwnd: Optional[int] = None

        def enum_cb(hwnd: int, extra: Any) -> None:
            nonlocal found_hwnd
            if found_hwnd is not None:
                return
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if pattern_lower in title.lower():
                    found_hwnd = hwnd

        win32gui.EnumWindows(enum_cb, None)
        return found_hwnd

    def focus_window(self, title_pattern: str) -> bool:
        """Brings the matching window to the foreground."""
        if not HAS_WIN32:
            return False

        hwnd = self.find_window_by_title(title_pattern)
        if not hwnd:
            logger.warning("No window found matching pattern: %s", title_pattern)
            return False

        try:
            # If minimized, restore it
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            return True
        except Exception as ex:
            logger.error("Failed to focus window %s: %s", title_pattern, ex)
            return False

    def launch_app(self, app_path_or_cmd: str, args: Optional[List[str]] = None) -> ExecutionResult:
        """Launches a desktop application as an independent background process."""
        cmd = [app_path_or_cmd]
        if args:
            cmd.extend(args)

        try:
            proc = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
                close_fds=True
            )
            return ExecutionResult(
                success=True,
                return_code=0,
                stdout=f"Launched '{app_path_or_cmd}' with PID {proc.pid}",
                stderr=""
            )
        except Exception as ex:
            logger.exception("Failed to launch %s: %s", app_path_or_cmd, ex)
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message=f"Failed to launch: {ex}"
            )

    def take_screenshot(
        self,
        output_path: str,
        window_title_pattern: Optional[str] = None
    ) -> ExecutionResult:
        """
        Takes a screenshot of the entire desktop or a specific active window.
        Saves the image as PNG.
        """
        abs_output = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)

        bbox = None
        if window_title_pattern and HAS_WIN32:
            hwnd = self.find_window_by_title(window_title_pattern)
            if hwnd:
                self.focus_window(window_title_pattern)
                rect = win32gui.GetWindowRect(hwnd)
                # Ensure width/height are positive
                if rect[2] > rect[0] and rect[3] > rect[1]:
                    bbox = rect

        try:
            img = ImageGrab.grab(bbox=bbox)
            img.save(abs_output, format="PNG")
            return ExecutionResult(
                success=True,
                return_code=0,
                stdout=f"Screenshot saved to {abs_output}",
                output_files=[abs_output]
            )
        except Exception as ex:
            logger.exception("Failed to take screenshot: %s", ex)
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message=f"Screenshot capture failed: {ex}"
            )

    def send_keys(self, keys: str, window_title_pattern: Optional[str] = None) -> ExecutionResult:
        """
        Sends keyboard keys/shortcuts to the active window or a targeted window.
        Supports hotkeys (e.g. 'ctrl+s', 'enter', 'alt+f4') or raw text.
        """
        if not HAS_PYAUTOGUI:
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message="pyautogui is not available on this system."
            )

        if window_title_pattern:
            if not self.focus_window(window_title_pattern):
                return ExecutionResult(
                    success=False,
                    return_code=-1,
                    error_message=f"Could not focus target window matching '{window_title_pattern}'"
                )

        time.sleep(0.2)

        try:
            if "+" in keys:
                # Shortcut combination, e.g. "ctrl+s"
                parts = [k.strip().lower() for k in keys.split("+")]
                pyautogui.hotkey(*parts)
            elif keys.lower() in pyautogui.KEY_NAMES:
                pyautogui.press(keys.lower())
            else:
                pyautogui.write(keys, interval=0.02)

            return ExecutionResult(
                success=True,
                return_code=0,
                stdout=f"Successfully sent keys: '{keys}'"
            )
        except Exception as ex:
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message=f"Failed to send keys: {ex}"
            )

    def click_mouse(
        self,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1
    ) -> ExecutionResult:
        """Clicks the mouse at specified desktop coordinates."""
        if not HAS_PYAUTOGUI:
            return ExecutionResult(success=False, return_code=-1, error_message="pyautogui is not available.")

        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return ExecutionResult(
                success=True,
                return_code=0,
                stdout=f"Clicked mouse at ({x}, {y}) button={button} clicks={clicks}"
            )
        except Exception as ex:
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message=f"Mouse click failed: {ex}"
            )
