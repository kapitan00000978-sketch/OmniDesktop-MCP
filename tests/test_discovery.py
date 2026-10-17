"""
Tests for AppDiscoveryEngine and SystemAdapter.
"""

import os
import pytest
from core.discovery import AppDiscoveryEngine, AppInfo
from adapters.system_adapter import SystemAdapter


def test_discovery_engine_initialization():
    engine = AppDiscoveryEngine()
    apps = engine.discover_all()
    assert isinstance(apps, dict)
    assert "blender" in apps
    assert "after_effects" in apps
    assert "photoshop" in apps
    assert "obs" in apps


def test_discovery_blender_detection():
    engine = AppDiscoveryEngine()
    blender = engine.get_app("blender")
    assert blender is not None
    assert blender.app_id == "blender"
    # On this machine, Blender 5.2 is installed
    if os.path.exists(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"):
        assert blender.is_installed is True
        assert blender.exe_path is not None
        assert os.path.isfile(blender.exe_path)


def test_system_specs():
    specs = SystemAdapter.get_system_specs()
    assert "os" in specs
    assert "cpu_count" in specs
    assert "ram_total_gb" in specs
    assert specs["ram_total_gb"] > 0
    assert specs["disk_c_free_gb"] > 0


def test_powershell_execution():
    res = SystemAdapter.run_powershell("Write-Output 'OMNI_TEST_SUCCESS'")
    assert res.success is True
    assert "OMNI_TEST_SUCCESS" in res.stdout
