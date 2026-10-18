"""
OmniDesktop-MCP Main Server.
A unified local Model Context Protocol (MCP) server connecting AI agents
to desktop software (Blender, After Effects, Photoshop, Windows GUI, PowerShell).
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

from core.discovery import AppDiscoveryEngine
from core.logger import get_logger
from adapters.blender_adapter import BlenderAdapter, BlenderRenderOptions
from adapters.after_effects_adapter import AfterEffectsAdapter, AERenderOptions
from adapters.universal_gui_adapter import UniversalGUIAdapter
from adapters.system_adapter import SystemAdapter
from templates.blender_templates import get_studio_scene_snippet

logger = get_logger("OmniDesktopServer")

# Initialize Server
mcp = MCPServer(
    name="OmniDesktop-MCP",
    description="Universal Desktop Creative & Productivity Automation Server for AI Agents"
)

# Initialize Core Services
discovery = AppDiscoveryEngine()
discovery.discover_all()

blender_adapter = BlenderAdapter(discovery)
ae_adapter = AfterEffectsAdapter(discovery)
gui_adapter = UniversalGUIAdapter()
sys_adapter = SystemAdapter()


# ==============================================================================
# APP DISCOVERY & SYSTEM TOOLS
# ==============================================================================

@mcp.tool()
def get_installed_apps() -> Dict[str, Any]:
    """
    Returns detection status and executable paths for all supported creative applications
    (Blender, Adobe After Effects, Photoshop, Premiere Pro, OBS Studio).
    """
    apps = discovery.discover_all(refresh=True)
    return {
        app_id: {
            "name": app.name,
            "installed": app.is_installed,
            "version": app.version,
            "exe_path": app.exe_path,
            "extra_tools": app.extra_tools,
            "metadata": app.metadata
        }
        for app_id, app in apps.items()
    }


@mcp.tool()
def search_installed_software(query: str) -> List[Dict[str, str]]:
    """
    Searches the Windows Installed Applications registry for any desktop software by name.
    Useful for finding where a specific program is installed on the user's PC.
    """
    return discovery.search_custom_app(query)


@mcp.tool()
def system_get_specs() -> Dict[str, Any]:
    """
    Returns host system hardware and operating system metrics: CPU, RAM total/available,
    disk storage space, and OS version.
    """
    return sys_adapter.get_system_specs()


@mcp.tool()
def system_run_powershell(command: str) -> Dict[str, Any]:
    """
    Executes a PowerShell command or script on the host Windows machine.
    Returns return_code, stdout, and stderr.
    """
    res = sys_adapter.run_powershell(command)
    return res.model_dump()


# ==============================================================================
# BLENDER 3D TOOLS
# ==============================================================================

@mcp.tool()
def blender_run_python(
    code: str,
    blend_file: Optional[str] = None,
    save_blend_as: Optional[str] = None,
    timeout: float = 180.0
) -> Dict[str, Any]:
    """
    Executes Python (`bpy`) code inside Blender 3D in headless mode.
    Can open an existing .blend file and/or save the modified scene to save_blend_as.
    Returns stdout, stderr, and whether the execution succeeded.
    """
    res = blender_adapter.run_python(
        code=code,
        blend_file=blend_file,
        save_blend_as=save_blend_as,
        timeout=timeout
    )
    return res.model_dump()


@mcp.tool()
def blender_render_frame(
    output_path: str,
    blend_file: Optional[str] = None,
    render_engine: str = "BLENDER_EEVEE_NEXT",
    frame: int = 1,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    samples: int = 64
) -> Dict[str, Any]:
    """
    Renders a frame of a 3D scene to an image file (PNG/JPEG) using Blender.
    Supported engines: 'BLENDER_EEVEE_NEXT', 'CYCLES', 'BLENDER_WORKBENCH'.
    """
    options = BlenderRenderOptions(
        blend_file=blend_file,
        output_path=output_path,
        render_engine=render_engine,
        frame=frame,
        resolution_x=resolution_x,
        resolution_y=resolution_y,
        samples=samples
    )
    res = blender_adapter.render_frame(options)
    return res.model_dump()


@mcp.tool()
def blender_export_3d_asset(
    export_format: str,
    output_path: str,
    blend_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exports a 3D scene from Blender to a standard 3D asset file.
    Supported formats: 'glb', 'gltf', 'fbx', 'obj', 'stl'.
    """
    res = blender_adapter.export_asset(
        export_format=export_format,
        output_file=output_path,
        blend_file=blend_file
    )
    return res.model_dump()


@mcp.tool()
def blender_get_scene_info(blend_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects a Blender .blend file and returns a structured breakdown of objects,
    materials, lights, cameras, and render settings.
    """
    return blender_adapter.get_scene_info(blend_file=blend_file)


@mcp.tool()
def blender_create_studio_scene(
    object_type: str = "SPHERE",
    output_blend_path: str = "C:/OmniDesktop_Outputs/scene.blend",
    render_image_path: Optional[str] = "C:/OmniDesktop_Outputs/render.png"
) -> Dict[str, Any]:
    """
    Generates a high-quality studio 3D scene with 3-point lighting, ground plane,
    and PBR materials, saves the .blend file, and optionally renders a preview image.
    Object types: 'SPHERE', 'TORUS', 'MONKEY', 'CUBE'.
    """
    code = get_studio_scene_snippet(object_type=object_type)
    res = blender_adapter.run_python(code=code, save_blend_as=output_blend_path)
    if res.success and render_image_path:
        opts = BlenderRenderOptions(
            blend_file=output_blend_path,
            output_path=render_image_path,
            render_engine="BLENDER_EEVEE_NEXT"
        )
        render_res = blender_adapter.render_frame(opts)
        res.output_files.extend(render_res.output_files)

    return res.model_dump()


# ==============================================================================
# ADOBE AFTER EFFECTS TOOLS
# ==============================================================================

@mcp.tool()
def ae_run_extendscript(
    script_content: str,
    save_project_as: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes Adobe After Effects ExtendScript (.jsx) code.
    Can control compositions, layers, keyframes, effects, and save the .aep project.
    """
    res = ae_adapter.run_extendscript(script_content, save_project_as=save_project_as)
    return res.model_dump()


@mcp.tool()
def ae_render_composition(
    project_path: str,
    composition_name: str,
    output_path: str,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None
) -> Dict[str, Any]:
    """
    Renders an After Effects composition to a video file using the CLI aerender engine.
    """
    options = AERenderOptions(
        project_path=project_path,
        composition_name=composition_name,
        output_path=output_path,
        start_frame=start_frame,
        end_frame=end_frame
    )
    res = ae_adapter.render_composition(options)
    return res.model_dump()


@mcp.tool()
def ae_create_title_animation(
    title_text: str,
    subtitle_text: str = "",
    output_project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a motion graphics animated title card inside After Effects.
    """
    res = ae_adapter.create_title_animation(
        title_text=title_text,
        subtitle_text=subtitle_text,
        output_project_path=output_project_path
    )
    return res.model_dump()


# ==============================================================================
# UNIVERSAL WINDOWS GUI & APP TOOLS
# ==============================================================================

@mcp.tool()
def desktop_list_windows() -> List[Dict[str, Any]]:
    """
    Lists all visible user application windows on the desktop, including window title,
    process name, PID, and memory usage.
    """
    return gui_adapter.list_running_apps()


@mcp.tool()
def desktop_launch_app(
    app_path_or_command: str,
    arguments: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Launches any desktop application executable or command on the host PC.
    """
    res = gui_adapter.launch_app(app_path_or_command, arguments)
    return res.model_dump()


@mcp.tool()
def desktop_focus_window(title_pattern: str) -> bool:
    """
    Finds a window by partial title match and brings it to the foreground.
    """
    return gui_adapter.focus_window(title_pattern)


@mcp.tool()
def desktop_take_screenshot(
    output_path: str,
    window_title_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Captures a screenshot of the entire desktop or a targeted application window,
    saving the result as a PNG image for visual inspection.
    """
    res = gui_adapter.take_screenshot(output_path, window_title_pattern)
    return res.model_dump()


@mcp.tool()
def desktop_send_keys(
    keys: str,
    window_title_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends keyboard strokes or hotkeys (e.g., 'ctrl+s', 'enter', 'f5', or text)
    to the active or targeted application window.
    """
    res = gui_adapter.send_keys(keys, window_title_pattern)
    return res.model_dump()


@mcp.tool()
def desktop_click_mouse(
    x: int,
    y: int,
    button: str = "left",
    clicks: int = 1
) -> Dict[str, Any]:
    """
    Clicks the mouse at specified desktop screen coordinates (X, Y).
    """
    res = gui_adapter.click_mouse(x, y, button, clicks)
    return res.model_dump()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OmniDesktop-MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="MCP transport protocol (stdio or sse)")
    parser.add_argument("--host", default="127.0.0.1", help="Host address for SSE (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port for SSE (default: 8765)")
    args, unknown = parser.parse_known_args()

    logger.info("Starting OmniDesktop-MCP server (transport=%s)...", args.transport)
    if args.transport == "sse":
        logger.info("OmniDesktop-MCP listening on http://%s:%d/sse", args.host, args.port)
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
