#!/usr/bin/env python3
"""Size-preserving native texture payload replacement, only four Max paths.

Keep original UE5.6 headers, flags, imports, dimensions, formats, mip records,
streaming/inline locations and Zen export/bulk metadata. Replace encoded bytes
inside the new mod staging copy; never edit original game or reference files.
"""
import sys,json,hashlib,struct,shutil
from pathlib import Path
import numpy as np
from PIL import Image
import ispc_texcomp


def layout(data):
 header=struct.unpack_from('<I',data,4)[0];bulk_end=struct.unpack_from('<I',data,24)[0]
 hits=[]
 for fmt in ['PF_DXT5','PF_DXT1','PF_BC5']:
  needle=fmt.encode()+b'\0';pos=0
  while (pos:=data.find(needle,pos))>=0:
   if pos>=32 and struct.unpack_from('<i',data,pos-4)[0]==len(needle):hits.append((pos,fmt))
   pos+=1
 assert len(hits)==1
 pos,fmt=hits[0];start=pos-32;assert data[start:start+16]==bytes(16)
 width,height,slices=struct.unpack_from('<iiI',data,start+16);assert width==height and slices==1
 q=pos+len(fmt)+1;first,count=struct.unpack_from('<ii',data,q);q+=8;assert first==0 and count==width.bit_length()
 map_at=bulk_end-count*32;assert struct.unpack_from('<q',data,map_at-8)[0]==count*32
 records=[]
 for i in range(count):
  offset,duplicate,size,flags,cooked=struct.unpack_from('<qqqIB3x',data,map_at+i*32);assert duplicate==-1 and cooked==0
  assert struct.unpack_from('<i',data,q)[0]==i;q+=4
  inline=bool(flags&0x40)
  if inline:assert offset+header==q;dest=q;q+=size
  else:assert flags&0x100;dest=offset
  x,y,z=struct.unpack_from('<iii',data,q);q+=12;assert (x,y,z)==(max(1,width>>i),max(1,height>>i),1)
  assert size==max(1,(x+3)//4)*max(1,(y+3)//4)*(8 if fmt=='PF_DXT1' else 16)
  records.append({'level':i,'width':x,'height':y,'bytes':size,'inline':inline,'offset':dest,'flags':flags})
 assert struct.unpack_from('<i',data,q)[0]==0;q+=4
 assert q+12==len(data) and data[-4:]==bytes.fromhex('c1832a9e')
 return {'width':width,'height':height,'format':fmt,'header_bytes':header,'platform_start':start,'platform_end':q,'mips':records}


def solid_bc1(rgb):
 r,g,b=rgb;c=(round(r*31/255)<<11)|(round(g*63/255)<<5)|round(b*31/255)
 return struct.pack('<HHI',c,c,0)


def solid_bc5(red=128,green=128):
 # BC5 is two BC4 blocks. Equal endpoints + zero selectors are constant.
 # Do not pass an interleaved RGBA surface to the ISPC BC5 wrapper: that
 # path produced alternating128/255 columns in the runtime-tested V1.
 return bytes([red,red])+bytes(6)+bytes([green,green])+bytes(6)


def encode(image,fmt):
 x,y=image.size;px,py=max(4,x),max(4,y)
 if (x,y)!=(px,py):image=Image.fromarray(np.pad(np.asarray(image),((0,py-y),(0,px-x),(0,0)),mode='edge'))
 surf=ispc_texcomp.RGBASurface(image.tobytes(),px,py)
 if fmt=='PF_DXT5':payload=ispc_texcomp.compress_blocks_bc3(surf)
 elif fmt=='PF_BC5':payload=ispc_texcomp.compress_blocks_bc5(surf)
 else:raise ValueError(fmt)
 assert len(payload)==max(1,(x+3)//4)*max(1,(y+3)//4)*16
 return payload


def write(raw,metadata,atlas,out):
 assert not out.exists();meta=json.loads(metadata.read_text());changes={};reports=[]
 suffixes={'T_Max_Apparel_01_C.uasset':'atlas base color','T_Max_Apparel_01_N.uasset':'neutral tangent normal','T_Max_Apparel_01_RMA.uasset':'temporary matte plastic RMA','T_Max_Apparel_01_SSS.uasset':'no subsurface mask'}
 base=Image.open(atlas).convert('RGBA');assert base.size==(4096,4096)
 for obj in meta:
  leaf=obj['path'].split('/')[-1]
  if leaf not in suffixes:continue
  cid=obj['chunk_id'];source=(raw/'chunks'/cid).read_bytes();assert hashlib.sha256(source).hexdigest()==obj['sha256']
  info=layout(source);bulk_id=cid[:16]+'00000002';oldbulk=(raw/'chunks'/bulk_id).read_bytes();target=bytearray(source);bulk=bytearray(oldbulk);expected=[]
  for m in info['mips']:
   wh=(m['width'],m['height']);fmt=info['format']
   if leaf.endswith('_C.uasset'):assert fmt=='PF_DXT5';im=base.resize(wh,Image.Resampling.LANCZOS);payload=encode(im,fmt)
   elif leaf.endswith('_N.uasset'):assert fmt=='PF_BC5';payload=solid_bc5()*(m['bytes']//16)
   else:
    assert fmt=='PF_DXT1';payload=solid_bc1((200,0,255) if '_RMA.' in leaf else (0,0,0))*(m['bytes']//8)
   assert len(payload)==m['bytes'];dest=target if m['inline'] else bulk;a=m['offset'];assert 0<=a<=len(dest)-len(payload);dest[a:a+len(payload)]=payload
   expected.append(dict(m,sha256=hashlib.sha256(payload).hexdigest()))
  assert len(target)==len(source) and len(bulk)==len(oldbulk)
  assert target[:info['header_bytes']]==source[:info['header_bytes']]
  # Every changed byte must lie within an explicitly measured mip range.
  mask=np.zeros(len(source),bool)
  for m in info['mips']:
   if m['inline']:mask[m['offset']:m['offset']+m['bytes']]=True
  assert np.array_equal(np.frombuffer(target,dtype='u1')[~mask],np.frombuffer(source,dtype='u1')[~mask])
  bulk_ranges=np.zeros(len(oldbulk),bool)
  for m in info['mips']:
   if not m['inline']:bulk_ranges[m['offset']:m['offset']+m['bytes']]=True
  assert bulk_ranges.all()
  changes[cid]=bytes(target);changes[bulk_id]=bytes(bulk)
  reports.append({'path':obj['path'],'chunk':cid,'bulk_chunk':bulk_id,'purpose':suffixes[leaf],**info,'mips':expected,'original_export_sha256':obj['sha256'],'new_export_sha256':hashlib.sha256(target).hexdigest(),'original_bulk_sha256':hashlib.sha256(oldbulk).hexdigest(),'new_bulk_sha256':hashlib.sha256(bulk).hexdigest(),'metadata_outside_mip_bytes_unchanged':True})
 assert len(reports)==4;shutil.copytree(raw,out/'raw')
 for cid,payload in changes.items():(out/'raw/chunks'/cid).write_bytes(payload)
 report={'strategy':'Mod-contained overrides of the same four Max-specific texture assets already supplied by Commander101; no on-disk game edit','textures':reports,'texture_chunks_replaced':8,'source_texture_images_preserved':True,'shaders_modified':False,'new_material_assets':False,'sampler_binding_limit':'Original MI_Character_Male01_Max_Apparel01 is external to the uploaded mod. Its parameter table/shader sampler binding cannot be independently inspected here; the Windows test must confirm atlas use or the original material dependencies must be supplied.','scope_limit':'No other character asset paths changed. Complete original-game reverse-reference graph is not available, so other uses of these Max-specific texture paths cannot be exhaustively ruled out offline.','game_test':'NOT RUN'}
 (out/'texture-write-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Replaced four native texture mip chains without changing headers, sizes or offsets')

if __name__=='__main__':write(*map(Path,sys.argv[1:]))
