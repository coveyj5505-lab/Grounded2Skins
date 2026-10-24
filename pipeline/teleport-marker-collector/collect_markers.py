"""Read-only, bounded discovery of current map/trail-marker/native travel assets."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'support'))
from extract_selected import listing, canonical, DLL_HASH
from discover_pete import header

SEEDS = (
    '/Game/Blueprints/Player/BP_SurvivalPlayerController',
    '/Game/UI/Map/UI_Map',
    '/Game/UI/Map/UI_MapPanel',
    '/Game/_Dev/Art/Buildings/Proto/BP_Teleporter',
    '/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door',
)
MAX_PACKAGES = 32
MAX_BYTES = 64 * 1024 * 1024


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def marker_candidate(path):
    """Select logic/UI by actual indexed names, never mesh/texture payloads."""
    key = canonical(path)
    leaf = key.rsplit('/', 1)[-1]
    compact = re.sub('[^a-z0-9]', '', leaf)
    return (key.startswith('/game/')
            and leaf.startswith(('bp_', 'bpc_', 'bpi_', 'wbp_', 'ui_'))
            and any(token in compact for token in (
                'trailmarker', 'trailmark', 'mapmarker', 'playermarker',
                'waypoint', 'hudmarker', 'worldlabel',
            )))


def collect(retoc, source, output):
    retoc, source, output = (Path(p).resolve() for p in (retoc, source, output))
    # The file picker accepts the PAK users recognize, but reads its matching
    # IoStore index/data pair. It does not treat a PAK as an IoStore index.
    if source.name.casefold() == 'augusta-wingdk.pak':
        source = source.with_suffix('.utoc')
    if source.name.casefold() != 'augusta-wingdk.utoc':
        raise ValueError('Select original Augusta-WinGDK.pak or Augusta-WinGDK.utoc')
    pair = [source, source.with_suffix('.ucas')]
    if not all(p.is_file() for p in pair):
        raise ValueError('Matching original Augusta-WinGDK.utoc and .ucas are required')
    if output.exists() or output.with_suffix('.zip').exists() or output.is_relative_to(source.parent):
        raise ValueError('Choose a NEW output directory/ZIP outside original game Paks')
    version = subprocess.check_output([str(retoc), '--version'], text=True).strip()
    if version != 'retoc_cli 0.1.5':
        raise ValueError('Use the existing Windows retoc.exe 0.1.5')
    for name, expected in DLL_HASH.items():
        lib = retoc.with_name(name)
        if lib.exists() and digest(lib) != expected:
            raise ValueError('Unexpected decoder checksum: ' + name)
    # Monitor PAK too when present, without copying or unpacking it.
    pak = source.with_suffix('.pak')
    observed = pair + ([pak] if pak.is_file() else [])
    before = [(p.stat().st_size, p.stat().st_mtime_ns) for p in observed]
    output.mkdir(parents=True)
    (output / 'chunks').mkdir()
    report = dict(
        status='INCOMPLETE', retoc_version=version, retoc_sha256=digest(retoc),
        required=list(SEEDS), missing=[], discovered_marker_paths=[], omitted=[],
        packages=[], chunks=[], errors=[], header_warnings=[], decoded_bytes=0,
        max_packages=MAX_PACKAGES, max_bytes=MAX_BYTES,
        source_metadata_unchanged=False,
        scope='Cooked logic/UI only. No saves, textures, mesh payloads, game installation, or mod changes. No native marker-travel capability is assumed.',
    )
    try:
        rows = listing(retoc, source, output / 'source-index.log')
        index = {}
        for row in rows:
            if row['type'] != 'ExportBundleData':
                continue
            key = canonical(row['path'])
            if key in index:
                raise ValueError('Duplicate indexed package path: ' + key)
            index[key] = row
        candidates = sorted((k for k in index if marker_candidate(k)),
                            key=lambda k: ('trail' not in k, k))
        report['discovered_marker_paths'] = [index[k]['path'] for k in candidates]
        queue = [canonical(p) for p in SEEDS] + candidates
        seen = set()
        while queue:
            key = queue.pop(0)
            if key in seen:
                continue
            seen.add(key)
            if key not in index:
                report['missing'].append(key)
                continue
            entry = index[key]
            # No bulk payloads are needed for Blueprint/name-map analysis.
            size = entry['size']
            if len(report['packages']) >= MAX_PACKAGES or report['decoded_bytes'] + size > MAX_BYTES:
                report['omitted'].append(dict(path=key, reason='package/byte budget'))
                continue
            dest = output / 'chunks' / entry['id']
            with (output / 'extract.log').open('a', encoding='utf-8') as log:
                subprocess.run([str(retoc), 'get', str(source), entry['id'], str(dest)],
                               check=True, stdout=log, stderr=subprocess.STDOUT)
            actual = dest.stat().st_size
            report['decoded_bytes'] += actual
            if actual != size:
                raise ValueError('Decoded chunk size mismatch: ' + key)
            report['chunks'].append(dict(entry, sha256=digest(dest)))
            record = dict(path=key, chunk=entry['id'])
            report['packages'].append(record)
            try:
                info = header(dest.read_bytes())
                record.update(info)
                # Follow only actual marker/UI logic imports. Do not expand into
                # character, material, image or world dependencies.
                queue.extend(canonical(p) for p in info['imported_packages'] if marker_candidate(p))
            except (AssertionError, ValueError, IndexError, UnicodeError, struct.error) as err:
                report['header_warnings'].append(dict(path=key, error=repr(err)))
        if not report['discovered_marker_paths']:
            report['errors'].append('No marker logic matched the indexed names; upload baselines rather than guessing asset filenames')
    except Exception as err:
        report['errors'].append(str(err))
    finally:
        report['source_metadata_unchanged'] = before == [(p.stat().st_size, p.stat().st_mtime_ns) for p in observed]
        if not report['source_metadata_unchanged']:
            report['errors'].append('Original file size/mtime changed while collecting')
        report['status'] = ('EXTRACTED_READ_ONLY' if report['packages'] and not any(
            report[k] for k in ('missing', 'errors', 'header_warnings', 'omitted')) else 'PARTIAL')
        (output / 'marker-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        with zipfile.ZipFile(output.with_suffix('.zip'), 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for file in sorted(output.rglob('*')):
                if file.is_file() and file.name != 'source-index.log':
                    archive.write(file, file.relative_to(output))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retoc', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = collect(args.retoc, args.source, args.output)
    print(result['status'], len(result['packages']), 'packages;', result['decoded_bytes'], 'bytes')
    print('UPLOAD ONE ZIP:', Path(args.output).with_suffix('.zip'))
    sys.exit(0 if result['status'] == 'EXTRACTED_READ_ONLY' else 2)
