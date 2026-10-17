"""
OmniDesktop-MCP Process & Script Execution Engine.
Executes CLI tools, headless scripts (Blender, After Effects ExtendScript),
and commands safely with timeouts, stdout/stderr capture, and temp file management.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import time
from typing import List, Optional
from pydantic import BaseModel, Field

from core.logger import get_logger

logger = get_logger("Executor")


class ExecutionResult(BaseModel):
    """Result of an external tool or script execution."""
    success: bool = Field(description="True if process exited with code 0")
    return_code: int = Field(description="Process exit code")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    duration_sec: float = Field(default=0.0, description="Execution duration in seconds")
    output_files: List[str] = Field(default_factory=list, description="Generated file paths")
    error_message: Optional[str] = Field(default=None, description="Formatted summary if failed")


class ScriptExecutor:
    """Executes commands and manages temporary script lifecycles."""

    @staticmethod
    def run_sync(
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: float = 120.0,
        env: Optional[dict] = None
    ) -> ExecutionResult:
        """Executes a command synchronously with timeout enforcement."""
        start_time = time.time()
        logger.debug("Executing sync: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env or os.environ.copy(),
                shell=False
            )
            duration = round(time.time() - start_time, 2)
            success = proc.returncode == 0
            err_msg = None if success else f"Command failed with exit code {proc.returncode}: {proc.stderr[:400]}"
            return ExecutionResult(
                success=success,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_sec=duration,
                error_message=err_msg
            )
        except subprocess.TimeoutExpired as e:
            duration = round(time.time() - start_time, 2)
            logger.error("Command timed out after %.1fs: %s", timeout, cmd)
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
                stderr=f"Timeout expired after {timeout} seconds",
                duration_sec=duration,
                error_message=f"Process timed out after {timeout}s"
            )
        except Exception as ex:
            duration = round(time.time() - start_time, 2)
            logger.exception("Execution error: %s", ex)
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(ex),
                duration_sec=duration,
                error_message=f"Failed to launch command: {ex}"
            )

    @staticmethod
    async def run_async(
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: float = 120.0,
        env: Optional[dict] = None
    ) -> ExecutionResult:
        """Executes a command asynchronously with timeout."""
        start_time = time.time()
        logger.debug("Executing async: %s", " ".join(cmd))
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env or os.environ.copy()
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                duration = round(time.time() - start_time, 2)
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                ret_code = proc.returncode if proc.returncode is not None else -1
                success = ret_code == 0
                err_msg = None if success else f"Exit code {ret_code}: {stderr[:400]}"
                return ExecutionResult(
                    success=success,
                    return_code=ret_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_sec=duration,
                    error_message=err_msg
                )
            except asyncio.TimeoutError:
                duration = round(time.time() - start_time, 2)
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return ExecutionResult(
                    success=False,
                    return_code=-1,
                    stdout="",
                    stderr=f"Async timeout expired after {timeout}s",
                    duration_sec=duration,
                    error_message=f"Process timed out after {timeout}s"
                )

        except Exception as ex:
            duration = round(time.time() - start_time, 2)
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(ex),
                duration_sec=duration,
                error_message=f"Failed to launch async command: {ex}"
            )

    @staticmethod
    def create_temp_script(content: str, suffix: str = ".py", prefix: str = "omni_") -> str:
        """Writes content into a temporary file and returns its absolute path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, prefix=prefix, delete=False, encoding="utf-8") as f:
            f.write(content)
            return os.path.abspath(f.name)

    @staticmethod
    def cleanup_file(path: str) -> None:
        """Safely removes a temporary file."""
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as ex:
            logger.warning("Could not delete temp file %s: %s", path, ex)
