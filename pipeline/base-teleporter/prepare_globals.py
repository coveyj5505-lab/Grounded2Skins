"""Resolve native symbol IDs from the collected, hash-verified uncompressed global pair."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'teleport-marker-collector/support'))
from discover_pete import names


def prepare(collection, output):
    report=json.loads((collection/'buildable-teleport-report.json').read_text())
    for item in report['global_files']:
        path=(collection/item['file']).resolve()
        if not path.is_relative_to(collection.resolve()):raise ValueError('Global path escapes collection')
        raw=path.read_bytes()
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Global file hash/size mismatch')
    root=collection/'global';toc=(root/'global.utoc').read_bytes();cas=(root/'global.ucas').read_bytes()
    if toc[:16]!=b'-==--==--==--==-' or toc[16]!=8 or toc[80]&2:raise ValueError('Unsupported/encrypted global TOC')
    count,blocks=struct.unpack_from('<II',toc,24)
    if struct.unpack_from('<I',toc,36)[0]!=0:raise ValueError('This inspector requires uncompressed global metadata')
    block_size=struct.unpack_from('<I',toc,44)[0]
    if blocks*block_size>32*1024*1024:raise ValueError('Global metadata exceeds inspector budget')
    start=144+count*22+4*struct.unpack_from('<I',toc,84)[0]+4*struct.unpack_from('<I',toc,96)[0]
    virtual=bytearray(blocks*block_size)
    for i in range(blocks):
        block=toc[start+12*i:start+12*(i+1)]
        off=int.from_bytes(block[:5],'little');compressed=int.from_bytes(block[5:8],'little');size=int.from_bytes(block[8:11],'little')
        if len(block)!=12 or compressed!=size or block[11] or size>block_size or off+size>len(cas):raise ValueError('Invalid/unsupported compression block')
        virtual[i*block_size:i*block_size+size]=cas[off:off+size]
    chunks=[]
    for i in range(count):
        cid=toc[144+12*i:156+12*i];entry=toc[144+count*12+10*i:154+count*12+10*i]
        if cid[-1]!=5:continue
        off=int.from_bytes(entry[:5],'big');size=int.from_bytes(entry[5:],'big')
        if off+size>len(virtual):raise ValueError('ScriptObjects range')
        chunks.append(virtual[off:off+size])
    if len(chunks)!=1:raise ValueError('Expected one ScriptObjects chunk')
    raw=chunks[0];strings,pos=names(raw,0);n=struct.unpack_from('<I',raw,pos)[0];pos+=4
    if pos+n*32!=len(raw):raise ValueError('Script object table size mismatch')
    entries={}
    for i in range(n):
        name,number,gid,outer,cdo=struct.unpack_from('<IIQQQ',raw,pos+i*32)
        value=strings[name&0x3fffffff]
        if number:value+='_'+str(number-1)
        if gid in entries:raise ValueError('Duplicate script object ID')
        entries[gid]=(value,outer)
    def full(gid,seen=()):
        if gid in seen or len(seen)>32:raise ValueError('Script object outer cycle')
        name,outer=entries[gid]
        return full(outer,seen+(gid,))+'/'+name if outer in entries else name
    result={f'{gid:016x}':full(gid) for gid in entries}
    text=json.dumps(result,indent=2)
    if output.exists() and json.loads(output.read_text())!=result:raise ValueError('Refusing to overwrite different derived symbol map')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(text)
    print('Resolved',len(result),'native script objects')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('collection',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();prepare(a.collection,a.output or a.collection/'global/script-object-paths.json')
