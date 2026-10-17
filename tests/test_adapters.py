"""
Tests for BlenderAdapter, AfterEffectsAdapter, UniversalGUIAdapter, and ScriptExecutor.
"""

import os
import pytest
from core.discovery import AppDiscoveryEngine
from core.executor import ScriptExecutor, ExecutionResult
from adapters.blender_adapter import BlenderAdapter, BlenderRenderOptions
from adapters.after_effects_adapter import AfterEffectsAdapter
from adapters.universal_gui_adapter import UniversalGUIAdapter
from templates.blender_templates import get_studio_scene_snippet


@pytest.fixture
def discovery():
    return AppDiscoveryEngine()


def test_script_executor_sync():
    res = ScriptExecutor.run_sync(["cmd.exe", "/c", "echo hello_executor"])
    assert res.success is True
    assert res.return_code == 0
    assert "hello_executor" in res.stdout


def test_script_executor_timeout():
    # Ping or powershell sleep with tight timeout
    res = ScriptExecutor.run_sync(
        ["powershell.exe", "-Command", "Start-Sleep -Seconds 5"],
        timeout=1.0
    )
    assert res.success is False
    assert res.return_code == -1
    assert "timed out" in (res.error_message or "").lower() or "timeout" in (res.stderr or "").lower()


def test_blender_adapter_status(discovery):
    adapter = BlenderAdapter(discovery)
    status = adapter.get_status()
    assert status["app_id"] == "blender"
    assert "capabilities" in status
    assert len(status["capabilities"]) > 0


def test_blender_script_execution_if_installed(discovery, tmp_path):
    adapter = BlenderAdapter(discovery)
    if not adapter.is_available:
        pytest.skip("Blender not installed on host")

    test_blend = str(tmp_path / "test_out.blend")
    code = """
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0)
"""
    res = adapter.run_python(code, save_blend_as=test_blend)
    assert res.success is True
    assert os.path.isfile(test_blend)
    assert os.path.getsize(test_blend) > 0


def test_blender_scene_info_if_installed(discovery, tmp_path):
    adapter = BlenderAdapter(discovery)
    if not adapter.is_available:
        pytest.skip("Blender not installed on host")

    info = adapter.get_scene_info()
    assert isinstance(info, dict)
    assert "scene_name" in info or "raw_output" in info


def test_after_effects_adapter_not_crashing_when_missing(discovery):
    ae = AfterEffectsAdapter(discovery)
    caps = ae.get_capabilities()
    assert isinstance(caps, list)
    if not ae.is_available:
        res = ae.run_extendscript("alert('test');")
        assert res.success is False
        assert "not installed" in (res.error_message or "").lower()


def test_universal_gui_list_apps():
    gui = UniversalGUIAdapter()
    apps = gui.list_running_apps()
    assert isinstance(apps, list)
    # On an active Windows session there are always processes running
    assert len(apps) > 0


def test_universal_gui_screenshot(tmp_path):
    gui = UniversalGUIAdapter()
    snap_path = str(tmp_path / "test_screenshot.png")
    res = gui.take_screenshot(snap_path)
    assert isinstance(res, ExecutionResult)
    if res.success:
        assert os.path.isfile(snap_path)
        assert os.path.getsize(snap_path) > 0
    else:
        # Graceful handling when running in headless or non-interactive terminal session
        assert "screenshot capture failed" in (res.error_message or "").lower()


def test_blender_studio_scene_template():
    snippet = get_studio_scene_snippet(object_type="TORUS", color=(1.0, 0.0, 0.0, 1.0))
    assert "bpy.ops.mesh.primitive_torus_add" in snippet
    assert "OmniMaterial" in snippet
    assert "Principled BSDF" in snippet
