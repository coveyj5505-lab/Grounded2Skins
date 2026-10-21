"""Freeze reviewed UE5.7 skin candidates and isolated accessory tests."""
import hashlib,json,zipfile
from pathlib import Path
repo=Path(__file__).resolve().parents[1];r=Path('/workspace/mod-work/skin-fixes-next');migration=Path('/workspace/mod-work/ue57-migration');reports=repo/'docs/skin-fixes-next'
def sha(b):return hashlib.sha256(b).hexdigest()
frozen=json.loads(Path('/workspace/mod-work/anatomy-corrections/frozen.json').read_text())
for p,h in frozen.items():assert sha((repo/p).read_bytes())==h,p
for doc,archive in [('CROOK-WINDOWS-BASELINE.json','BoPeep-Crook-Persistent-Views-Test.zip'),('BUZZ-WINGS-WINDOWS-BASELINE.json','Buzz-Wings-F1-Recreate-Test.zip')]:
 data=json.loads((repo/'docs'/doc).read_text());assert sha((repo/archive).read_bytes())==data['sha256']
assert json.loads((reports/'visual-review.json').read_text())['images_opened_and_evaluated']
packages=[]
def pack(name,files,scope,instructions):
 target=repo/name;assert not target.exists()
 files['TEST-STEPS.txt']=(instructions+'\n\n'+scope+'\nOFFLINE VALIDATED; WINDOWS RESULTS PENDING.\n').encode()
 with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for key,value in sorted(files.items()):
   info=zipfile.ZipInfo(key,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,value,compresslevel=6)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None;assert {n:z.read(n) for n in z.namelist()}==files
 packages.append({'file':name,'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'scope':scope,'instructions':instructions,'status':'OFFLINE_VALIDATED_WINDOWS_PENDING','files':{k:sha(v) for k,v in sorted(files.items())}})
files={}
for name,st,pk in [('Buzz',r/'Buzz','package-v2'),('BoPeep',r/'BoPeep-final','package'),('Woody',r/'Woody','package-v2'),('Jessie',r/'Jessie','package-v2')]:
 assert json.loads((st/'validation.json').read_text())['status']=='PASS_OFFLINE_WINDOWS_PENDING'
 for f in (st/pk/'mod').iterdir():files['Paks/'+f.name]=f.read_bytes()
 files['Validation/'+name+'.json']=(st/'validation.json').read_bytes()
for f in (reports/'previews').glob('*-cooked-*.png'):files['Previews/'+f.name]=f.read_bytes()
pack('ToyStory-Four-Skins-Visual-V2-UE57-Test.zip',files,'Four independent skin replacements: Buzz shoulder fit; Bo Peep cape topology/weights/collar underlay; Jessie neck posture; Woody hip-rigid outward holster. Existing native references, textures, material paths and FP head/body classification retained.', 'Close game. Move previous four replacement trios OUTSIDE Paks: zBuzzUE57_P, zBoPeepUE57_P, zWoodyUE57_P, zJessieUE57_P (and any other older skin replacements). Copy all12 files from Paks into Augusta/Content/Paks. Keep working wing/crook accessories. No UE4SS changes in this ZIP. Test idle/walk/attack/sitting and both views on all4 characters. Rollback: remove the four z*SkinV2UE57_P trios and restore previous trios.')
files={}
for f in (r/'CrookHand-final-v2/package/mod').iterdir():files['Paks/'+f.name]=f.read_bytes()
files['Mods/BoPeepCrook/Scripts/main.lua']=(repo/'runtime-ue57/BoPeepCrook/Scripts/main.lua').read_bytes()
for n in ['Crook-FP-upright-review.png','Crook-FP-camera-review.png']:files['Previews/'+n]=(reports/'previews'/n).read_bytes()
files['Validation/CrookHand.json']=(r/'CrookHand-final-v2/validation.json').read_bytes()
pack('BoPeep-Crook-Upright-Hand-V2-UE57-Test.zip',files,'Corrected thumb-up proxy hand and connected forearm, palm-matched skin texel. TP and bare-FP assets unchanged. Persistent component lifetime fix retained. FP65/50/-32 placement; no global scale change. Existing cosmetic jab retained; native spear montage NOT substituted.', 'Close game. Move old zBoCrookUE57_P trio outside Paks; copy new zBoCrookHandV2UE57_P trio from Paks. Replace only Mods/BoPeepCrook/Scripts/main.lua. Keep BoPeepCrook : 1 in existing mods.txt. Crook should appear automatically for Willow with empty hands; no F9 needed. Check FP upright thumb/hand/height/side placement, repeat FP-TP several times, then equip main-hand and off-hand separately and empty both. Rollback: restore old trio and main.lua from BoPeep-Crook-Persistent-Views-Test.zip.')
files={}
for f in (migration/'flight-package-v1/mod').iterdir():files['Paks/'+f.name]=f.read_bytes()
for f in (repo/'runtime-ue57/BuzzFlightVisual/Scripts').glob('*.lua'):
 data=f.read_bytes()
 if f.name=='flight_config.lua':data=b'-- Isolated Windows source-mesh / flight / optional tuft visual test.\nreturn {Enabled=true,DebugToggleKey=nil}\n'
 files['Mods/BuzzFlightVisual/Scripts/'+f.name]=data
for f in ['buzz-flight-adapter-regressions.json','buzz-flight-controller-regressions.json']:files['Validation/'+f]=(repo/'docs'/f).read_bytes()
for n in ['cooked-flight-quarter.png','cooked-flight-side.png']:files['Previews/'+n]=(Path('/workspace/mod-work/anatomy-corrections/buzz-flight-check-v1/previews')/n).read_bytes()
pack('Buzz-Flight-Source-Mesh-Repair-V2-UE57-Test.zip',files,'Repairs missing direct Character.Mesh route; same corrected side-socket horizontal proxy. Optional active inventory item / Glider-slot visual-only tuft suppression with exact visibility rollback. No wing-mod changes, attack RPCs, equipment writes, actor/camera/movement transforms or physics changes. TP only, local-client cosmetic. Windows native execution remains unverified.', 'Keep the working BuzzWings folder, F1 bind, config and zBuzzWingsUE57_P trio. Copy this Paks trio (zBuzzFlightUE57_P) and replace Mods/BuzzFlightVisual/Scripts with these three Lua files. Add/keep BuzzFlightVisual : 1 in existing mods.txt. First check F1 open-close standing: no flight pose. With wings folded, actually jump/fall far enough and press Shift to OPEN the reusable tuft. In THIRD PERSON, check forward pose, wings and tuft; land. Repeat with manual wings extended: landing must leave them extended. Switch FP during a glide if safe, then return TP; native FP presentation is intentional. Send UE4SS.log. If tuft remains, its optional stage is logged and should not block flight. Rollback: disable BuzzFlightVisual in mods.txt; keep working wings.')
files={}
for f in (repo/'pipeline/spear-animation-collector').iterdir():
 if f.is_file():files[f.name]=f.read_bytes()
files['extract_animation_dependencies.py']=(repo/'pipeline/extract_animation_dependencies.py').read_bytes()
for n in ['extract_selected.py','discover_pete.py']:files['pete-extractor/'+n]=(repo/'pipeline/pete-extractor'/n).read_bytes()
pack('Grounded2-Targeted-Spear-Animation-Collector.zip',files,'Read-only exact recorded montage plus actual indexed animation/skeleton dependencies. At most32 packages /64MiB decoded. No game launch, no gameplay recording, no mod installation. Needed before inspecting native spear notify/root-motion/slot tracks safely.', 'Optional separate collection for the next native-animation iteration. Close game; run Start-Collection.cmd from extracted folder. Select existing Windows retoc.exe0.1.5, then ORIGINAL Augusta-WinGDK.utoc. Requires existing Python3.11+. Send the ONE Grounded2-SpearAnimation-*.zip on Desktop. No four-character collector or attack sequence repeated.')
(reports/'downloads.json').write_text(json.dumps({'packages':packages,'frozen_inputs_verified':frozen,'working_wings_and_crook_releases_verified_unchanged':True},indent=2)+'\n');print(json.dumps([{k:p[k] for k in ['file','bytes','sha256']} for p in packages],indent=2))
