from pathlib import Path
import zipfile,json,hashlib
root=Path(__file__).resolve().parents[2];dst=root/'Buzz-Flight-Landing-V5-UE57-Test.zip';assert not dst.exists()
readme='''Buzz flight landing V5 — Windows validation pending

Replace only ue4ss/Mods/BuzzFlightVisual with the folder under Mods in this ZIP. Keep all Paks, BuzzWings, BoPeepCrook and mods.txt unchanged. No asset, skin, camera, physics or equipment changes.

V4's log identifies repeated restoration failures on the old deployed wing and retired dandelion StaticMesh after landing. That cleanup debt blocked later glides. V5 checks transient-component membership before restoration/retry, retires replaced private wings, and attempts restoration of disappearing tuft visuals without making an inactive, rejecting tuft block subsequent glides. Actual native body and wrist-device restoration remains strict and retryable. Existing live tuft visibility still restores normally. F1 manual OR glide state unchanged.

Please test several glides with landings between them. Forward flight should engage on each glide without pausing/screenshotting or restarting. Check F1 preference restoration after landing and FP/TP transitions. Send the latest UE4SS.log.48 mocked Lua groups pass; native Windows behavior is not yet confirmed.

Buzz arm geometry is unchanged and remains unresolved. Bo Peep V4 and accepted Woody/Jessie skins are unchanged. Rollback: restore BuzzFlightVisual from Buzz-BoPeep-Runtime-V4-UE57-Test.zip. No installers.
'''
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('README.txt',readme)
 for p in sorted((root/'runtime-feedback-v5/BuzzFlightVisual').rglob('*')):
  if p.is_file():
   data=p.read_bytes()
   if p.name=='flight_config.lua':data=data.replace(b'Enabled=false',b'Enabled=true')
   z.writestr('Mods/BuzzFlightVisual/'+str(p.relative_to(root/'runtime-feedback-v5/BuzzFlightVisual')),data)
with zipfile.ZipFile(dst) as z:assert z.testzip() is None;assert not any(n.endswith(('.pak','.utoc','.ucas')) for n in z.namelist())
report={'file':dst.name,'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'status':'CANDIDATE_NOT_WINDOWS_VALIDATED','mocked_groups':48,'replaces':'BuzzFlightVisual only'};(root/'docs/feedback-v5/package.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
