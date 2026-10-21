from pathlib import Path
import json,zipfile,hashlib
root=Path(__file__).resolve().parents[2];dst=root/'BoPeep-Crook-Smooth-Jab-V1-UE57-Test.zip';assert not dst.exists()
readme='''Bo Peep crook smooth jab V1 — Windows test

Replace only ue4ss/Mods/BoPeepCrook with the folder inside Mods in this ZIP. Keep all Paks, mods.txt, Buzz runtime and accepted skins unchanged. No installer and no new assets.

This pass animates the crook only. Bo Peep's arms still use native unarmed animations; the native spear montage is NOT substituted. Attacks ease the staff hook-first into a forward jab and return upright. Damage, stamina, attack timing, reach, hit detection and equipment remain vanilla. FP remains staff-only, with no added hand/forearm. Rest placement/thickness and persistent camera-switch components are preserved.

Test as Bo Peep with both actual equipment slots empty: upright carry while standing/walking; single attacks in FP and TP; repeated attacks; pause/unpause during attack; switch FP/TP during recovery; equip an item to hide and unequip to restore. Look for smooth forward rotation and upright return without clipping across the camera.45 local Lua groups pass; native Windows appearance/timing still needs validation.

Send latest UE4SS.log and tell me whether the jab direction and recovery look right in each view. CROOK MOTION lines show game-time phase changes. A missing optional game clock logs one warning and keeps the previous instantaneous attack fallback, preserving carry.

Rollback: restore BoPeepCrook from accepted Buzz-BoPeep-Runtime-V4-UE57-Test.zip. Do not replace BuzzFlightVisual as part of this crook test.
'''
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('README.txt',readme)
 for p in sorted((root/'runtime-crook-jab-v1/BoPeepCrook').rglob('*')):
  if p.is_file():z.write(p,'Mods/BoPeepCrook/'+str(p.relative_to(root/'runtime-crook-jab-v1/BoPeepCrook')))
with zipfile.ZipFile(dst) as z:assert z.testzip() is None;assert all(not n.endswith(('.pak','.utoc','.ucas')) for n in z.namelist())
report={'file':dst.name,'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'status':'COSMETIC_STAFF_ANIMATION_WINDOWS_TEST_PENDING','native_spear_arm_animation':False,'local_lua_groups':45};(root/'docs/crook-jab-v1/package.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
