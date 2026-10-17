"""
OmniDesktop-MCP Adobe After Effects Adapter.
Controls Adobe After Effects via ExtendScript (.jsx) and the CLI render engine (aerender.exe).
Supports programmatic motion graphics, title cards, composition creation, and headless rendering.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from adapters.base import BaseAdapter
from core.discovery import AppDiscoveryEngine
from core.executor import ExecutionResult, ScriptExecutor
from core.logger import get_logger

logger = get_logger("AfterEffectsAdapter")


class AERenderOptions(BaseModel):
    """Options for rendering an After Effects composition via aerender."""
    project_path: str = Field(description="Path to .aep file")
    composition_name: str = Field(description="Name of the composition to render")
    output_path: str = Field(description="Path to target output video file (e.g. C:/renders/output.mov or .mp4)")
    start_frame: Optional[int] = Field(default=None, description="Starting frame")
    end_frame: Optional[int] = Field(default=None, description="Ending frame")
    render_settings: str = Field(default="Best Settings", description="Render settings template name")
    output_module: str = Field(default="High Quality", description="Output module template name")


class AfterEffectsAdapter(BaseAdapter):
    """Adapter for Adobe After Effects ExtendScript and aerender automation."""

    @property
    def app_id(self) -> str:
        return "after_effects"

    @property
    def display_name(self) -> str:
        return "Adobe After Effects"

    @property
    def aerender_path(self) -> Optional[str]:
        """Returns path to aerender.exe if available."""
        return self._app_info.extra_tools.get("aerender")

    def get_capabilities(self) -> List[str]:
        caps = ["ae_run_extendscript", "ae_create_composition", "ae_create_title_animation"]
        if self.aerender_path:
            caps.append("ae_render_composition")
        return caps

    def run_extendscript(
        self,
        script_content: str,
        save_project_as: Optional[str] = None,
        timeout: float = 120.0
    ) -> ExecutionResult:
        """
        Executes an ExtendScript (.jsx) file via AfterFX.exe -r.
        """
        if not self.is_available:
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message="Adobe After Effects is not installed or AfterFX.exe was not found."
            )

        jsx_lines = [
            "// OmniDesktop After Effects Automation Script",
            "app.beginUndoGroup('OmniDesktop Automation');",
            "try {",
        ]

        for line in script_content.splitlines():
            jsx_lines.append(f"    {line}")

        if save_project_as:
            safe_proj = os.path.abspath(save_project_as).replace("\\", "/")
            jsx_lines.extend([
                f"    var saveFile = new File('{safe_proj}');",
                "    app.project.save(saveFile);",
            ])

        jsx_lines.extend([
            "} catch (err) {",
            "    alert('OmniDesktop Script Error: ' + err.toString());",
            "} finally {",
            "    app.endUndoGroup();",
            "}",
        ])

        final_jsx = "\n".join(jsx_lines)
        temp_jsx_path = ScriptExecutor.create_temp_script(final_jsx, suffix=".jsx", prefix="ae_task_")

        cmd = [self.exe_path, "-r", temp_jsx_path]

        try:
            res = ScriptExecutor.run_sync(cmd, timeout=timeout)
            if save_project_as and os.path.isfile(save_project_as):
                res.output_files.append(os.path.abspath(save_project_as))
            return res
        finally:
            ScriptExecutor.cleanup_file(temp_jsx_path)

    def render_composition(self, options: AERenderOptions, timeout: float = 600.0) -> ExecutionResult:
        """
        Renders a composition via aerender.exe.
        """
        if not self.aerender_path or not os.path.isfile(self.aerender_path):
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message="aerender.exe was not found in After Effects installation."
            )

        abs_proj = os.path.abspath(options.project_path)
        abs_output = os.path.abspath(options.output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)

        cmd = [
            self.aerender_path,
            "-project", abs_proj,
            "-comp", options.composition_name,
            "-output", abs_output,
            "-RStemplate", options.render_settings,
            "-OMtemplate", options.output_module
        ]

        if options.start_frame is not None:
            cmd.extend(["-s", str(options.start_frame)])
        if options.end_frame is not None:
            cmd.extend(["-e", str(options.end_frame)])

        res = ScriptExecutor.run_sync(cmd, timeout=timeout)
        if os.path.isfile(abs_output):
            res.output_files.append(abs_output)
        return res

    def create_title_animation(
        self,
        title_text: str,
        subtitle_text: str = "",
        width: int = 1920,
        height: int = 1080,
        duration_sec: float = 5.0,
        fps: float = 30.0,
        output_project_path: Optional[str] = None
    ) -> ExecutionResult:
        """
        Generates an animated title card composition in After Effects.
        """
        clean_title = title_text.replace("'", "\\'")
        clean_sub = subtitle_text.replace("'", "\\'")

        script = f"""
var comp = app.project.items.addComp('TitleCard', {width}, {height}, 1, {duration_sec}, {fps});
comp.bgColor = [0.08, 0.08, 0.1];

// Main Title Layer
var titleLayer = comp.layers.addText('{clean_title}');
var textProp = titleLayer.property("Source Text");
var textDoc = textProp.value;
textDoc.fontSize = 72;
textDoc.fillColor = [1, 1, 1];
textDoc.justification = ParagraphJustification.CENTER_JUSTIFY;
textProp.setValue(textDoc);
titleLayer.property("Position").setValue([{width / 2}, {height / 2 - 40}, 0]);

// Add Opacity Fade In
var opacity = titleLayer.property("Opacity");
opacity.setValueAtTime(0, 0);
opacity.setValueAtTime(1.0, 100);

if ('{clean_sub}') {{
    var subLayer = comp.layers.addText('{clean_sub}');
    var subDoc = subLayer.property("Source Text").value;
    subDoc.fontSize = 36;
    subDoc.fillColor = [0.4, 0.7, 1.0];
    subDoc.justification = ParagraphJustification.CENTER_JUSTIFY;
    subLayer.property("Source Text").setValue(subDoc);
    subLayer.property("Position").setValue([{width / 2}, {height / 2 + 50}, 0]);
    
    var subOpacity = subLayer.property("Opacity");
    subOpacity.setValueAtTime(0.5, 0);
    subOpacity.setValueAtTime(1.5, 100);
}}
"""
        return self.run_extendscript(script, save_project_as=output_project_path)
