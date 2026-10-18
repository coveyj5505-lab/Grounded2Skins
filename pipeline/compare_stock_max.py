#!/usr/bin/env python3
"""Read only selected ORIGINAL game packages; compare to recovered mod bones.

Input is the output of the targeted extractor, not the mod container. Native
structures are validated without guessing UObject mappings. No rig is changed.
"""
import argparse,json,struct,hashlib
from pathlib import Path
from extract_reference_skeleton import extract
from compare_reference_skeletons import compare


def names(data,pos):
 count=struct.unpack_from('<I',data,pos)[0];pos+=4
 if count==0:return [],pos
 assert 0<count<100000
 size,_=struct.unpack_from('<IQ',data,pos);pos+=12+count*8
 lengths=struct.unpack_from('>'+str(count)+'H',data,pos);pos+=count*2;start=pos;result=[]
 for raw in lengths:
  length=(raw&0x7fff)*(2 if raw&0x8000 else 1);result.append(data[pos:pos+length].decode('utf-16-le' if raw&0x8000 else 'utf-8'));pos+=length
 assert pos-start==size
 return result,pos


def run(folder,reference,out):
 assert not out.exists();report=json.loads((folder/'extraction-report.json').read_text(encoding='utf-8-sig'))
 assert report['source'].replace('\\','/').split('/')[-1].casefold()=='augusta-wingdk.utoc','Must originate from ORIGINAL game index, not mod'
 assert report['source_size_and_mtime_unchanged'] and not report['missing_targets']
 baseline=json.loads(reference.read_text())['meshes'][0]['bones'];assets=[];bones_out=[]
 for entry in report['chunks']:
  if entry['type']!='ExportBundleData':continue
  raw=(folder/'chunks'/entry['id']).read_bytes();assert len(raw)==entry['size'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
  summary=struct.unpack_from('<15I',raw);assert summary[0]==0,'Versioned Zen header needs a separate checked decoder'
  local,_=names(raw,60);imports,pos=names(raw,summary[12]);numbers=struct.unpack_from('<'+'i'*len(imports),raw,pos);imports=[v if n==0 else v+'_'+str(n-1) for v,n in zip(imports,numbers)]
  item={'path':entry['path'],'chunk':entry['id'],'sha256':entry['sha256'],'imported_packages':imports}
  leaf=entry['path'].replace('\\','/').split('/')[-1]
  if leaf in ['SK_Male_Teen_01.uasset','SK_Male_Teen_01_w_BackPack.uasset','SK_Male_Teen_01_Skeleton.uasset']:
   result=extract(raw,local);result['package']=entry['path'];result['chunk_sha256']=entry['sha256'];bones_out.append(result);item['compared_to_Commander101']=compare(baseline,result['bones'])
  else:
   item['note']='Dependency/header inventory only, not mapped property/shader/physics-shape deserialization'
   if leaf.startswith('MI_'):item['parameter_name_candidates_not_a_verified_binding']=[n for n in local if any(s in n.lower() for s in ['texture','color','diffuse','albedo','normal'])]
  assets.append(item)
 assert len(bones_out)==3,'Expected original Max body/backpack meshes and USkeleton'
 out.mkdir();(out/'stock-reference-skeletons.json').write_text(json.dumps({'meshes':bones_out},indent=2)+'\n')
 result={'source':'Original Augusta-WinGDK game container, as recorded by read-only extractor','assets':assets,'scope':'Bone names/order/parents/local rest poses compared. Physics and material parameters are inventoried, not fully deserialized.','game_runtime_compatibility':'Still requires Windows test; equality alone does not test all animations.'}
 (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({x['path']:x['compared_to_Commander101']['rest_pose_equal_within_tolerance'] for x in assets if 'compared_to_Commander101' in x},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('selected_original_assets',type=Path);p.add_argument('reference_json',type=Path);p.add_argument('new_output',type=Path);a=p.parse_args();run(a.selected_original_assets,a.reference_json,a.new_output)
