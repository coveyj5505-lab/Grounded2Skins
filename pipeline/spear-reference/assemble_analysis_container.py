"""Offline analysis container from already hash-verified collected animation chunks.
Never install this container into the game; original paths/bytes are preserved.
"""
from pathlib import Path
import argparse,json,struct,sys,shutil,hashlib,subprocess,os
from cityhash import CityHash64
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pete-extractor'))
from discover_pete import header
p=argparse.ArgumentParser();p.add_argument('collection',type=Path);p.add_argument('baseline',type=Path);p.add_argument('output',type=Path);p.add_argument('global_input',type=Path);p.add_argument('--report',default='animation-extraction-report.json');a=p.parse_args();r=a.collection;raw=a.output/'raw';(raw/'chunks').mkdir(parents=True,exist_ok=False);report=json.load(open(r/a.report));paths={};entries={}
for c in report['chunks']:
 f=r/'chunks'/c['id'];assert hashlib.sha256(f.read_bytes()).hexdigest()==c['sha256'];shutil.copyfile(f,raw/'chunks'/c['id'])
for package in report['packages']:
 cid=package['chunk'];shutil.copyfile(r/'chunks'/cid,raw/'chunks'/cid);paths[cid]='../../../Augusta/Content/'+package['path'][6:]+'.uasset';ident=int.from_bytes(bytes.fromhex(cid[:16]),'little');assert CityHash64(package['path'].lower().encode('utf-16-le'))==ident
 entries[ident]=[CityHash64(n.lower().encode('utf-16-le')) for n in header((r/'chunks'/cid).read_bytes())['imported_packages']]
entries=dict(sorted(entries.items()));store=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',store,i*16,len(imports),len(store)-i*16);store.extend(struct.pack('<'+'Q'*len(imports),*imports))
h=next((a.baseline/'chunks').glob('*00000006'));prefix=h.read_bytes()[:16];identity=CityHash64('offline-native-spear-inspection');prefix=prefix[:8]+struct.pack('<Q',identity)
b=bytearray(prefix+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(store))+store+bytes(20));b.extend(struct.pack('<qqI',len(b)+16,4,0));(raw/'chunks'/(struct.pack('<Q',identity).hex()+'00000006')).write_bytes(b);m=json.load(open(a.baseline/'manifest.json'));m['chunk_paths']=paths;(raw/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(a.output/'input').mkdir()
for f in a.global_input.glob('global.*'):shutil.copyfile(f,a.output/'input'/f.name)
print('OFFLINE PACKAGES',len(entries))

# Match the filename-derived writer identity before packing the offline container.
retoc=Path('/workspace/mod-work/bin/retoc')
probe=a.output/'identity-probe';(probe/'raw/chunks').mkdir(parents=True)
(probe/'raw/manifest.json').write_text(json.dumps(dict(m,chunk_paths={})))
tocname='NativeSpearInspect.utoc'
def pack(src,dst):
 subprocess.run([str(retoc),'pack-raw',str(src),str(dst)],check=True,env=dict(os.environ,RAYON_NUM_THREADS='4'),stdout=subprocess.DEVNULL)
pack(probe/'raw',probe/tocname)
newid=(probe/tocname).read_bytes()[56:64]
old=raw/'chunks'/(struct.pack('<Q',identity).hex()+'00000006')
data=old.read_bytes();old.unlink();(raw/'chunks'/(newid.hex()+'00000006')).write_bytes(data[:8]+newid+data[16:])
pack(raw,a.output/'input'/tocname)
assert (a.output/'input'/tocname).read_bytes()[56:64]==newid
print('Offline container identity matched:',newid.hex())
