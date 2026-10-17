"""
Pre-built Python snippets and procedural generators for Blender bpy automation.
"""

from typing import List, Tuple


def get_studio_scene_snippet(
    object_type: str = "SPHERE",
    color: Tuple[float, float, float, float] = (0.2, 0.6, 1.0, 1.0),
    metallic: float = 0.8,
    roughness: float = 0.2
) -> str:
    """Returns a standalone Python script to generate a lit studio scene with a custom PBR material."""
    return f"""
import bpy
import math

# 1. Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Add Object
if '{object_type.upper()}' == 'SPHERE':
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 1.5))
elif '{object_type.upper()}' == 'TORUS':
    bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.5, major_segments=64, minor_segments=32, location=(0, 0, 1.5))
elif '{object_type.upper()}' == 'MONKEY':
    bpy.ops.mesh.primitive_monkey_add(size=2.0, location=(0, 0, 1.5))
else:
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1.5))

obj = bpy.context.active_object
bpy.ops.object.shade_smooth()

# 3. Create PBR Material
mat = bpy.data.materials.new(name="OmniMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
principled = nodes.get("Principled BSDF")

if principled:
    principled.inputs["Base Color"].default_value = {list(color)}
    principled.inputs["Metallic"].default_value = {metallic}
    principled.inputs["Roughness"].default_value = {roughness}

obj.data.materials.append(mat)

# 4. Studio Ground Plane
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new(name="GroundMat")
gmat.use_nodes = True
g_nodes = gmat.node_tree.nodes
g_principled = g_nodes.get("Principled BSDF")
if g_principled:
    g_principled.inputs["Base Color"].default_value = [0.05, 0.05, 0.07, 1.0]
    g_principled.inputs["Roughness"].default_value = 0.5
ground.data.materials.append(gmat)

# 5. Three-Point Studio Lighting
# Key light
bpy.ops.object.light_add(type='AREA', radius=2.5, location=(4, -4, 5))
key = bpy.context.active_object
key.data.energy = 800
key.rotation_euler = (math.radians(45), 0, math.radians(45))

# Fill light
bpy.ops.object.light_add(type='AREA', radius=3.0, location=(-4, -3, 3))
fill = bpy.context.active_object
fill.data.energy = 300

# Rim light
bpy.ops.object.light_add(type='POINT', location=(0, 4, 4))
rim = bpy.context.active_object
rim.data.energy = 600

# 6. Camera
bpy.ops.object.camera_add(location=(0, -6, 3.5), rotation=(math.radians(65), 0, 0))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
"""
