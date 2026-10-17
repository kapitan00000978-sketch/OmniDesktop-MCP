"""
OmniDesktop-MCP Interactive Command-Line Tool.
Allows quick testing of app discovery, Blender scripting, screenshots, and system info.
"""

from __future__ import annotations

import argparse
import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.discovery import AppDiscoveryEngine
from adapters.blender_adapter import BlenderAdapter, BlenderRenderOptions
from adapters.universal_gui_adapter import UniversalGUIAdapter
from adapters.system_adapter import SystemAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="OmniDesktop-MCP Diagnostic & Testing CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Command: discover
    subparsers.add_parser("discover", help="Scan and list detected creative applications")

    # Command: specs
    subparsers.add_parser("specs", help="Show system hardware and OS specs")

    # Command: windows
    subparsers.add_parser("windows", help="List active visible desktop application windows")

    # Command: screenshot
    snap_p = subparsers.add_parser("screenshot", help="Capture a desktop or window screenshot")
    snap_p.add_argument("--output", "-o", default="screenshot.png", help="Target output file path")
    snap_p.add_argument("--title", "-t", default=None, help="Optional window title match")

    # Command: blender-test
    b_p = subparsers.add_parser("blender-test", help="Test background Blender Python execution")
    b_p.add_argument("--save", "-s", default="test_cube.blend", help="Path to save generated .blend file")

    args = parser.parse_args()
    discovery = AppDiscoveryEngine()

    if args.command == "discover":
        apps = discovery.discover_all()
        print("\n--- DETECTED APPLICATIONS ---")
        for app_id, info in apps.items():
            status = "INSTALLED" if info.is_installed else "NOT FOUND"
            print(f"[{status:9}] {info.name:20} -> {info.exe_path or 'N/A'}")
            if info.extra_tools:
                print(f"            Extra Tools: {info.extra_tools}")

    elif args.command == "specs":
        specs = SystemAdapter.get_system_specs()
        print("\n--- HOST SYSTEM SPECS ---")
        print(json.dumps(specs, indent=2))

    elif args.command == "windows":
        gui = UniversalGUIAdapter()
        wins = gui.list_running_apps()
        print(f"\n--- ACTIVE USER WINDOWS ({len(wins)}) ---")
        for w in wins[:20]:
            print(f"[{w['pid']}] {w['process_name']} ({w['memory_mb']} MB): {w['title']}")

    elif args.command == "screenshot":
        gui = UniversalGUIAdapter()
        res = gui.take_screenshot(args.output, args.title)
        print(f"Result: {res.stdout or res.error_message}")

    elif args.command == "blender-test":
        blender = BlenderAdapter(discovery)
        if not blender.is_available:
            print("Blender is not installed on this machine.")
            sys.exit(1)
        print(f"Running Blender test at: {blender.exe_path}")
        code = """
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1.0))
print('Successfully created cube in Blender!')
"""
        res = blender.run_python(code, save_blend_as=args.save)
        if res.success:
            print(f"SUCCESS: Cube created and saved to {os.path.abspath(args.save)}")
        else:
            print(f"FAILED: {res.error_message}")
            print(res.stderr)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
