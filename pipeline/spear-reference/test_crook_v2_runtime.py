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
if len(sys.argv)>1 and sys.argv[1] in ('runtime-native-spear-v2-1','runtime-native-spear-v2-2','runtime-native-spear-v2-3','runtime-native-spear-v2-4','runtime-native-spear-v2-6'):
 # The Windows function exists on Controller, not PlayerController. Model that
 # exact declaring-class constraint instead of allowing either fixture parent.
 data['fixture']=data['fixture'].replace("assert(api.isa(o,owner),'Bad receiver '..owner..':'..method)","assert(api.isa(o,owner),'Bad receiver '..owner..':'..method);if method=='IsLocalController' then assert(owner=='Engine.Controller','Function belongs to Controller') end")
if len(sys.argv)>1 and sys.argv[1] in ('runtime-native-spear-v2-2','runtime-native-spear-v2-3','runtime-native-spear-v2-4','runtime-native-spear-v2-6'):
 data['fixture']=data['fixture'].replace('function api.log(s)',"function api.once(k,s) api.log(s) end\nfunction api.log(s)")
 # Actual visual arrays can include Niagara/other components. Never read
 # StaticMesh from one, even if returned by the class-filtered engine call.
 data['main_fixture']=data['main_fixture'].replace('return array({smc})',"return array({object('WeaponEffect','Niagara.NiagaraComponent'),smc})")
 data['fixture']=data['fixture'].replace('assert(api.valid(o));return o[k]',"assert(api.valid(o));if k=='StaticMesh' then assert(api.isa(o,'Engine.StaticMeshComponent'),'Wrong field receiver StaticMesh') end;return o[k]")
if len(sys.argv)>1 and sys.argv[1] in ('runtime-native-spear-v2-3','runtime-native-spear-v2-4','runtime-native-spear-v2-6'):
 # Exercise the production unwrap, with real get-only array entry wrappers.
 setup+="\napi.unwrap=assert(load([====["+(scripts/'crook_guard.lua').read_text()+"]====]))().new('WrapperFixture',{},{}).unwrap\n"
if len(sys.argv)>1 and sys.argv[1] in ('runtime-native-spear-v2-4','runtime-native-spear-v2-6'):
 # Actual UE4SS UFunction-return array: plain list of RemoteUnrealParam entries.
 data['main_fixture']=data['main_fixture'].replace("return array({object('WeaponEffect','Niagara.NiagaraComponent'),smc})", "return {{get=function() return object('WeaponEffect','Niagara.NiagaraComponent') end},{get=function() return smc end}}")
if len(sys.argv)>1 and sys.argv[1]=='runtime-native-spear-v2-6':
 data['main_cases']={
  'empty hands automatically equip once without registering F7': 'tick();assert(creates==1 and equips==1 and assigned==1 and key==nil);for i=1,8 do tick() end;assert(creates==1 and equips==1 and assigned==1)',
  'real main hand is preserved': "desiredMain=object('Axe','Maine.Item');function desiredMain:GetItemDataRowHandle() return {DataTable=source,RowName=FName('Axe')} end;tick();assert(creates==0 and desiredMain.full=='Axe')",
  'real offhand blocks automatic equip': "desiredOff=object('Torch','Maine.Item');tick();assert(creates==0 and removed==0)",
  'offhand equip removes crook then clearing both hands restores it': "tick();desiredOff=object('Torch','Maine.Item');tick();assert(removed==1 and desiredMain==nil and desiredOff.full=='Torch');tick();assert(creates==1);desiredOff=nil;tick();assert(creates==2 and equips==2)",
  'main equipment replacement preserves axe and retires private item': "tick();desiredMain=object('Axe','Maine.Item');function desiredMain:GetItemDataRowHandle() return {DataTable=source,RowName=FName('Axe')} end;tick();assert(removed==0 and desiredMain.full=='Axe' and not proxies[1].visible);desiredMain=nil;tick();assert(creates==2)",
  'other characters do not receive crook': 'character=false;tick();assert(creates==0)',
  'character change retires owned crook': 'tick();character=false;tick();assert(removed==1 and desiredMain==nil and not proxies[1].visible)',
  'clients never create authoritative equipment locally': 'host=false;tick();assert(creates==0)',
  'invalid native attack cache still rolls back': "charge=true;tick();assert(equips==1 and removed==1 and desiredMain==nil and hasLog('STOPPED SAFELY'))",
  'camera visibility changes reuse the same deferred mesh': 'tick();for i=1,8 do smc.bHiddenInGame=i%2==1;tick();assert(proxies[1].visible==not smc.bHiddenInGame) end;assert(assigned==1 and finished==1 and attached==1)',
 }
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
