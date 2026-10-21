from pathlib import Path
import zipfile,json,hashlib
root=Path(__file__).resolve().parents[2];dst=root/'BoPeep-Native-Spear-Reference-Probe-V1.zip';assert not dst.exists()
readme='''Bo Peep native-spear reference probe V1 — read-only diagnostic

WHY THIS NEW SESSION
We already have16 spear animation packages. The old logger did not capture native spear attachment/hand transforms or the damage source. This probe collects those specific missing fields and a current native type-layout .usmap. No repeated asset extraction. It does not change the crook or any gameplay yet.

INSTALL
1. Close the game. Copy Mods/SpearReferenceProbe into ue4ss/Mods.
2. Add SpearReferenceProbe : 1 to your existing mods.txt, once. Keep all other files/entries and Paks unchanged. No installer or keybind.
3. Launch normally and load Bo Peep/Willow. Equip the same reference spear from your inventory. A brief pause may occur once while UE4SS writes native type mappings.

ONE SHORT RECORDING (about30-45seconds)
- First person: hold the native spear still2seconds, then do3 separate normal jabs into empty space.
- Third person: hold still2seconds, then do3 normal jabs.
- Unequip the spear so BOTH actual hand slots are empty: stand2seconds, then do2 unarmed attacks.
- Exit normally and send the two outputs below. No screenshots or damage target needed for this collection. Do not wait for its optional automatic2minute/600frame safety stop.

SEND TWO FILES
1. The latest UE4SS.log.
2. The newly generated file ending .usmap. It is normally beside UE4SS.log/UE4SS.dll in the ue4ss folder (or its game-specific subfolder). Its exact filename is printed by UE4SS as 'Output file: ...usmap', normally <GameName>-<EngineVersion>-<UE4SSCommitSHA>.usmap. If necessary, search the game's Binaries folder for *.usmap sorted by date. If there is no .usmap, send the log anyway; do not repeat the session just for that.

AFTERWARDS
Remove the SpearReferenceProbe : 1 line and its folder after collection. Your accepted character/crook/wing files are unchanged. Damage changes are NOT implemented by this probe. The target remains native spear animations/reach with unarmed-level damage.

VALIDATION
13 mocked-Lua groups pass, including read-only bounds/poses/row capture, absent mapping dumper, optional native failures, client authority false and bounded self-stop. This does not establish Windows function availability. All new UFunction/property accesses check live metadata. No raw memory offsets, RPCs, attack execution, component creation or installed-mod edits. No scripts to run.
'''
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('README.txt',readme)
 for p in sorted((root/'runtime-spear-reference/SpearReferenceProbe').rglob('*')):
  if p.is_file():z.write(p,'Mods/SpearReferenceProbe/'+str(p.relative_to(root/'runtime-spear-reference/SpearReferenceProbe')))
with zipfile.ZipFile(dst) as z:assert z.testzip() is None;assert len(z.namelist())==3;assert all(not n.endswith(('.pak','.ucas','.utoc')) for n in z.namelist())
report={'file':dst.name,'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'status':'READ_ONLY_PROBE_WINDOWS_PENDING','mocked_groups':13,'uploads':['UE4SS.log','new native .usmap'],'existing_animation_packages_recollected':False};(root/'docs/spear-reference/package.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
