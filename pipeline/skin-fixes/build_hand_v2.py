from pathlib import Path
import subprocess,os,json,numpy as np,sys
repo=Path('/workspace/Grounded2Skins');r=Path('/workspace/mod-work/skin-fixes-next');migration=Path('/workspace/mod-work/ue57-migration');env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home');sys.path.insert(0,str(repo/'pipeline'));from native_buffers import encode,skeleton_signature

def run(label,args):
 with (r/(label+'.log')).open('w') as f:subprocess.run([str(x) for x in args],cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
for name,scene,group in [('CrookHand','Crook-FP-Hand-Upright-Candidate','crook')]:
 st=r/(name+'-final-v2');st.mkdir();old=migration/(group+'-check-v1');base=migration/(group+'-package-v1');cid='2ee2517f02d2199900000001' if name=='BoPeep' else 'f18d1a7a07c9a4a700000001'
 if name=='BoPeep':
  for f in ['reference.json','profiles.json']:(st/f).write_bytes((r/'BoPeep'/f).read_bytes())
 else:
  meta=json.load(open(old/'final-metadata.json'));m=next(x for x in meta if x['chunk_id']==cid);refs=json.load(open(old/'final-skeletons.json'));ref=next(x for x in refs['meshes'] if x['chunk_sha256']==m['sha256']);assert ref['bones'][0]['name']=='Root_NSK' and ref['bones'][0]['parent']==-1;(st/'reference.json').write_text(json.dumps({'meshes':[ref]}));d=next(d for d in old.glob('final-mesh-readback-*') if d.is_dir() and json.load(open(d/'mesh.json'))['source_sha256']==m['sha256']);profile=json.load(open(d/'mesh.json'));profile['chunk']=cid;profile['skeleton_bones']=192;(st/'profiles.json').write_text(json.dumps([profile]))
 run(name+'-export',['blender','-b',r/(scene+'.blend'),'--threads','2','--python-exit-code','1','--python',repo/'pipeline/export_skin_fix_candidate.py','--','BoPeep',st/'reference.json',st/'export'])
 data=dict(np.load(st/'export/BoPeep-geometry-SKINNED.npz'));bones=json.load(open(st/'reference.json'))['meshes'][0]['bones']
 if name=='BoPeep':
  heads={i for i,b in enumerate(bones) if b['name']=='head_JNT'}
  for i,b in enumerate(bones):
   p=i
   while p>=0:
    if p in heads:heads.add(i);break
    p=bones[p]['parent']
  mass=(data['weights']*np.isin(data['joints'],list(heads))).sum(1);data['materials']=np.where(mass[data['indices']].max(1)>.25,3,0).astype('u2')
 else:
  assert np.all(data['joints'][data['weights']>0]==0);data['materials']=np.zeros(len(data['indices']),dtype='u2')
 data['material_count']=np.array(len(json.load(open(st/'profiles.json'))[0]['materials']));np.savez_compressed(st/'geometry.npz',**data);encode(data,skeleton_signature(st/'reference.json'),st/'buffers')
 run(name+'-rewrite',[sys.executable,repo/'pipeline/rewrite_ue57_skin_lods.py',base/'unpacked',st/'profiles.json',st/'buffers',st/'reference.json',st/'raw'])
 stem='zBoPeepSkinV2UE57_P' if name=='BoPeep' else 'zBoCrookHandV2UE57_P';pak=next((base/'mod').glob('*.pak'));run(name+'-package',[sys.executable,repo/'pipeline/repackage_iostore.py',st/'raw',pak,st/'package','--mod-name',stem]);(st/'check').mkdir()
 args=[sys.executable,repo/'pipeline/readback_buzz_package.py',st/'check',st/'package','--global-input',migration/'Shared','--ue57','--texture-prefix','__UNCHANGED_TEXTURES_HASH_CHECKED','--mesh-suffixes','_BoCrFP1/Art/Characters/Player_Female01/SK_Female_Teen_01.uasset' if name=='CrookHand' else 'SK_Female_Teen_01.uasset']
 if name=='BoPeep':args+=['SK_Female_Teen_01_w_BackPack.uasset']
 args+=['--expected-mesh-count','1' if name=='CrookHand' else '2'];run(name+'-readback',args)
 run(name+'-validate',[sys.executable,repo/'pipeline/validate_skin_fix_package.py',name,st,st/'check',old]);print('COMPLETE',name,flush=True)
 if name=='BoPeep':run(name+'-cooked-previews',['blender','-b','--threads','2','--python-exit-code','1','--python',repo/'pipeline/render_skin_fix_readback.py','--','BoPeep',st,st/'check',r/(scene+'.blend'),old])
