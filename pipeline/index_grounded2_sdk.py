"""Index only character-feature definitions in the published SDK; no game execution."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
classes={
'Maine.MaineCharMovementComponent':r'IsGliding|GetGlidingStyle|GetCameraDisplayMode|IsSitting|IsClimbing|IsZiplining|OnGliderMovementModeChanged',
'Maine.EquipmentComponent':r'\bbHasMainHand\b|\bbHasOffHand\b|\bMainHand\b|\bOffHand\b|GetItemInSlot|GetWeapon\(|GetStance|GetOffhandStance|SpawnVisuals|DestroyVisuals|HideSlot|UnhideSlot',
'Maine.SurvivalCharacter':r'CharMovementComponent|EquipmentComponent|InventoryComponent|GetIsFirstPerson|GetCameraDisplayMode|MulticastGliderVisuals|MulticastPlayAttackAnimMontage|CurrentAttack',
'Maine.InventoryComponent':r'UsingGliderItem|BestGliderItem|BestGliderQty',
'Maine.CharacterAnimInstance':r'\bStance\b|OffhandStance|IsFirstPerson|GlidingStyle|HasWeapon',
'Maine.Attack':r'GetAnimMontage|GetAttackDataRowHandle|GetCurrentStaminaCost|GetAttackRange',
'AB_Player_Character.AB_Player_Character_C':r'WeaponStances|IsPlayerFirstPerson',
'DAC_StanceAnimationKit.DAC_StanceAnimationKit_C':r'StandIdle|FP_Idle|BS_StandWalkRun',
}
records=[];enums={}
with zipfile.ZipFile(a.archive) as z:
 assert z.testzip() is None
 header=z.read('SDK.hpp').decode('utf-8-sig');version=next(l.strip('/ ').strip() for l in header.splitlines() if '+++Augusta+' in l)
 for name in ['Maine_classes.hpp','AB_Player_Character_classes.hpp','DAC_StanceAnimationKit_classes.hpp']:
  owner=None
  for line,text in enumerate(z.read('SDK/'+name).decode('utf-8-sig').splitlines(),1):
   m=re.match(r'// (?:Class|BlueprintGeneratedClass) (\S+)',text)
   if m:owner=m[1]
   if owner in classes and re.search(classes[owner],text) and not text.startswith('//'):
    records.append({'owner':owner,'file':'SDK/'+name,'line':line,'declaration':text.split('//',1)[0].strip()})
 s=z.read('SDK/Maine_structs.hpp').decode('utf-8-sig')
 for enum in ['EEquipmentSlot','ECameraDisplayMode','EGlidingStyle','EMaineCustomMovementMode']:
  m=re.search(r'enum class '+enum+r'\b[^\{]*\{(.*?)\};',s,re.S);assert m,enum
  enums[enum]={k:int(v) for k,v in re.findall(r'(\w+)\s*=\s*(\d+)',m[1])}
 funcs=z.read('SDK/Maine_functions.cpp').decode('utf-8-sig')
 paths=['Maine.MaineCharMovementComponent.IsGliding','Maine.MaineCharMovementComponent.GetGlidingStyle','Maine.SurvivalCharacter.GetIsFirstPerson','Maine.EquipmentComponent.GetItemInSlot','Maine.EquipmentComponent.GetStance','Maine.Attack.GetAnimMontage']
 flags={}
 for path in paths:
  m=re.search(r'// Function '+re.escape(path)+r'\r?\n// (.*)',funcs);assert m,path;flags[path]=m[1]
assert any('bool IsGliding() const;'==r['declaration'] for r in records)
assert any('GetItemInSlot(EEquipmentSlot Slot)' in r['declaration'] for r in records)
report={'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'archive_sha384':hashlib.sha384(a.archive.read_bytes()).hexdigest(),'generated_header_build':version,'scope':'Static SDK evidence only; target runtime not validated; never reuse offsets','definitions':records,'enum_definitions':enums,'function_flags':flags}
a.out.write_text(json.dumps(report,indent=2)+'\n');print('SDK_INDEX_PASS',len(records),'definitions;',len(enums),'enums;',len(flags),'function signatures')
