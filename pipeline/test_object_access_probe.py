"""Run single-shot diagnostic with different wrapper/missing-method outcomes in real Lua."""
import ctypes
from pathlib import Path
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
root=Path(__file__).resolve().parents[1]
pre=r'''
local lines={};print=function(s) table.insert(lines,s) end
local key;local queued;local getterFails=false;local noPawn=false
Key={F9=120}
function RegisterKeyBind(k,f) assert(k==Key.F9);key=f end
function ExecuteInGameThread(f) assert(not queued);queued=f end
local function flush() local f=queued;queued=nil;if f then f() end end
local function object(tag,name)
 return {type=function() return tag end,IsValid=function() return true end,GetFullName=function() return name end}
end
local movement=object('UObject','MaineCharMovementComponent Player.Move')
local equipment=object('UObject','EquipmentComponent Player.Equip')
-- Both methods absent as in the failed logs. No :get unwrapping may be invoked.
movement.get=function() error('diagnostic must not unwrap or call arbitrary methods') end
local metadata=object('ObjectProperty','ObjectProperty /Script/Maine.SurvivalCharacter:CharMovementComponent')
local pawn=object('AActor','PlayerCharacter LocalPawn')
pawn.CharMovementComponent=movement;pawn.EquipmentComponent=equipment
pawn.Reflection=function() return {GetProperty=function() return metadata end} end
pawn.GetPropertyValue=function(self,n) if getterFails then error('mock property access failure') end;return metadata end
local pc={IsValid=function() return true end,IsLocalController=function() return true end}
setmetatable(pc,{__index=function(self,k) if k=='Pawn' then if noPawn then return nil end;return pawn end end})
function FindAllOf(k) assert(k=='PlayerController');return {pc} end
'''
tests={
'wrapper tags distinguish metadata from instance; missing methods tolerated; single shot':r'''
key();key();flush();local all=table.concat(lines,'');assert(all:find('WRAPPER CharMovementComponent.GetPropertyValue = ObjectProperty',1,true));assert(all:find('WRAPPER CharMovementComponent.direct = UObject',1,true));assert(all:find('CharMovementComponent.direct.GetClass LuaType=nil',1,true));assert(all:find('CharMovementComponent.direct.IsA LuaType=nil',1,true));assert(all:find('WRAPPER EquipmentComponent.direct = UObject',1,true));assert(all:find('END complete',1,true));assert(not all:find('LUA ERROR',1,true));key();assert(queued==nil)
''',
'one property-access error does not prevent direct/other component diagnostics':r'''
getterFails=true;key();flush();local all=table.concat(lines,'');assert(all:find('LUA ERROR CharMovementComponent GetPropertyValue',1,true));assert(all:find('WRAPPER CharMovementComponent.direct = UObject',1,true));assert(all:find('WRAPPER EquipmentComponent.direct = UObject',1,true));assert(all:find('END complete',1,true))
''',
'menu without pawn permits retry after loading':r'''
noPawn=true;key();flush();noPawn=false;key();flush();assert(table.concat(lines,''):find('END complete',1,true))
'''}
src=(root/'runtime/ToyStoryObjectAccess/Scripts/main.lua').read_text()
for name,post in tests.items():
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  code=lib.luaL_loadstring(state,(pre+src+post).encode())
  if code==0:code=lib.lua_pcallk(state,0,0,0,0,None)
  if code:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
