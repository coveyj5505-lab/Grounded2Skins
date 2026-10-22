"""Actual multiplayer Teleport Lua, using reflected native/current Blueprint fixtures."""
import runpy,re
from pathlib import Path
v=runpy.run_path(str(Path(__file__).with_name('test_utilities.py')));lib=v['lib'];root=v['root']
source=(root/'runtime-teleport-v2/Teleport/Scripts/main.lua').read_text();guard=(root/'runtime-teleport-v2/Teleport/Scripts/teleport_guard.lua').read_text()
fixture=r'''
local script=SOURCE
local guard=GUARD
package.preload.teleport_guard=function() return assert(load(guard))() end
local key,poll,hook;local hookCount=0;local clientSent=0;local spawnPawn;local thread=false;local clock=100;local logs={};local calls={};local spawns=0;local destroyed=0;local requested=0;local host=true;local menu=true;local locked=false;local shown=true;local poiValid=true;local destinationValid=true;local wrongSchema=false;local failedDoor=false
print=function(s) logs[#logs+1]=s end
os.time=function() return clock end
Key={F8=119};function RegisterKeyBind(k,f) assert(k==Key.F8);key=f end
function ExecuteInGameThread(f) thread=true;f();thread=false end
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local CONTROLLER='/Game/Blueprints/Player/BP_SurvivalPlayerController.BP_SurvivalPlayerController_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
function LoopAsync(ms,f) assert(ms==1000);poll=f end
function RegisterHook(path,f) assert(not thread,'Hook registration must be outside game thread');assert(path==CONTROLLER..':ServerRequestPTSTravel');hookCount=hookCount+1;hook=f;return 1,1 end
local function path(n) return n:sub(1,1)=='/' and n or '/Script/'..n end
local function object(n,classes)
 local o={IsValid=function() return true end,GetFullName=function() return n end}
 o.GetClass=function()
  local function cls(i) if not classes[i] then return nil end;return {IsValid=function() return true end,GetFullName=function() return (classes[i]:sub(1,1)=='/' and 'BlueprintGeneratedClass ' or 'Class ')..path(classes[i]) end,GetSuperStruct=function() return cls(i+1) end} end;return cls(1)
 end
 return o
end
-- Read the signature table literal from the production script, not a mirrored fixture.
local enum='ByteProperty|EnumProperty';local TELEPORTER=TP
local signatures=assert(load('local enum="ByteProperty|EnumProperty";local TELEPORTER=...;local DOOR=select(2,...);local CONTROLLER=select(3,...);return '..SCHEMAS))(TP,DOOR,CONTROLLER)
local function resolveSpec(key)
 for k,s in pairs(signatures) do local owner,method=k:match('^(.*)%.([^%.]+)$');if key==path(owner)..':'..method then return s end end
end
local fields={['Maine.MapWidget']={MapPanel='ObjectProperty'},['Maine.MapPOIWidget']={POIData='ObjectProperty'},[TP]={Teleporter_Door_Object_REF='ObjectProperty',POIDataAsset='ObjectProperty'}}
local invalid={IsValid=function() return false end}
local objects={}
local actorMethods=function(o)
 o.SetActorHiddenInGame=function(self,x) assert(thread and x==true);self.hidden=x end
 o.SetActorEnableCollision=function(self,x) assert(thread and x==false);self.collision=x end
 o.SetLifeSpan=function(self,x) assert(thread and x==30);self.lifespan=x end
 o.K2_DestroyActor=function() assert(thread);destroyed=destroyed+1 end
 return o
end
local pawn=actorMethods(object('Player',{'Maine.SurvivalPlayerCharacter','Engine.Actor'}))
pawn.HasAuthority=function() assert(thread);return host end;pawn.GetTransform=function() assert(thread);return {Translation={X=10,Y=20,Z=30},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end
local pc=object('LocalController',{CONTROLLER,'Engine.Controller','Engine.Actor'});pc.HasAuthority=function() assert(thread);return host end;pc.IsLocalController=function() assert(thread);return true end;pc.K2_GetPawn=function() assert(thread);return pawn end
local ui=object('UI',{'Maine.UserInterfaceStatics'});local manager=object('WidgetManager',{'Maine.WidgetManager'})
ui.GetWidgetManager=function() assert(thread);return manager end;manager.IsInGameMenuActive=function() assert(thread);return menu end;manager.HideInGameMenu=function() assert(thread);calls[#calls+1]='closeMap' end
local map=object('Map',{ 'Maine.MapWidget','UMG.Widget'});local parent=object('Parent',{'UMG.Widget'})
map.IsVisible=function() assert(thread);return true end;map.GetParent=function() assert(thread);return parent end;parent.IsVisible=function() assert(thread);return shown end;parent.GetParent=function() assert(thread);return nil end
local panel=object('Panel',{'Maine.MapPanelWidget'});map.MapPanel=panel
local entry=object('OutpostEntry',{'Maine.MapPOIWidget'});entry.POIData=object('POI',{'CoreUObject.Object'});panel.GetEntryUnderCursor=function() assert(thread);return poiValid and entry or invalid end
local ss=object('SurvivalStatics',{'Maine.SurvivalGameplayStatics'});local state=object('State',{'Maine.SurvivalGameState'})
ss.GetSurvivalGameState=function() assert(thread);return state end;state.IsPTSTravelLocked=function() assert(thread);return locked end
local dest=object('Destination',{TP,'Engine.Actor'});dest.POIDataAsset=entry.POIData;state.GetRegisteredPTSTravel=function() assert(thread);return destinationValid and dest or invalid end
local class=object('Class Teleporter',{'CoreUObject.Class'});class.ForEachProperty=function(self,f) f({GetFullName=function() return 'ObjectProperty '..TP..':Teleporter_Door_Object_REF' end});f({GetFullName=function() return 'ObjectProperty '..TP..':POIDataAsset' end}) end
local sourceCDO=object('Default__Teleporter',{TP});local doorCDO=object('Default__Door',{DOOR})
local gameplay=object('GameplayStatics',{'Engine.GameplayStatics'});local source,door
local function makeSource()
 spawns=spawns+1;source=actorMethods(object('TemporarySource',{TP,'Engine.Actor'}));door=actorMethods(object('TemporaryDoor',{DOOR,'Engine.Actor'}))
 source.SetTeleportDoorRef=function() assert(thread);source.Teleporter_Door_Object_REF=failedDoor and invalid or door end
 door.SetAndPrintInteractionInstigator=function(self,p) assert(thread and p==spawnPawn);calls[#calls+1]='setPawn' end
 source.OnTeleportRequested=function(self,c,d) assert(thread and c==false and d==dest);assert(source.hidden and source.collision==false and source.lifespan==30);assert(door.hidden and door.collision==false and door.lifespan==30);requested=requested+1;calls[#calls+1]='request' end
 return source
end
gameplay.BeginDeferredActorSpawnFromClass=function(self,p,c,t,collision,owner,scale) assert(thread and c==class and owner==p and collision==1 and scale==1);spawnPawn=p;return makeSource() end
gameplay.FinishSpawningActor=function(self,o,t,scale) assert(thread and o==source);return o end
objects['/Script/Maine.Default__UserInterfaceStatics']=ui;objects['/Script/Maine.Default__SurvivalGameplayStatics']=ss;objects['/Script/Engine.Default__GameplayStatics']=gameplay;objects[TP]=class
objects['/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.Default__BP_Teleporter_C']=sourceCDO
objects['/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.Default__BP_Teleporter_Door_C']=doorCDO
function StaticFindObject(key)
 assert(thread,'No UObject lookup before the hotkey/game thread')
 if objects[key] then return objects[key] end
 if key:find('/Script/Engine.ESpawn',1,true)==1 then return {IsValid=function() return true end,ForEachName=function(self,f) f({ToString=function() return key:find('Collision',1,true) and 'AlwaysSpawn' or 'MultiplyWithRoot' end},1) end} end
 local spec=resolveSpec(key)
 if not spec then for owner,s in pairs(fields) do if key==path(owner) then spec=s end end end
 if not spec then return nil end
 return {IsValid=function() return true end,ForEachProperty=function(self,f) for name,t in pairs(spec) do local typ=t:match('^[^|]+');if wrongSchema and key:find(':OnTeleportRequested',1,true) then typ='IntProperty' end;if f({GetFullName=function() return typ..' '..key..':'..name end}) then break end end end}
end
function FindAllOf(name) assert(thread);if name=='PlayerController' then return {pc} elseif name=='MapWidget' then return {map} end;error('Unexpected scan') end
pc.ServerRequestPTSTravel=function(self,cancel,departure,target) assert(thread and cancel==false and departure==nil and target==dest);clientSent=clientSent+1 end
local function press() clock=clock+3;key() end
local function wrap(value) return {type=function() return 'RemoteUnrealParam' end,get=function() return value end} end
local function receive(controller,cancel,source,target) assert(hook);hook(wrap(controller),wrap(cancel),wrap(source),wrap(target)) end
local function register() poll();poll();assert(hookCount==1 and hook) end

'''
schemas=re.search(r'local schemas=(\{.*?\n\})\nlocal api',source,re.S).group(1)
fixture=fixture.replace('local script=SOURCE','local script=[====['+source+']====]').replace('local guard=GUARD','local guard=[====['+guard+']====]').replace('SCHEMAS','[====['+schemas+']====]')
cases={
 'startup creates nothing':('', 'assert(spawns==0 and requested==0 and key~=nil)'),
 'native host travel pipeline, only temporary actors':('', "press();assert(spawns==1 and requested==1 and destroyed==0);assert(pawn.hidden==nil and pawn.collision==nil);assert(table.concat(calls,',')=='setPawn,closeMap,request')"),
 'client sends existing native RPC without moving locally':('host=false;', 'press();assert(clientSent==1 and spawns==0 and requested==0)'),
 'closed menu ignored':('menu=false;', 'press();assert(spawns==0)'),
 'hidden map ancestor ignored':('shown=false;', 'press();assert(spawns==0)'),
 'locked outpost stays locked':('locked=true;', 'press();assert(spawns==0)'),
 'nonPOI and unregistered destinations ignored':('poiValid=false;', 'press();assert(spawns==0);poiValid=true;destinationValid=false;press();assert(spawns==0)'),
 'Blueprint schema mismatch blocks before spawning':('wrongSchema=true;', 'press();assert(spawns==0 and requested==0);assert(table.concat(logs):find("GUARDED STOP",1,true))'),
 'missing departure door cleans up only temporary actor':('failedDoor=true;', 'press();assert(spawns==1 and requested==0 and destroyed==1)'),
 'rapid duplicate key suppressed':('', 'press();key();assert(spawns==1 and requested==1)'),
 'hook registered outside game thread and once':('', 'register();poll();assert(hookCount==1 and spawns==0)'),
 'server completes remote request without closing host menu':('menu=false;', 'register();receive(pc,false,nil,dest);assert(spawns==1 and requested==1);assert(table.concat(calls,",")=="setPawn,request")'),
 'normal native travel and cancellation untouched':('', 'register();receive(pc,false,dest,dest);receive(pc,true,nil,dest);assert(spawns==0 and requested==0)'),
 'client-side hook cannot execute travel':('', 'register();host=false;receive(pc,false,nil,dest);assert(spawns==0 and requested==0)'),
 'server rejects locked or stale destination':('', 'register();locked=true;receive(pc,false,nil,dest);assert(spawns==0);clock=clock+3;locked=false;destinationValid=false;receive(pc,false,nil,dest);assert(spawns==0)'),
 'server cooldown independent per controller and correct pawn':('', '''register();receive(pc,false,nil,dest);receive(pc,false,nil,dest);assert(spawns==1);
 local other=object('RemoteClientController',{CONTROLLER,'Engine.Controller','Engine.Actor'});other.HasAuthority=function() return true end
 local remotePawn=object('RemotePawn',{'Maine.SurvivalPlayerCharacter','Engine.Actor'});remotePawn.HasAuthority=function() return true end;remotePawn.GetTransform=function() return pawn:GetTransform() end
 other.K2_GetPawn=function() return remotePawn end;receive(other,false,nil,dest);assert(spawns==2 and requested==2 and spawnPawn==remotePawn)'''),
}
for name,(pre,post) in cases.items():
 s=lib.luaL_newstate();lib.luaL_openlibs(s)
 try:
  code=fixture+pre+'\nassert(load(script))()\nlocal passed,why=pcall(function() '+post+' end);if not passed then error(tostring(why)..table.concat(logs)) end'
  rc=lib.luaL_loadstring(s,code.encode())
  if not rc:rc=lib.lua_pcallk(s,0,0,0,0,None)
  if rc:raise AssertionError(name+': '+lib.lua_tolstring(s,-1,None).decode())
 finally:lib.lua_close(s)
 print('PASS',name)
print(str(len(cases))+' multiplayer teleport fixture groups passed; native Windows travel not verified')
