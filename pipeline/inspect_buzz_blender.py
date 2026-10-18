"""Import the supplied OBJ and inspect/alignment-test without changing the rig.

Run on the recovered skeleton-only blend. This creates a source inspection
scene, not a rigged Buzz or a game-ready mesh. Imported files are data only.
"""
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path

from mathutils import Vector, Matrix

source, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
if output.exists():
    raise FileExistsError(output)
output.mkdir(parents=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
before = {b.name: [list(row) for row in b.matrix_local] for b in arm.data.bones}
original_objects = set(bpy.data.objects)
bpy.ops.wm.obj_import(filepath=str(source), forward_axis='NEGATIVE_Z', up_axis='Y')
meshes = [o for o in bpy.data.objects if o not in original_objects and o.type == 'MESH']
assert meshes
# Source-specific orientation: Y vertical, wings along Z, face toward -X.
# Confirmed by inspecting the textured render (the opposite yaw shows the back).
# Import establishes Blender Z-up; yaw aligns the face toward reference +Y.
yaw = Matrix.Rotation(-math.pi / 2, 4, 'Z')
all_positions = [yaw @ o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
low = Vector(tuple(min(v[k] for v in all_positions) for k in range(3)))
high = Vector(tuple(max(v[k] for v in all_positions) for k in range(3)))
# Stage an initial height/ground alignment, with no claim of joint correspondence.
target_height = 1.9324701  # measured reference mesh height above ground, meters
height = high.z - low.z
assert height > 0
scale = target_height / height
offset = Vector((-(low.x + high.x) / 2, -(low.y + high.y) / 2, -low.z))
for o in meshes:
    # Preserve normals/UVs and mesh topology; apply one common world transform.
    original = yaw @ o.matrix_world
    for v in o.data.vertices:
        v.co = (original @ v.co + offset) * scale
    o.matrix_world.identity()
    o.data.update()
    o['rigging_status'] = 'Unrigged source inspection; no weights or animation compatibility claimed'
    o['alignment_status'] = 'Height/ground aligned only; shoulder/hip/limb correspondence not solved'
inventory = []
for o in meshes:
    m = o.data
    m.calc_loop_triangles()
    inventory.append({'name': o.name, 'vertices': len(m.vertices), 'faces': len(m.polygons),
        'triangles': len(m.loop_triangles), 'uv_layers': [u.name for u in m.uv_layers],
        'material_slots': [s.material.name if s.material else None for s in o.material_slots],
        'vertex_groups': len(o.vertex_groups), 'armature_modifiers': sum(x.type == 'ARMATURE' for x in o.modifiers),
        'loose_vertices': len(set(range(len(m.vertices))) - {v for p in m.polygons for v in p.vertices})})
images = []
for image in bpy.data.images:
    if image.source == 'FILE':
        image.reload()
        images.append({'name': image.name, 'width': image.size[0], 'height': image.size[1],
                       'has_pixels': image.has_data, 'path': image.filepath})
        if image.has_data:
            image.pack()
assert before == {b.name: [list(row) for row in b.matrix_local] for b in arm.data.bones}
assert len(arm.data.bones) == 230
result = {'objects': inventory, 'images': images, 'source_height_units_after_axis_conversion': height,
          'uniform_scale_to_reference_m': scale, 'target_height_m': target_height,
          'source_centering_offset': list(offset), 'axis_import': 'OBJ Y-up/-Z-forward -> Blender Z-up, then -90deg yaw toward reference +Y',
          'armature_bones': len(arm.data.bones), 'armature_rest_matrices_unchanged': True,
          'armature_rest_matrices_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
          'new_vertex_weights': 'NOT CREATED', 'rigged_mesh': False, 'game_compatibility': 'NOT TESTED',
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
(output / 'blender-inspection.json').write_text(json.dumps(result, indent=2) + '\n')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(output / 'Buzz-source-and-reference-skeleton.blend'), compress=True)
print(json.dumps(result), flush=True)
