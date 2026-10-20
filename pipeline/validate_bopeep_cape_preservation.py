"""Compare exported retained lower geometry and head mask against accepted V3."""
import argparse,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);a=p.parse_args();r=a.stage;old=np.load('/workspace/mod-work/bopeep-refine-stage/geometry-v5/BoPeep-geometry-SKINNED.npz');new=np.load(r/'geometry/BoPeep-geometry-SKINNED.npz');mapping=np.load(r/'preservation.npz');kept=mapping['retained_source_faces'];n=len(kept);oi=old['indices'][kept];ni=new['indices'][:n]
assert np.array_equal(old['source_vertices'][oi],new['source_vertices'][ni]);assert np.array_equal(old['positions'][oi],new['positions'][ni]);lower=old['positions'][oi][:,:,2]<=125
for field in ['uv0','weights','joints']:assert np.array_equal(old[field][oi][lower],new[field][ni][lower]),field
oldfp=np.load('/workspace/mod-work/bopeep-refine-stage/geometry-fp-v5.npz');newfp=np.load(r/'geometry-fp.npz');assert np.array_equal(oldfp['materials'][kept],newfp['materials'][:n]);assert np.all(newfp['materials'][n:]==0);assert int((oldfp['materials']==3).sum())==int((newfp['materials']==3).sum())==2650
report={'status':'PASS','retained_original_faces':n,'retained_source_vertex_correspondence_exact':True,'all_retained_positions_exact':True,'lower_corners_geometry_UVs_weights_joint_ids_exact':int(lower.sum()),'original_head_section_membership_exact':True,'head_triangles':2650,'added_geometry_body_slot0_only':True,'runtime':'Windows pending; visible collar artifact remains in preview'};(r/'source-preservation-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
