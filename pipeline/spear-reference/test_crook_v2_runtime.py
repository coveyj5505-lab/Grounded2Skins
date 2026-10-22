"""Run V2 production runtime against native lifecycle/cache regression fixtures."""
import ast,ctypes
from pathlib import Path
root=Path(__file__).resolve().parents[2]
tree=ast.parse((root/'pipeline/spear-reference/test_native_crook.py').read_text())
data={}
for node in tree.body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ('fixture','main_fixture','main_cases'):data[target.id]=ast.literal_eval(node.value)
scripts=root/'runtime-native-spear-v2/BoPeepNativeSpear/Scripts'
setup='''
local cooked=copy(native);cooked.ThrowData.bCanThrow=false;cooked.ThrowData.bCanThrowUnderWater=false
for _,h in ipairs(cooked.AttackComboData.Attacks) do h.DataTable=attackTable end
added[module.row]=cooked
function items:AddRow() error('Unsupported native copy must never execute') end
'''
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
for title,test in data['main_cases'].items():
 code=data['fixture'].replace('ROWS','[====['+(scripts/'item_rows.lua').read_text()+']====]')+setup+data['main_fixture'].replace('F10','F7').replace('MAIN','[====['+(scripts/'main.lua').read_text()+']====]')+'\n'+test
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  result=lib.luaL_loadstring(state,code.encode())
  if not result:result=lib.lua_pcallk(state,0,0,0,0,None)
  if result:raise AssertionError(title+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',title.replace('F10','F7'))
 finally:lib.lua_close(state)
print(len(data['main_cases']),'V2 runtime regression groups passed; not a Windows engine test')
