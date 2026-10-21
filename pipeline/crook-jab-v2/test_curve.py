"""Run actual Lua curve through interruptions, held attacks, pause and clock reset."""
from pathlib import Path
import ctypes,json
root=Path(__file__).resolve().parents[2];source=(root/'runtime-crook-jab-v2/BoPeepCrook/Scripts/jab_curve.lua').read_text()
checks=[
('standing and walking stay upright','for i=0,100 do local t,x,s=c.sample(i*.033,false,true);assert(t==0 and x==0 and s=="carry") end'),
('attack lowers before thrust with bounded smooth motion','c.sample(0,true,true);local previous=0;for i=1,100 do local t,x=c.sample(i*.001,true,true);assert(t>=previous and t<=1 and x>=-.15 and x<=1);previous=t end;local t,x=c.sample(.30,true,true);assert(t==1 and math.abs(x-1)<1e-10)'),
('release smoothly returns exactly upright','c.sample(0,true,true);c.sample(.30,true,true);local t,x=c.sample(.31,false,true);assert(t==1 and x==1);local a,b=c.sample(.39,false,true);assert(a>0 and a<1 and b>0 and b<1);a,b=c.sample(.48,false,true);assert(a==0 and b==0)'),
('pause freezes the curve at unchanged game time','c.sample(0,true,true);local a,b=c.sample(.10,true,true);for i=1,50 do local t,x=c.sample(.10,true,true);assert(t==a and x==b) end'),
('early interruption recovers without snapping','c.sample(0,true,true);local a,b=c.sample(.035,true,true);local t,x=c.sample(.036,false,true);assert(t==a and x==b);t,x=c.sample(.32,false,true);assert(t==0 and x==0)'),
('rapid retrigger starts continuously from recovery','c.sample(0,true,true);c.sample(.30,true,true);c.sample(.31,false,true);local a,b=c.sample(.36,false,true);local t,x=c.sample(.37,true,true);assert(t==a and x==b);t,x=c.sample(.67,true,true);assert(t==1 and x==1)'),
('forward stroke retracts before native attack flag ends','c.sample(0,true,true);local t,x=c.sample(.30,true,true);assert(x==1);t,x=c.sample(.41,true,true);assert(x>.45 and x<.55 and t==1);t,x=c.sample(.53,true,true);assert(x==0 and t==1);t,x=c.sample(.9,true,true);assert(x==0 and t==1)'),
('held attack has one thrust and no invented attack repeats','c.sample(0,true,true);for i=1,100 do c.sample(i*.05,true,true) end;assert(c.phase=="jab" and c.start==0 and c.turn==1 and c.thrust==0)'),
('equipment change cancels visual motion immediately','c.sample(0,true,true);c.sample(.30,true,true);local t,x,s=c.sample(.31,true,false);assert(t==0 and x==0 and s=="carry");t,x=c.sample(.32,false,true);assert(t==0 and x==0)'),
('world time rewind resets old transition','c.sample(20,true,true);c.sample(20.18,true,true);local t,x=c.sample(1,true,true);assert(t==0 and x==0 and c.start==1)'),
('nonfinite clock rejected','assert(not pcall(c.sample,0/0,true,true));assert(not pcall(c.sample,math.huge,true,true));assert(not pcall(c.sample,-1,true,true))'),
]
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p;lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
for name,tail in checks:
 L=lib.luaL_newstate();lib.luaL_openlibs(L);code='local m=(function()\n'+source+'\nend)();local c=m.new();\n'+tail;result=lib.luaL_loadstring(L,code.encode())
 if not result:result=lib.lua_pcallk(L,0,0,0,0,None)
 error=lib.lua_tolstring(L,-1,None) if result else None;lib.lua_close(L);assert not result,(name,error);print('PASS',name)
(root/'docs/crook-jab-v2/curve-regressions.json').write_text(json.dumps({'status':'PASS_REAL_LUA_MOCKED_TIME_NOT_WINDOWS','groups':len(checks),'checks':[n for n,_ in checks]},indent=2)+'\n')
