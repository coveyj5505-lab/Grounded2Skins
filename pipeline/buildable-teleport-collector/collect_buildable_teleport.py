"""Read-only build-menu/recipe and native type metadata follow-up collector."""
import argparse
import hashlib
import json
import re
import struct
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'support'))
from extract_selected import listing, canonical, DLL_HASH
from discover_pete import header

SEEDS = ('/Game/Blueprints/Items/Table_AllBuildings',)
MAX_GLOBAL_BYTES = 16 * 1024 * 1024
MAX_PACKAGES = 32
MAX_BYTES = 64 * 1024 * 1024


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def marker_candidate(path):
    """Only indexed construction catalogs, relevant UI, and teleport logic."""
    key = canonical(path)
    leaf = key.rsplit('/', 1)[-1]
    compact = re.sub('[^a-z0-9]', '', leaf)
    return (key.startswith('/game/')
            and leaf.startswith(('bp_', 'bpc_', 'bpi_', 'wbp_', 'ui_', 'table_', 'dt_', 'da_'))
            and any(token in compact for token in (
                'teleport', 'trailmarker', 'trailmark', 'allbuildings',
                'buildingrecipe', 'allrecipes', 'allcraftingrecipes',
                'constructionrecipe', 'buildingplacement', 'buildmenu',
                'buildingmenu', 'constructionmenu',
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
    globals_pair = [source.with_name('global.utoc'), source.with_name('global.ucas')]
    observed = pair + ([pak] if pak.is_file() else []) + [p for p in globals_pair if p.is_file()]
    before = [(p.stat().st_size, p.stat().st_mtime_ns) for p in observed]
    output.mkdir(parents=True)
    (output / 'chunks').mkdir()
    report = dict(
        status='INCOMPLETE', retoc_version=version, retoc_sha256=digest(retoc),
        required=list(SEEDS), missing=[], discovered_construction_paths=[], omitted=[],
        packages=[], chunks=[], errors=[], header_warnings=[], decoded_bytes=0,
        global_files=[], global_bytes=0, max_global_bytes=MAX_GLOBAL_BYTES,
        max_packages=MAX_PACKAGES, max_bytes=MAX_BYTES,
        source_metadata_unchanged=False,
        scope='Construction catalogs and related logic plus bounded global script-object metadata. No saves, models, textures, mods, game installation changes or buildable-teleporter implementation.',
    )
    try:
        # Global names resolve native class/function hashes, not game art. Copy
        # only the pair when BOTH are present and their combined size is bounded.
        if not all(p.is_file() for p in globals_pair):
            report['errors'].append('Missing adjacent global.utoc/global.ucas; retaining construction assets')
        elif sum(p.stat().st_size for p in globals_pair) > MAX_GLOBAL_BYTES:
            report['errors'].append('Global pair exceeds 16 MiB; not copied')
        else:
            context = output / 'global'
            context.mkdir()
            for p in globals_pair:
                target = context / p.name
                shutil.copyfile(p, target)
                size = target.stat().st_size
                report['global_files'].append(dict(file='global/' + p.name, bytes=size, sha256=digest(target)))
                report['global_bytes'] += size
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
                            key=lambda k: ('allbuildings' not in k, k))
        report['discovered_construction_paths'] = [index[k]['path'] for k in candidates]
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
            # No bulk art payloads are needed for Blueprint/table analysis.
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
                # Follow only actual construction/teleport logic imports. Never
                # expand into character, material, image or world dependencies.
                queue.extend(canonical(p) for p in info['imported_packages'] if marker_candidate(p))
            except (AssertionError, ValueError, IndexError, UnicodeError, struct.error) as err:
                report['header_warnings'].append(dict(path=key, error=repr(err)))
        if not report['discovered_construction_paths']:
            report['errors'].append('No construction/teleport paths matched; upload the partial metadata rather than guessing asset filenames')
    except Exception as err:
        report['errors'].append(str(err))
    finally:
        report['source_metadata_unchanged'] = before == [(p.stat().st_size, p.stat().st_mtime_ns) for p in observed]
        if not report['source_metadata_unchanged']:
            report['errors'].append('Original file size/mtime changed while collecting')
        report['status'] = ('EXTRACTED_READ_ONLY' if report['packages'] and not any(
            report[k] for k in ('missing', 'errors', 'header_warnings', 'omitted')) else 'PARTIAL')
        (output / 'buildable-teleport-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
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
