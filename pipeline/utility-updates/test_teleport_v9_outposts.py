"""Production Lua native-map candidate, with on-demand server requests and native-map fixtures."""
import ctypes,re
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=(root/'runtime-teleport-v9/Teleport/Scripts/main.lua').read_text()
guard=(root/'runtime-teleport-v9/Teleport/Scripts/teleport_native_guard.lua').read_text()
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
schemas=source.split('local schemas=',1)[1].split('local api=',1)[0].strip()
fixture=r'''
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local MAP='/Game/UI/Map/UI_Map.UI_Map_C'
local CONTROLLER='/Game/Blueprints/Player/BP_SurvivalPlayerController.BP_SurvivalPlayerController_C'
local enum='ByteProperty|EnumProperty';local specs=SCHEMAS
package.preload.teleport_native_guard=function() return assert(load(GUARD))() end
local thread=false;local timer;local host=true;local menu=true;local showMap=true;local locked=false;local canTravel=true;local wrongRegistry=false;local emptyRegistry=false;local terrain=false;local metadataBad=false;local classReady=true;local spawnFail=false
local logs={};print=function(s) logs[#logs+1]=s end
local moveFail=false;local creates,refreshes,moves,destroyed=0,0,0,0
local objects={};local sources={}
local function path(c) return c:sub(1,1)=='/' and c or '/Script/'..c end
local function object(n,classes)
 local o={full=n,classes=classes,IsValid=function(s) return not s.dead end,GetFullName=function(s) return s.full end}
 function o:GetClass()
  local function cls(i) if not self.classes or not self.classes[i] then return nil end
   local c=self.classes[i]
   return {IsValid=function() return true end,GetFullName=function() return 'Class '..path(c) end,GetSuperStruct=function() return cls(i+1) end}
  end;return cls(1)
 end
 return o
end
local function actor(o,portable)
 local part=object('PortableRenderPart',{'Engine.PrimitiveComponent','Engine.SceneComponent'})
 function part:SetVisibility(v,propagate) assert(thread and portable and v==false and propagate);self.visible=v end
 function part:SetRenderInMainPass(v) assert(thread and portable and v==false);self.main=v end
 function part:SetRenderInDepthPass(v) assert(thread and portable and v==false);self.depth=v end
 function part:SetCastShadow(v) assert(thread and portable and v==false);self.shadow=v end
 o.part=part
 function o:K2_GetComponentsByClass(cls) assert(thread and portable);return {{get=function() return part end}} end
 o.portable=portable;o.bAlwaysRelevant=true;o.bOnlyRelevantToOwner=false
 function o:HasAuthority() assert(thread);return host end
 function o:GetOwner() assert(thread);return self.owner end
 function o:GetTransform() assert(thread);if self.transform then return self.transform end;return {Translation={X=self.position or 1,Y=2,Z=3},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end
 function o:K2_SetActorTransform(t,sweep,hit,teleport) assert(thread and self.portable and sweep==false and teleport);moves=moves+1;if moveFail then return false end;self.transform=t;return true end
 function o:SetActorHiddenInGame(v) assert(thread and self.portable and v);self.hidden=v end
 function o:SetActorEnableCollision(v) assert(thread and self.portable and v==false);self.collision=v end
 function o:SetReplicates(v) assert(thread and v);self.replicates=v end
 function o:SetReplicateMovement(v) assert(thread and self.portable and v==true);self.movementReplicates=v end
 function o:SetLifeSpan(v) assert(thread and self.portable and (v==120 or v==30));self.lifespan=v end
 function o:K2_DestroyActor() assert(thread and self.portable);self.dead=true;destroyed=destroyed+1 end
 return o
end
local pawn=actor(object('Pawn',{'Maine.SurvivalPlayerCharacter','Engine.Pawn','Engine.Actor'}),false)
local pc=actor(object('LocalPC',{CONTROLLER,'Maine.SurvivalPlayerController','Engine.Controller','Engine.Actor'}),false)
function pc:K2_GetPawn() assert(thread);return pawn end
function pc:IsLocalController() assert(thread);return true end
local remotePawn=actor(object('RemotePawn',{'Maine.SurvivalPlayerCharacter','Engine.Pawn','Engine.Actor'}),false)
local remote=actor(object('RemotePC',{CONTROLLER,'Maine.SurvivalPlayerController','Engine.Controller','Engine.Actor'}),false)
function remote:K2_GetPawn() return remotePawn end
function remote:IsLocalController() return false end
local controllers={pc}
local requested,rpcSent,nativeRequests=0,0,0;local clock=100;os.time=function() return clock end
local hooks={};local registrations={};local failHook=false;local sentTarget;local deferred={}
local destination
local function departure(owner)
 local a=actor(object('Portable'..(#sources+1),{TP,'Engine.Actor'}),true);a.owner=owner;a.Instigator=owner==pc and pawn or remotePawn;a.IsInUse=false;a.POIDataAsset=nil
 local r=object('PortableRoot',{'Engine.SceneComponent'});function r:SetMobility(v) assert(thread and v==1);self.movable=true end;function a:K2_GetRootComponent() return r end
 local d=actor(object('PortableDoor'..(#sources+1),{DOOR,'Maine.Switch','Engine.Actor'}),true);a.Teleporter_Door_Object_REF=d;d.TeleporterOwner=a;d.PersistenceComponent=object('PortablePersistence',{'Maine.PersistenceComponent'});d.PersistenceComponent.bNeverSpawnAsDynamicActor=false;d.PersistenceComponent.bShouldEditModeSave=true
 function a:SetTeleportDoorRef() assert(thread);assert(self.Teleporter_Door_Object_REF.TeleporterOwner==self) end
 function d:SetAndPrintInteractionInstigator(p) assert(thread);self.instigator=p end
 function a:OnTeleportRequested(cancel,target)
  assert(thread and not cancel and target==destination)
  assert(self.lifespan==30 and self.Teleporter_Door_Object_REF.lifespan==30)
  assert(self.hidden and self.collision==false and self.Teleporter_Door_Object_REF.collision==false)
  assert(self.Teleporter_Door_Object_REF.PersistenceComponent.bNeverSpawnAsDynamicActor)
  assert(not self.Teleporter_Door_Object_REF.PersistenceComponent.bShouldEditModeSave)
  self.IsInUse=true;requested=requested+1
 end
 sources[#sources+1]=a;return a
end
destination=actor(object('OutpostParent',{TP,'Engine.Actor'}),false)
destination.IsInUse=false
local door=actor(object('RegisteredDoor',{DOOR,'Maine.Switch','Engine.Actor'}),false);door.TeleporterOwner=destination
local poi=object('UnlockedOutpost',{'Maine.PointOfInterestDataAsset'});destination.POIDataAsset=poi
local entry=object('Marker',{'Maine.MapPOIWidget'});entry.POIData=poi
local panel=object('MapPanel',{'Maine.MapPanelWidget'})
function panel:GetEntryUnderCursor() assert(thread);if terrain then return nil end;return entry end
local map=object('Map',{MAP,'Maine.MapWidget','UMG.Widget'});map.MapPanel=panel;map.IsInPTSView=false;map.InteractableItem=nil;map.PTSTravelRequested=false
function map:IsVisible() assert(thread);return showMap end
function map:GetParent() return nil end
function map:RefreshPTSButton() assert(thread);refreshes=refreshes+1;self.nativeButtonVisible=self.IsInPTSView and not terrain and not locked and canTravel and not emptyRegistry and not wrongRegistry end
local manager=object('Manager',{'Maine.WidgetManager'})
function manager:IsInGameMenuActive() assert(thread);return menu end
local state=object('State',{'Maine.SurvivalGameState'})
function state:IsPTSTravelLocked(p) assert(thread and p==poi);return locked end
function state:CanPTSTravel(p) assert(thread and p==poi);return canTravel end
function state:GetRegisteredPTSTravel(p) assert(thread and p==poi);if emptyRegistry then return nil end;return wrongRegistry and destination or door end
local ui=object('UIStatics',{'Maine.UserInterfaceStatics'})
function ui:GetWidgetManager(p) assert(thread and p==pawn);return manager end
function manager:HideInGameMenu() assert(thread);menu=false end
function pc:ServerRequestPTSTravel(cancel,source,target) assert(thread and not cancel and source==nil);rpcSent=rpcSent+1;sentTarget=target end
local maine=object('Statics',{'Maine.SurvivalGameplayStatics'})
function maine:GetSurvivalGameState(p) assert(thread and (p==pawn or p==remotePawn));return state end
local gameplay=object('Gameplay',{'Engine.GameplayStatics'})
function gameplay:BeginDeferredActorSpawnFromClass(p,cls,t,collision,owner,scale)
 assert(thread and host and (p==pawn or p==remotePawn) and cls==objects[TP] and collision==1 and scale==1 and (owner==pc or owner==remote));creates=creates+1;local a=departure(owner);a.transform={Translation={X=t.Translation.X,Y=t.Translation.Y,Z=t.Translation.Z}};return a
end
function gameplay:FinishSpawningActor(a,t,scale) assert(thread and scale==1 and a.portable);assert(not spawnFail,'Simulated finish failure');return a end
local function meta(class,fieldTypes)
 local o=object('Class '..path(class))
 function o:ForEachProperty(fn)
  for n,t in pairs(fieldTypes) do fn({GetFullName=function() return (metadataBad and n=='IsInPTSView' and 'ObjectProperty' or t)..' '..path(class)..'.'..n end}) end
 end
 return o
end
local fieldSpecs={['Maine.Switch']={PersistenceComponent='ObjectProperty'},['Maine.PersistenceComponent']={bNeverSpawnAsDynamicActor='BoolProperty',bShouldEditModeSave='BoolProperty'},['Engine.Actor']={bOnlyRelevantToOwner='BoolProperty',bAlwaysRelevant='BoolProperty',Instigator='ObjectProperty'},['Maine.MapWidget']={MapPanel='ObjectProperty'},['Maine.MapPOIWidget']={POIData='ObjectProperty'},[MAP]={IsInPTSView='BoolProperty',InteractableItem='ObjectProperty',PTSTravelRequested='BoolProperty'},[TP]={Teleporter_Door_Object_REF='ObjectProperty',POIDataAsset='ObjectProperty',IsInUse='BoolProperty'},[DOOR]={TeleporterOwner='ObjectProperty',['Interaction Instigator']='ObjectProperty'}}
for c,f in pairs(fieldSpecs) do objects[path(c)]=meta(c,f) end
local cdo=actor(object('TP_CDO',{TP,'Engine.Actor'}),false);cdo.POIDataAsset=nil
objects['/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.Default__BP_Teleporter_C']=cdo
objects['/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.Default__BP_Teleporter_Door_C']=actor(object('DOOR_CDO',{DOOR,'Maine.Switch','Engine.Actor'}),false)
objects['/Script/Engine.SceneComponent']=object('SceneComponentClass',{'Engine.Class'});objects['/Script/Engine.Default__GameplayStatics']=gameplay;objects['/Script/Maine.Default__UserInterfaceStatics']=ui;objects['/Script/Maine.Default__SurvivalGameplayStatics']=maine
for _,en in ipairs({'ESpawnActorCollisionHandlingMethod','ESpawnActorScaleMethod','EComponentMobility'}) do
 local e=object('Enum');function e:ForEachName(fn) fn({ToString=function() return en=='EComponentMobility' and 'Movable' or en=='ESpawnActorScaleMethod' and 'MultiplyWithRoot' or 'AlwaysSpawn' end},1) end;objects['/Script/Engine.'..en]=e
end
function StaticFindObject(p)
 if not classReady and p==TP then return nil end
 local o=objects[p];if o then return o end
 if p==MAP..':PTSTravel' or p==MAP..':UGCTeleport' or p==MAP..':RefreshTeleportButton' then return object('MapTravelFunction') end
 for key,s in pairs(specs) do
  local c,m=key:match('^(.*)%.([^%.]+)$')
  if p==path(c)..':'..m then return meta(c..':'..m,s) end
 end
end
function FindAllOf(c)
 assert(thread)
 if c=='MarkerBuilding' then return {} elseif c=='PlayerController' then return controllers elseif c=='MapWidget' then return {map} elseif c=='BP_Teleporter_C' then return sources end
 error('Unexpected class scan '..c)
end

function ExecuteInGameThread(fn) deferred[#deferred+1]=fn end
local function drain()
 local steps=0
 while #deferred>0 do steps=steps+1;assert(steps<100,'Unbounded deferred work');local fn=table.remove(deferred,1);thread=true;fn();thread=false end
end
function LoopAsync(ms,fn) assert(ms==250);timer=fn end
function RegisterKeyBind() error('Native travel must not bind a key') end
function RegisterHook(p,fn)
 assert(not thread,'Register hooks outside game thread')
 if failHook and p==MAP..':PTSTravel' then error('Map hook not ready') end
 assert(p==MAP..':PTSTravel' or p==CONTROLLER..':ServerRequestPTSTravel' or p==MAP..':UGCTeleport' or p==MAP..':RefreshTeleportButton')
 registrations[p]=(registrations[p] or 0)+1;assert(registrations[p]==1,'Duplicate hook')
 hooks[p]=fn;return 1,2
end
local function pulse() timer();drain() end
local function ready() pulse();pulse();assert(hooks[MAP..':PTSTravel'] and hooks[CONTROLLER..':ServerRequestPTSTravel']) end
local function hold()
 assert(map.nativeButtonVisible,'Native hold must be available')
 -- Stock PTSTravel exits at the missing InteractableItem cast, before a request.
 if map.InteractableItem then nativeRequests=nativeRequests+1 end
 hooks[MAP..':PTSTravel']({get=function() return map end});drain()
end
local function rpc(controller,cancel,source,target)
 hooks[CONTROLLER..':ServerRequestPTSTravel']({get=function() return controller end},{get=function() return cancel end},{get=function() return source end},{get=function() return target end});drain()
end
local kismet=object('Kismet',{'Engine.KismetSystemLibrary'});function kismet:IsServer(context) assert(thread);return host end;objects['/Script/Engine.Default__KismetSystemLibrary']=kismet
local function logged(s) for _,v in ipairs(logs) do if v:find(s,1,true) then return true end end;return false end

package.preload.base_teleport=function() return {new=function() return {tick=function() end,guardTemporary=function() end,isTarget=function() return false end,refreshButton=function() end,targetOnMap=function() end} end} end
'''
cases={
 'startup and map opening create no actors': 'ready();for i=1,20 do pulse() end;assert(creates==0 and moves==0 and map.InteractableItem==nil and map.IsInPTSView)',
 'native hold completion creates one bounded departure': 'ready();hold();assert(creates==1 and requested==1 and nativeRequests==0 and rpcSent==0);assert(sources[1].owner==pc and sources[1].Instigator==pawn and sources[1].Teleporter_Door_Object_REF["Interaction Instigator"]==pawn);assert(sources[1].movementReplicates and sources[1].replicates)',
 'no follower movement or lifetime renewal after request': 'ready();hold();local a=sources[1];local x=a.transform.Translation.X;pawn.position=5000;for i=1,20 do pulse() end;assert(moves==0 and creates==1 and a.transform.Translation.X==x and a.lifespan==30 and a.Teleporter_Door_Object_REF.lifespan==30)',
 'new trip creates at the new pawn position instead of reusing old pod': 'ready();hold();sources[1].IsInUse=false;clock=clock+3;pawn.position=9000;menu=true;ready();hold();assert(creates==2 and requested==2 and sources[2].transform.Translation.X==9000 and moves==0)',
 'save persistence flags are set before native travel': 'ready();hold();local p=sources[1].Teleporter_Door_Object_REF.PersistenceComponent;assert(p.bNeverSpawnAsDynamicActor and not p.bShouldEditModeSave);assert(door.PersistenceComponent==nil)',
 'menu close restores map mode without injecting a door': 'ready();hold();pulse();assert(not map.IsInPTSView and map.InteractableItem==nil and destroyed==0)',
 'stable hover preserves hold progress': 'ready();local n=refreshes;for i=1,12 do pulse() end;assert(refreshes==n and creates==0)',
 'locked hover cannot offer native hold': 'locked=true;ready();assert(not map.IsInPTSView and not map.nativeButtonVisible and creates==0)',
 'lock change during hold rejects request': 'ready();locked=true;hold();assert(creates==0 and requested==0 and menu)',
 'CanPTSTravel restriction rejects requests': 'ready();canTravel=false;hold();assert(creates==0 and requested==0)',
 'unregistered marker never offers travel': 'emptyRegistry=true;ready();assert(not map.IsInPTSView and creates==0)',
 'wrong registry actor is rejected': 'wrongRegistry=true;ready();assert(not map.IsInPTSView and creates==0)',
 'terrain and trail markers remain unsupported': 'terrain=true;ready();assert(not map.IsInPTSView);terrain=false;entry.classes={"Maine.MapMarkerWidget"};pulse();assert(not map.IsInPTSView and creates==0)',
 'real native pod travel is not intercepted': 'ready();map.InteractableItem=door;hold();assert(creates==0 and requested==0 and nativeRequests==1);pulse();assert(map.InteractableItem==door and map.IsInPTSView)',
 'joining client sends reliable request and never spawns': 'host=false;ready();hold();assert(rpcSent==1 and sentTarget==destination and creates==0 and requested==0);assert(logged("CLIENT_REQUEST_SENT"))',
 'client-side RPC callback cannot spawn': 'host=false;ready();rpc(pc,false,nil,destination);assert(creates==0 and requested==0)',
 'server handles remote request without opening its own map': 'menu=false;controllers={remote};pulse();pulse();assert(hooks[CONTROLLER..":ServerRequestPTSTravel"]);rpc(remote,false,nil,destination);assert(creates==1 and requested==1 and sources[1].owner==remote and sources[1].Instigator==remotePawn)',
 'server revalidates destination lock': 'ready();locked=true;rpc(remote,false,nil,destination);assert(creates==0 and logged("REJECTED"))',
 'server revalidates registry identity': 'ready();local fake=actor(object("Forged",{TP,"Engine.Actor"}),false);fake.POIDataAsset=poi;fake.IsInUse=false;rpc(remote,false,nil,fake);assert(creates==0 and logged("REJECTED"))',
 'server rejects busy destination': 'ready();destination.IsInUse=true;rpc(remote,false,nil,destination);assert(creates==0)',
 'cancellation without departure creates nothing': 'ready();rpc(remote,true,nil,destination);assert(creates==0)',
 'existing departure RPC is left to native code': 'ready();rpc(remote,false,destination,destination);assert(creates==0)',
 'repeated RPC is rate limited and busy trip cannot respawn': 'ready();rpc(remote,false,nil,destination);rpc(remote,false,nil,destination);assert(creates==1);clock=clock+3;rpc(remote,false,nil,destination);assert(creates==1)',
 'different server players get request-specific sources': 'ready();rpc(pc,false,nil,destination);rpc(remote,false,nil,destination);assert(creates==2 and sources[1].owner==pc and sources[2].owner==remote)',
 'finish failure cleans temporary source without touching outpost': 'ready();spawnFail=true;hold();assert(creates==1 and requested==0 and destroyed==2 and destination.dead==nil and door.dead==nil and logged("SERVER_REQUEST_STOP")==false and logged("MAP_REQUEST_STOP"))',
 'class not loaded refuses spawning and permits later retry': 'ready();classReady=false;hold();assert(creates==0);classReady=true;menu=true;ready();hold();assert(creates==1)',
 'metadata mismatch refuses UI mutation and actor creation': 'metadataBad=true;ready();assert(creates==0 and map.InteractableItem==nil and not map.IsInPTSView and logged("UI_GUARDED_STOP"))',
 'partially registered hooks retry without duplicating RPC hook': 'failHook=true;pulse();pulse();assert(not map.IsInPTSView and hooks[CONTROLLER..":ServerRequestPTSTravel"] and not hooks[MAP..":PTSTravel"]);failHook=false;pulse();assert(map.IsInPTSView and registrations[CONTROLLER..":ServerRequestPTSTravel"]==1)',
}
for name,check in cases.items():
 code=fixture.replace('SCHEMAS',schemas).replace('GUARD','[====['+guard+']====]')+'\n'+source+'\nlocal checked,why=pcall(function() '+check+' end);if not checked then error(tostring(why).." LOGS: "..table.concat(logs," | ")) end'
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  r=lib.luaL_loadstring(state,code.encode())
  if not r:r=lib.lua_pcallk(state,0,0,0,0,None)
  if r:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
print(len(cases),'on-demand Lua fixture groups passed; Windows hold/travel/save behavior not proven')
