"""Validate packaged Lua/config/trios and actual renamed runtime file receipts."""
import ctypes,json,sys,zipfile,hashlib
from pathlib import Path
stage=Path(sys.argv[1]);mods=stage/'Augusta/Binaries/WinGDK/ue4ss/Mods';paks=stage/'Augusta/Content/Paks/~mods'
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
count=0
for p in mods.rglob('*.lua'):
 state=lib.luaL_newstate()
 try:assert lib.luaL_loadstring(state,p.read_bytes())==0,p
 finally:lib.lua_close(state)
 count+=1
entries=json.loads((mods/'mods.json').read_text());txt=dict(line.split(' : ') for line in (mods/'mods.txt').read_text().splitlines())
for e in entries:
 n=e['mod_name'];assert (mods/n/'Scripts/main.lua').is_file();assert (txt[n]=='1')==e['mod_enabled'];assert (mods/n/'enabled.txt').exists()==e['mod_enabled']
assert len(list(paks.glob('*.utoc')))==8
for t in paks.glob('*.utoc'):
 assert t.stem.startswith('Rivet-');assert t.with_suffix('.pak').is_file() and t.with_suffix('.ucas').is_file()
# Exercise both real disk-check implementations against the staged names/bytes.
receipt=(mods/'Rivet-Buzz-Flight/Scripts/build_receipt.lua').read_text()
wing=(mods/'Rivet-Buzz-Wings/Scripts/main.lua').read_text();a=wing.index('local function verifyInstalledContainer()');b=wing.index('\ncreate=function',a);wing=wing[a:b]
code="local real=io.open;io.open=function(path,mode) local name=path:match('[^/]+$');return real([====["+str(paks)+"/]====]..name,mode) end;local logs={};local function log(s) logs[#logs+1]=s end;local module=assert(load([====["+receipt+"]====]))();module.run(log);local matches=0;for _,s in ipairs(logs) do assert(not s:find('MISSING') and not s:find('MISMATCHED'),s);if s:find('FILES MATCH RIVET RC') or s:find('FILES MATCH RIVET FINAL') then matches=matches+1 end end;assert(matches==8);"+wing+";verifyInstalledContainer()"
state=lib.luaL_newstate();lib.luaL_openlibs(state)
try:
 r=lib.luaL_loadstring(state,code.encode())
 if not r:r=lib.lua_pcallk(state,0,0,0,0,None)
 assert not r,lib.lua_tolstring(state,-1,None)
finally:lib.lua_close(state)
# The loader binaries must exactly match the previously tested update.
root=Path(__file__).resolve().parents[2]
with zipfile.ZipFile(root/'ToyStory-UE57-Loader-Repair-Test.zip') as z:
 for name in ['WinGDK/dwmapi.dll','WinGDK/ue4ss/UE4SS.dll']:assert z.read(name)==(stage/'Augusta/Binaries'/name).read_bytes()
result={'lua_files_syntax_checked':count,'configuration_agrees_with_enabled_markers':True,'renamed_containers':8,'real_runtime_receipt_matches':8,'wing_header_check_passed':True,'loader_byte_identical_to_tested_update':True,'combined_windows_tested':False}
(stage/'Validation/stage-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
