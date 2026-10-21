import os
"""Exercise the staged native adapter using the proven accessory Lua fixtures.
These mocks validate flow, rollback and signature gates, not Windows access.
"""
import ctypes,re,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];folder=Path(os.environ.get('TOYSTORY_FLIGHT_ROOT',str(root/'experiments/BuzzFlightVisual/Scripts')));source=(folder/'main.lua').read_text();controller=(folder/'flight_controller.lua').read_text();original=(root/'pipeline/test_crook_carry.py').read_text();pre=original.split("pre=r'''",1)[1].split("'''.replace",1)[0];specs=[]
for owner,method,args in re.findall(r"spec\('([^']+)','([^']+)',(\{[^\n]+\})\)",source):specs.append("['/Script/"+owner+':'+method+"']="+args)
specs.extend(["['/Script/Maine.EquipmentComponent:GetItemInSlot']={Slot='EnumProperty',ReturnValue='ObjectProperty'}","['/Script/Maine.Item:GetItemVisuals']={ReturnValue='ObjectProperty'}"])
pre=pre.replace('SPECS',',\n'.join(specs)).replace('_BoCrTP1','_BzFlit1').replace('/Game/_BoCr','/Game/_BzFlit1')
pre=pre.replace('/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01','/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01')
pre=pre.replace("or 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01'", "or 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male02/SK_Male_Teen_02.SK_Male_Teen_02'")
pre=pre.replace("{EquipmentComponent='ObjectProperty',bIsAttacking='BoolProperty'}", "{CharMovementComponent='ObjectProperty',EquipmentComponent='ObjectProperty',InventoryComponent='ObjectProperty'}")
pre=pre.replace("if fields[path] then", "fields['/Script/Maine.InventoryComponent']={UsingGliderItem='ObjectProperty'};fields['/Script/Engine.SkinnedMeshComponent']={VisibilityBasedAnimTickOption=tickKind or 'EnumProperty'};if fields[path] then")
pre=pre.replace("if enumMaps[path] then", "enumMaps['/Script/Engine.EVisibilityBasedAnimTickOption']={AlwaysTickPoseAndRefreshBones=7,OnlyTickPoseWhenRendered=5};if enumMaps[path] then")
pre=pre.replace("MainHand=17,OffHand=29","MainHand=17,OffHand=29,Glider=41").replace("path=='/Script/Engine.SkeletalMeshComponent'","(path=='/Script/Engine.SkeletalMeshComponent' or path=='/Script/Engine.PrimitiveComponent')")
pre+='''
local glide=false;local nativeVisible=true;local wingVisible=true;local tickValue=5;local tickKind=nil;local tickWriteFails=false
-- Keep these names global for StaticFindObject's existing closure.
_G.tickKind=nil
body.IsVisible=function() return nativeVisible end
body.SetVisibility=function(self,v,prop) assert(not prop);nativeVisible=v end
setmetatable(body,{__index=function(t,k) if k=='VisibilityBasedAnimTickOption' then return tickValue end end,__newindex=function(t,k,v) if k=='VisibilityBasedAnimTickOption' then if tickWriteFails then error('tick setter failed') end;tickValue=v else rawset(t,k,v) end end})
local movement=obj('MaineCharMovementComponent Movement',{'Maine.MaineCharMovementComponent'})
movement.IsGliding=function() return glide end;p.CharMovementComponent=movement
eq.GetItemInSlot=function() error('Flight must never access equipment') end
local wing=obj('SkeletalMeshComponent NativeWing',{'Engine.SkeletalMeshComponent','Engine.SkinnedMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent'})
wing.GetSkeletalMeshAsset=function() return obj('SkeletalMesh /Game/_BzWExt1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01',{'Engine.SkeletalMesh'}) end
wing.IsVisible=function() return wingVisible end
wing.SetVisibility=function(self,v,prop) assert(not prop);wingVisible=v end
p.K2_GetComponentsByClass=function() return c and {body,wing,c} or {body,wing} end
local create=p.AddComponentByClass
p.AddComponentByClass=function(...)
 local x=create(...);local setter=x.SetSkeletalMeshAsset
 x.SetSkeletalMeshAsset=function(self,a) setter(self,a);self.mesh=a end
 x.GetSkeletalMeshAsset=function(self) return self.mesh end
 return x
end
local experimentEnabled=true
local module=(function()
CONTROLLER
end)()
function require(name) if name=='flight_config' then return {Enabled=experimentEnabled,DebugToggleKey=nil} end;assert(name=='flight_controller');return module end
'''.replace('CONTROLLER',controller)
checks=[
('optional glider getter failure cannot block forward flight',"eq.GetItemInSlot=function() error('getter unavailable') end","glide=true;timer();assert(show and made==1 and not nativeVisible);glide=false;timer();assert(nativeVisible and wingVisible)"),
('exact glider item render primitives hide and restore',"local tuft=obj('StaticMeshComponent Tuft',{'Engine.PrimitiveComponent','Engine.SceneComponent'});local tuftVisible=true;tuft.IsVisible=function() return tuftVisible end;tuft.SetVisibility=function(self,v,prop) assert(not prop);tuftVisible=v end;local visual=obj('BP_Tuft_C Visual',{'Maine.SpawnedItem','Engine.Actor'});visual.K2_GetComponentsByClass=function() return {tuft} end;item.GetItemVisuals=function() return visual end;eq.GetItemInSlot=function(self,slot) assert(slot==41);return item end;_G.testTuftVisible=function() return tuftVisible end","glide=true;timer();assert(show and not testTuftVisible());glide=false;timer();assert(testTuftVisible() and nativeVisible)"),
('reusable tuft uses active inventory item before equipment fallback',"local tuft=obj('StaticMeshComponent Tuft',{'Engine.PrimitiveComponent','Engine.SceneComponent'});local tuftVisible=true;tuft.IsVisible=function() return tuftVisible end;tuft.SetVisibility=function(self,v,prop) assert(not prop);tuftVisible=v end;local visual=obj('BP_Tuft_C Visual',{'Maine.SpawnedItem','Engine.Actor'});visual.K2_GetComponentsByClass=function() return {tuft} end;item.GetItemVisuals=function() return visual end;local inv=obj('InventoryComponent Inventory',{'Maine.InventoryComponent'});inv.UsingGliderItem=item;p.InventoryComponent=inv;eq.GetItemInSlot=function() error('must not query equipment when active item exists') end;_G.testTuftVisible=function() return tuftVisible end","glide=true;timer();assert(show and not testTuftVisible());glide=false;timer();assert(testTuftVisible() and nativeVisible)"),
('direct character mesh works when enumeration omits native body',"p.K2_GetComponentsByClass=function() return {wing} end","glide=true;timer();assert(show and made==1 and not nativeVisible and not wingVisible);glide=false;timer();assert(nativeVisible and wingVisible)"),
('direct and enumerated body is suppressed only once','',"local calls=0;local f=body.SetVisibility;body.SetVisibility=function(...) calls=calls+1;return f(...) end;glide=true;timer();assert(show and calls==1);glide=false;timer();assert(calls==2)"),
('callable reflected controller getter is accepted',"local find=FindAllOf;FindAllOf=function(name) local list=find(name);for _,pc in ipairs(list) do local fn=pc.IsLocalController;pc.IsLocalController=setmetatable({},{__call=function(_,self) return fn(self) end}) end;return list end","glide=true;timer();assert(show and made==1 and not nativeVisible and not wingVisible);glide=false;timer();assert(nativeVisible and wingVisible)"),
('disabled development default makes no native changes',"experimentEnabled=false", "glide=true;timer();assert(made==0 and nativeVisible and wingVisible and tickValue==5)"),
('standing leaves manual wings and native body alone','',"timer();assert(made==0 and nativeVisible and wingVisible and tickValue==5)"),
('glide creates hidden proxy before suppression and restores on landing','',"glide=true;timer();assert(show and made==1 and not nativeVisible and not wingVisible and tickValue==7);timer();assert(made==1);glide=false;timer();assert(not show and destroyed==1 and nativeVisible and wingVisible and tickValue==5)"),
('independent wing update cannot leave duplicate upright wings visible','',"glide=true;timer();wingVisible=true;timer();assert(show and not wingVisible and not nativeVisible);glide=false;timer();assert(wingVisible and nativeVisible and tickValue==5)"),
('first-person switch restores original presentation and tick policy','',"glide=true;timer();fp=true;timer();assert(not show and nativeVisible and wingVisible and tickValue==5);fp=false;timer();assert(show and made==2)"),
('asset-load failure never hides native source','',"missingAsset=true;glide=true;timer();assert(made==0 and nativeVisible and wingVisible and tickValue==5);timer();assert(made==0)"),
('unknown glide restores active visual safely','',"glide=true;timer();movement.IsGliding=function() return nil end;timer();assert(not show and nativeVisible and wingVisible and tickValue==5)"),
('source tick setter failure aborts before native suppression','',"tickWriteFails=true;glide=true;timer();assert(not show and nativeVisible and wingVisible and tickValue==5)"),
('wrong source tick property type fails safely','',"_G.tickKind='StructProperty';glide=true;timer();assert(not show and nativeVisible and wingVisible and tickValue==5)"),
('wrong character receives no flight visual','',"female=false;glide=true;timer();assert(made==0 and nativeVisible and wingVisible)"),
('missing native function signature rejects before creation','',"bad=true;glide=true;timer();assert(made==0 and nativeVisible and wingVisible)"),
]
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p;lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
for name,setup,tail in checks:
 state=lib.luaL_newstate();lib.luaL_openlibs(state);code=(pre+'\n'+setup+'\n'+source+'\n'+tail).encode();result=lib.luaL_loadstring(state,code)
 if result==0:result=lib.lua_pcallk(state,0,0,0,0,None)
 error=lib.lua_tolstring(state,-1,None) if result else None;lib.lua_close(state);assert not result,(name,error);print('PASS',name)
(root/'docs/buzz-flight-adapter-regressions.json').write_text(json.dumps({'status':'PASS_MOCKED_LUA_NOT_UNREAL','groups':len(checks),'checks':[x[0] for x in checks],'default':'DISABLED, no default hotkey, no enabled.txt, not installed or in v0.3','runtime':'NOT TESTED; live property/function validation still required'},indent=2)+'\n')
