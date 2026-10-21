"""Run actual Lua probe with native reflection fixtures and injected failures."""
import ctypes,re,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];source=(root/'runtime-spear-reference/SpearReferenceProbe/Scripts/main.lua').read_text();original=(root/'pipeline/feedback-v4/test_crook.py').read_text();pre=original.split("pre=r'''",1)[1].split("'''.replace",1)[0];specs=[]
for name,args in re.findall(r"\['([^']+)'\]=(\{[^\n]+\})",source):
 owner,method=name.rsplit('.',1);args=args.replace('ByteProperty|EnumProperty','EnumProperty').replace('FloatProperty|DoubleProperty','FloatProperty');specs.append("['/Script/"+owner+':'+method+"']="+args)
pre=pre.replace('SPECS',',\n'.join(specs)).replace('assert(ms==200)','assert(ms==50)')
pre+='''
local dumps=0;local reads=0
function DumpUSMAP(include) assert(include==false);dumps=dumps+1 end
body.DoesSocketExist=function() return true end
local nativeMesh=obj('StaticMesh /Game/_Augusta/Art/Items/Weapons/Spear/SpearPebble.SpearPebble',{'Engine.StaticMesh'})
local weapon=obj('StaticMeshComponent Spear.StaticMesh',{'Engine.StaticMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent'})
weapon.StaticMesh=nativeMesh;weapon.GetSocketTransform=body.GetSocketTransform
weapon.GetAttachParent=function() return body end
weapon.GetAttachSocketName=function() return {ToString=function() return 'r_hand_JNT' end} end
weapon.GetLocalBounds=function(self,lo,hi) lo.X=-3;lo.Y=-3;lo.Z=-60;hi.X=3;hi.Y=3;hi.Z=100 end
local visual=obj('BP_Weapon_Spear_C ItemVisual',{'Maine.SpawnedItem','Engine.Actor'})
visual.K2_GetComponentsByClass=function() return {{type=function() return 'RemoteUnrealParam' end,get=function() return weapon end}} end
item.GetItemVisuals=function() return visual end
local montage=obj('AnimMontage /Game/AM_Spear.AM_Spear',{'Engine.AnimMontage'})
local instance=obj('AnimInstance SpearInstance',{'Engine.AnimInstance'})
instance.GetCurrentActiveMontage=function() return montage end
instance.Montage_GetPosition=function(self,m) assert(m==montage);return .15 end
body.GetAnimInstance=function() return instance end
local tableObj=obj('DataTable /Game/DT_Attacks.DT_Attacks',{'Engine.DataTable'})
local function handle(name) return {DataTable=tableObj,RowName={ToString=function() return name end}} end
local attack=obj('Attack SpearAttack',{'Maine.Attack'})
attack.GetAttackDataRowHandle=function() return handle('SpearAttack') end
attack.GetAttackRange=function() return 250 end
attack.GetChargedAttackRange=function() return 300 end
attack.GetAnimMontage=function() return montage end
local fist=obj('Attack UnarmedAttack',{'Maine.Attack'})
fist.GetAttackDataRowHandle=function() return handle('UnarmedAttack') end
fist.GetAttackRange=function() return 100 end
fist.GetChargedAttackRange=function() return 100 end
fist.GetAnimMontage=function() return invalid end
p.GetDefaultAttack=function() return fist end
p.GetCurrentAttack=function() return main and attack or fist end
item.GetItemDataRowHandle=function() return handle('PebbleSpear') end
item.GetAttackDamageModifier=function() return 1 end
item.CustomAttackMultiplier=1
local combo=obj('AttackCombo SpearCombo',{'Maine.AttackCombo'})
combo.Attacks={ForEach=function(self,fn) fn(1,{type=function() return 'RemoteUnrealParam' end,get=function() return attack end}) end}
item.AttackCombo=combo
local clock=obj('GameplayStatics /Script/Engine.Default__GameplayStatics',{'Engine.GameplayStatics'})
clock.GetTimeSeconds=function(self,ctx) assert(ctx==p);reads=reads+1;return reads*.05 end
local find=StaticFindObject
function StaticFindObject(path)
 if path=='/Script/Engine.Default__GameplayStatics' then return clock end
 if path=='/Script/Engine.PrimitiveComponent' then return obj('Class '..path,{'CoreUObject.Class'}) end
 local fields={['/Script/Engine.StaticMeshComponent']={StaticMesh='ObjectProperty'},['/Script/Maine.Item']={AttackCombo='ObjectProperty',CustomAttackMultiplier='FloatProperty'},['/Script/Maine.AttackCombo']={Attacks='ArrayProperty'}}
 if fields[path] then return {IsValid=function() return true end,ForEachProperty=function(self,fn) for n,t in pairs(fields[path]) do fn(desc(n,t)) end end} end
 return find(path)
end
local function output() return table.concat(events,'\\n') end
'''
checks=[
('menu/empty hands wait without mapping dump','timer();assert(dumps==0 and not output():find("SPEAR_FRAME",1,true))'),
('equipped spear captures assets poses attack rows and one native-only map','main=true;timer();timer();assert(dumps==1);assert(output():find("SPEAR_COMPONENT",1,true));assert(output():find("SpearPebble",1,true));assert(output():find("UnarmedAttack",1,true));assert(output():find("SpearAttack",1,true));assert(output():find("localBounds",1,true));assert(made==0 and destroyed==0)'),
('unarmed comparison after spear retains default and current attack','main=true;timer();main=false;timer();p.bIsAttacking=true;timer();assert(output():find("UnarmedAttack",1,true));assert(dumps==1)'),
('default unarmed damage getter captured when supported',"system.Conv_ClassToSoftClassReference=function(self,cls) return {SoftClass=cls} end;local ui=obj('UserInterfaceStatics /Script/Maine.Default__UserInterfaceStatics',{'Maine.UserInterfaceStatics'});ui.GetDefaultBaseDamageFirstAttackOfCharacter=function(self,ctx,cls) assert(ctx==p and cls.SoftClass);return 5 end;local old=StaticFindObject;StaticFindObject=function(path) if path=='/Script/Maine.Default__UserInterfaceStatics' then return ui end;return old(path) end;main=true;timer();assert(output():find('\"baseUnarmedDamage\":5',1,true))"),
('client authority false is preserved as a JSON boolean',"p.HasAuthority=function() return false end;main=true;timer();assert(output():find('\"authority\":false',1,true))"),
('missing optional map global does not stop pose capture','DumpUSMAP=nil;main=true;timer();assert(output():find("MAPPINGS UNAVAILABLE",1,true));assert(output():find("SPEAR_FRAME",1,true))'),
('map dumper failure preserves independent pose capture','DumpUSMAP=function() error("mock disk failure") end;main=true;timer();assert(output():find("MAPPINGS FAILED",1,true));assert(output():find("SPEAR_FRAME",1,true))'),
('bad function metadata stops calls before invocation','bad=true;main=true;timer();assert(dumps==0 and not output():find("SPEAR_FRAME",1,true))'),
('optional montage getter failure leaves hand transforms','instance.GetCurrentActiveMontage=function() error("optional unavailable") end;main=true;timer();assert(output():find("SPEAR_FRAME",1,true));assert(output():find("r_hand_JNT",1,true))'),
('late missing item visuals leave body and attack sources','item.GetItemVisuals=function() return invalid end;main=true;timer();assert(output():find("SPEAR_FRAME",1,true));assert(output():find("UnarmedAttack",1,true))'),
('game-thread dispatch failure stops safely','ExecuteInGameThread=function() error("mock dispatch failure") end;main=true;timer();assert(dumps==0 and output():find("DISPATCH STOP",1,true))'),
('bounded recording self-stops without any native mutations','main=true;p.bIsAttacking=true;for i=1,650 do timer() end;assert(output():find("COMPLETE frames=600",1,true));local count=#events;timer();assert(#events==count and made==0 and destroyed==0 and dumps==1)'),
('FP and TP transitions capture both views','main=true;fp=true;timer();fp=false;timer();assert(output():find("\\\"firstPerson\\\":true",1,true));assert(output():find("\\\"firstPerson\\\":false",1,true))'),
]
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p;lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
for name,tail in checks:
 state=lib.luaL_newstate();lib.luaL_openlibs(state);result=lib.luaL_loadstring(state,(pre+'\n'+source+'\n'+tail).encode())
 if not result:result=lib.lua_pcallk(state,0,0,0,0,None)
 error=lib.lua_tolstring(state,-1,None) if result else None;lib.lua_close(state);assert not result,(name,error);print('PASS',name)
(root/'docs/spear-reference/probe-regressions.json').write_text(json.dumps({'status':'PASS_MOCKED_LUA_NOT_WINDOWS','groups':len(checks),'checks':[n for n,_ in checks]},indent=2)+'\n')
