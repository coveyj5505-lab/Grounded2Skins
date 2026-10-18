#!/usr/bin/env python3
"""Reversible static stowed visibility state; no new bones or runtime controls.

Preserve every wing vertex/face in fitted.npz and authoring archive. Exclude only
six panel components from the initial render mesh; the backpack stays visible.
No claim that the supplied solid panels physically telescope into its interior.
"""
import json,sys
from pathlib import Path
import numpy as np
source,output=map(Path,sys.argv[1:]);output.mkdir(exist_ok=False)
d={k:v.copy() for k,v in np.load(source/'fitted.npz').items()};wing=np.isin(d['component'],[0,1,12,51,62,72]);tri=d['faces']
assert np.all(d['rigid'][wing]==208)
assert np.all(d['joints'][wing][d['weights'][wing]>0]==208)
assert np.allclose(d['weights'][wing].sum(1),1)
wingfaces=wing[tri].all(1);assert not np.any(wing[tri].any(1)&~wingfaces)
old=d['face_keep'].copy();d['face_keep'] &= ~wingfaces;d['source_vertices']=np.unique(tri[d['face_keep']])
d['extended_wing_faces']=tri[wingfaces];d['wing_components']=np.array([0,1,12,51,62,72]);np.savez_compressed(output/'fitted.npz',**d)
report={'state':'stowed visibility variant','method':'Wing panels retained in hidden authoring collection; excluded from initial render mesh. Backpack remains visible.','reason':'A tested rigid orientation search did not establish containment of the large panels even in the convex backpack envelope. No shrinking, permanent deletion, or unsupported physical-fold claim.','wing_components':d['wing_components'].tolist(),'wing_vertices_preserved':int(wing.sum()),'wing_triangles_preserved':int(wingfaces.sum()),'visible_triangles':int(d['face_keep'].sum()),'visible_vertices':len(d['source_vertices']),'wing_bone':208,'wing_bone_name':'chest_JNT','original_extended_positions_unchanged':True,'visible_backpack_unchanged':True,'future_deployment':'Separate rigid panel objects preserve source topology, UVs, materials and extended locations; hinge/pivot paths, telescoping motion and runtime animation require future authoring. No runtime deployment implemented.','collision_movement_inputs_gliding':'No changes; Blender authoring only','game_test':'NOT RUN'}
(output/'wing-state.json').write_text(json.dumps(report,indent=2)+'\n')
(output/'fit-report.json').write_bytes((source/'fit-report.json').read_bytes());print(json.dumps(report))
