"""Execute real Lua 5.4 against narrow mocks; does not validate UE4SS native safety."""
import ctypes
from pathlib import Path
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
lib.lua_close.argtypes=[ctypes.c_void_p]
pre='''
local lines={}; print=function(s) table.insert(lines,s) end
Key={F9=120};ModifierKey={CONTROL=1};local key;local pending;local mode='menu';local scans=0;local desc=0;local fail=false
function RegisterKeyBind(k,m,f) assert(k==Key.F9);key=f end
function ExecuteInGameThread(f) assert(not pending);pending=f end
local function run() local f=pending;pending=nil;if f then f() end end
local function forbidden() error('Forbidden property-value or gameplay call') end
local class
class={IsValid=function() return true end,GetFullName=function() return 'Class TestPawn' end,
GetSuperStruct=function() return nil end,ForEachProperty=function(self,cb)
 scans=scans+1
 for i=1,200 do
  local p={GetFullName=function() if fail then error('descriptor unavailable') end;desc=desc+1;return 'MulticastInlineDelegateProperty Test:OnItemEquipped' end,GetPropertyValue=forbidden}
  if cb(p)==true then break end
 end
end}
local pawn={IsValid=function() return true end,GetFullName=function() return 'Pawn Local' end,GetClass=function() return class end,GetPropertyValue=forbidden}
local remote={IsValid=function() return true end,IsLocalController=function() return false end,Pawn=setmetatable({}, {__index=forbidden})}
local pc={IsValid=function() return true end,IsLocalController=function() return true end,Pawn=pawn}
function FindAllOf(k) assert(k=='PlayerController');if mode=='menu' then return nil end;return {remote,pc} end
'''
post='''
key();run();assert(scans==0)
mode='game';key();key();run();assert(scans==0) -- second press while queued must be ignored
key();run();assert(scans==1 and desc==128) -- descriptor bound, no value reads
key();run();assert(scans==1) -- exhausted superclass
local all=table.concat(lines,'');assert(string.find(all,'STEP END identity complete',1,true));assert(string.find(all,'BUSY:',1,true));assert(string.find(all,'hierarchy exhausted',1,true));assert(not string.find(all,'STEP ERROR',1,true))
'''
errorpost='''
mode='game';key();run();fail=true;key();run();local all=table.concat(lines,'');assert(string.find(all,'STEP ERROR',1,true));fail=false;key();run();assert(desc==128) -- retry same stage and busy latch released
'''
source=Path(__file__).resolve().parents[1].joinpath('runtime/ToyStoryDiscoveryV2/Scripts/main.lua').read_text()
for name,tail in [('menu/local/remote/bounds/reentrancy',post),('descriptor error and retry',errorpost)]:
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  result=lib.luaL_loadstring(state,(pre+source+tail).encode())
  if result==0:result=lib.lua_pcallk(state,0,0,0,0,None)
  if result:raise AssertionError(lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
