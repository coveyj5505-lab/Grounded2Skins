"""Add a separate base-teleporter building/recipe; preserve native rows byte for byte.

Inputs are hash-verified collector chunks and CUE4Parse-measured native row layouts.
The only replacements are the two composite catalogs, with additive private parents.
No runtime AddRow/CopyScriptStruct, existing recipe swap, or cooked map/controller edit.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from cityhash import CityHash64

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'teleport-marker-collector/support'))
from discover_pete import names

ROW = 'RivetBaseTeleporter'
BUILD_TABLE = '/Game/Rivet/Teleport/RivetBaseBuildingData'
RECIPE_TABLE = '/Game/Rivet/Teleport/RivetBaseRecipeData'
BUILD_ID = '69a09afefc4abfcd00000001'
RECIPE_ID = 'cd0419132f02479000000001'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def H(value):
    return CityHash64(value.lower().encode('utf-16le'))


def batch(values):
    encoded = [s.encode('ascii') for s in values]
    require(all(len(s) < 32768 for s in encoded), 'Name too long')
    return (struct.pack('<IIQ', len(encoded), sum(map(len, encoded)), 0xc1640000)
            + b''.join(struct.pack('<Q', CityHash64(s.lower())) for s in encoded)
            + b''.join(struct.pack('>H', len(s)) for s in encoded) + b''.join(encoded))


def encode_struct(fields):
    """Serialize measured opaque fields with a rebuilt native unversioned header."""
    fields = sorted(fields, key=lambda x: x['Index'])
    require(len({f['Index'] for f in fields}) == len(fields), 'Duplicate field index')
    fragments = []
    current = 0
    pos = 0
    while pos < len(fields):
        skip = fields[pos]['Index'] - current
        while skip > 127:
            fragments.append((127, []))
            skip -= 127
            current += 127
        run = [fields[pos]]
        pos += 1
        while pos < len(fields) and len(run) < 127 and fields[pos]['Index'] == run[-1]['Index'] + 1:
            run.append(fields[pos]); pos += 1
        fragments.append((skip, run))
        current = run[-1]['Index'] + 1
    require(fragments, 'Cannot encode an empty row')
    headers, mask = bytearray(), []
    for i, (skip, run) in enumerate(fragments):
        zeroes = any(not f['NonZero'] for f in run)
        packed = skip | (int(zeroes) << 7) | (int(i == len(fragments)-1) << 8) | (len(run) << 9)
        headers.extend(struct.pack('<H', packed))
        if zeroes:
            mask.extend(not f['NonZero'] for f in run)
    if mask:
        size = 1 if len(mask) <= 8 else 2 if len(mask) <= 16 else 4*((len(mask)+31)//32)
        headers.extend(sum(int(b) << i for i, b in enumerate(mask)).to_bytes(size, 'little'))
    return bytes(headers) + b''.join(f['Bytes'] for f in fields if f['NonZero'])


class Package:
    def __init__(self, raw, layout):
        self.raw = raw
        self.summary = list(struct.unpack_from('<15I', raw))
        s = self.summary
        require(s[0] == 0 and s[9]-s[8] == 72, 'Expected one-export unversioned Zen table')
        self.names, self.name_end = names(raw, 60)
        self.packages, self.package_end = names(raw, s[12])
        require(len(raw[s[12]:s[1]]) >= 4*len(self.packages), 'Imported-name footer')
        self.layout = layout

    def name_index(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def row(self, name):
        info = next(r for r in self.layout['Rows'] if r['Name'] == name)
        return [dict(f, Bytes=self.raw[f['Position']:f['Position']+f['Size']]) for f in info['Properties']]

    def record(self, fields):
        return struct.pack('<II', self.name_index(ROW), 0) + encode_struct(fields)

    def emit(self, payload, *, new_name=None, parent=None, script_ids=None):
        raw, s = self.raw, self.summary.copy()
        ns = self.names.copy()
        old_name_index = struct.unpack_from('<I', raw, s[8]+16)[0] & 0x3fffffff
        old_name = ns[old_name_index]
        publics = list(struct.unpack_from('<'+'Q'*((s[7]-s[6])//8), raw, s[6]))
        imports = list(struct.unpack_from('<'+'Q'*((s[8]-s[7])//8), raw, s[7]))
        packages = self.packages.copy()
        package_nums = list(struct.unpack_from('<'+'I'*len(packages), raw, self.package_end))
        require(self.package_end+4*len(packages) == s[1], 'Unexpected package-name footer')
        dep_headers = bytearray(raw[s[10]:s[11]])
        dep_entries = raw[s[11]:s[12]]
        export = bytearray(raw[s[8]:s[9]])
        if new_name:
            ns[s[2] & 0x3fffffff] = new_name
            ns[old_name_index] = new_name.rsplit('/', 1)[-1]
            require(struct.unpack_from('<Q', export, 56)[0] == H(old_name), 'Unexpected public table hash')
            struct.pack_into('<Q', export, 56, H(ns[old_name_index]))
            struct.pack_into('<Q', export, 32, script_ids['/Script/Engine/DataTable'])
            struct.pack_into('<Q', export, 48, script_ids['/Script/Engine/Default__DataTable'])
        if parent:
            object_id = (2 << 62) | (len(packages) << 32) | len(publics)
            publics.append(H(parent.rsplit('/', 1)[-1]))
            imports.append(object_id); packages.append(parent); package_nums.append(0)
            require(len(dep_headers) == 20, 'Dependency header must describe one export')
            count = struct.unpack_from('<I', dep_headers, 16)[0]
            struct.pack_into('<I', dep_headers, 16, count+1)
            dep_entries += struct.pack('<i', -len(imports))
        struct.pack_into('<Q', export, 8, len(payload))
        chunks = [raw[:60], batch(ns), raw[self.name_end:s[6]],
                  struct.pack('<'+'Q'*len(publics), *publics),
                  struct.pack('<'+'Q'*len(imports), *imports), bytes(export),
                  raw[s[9]:s[10]], bytes(dep_headers), dep_entries,
                  batch(packages)+struct.pack('<'+'I'*len(package_nums), *package_nums)]
        # Sections 6..12 are reconstructed; the two empty cell maps track bundles.
        boundaries = {}; cursor = 60
        for section, part in zip([None,None,6,7,8,9,10,11,12], chunks[1:]):
            if section is not None:
                boundaries[section] = cursor
            cursor += len(part)
        delta = cursor-s[1]
        out_summary = s.copy(); out_summary[1] = cursor; out_summary[5] += delta
        for index, value in boundaries.items(): out_summary[index] = value
        for index in [13,14]:
            require(s[index] == s[9], 'Unexpected nonempty cell import/export map')
            out_summary[index] = out_summary[9]
        out = bytearray(b''.join(chunks)+payload)
        struct.pack_into('<15I', out, 0, *out_summary)
        return bytes(out)

    def with_parent(self, record):
        s = self.summary
        payload = bytearray(self.raw[s[1]:])
        require(payload[:4] == bytes.fromhex('00020103'), 'Unexpected composite object header')
        parent_count = struct.unpack_from('<I', payload, 4)[0]
        count_at = self.layout['CountPosition']-s[1]
        require(count_at == 16+4*parent_count, 'Unexpected parent-array/object prefix')
        count = struct.unpack_from('<I', payload, count_at)[0]
        # The new import is appended by emit().
        import_count = (s[8]-s[7])//8
        insert = 8+4*parent_count
        payload[insert:insert] = struct.pack('<i', -import_count-1)
        struct.pack_into('<I', payload, 4, parent_count+1)
        struct.pack_into('<I', payload, count_at+4, count+1)
        return bytes(payload)+record

    def standalone(self, record):
        at = self.layout['CountPosition']
        require(self.raw[at-4:at] == bytes(4), 'Expected no object GUID')
        row_struct = self.raw[at-8:at-4]
        return bytes.fromhex('0003')+row_struct+bytes(4)+struct.pack('<I',1)+record


def build(collection, layouts, template, output):
    require(not output.exists(), 'Use a new output directory')
    report = json.loads((collection/'buildable-teleport-report.json').read_text())
    by_id = {c['id']:c for c in report['chunks']}
    packages = {}
    for cid in [BUILD_ID, RECIPE_ID]:
        raw = (collection/'chunks'/cid).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == by_id[cid]['sha256'], 'Source hash mismatch')
        path = next(layouts.glob(cid+'-*.layout.json'))
        layout=json.loads(path.read_text())
        require(layout.get('SourceSHA256')==hashlib.sha256(raw).hexdigest(), 'Stale/missing source hash in measured layout')
        packages[cid] = Package(raw, layout)
    b, r = packages[BUILD_ID], packages[RECIPE_ID]
    require(all(row['Name']!=ROW for package in [b,r] for row in package.layout['Rows']), 'Base row already exists; do not duplicate it')
    building = b.row('MarkerBuilding')
    display = {f['Name']:f for f in b.row('UGCTeleporter')}
    inspect = {f['Name']:f for f in b.row('SurvivalTeleporter')}
    for f in building:
        if f['Name']=='PlacementData':
            data=bytearray(f['Bytes'])
            for name in ['bPermitForUGC','bPermitRescaling','bPermitExtraRotationAxes']:
                child=next(c for c in f['Children'] if c['Name']==name)
                at=child['Position']-f['Position']
                require(child['Size']==1 and data[at]==1, 'Expected native placement boolean: '+name)
                data[at]=0
            f['Bytes']=bytes(data)
        source = inspect.get(f['Name']) if f['Name']=='ModelViewerMeshOverride' else display.get(f['Name'])
        if f['Name'] in ['LocalizedDisplayName','LocalizedWildcardDisplayName','LocalizedDescription','IconSoft','ModelViewerMeshOverride']:
            require(source is not None, 'Display source field absent')
            f['Bytes']=source['Bytes']; f['NonZero']=source['NonZero']
    recipe = r.row('MarkerBuilding')
    old_index = r.name_index('MarkerBuilding'); new_index = r.name_index(ROW)
    for f in recipe:
        if f['Name']=='Building':
            require(len(f['Bytes']) == 14 and f['Bytes'][-8:] == struct.pack('<II',old_index,0), 'Building row handle layout')
            f['Bytes']=f['Bytes'][:-8]+struct.pack('<II',new_index,0)
        elif f['Name'] in ['Visibility','MetaRecipe']:
            # Visible=0. No existing meta-recipe group/variant is reused.
            f['NonZero']=False; f['Bytes']=b''
    building_record=b.record(building); recipe_record=r.record(recipe)
    globals_=json.loads((collection/'global/script-object-paths.json').read_text())
    script_ids={v:int(k,16) for k,v in globals_.items()}
    generated={BUILD_ID:b.emit(b.with_parent(building_record),parent=BUILD_TABLE),
               RECIPE_ID:r.emit(r.with_parent(recipe_record),parent=RECIPE_TABLE)}
    paths={BUILD_ID:'../../../Augusta/Content/Blueprints/Items/Table_AllBuildings.uasset',
           RECIPE_ID:'../../../Augusta/Content/Blueprints/Items/Table_BuildingRecipes.uasset'}
    for package, path, record in [(b,BUILD_TABLE,building_record),(r,RECIPE_TABLE,recipe_record)]:
        cid=H(path).to_bytes(8,'little').hex()+'00000001'
        generated[cid]=package.emit(package.standalone(record),new_name=path,script_ids=script_ids)
        paths[cid]='../../../Augusta/Content/'+path.removeprefix('/Game/')+'.uasset'
    entries={}
    for cid,raw in generated.items():
        s=struct.unpack_from('<15I',raw);imports,_=names(raw,s[12])
        entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(v) for v in imports]
    entries=dict(sorted(entries.items())); store=bytearray(16*len(entries))
    for i,imports in enumerate(entries.values()):
        if imports:
            struct.pack_into('<II',store,i*16,len(imports),len(store)-i*16)
            store.extend(struct.pack('<'+'Q'*len(imports),*imports))
    oldheader=next((template/'chunks').glob('*00000006'))
    header=bytearray(oldheader.read_bytes()[:16]+struct.pack('<I',len(entries))+
                     struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(store))+store+bytes(20))
    header.extend(struct.pack('<qqI',len(header)+16,4,0))
    (output/'chunks').mkdir(parents=True)
    for cid,raw in generated.items():(output/'chunks'/cid).write_bytes(raw)
    (output/'chunks'/oldheader.name).write_bytes(header)
    manifest=json.loads((template/'manifest.json').read_text());manifest['chunk_paths']=paths
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'build-evidence.json').write_text(json.dumps(dict(row=ROW,packages=paths,
        prototype_cost='Inherited trail-marker recipe: 2 Twig, 2 FiberRaw, 1 CloverTop',
        source_rows_removed=False,source_rows_modified=False,runtime_AddRow=False,
        cooked_map_or_controller_modified=False,game_validation='NOT_RUN'),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['collection','layouts','template','output']:p.add_argument(arg,type=Path)
    a=p.parse_args();build(a.collection,a.layouts,a.template,a.output)
