#!/usr/bin/env python3
"""Audit the third-party Commander101 reference; never label it stock Max."""
import json,re,struct,sys,hashlib,collections
from pathlib import Path
import numpy as np
from compare_reference_skeletons import compare
meta_path,raw,script_names,reference,buzz,out=map(Path,sys.argv[1:]);assert not out.exists()
meta=json.loads(meta_path.read_text());ref=json.loads(reference.read_text());new=json.loads(buzz.read_text());text=script_names.read_text()
classes={int(i):n for n,i in re.findall(r'^([^\n]+):\n  global_index:\s+Some\((\d+)\)',text,re.M)}
exports=[];counts=collections.Counter();prefixes=[]
for m in meta:
 b=(raw/'chunks'/m['chunk_id']).read_bytes();assert hashlib.sha256(b).hexdigest()==m['sha256']
 begin,end=struct.unpack_from('<II',b,32)
 for offset in range(begin,end,72):
  cls=struct.unpack_from('<Q',b,offset+32)[0];name=classes.get(cls,'UNRESOLVED:'+hex(cls));counts[name]+=1;exports.append({'package':m['path'],'export_class':name,'class_script_index_hex':hex(cls)})
 if m['chunk_id'] in ('cd809abc483f179000000001','8021448bfc8c514500000001'):
  h=struct.unpack_from('<I',b,4)[0];shift=h-8303;start=h+6;stop=8502+shift;import_start=struct.unpack_from('<I',b,28)[0]
  links=[]
  for index in (1,23,25):
   encoded=struct.unpack_from('<Q',b,import_start+index*8)[0];kind=encoded>>62;payload=encoded&((1<<62)-1);package_index=payload>>32;public_hash_index=payload&0xffffffff
   assert kind==2
   target=m['imported_packages'][package_index];pat=struct.pack('<i',-index-1);hits=[i for i in range(start,stop-3) if b[i:i+4]==pat]
   links.append({'import_table_index':index,'serialized_FPackageIndex':-index-1,'target_package':target,'public_export_hash_index':public_hash_index,'prefix_byte_offsets':hits,'note':'Object-reference candidates in unversioned property bytes; property labels are not fully mapped.'})
  candidate_path=buzz.parent/'raw/chunks'/m['chunk_id'];candidate=candidate_path.read_bytes();assert candidate[start:stop]==b[start:stop]
  original_skeleton=next(x for x in ref['meshes'] if x['package']==m['path']);assert candidate[original_skeleton['offset']:original_skeleton['end']]==b[original_skeleton['offset']:original_skeleton['end']]
  prefixes.append({'chunk':m['chunk_id'],'Buzz_unversioned_property_prefix_byte_exact':True,'Buzz_native_reference_skeleton_bytes_exact':True,'property_prefix_sha256':hashlib.sha256(b[start:stop]).hexdigest(),'original_game_object_links':links})
assert all(not k.startswith('UNRESOLVED') for k in counts)
absent=[c for c in ['Skeleton','AnimSequence','AnimBlueprint','AnimBlueprintGeneratedClass','AnimMontage'] if counts[c]==0]
controls={'commander_body_vs_commander_backpack':compare(ref['meshes'][0]['bones'],ref['meshes'][1]['bones'])}
for mesh in new['meshes']:controls['commander_vs_buzz_'+mesh['package'].split('/')[-1]]=compare(ref['meshes'][0]['bones'],mesh['bones'])
scales=np.asarray([b['scale_xyz'] for b in ref['meshes'][0]['bones']]);report={'source_identity':'Commander101 is a third-party custom Max replacement, not stock Grounded2 art.','packages':len(meta),'export_class_counts':dict(counts),'no_exports_of_classes':absent,'exports':exports,'mesh_game_object_links':prefixes,'native_bone_count':230,'maximum_scale_deviation_from_unity':float(abs(scales-1).max()),'scale_observation':'Differences below 4.8e-7 are floating precision, not evidence of meaningful scaling edits.','verified_existing_comparisons':controls,'stock_Max_reference_skeleton_available':False,'stock_Max_equality':'NOT DETERMINED: original Max mesh and USkeleton packages not supplied. Equal names/import path or working animations cannot prove local rest-pose identity.','physics_warning':'Commander101 also overrides the backpack PhysicsAsset and three hair PhysicsAssets. Buzz staging preserved those mod bytes; their equality to stock physics has not been established. Pawn/capsule/movement assets are not in this mod.','recommendation':'Preserve current Buzz rig/encoder/template. Compare original-game Max mesh, backpack mesh, USkeleton and physics before final test ZIP. Original Max materials are the authoritative material-binding source. No rebuild without actual meaningful differences.','atlas_status':'Source images extracted; atlas and size-preserving four-texture mip staging written; original CUE texture mip readback works. Final atlas test ZIP paused for this assessment.','game_evidence':'User-tested Commander101 and fixed-count zMeshTest launch/render/animate. New Buzz topology/weights/materials have NOT been tested in-game.'}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'classes':dict(counts),'comparisons_passed':all(v['raw_bone_records_exact'] for v in controls.values()),'stock_Max_equality':report['stock_Max_equality']},indent=2))
