"""Execute targeted runtime Lua against mocks. No native UE4SS safety claim."""
import ctypes
from pathlib import Path
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
root=Path(__file__).resolve().parents[1]
pre=r'''
local lines={};print=function(s) table.insert(lines,s) end
local wall=1000;os.time=function() return wall end
function StaticConstructObject() error('unexpected actor/component creation') end
function RegisterHook() error('unexpected hook') end
local keys={};local timer;local queued;local first=false;local glide=false;local main=false;local off=false;local mismatch=false;local wrongReceiver=false;local menu=false;local attackActive=false;local writes=0;local remoteCalls=0;local calls=0
Key={F9=120,F10=121}
function RegisterKeyBind(k,f) assert(type(f)=='function');keys[k]=f end
function LoopAsync(ms,f) assert(ms==500);timer=f end
function ExecuteInGameThread(f) assert(not queued);queued=f end
local function flush() local f=queued;queued=nil;if f then f() end end
local function tick() timer();flush() end
local methods={
 ['Maine.SurvivalCharacter:GetIsFirstPerson']={ReturnValue='BoolProperty'},
 ['Maine.SurvivalCharacter:GetCameraDisplayMode']={ReturnValue='EnumProperty'},
 ['Maine.SurvivalCharacter:GetCurrentAttack']={ReturnValue='ObjectProperty'},
 ['Maine.MaineCharMovementComponent:IsGliding']={ReturnValue='BoolProperty'},
 ['Maine.MaineCharMovementComponent:GetGlidingStyle']={ReturnValue='EnumProperty'},
 ['Maine.EquipmentComponent:GetItemInSlot']={Slot='EnumProperty',ReturnValue='ObjectProperty'},
 ['Maine.EquipmentComponent:GetStance']={ReturnValue='IntProperty'},
 ['Maine.EquipmentComponent:GetOffhandStance']={ReturnValue='IntProperty'},
 ['Maine.Attack:GetAnimMontage']={ReturnValue='ObjectProperty'},
}
local function descriptor(n,t) return {IsValid=function() return true end,GetFullName=function() return t..' Test.Function:'..n end} end
function StaticFindObject(path)
 if path=='/Script/Maine.EEquipmentSlot' then return {IsValid=function() return true end,ForEachName=function(self,fn)
  -- Deliberately differ from SDK numeric values: script must resolve these live.
  fn({ToString=function() return 'EEquipmentSlot::MainHand' end},17)
  fn({ToString=function() return 'EEquipmentSlot::OffHand' end},29)
 end} end
 local spec=methods[path:gsub('^/Script/','')]
 if not spec then return {IsValid=function() return false end} end
 return {IsValid=function() return true end,ForEachProperty=function(self,fn)
  for n,t in pairs(spec) do if fn(descriptor(n,t)) then break end end
 end}
end
local function object(name,classes,props)
 local o={SetPropertyValue=function() writes=writes+1;error('unexpected write') end,IsValid=function() return true end,GetFullName=function() return name end,GetClass=function(self)
  local list={};for c in pairs(classes) do table.insert(list,c) end
  local function at(i)
   if not list[i] then return nil end
   return {IsValid=function() return true end,GetFullName=function() return 'Class '..(wrongReceiver and '/Script/Engine.Unrelated' or list[i]) end,GetSuperStruct=function() return at(i+1) end}
  end
  return at(1)
 end}
 o.Reflection=function() return {GetProperty=function(self,k) local v=props[k];if not v then return nil end;return descriptor(k,v.kind) end} end
 o.GetPropertyValue=function(self,k) calls=calls+1;assert(props[k],'unapproved property '..k);return props[k].value() end
 return o
end
local movement=object('MaineCharMovementComponent LocalPawn.Move',{['/Script/Maine.MaineCharMovementComponent']=true},{})
movement.IsGliding=function() return glide end;movement.GetGlidingStyle=function() return glide and 2 or 0 end
local equipment=object('EquipmentComponent LocalPawn.Equip',{['/Script/Maine.EquipmentComponent']=true},{bHasMainHand={kind='BoolProperty',value=function() return main end},bHasOffHand={kind='BoolProperty',value=function() return off end}})
equipment.GetStance=function() return main and 7 or 0 end;equipment.GetOffhandStance=function() return off and 3 or 0 end
equipment.GetItemInSlot=function(self,slot) assert(slot==17 or slot==29,'copied SDK enum constant');if slot==17 and main then return object('Item Spear',{}, {}) end;if slot==29 and off then return object('Item Shield',{}, {}) end end
local montage=object('AnimMontage SpearObservedOnly',{}, {})
local attack=object('Attack Current',{['/Script/Maine.Attack']=true},{})
attack.GetAnimMontage=function() return montage end
local localCharacter=object('SurvivalPlayerCharacter LocalPawn',{['/Script/Maine.SurvivalCharacter']=true},{
 CharMovementComponent={kind='ObjectProperty',value=function() return movement end},EquipmentComponent={kind='ObjectProperty',value=function() return equipment end},bIsAttacking={kind='BoolProperty',value=function() return attackActive end}})
localCharacter.GetIsFirstPerson=function() return first end;localCharacter.GetCameraDisplayMode=function() return first and 1 or 2 end;localCharacter.GetCurrentAttack=function() return attack end
local pc={IsValid=function() return true end,IsLocalController=function() return true end,Pawn=localCharacter}
local remote={IsValid=function() return true end,IsLocalController=function() return false end,Pawn=setmetatable({}, {__index=function() remoteCalls=remoteCalls+1;error('remote access') end})}
function FindAllOf(k) assert(k=='PlayerController');if menu then return nil end;return {remote,pc} end
'''
src=(root/'runtime/ToyStoryAccessoryCheck/Scripts/main.lua').read_text()
tests={
 'regression: IsA absent on all objects; automatic exact getters still work':r"""
assert(movement.IsA==nil and equipment.IsA==nil)
keys[Key.F9]();flush();assert(writes==0 and remoteCalls==0)
first=true;glide=true;main=true;off=true;attackActive=true;tick();assert(writes==0)
local all=table.concat(lines,'');assert(all:find('gliding=true',1,true));assert(all:find('MainHand=Item Spear',1,true));assert(all:find('OffHand=Item Shield',1,true));assert(all:find('attackMontage=AnimMontage SpearObservedOnly',1,true));assert(not all:find('ERROR',1,true))
assert(keys[Key.F10]==nil)
wall=1181;local old=calls;tick();assert(calls==old)
""",
 'signature mismatch skips incompatible getter':r"""
methods['Maine.MaineCharMovementComponent:IsGliding']={ReturnValue='IntProperty'}
keys[Key.F9]();flush();assert(writes==0);local all=table.concat(lines,'');assert(all:find('SIGNATURE REJECTED',1,true));assert(all:find('gliding=UNAVAILABLE',1,true))
""",
 'unexpected property types rejected, menu and wrong receiver handled':r"""
menu=true;keys[Key.F9]();flush();assert(calls==0);menu=false
localCharacter.Reflection=function() return {GetProperty=function(self,k) return descriptor(k,'ArrayProperty') end} end
wrongReceiver=true;tick();assert(calls==0 and writes==0)
""",
 'queued game-thread samples never overlap':r"""
keys[Key.F9]();timer();timer();flush();assert(writes==0);tick();assert(not table.concat(lines,''):find('ERROR',1,true))
""",
}
for name,post in tests.items():
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  result=lib.luaL_loadstring(state,(pre+src+post).encode())
  if result==0:result=lib.lua_pcallk(state,0,0,0,0,None)
  if result:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
