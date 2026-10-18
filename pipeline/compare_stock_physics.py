#!/usr/bin/env python3
"""Compare Zen physics export inventories without inventing UObject mappings."""
import argparse,hashlib,json,struct
from collections import Counter
from pathlib import Path
from compare_stock_max import names

CLASSES={0x6ce65259da8a872c:'PhysicsAsset',0x5853f63f596ff202:'PhysicsConstraintTemplate',0x7e606950971db15a:'SkeletalBodySetup'}

def inventory(raw):
 summary=struct.unpack_from('<15I',raw);assert summary[0]==0
 local,_=names(raw,60);exports=[]
 for offset in range(summary[8],summary[9],72):
  serial,size,idx,num=struct.unpack_from('<QQII',raw,offset);cls=CLASSES[struct.unpack_from('<Q',raw,offset+32)[0]]
  payload=raw[summary[1]+serial:summary[1]+serial+size];assert len(payload)==size
  item={'class':cls,'object_name':local[idx]+('' if num==0 else '_'+str(num-1)),'serialized_size':size,'payload_sha256':hashlib.sha256(payload).hexdigest()}
  # Identical observed 114-byte layout across both supplied containers. These
  # are structural FName candidates, not a claimed mapped BoneName property.
  if cls=='SkeletalBodySetup' and size==114 and payload[:15]==bytes.fromhex('02020d020103020301000000801130') and payload[71:73]==b'\x01\x03':
   ni,number=struct.unpack_from('<II',payload,73);assert ni<len(local) and number==0
   item['bone_FName_candidate']=local[ni]
   item['pre_FName_numeric_region_sha256']=hashlib.sha256(payload[15:71]).hexdigest()
  exports.append(item)
 return {'export_counts':dict(Counter(e['class'] for e in exports)),'name_map':local,'exports':exports}

def run(folder,commander,out):
 assert not out.exists();r=json.loads((folder/'extraction-report.json').read_text(encoding='utf-8-sig'))
 assert r['source'].replace('\\','/').split('/')[-1].casefold()=='augusta-wingdk.utoc' and r['source_size_and_mtime_unchanged'] and not r['missing_targets']
 assert r['package_count']==1 and len(r['chunks'])==1;e=r['chunks'][0];b=(folder/'chunks'/e['id']).read_bytes();assert len(b)==e['size'] and hashlib.sha256(b).hexdigest()==e['sha256']
 cb=commander.read_bytes();assert hashlib.sha256(cb).hexdigest()=='117ad3a6adad978d335fed7b036a2c95ee20b90aca0b4801527386fe8a9830f6'
 stock,mod=inventory(b),inventory(cb)
 a={e['bone_FName_candidate']:e for e in stock['exports'] if 'bone_FName_candidate' in e};c={e['bone_FName_candidate']:e for e in mod['exports'] if 'bone_FName_candidate' in e}
 report={'stock_package':e['path'],'stock_sha256':e['sha256'],'stock':stock,'Commander101':mod,'body_bone_FName_candidates_only_in_stock':sorted(a.keys()-c.keys()),'body_bone_FName_candidates_only_in_Commander101':sorted(c.keys()-a.keys()),'shared_body_numeric_regions':{n:{'byte_equal':a[n]['pre_FName_numeric_region_sha256']==c[n]['pre_FName_numeric_region_sha256']} for n in sorted(a.keys()&c.keys())},'scope':'Actual export classes/counts and payload bytes, plus guarded structural FName candidates. No full mapped body/constraint shape, collision response, mass, limits or runtime simulation deserialization. Different export counts prove these are not equivalent serialized physics setups.','decision':'Retain existing Buzz baseline unchanged. Do not describe Commander physics as stock. Any stock-physics reference change must be a separate validated revision; do not blindly remove its PhysicsAsset dependency.'}
 out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['body_bone_FName_candidates_only_in_stock','body_bone_FName_candidates_only_in_Commander101']}));print(stock['export_counts'],mod['export_counts'])
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('stock_folder',type=Path);p.add_argument('commander_physics_chunk',type=Path);p.add_argument('new_output',type=Path);a=p.parse_args();run(a.stock_folder,a.commander_physics_chunk,a.new_output)
