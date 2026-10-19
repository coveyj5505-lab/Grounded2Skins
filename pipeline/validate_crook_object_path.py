"""Check actual unpacked Zen package/export names against the Lua requested object path."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from compare_stock_max import names
p=argparse.ArgumentParser();p.add_argument('unpacked_uasset',type=Path);p.add_argument('script_objects',type=Path);p.add_argument('lua',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
b=a.unpacked_uasset.read_bytes();s=struct.unpack_from('<15I',b);assert s[0]==0 and s[1]<=len(b)
n,_=names(b,60)
def mapped(index,number):
 assert index>>30==0,'Expected package-local FMappedName'
 name=n[index&0x3fffffff];return name if number==0 else name+'_'+str(number-1)
package=mapped(s[2],s[3]);assert package.startswith('/Game/')
classes={int(i):name for name,i in re.findall(r'^([^\n]+):\n  global_index:\s+Some\((\d+)\)',a.script_objects.read_text(),re.M)}
exports=[]
assert (s[9]-s[8])%72==0
for at in range(s[8],s[9],72):
 index,number=struct.unpack_from('<II',b,at+16);outer,cls=struct.unpack_from('<QQ',b,at+24)
 exports.append({'name':mapped(index,number),'class':classes.get(cls,'UNRESOLVED'),'outer_index':hex(outer)})
meshes=[x for x in exports if x['class']=='SkeletalMesh' and x['outer_index']=='0xffffffffffffffff'];assert len(meshes)==1
actual=package+'.'+meshes[0]['name']
requested=re.search(r"local assetPath='([^']+)'",a.lua.read_text()).group(1)
assert actual==requested,(actual,requested)
r={'status':'PASS','source':'Fresh retoc unpack of packaged zBoCrookAsset_P.utoc/ucas, not authoring JSON','unpacked_chunk_sha256':hashlib.sha256(b).hexdigest(),'cooked_package_summary_name':package,'cooked_exports':exports,'resolved_top_level_mesh_object_path':actual,'lua_requested_object_path':requested,'exact_match':True,'scope':'Confirms serialized package/export identity and actual global metadata class; does not prove mounted or loaded in game'}
a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
