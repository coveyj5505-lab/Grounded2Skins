"""Exercise the actual one-shot probe against native schema/row-array fixtures."""
import runpy
from pathlib import Path
v=runpy.run_path(str(Path(__file__).with_name('test_utilities.py')));lib=v['lib'];root=v['root']
fixture=v['fixture'].replace('GUARD','[====['+v['guard']+']====]')
source=(root/'runtime-spear-damage-probe/SpearDamageProbe/Scripts/main.lua').read_text()
module=(root/'runtime-native-spear-next/BoPeepNativeSpear/Scripts/damage_rows.lua').read_text()
setup=r'''
package.preload.damage_rows=function() return assert(load(MODULE))() end
function FName(s) return s end
schemas['Engine.DataTableFunctionLibrary:GetDataTableRowNames']={Table='ObjectProperty',OutRowNames='ArrayProperty'}
schemas['Engine.DataTableFunctionLibrary:GetDataTableColumnAsString']={DataTable='ObjectProperty',PropertyName='NameProperty',ReturnValue='ArrayProperty'}
local reads=0;local mismatch=false;local charged=false
local fists=object('DataTable /Game/Blueprints/Attacks/CreatureAttacks.CreatureAttacks',{'Engine.DataTable'})
local spears=object('DataTable /Game/Blueprints/Attacks/ItemAttacks.ItemAttacks',{'Engine.DataTable'})
local library=object('DataTableFunctionLibrary Default',{'Engine.DataTableFunctionLibrary'})
library.GetDataTableRowNames=function(self,t,out) assert(thread);local names=t==fists and {'Player'} or {'Spear','Spear2','Spear3'};for i,n in ipairs(names) do out[i]={ToString=function() return n end} end end
library.GetDataTableColumnAsString=function(self,t,field)
 assert(thread);reads=reads+1;local out={};local count=t==fists and 1 or 3
 if mismatch then count=0 end
 for i=1,count do local damage=field=='DamageData' and (t==fists and 10 or 20) or (charged and 60 or 0);out[i]={type=function() return 'RemoteUnrealParam' end,get=function() return {ToString=function() return '(Damage='..damage..',DamageMultiplier=1)' end} end} end
 return out
end
local originalFind=StaticFindObject
function StaticFindObject(path)
 if path=='/Game/Blueprints/Attacks/CreatureAttacks.CreatureAttacks' then return fists end
 if path=='/Game/Blueprints/Attacks/ItemAttacks.ItemAttacks' then return spears end
 if path=='/Script/Engine.Default__DataTableFunctionLibrary' then return library end
 return originalFind(path)
end
'''.replace('MODULE','[====['+module+']====]')
cases={
 'native row outputs, complete once, no gameplay writes':("", "tick();assert(reads==6);tick();assert(reads==6);local s=table.concat(events);assert(s:find('NATIVE_DAMAGE',1,true) and s:find('UNIFORM_MULTIPLIER_CANDIDATE 0.5',1,true) and s:find('COMPLETE',1,true));assert(not settings.bAutoCompleteBuildings and pawn.Mesh.visible)"),
 'no repeated attacks required after loading world':('absent=true;','tick();assert(reads==0);absent=false;tick();assert(reads==6)'),
 'column-size mismatch stops without guessed damage':('mismatch=true;','tick();tick();assert(reads==3);assert(table.concat(events):find("STOP",1,true));assert(not table.concat(events):find("COMPLETE",1,true))'),
 'nonuniform charged rows request per-attack handling':('charged=true;','tick();assert(table.concat(events):find("PER_ATTACK_REQUIRED",1,true));assert(not table.concat(events):find("UNIFORM_MULTIPLIER_CANDIDATE",1,true))'),
 'metadata mismatch blocks native invocation':('schemaBad=true;','tick();assert(reads==0);assert(table.concat(events):find("STOP",1,true))'),
}
for name,(pre,post) in cases.items():
 s=lib.luaL_newstate();lib.luaL_openlibs(s)
 try:
  code=fixture+setup+pre+source+'\n'+post
  rc=lib.luaL_loadstring(s,code.encode())
  if not rc:rc=lib.lua_pcallk(s,0,0,0,0,None)
  if rc:raise AssertionError(name+': '+lib.lua_tolstring(s,-1,None).decode())
 finally:lib.lua_close(s)
 print('PASS',name)
print('5 read-only native damage probe fixture groups passed; Windows not run')
