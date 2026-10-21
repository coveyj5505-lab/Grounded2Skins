"""Package isolated V4 runtime changes. All released assets remain unchanged."""
from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parents[2];dst=root/'Buzz-BoPeep-Runtime-V4-UE57-Test.zip';assert not dst.exists()
readme='''V4 Buzz + Bo Peep runtime update — Windows validation pending

Copy both folders inside Mods into ue4ss/Mods, replacing the existing BuzzFlightVisual and BoPeepCrook files. Keep all installed V3 Paks and the current BuzzWings folder. Keep existing mods.txt entries. There are NO Paks or skin geometry changes in this ZIP.

Buzz: keeps the forward proxy alive when BuzzWings replaces a folded/deployed component; retires discarded private wings without blocking restoration; hides the separate wrist device during flight; preserves F1 manual OR glide logic and native physics/camera. Check several consecutive glides, landing, and both camera views when convenient. Buzz arm geometry is NOT changed; the rigid-shell experiment failed render review and was not bundled.

Bo Peep: uses existing bare FP staff, without added hand/forearm. Same position/thickness. Optional shadow flag disables shadows on the separate FP staff only when supported. Persistent camera-switch lifecycle and empty-hand equipment gating preserved. Cosmetic jab remains; native spear substitution is not implemented.

Woody and Jessie: accepted V3 skins are final; leave installed files unchanged. Bo Peep body/cape likewise unchanged.

75 mocked Lua regression groups pass; not native Windows validation. Keep latest UE4SS.log after testing. Rollback: restore only these two Mods folders from frozen ToyStory-All-Fixes-V3-UE57-Test.zip. No installer scripts.
'''
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('README.txt',readme)
 for mod in ['BuzzFlightVisual','BoPeepCrook']:
  for p in sorted((root/'runtime-feedback-v4'/mod).rglob('*')):
   if p.is_file():
    data=p.read_bytes()
    if p.name=='flight_config.lua':data=data.replace(b'Enabled=false',b'Enabled=true')
    z.writestr('Mods/'+mod+'/'+str(p.relative_to(root/'runtime-feedback-v4'/mod)),data)
with zipfile.ZipFile(dst) as z:assert z.testzip() is None;assert not any(n.endswith(('.pak','.utoc','.ucas')) for n in z.namelist())
report={'file':dst.name,'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'status':'CANDIDATE_NOT_WINDOWS_VALIDATED','asset_changes':False,'mocked_lua_groups':75}
(root/'docs/feedback-v4/package.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
