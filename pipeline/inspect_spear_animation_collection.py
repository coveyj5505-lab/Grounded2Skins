"""Inventory exact collected Zen exports using current global script-object IDs.
No unversioned property labels, notify timings, compressed tracks or montage
section wiring are guessed from name-table strings.
"""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'pete-extractor'))
from discover_pete import header
p=argparse.ArgumentParser();p.add_argument('collection',type=Path);p.add_argument('script_objects',type=Path);p.add_argument('output',type=Path);a=p.parse_args();assert not a.output.exists();r=json.load(open(a.collection/'animation-extraction-report.json'));assert r['status']=='EXTRACTED_READ_ONLY' and not r['missing'] and not r['errors'] and r['original_source_size_and_mtime_unchanged'];classes={int(i):n for n,i in re.findall(r'^([^\n]+):\n  global_index:\s+Some\((\d+)\)',a.script_objects.read_text(),re.M)};assert classes
for c in r['chunks']:
 f=a.collection/'chunks'/c['id'];assert f.stat().st_size==c['size'] and hashlib.sha256(f.read_bytes()).hexdigest()==c['sha256']
packages=[]
for package in r['packages']:
 b=(a.collection/'chunks'/package['chunk']).read_bytes();s=struct.unpack_from('<15I',b);h=header(b);assert h['name_map']==package['name_map'] and h['imported_packages']==package['imported_packages'];exports=[]
 for offset in range(s[8],s[9],72):
  serial,size,idx,num=struct.unpack_from('<QQII',b,offset);cls=struct.unpack_from('<Q',b,offset+32)[0];assert idx<len(h['name_map']);name=h['name_map'][idx]+('' if num==0 else '_'+str(num-1));start=s[1]+serial;payload=b[start:start+size];assert len(payload)==size
  exports.append({'object_name':name,'class':classes.get(cls,'UNRESOLVED:'+hex(cls)),'class_script_index':hex(cls),'serialized_bytes':size,'payload_sha256':hashlib.sha256(payload).hexdigest()})
 packages.append({'path':package['path'],'chunk':package['chunk'],'exports':exports,'name_map':h['name_map'],'actual_imports':h['imported_packages']})
report={'status':'HASH_VERIFIED_ZEN_EXPORT_INVENTORY','packages':packages,'package_count':len(packages),'decoded_bytes':r['decoded_bytes'],'original_collection_complete':True,'script_object_source':str(a.script_objects),'script_object_sha256':hashlib.sha256(a.script_objects.read_bytes()).hexdigest(),'scope':'Actual serialized export inventory resolved with the supplied current-build global script-object IDs; not a full UObject property or compressed-animation decode','unresolved':['Montage section-to-sequence wiring and per-track timing','Sequence duration, compression and bone pose tracks','Notify frames/properties and root-motion settings','Safe cosmetic-only adaptation onto Willow without gameplay socket/timing changes']};a.output.write_text(json.dumps(report,indent=2)+'\n')
for package in packages:
 print(package['path'].split('/')[-1],[(x['object_name'],x['class']) for x in package['exports']])
