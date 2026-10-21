import os
"""Lua regression checks for isolated crook component lifecycle; not native UE4SS validation."""
import ctypes,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(Path(os.environ.get('TOYSTORY_RUNTIME_ROOT',str(root/'runtime')))/'BoPeepCrook/Scripts/main.lua').read_text()
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
lib.lua_close.argtypes=[ctypes.c_void_p]
specs=[]
for owner,method,args in re.findall(r"spec\('([^']+)','([^']+)',(\{[^\n]+\})\)",source):
    specs.append("['/Script/"+owner+':'+method+"']="+args)
pre=r'''
local enum='EnumProperty'
local specs={SPECS}
local key,timer;local made=0;local destroyed=0;local show=false;local main=false;local off=false;local female=true;local fp=false;local bad=false;local missingAsset=false;local collision=false;local anim=false;local post=false;local meshSet=false
local events={};local nativeHandVisible=false
print=function(s) events[#events+1]=s end
Key={F9=120};function RegisterKeyBind(k,fn) key=fn end
function LoopAsync(ms,fn) assert(ms==200);timer=fn end
function ExecuteInGameThread(fn) fn() end
function FName(s) return s end
function LoadAsset(s) error('Registry-only UE4SS LoadAsset forbidden for new private assets') end
local function obj(name,classes)
 local o={IsValid=function() return true end,GetFullName=function() return name end,type=function() return 'UObject' end}
 o.Reflection=function() error('Reflection forbidden') end
 o.GetClass=function()
  local function cls(i)
   if not classes[i] then return nil end
   return {IsValid=function() return true end,GetFullName=function() return 'Class /Script/'..classes[i] end,GetSuperStruct=function() return cls(i+1) end}
  end
  return cls(1)
 end
 return o
end
local invalid={IsValid=function() return false end}
local asset=obj('SkeletalMesh /Game/_BoCrTP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01',{'Engine.SkeletalMesh'})
local system=obj('KismetSystemLibrary /Script/Engine.Default__KismetSystemLibrary',{'Engine.KismetSystemLibrary'})
system.MakeSoftObjectPath=function(self,path) assert(path:find('/Game/_BoCr',1,true));return {Path=path} end
system.Conv_SoftObjPathToSoftObjRef=function(self,path) assert(path.Path);return {SoftPath=path.Path} end
system.LoadAsset_Blocking=function(self,soft) assert(soft.SoftPath:find('/Game/_BoCr',1,true));return missingAsset and invalid or (soft.SoftPath:find('_BoCrTP1',1,true) and asset or obj('SkeletalMesh '..soft.SoftPath,{'Engine.SkeletalMesh'})) end
local item=obj('Item Equipped',{'Maine.Item'})
local body=obj('SkeletalMeshComponent Body',{'Engine.SkeletalMeshComponent','Engine.SkinnedMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent'})
body.SkeletalMeshAsset=obj('SkeletalMesh /Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01',{'Engine.SkeletalMesh'})
body.SkeletalMeshAsset.GetFullName=function() return female and 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01' or 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01' end
body.GetSkeletalMeshAsset=function() return body.SkeletalMeshAsset end
body.DoesSocketExist=function(self,b) assert(b=='r_hand_JNT');return true end
body.GetSocketTransform=function(self,bone) return {Rotation={X=0,Y=0,Z=0,W=1},Translation=bone=='None' and {X=0,Y=0,Z=0} or (nativeHandVisible and {X=50,Y=20,Z=-10} or {X=-10,Y=30,Z=-60})} end
local eq=obj('EquipmentComponent Equipment',{'Maine.EquipmentComponent'})
eq.GetItemInSlot=function(self,slot) assert(slot==17 or slot==29);return ((slot==17 and main) or (slot==29 and off)) and item or invalid end
local p=obj('BP_SurvivalPlayerCharacter_Female01_C Player',{'Maine.SurvivalCharacter','Engine.Character','Engine.Actor'})
p.Mesh=body;p.EquipmentComponent=eq;p.bIsAttacking=false
p.K2_GetComponentsByClass=function() return {body} end
p.GetFullName=function() return female and 'BP_SurvivalPlayerCharacter_Female01_C Player' or 'BP_SurvivalPlayerCharacter_Male01_C Player' end
p.GetIsFirstPerson=function() return fp end
p.GetFirstPersonCamera=function() return body end
p.K2_GetActorRotation=function() return {Pitch=0,Yaw=0,Roll=0} end
local c
p.AddComponentByClass=function(self,cls,manual,t,deferred)
 assert(manual and deferred);made=made+1
 c=obj('SkeletalMeshComponent Cosmetic',{'Engine.SkeletalMeshComponent','Engine.SkinnedMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent','Engine.ActorComponent'})
 c.SetHiddenInGame=function(self,v,prop) assert(not prop);show=not v end
 c.IsVisible=function() return show end
 c.SetVisibility=function(self,v,prop) assert(not prop);show=v end
 c.SetCollisionEnabled=function(self,v) assert(v==0);collision=true end
 c.SetSimulatePhysics=function(self,v) assert(not v) end
 c.SetDisablePostProcessBlueprint=function(self,v) assert(v);post=true end
 c.SetEnableAnimation=function(self,v) assert(not v);anim=true end
 c.SetAllowClothActors=function(self,v) assert(not v) end
 c.SetOnlyOwnerSee=function(self,v) assert(not v) end
 c.SetOwnerNoSee=function(self,v) assert(not v) end
 c.SetSkeletalMeshAsset=function(self,v) assert(collision and post and anim and not show);assert(v:GetFullName():find('/Game/_BoCr',1,true));meshSet=true;self.asset=v:GetFullName() end
 c.SetAbsolute=function(self,loc,rot,scale) assert(not loc and not scale);self.absoluteRotation=rot end
 c.K2_AttachToComponent=function(self,parent,bone,l,r,s,weld) assert(parent==body and (bone=='r_hand_JNT' or bone=='None') and not weld);self.socket=bone;return true end
 c.K2_SetRelativeTransform=function(self,t,sweep,hit,teleport) assert(not sweep and teleport);self.lastTransform=t end
 c.K2_DestroyComponent=function() destroyed=destroyed+1;c.IsValid=function() return false end end
 return c
end
p.FinishAddComponent=function() assert(meshSet and collision and post and anim) end
function FindAllOf(name) assert(name=='PlayerController');return {{IsValid=function() return true end,IsLocalController=function() return true end,Pawn=p}} end
local function desc(name,kind) return {GetFullName=function() return kind..' Test.Owner:'..name end} end
function StaticFindObject(path)
 if path=='/Script/Engine.Default__KismetSystemLibrary' then return system end
 if path:find('_BoCrook',1,true) then return missingAsset and invalid or (soft.SoftPath:find('_BoCrTP1',1,true) and asset or obj('SkeletalMesh '..soft.SoftPath,{'Engine.SkeletalMesh'})) end
 local fields={['/Script/Engine.Character']={Mesh='ObjectProperty'},['/Script/Maine.SurvivalCharacter']={EquipmentComponent='ObjectProperty',bIsAttacking='BoolProperty'}}
 if fields[path] then return {IsValid=function() return true end,ForEachProperty=function(self,f) for n,t in pairs(fields[path]) do f(desc(n,t)) end end} end
 local enumMaps={['/Script/Maine.EEquipmentSlot']={MainHand=17,OffHand=29},['/Script/Engine.ECollisionEnabled']={NoCollision=0},['/Script/Engine.EAttachmentRule']={SnapToTarget=2},['/Script/Engine.ERelativeTransformSpace']={RTS_World=0}}
 if enumMaps[path] then return {IsValid=function() return true end,ForEachName=function(self,f) for n,v in pairs(enumMaps[path]) do f({ToString=function() return n end},v) end end} end
 if path=='/Script/Engine.SkeletalMeshComponent' then return obj('Class '..path,{'CoreUObject.Class'}) end
 if specs[path] then return {IsValid=function() return true end,ForEachProperty=function(self,f) for n,t in pairs(specs[path]) do f(desc(n,bad and 'WrongProperty' or t)) end end} end
 return invalid
end
'''.replace('SPECS',',\n'.join(specs))
# Track visibility/lifetime per component: persistent views must not share fixture state.
pre=pre.replace("c.IsVisible=function() return show end", "c.IsVisible=function(self) return self.testVisible==true end")
pre=pre.replace("c.SetVisibility=function(self,v,prop) assert(not prop);show=v end", "c.SetVisibility=function(self,v,prop) assert(not prop);self.testVisible=v;show=v;if v then c=self end end")
pre=pre.replace("c.K2_DestroyComponent=function() destroyed=destroyed+1;c.IsValid=function() return false end end", "c.K2_DestroyComponent=function(self) destroyed=destroyed+1;self.IsValid=function() return false end end")
checks=[
("cached FP-to-TP return performs no load/create/destroy/reparent/mesh assignment", "timer();local tp=c;fp=true;timer();local first=c;local function forbidden() error('view return attempted native lifecycle mutation') end;p.AddComponentByClass=forbidden;system.LoadAsset_Blocking=forbidden;for _,o in ipairs({tp,first}) do o.SetSkeletalMeshAsset=forbidden;o.K2_DestroyComponent=forbidden;o.K2_AttachToComponent=forbidden end;fp=false;timer();assert(show and c==tp);fp=true;timer();assert(show and c==first and made==2 and destroyed==0)"),
("view transitions never reassign a registered crook mesh", "local add=p.AddComponentByClass;p.AddComponentByClass=function(...) local o=add(...);local setter=o.SetSkeletalMeshAsset;local assigned=false;o.SetSkeletalMeshAsset=function(self,mesh) assert(not assigned,'registered crook mesh reassigned');assigned=true;return setter(self,mesh) end;return o end;timer();fp=true;timer();fp=false;timer();assert(made==2 and destroyed==0 and show and c.socket=='r_hand_JNT');local count=made;for i=1,4 do fp=true;timer();fp=false;timer() end;assert(made==count and destroyed==0)"),
("copied hand omitted when native hand enters conservative view cone", "fp=true;timer();assert(c.asset:find('_BoCrFP1',1,true));nativeHandVisible=true;timer();assert(c.asset:find('_BoCrFN1',1,true) and show);nativeHandVisible=false;timer();assert(c.asset:find('_BoCrFP1',1,true))"),
("optional hand transform failure preserves staff-only carry", "body.GetSocketTransform=function(self,bone) if bone=='None' then error('camera transform unavailable') end;return {Rotation={X=0,Y=0,Z=0,W=1}} end;fp=true;timer();assert(show and c.asset:find('_BoCrFN1',1,true))"),
("wrong installed container revision stops before native creation", "io.open=function() return {read=function() return 'wrong' end,seek=function() return 1 end,close=function() end} end;timer();assert(made==0);assert(table.concat(events,'\\n'):find('Wrong container revision installed',1,true))"),
("automatic startup waits safely at menus before gameplay", "local find=FindAllOf;FindAllOf=function() return {} end;timer();assert(made==0);local menu=obj('MenuPawn Preview',{'Engine.Actor'});FindAllOf=function() return {{IsValid=function() return true end,IsLocalController=function() return true end,Pawn=menu}} end;timer();assert(made==0);FindAllOf=find;timer();assert(show)"),
("automatic startup without key and debug suspend/resume", "timer();assert(made==1 and show);key();assert(not show and destroyed==1);key();assert(show and made==2)"),
("unknown owned component wrapper skipped safely", "p.Mesh=nil;p.K2_GetComponentsByClass=function() return {{Other=true},body} end;timer();assert(show)"),
("unknown equipment wrapper never guessed empty", "eq.GetItemInSlot=function() return {} end;timer();assert(not show);assert(table.concat(events,'\\n'):find('no empty%-slot guess'))"),
("optional attack getter failure does not block carry", "p.bIsAttacking={};timer();assert(show)"),
("FP source grip omitted during actual native attack and restored afterward", "fp=true;timer();assert(c.asset:find('_BoCrFP1',1,true));p.bIsAttacking=true;timer();assert(c.asset:find('_BoCrFN1',1,true) and show and c.lastTransform.Rotation.Y>0);p.bIsAttacking=false;timer();assert(c.asset:find('_BoCrFP1',1,true) and c.lastTransform.Rotation.Y==0)"),
("measured palm offset and upright carry frame", "key();local t=c.lastTransform;assert(math.abs(t.Translation.X-(6.34267822))<1e-6);assert(math.abs(t.Translation.Y-(0.00091054))<1e-6);assert(math.abs(t.Translation.Z-(-0.88787583))<1e-6);assert(c.absoluteRotation==true and t.Scale3D.Z==1)"),
("first-person accessory reparenting and return without camera movement", "key();fp=true;timer();assert(c.socket=='None' and c.absoluteRotation==false);assert(c.lastTransform.Translation.X==75 and c.lastTransform.Translation.Y==43);main=true;timer();assert(not show);main=false;fp=false;timer();assert(show and c.socket=='r_hand_JNT' and c.absoluteRotation==true)"),
("attachment rejection logs final error and destroys cosmetic", "local make=p.AddComponentByClass;p.AddComponentByClass=function(...) local created=make(...);created.K2_AttachToComponent=function() return false end;return created end;key();assert(made==1 and destroyed==1 and not show);assert(table.concat(events,'\\n'):find('phase=hand%-attachment'))"),
("visibility readback mismatch removes cosmetic and logs phase", "local make=p.AddComponentByClass;p.AddComponentByClass=function(...) local created=make(...);created.IsVisible=function() return false end;return created end;key();assert(destroyed==1 and not show);assert(table.concat(events,'\\n'):find('phase=visibility',1,true))"),
("six separately logged milestones and successful final readback", "key();local text=table.concat(events,'\\n');for i=1,6 do assert(text:find('MILESTONE '..i..'/6',1,true)) end;assert(text:find('RESULT SUCCESS',1,true))"),
("failed load reports exact path and phase without component creation", "missingAsset=true;key();local text=table.concat(events,'\\n');assert(made==0);assert(text:find('phase=asset%-load'));assert(text:find('/Game/_BoCrTP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01',1,true));assert(text:find('RESULT ERROR',1,true))"),
("native loader works without asset-registry helper or preloaded object", "key();assert(made==1 and show);assert(table.concat(events,'\\n'):find('LOAD RESULT SkeletalMesh',1,true))"),
("native getter succeeds without guessed asset property", "local actual=body.SkeletalMeshAsset;body.SkeletalMeshAsset=nil;body.GetSkeletalMeshAsset=function() return actual end;key();assert(made==1 and show)"),
("empty base Mesh falls back to owned Willow component", "local empty=obj('SkeletalMeshComponent Empty',{'Engine.SkeletalMeshComponent'});empty.GetSkeletalMeshAsset=function() return invalid end;p.Mesh=empty;key();assert(made==1 and show)"),
("valid Willow mesh with unexpected Blueprint name", "p.GetFullName=function() return 'BP_ActualWillowVariant_C Player' end;key();assert(made==1 and show)"),
("wrong mesh explains why nothing attaches", "female=false;key();assert(made==0);assert(table.concat(events,'\\n'):find('WAIT: no owned component uses verified Willow mesh',1,true))"),
("attachment, safety ordering, actual slots, both views, cleanup", "key();assert(made==1 and show);main=true;timer();assert(not show);main=false;off=true;timer();assert(not show);off=false;timer();assert(show);fp=true;timer();assert(show and c.socket=='None' and c.absoluteRotation==false and c.lastTransform.Translation.X==75);fp=false;timer();assert(c.socket=='r_hand_JNT' and c.absoluteRotation==true);key();assert(destroyed==1 and not show)"),
("signature rejection before creation", "bad=true;key();assert(made==0);timer();assert(made==0)"),
("missing asset before creation", "missingAsset=true;key();assert(made==0)"),
("only Willow mesh gets accessory", "female=false;key();assert(made==0)"),
("player swap removes accessory", "key();assert(show);female=false;timer();assert(destroyed==1 and not show)"),
]
for name,checksLua in checks:
 if os.environ.get('TOYSTORY_RUNTIME_ROOT'): checksLua=checksLua.replace('Translation.Y==43','Translation.Y==50').replace('Translation.X==75','Translation.X==65')
 if os.environ.get('TOYSTORY_RUNTIME_ROOT') and name=='attachment, safety ordering, actual slots, both views, cleanup': checksLua=checksLua.replace('destroyed==1','destroyed==2')
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 if not checksLua.startswith('timer();') and not checksLua.startswith('fp=true;timer();'):checksLua=checksLua.replace('key();','timer();',1)
 code=(pre+'\n'+source+'\n'+checksLua).encode()
 result=lib.luaL_loadstring(state,code)
 if result==0:result=lib.lua_pcallk(state,0,0,0,0,None)
 error=lib.lua_tolstring(state,-1,None) if result else None
 lib.lua_close(state)
 assert not result,(name,error)
 print('PASS',name)
