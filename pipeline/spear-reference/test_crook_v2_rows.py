"""V2 read-only row validation cannot call the Windows-unsupported AddRow path."""
import ast,ctypes,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
old=root/'pipeline/spear-reference/test_native_crook.py'
fixture=next(ast.literal_eval(n.value) for n in ast.parse(old.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixture' for t in n.targets))
if len(sys.argv)>1 and sys.argv[1] in ('runtime-native-spear-v2-8','runtime-native-spear-v2-9'):
 fixture=fixture.replace("{'Spear','Spear2','Spear3'}","{'RivetCrookJab1','RivetCrookJab2','RivetCrookJab3'}")
module=(root/(sys.argv[1] if len(sys.argv)>1 else 'runtime-native-spear-v2')/'BoPeepNativeSpear/Scripts/item_rows.lua').read_text()
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
setup="""
function items:AddRow() error('Virtual UScriptStruct::ICppStructOps::Copy is unavailable') end
local cooked=copy(native);cooked.ThrowData.bCanThrow=false;cooked.ThrowData.bCanThrowUnderWater=false
for _,h in ipairs(cooked.AttackComboData.Attacks) do h.DataTable=attackTable end
added[module.row]=cooked
"""
cases={
 'pre-cooked private item reads without any native row copying':'local ok,h=prepare();assert(ok,h);assert(h.DataTable==items and added[module.row]==cooked and removes==0)',
 'empty V1 item-table explicitly rejected':'added[module.row]=nil;local ok,h=prepare();assert(not ok and tostring(h):find("Cooked item row missing",1,true) and removes==0)',
 'ordinary spear reference rejected before creation':'cooked.AttackComboData.Attacks[2].DataTable=nativeAttacks;assert(not prepare())',
 'wrong damage profile rejected':'badDamage=true;assert(not prepare())',
}
for name,test in cases.items():
 code=fixture.replace('ROWS','[====['+module+']====]')+setup+test
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  r=lib.luaL_loadstring(state,code.encode())
  if not r:r=lib.lua_pcallk(state,0,0,0,0,None)
  if r:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
print('4 read-only V2 row groups passed; Windows native execution remains unverified')
