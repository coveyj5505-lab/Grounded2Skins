"""Read original packed source images/material links without changing the blend."""
import bpy,json,sys,hashlib
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
obj=bpy.data.objects['Buzz_Skinned'];report=[]
for i,mat in enumerate(obj.data.materials):
 nodes=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
 assert len(nodes)==1,(mat.name,[n.name for n in nodes])
 node=nodes[0];image=node.image;assert image.packed_file
 data=bytes(image.packed_file.data);path=out/f'material-{i}.image';path.write_bytes(data)
 bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');links=[l for l in mat.node_tree.links if l.to_node==bsdf and l.to_socket.name=='Base Color'];assert len(links)==1 and links[0].from_node==node
 assert node.extension=='REPEAT'
 report.append({'material_slot':i,'name':mat.name,'image':image.name,'file':path.name,'width':image.size[0],'height':image.size[1],'sha256':hashlib.sha256(data).hexdigest(),'extension':node.extension,'color_space':image.colorspace_settings.name})
(out/'materials.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
