from pathlib import Path
import subprocess,os,json,numpy as np,sys,shutil,concurrent.futures
repo=Path('/workspace/Grounded2Skins');r=Path('/tmp/toystory-feedback-v3');prev=Path('/workspace/mod-work/skin-fixes-next');mig=Path('/workspace/mod-work/ue57-migration');env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home');sys.path.insert(0,str(repo/'pipeline'));from native_buffers import encode,skeleton_signature

def run(st,label,args):
 with (st/(label+'.log')).open('w') as f:subprocess.run([str(x) for x in args],cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
def build(name):
 st=r/(name+'-complete');st.mkdir();group={'CrookHand':'crook'}.get(name,name.lower());old=mig/(group+'-check-v1');base=mig/(group+'-package-v1');prototype=prev/({'BoPeep':'BoPeep-final','CrookHand':'CrookHand-final-v2'}.get(name,name))
 for f in ['reference.json','profiles.json']:shutil.copyfile(prototype/f,st/f)
 if name in ['Buzz','Jessie']:
  data=dict(np.load(r/'Buzz-geometry.npz' if name=='Buzz' else prev/'Jessie/geometry.npz'))
 else:
  run(st,'export',['blender','-b',r/(name+'.blend'),'--threads','2','--python-exit-code','1','--python',repo/'pipeline/export_skin_fix_candidate.py','--','BoPeep' if name=='CrookHand' else name,st/'reference.json',st/'export']);data=dict(np.load(st/'export'/((('BoPeep' if name=='CrookHand' else name))+'-geometry-SKINNED.npz')))
 bones=json.load(open(st/'reference.json'))['meshes'][0]['bones'];headslot={'Buzz':5,'BoPeep':3,'Woody':3,'Jessie':0,'CrookHand':0}[name];bodyslot=5 if name=='Jessie' else 0
 if name!='CrookHand':
  heads={i for i,b in enumerate(bones) if b['name']=='head_JNT'}
  for i,b in enumerate(bones):
   p=i
   while p>=0:
    if p in heads:heads.add(i);break
    p=bones[p]['parent']
  mass=(data['weights']*np.isin(data['joints'],list(heads))).sum(1);data['materials']=np.where(mass[data['indices']].max(1)>.25,headslot,bodyslot).astype('u2')
 else:assert np.all(data['joints'][data['weights']>0]==0);data['materials']=np.zeros(len(data['indices']),dtype='u2')
 data['material_count']=np.array(len(json.load(open(st/'profiles.json'))[0]['materials']));np.savez_compressed(st/'geometry.npz',**data);encode(data,skeleton_signature(st/'reference.json'),st/'buffers')
 run(st,'rewrite',[sys.executable,repo/'pipeline/rewrite_ue57_skin_lods.py',base/'unpacked',st/'profiles.json',st/'buffers',st/'reference.json',st/'raw'])
 stem='zBoCrookHandV3UE57_99_P' if name=='CrookHand' else 'z'+name+'SkinV3UE57_99_P';run(st,'package',[sys.executable,repo/'pipeline/repackage_iostore.py',st/'raw',next((base/'mod').glob('*.pak')),st/'package','--mod-name',stem]);(st/'check').mkdir();suffix={'Buzz':'Male01/SK_Male_Teen_01','BoPeep':'Female01/SK_Female_Teen_01','Woody':'Male02/SK_Male_Teen_02','Jessie':'Female02/SK_Female_Teen_02','CrookHand':'Female01/SK_Female_Teen_01'}[name].split('/')[-1];args=[sys.executable,repo/'pipeline/readback_buzz_package.py',st/'check',st/'package','--global-input',mig/'Shared','--ue57','--texture-prefix','__UNCHANGED_TEXTURES_HASH_CHECKED','--mesh-suffixes']
 if name=='CrookHand':args+=['_BoCrFP1/Art/Characters/Player_Female01/SK_Female_Teen_01.uasset']
 else:args+=[suffix+'.uasset',suffix+'_w_BackPack.uasset']
 args+=['--expected-mesh-count','1' if name=='CrookHand' else '2'];run(st,'readback',args);run(st,'validate',[sys.executable,repo/'pipeline/validate_skin_fix_package.py',name,st,st/'check',old]);print('NATIVE_PASS',name,flush=True)
 if name!='CrookHand':
  scene=r/(name+'.blend') if name!='Jessie' else prev/'Jessie-Neck-Candidate.blend';run(st,'previews',['blender','-b','--threads','2','--python-exit-code','1','--python',repo/'pipeline/render_skin_fix_readback.py','--',name,st,st/'check',scene,old]);print('PREVIEWS_READY',name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(build,['BoPeep']))
