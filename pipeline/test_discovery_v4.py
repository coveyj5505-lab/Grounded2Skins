"""Real Lua mocked execution, not proof of native UE4SS safety."""
import ctypes
from pathlib import Path
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
pre='''
local lines={};print=function(s) table.insert(lines,s) end
Key={F9=120};local key;local pending;local mode='menu';local gliding=false;local scans=0;local reads=0;local fault=false;local weird=false
function RegisterKeyBind(k,f,extra) assert(k==Key.F9 and type(f)=='function' and extra==nil);key=f end
function ExecuteInGameThread(f) assert(not pending);pending=f end
local function run() local f=pending;pending=nil;if f then f() end end
local metadata={'MulticastInlineDelegateProperty Test:OnItemEquipped','ArrayProperty Test:EquippedItems','StructProperty Test:GlidingData','ObjectProperty Test:EquippedWeapon','BoolProperty Test:bIsGliding','ByteProperty Test:MovementMode','FloatProperty Test:JumpHeight','BoolProperty Test:Irrelevant'}
local cls={IsValid=function() return true end,GetFullName=function() return 'Class Test' end,GetSuperStruct=function() return nil end,
ForEachProperty=function(self,cb) scans=scans+1;for _,v in ipairs(metadata) do if cb({GetFullName=function() return v end})==true then break end end end}
local component={IsValid=function() return true end,GetFullName=function() return 'Component LocalOwned' end,GetClass=function() return cls end,GetPropertyValue=function(self,name) assert(name=='bIsGliding' or name=='MovementMode' or name=='JumpHeight' or name=='Irrelevant');if name=='bIsGliding' then return gliding end;return 1 end}
local refs=0
local pawn={IsValid=function() return true end,GetFullName=function() return 'Pawn Local' end,GetClass=function() return cls end,
GetPropertyValue=function(self,name)
 if name=='CharMovementComponent' or name=='EquipmentComponent' then refs=refs+1;return component end
 reads=reads+1;if fault then error('mock scalar read unavailable') end
 assert(name=='bIsGliding' or name=='MovementMode' or name=='JumpHeight','forbidden value read: '..name)
 if name=='bIsGliding' then if weird then return setmetatable({}, {__tostring=function() error('unsafe stringify') end}) end;return gliding end
 return name=='MovementMode' and 3 or 42.0
end}
local pc={IsValid=function() return true end,IsLocalController=function() return true end,Pawn=pawn}
function FindAllOf(k) assert(k=='PlayerController');if mode=='menu' then return nil end;return {pc} end
'''
post='''
key();run();assert(scans==0 and reads==0)
mode='game';key();key();run();assert(scans==3 and reads==3 and refs==2)
gliding=true;key();run();assert(scans==3 and reads==6 and refs==4)
gliding=false;key();run();assert(scans==3 and reads==9)
weird=true;key();run();assert(scans==3 and reads==12)
local all=table.concat(lines,'');assert(string.find(all,'VALUE player.bIsGliding = false',1,true));assert(string.find(all,'VALUE player.bIsGliding = true',1,true));assert(string.find(all,'SKIPPED NONSCALAR player.bIsGliding',1,true));assert(string.find(all,'BUSY:',1,true));assert(not string.find(all,'SNAPSHOT ERROR',1,true))
'''
errorpost='''mode='game';fault=true;key();run();fault=false;key();run();local all=table.concat(lines,'');assert(string.find(all,'SNAPSHOT ERROR',1,true));assert(string.find(all,'SNAPSHOT END id=2',1,true))'''
src=Path(__file__).resolve().parents[1].joinpath('runtime/ToyStoryDiscoveryV4/Scripts/main.lua').read_text()
for name,tail in [('F9/no modifier; menu; per-scope cache; exact two component references; bounded scalar filtering; state changes; no unsafe conversion; busy',post),('read error recovery',errorpost)]:
 s=lib.luaL_newstate();lib.luaL_openlibs(s)
 try:
  code=lib.luaL_loadstring(s,(pre+src+tail).encode())
  if code==0:code=lib.lua_pcallk(s,0,0,0,0,None)
  if code:raise AssertionError(lib.lua_tolstring(s,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(s)
