import bpy,json,sys
from pathlib import Path
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
obj=next(o for o in bpy.data.objects if o.type=='MESH');arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
m=obj.data;m.calc_loop_triangles()
np.savez(out/'source.npz',positions=np.array([v.co[:] for v in m.vertices]),indices=np.array([t.vertices[:] for t in m.loop_triangles]),materials=np.array([t.material_index for t in m.loop_triangles]))
bones=[{'index':i,'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'matrix':[list(row) for row in b.matrix_local]} for i,b in enumerate(arm.data.bones)]
(out/'bones.json').write_text(json.dumps(bones,indent=2)+'\n')
print('Landmark inputs saved',len(m.vertices),len(bones),flush=True)
