"""Incremental source-informed torso/cape correction; bones, hands and original scene preserved."""
import bpy,sys,argparse,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(exist_ok=False);bpy.ops.wm.open_mainfile(filepath=str(a.source))
old=bpy.data.objects['BoPeep_Skinned'];src=bpy.data.objects['BoPeep_Body'];arm=old.find_armature();sa=src.find_armature();rest={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones};assert len(rest)==192
before=np.array([tuple(v.co) for v in old.data.vertices]);points=before.copy();groups=[{src.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0} for v in src.data.vertices];sw={b.name:np.array(sa.matrix_world@b.head_local) for b in sa.data.bones};nw={b.name:np.array(b.head_local) for b in arm.data.bones}
spec={'e_root_m':('Hips_JNT','e_spine1_m','spine1_JNT'),'e_spine1_m':('spine1_JNT','e_chest_m','spine3_JNT'),'e_chest_m':('spine3_JNT','e_neck_m','neck1_JNT'),'e_neck_m':('neck1_JNT','e_head_m','head_JNT')};transforms={};ratios={}
for name,(dest,end,dend) in spec.items():
 av=sw[end]-sw[name];bv=nw[dend]-nw[dest];u=av/np.linalg.norm(av);ratio=np.linalg.norm(bv)/(np.linalg.norm(av)*.25);newratio=np.clip(ratio,.85,1.2);rot=np.array(Vector(av).rotation_difference(Vector(bv)).to_matrix());oldm=rot@(np.eye(3)+(ratio-1)*np.outer(u,u))*.25;newm=rot@(np.eye(3)+(newratio-1)*np.outer(u,u))*.25;transforms[name]=(newm-oldm,sw[name]);ratios[name]={'old':float(ratio),'new':float(newratio)}
cape=[i for i,g in enumerate(groups) if any(n.startswith('e_cape') for n in g)];hands=[i for i,g in enumerate(groups) if any('finger' in n or n.startswith('e_wrist') for n in g)];face=[i for i,g in enumerate(groups) if g.get('e_head_m',0)>=.9];protected=set(hands+face)
for v in src.data.vertices:
 i=v.index
 if i in protected or i in cape:continue
 pos=np.array(src.matrix_world@v.co)
 for name,w in groups[i].items():
  if name in transforms:
   delta,origin=transforms[name];points[i]+=w*(delta@(pos-origin))
# Correct the measured 1.469 cape elongation, keeping its top attachment fixed.
capetop=before[cape,2].max();ratio=1/ratios['e_chest_m']['old'];points[cape,2]=capetop+(before[cape,2]-capetop)*ratio
progress=np.clip((capetop-points[cape,2])/(capetop-points[cape,2].min()),0,1);points[cape,0]*=(1-.18*progress)
o=old.copy();o.data=old.data.copy();bpy.context.collection.objects.link(o);old.name='BoPeep_VisibleBaseline_V2_PRESERVED';old.hide_render=True;old.hide_set(True);o.name='BoPeep_Skinned'
oldnormals=[tuple(l.normal) for l in o.data.loops]
for v,q in zip(o.data.vertices,points):v.co=q
o.data.update();o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops));newnormals=[tuple(l.normal) for l in o.data.loops];changed=np.linalg.norm(points-before,axis=1)>1e-8;o.data.normals_split_custom_set([newnormals[i] if changed[l.vertex_index] else oldnormals[i] for i,l in enumerate(o.data.loops)])
assert np.array_equal(points[list(protected)],before[list(protected)])
assert rest=={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
assert [tuple(x.uv) for x in o.data.uv_layers.active.data]==[tuple(x.uv) for x in old.data.uv_layers.active.data]
assert [[(g.group,g.weight) for g in v.groups] for v in o.data.vertices]==[[(g.group,g.weight) for g in v.groups] for v in old.data.vertices]
r={'source':str(a.source),'source_file_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'vertices':len(points),'triangles':len(o.data.polygons),'bone_rest_hash':hashlib.sha256(json.dumps(rest,sort_keys=True).encode()).hexdigest(),'native_bones_unchanged':192,'all_weights_UVs_topology_unchanged':True,'hands_and_pure_head_positions_exact':len(protected),'changed_vertices':int(changed.sum()),'torso_longitudinal_ratio_correction':ratios,'cape_old_bounds':[before[cape].min(0).tolist(),before[cape].max(0).tolist()],'cape_new_bounds':[points[cape].min(0).tolist(),points[cape].max(0).tolist()],'cape':'Top fixed; source vertical aspect restored; hem tucked18%. Original stiff spine3 weighting retained; no cloth simulation claim.','runtime':'NOT TESTED; native animated stance may still contribute to apparent hunch. No animation or bone changes.'}
np.savez_compressed(a.out/'expected.npz',positions=points,old_positions=before,changed=changed,protected=np.array(sorted(protected)))
(a.out/'correction-report.json').write_text(json.dumps(r,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a.out/'BoPeep-Proportions-V3.blend'),compress=True);print('BOPEEP_V3_SHAPE_PASS',r['changed_vertices'])
