"""Atlas UVs on a new playable mesh; preserve all source and review copies."""
import bpy,json,sys
from pathlib import Path
import numpy as np
atlas,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
old=bpy.data.objects['Woody_Skinned'];arm=old.find_armature();mesh=old.data.copy();o=old.copy();o.data=mesh;bpy.context.collection.objects.link(o);old.name='Woody_PreAtlas_Preserved';old.hide_render=True;old.hide_set(True);o.name='Woody_Skinned'
layout=json.loads((atlas/'atlas-layout.json').read_text());part={'22_hat_0+':'Hat','22_hat_0':'Hat','22_boots_0':'Boots','22_clothes_0':'Clothes','22_shirt_0':'Shirt','24_hair_0':'Hair','24_skin_0':'Head','New ':'Eyes','-Pull String.a':'White'}
uv=mesh.uv_layers.active
# Existing eye geometry consists of upper/lower components; use one projection
# per complete left/right eye, not separate irises on every component.
eye_ids={v for p in mesh.polygons if mesh.materials[p.material_index].name=='New ' for v in p.vertices};p=np.asarray([v.co[:] for v in mesh.vertices]);eye_uv={}
for sign in [-1,1]:
 ids=sorted(i for i in eye_ids if (p[i,0]>=0)==(sign>0));xy=p[ids][:,[0,2]];lo=xy.min(0);hi=xy.max(0)
 for i,q in zip(ids,(xy-lo)/(hi-lo)):eye_uv[i]=q
for poly in mesh.polygons:
 tile=part[mesh.materials[poly.material_index].name];x,y,w,h=layout['tiles'][tile]
 for li in poly.loop_indices:
  vid=mesh.loops[li].vertex_index;u,v=eye_uv[vid] if tile=='Eyes' else (.5,.5) if tile=='White' else uv.data[li].uv
  uv.data[li].uv=((x+float(u)*w)/4096,1-(y+(1-float(v))*h)/4096)
 poly.material_index=0
mesh.materials.clear();mat=bpy.data.materials.new('Woody_Private_Atlas_Preview');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');im=bpy.data.images.load(str(atlas/'Woody-basecolor-atlas.png'));im.pack();im.use_fake_user=True;tex.image=im;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Roughness'].default_value=.8;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);mesh.materials.append(mat)
assert len(o.vertex_groups)==188 and not mesh.shape_keys
mesh.calc_loop_triangles();np.savez_compressed(out/'expected.npz',positions=[v.co[:] for v in mesh.vertices],indices=[t.vertices[:] for t in mesh.loop_triangles],loop_uv=[d.uv[:] for d in uv.data]);(out/'atlas-binding.json').write_text(json.dumps({'layout':layout,'source_materials':part,'originals_preserved':True,'runtime':'NOT TESTED'},indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Woody-Pete-gameplay.blend'),compress=True)
