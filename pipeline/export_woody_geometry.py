"""Blender exporter for source geometry or an explicitly verified skinned scene.

Run against the orientation/height-aligned Woody rigged scene. Hard-normal,
tangent, and UV seams are split into render vertices; materials remain per face.
Default unskinned output is rejected by the skinned encoder until real weights
exist. --skinned exports real vertex groups from Woody_Skinned and excludes
hidden wing authoring collections.
"""
import bpy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from native_buffers import skeleton_signature, validate

args = sys.argv[sys.argv.index('--') + 1:]
skinned = args[-1] == '--skinned'
if skinned:
    args = args[:-1]
reference, inspection, output = map(Path, args)
if output.exists():
    raise FileExistsError(output)
output.mkdir(parents=True)
arm = bpy.data.objects['Grounded2_Pete_188']
obj = bpy.data.objects['Woody_Skinned'] if skinned else next(o for o in bpy.data.objects if o.type == 'MESH')
mesh = obj.data
assert len(arm.data.bones) == 188
if skinned:
    assert len(obj.vertex_groups) == 188
    assert [g.name for g in obj.vertex_groups] == [b.name for b in arm.data.bones]
    assert sum(m.type == 'ARMATURE' and m.object == arm for m in obj.modifiers) == 1
else:
    assert not obj.vertex_groups
    assert not any(m.type == 'ARMATURE' for m in obj.modifiers)
signature = skeleton_signature(reference)
mesh.calc_loop_triangles()
mesh.calc_tangents(uvmap=mesh.uv_layers.active.name)
tri_loops = np.asarray([tuple(t.loops) for t in mesh.loop_triangles], dtype='i4')
materials = np.asarray([t.material_index for t in mesh.loop_triangles], dtype='u2')
loops = np.asarray([l.vertex_index for l in mesh.loops], dtype='i4')
uv = np.asarray([tuple(v.uv) for v in mesh.uv_layers.active.data], dtype='f4')
uv[:, 1] = 1 - uv[:, 1]  # Blender bottom-left -> Unreal/PNG top-left
normal = np.asarray([tuple(l.normal) for l in mesh.loops], dtype='f8')
tangent = np.asarray([tuple(l.tangent) for l in mesh.loops], dtype='f8')
sign = np.asarray([l.bitangent_sign for l in mesh.loops], dtype='f4')
transform = arm.matrix_world.inverted() @ obj.matrix_world
positions = np.asarray([tuple(transform @ v.co) for v in mesh.vertices], dtype='f8')
assert np.max(np.abs(np.asarray(transform) - np.eye(4))) < 1e-6, 'Inspection scene must have applied mesh-to-armature transform'
# Same reference conversion as the proven exporter, reversed: meters -> cm,
# reflect Y; retain Blender triangle order for Unreal clockwise faces.
positions *= np.array([100, -100, 100])
normal *= np.array([1, -1, 1])
tangent *= np.array([1, -1, 1])
sign *= 1  # Y reflection and V reversal each invert handedness
points = positions[loops[tri_loops]]
areas2 = np.linalg.norm(np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]), axis=1)
keep = areas2 > 1e-12
removed = np.flatnonzero(~keep).tolist()
tri_loops, materials = tri_loops[keep], materials[keep]
used = np.unique(tri_loops)
normal_length = np.linalg.norm(normal[used], axis=1)
assert np.all(normal_length > 1e-8), 'Cannot generate a normal for nondegenerate source faces'
normal[used] /= normal_length[:, None]
tangent[used] -= np.sum(tangent[used] * normal[used], axis=1, keepdims=True) * normal[used]
bad = used[np.linalg.norm(tangent[used], axis=1) < 1e-8]
axes = np.eye(3)[np.argmin(np.abs(normal[bad]), axis=1)]
tangent[bad] = np.cross(axes, normal[bad])
tangent[used] /= np.linalg.norm(tangent[used], axis=1, keepdims=True)
# Handedness is undefined on degenerate UV derivatives. Use a deterministic
# frame for those loops and explicitly report them; their UVs are not changed.
bad_signs = used[~np.isin(sign[used], [-1, 1])]
sign[bad_signs] = 1
keys = np.empty(len(used), dtype=[('vertex', '<i4'), ('uv', '<f4', (2,)),
                               ('normal', '<f4', (3,)), ('tangent', '<f4', (3,)), ('sign', '<f4')])
keys['vertex'], keys['uv'] = loops[used], uv[used]
keys['normal'], keys['tangent'], keys['sign'] = normal[used], tangent[used], sign[used]
unique, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
source_loop = used[first]
lookup = np.full(len(mesh.loops), -1, dtype='i4')
lookup[used] = inverse
indices = lookup[tri_loops].astype('<u4')
source_vertex = loops[source_loop]
n = len(source_loop)
data = {'positions': positions[source_vertex].astype('f4'), 'normals': normal[source_loop].astype('f4'),
        'tangents': tangent[source_loop].astype('f4'), 'signs': sign[source_loop], 'uv0': uv[source_loop],
        'indices': indices, 'materials': materials, 'colors': np.full((n, 4), 255, dtype='u1'),
        'source_vertices': source_vertex, 'material_count': np.asarray(len(mesh.materials)),
        'skeleton_bone_count': np.asarray(188), 'skeleton_signature': np.asarray(signature), 'joints': np.empty((n, 0), dtype='u2'),
        'weights': np.empty((n, 0), dtype='f4')}
validate(data, signature, require_skin=False)
if skinned:
    joints = np.zeros((len(mesh.vertices), 8), dtype='u2')
    weights = np.zeros((len(mesh.vertices), 8), dtype='f4')
    for v in mesh.vertices:
        groups = sorted((g for g in v.groups if g.weight > 0), key=lambda g: (-g.weight, g.group))
        assert 0 < len(groups) <= 8
        for slot, g in enumerate(groups):
            joints[v.index, slot], weights[v.index, slot] = g.group, g.weight
    data['joints'], data['weights'] = joints[source_vertex], weights[source_vertex]
    validate(data, signature)
    skin_rejection = None
else:
    try:
        validate(data, signature)
    except ValueError as error:
        skin_rejection = str(error)
    else:
        raise AssertionError('Unrigged source must not be accepted as a skinned mesh')
np.savez_compressed(output / ('Woody-geometry-SKINNED.npz' if skinned else 'Woody-geometry-UNSKINNED.npz'), **data)
report = {'source_vertices': len(mesh.vertices), 'source_triangles': len(mesh.loop_triangles),
          'render_vertices_after_uv_normal_tangent_seam_splitting': n, 'triangles': len(indices),
          'material_slots': [m.name for m in mesh.materials], 'uv_channels': 1,
          'coordinate_system': 'Unreal centimeters, Y reflected from Blender, clockwise triangle order',
          'removed_degenerate_triangle_ids': removed, 'fallback_tangent_loop_count': len(bad),
          'fallback_tangent_sign_loop_count': len(bad_signs), 'normals': 'Blender smooth FBX geometry; UV V reversed for Unreal/PNG orientation',
          'tangents': 'Blender UV tangents orthogonalized; degenerate derivative fallbacks reported',
          'geometry_preflight': 'passed', 'skin_preflight_expected_rejection': skin_rejection,
          'skin_weights': 'Preserved from verified Blender vertex groups' if skinned else 'NOT CREATED', 'game_compatibility': 'NOT TESTED',
          'skeleton_signature': signature, 'armature_bones': len(arm.data.bones)}
(output / 'geometry-preflight.json').write_text(json.dumps(report, indent=2) + '\n')

print(json.dumps(report), flush=True)
