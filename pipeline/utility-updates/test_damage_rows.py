"""Run the pure native damage profile parser in Lua, with malformed/charged cases."""
import runpy
from pathlib import Path
# Reuse only the ctypes Lua binding initialized by the utility regression runner.
v=runpy.run_path(str(Path(__file__).with_name('test_utilities.py')));lib=v['lib'];root=v['root']
src=(root/'runtime-native-spear-next/BoPeepNativeSpear/Scripts/damage_rows.lua').read_text()
code='local M=assert(load([====['+src+']====]))()\n'+r'''
assert(M.damage('(Damage=10.000000,DamageType=None)')==10)
assert(M.damage('(Damage=1e+1,DamageMultiplier=99)')==10)
assert(M.damage({get=function() return {ToString=function() return '(Damage=12.5)' end} end})==12.5)
for _,s in ipairs({'(DamageMultiplier=10)','(Damage=-1)','(Damage=nan)','(Damage=1e999)','(Damage=10,Nested=(Damage=20))'}) do assert(not pcall(M.damage,s)) end
local cols={DamageData={'(Damage=20)','(Damage=10)'},ChargedDamageData={'(Damage=0)','(Damage=0)'},PerfectChargedDamageData={'(Damage=0)','(Damage=0)'}}
local rows=M.select({'Spear','Player'},cols,{'Player','Spear'});assert(rows.Player.DamageData==10 and rows.Spear.DamageData==20)
assert(M.uniformMultiplier(rows.Player,{Spear=rows.Spear})==.5)
assert(not pcall(M.select,{'Player','Player'},cols,{'Player'}))
cols.DamageData[2]=nil;assert(not pcall(M.select,{'Spear','Player'},cols,{'Player'}))
assert(not pcall(M.uniformMultiplier,{DamageData=0},{Spear=rows.Spear}))
assert(not pcall(M.uniformMultiplier,rows.Player,{Spear={DamageData=20,ChargedDamageData=60,PerfectChargedDamageData=80}}))
'''
s=lib.luaL_newstate();lib.luaL_openlibs(s)
try:
 rc=lib.luaL_loadstring(s,code.encode())
 if not rc:rc=lib.lua_pcallk(s,0,0,0,0,None)
 if rc:raise AssertionError(lib.lua_tolstring(s,-1,None).decode())
finally:lib.lua_close(s)
print('PASS damage parsing, wrapper normalization, exact field matching, malformed/nonfinite/negative rejection, row alignment, duplicate rows, zero-baseline rejection, combo/charge incompatibility rejection')
