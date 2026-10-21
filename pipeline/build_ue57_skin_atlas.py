"""Current-build templates + unchanged accepted Jessie native LODs and atlas UVs.
No old5.6 UObject/texture prefix or other skin overrides are included.
"""
import argparse,json,hashlib,struct,shutil
from ue57_skin_config import CONFIG
from ue57_accessory_config import CONFIG as ACCESSORIES
CONFIG={**CONFIG,**{k:v for k,v in ACCESSORIES.items() if v['atlas'] is not None}}
from pathlib import Path
import numpy as np
from PIL import Image
import ispc_texcomp,texture2ddecoder
from write_buzz_atlas_textures import layout,solid_bc1,solid_bc5
from assemble_jessie_zen import batch,H
from compare_stock_max import names
p=argparse.ArgumentParser();p.add_argument('character',choices=CONFIG);p.add_argument('rebase',type=Path);p.add_argument('material',type=Path);p.add_argument('out',type=Path);a=p.parse_args();c=CONFIG[a.character];r=Path('/workspace/mod-work');stage=r/'ue57-migration';out=a.out;out.mkdir(exist_ok=False);(out/'raw/chunks').mkdir(parents=True);(out/'expected-mips').mkdir();paths=json.loads((a.rebase/'mesh-paths.json').read_text())
for cid in paths:shutil.copyfile(a.rebase/'chunks'/cid,out/'raw/chunks'/cid)
mi=json.loads((a.material/'material-report.json').read_text());paths[mi['chunk']]=mi['path'];shutil.copyfile(a.material/mi['chunk'],out/'raw/chunks'/mi['chunk']);report=json.loads((stage/'textures/texture-report.json').read_text());assert report['status']=='complete';atlas=c['atlas'];image=Image.open(atlas).convert('RGBA');assert image.size==(4096,4096);assert np.asarray(image)[:,:,3].min()==255;textures=[]
for e in report['packages']:
 cid=e['id'];source=(stage/'textures/chunks'/cid).read_bytes();bulk_source=(stage/'textures/chunks'/(cid[:16]+'00000002')).read_bytes();info=layout(source,allow_zen_without_footer=True);b=bytearray(source);bulk=bytearray(bulk_source);chain=[];leaf=e['path'].rsplit('/',1)[-1];suffix=leaf[:-7].rsplit('_',1)[-1];destination=out/'expected-mips'/suffix;destination.mkdir()
 for m in info['mips']:
  w,h=m['width'],m['height']
  if suffix=='C':
   assert info['format']=='PF_DXT1';im=image.resize((w,h),Image.Resampling.LANCZOS);arr=np.array(im);arr=np.pad(arr,((0,max(0,4-h)),(0,max(0,4-w)),(0,0)),mode='edge');surface=ispc_texcomp.RGBASurface(arr.tobytes(),max(4,w),max(4,h))
   # Wrapper allocates a BC3-sized buffer for BC1; only the BC1 prefix is
   # initialized. Retain exactly the measured8-byte-per-block payload.
   payload=ispc_texcomp.compress_blocks_bc1(surface)[:m['bytes']]
  elif suffix=='N':assert info['format']=='PF_BC5';payload=solid_bc5()*(m['bytes']//16)
  else:assert info['format']=='PF_DXT1';payload=solid_bc1((200,0,255) if suffix=='RMA' else (0,0,0))*(m['bytes']//8)
  assert len(payload)==m['bytes'];target=b if m['inline'] else bulk;at=m['offset'];assert at+len(payload)<=len(target);target[at:at+len(payload)]=payload;f=destination/('mip-%02d.bin'%m['level']);f.write_bytes(payload);chain.append(dict(m,sha256=hashlib.sha256(payload).hexdigest()))
 # All bytes outside the measured mip ranges are immutable current-build data.
 for old,new,inline in [(source,b,True),(bulk_source,bulk,False)]:
  mask=np.zeros(len(old),bool)
  for m in info['mips']:
   if m['inline']==inline:mask[m['offset']:m['offset']+m['bytes']]=True
  assert len(old)==len(new) and not np.any((np.frombuffer(old,'u1')!=np.frombuffer(new,'u1'))&~mask)
 s=struct.unpack_from('<15I',b);oldshort=leaf[:-7];newshort=oldshort.replace('_Max_','_'+c['tag']+'_' );oldpkg='/Game/'+e['path'].split('/Content/',1)[1][:-7];newpkg=oldpkg.replace('/_Augusta/','/'+c['namespace']+'/').replace('_Max_','_'+c['tag']+'_' );replace={oldshort:newshort,oldpkg:newpkg}
 for at in [60,s[12]]:
  ns,end=names(b,at);nb=batch([replace.get(n,n) for n in ns]);assert len(nb)==end-at;b[at:end]=nb
 for at in range(s[8],s[9],72):
  if struct.unpack_from('<Q',b,at+56)[0]==H(oldshort):struct.pack_into('<Q',b,at+56,H(newshort))
 newcid=H(newpkg).to_bytes(8,'little').hex()+'00000001';newbulk=newcid[:16]+'00000002';path=newpkg.replace('/Game/','../../../Augusta/Content/')
 for nc,data,ext in [(newcid,b,'.uasset'),(newbulk,bulk,'.ubulk')]:assert nc not in paths;paths[nc]=path+ext;(out/'raw/chunks'/nc).write_bytes(data)
 textures.append({'original_path':e['path'],'private_path':path+'.uasset','chunk':newcid,'format':info['format'],'width':info['width'],'mips':chain,'original_object_prefix_and_layout_outside_mips_exact':True})
 if suffix=='C':
  pixels=np.frombuffer(texture2ddecoder.decode_bc1((destination/'mip-00.bin').read_bytes(),info['width'],info['height']),dtype='u1').reshape(info['height'],info['width'],4)[:,:,[2,1,0,3]];assert np.all(pixels[:,:,3]==255);expected=np.array(image.resize((info['width'],info['height']),Image.Resampling.LANCZOS));err=float(abs(pixels[:,:,:3].astype(float)-expected[:,:,:3]).mean());assert err<7;Image.fromarray(pixels).save(out/('decoded-'+a.character+'-atlas.png'));textures[-1]['BC1_RGB_mean_error_0_255']=err
# Build the supported v5 package-store table from actual new import names.
entries={}
for cid,path in paths.items():
 if not path.endswith('.uasset'):continue
 b=(out/'raw/chunks'/cid).read_bytes();s=struct.unpack_from('<15I',b);imp,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),b,end);imp=[n if v==0 else n+'_'+str(v-1) for n,v in zip(imp,nums)];entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(n) for n in imp]
entries=dict(sorted(entries.items()));buf=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',buf,i*16,len(imports),len(buf)-i*16);buf.extend(struct.pack('<'+'Q'*len(imports),*imports))
oldraw=c['old'];header=next((oldraw/'chunks').glob('*00000006'));prefix=header.read_bytes()[:16];assert struct.unpack_from('<II',prefix)==(0x496f436e,5);head=bytearray(prefix+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(buf))+buf+bytes(20));head.extend(struct.pack('<qqI',len(head)+16,4,0));(out/'raw/chunks'/header.name).write_bytes(head);manifest=json.loads((oldraw/'manifest.json').read_text());manifest['chunk_paths']=paths;(out/'raw/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
r={'status':'CURRENT_BUILD_CANDIDATE_PACK_READBACK_PENDING','packages':len(entries),'private_texture_mips':sum(len(t['mips']) for t in textures),'textures':textures,'atlas_source_sha256':hashlib.sha256(atlas.read_bytes()).hexdigest(),'color_atlas_4096_to_2048':'UV-preserving resample to current stock size and BC1 format; original image retained','source_model_weights_UVs_and_FP_split_changed':False,'only_requested_character_override':a.character,'runtime':'NOT TESTED'};(out/'build-report.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',len(entries),'packages;',r['private_texture_mips'],'current-template mips')
