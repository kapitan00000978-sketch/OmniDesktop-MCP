"""
OmniDesktop-MCP Adapters package.
"""

from adapters.base import BaseAdapter
from adapters.blender_adapter import BlenderAdapter, BlenderRenderOptions
from adapters.after_effects_adapter import AfterEffectsAdapter, AERenderOptions
from adapters.universal_gui_adapter import UniversalGUIAdapter
from adapters.system_adapter import SystemAdapter

__all__ = [
    "BaseAdapter",
    "BlenderAdapter",
    "BlenderRenderOptions",
    "AfterEffectsAdapter",
    "AERenderOptions",
    "UniversalGUIAdapter",
    "SystemAdapter"
]
