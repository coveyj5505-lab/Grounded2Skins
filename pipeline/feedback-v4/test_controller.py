import os
"""Real Lua5.4 fault-injection tests for isolated flight visibility rollback.
No Unreal runtime or native-function availability is claimed.
"""
import ctypes,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];source=(Path(os.environ.get('TOYSTORY_FLIGHT_ROOT',str(root/'runtime-feedback-v4/BuzzFlightVisual/Scripts')))/'flight_controller.lua').read_text();pre='''
local events={};local fail={};local all={};local n=0
local function object(name,visible) local o={name=name,visible=visible,alive=true};all[#all+1]=o;return o end
local owner=object('owner',true);local body=object('body',true);local backup=object('backup',false);local wing=object('wing',true)
local api={}
api.valid=function(o) return o and o.alive==true end
api.log=function(s) events[#events+1]=s end
api.createHiddenVisual=function(asset,p,b)
 assert(asset=='/Game/Flight.Flight' and p and b);if fail.create then error('load failed') end
 n=n+1;return object('proxy'..n,false)
end
api.destroyVisual=function(o) if fail.destroy then error('destroy failed') end;o.alive=false end
api.setVisibility=function(o,v)
 if fail[o.name..':'..tostring(v)] then error('injected visibility failure '..o.name) end
 o.visible=v;events[#events+1]=o.name..'='..tostring(v)
end
api.getVisibility=function(o) if fail.read then return nil end;return o.visible end
local function snapshot(glide,fp) return {owner=owner,body=body,bodies={body,backup},wings={wing},isBuzz=true,isGliding=glide,isFirstPerson=fp,manualWingsExtended=false} end
'''
checks=[
('tuft render components hide only during flight and restore exact prior state',"local tuft=object('tuft',true);local hidden=object('hiddenTuft',false);local s=snapshot(true,false);s.tufts={tuft,hidden};assert(c.tick(s));assert(not tuft.visible and not hidden.visible);s.isGliding=false;c.tick(s);assert(tuft.visible and not hidden.visible and body.visible)"),
('late tuft render discovery joins existing proxy safely',"c.tick(snapshot(true,false));local tuft=object('tuft',true);local s=snapshot(true,false);s.tufts={tuft};assert(c.tick(s));assert(not tuft.visible and n==1);c.stop();assert(tuft.visible and body.visible)"),
('pending-destroy private wing never blocks glide or landing',"c.tick(snapshot(true,false));local old=wing;fail['wing:true']=true;wing=object('newWing',true);assert(c.tick(snapshot(true,false)));assert(n==1 and c.active and not wing.visible);c.tick(snapshot(false,false));assert(not c.restorePending and body.visible and wing.visible);assert(old.visible==false)"),
('late glider query restores disappeared item without proxy replacement',"local tuft=object('tuft',true);local s=snapshot(true,false);s.tufts={tuft};c.tick(s);assert(not tuft.visible);assert(c.tick(snapshot(true,false)));assert(tuft.visible and n==1);c.stop();assert(body.visible)"),
('landing retires destroyed wing before restoration',"c.tick(snapshot(true,false));fail['wing:true']=true;wing=object('folded',true);c.tick(snapshot(false,false));assert(not c.restorePending and body.visible and wing.visible)"),
('manual standing wings never start flight',"local s=snapshot(false,false);s.manualWingsExtended=true;assert(not c.tick(s));assert(n==0 and body.visible and wing.visible)"),
('glide entry and landing restore prior states',"assert(c.tick(snapshot(true,false)));assert(not body.visible and not wing.visible and not backup.visible);assert(c.visual.visible);assert(not c.tick(snapshot(false,false)));assert(body.visible and wing.visible and not backup.visible and not c.visual)"),
('first-person entry restores complete native model',"c.tick(snapshot(true,false));c.tick(snapshot(true,true));assert(body.visible and wing.visible and not c.visual)"),
('manual toggle cannot end actual flight',"local s=snapshot(true,false);assert(c.tick(s));s.manualWingsExtended=true;assert(c.tick(s));s.manualWingsExtended=false;assert(c.tick(s) and n==1)"),
('concurrent wing visibility is suppressed without replacing rollback state',"c.tick(snapshot(true,false));wing.visible=true;assert(c.tick(snapshot(true,false)));assert(not wing.visible and n==1);c.stop();assert(wing.visible and body.visible and not backup.visible)"),
('suppression refresh failure rolls back native presentation',"c.tick(snapshot(true,false));wing.visible=true;fail['wing:false']=true;assert(not c.tick(snapshot(true,false)));assert(body.visible and wing.visible and not c.visual)"),
('failed asset load never hides native components',"fail.create=true;assert(not c.tick(snapshot(true,false)));assert(body.visible and wing.visible and not c.visual)"),
('unknown prior visibility aborts before suppression',"fail.read=true;assert(not c.tick(snapshot(true,false)));assert(body.visible and wing.visible)"),
('partial suppression failure restores all previous values',"fail['wing:false']=true;assert(not c.tick(snapshot(true,false)));assert(body.visible and wing.visible and not backup.visible and not c.visual)"),
('proxy visibility failure restores native bodies',"fail['proxy1:true']=true;assert(not c.tick(snapshot(true,false)));assert(body.visible and wing.visible and not c.visual)"),
('restoration failure retries before another flight attempt',"c.tick(snapshot(true,false));fail['body:true']=true;c.tick(snapshot(false,false));assert(c.restorePending);assert(not c.tick(snapshot(true,false)));assert(n==1);fail['body:true']=false;c.tick(snapshot(false,false));assert(body.visible and not c.restorePending)"),
('pawn replacement restores old body first',"c.tick(snapshot(true,false));owner=object('owner2',true);c.tick(snapshot(false,false));assert(body.visible and wing.visible and not c.visual)"),
('late wing component joins existing proxy',"c.tick(snapshot(true,false));local extra=object('lateWing',true);local s=snapshot(true,false);s.wings={wing,extra};assert(c.tick(s));assert(n==1 and not extra.visible);c.stop();assert(body.visible and wing.visible and extra.visible)"),
('destroy failure is retried while native view restores',"c.tick(snapshot(true,false));fail.destroy=true;c.stop();assert(body.visible and wing.visible and c.visualCleanupPending);fail.destroy=false;c.tick(snapshot(false,false));assert(not c.visual and not c.visualCleanupPending)"),
('unknown glide/view state stays native',"local s=snapshot(nil,false);assert(not c.tick(s));s.isGliding=true;s.isFirstPerson=nil;assert(not c.tick(s));assert(n==0)"),
('externally destroyed proxy restores then recreates safely',"c.tick(snapshot(true,false));c.visual.alive=false;assert(c.tick(snapshot(true,false)));assert(n==2 and c.visual.visible);c.stop();assert(body.visible and wing.visible)"),
('wrong character receives no proxy',"local s=snapshot(true,false);s.isBuzz=false;assert(not c.tick(s));assert(n==0 and body.visible)"),
]
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p;lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
for name,tail in checks:
 L=lib.luaL_newstate();lib.luaL_openlibs(L);script=pre+'\nlocal module=(function()\n'+source+'\nend)();local c=module.new(api,"/Game/Flight.Flight")\n'+tail;result=lib.luaL_loadstring(L,script.encode())
 if not result:result=lib.lua_pcallk(L,0,0,0,0,None)
 error=lib.lua_tolstring(L,-1,None) if result else None;lib.lua_close(L);assert not result,(name,error);print('PASS',name)
(root/'docs/feedback-v4/controller-regressions.json').write_text(json.dumps({'status':'PASS_MOCKED_LUA_NOT_UNREAL','groups':len(checks),'checks':[x[0] for x in checks],'runtime_adapter':'Prepared separately, disabled; not installed or Windows validated'},indent=2)+'\n')
