"""Build final Rivet suite from user-accepted component releases.
Rename container identities with retoc; never alter their game asset chunks.
"""
from pathlib import Path
import zipfile,sys,json,hashlib,shutil,subprocess,os,re
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'pipeline'))
from repackage_iostore import repackage
work=Path(sys.argv[1]);work.mkdir(parents=True,exist_ok=False)
stage=work/'stage';pakout=stage/'Augusta/Content/Paks/~mods';mods=stage/'Augusta/Binaries/WinGDK/ue4ss/Mods';pakout.mkdir(parents=True);mods.mkdir(parents=True)
retoc=Path('/workspace/mod-work/bin/retoc');receipts=[]
assets=[
 ('ToyStory-All-Fixes-V3-UE57-Test.zip','Paks/zBoPeepSkinV3UE57_99_P','Rivet-BoPeep_99_P'),
 ('ToyStory-All-Fixes-V3-UE57-Test.zip','Paks/zBuzzSkinV3UE57_99_P','Rivet-Buzz_99_P'),
 ('ToyStory-All-Fixes-V3-UE57-Test.zip','Paks/zJessieSkinV3UE57_99_P','Rivet-Jessie_99_P'),
 ('ToyStory-All-Fixes-V3-UE57-Test.zip','Paks/zWoodySkinV3UE57_99_P','Rivet-Woody_99_P'),
 ('ToyStory-All-Fixes-V3-UE57-Test.zip','Paks/zBoCrookHandV3UE57_99_P','Rivet-BoPeep-CrookMesh_99_P'),
 ('BoPeep-Crook-V2.8-Automatic-Original-Orientation.zip','Paks/zBoCrookNativeUE57_P','Rivet-BoPeep-CrookNative_99_P'),
 ('ToyStory-UE57-Skins-Accessories-Test.zip','02-Accessories/Paks/zBuzzWingsUE57_P','Rivet-Buzz-Wings_99_P'),
 ('ToyStory-All-Fixes-V3-UE57-Test.zip','Paks/zBuzzFlightUE57_P','Rivet-Buzz-Flight_99_P'),
]
for archive,stem,new in assets:
 source=work/'sources'/new;source.mkdir(parents=True)
 with zipfile.ZipFile(root/archive) as z:
  for ext in ['pak','utoc','ucas']:(source/(Path(stem).name+'.'+ext)).write_bytes(z.read(stem+'.'+ext))
 toc=source/(Path(stem).name+'.utoc');raw=source/'raw'
 subprocess.run([str(retoc),'unpack-raw',str(toc),str(raw)],check=True,stdout=subprocess.DEVNULL,env=dict(os.environ,RAYON_NUM_THREADS='4'))
 result=repackage(raw,toc.with_suffix('.pak'),work/'repacked'/new,retoc,new)
 # Compare all game chunks, excluding the container header identity only.
 before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (raw/'chunks').iterdir() if not p.name.endswith('00000006')}
 after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (work/'repacked'/new/'unpacked/chunks').iterdir() if not p.name.endswith('00000006')}
 assert before==after
 for f in (work/'repacked'/new/'mod').iterdir():shutil.copyfile(f,pakout/f.name)
 receipts.append({'source_archive':archive,'source_stem':Path(stem).name,'rivet_stem':new,'asset_chunks_byte_identical':True,'validation':result})
 print('VERIFIED',new,flush=True)
# Assemble Lua sources from frozen packages or isolated current candidate.
def zipmod(archive,old,new):
 with zipfile.ZipFile(root/archive) as z:
  prefix='Mods/'+old+'/'
  for n in z.namelist():
   if n.startswith(prefix) and not n.endswith('/'):
    p=mods/new/n[len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
def copytree(src,new):shutil.copytree(root/src,mods/new)
copytree('runtime-native-spear-v2-8/BoPeepNativeSpear','Rivet-BoPeep')
copytree('runtime-teleport-v6/Teleport','Rivet-Teleport')
copytree('runtime-utilities-v1/FreeBuild','Rivet-FreeBuild')
copytree('runtime-utilities-v1/InvisibleArmor','Rivet-InvisibleArmor')
zipmod('Buzz-Wings-F1-Recreate-Test.zip','BuzzWings','Rivet-Buzz-Wings')
zipmod('Buzz-Flight-Landing-V5-UE57-Test.zip','BuzzFlightVisual','Rivet-Buzz-Flight')
# Update exact wing file receipt for renamed/reidentified identical game assets.
p=mods/'Rivet-Buzz-Wings/Scripts/main.lua';s=p.read_text();toc=(pakout/'Rivet-Buzz-Wings_99_P.utoc').read_bytes()
s=s.replace('zBuzzWingsUE57_P','Rivet-Buzz-Wings_99_P')
s=re.sub(r"hex=='[0-9a-f]+' and size==3953",f"hex=='{toc[:64].hex()}' and size=={len(toc)}",s);p.write_text(s)
# Brand log tags only, preserving cooked asset paths, schema names and module APIs.
for folder,label in [('Rivet-BoPeep','BoPeepNativeSpear'),('Rivet-Teleport','Teleport Native V6'),('Rivet-FreeBuild','FreeBuild UE57'),('Rivet-InvisibleArmor','InvisibleArmor UE57')]:
 p=mods/folder/'Scripts/main.lua';s=p.read_text().replace("'"+label+"'","'"+folder+"'");p.write_text(s)
# Rebuild the flight runtime's installation receipt against ALL renamed assets.
p=mods/'Rivet-Buzz-Flight/Scripts/build_receipt.lua';s=p.read_text();a=s.index('local expected={');b=s.index('\nlocal old=',a)
entries=[]
for _,old,new in assets:
 t=(pakout/(new+'.utoc')).read_bytes();sizes={ext:(pakout/(new+'.'+ext)).stat().st_size for ext in ['pak','utoc','ucas']}
 entries.append("{name='%s',stem='%s',head='%s',sizes={pak=%s,utoc=%s,ucas=%s}},"%(new,new,t[:64].hex(),sizes['pak'],sizes['utoc'],sizes['ucas']))
s=s[:a]+'local expected={\n'+'\n'.join(entries)+'\n}'+s[b:];s=s.replace('FILES MATCH V3','FILES MATCH RIVET FINAL');p.write_text(s)
p=mods/'Rivet-Buzz-Flight/Scripts/flight_config.lua';p.write_text('-- User-accepted flight behavior; brief initial tuft flash accepted.\nreturn {Enabled=true,DebugToggleKey=nil}\n')
(mods/'Rivet-Buzz-Flight/enabled.txt').write_text('')
# Match the actual consolidated ~mods location in existing read-only receipts.
for relative in ['Rivet-Buzz-Wings/Scripts/main.lua','Rivet-Buzz-Flight/Scripts/build_receipt.lua']:
 p=mods/relative;s=p.read_text();s=s.replace("local dirs={'../../Content/Paks/'","local dirs={'../../Content/Paks/~mods/','../../Content/Paks/'");p.write_text(s)
# Only ship the official engine-compatible loader and its standard runtime config.
with zipfile.ZipFile(root/'ToyStory-UE57-Loader-Repair-Test.zip') as z:
 for name in ['WinGDK/dwmapi.dll','WinGDK/ue4ss/UE4SS.dll','WinGDK/ue4ss/LICENSE']:
  p=stage/'Augusta/Binaries'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
official=Path('/workspace/mod-work/ue4ss-loader-update/official/ue4ss')
shutil.copyfile(official/'UE4SS-settings.ini',mods.parent/'UE4SS-settings.ini')
shutil.copytree(official/'UE4SS_SDK_Backends',mods.parent/'UE4SS_SDK_Backends')
active=['Rivet-BoPeep','Rivet-Buzz-Wings','Rivet-Buzz-Flight','Rivet-FreeBuild','Rivet-InvisibleArmor','Rivet-Teleport']
for name in active:(mods/name/'enabled.txt').write_text('')
(mods/'mods.txt').write_text('\n'.join(n+' : 1' for n in active)+'\n')
(mods/'mods.json').write_text(json.dumps([{'mod_name':n,'mod_enabled':True} for n in active],indent=2)+'\n')
(stage/'Validation').mkdir();(stage/'Validation/container-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
(work/'preparation.json').write_text(json.dumps({'stage':str(stage),'containers':len(assets),'old_to_new':{Path(old).name:new for _,old,new in assets},'crook_automatic':'V2.8 USER ACCEPTED FINAL; original orientation','buzz_flight':'V5 USER ACCEPTED; ENABLED; brief initial tuft flash accepted','teleport':'V6 USER ACCEPTED FINAL','ue4ss':'3.0.1-1181-g83330635; DLLs byte-identical to confirmed loader repair'},indent=2)+'\n')
print('STAGED',stage,flush=True)
