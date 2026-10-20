#!/usr/bin/env python3
"""Bake source repeat textures into a temporary opaque atlas; reuse proven slot0.

No new shader or game skeleton. Source Blender and its eight material slots stay
untouched. Repeat UV islands remain continuous (no modulo applied to vertices).
Native UV V runs down the PNG, with tangent handedness adjusted accordingly.
"""
import sys,json,hashlib,argparse
from pathlib import Path
import numpy as np
from PIL import Image
from native_buffers import validate,skeleton_signature
parser=argparse.ArgumentParser();parser.add_argument('geometry',type=Path);parser.add_argument('images',type=Path);parser.add_argument('reference',type=Path);parser.add_argument('out',type=Path);parser.add_argument('--max-repeat',type=int,default=4);args=parser.parse_args();geometry,images,reference,out=args.geometry,args.images,args.reference,args.out;assert 1<=args.max_repeat<=32;out.mkdir(exist_ok=False)
d={k:v.copy() for k,v in np.load(geometry).items()};sources=json.loads((images/'materials.json').read_text());assert len(sources)==8
size=4096;cols=4;rows=2;cw=size//cols;ch=size//rows;gutter=16
atlas=Image.new('RGBA',(size,size));records=[];new={k:[] for k in ['positions','normals','tangents','signs','colors','uv0','joints','weights','source_vertices']};triangles=[];source_materials=[];base=0
for item in sources:
 slot=item['material_slot'];selected=np.flatnonzero(d['materials']==slot);oldtri=d['indices'][selected];used,inverse=np.unique(oldtri,return_inverse=True)
 uv=d['uv0'][used] if len(used) else np.array([[0.,0.],[1.,1.]])
 lower=np.floor(uv.min(0));upper=np.ceil(uv.max(0));upper=np.maximum(upper,lower+1);repeat=(upper-lower).astype(int);assert np.all(repeat<=args.max_repeat)
 im=Image.open(images/item['file']).convert('RGBA');assert im.getextrema()[3]==(255,255)
 pattern=Image.new('RGBA',(im.width*int(repeat[0]),im.height*int(repeat[1])))
 for y in range(repeat[1]):
  for x in range(repeat[0]):pattern.paste(im,(x*im.width,y*im.height))
 patch=pattern.resize((cw-2*gutter,ch-2*gutter),Image.Resampling.LANCZOS)
 # Extruded edges isolate atlas cells through the first several mip levels.
 pixels=np.asarray(patch);tile=Image.fromarray(np.pad(pixels,((gutter,gutter),(gutter,gutter),(0,0)),mode='edge'))
 col,row=slot%cols,slot//cols;atlas.paste(tile,(col*cw,row*ch))
 mapped=np.column_stack([(col*cw+gutter+(uv[:,0]-lower[0])/repeat[0]*(cw-2*gutter))/size,
                         (row*ch+gutter+(upper[1]-uv[:,1])/repeat[1]*(ch-2*gutter))/size])
 if len(used):
  for key in new:
   new[key].append(mapped.astype('f4') if key=='uv0' else (-d[key][used] if key=='signs' else d[key][used] if key!='source_vertices' else used.astype('u4')))
  triangles.append(inverse.reshape(-1,3).astype('u4')+base);source_materials.extend([slot]*len(selected));base+=len(used)
 records.append(dict(item,source_uv_bounds=[lower.tolist(),upper.tolist()],repeat=repeat.tolist(),atlas_cell=[col*cw,row*ch,cw,ch],gutter=gutter,triangles=len(selected),render_vertices=len(used)))
mesh={k:np.concatenate(v) for k,v in new.items()};mesh.update(indices=np.concatenate(triangles),materials=np.zeros(len(source_materials),dtype='u2'),source_materials=np.array(source_materials,dtype='u2'),material_count=np.asarray(9),skeleton_signature=d['skeleton_signature'])
validate(mesh,skeleton_signature(reference));atlas.save(out/'Buzz-basecolor-atlas.png');np.savez_compressed(out/'Buzz-atlas-SKINNED.npz',**mesh)
report={'method':'Opaque atlas using original source textures, repeat-aware affine UV bounds, gutter16; all cooked faces use existing material slot0','width':size,'height':size,'vertices':base,'triangles':len(source_materials),'original_render_vertices':len(d['positions']),'original_source_material_slots':8,'effective_Unreal_materials':1,'parent_material':'/Game/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Apparel01','native_uv_convention':'PNG top-left; V reflected from Blender source; tangent signs inverted to match','original_source_blender_modified':False,'materials':records,'texture_sha256':hashlib.sha256((out/'Buzz-basecolor-atlas.png').read_bytes()).hexdigest(),'visual_limitations':['One shared existing opaque character material, no separate eye/skin shader','UV repeat regions share atlas space; some details downsampled','High mip levels blend atlas cells; distant colors can bleed','Original game material parameter/parent shader table not present; runtime color/shading still requires Windows test'],'game_test':'NOT RUN'}
(out/'atlas-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['vertices','triangles','effective_Unreal_materials']}))
