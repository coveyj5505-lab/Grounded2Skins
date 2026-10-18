#!/usr/bin/env python3
"""Hash-guarded Commander101 LOD replacement and measured Zen relocation.

Only the two measured UE5.6 inline-LOD layouts are supported. Material imports,
reference skeleton, physics and every unrelated package are preserved. This is
an experimental geometry package; Buzz's Unreal materials are NOT created here.
"""
import argparse,hashlib,json,struct,shutil
from pathlib import Path
import numpy as np
from native_buffers import skeleton_signature,require

SOURCES={'cd809abc483f179000000001':('7c4f26505028ebce27c7dc02aabfc61a719aa2e4ee4204a08b73884890664901',0),
         '8021448bfc8c514500000001':('4f7fef0ff36eb41e74375625dfef50c9fb182e6a22643c61f52160b6d9984f18',24)}
STREAM_TAIL=bytes.fromhex('00000000ffffffffffffffffffffffffffffffffffffffffffffffff0100000000000000000000000000000005000000000000000000')

def array16(a):return struct.pack('<i',len(a))+np.asarray(a,dtype='<u2').tobytes()

def section(s):
    p=s['palette'];require(0<len(p)<=70,'Unsupported palette')
    return (struct.pack('<2shiiiBiiIi',b'\x05\x01',s['material'],s['index_start'],s['triangles'],0,3,1,1,s['vertex_start'],0)
            +array16(p)+struct.pack('<iih16sii',s['vertices'],s['max_influences'],-1,bytes(16),-1,0))

def write(raw,buffers,skeleton,output):
    require(not output.exists(),'Output must be new')
    manifest=json.loads((buffers/'manifest.json').read_text());require(manifest['skeleton_signature']==skeleton_signature(skeleton),'Skeleton mismatch')
    require(manifest['skeleton_signature']=='204fba7a92cf816c84af30417b78b6e6f6d11716c3071611fffedb8b30a7a46a','Different reference skeleton is unsupported')
    require(manifest['format']=='experimental-grounded2-native-buffers-v1','Unsupported buffer format')
    vertex_base=index_base=0
    for s in manifest['sections']:
        require(s['vertex_start']==vertex_base and s['index_start']==index_base,'Noncontiguous section ranges')
        require(s['vertices']>0 and s['triangles']>0 and 1<=s['max_influences']<=8,'Invalid section counts')
        require(s['palette']==sorted(set(s['palette'])) and all(0<=b<230 for b in s['palette']),'Invalid bone palette')
        vertex_base+=s['vertices'];index_base+=s['triangles']*3
    require(vertex_base==manifest['output_vertices'] and index_base==manifest['triangles']*3,'Section coverage mismatch')
    records=[]
    for name in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']:
        b=(buffers/name).read_bytes();info=manifest['files'][name]
        require(len(b)==info['bytes'] and hashlib.sha256(b).hexdigest()==info['sha256'],'Changed encoded buffer')
        records.append(b)
    bones=json.loads(skeleton.read_text())['meshes'][0]['bones'];used=set()
    for s in manifest['sections']:
        require(0<=s['material']<9,'Reference has nine material slots')
        used.update(s['palette'])
    active=set(used)
    for bone in sorted(used):
        while bone>=0:
            active.add(bone);bone=bones[bone]['parent']
    active=sorted(active)
    stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL
    lod=(b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(230))+struct.pack('<i',len(manifest['sections']))
         +b''.join(section(s) for s in manifest['sections'])+array16(active)+struct.pack('<I',len(stream))+stream)
    position=np.load(buffers/'expected.npz')['positions'].astype('f8');lo,hi=position.min(0),position.max(0);origin=(lo+hi)/2;extent=(hi-lo)/2
    bounds=struct.pack('<7d',*origin,*extent,float(np.linalg.norm(extent)))
    results=[];changed={}
    for chunk,(sha,shift) in SOURCES.items():
        source=(raw/'chunks'/chunk).read_bytes();require(hashlib.sha256(source).hexdigest()==sha,'Unexpected source chunk')
        start,end=32898+shift,15761184+shift
        require(source[end-54:end]==STREAM_TAIL,'Nonempty derived/morph/cloth buffers need explicit regeneration')
        require(len(source)-end==100 and source[-4:]==bytes.fromhex('c1832a9e'),'Unexpected native package tail')
        require(struct.unpack_from('<I',source,34355+shift)[0]==end-(34359+shift),'Unexpected original streamed byte count')
        require(source[start:start+474]==b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(230)),'Unexpected cooked/required-bone flags')
        header_size=struct.unpack_from('<I',source,4)[0];export_map,bundle=struct.unpack_from('<II',source,32)
        require(header_size==8303+shift and bundle-export_map==144,'Unexpected Zen two-export layout')
        export=export_map+72;oldoffset,oldsize=struct.unpack_from('<QQ',source,export)
        require(oldoffset==6 and header_size+oldoffset+oldsize==len(source)-4,'Unexpected export extent')
        # This zero-length Nanite bulk entry uses a payload-relative serial
        # offset which points just after the LOD. Relocate even though size=0.
        bulk=struct.pack('<qqqIB3x',15752885,-1,0,0,0);bulk_at=source.find(bulk,0,header_size)
        require(bulk_at>=0 and source[:header_size].count(bulk)==1,'Unexpected bulk map')
        require(header_size+15752885==end+4,'Bulk relocation anchor differs')
        delta=len(lod)-(end-start);target=bytearray(source[:start]+lod+source[end:])
        struct.pack_into('<Q',target,export+8,oldsize+delta)
        struct.pack_into('<q',target,bulk_at,15752885+delta)
        target[8502+shift:8558+shift]=bounds
        require(target[8558+shift:start]==source[8558+shift:start],'Materials/skeleton/cooked flags changed')
        require(target[start+len(lod):]==source[end:],'Post-LOD native tail changed')
        require(header_size+oldoffset+oldsize+delta==len(target)-4,'Relocated export extent mismatch')
        changed[chunk]=bytes(target)
        results.append({'chunk':chunk,'source_sha256':sha,'output_sha256':hashlib.sha256(target).hexdigest(),'old_bytes':len(source),'new_bytes':len(target),'delta':delta,'lod_start':start,'lod_end':start+len(lod),'bounds_offset':8502+shift,'export_size_field':export+8,'old_export_size':oldsize,'new_export_size':oldsize+delta,'bulk_serial_offset_field':bulk_at,'old_bulk_serial_offset':15752885,'new_bulk_serial_offset':15752885+delta,'materials_reference_skeleton_and_native_tail_unchanged':True})
    shutil.copytree(raw,output/'raw')
    for chunk,data in changed.items():(output/'raw/chunks'/chunk).write_bytes(data)
    report={'scope':'Experimental resized geometry/skin/UV package; original Commander material references retained. NOT a finished textured Buzz mod.','source_profile':'Grounded2 WinGDK 0.316.9020.0 / reference mod','vertices':manifest['output_vertices'],'triangles':manifest['triangles'],'sections':manifest['sections'],'required_bones':230,'active_bones':active,'streamed_bytes':len(stream),'imported_bounds_origin_extent_radius_cm':[*origin,*extent,float(np.linalg.norm(extent))],'packages':results,'unrelated_chunks_unchanged':True,'game_test':'NOT RUN','full_UObject_deserialization':'Not used; measured native/Zen fields only'}
    (output/'write-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['vertices','triangles','required_bones','streamed_bytes']}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('raw',type=Path);p.add_argument('buffers',type=Path);p.add_argument('skeleton',type=Path);p.add_argument('output',type=Path);a=p.parse_args();write(a.raw,a.buffers,a.skeleton,a.output)
