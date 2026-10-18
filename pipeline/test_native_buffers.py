#!/usr/bin/env python3
"""Integration tests: Python encoding -> unmodified CUE4Parse -> compare data.

Uses the real recovered Commander101 buffers plus explicitly synthetic test
triangles (not substitute character artwork). All outputs must be new.
"""
import argparse
import copy
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from native_buffers import encode, skeleton_signature, validate, quantize

ROOT = Path('/workspace/mod-work')
REFERENCE = ROOT / 'global-stage/reports/reference-skeletons.json'
PROBE = Path(__file__).parent / 'native-buffer-probe/bin/Release/net10.0/NativeBufferProbe.dll'


def read(path, dtype, shape):
    return np.fromfile(path, dtype=dtype).reshape(shape)


def reference_mesh(signature, native):
    body = ROOT / 'mesh-stage/body'
    metadata = json.loads((body / 'mesh.json').read_text())
    n = metadata['vertices']
    # This is a new-buffer test, not a byte-identical tangent round-trip. The
    # measured source has three near-zero tangents and nonorthogonal packed
    # frames. Explicitly repair those for the encoder's stricter input contract.
    normals = read(body / 'normals.f32', '<f4', (n, 3)).astype('f8')
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    tangents = read(native / 'tangents.f32', '<f4', (n, 3)).astype('f8')
    broken = np.linalg.norm(tangents, axis=1) < .5
    tangents -= np.sum(tangents * normals, axis=1, keepdims=True) * normals
    broken |= np.linalg.norm(tangents, axis=1) < 1e-8
    axes = np.eye(3)[np.argmin(np.abs(normals[broken]), axis=1)]
    tangents[broken] = np.cross(axes, normals[broken])
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    print('Reference frame preparation: Gram-Schmidt tangent orthogonalization; fallback tangents:', int(broken.sum()), flush=True)
    return {'positions': read(body / 'positions.f32', '<f4', (n, 3)),
            'normals': normals,
            'tangents': tangents,
            'signs': np.where(read(native / 'signs.f32', '<f4', (n,)) > 0, 1, -1),
            'uv0': read(body / 'uv0.f32', '<f4', (n, 2)),
            'colors': read(body / 'colors.rgba8', 'u1', (n, 4)),
            'indices': read(body / 'indices.u32', '<u4', (-1, 3)),
            'materials': read(body / 'triangle-materials.u16', '<u2', (-1,)),
            'joints': read(body / 'joints.u16', '<u2', (n, 8)),
            'weights': read(body / 'weights.f32', '<f4', (n, 8)),
            'material_count': np.asarray(9), 'skeleton_signature': np.asarray(signature)}


def fixture(signature):
    # Four source vertices, two triangles, two materials. Shared vertices must
    # be duplicated between sections, yielding six render vertices.
    return {'positions': np.array([[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]], dtype='f4'),
            'normals': np.tile([0., 0., 1.], (4, 1)),
            'tangents': np.tile([1., 0., 0.], (4, 1)), 'signs': np.array([1, -1, 1, -1]),
            'uv0': np.array([[0, 0], [1, 0], [1, 1], [.12345, 1]], dtype='f4'),
            'colors': np.array([[255, 1, 2, 255], [3, 254, 4, 128], [5, 6, 253, 64], [42, 17, 89, 255]], dtype='u1'),
            'indices': np.array([[0, 1, 2], [0, 2, 3]], dtype='u4'),
            'materials': np.array([0, 1], dtype='u2'),
            'joints': np.tile([56, 101], (4, 1)),
            'weights': np.array([[.3, .7], [.2, .8], [.6, .4], [.7, .3]], dtype='f4'),
            'material_count': np.asarray(2), 'skeleton_signature': np.asarray(signature)}


def check_decoded(encoded, decoded, source):
    metadata = json.loads((encoded / 'manifest.json').read_text())
    with np.load(encoded / 'expected.npz') as data:
        n = len(data['positions'])
        p = read(decoded / 'positions.f32', '<f4', (n, 3))
        assert np.array_equal(p, data['positions'].astype('f4'))
        for key in ('normals', 'tangents'):
            actual = read(decoded / (key + '.f32'), '<f4', (n, 3))
            assert np.max(np.abs(actual - data[key])) < .004, key
        assert np.array_equal(read(decoded / 'indices.u32', '<u4', (-1,)), data['indices'])
        uv = read(decoded / 'uv0.f32', '<f4', (n, 2))
        assert np.array_equal(uv, data['uv0'].astype('f2').astype('f4'))
        assert np.array_equal(read(decoded / 'colors.rgba8', 'u1', (n, 4)), data['colors'])
        assert np.array_equal(read(decoded / 'signs.f32', '<f4', (n,)), data['signs'])
        joints = read(decoded / 'joints-local.u16', '<u2', (n, 8))
        weights = read(decoded / 'weights.u16', '<u2', (n, 8))
        assert np.array_equal(joints, data['local_joints'])
        assert np.array_equal(weights, data['quantized_weights'])
        assert np.all(weights.sum(axis=1) == 255)
        global_joints = np.zeros_like(joints)
        for section in metadata['sections']:
            start, count = section['vertex_start'], section['vertices']
            global_joints[start:start + count] = np.asarray(section['palette'])[joints[start:start + count]]
            tris = data['indices'][section['index_start']:section['index_start'] + section['triangles'] * 3]
            assert np.all((tris >= start) & (tris < start + count))
        expected_global = source['joints'][data['source_vertices']]
        expected_q = quantize(source['weights'])[data['source_vertices']]
        for actual_joints, actual_q, source_joints, source_q in zip(global_joints, weights, expected_global, expected_q):
            expected = {int(j): int(w) for j, w in zip(source_joints, source_q) if w > 0}
            actual = {int(j): int(w) for j, w in zip(actual_joints, actual_q) if w > 0}
            assert expected == actual
            count = np.count_nonzero(actual_q)
            assert np.all(actual_q[:count] > 0) and not np.any(actual_q[count:])
        return {'vertices': n, 'triangles': len(data['indices']) // 3,
                'sections': len(metadata['sections']), 'positions_indices_colors_exact': True,
                'uvs_equal_float16_quantization': True, 'normal_tangent_error_below': .004,
                'raw_weights_and_local_joints_exact': True, 'palette_to_original_skeleton_ids_exact': True,
                'weights_sum255_every_vertex': True}


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    signature = skeleton_signature(REFERENCE)
    native = ROOT / 'variable-mesh-stage/reference-native'
    env = dict(os.environ, DOTNET_ROOT='/workspace/toolchains/dotnet', DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home')
    report = {'cases': {}, 'expected_rejections': [], 'cooked_package_integration': 'NOT IMPLEMENTED',
              'arbitrary_mesh_in_game_test': 'NOT RUN', 'skeleton_signature': signature}
    cases = [('reference', reference_mesh(signature, native)), ('new-topology', fixture(signature))]
    split = fixture(signature)
    split['materials'][:] = 0
    split['joints'] = np.array([[56, 0], [101, 0], [56, 0], [160, 0]])
    split['weights'] = np.array([[1., 0.]] * 4)
    cases.append(('palette-split', split))
    holes = fixture(signature)
    holes['joints'] = np.tile([56, 0, 0, 0, 0, 0, 0, 101], (4, 1))
    holes['weights'] = np.tile([.3, 0, 0, 0, 0, 0, 0, .7], (4, 1))
    cases.append(('noncontiguous-influences', holes))
    for name, data in cases:
        directory = output / name
        directory.mkdir()
        metadata = encode(data, signature, directory / 'encoded', palette_limit=2 if name == 'palette-split' else 70)
        cmd = ['/workspace/toolchains/dotnet/dotnet', str(PROBE), 'decode', str(directory / 'encoded'), str(directory / 'decoded')]
        with (directory / 'reader.log').open('w') as log:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        report['cases'][name] = check_decoded(directory / 'encoded', directory / 'decoded', data)
        if name == 'new-topology':
            assert metadata['input_vertices'] == 4 and metadata['output_vertices'] == 6
        if name == 'palette-split':
            assert len(metadata['sections']) == 2
        print(name, 'encoder -> CUE4Parse -> comparison passed', flush=True)
    bad = fixture(signature)
    mutations = {
        'changed-skeleton': lambda x: x.update(skeleton_signature=np.asarray('wrong')),
        'nonfinite-position': lambda x: x['positions'].__setitem__((0, 0), np.nan),
        'index-out-of-range': lambda x: x['indices'].__setitem__((0, 0), 9999),
        'unweighted-vertex': lambda x: x['weights'].__setitem__(0, 0),
        'unknown-bone': lambda x: x['joints'].__setitem__((0, 0), 230),
        'duplicate-influence': lambda x: x['joints'].__setitem__((0, 0), 101),
        'unknown-material': lambda x: x['materials'].__setitem__(0, 2),
        'over-eight-influences': lambda x: x.update(joints=np.zeros((4, 9), dtype='u2'), weights=np.full((4, 9), 1 / 9)),
        'missing-skin': lambda x: x.update(joints=np.empty((4, 0), dtype='u2'), weights=np.empty((4, 0))),
        'UV-half-overflow': lambda x: x['uv0'].__setitem__((0, 0), 100000),
    }
    for name, mutate in mutations.items():
        data = copy.deepcopy(bad)
        mutate(data)
        try:
            validate(data, signature)
        except ValueError as error:
            report['expected_rejections'].append({'case': name, 'reason': str(error)})
        else:
            raise AssertionError(f'Invalid input accepted: {name}')
    (output / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('All four native-buffer cases and ten invalid-input checks passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('new_output_directory', type=Path)
    main(parser.parse_args().new_output_directory.resolve())
