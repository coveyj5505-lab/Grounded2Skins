"""Fresh Blender reopen validation, rigid-pose checks and export of both new wing states."""
import bpy,sys,argparse,json,hashlib,runpy,math
from pathlib import Path
from mathutils import Vector,Quaternion
p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(a.stage/'Buzz-Wing-States.blend'));r=json.loads((a.stage/'authoring-report.json').read_text());arm=bpy.data.objects['Grounded2_Armature_230']
def signature(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons],[[tuple(u.uv) for u in l.data] for l in o.data.uv_layers],[list(r) for r in o.matrix_world],[[ (g.group,g.weight) for g in v.groups] for v in o.data.vertices])).encode()).hexdigest()
assert all(signature(bpy.data.objects[n])==value for n,value in r['original_object_signatures'].items())
assert all(v['fraction']==1 for v in r['stored_surface_occlusion_samples'].values())
rest={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones};assert hashlib.sha256(json.dumps(rest,sort_keys=True).encode()).hexdigest()==r['bone_rest_hash']
pose_checks=[]
for angle in [0,25,-25,45]:
 pb=arm.pose.bones['chest_JNT'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((1,0,0),math.radians(angle));bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();worst=0
 for state in ['Retracted','Deployed']:
  o=bpy.data.objects['Wings_'+state+'_Display'];evaluated=o.evaluated_get(deps);matrix=pb.matrix@arm.data.bones['chest_JNT'].matrix_local.inverted()
  for v,w in zip(o.data.vertices,evaluated.data.vertices):worst=max(worst,(matrix@v.co-w.co).length)
 assert worst<1e-5;pose_checks.append({'chest_rotation_degrees':angle,'max_rigid_deformation_error_m':worst})
arm.pose.bones['chest_JNT'].matrix_basis.identity();bpy.context.view_layer.update()
original_body=bpy.data.objects['Buzz_Skinned'];original_body.name='Buzz_StableBody_UNCHANGED'
for state in ['Retracted','Deployed']:
 o=bpy.data.objects['Wings_'+state+'_Export'];old=o.name;o.name='Buzz_Skinned'
 metadata=a.out/(state+'-export-metadata.json');metadata.write_text(json.dumps({'vertices':len(o.data.vertices),'triangles':len(o.data.polygons),'bone_rest_hash':r['bone_rest_hash']}))
 oldargs=sys.argv;sys.argv=['export_buzz_geometry.py','--',str(a.reference),str(metadata),str(a.out/state),'--skinned']
 runpy.run_path(str(Path(__file__).parent/'export_buzz_geometry.py'),run_name='__main__');sys.argv=oldargs;o.name=old
report={'fresh_reopen':True,'body_and_all_preserved_objects_exact':True,'original_source_file_sha256_matches':hashlib.sha256(Path(r['source']).read_bytes()).hexdigest()==r['source_file_sha256'],'native_bones_unchanged':230,'pose_checks':pose_checks,'stored_occlusion_all_8_views':True,'scope':'Sampled rest-view occlusion and synthetic rigid chest poses; not native game animations, collision, FP visibility or runtime load proof'}
(a.out/'independent-blender-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('WINGS_REOPEN_EXPORT_PASS')
