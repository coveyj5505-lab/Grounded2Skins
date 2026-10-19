"""Lua regression checks for isolated crook component lifecycle; not native UE4SS validation."""
import ctypes,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/'runtime/BoPeepCrook/Scripts/main.lua').read_text()
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
local events={}
print=function(s) events[#events+1]=s end
Key={F9=120};function RegisterKeyBind(k,fn) key=fn end
function LoopAsync(ms,fn) assert(ms==200);timer=fn end
function ExecuteInGameThread(fn) fn() end
function FName(s) return s end
function LoadAsset(s) assert(s:find('_BoCrook',1,true)) end
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
local asset=obj('SkeletalMesh /Game/_BoCrook/Asset',{'Engine.SkeletalMesh'})
local item=obj('Item Equipped',{'Maine.Item'})
local body=obj('SkeletalMeshComponent Body',{'Engine.SkeletalMeshComponent','Engine.SkinnedMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent'})
body.SkeletalMeshAsset=obj('SkeletalMesh /Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01',{'Engine.SkeletalMesh'})
body.SkeletalMeshAsset.GetFullName=function() return female and 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01' or 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01' end
body.DoesSocketExist=function(self,b) assert(b=='r_hand_JNT');return true end
body.GetSocketTransform=function() return {Rotation={X=0,Y=0,Z=0,W=1}} end
local eq=obj('EquipmentComponent Equipment',{'Maine.EquipmentComponent'})
eq.GetItemInSlot=function(self,slot) assert(slot==17 or slot==29);return ((slot==17 and main) or (slot==29 and off)) and item or invalid end
local p=obj('BP_SurvivalPlayerCharacter_Female01_C Player',{'Maine.SurvivalCharacter','Engine.Character','Engine.Actor'})
p.Mesh=body;p.EquipmentComponent=eq
p.GetFullName=function() return female and 'BP_SurvivalPlayerCharacter_Female01_C Player' or 'BP_SurvivalPlayerCharacter_Male01_C Player' end
p.GetIsFirstPerson=function() return fp end
local c
p.AddComponentByClass=function(self,cls,manual,t,deferred)
 assert(manual and deferred);made=made+1
 c=obj('SkeletalMeshComponent Cosmetic',{'Engine.SkeletalMeshComponent','Engine.SkinnedMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent','Engine.ActorComponent'})
 c.SetHiddenInGame=function(self,v,prop) assert(not prop);show=not v end
 c.SetVisibility=function(self,v,prop) assert(not prop);show=v end
 c.SetCollisionEnabled=function(self,v) assert(v==0);collision=true end
 c.SetSimulatePhysics=function(self,v) assert(not v) end
 c.SetDisablePostProcessBlueprint=function(self,v) assert(v);post=true end
 c.SetEnableAnimation=function(self,v) assert(not v);anim=true end
 c.SetAllowClothActors=function(self,v) assert(not v) end
 c.SetOnlyOwnerSee=function(self,v) assert(not v) end
 c.SetOwnerNoSee=function(self,v) assert(not v) end
 c.SetSkeletalMeshAsset=function(self,v) assert(collision and post and anim and not show);assert(v==asset);meshSet=true end
 c.K2_AttachToComponent=function(self,parent,bone,l,r,s,weld) assert(parent==body and bone=='r_hand_JNT' and not weld);return true end
 c.K2_SetRelativeTransform=function(self,t,sweep,hit,teleport) assert(t.Rotation.W==1 and not sweep and teleport) end
 c.K2_DestroyComponent=function() destroyed=destroyed+1;c.IsValid=function() return false end end
 return c
end
p.FinishAddComponent=function() assert(meshSet and collision and post and anim) end
function FindAllOf(name) assert(name=='PlayerController');return {{IsValid=function() return true end,IsLocalController=function() return true end,Pawn=p}} end
local function desc(name,kind) return {GetFullName=function() return kind..' Test.Owner:'..name end} end
function StaticFindObject(path)
 if path:find('_BoCrook',1,true) then return missingAsset and invalid or asset end
 local fields={['/Script/Engine.Character']={Mesh='ObjectProperty'},['/Script/Maine.SurvivalCharacter']={EquipmentComponent='ObjectProperty'}}
 if fields[path] then return {IsValid=function() return true end,ForEachProperty=function(self,f) for n,t in pairs(fields[path]) do f(desc(n,t)) end end} end
 local enumMaps={['/Script/Maine.EEquipmentSlot']={MainHand=17,OffHand=29},['/Script/Engine.ECollisionEnabled']={NoCollision=0},['/Script/Engine.EAttachmentRule']={SnapToTarget=2},['/Script/Engine.ERelativeTransformSpace']={RTS_World=0}}
 if enumMaps[path] then return {IsValid=function() return true end,ForEachName=function(self,f) for n,v in pairs(enumMaps[path]) do f({ToString=function() return n end},v) end end} end
 if path=='/Script/Engine.SkeletalMeshComponent' then return obj('Class '..path,{'CoreUObject.Class'}) end
 if specs[path] then return {IsValid=function() return true end,ForEachProperty=function(self,f) for n,t in pairs(specs[path]) do f(desc(n,bad and 'WrongProperty' or t)) end end} end
 return invalid
end
'''.replace('SPECS',',\n'.join(specs))
checks=[
("valid Willow mesh with unexpected Blueprint name", "p.GetFullName=function() return 'BP_ActualWillowVariant_C Player' end;key();assert(made==1 and show)"),
("wrong mesh explains why nothing attaches", "female=false;key();assert(made==0);assert(table.concat(events,'\\n'):find('WAIT: Willow mesh required',1,true))"),
("attachment, safety ordering, actual slots, both views, cleanup", "key();assert(made==1 and show);main=true;timer();assert(not show);main=false;off=true;timer();assert(not show);off=false;timer();assert(show);fp=true;timer();assert(show);key();assert(destroyed==1 and not show)"),
("signature rejection before creation", "bad=true;key();assert(made==0);timer();assert(made==0)"),
("missing asset before creation", "missingAsset=true;key();assert(made==0)"),
("only Willow mesh gets accessory", "female=false;key();assert(made==0)"),
("player swap removes accessory", "key();assert(show);female=false;timer();assert(destroyed==1 and not show)"),
]
for name,checksLua in checks:
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 code=(pre+'\n'+source+'\n'+checksLua).encode()
 result=lib.luaL_loadstring(state,code)
 if result==0:result=lib.lua_pcallk(state,0,0,0,0,None)
 error=lib.lua_tolstring(state,-1,None) if result else None
 lib.lua_close(state)
 assert not result,(name,error)
 print('PASS',name)
