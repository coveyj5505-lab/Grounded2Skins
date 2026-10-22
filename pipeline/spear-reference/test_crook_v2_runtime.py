"""Run V2 production runtime against native lifecycle/cache regression fixtures."""
import ast,ctypes,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
tree=ast.parse((root/'pipeline/spear-reference/test_native_crook.py').read_text())
data={}
for node in tree.body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ('fixture','main_fixture','main_cases'):data[target.id]=ast.literal_eval(node.value)
scripts=root/(sys.argv[1] if len(sys.argv)>1 else 'runtime-native-spear-v2')/'BoPeepNativeSpear/Scripts'
setup='''
local cooked=copy(native);cooked.ThrowData.bCanThrow=false;cooked.ThrowData.bCanThrowUnderWater=false
for _,h in ipairs(cooked.AttackComboData.Attacks) do h.DataTable=attackTable end
added[module.row]=cooked
function items:AddRow() error('Unsupported native copy must never execute') end
'''
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
if len(sys.argv)>1 and sys.argv[1] in ('runtime-native-spear-v2-1','runtime-native-spear-v2-2'):
 # The Windows function exists on Controller, not PlayerController. Model that
 # exact declaring-class constraint instead of allowing either fixture parent.
 data['fixture']=data['fixture'].replace("assert(api.isa(o,owner),'Bad receiver '..owner..':'..method)","assert(api.isa(o,owner),'Bad receiver '..owner..':'..method);if method=='IsLocalController' then assert(owner=='Engine.Controller','Function belongs to Controller') end")
if len(sys.argv)>1 and sys.argv[1]=='runtime-native-spear-v2-2':
 data['fixture']=data['fixture'].replace('function api.log(s)',"function api.once(k,s) api.log(s) end\nfunction api.log(s)")
 # Actual visual arrays can include Niagara/other components. Never read
 # StaticMesh from one, even if returned by the class-filtered engine call.
 data['main_fixture']=data['main_fixture'].replace('return array({smc})',"return array({object('WeaponEffect','Niagara.NiagaraComponent'),smc})")
 data['fixture']=data['fixture'].replace('assert(api.valid(o));return o[k]',"assert(api.valid(o));if k=='StaticMesh' then assert(api.isa(o,'Engine.StaticMeshComponent'),'Wrong field receiver StaticMesh') end;return o[k]")
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
