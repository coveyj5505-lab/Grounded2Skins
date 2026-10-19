#!/usr/bin/env python3
"""Fresh independent reads of a generated package; preserve all source artifacts."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from compare_stock_max import names
from extract_reference_skeleton import extract
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('package_work',type=Path);p.add_argument('--global-input',type=Path,default=Path('/workspace/mod-work/global-stage/input'));a=p.parse_args();stage=a.stage.resolve();pack=a.package_work.resolve();pipeline=Path(__file__).resolve().parent
for n,t in {'final-unpacked':pack/'unpacked','final-package':pack/'mod'}.items():assert not (stage/n).exists();(stage/n).symlink_to(t,target_is_directory=True)
manifest=json.loads((stage/'final-unpacked/manifest.json').read_text());metadata=[];skeletons=[]
for cid,path in manifest['chunk_paths'].items():
 if not path.endswith('.uasset'):continue
 b=(stage/'final-unpacked/chunks'/cid).read_bytes();s=struct.unpack_from('<15I',b);assert s[0]==0;nm,_=names(b,60);imp,pos=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),b,pos);imp=[n if i==0 else n+'_'+str(i-1) for n,i in zip(imp,nums)];assert not any('UnknownPackage' in v for v in imp)
 m={'path':path,'chunk_id':cid,'sha256':hashlib.sha256(b).hexdigest(),'name_map':nm,'imported_packages':imp,'header_size':s[1]};metadata.append(m)
 if path.endswith(tuple(p.split('/')[-1] for p in manifest['chunk_paths'].values() if '/Player_Male02/' in p and p.endswith('.uasset'))):
  sk=extract(b,nm);sk.update(package=path,chunk_sha256=m['sha256']);skeletons.append(sk)
assert len(skeletons)==12
(stage/'final-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');(stage/'final-skeletons.json').write_text(json.dumps({'meshes':skeletons},indent=2)+'\n')
env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home');dotnet='/workspace/toolchains/dotnet/dotnet';commands=[]
def run(label,command):
 with (stage/(label+'.log')).open('w') as f:result=subprocess.run(list(map(str,command)),env=env,stdout=f,stderr=subprocess.STDOUT)
 commands.append({'label':label,'command':list(map(str,command)),'exit_code':result.returncode});(stage/'readback-commands.json').write_text(json.dumps(commands,indent=2)+'\n');result.check_returncode()
for i,m in enumerate([m for m in metadata if m['path'].endswith(tuple(p.split('/')[-1] for p in manifest['chunk_paths'].values() if '/Player_Male02/' in p and p.endswith('.uasset')))]):
 run(f'final-mesh-readback-{i}',[dotnet,pipeline/'native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll',stage/'final-unpacked/chunks'/m['chunk_id'],stage/'final-skeletons.json',stage/'final-metadata.json',stage/f'final-mesh-readback-{i}']+(['--no-colors'] if '/Hair/' in m['path'] or 'Peeper' in m['path'] else []))
li=stage/'final-legacy-input';li.mkdir()
for f in list((stage/'final-package').iterdir())+list(a.global_input.glob('global.*')):shutil.copyfile(f,li/f.name)
run('final-readback-legacy',['/workspace/mod-work/bin/retoc','to-legacy',li,stage/'final-readback-legacy','--no-shaders','--no-script-objects','--no-parallel','--verbose'])
for f in (stage/'final-readback-legacy').rglob('T_Wdy*.uasset'):
 run(f.stem+'-mip-readback',[dotnet,pipeline/'texture-probe/bin/Release/net10.0/TextureProbe.dll',f.with_suffix(''),stage/('final-mips-'+f.stem)])
print('Fresh native mesh and texture readbacks complete')
