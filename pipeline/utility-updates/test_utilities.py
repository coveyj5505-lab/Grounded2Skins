"""Execute actual utility Lua with reflected native API fixtures; no Windows claim."""
import ctypes
from pathlib import Path
root=Path(__file__).resolve().parents[2]
lib=ctypes.CDLL('liblua5.4.so.0')
lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
fixture=r'''
local guard=GUARD
package.preload.native_guard=function() return assert(load(guard))() end
local timers,events={},{};local thread=false;local authority=true;local absent=false;local schemaBad=false
print=function(s) events[#events+1]=s end
function LoopAsync(ms,f) timers[#timers+1]=f end
function ExecuteInGameThread(f) assert(not thread);thread=true;f();thread=false end
local function object(name,classes)
 local o={IsValid=function() return true end,GetFullName=function() return name end}
 o.GetClass=function()
  local function cls(i) if not classes[i] then return nil end;return {IsValid=function() return true end,GetFullName=function() return 'Class /Script/'..classes[i] end,GetSuperStruct=function() return cls(i+1) end} end
  return cls(1)
 end;return o
end
local schemas={
 ['Engine.ActorComponent:GetOwner']={ReturnValue='ObjectProperty'},['Engine.Actor:HasAuthority']={ReturnValue='BoolProperty'},
 ['Maine.SurvivalModeManagerComponent:GetGameModeSettings']={ReturnValue='ObjectProperty'},
 ['Engine.SceneComponent:IsVisible']={ReturnValue='BoolProperty'},['Engine.SceneComponent:SetVisibility']={bNewVisibility='BoolProperty',bPropagateToChildren='BoolProperty'},
 ['Maine.SurvivalGameModeSettings']={bAutoCompleteBuildings='BoolProperty'},
 ['Maine.SurvivalPlayerCharacter']={HeadArmorMeshComponent='ObjectProperty',ChestArmorMeshComponent='ObjectProperty',ArmsArmorMeshComponent='ObjectProperty',LegsArmorMeshComponent='ObjectProperty'},
}
function StaticFindObject(path)
 local key=path:gsub('^/Script/','');local spec=schemas[key];if not spec then return nil end
 return {IsValid=function() return true end,ForEachProperty=function(self,fn) for n,t in pairs(spec) do local p={GetFullName=function() return (schemaBad and 'IntProperty' or t)..' /Script/'..key..':'..n end};if fn(p) then break end end end}
end
local settings=object('Settings',{'Maine.SurvivalGameModeSettings'});settings.bAutoCompleteBuildings=false;settings.bFreeCrafting=false
local owner=object('Actor',{'Engine.Actor'});owner.HasAuthority=function() assert(thread);return authority end
local manager=object('Live Manager',{'Maine.SurvivalModeManagerComponent','Engine.ActorComponent'})
manager.GetOwner=function() assert(thread);return owner end;manager.GetGameModeSettings=function() assert(thread);return settings end
local cdo=object('Default__Manager',{'Maine.SurvivalModeManagerComponent','Engine.ActorComponent'});cdo.GetOwner=function() error('CDO must be skipped') end
local pawn=object('Live Player',{'Maine.SurvivalPlayerCharacter'})
local armor={};for _,n in ipairs({'HeadArmorMeshComponent','ChestArmorMeshComponent','ArmsArmorMeshComponent','LegsArmorMeshComponent'}) do
 local c=object(n,{'Engine.SceneComponent'});c.visible=true;c.IsVisible=function(self) assert(thread);return self.visible end;c.SetVisibility=function(self,v,prop) assert(thread and v==false and prop==false);self.visible=v end;pawn[n]=c;armor[#armor+1]=c
end
pawn.Mesh={visible=true};pawn.SCAB={visible=true}
function FindAllOf(name) assert(thread);if absent then return {} end;if name=='SurvivalModeManagerComponent' then return {cdo,manager} elseif name=='SurvivalPlayerCharacter' then return {pawn} end;error('Unbounded/unknown scan') end
local function tick() for _,f in ipairs(timers) do assert(f()==false) end end
'''
cases={
 'FreeBuild host and repeated world discovery':('FreeBuild','tick();assert(settings.bAutoCompleteBuildings);assert(not settings.bFreeCrafting);settings.bAutoCompleteBuildings=false;tick();assert(settings.bAutoCompleteBuildings)'),
 'FreeBuild client writes rejected':('FreeBuild','authority=false;tick();assert(not settings.bAutoCompleteBuildings)'),
 'FreeBuild menu then host':('FreeBuild','absent=true;tick();assert(not settings.bAutoCompleteBuildings);absent=false;tick();assert(settings.bAutoCompleteBuildings)'),
 'FreeBuild schema mismatch fails closed':('FreeBuild','schemaBad=true;tick();assert(not settings.bAutoCompleteBuildings)'),
 'Armor dedicated components only and equipment refresh':('InvisibleArmor','tick();for _,c in ipairs(armor) do assert(not c.visible);c.visible=true end;tick();for _,c in ipairs(armor) do assert(not c.visible) end;assert(pawn.Mesh.visible and pawn.SCAB.visible)'),
 'Armor menu and rejoin':('InvisibleArmor','absent=true;tick();assert(armor[1].visible);absent=false;tick();assert(not armor[1].visible)'),
 'Armor schema mismatch fails closed':('InvisibleArmor','schemaBad=true;tick();assert(armor[1].visible)'),
}
guard=(root/'pipeline/utility-updates/native_guard.lua').read_text()
for name,(mod,checks) in cases.items():
 source=(root/f'runtime-utilities-v1/{mod}/Scripts/main.lua').read_text()
 code=fixture.replace('GUARD','[====['+guard+']====]')+'\n'+source+'\n'+checks
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  result=lib.luaL_loadstring(state,code.encode())
  if not result:result=lib.lua_pcallk(state,0,0,0,0,None)
  if result:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
print(f'{len(cases)} fixture groups passed; native Windows execution remains unverified')
