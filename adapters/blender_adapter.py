"""
OmniDesktop-MCP Blender Adapter.
Controls Blender 3D via headless background execution and Python (`bpy`) scripting.
Supports 3D modeling, material generation, procedural scenes, asset export (GLTF/FBX/OBJ),
and rendering (EEVEE/Cycles).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from adapters.base import BaseAdapter
from core.discovery import AppDiscoveryEngine
from core.executor import ExecutionResult, ScriptExecutor
from core.logger import get_logger

logger = get_logger("BlenderAdapter")


class BlenderRenderOptions(BaseModel):
    """Options for rendering a 3D scene."""
    blend_file: Optional[str] = Field(default=None, description="Path to .blend file (or None for default)")
    output_path: str = Field(description="Output image or video path (e.g. C:/renders/frame_###.png)")
    render_engine: str = Field(default="BLENDER_EEVEE_NEXT", description="BLENDER_EEVEE_NEXT or CYCLES or BLENDER_WORKBENCH")
    frame: int = Field(default=1, description="Frame number to render")
    resolution_x: int = Field(default=1920, description="Width in pixels")
    resolution_y: int = Field(default=1080, description="Height in pixels")
    samples: int = Field(default=64, description="Render samples")


class BlenderAdapter(BaseAdapter):
    """Adapter for Blender 3D automation."""

    @property
    def app_id(self) -> str:
        return "blender"

    @property
    def display_name(self) -> str:
        return "Blender 3D"

    def get_capabilities(self) -> List[str]:
        return [
            "blender_run_python",
            "blender_render_frame",
            "blender_get_scene_info",
            "blender_export_asset",
            "blender_create_3d_model"
        ]

    def run_python(
        self,
        code: str,
        blend_file: Optional[str] = None,
        save_blend_as: Optional[str] = None,
        timeout: float = 180.0
    ) -> ExecutionResult:
        """
        Executes a Python script inside headless Blender.
        If save_blend_as is specified, automatically appends bpy.ops.wm.save_as_mainfile.
        """
        if not self.is_available:
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message="Blender is not installed or blender.exe was not found."
            )

        # Wrap code with helper imports and optional save
        script_parts = [
            "import bpy",
            "import sys",
            "import os",
            "print('--- OMNI_BLENDER_START ---')",
            "try:",
        ]

        # Indent user code
        for line in code.splitlines():
            script_parts.append(f"    {line}")

        if save_blend_as:
            safe_save = os.path.abspath(save_blend_as).replace("\\", "/")
            os.makedirs(os.path.dirname(safe_save), exist_ok=True)
            script_parts.extend([
                f"    os.makedirs(os.path.dirname(r'{safe_save}'), exist_ok=True)",
                f"    bpy.ops.wm.save_as_mainfile(filepath=r'{safe_save}')",
                f"    print('OMNI_SAVED_BLEND:', r'{safe_save}')",
            ])

        script_parts.extend([
            "    print('--- OMNI_BLENDER_SUCCESS ---')",
            "except Exception as e:",
            "    import traceback",
            "    print('--- OMNI_BLENDER_ERROR ---', file=sys.stderr)",
            "    traceback.print_exc()",
            "    sys.exit(1)",
        ])

        final_script = "\n".join(script_parts)
        temp_script_path = ScriptExecutor.create_temp_script(final_script, suffix=".py", prefix="blender_task_")

        cmd = [self.exe_path, "-b"]
        if blend_file and os.path.isfile(blend_file):
            cmd.append(os.path.abspath(blend_file))

        cmd.extend(["-P", temp_script_path])

        try:
            res = ScriptExecutor.run_sync(cmd, timeout=timeout)
            if save_blend_as and os.path.isfile(save_blend_as):
                res.output_files.append(os.path.abspath(save_blend_as))
            return res
        finally:
            ScriptExecutor.cleanup_file(temp_script_path)

    def render_frame(self, options: BlenderRenderOptions, timeout: float = 300.0) -> ExecutionResult:
        """Renders a single frame to an image file."""
        if not self.is_available:
            return ExecutionResult(success=False, return_code=-1, error_message="Blender not installed")

        abs_output = os.path.abspath(options.output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)

        render_script = f"""
import bpy
bpy.context.scene.render.engine = '{options.render_engine}'
bpy.context.scene.render.resolution_x = {options.resolution_x}
bpy.context.scene.render.resolution_y = {options.resolution_y}
bpy.context.scene.render.filepath = r'{abs_output}'
bpy.context.scene.frame_set({options.frame})
if '{options.render_engine}' == 'CYCLES':
    bpy.context.scene.cycles.samples = {options.samples}
bpy.ops.render.render(write_still=True)
print('RENDER_COMPLETED:', r'{abs_output}')
"""
        res = self.run_python(render_script, blend_file=options.blend_file, timeout=timeout)
        if os.path.isfile(abs_output):
            res.output_files.append(abs_output)
        return res

    def export_asset(
        self,
        export_format: str,
        output_file: str,
        blend_file: Optional[str] = None,
        timeout: float = 120.0
    ) -> ExecutionResult:
        """
        Exports the scene to a 3D asset file (glb, gltf, fbx, obj, stl).
        """
        abs_output = os.path.abspath(output_file).replace("\\", "/")
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)

        fmt = export_format.lower()
        if fmt in ("glb", "gltf"):
            export_cmd = f"bpy.ops.export_scene.gltf(filepath=r'{abs_output}', export_format='GLB' if '{fmt}'=='glb' else 'GLTF_SEPARATE')"
        elif fmt == "fbx":
            export_cmd = f"bpy.ops.export_scene.fbx(filepath=r'{abs_output}')"
        elif fmt == "obj":
            export_cmd = f"bpy.ops.wm.obj_export(filepath=r'{abs_output}')"
        elif fmt == "stl":
            export_cmd = f"bpy.ops.wm.stl_export(filepath=r'{abs_output}')"
        else:
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message=f"Unsupported 3D export format '{export_format}'. Supported: glb, gltf, fbx, obj, stl"
            )

        script = f"""
import bpy
{export_cmd}
print('ASSET_EXPORTED:', r'{abs_output}')
"""
        res = self.run_python(script, blend_file=blend_file, timeout=timeout)
        if os.path.isfile(output_file):
            res.output_files.append(os.path.abspath(output_file))
        return res

    def get_scene_info(self, blend_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Introspects scene structure, active objects, materials, and render settings.
        """
        script = """
import bpy
import json

data = {
    "scene_name": bpy.context.scene.name,
    "render_engine": bpy.context.scene.render.engine,
    "resolution": [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
    "objects": [],
    "materials": [mat.name for mat in bpy.data.materials],
    "cameras": [cam.name for cam in bpy.data.cameras],
    "lights": [light.name for light in bpy.data.lights]
}

for obj in bpy.context.scene.objects:
    data["objects"].append({
        "name": obj.name,
        "type": obj.type,
        "location": [round(c, 3) for c in obj.location],
        "visible": obj.visible_get()
    })

print("JSON_SCENE_INFO_START")
print(json.dumps(data))
print("JSON_SCENE_INFO_END")
"""
        res = self.run_python(script, blend_file=blend_file)
        if not res.success:
            return {"error": res.error_message or "Failed to inspect scene"}

        try:
            output = res.stdout
            if "JSON_SCENE_INFO_START" in output and "JSON_SCENE_INFO_END" in output:
                json_part = output.split("JSON_SCENE_INFO_START")[1].split("JSON_SCENE_INFO_END")[0].strip()
                return json.loads(json_part)
        except Exception as ex:
            logger.warning("Failed to parse scene info json: %s", ex)

        return {"raw_output": res.stdout}
