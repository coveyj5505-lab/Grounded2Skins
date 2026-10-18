#!/usr/bin/env python3
"""Experimental UE5.6 render-buffer encoder; NOT a cooked package writer.

Input is an NPZ containing Unreal-local centimeter positions, split vertex
normals/tangents, UV0, triangle indices/material IDs, and global skeleton IDs.
UV/hard-normal/material seams must already be split by the source exporter.
Bone signature is a SHA-256 of the preserved 230-bone reference data.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

STRIP = b'\x05\x00'  # measured cooked reference: editor/cooking data stripped


def skeleton_signature(path):
    meshes = json.loads(Path(path).read_text())['meshes']
    bones = meshes[0]['bones']
    if len(bones) != 230 or any(x['bones'] != bones for x in meshes):
        raise ValueError('Expected the preserved identical 230-bone reference')
    canonical = json.dumps(bones, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def validate(data, signature, require_skin=True):
    require(str(np.asarray(data['skeleton_signature']).item()) == signature, 'Skeleton signature differs')
    n = len(data['positions'])
    require(n >= 3, 'Need at least three vertices')
    for key, shape in [('positions', (n, 3)), ('normals', (n, 3)), ('tangents', (n, 3)),
                       ('uv0', (n, 2)), ('signs', (n,)), ('colors', (n, 4))]:
        a = np.asarray(data[key])
        require(a.shape == shape and np.isfinite(a).all(), f'Invalid shape or nonfinite {key}')
        if key != 'colors':
            with np.errstate(over='ignore'):
                require(np.isfinite(a.astype('<f4')).all(), f'{key} exceeds float32 range')
    require(np.isin(data['signs'], [-1, 1]).all(), 'Tangent handedness must be +/-1')
    for key in ('normals', 'tangents'):
        lengths = np.linalg.norm(data[key], axis=1)
        require(np.all(np.abs(lengths - 1) < .02), f'{key} must be unit vectors (packed-normal tolerance .02)')
    require(np.all(np.abs(np.sum(data['normals'] * data['tangents'], axis=1)) < .02),
            'Normals and tangents are not perpendicular')
    require(np.asarray(data['colors']).dtype == np.uint8, 'Colors must be RGBA uint8')
    triangles = np.asarray(data['indices'])
    require(triangles.ndim == 2 and triangles.shape[1] == 3 and len(triangles) > 0,
            'Indices must be a nonempty triangle array')
    require(np.issubdtype(triangles.dtype, np.integer), 'Indices must be integers')
    require(np.all((triangles >= 0) & (triangles < n)), 'Triangle index outside vertex array')
    require(len(np.unique(triangles)) == n, 'Unreferenced vertices must be removed before encoding')
    p = np.asarray(data['positions'], dtype='f8')[triangles]
    require(np.all(np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) > 1e-12),
            'Degenerate triangles')
    materials = np.asarray(data['materials'])
    require(materials.shape == (len(triangles),) and np.issubdtype(materials.dtype, np.integer),
            'Triangle material IDs must be integers')
    count = int(np.asarray(data['material_count']).item())
    require(0 < count <= 32767 and np.all((materials >= 0) & (materials < count)), 'Invalid material slot ID')
    with np.errstate(over='ignore'):
        require(np.isfinite(np.asarray(data['uv0']).astype('<f2')).all(), 'UV exceeds measured float16 format')
    if not require_skin:
        return n, len(triangles)
    joints, weights = np.asarray(data['joints']), np.asarray(data['weights'], dtype='f8')
    require(joints.shape == weights.shape and joints.ndim == 2 and joints.shape[0] == n,
            'Joint/weight dimensions differ')
    require(joints.shape[1] >= 1, 'No skin weights: weight transfer and binding are required')
    require(joints.shape[1] <= 8, 'Only the measured maximum of eight influences is supported')
    require(np.issubdtype(joints.dtype, np.integer) and np.all((joints >= 0) & (joints < 230)),
            'Joint IDs must refer to the unchanged 230-bone skeleton')
    require(np.isfinite(weights).all() and np.all(weights >= 0), 'Invalid bone weights')
    require(np.all(np.abs(weights.sum(axis=1) - 1) < 1e-5), 'Unweighted or unnormalized vertex')
    for a in range(joints.shape[1]):
        for b in range(a):
            require(not np.any((joints[:, a] == joints[:, b]) & (weights[:, a] > 0) & (weights[:, b] > 0)),
                    'Duplicate nonzero influences')
    return n, len(triangles)


def quantize(weights):
    """Largest-remainder UNORM8 conversion, exact sum 255; no top-eight pruning."""
    w = np.asarray(weights, dtype='f8')
    w = w / w.sum(axis=1, keepdims=True)
    scaled = w * 255
    q = np.floor(scaled).astype('u2')
    order = np.argsort(-(scaled - q), axis=1, kind='stable')
    remaining = 255 - q.sum(axis=1)
    for rank in range(w.shape[1]):
        rows = np.flatnonzero(remaining > rank)
        q[rows, order[rows, rank]] += 1
    require(np.all(q.sum(axis=1) == 255), 'Weight quantization failed')
    return q.astype('u1')


def compile_sections(data, signature, palette_limit=70):
    """Reorder/split by material and palette; duplicate shared section vertices.

    70 is the largest palette observed in the working reference, not a proven
    engine maximum. Keeping that conservative cap avoids assuming larger ones.
    """
    n, triangles = validate(data, signature)
    require(1 <= palette_limit <= 70, 'Palette cap must be 1..70 until larger caps are tested')
    weights = quantize(data['weights'])
    quantization_error = float(np.max(np.abs(weights / 255 - data['weights'])))
    quantization_zeroes = int(np.count_nonzero((weights == 0) & (data['weights'] > 0)))
    # Shader paths may use only the first section.MaxBoneInfluences slots.
    # Compact all positive influences before padding, including after UNORM8
    # rounding. Keep matching bone IDs and weights together when sorting.
    order = np.argsort(-weights.astype('i2'), axis=1, kind='stable')
    joints = np.take_along_axis(np.asarray(data['joints']), order, axis=1)
    weights = np.take_along_axis(weights, order, axis=1)
    index = np.asarray(data['indices'])
    material = np.asarray(data['materials'])
    stride = weights.shape[1]
    # Cache per-vertex influence sets to avoid repeatedly scanning eight slots.
    bone_sets = [set(map(int, j[w > 0])) for j, w in zip(joints, weights)]
    groups = []
    for mat in sorted(set(map(int, material))):
        rows, bones = [], set()
        for t in np.flatnonzero(material == mat):
            need = set().union(*(bone_sets[int(v)] for v in index[t]))
            require(len(need) <= palette_limit, 'A triangle exceeds the section palette cap')
            if rows and len(bones | need) > palette_limit:
                groups.append((mat, rows, sorted(bones)))
                rows, bones = [], set()
            rows.append(int(t))
            bones |= need
        if rows:
            groups.append((mat, rows, sorted(bones)))
    source_vertices, reordered_indices, local_joints, qweights, sections, source_triangles = [], [], [], [], [], []
    vertex_base, index_base = 0, 0
    for mat, rows, palette in groups:
        source = index[rows].reshape(-1)
        unique, inverse = np.unique(source, return_inverse=True)
        lookup = np.zeros(230, dtype='u1')
        lookup[palette] = np.arange(len(palette), dtype='u1')
        local = np.zeros((len(unique), 8), dtype='u1')
        q = np.zeros_like(local)
        q[:, :stride] = weights[unique]
        local[:, :stride] = np.where(weights[unique] > 0, lookup[joints[unique]], 0)
        source_vertices.append(unique)
        source_triangles.extend(rows)
        reordered_indices.append(inverse.astype('<u4') + vertex_base)
        local_joints.append(local)
        qweights.append(q)
        sections.append({'material': mat, 'index_start': index_base, 'triangles': len(rows),
                         'vertex_start': vertex_base, 'vertices': len(unique), 'palette': palette,
                         'max_influences': int(np.count_nonzero(q, axis=1).max())})
        vertex_base += len(unique)
        index_base += len(rows) * 3
    source_vertices = np.concatenate(source_vertices)
    result = {key: np.asarray(data[key])[source_vertices] for key in
              ('positions', 'normals', 'tangents', 'uv0', 'signs', 'colors')}
    result.update(indices=np.concatenate(reordered_indices), local_joints=np.concatenate(local_joints),
                  quantized_weights=np.concatenate(qweights), source_vertices=source_vertices,
                  source_triangles=np.asarray(source_triangles), sections=sections,
                  input_vertices=n, triangles=triangles, skeleton_signature=signature,
                  input_material_slots=int(np.asarray(data['material_count']).item()),
                  input_influences=stride,
                  quantization_zeroed_influences=quantization_zeroes,
                  max_weight_quantization_error=quantization_error)
    return result


def bulk(element_size, count, payload):
    require(len(payload) == element_size * count, 'Bulk array size mismatch')
    return struct.pack('<ii', element_size, count) + payload


def packed_normal(xyz, w):
    # FPackedNormal's UE5 reader XORs 0x80808080 (IncreaseNormalPrecision).
    a = np.column_stack((xyz, w))
    return (np.clip(np.rint((a + 1) * 127.5), 0, 255).astype('u1') ^ 0x80)


def encode(data, signature, output, palette_limit=70):
    c = compile_sections(data, signature, palette_limit)
    require(not output.exists(), 'Output path must be new')
    n = len(c['positions'])
    position = c['positions'].astype('<f4').tobytes()
    index = c['indices'].astype('<u4').tobytes()
    tx = packed_normal(c['tangents'], np.ones(n))
    nz = packed_normal(c['normals'], c['signs'])
    tangent = np.concatenate((tx, nz), axis=1).tobytes()
    uv = c['uv0'].astype('<f2').tobytes()
    skin = np.concatenate((c['local_joints'], c['quantized_weights']), axis=1).tobytes()
    color = c['colors'][:, [2, 1, 0, 3]].tobytes()  # FColor's native BGRA memory layout
    blobs = {
        'indices.bin': b'\x04' + bulk(4, len(c['indices']), index),
        'positions.bin': struct.pack('<II', 12, n) + bulk(12, n, position),
        'static-vertices.bin': STRIP + struct.pack('<iiii', 1, n, 0, 0)
                               + bulk(8, n, tangent) + bulk(4, n, uv),
        'skin-weights.bin': STRIP + struct.pack('<iIIIII', 0, 8, n * 8, n, 0, 0)
                            + bulk(1, n * 16, skin) + STRIP + struct.pack('<i', 0) + bulk(4, 0, b''),
        'colors.bin': STRIP + struct.pack('<ii', 4, n) + bulk(4, n, color)}
    metadata = {'format': 'experimental-grounded2-native-buffers-v1',
                'scope': 'Standalone buffer records and section plan only; NOT an installable cooked mesh',
                'profile': 'CUE4Parse GAME_Grounded2 UE5.6', 'skeleton_signature': signature,
                'skeleton_bones': 230, 'input_vertices': c['input_vertices'], 'output_vertices': n,
                'triangles': c['triangles'], 'uv_channels': 1, 'uv_precision': 'float16',
                'normal_tangent_precision': '8-bit packed signed components',
                'weight_precision': 'UNORM8, fixed eight influence slots, exact total255',
                'palette_limit': palette_limit, 'sections': c['sections'],
                'input_material_slots': c['input_material_slots'],
                'max_weight_quantization_error': c['max_weight_quantization_error'],
                'quantization_zeroed_influences': c['quantization_zeroed_influences'],
                'files': {name: {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}
                          for name, blob in blobs.items()},
                'cooked_package_integration': 'Not performed by standalone encoder; see write_resized_lod.py', 'in_game_test': 'NOT RUN'}
    output.mkdir(parents=True)
    for name, blob in blobs.items():
        (output / name).write_bytes(blob)
    np.savez(output / 'expected.npz', **{k: v for k, v in c.items() if isinstance(v, np.ndarray)})
    (output / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh_npz', type=Path)
    parser.add_argument('reference_skeleton_json', type=Path)
    parser.add_argument('new_output_directory', type=Path)
    args = parser.parse_args()
    with np.load(args.mesh_npz, allow_pickle=False) as data:
        result = encode(dict(data), skeleton_signature(args.reference_skeleton_json), args.new_output_directory)
    print(json.dumps({k: result[k] for k in ('output_vertices', 'triangles', 'cooked_package_integration')}))
