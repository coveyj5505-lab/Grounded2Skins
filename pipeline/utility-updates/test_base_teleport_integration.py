"""Production Lua native-map candidate, with on-demand server requests and native-map fixtures."""
import ctypes,re
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=(root/'runtime-teleport-v9/Teleport/Scripts/base_teleport.lua').read_text()
registry=(root/'runtime-teleport-v9/Teleport/Scripts/base_registry.lua').read_text()
guard=(root/'runtime-teleport-v9/Teleport/Scripts/teleport_native_guard.lua').read_text()
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
main=(root/'runtime-teleport-v9/Teleport/Scripts/main.lua').read_text()
base_schemas=source.split('local schemas=',1)[1].split('local fields=',1)[0].strip()
main_schemas=main.split('local schemas=',1)[1].split('local api=',1)[0].strip()
schemas='(function() local a='+main_schemas+';local b='+base_schemas+';for k,v in pairs(b) do a[k]=v end;return a end)()'
fixture=r'''
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local MAP='/Game/UI/Map/UI_Map.UI_Map_C'
local CONTROLLER='/Game/Blueprints/Player/BP_SurvivalPlayerController.BP_SurvivalPlayerController_C'
local enum='ByteProperty|EnumProperty';local specs=SCHEMAS
package.preload.teleport_native_guard=function() return assert(load(GUARD))() end
local baseBuildings={};local editing=false;local thread=false;local timer;local host=true;local menu=true;local showMap=true;local locked=false;local canTravel=true;local wrongRegistry=false;local emptyRegistry=false;local terrain=false;local metadataBad=false;local classReady=true;local spawnFail=false
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
 local n=o.full
 local part=object('PortableRenderPart'..n,{'Engine.StaticMeshComponent','Engine.PrimitiveComponent','Engine.SceneComponent'})
 local persistence=object('Persistence'..n,{'Maine.PersistenceComponent'});o.persistence=persistence
 function part:SetStaticMesh(mesh) assert(thread and mesh);if self.StaticMesh==mesh then return false end;self.StaticMesh=mesh;self.mesh=mesh;return true end
 o.StaticMeshComponent=part
 function part:SetVisibility(v,propagate) assert(thread and portable and v==false and propagate);self.visible=v end
 function part:SetRenderInMainPass(v) assert(thread and portable and v==false);self.main=v end
 function part:SetRenderInDepthPass(v) assert(thread and portable and v==false);self.depth=v end
 function part:SetCastShadow(v) assert(thread and portable and v==false);self.shadow=v end
 o.part=part
 function o:K2_GetComponentsByClass(cls) assert(thread and portable);local p=cls==objects['/Script/Maine.PersistenceComponent'] and persistence or part;return {{get=function() return p end}} end
 o.portable=portable;o.bAlwaysRelevant=true;o.bOnlyRelevantToOwner=false
 function o:HasAuthority() assert(thread);return host end
 function o:GetOwner() assert(thread);return self.owner end
 function o:GetTransform() assert(thread);if self.transform then return self.transform end;return {Translation={X=self.position or 1,Y=2,Z=3},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end
 function o:K2_SetActorTransform(t,sweep,hit,teleport) assert(thread and self.portable and sweep==false and teleport);moves=moves+1;if moveFail then return false end;self.transform=t;return true end
 function o:SetActorHiddenInGame(v) assert(thread and self.portable and v);self.hidden=v end
 function o:SetActorEnableCollision(v) assert(thread and self.portable and v==false);self.collision=v end
 function o:SetReplicates(v) assert(thread and v);self.replicates=v end
 function o:SetReplicateMovement(v) assert(thread and self.portable and v==true);self.movementReplicates=v end
 function o:SetLifeSpan(v) assert(thread and self.portable and (v==120 or v==30 or v==5));self.lifespan=v end
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
  assert(thread and not cancel and (target==destination or target.owner==baseBuildings[1]));target.IsInUse=true
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
function maine:IsEditMode() assert(thread);return editing end
function maine:GetSurvivalGameState(p) assert(thread and (p==pawn or p==remotePawn));return state end
local gameplay=object('Gameplay',{'Engine.GameplayStatics'})
function gameplay:BeginDeferredActorSpawnFromClass(p,cls,t,collision,owner,scale)
 assert(thread and host and (p==pawn or p==remotePawn or p==owner) and cls==objects[TP] and collision==1 and scale==1 and (owner==pc or owner==remote or owner==p));creates=creates+1;local a=departure(owner);a.transform={Translation={X=t.Translation.X,Y=t.Translation.Y,Z=t.Translation.Z}};return a
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
fieldSpecs['Engine.StaticMeshComponent']={StaticMesh='ObjectProperty'}
fieldSpecs['Maine.Building']={BuildingData='StructProperty',BuildingState='EnumProperty',StaticMeshComponent='ObjectProperty',bCanBeInstanced='BoolProperty',bShouldCreateLODActor='BoolProperty',bCanActorEverProxy='BoolProperty'}
fieldSpecs['Maine.MarkerBuilding']={CustomNameFiltered='StrProperty'}
fieldSpecs['Maine.MapMarkerWidget']={HUDMarkerData='ObjectProperty'}
fieldSpecs[MAP].TeleportButton='ObjectProperty'
fieldSpecs['/Game/UI/Buttons/UI_BottomButton.UI_BottomButton_C']={ButtonTextBlock='ObjectProperty'}
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
 if c=='MarkerBuilding' then return baseBuildings elseif c=='PlayerController' then return controllers elseif c=='MapWidget' then return {map} elseif c=='BP_Teleporter_C' then return sources end
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
local function logged(s) for _,v in ipairs(logs) do if v:find(s,1,true) then return true end end;return false end

local meshAsset=object('PadMesh',{'Engine.StaticMesh'})
local kismet=object('Kismet',{'Engine.KismetSystemLibrary'})
function kismet:IsServer(context) assert(thread);return host end
function kismet:MakeSoftObjectPath(p) assert(thread);return p end
function kismet:Conv_SoftObjPathToSoftObjRef(p) assert(thread);return p end
function kismet:LoadAsset_Blocking(p) assert(thread);return meshAsset end
objects['/Script/Engine.Default__KismetSystemLibrary']=kismet
local kt=object('TextLibrary',{'Engine.KismetTextLibrary'})
function kt:Conv_StringToText(s) assert(thread);return s end
objects['/Script/Engine.Default__KismetTextLibrary']=kt
local button=object('Button',{'/Game/UI/Buttons/UI_BottomButton.UI_BottomButton_C','UMG.Widget'})
local label=object('Label',{'UMG.TextBlock'})
function label:SetText(t) assert(thread);self.text=t end
function label:GetText() assert(thread);return self.text or "Teleport" end
function button:SetVisibility(v) assert(thread);self.visibility=v end
button.ButtonTextBlock=label;map.TeleportButton=button
local buildingTable=object('CompositeDataTable /Game/Blueprints/Items/Table_AllBuildings.Table_AllBuildings',{'Engine.CompositeDataTable'})
local function makeBase(name)
 local b=actor(object(name,{'Maine.MarkerBuilding','Maine.WidgetBuilding','Maine.Building','Engine.Actor'}),false)
 b.BuildingData={DataTable=buildingTable,RowName='RivetBaseTeleporter'};b.BuildingState=1;b.CustomNameFiltered='Home'
 return b
end
local baseBuilding=makeBase('Base1');baseBuildings={baseBuilding}
local markerData=object('MarkerData',{'Maine.HUDMarkerData'})
function markerData:GetReferencedActor() return baseBuildings[1] end
local baseEntry=object('BaseMapEntry',{'Maine.MapMarkerWidget'});baseEntry.HUDMarkerData=markerData
function panel:GetEntryUnderCursor() assert(thread);if terrain then return nil end;return baseEntry end
package.preload.base_registry=function() return assert(load(REGISTRY))() end
local implementation=assert(load(BASE))()
local mod=implementation.new({enumValue=function(n,l,ns) return n=='ESlateVisibility' and (l=='Collapsed' and 1 or 0) or 1 end,
 suppress=function(a) a:SetActorHiddenInGame(true);a:SetActorEnableCollision(false) end})
local function tickBases() ExecuteInGameThread(function() mod.tick() end);drain() end
local function target() local v;ExecuteInGameThread(function() v=mod.targetOnMap(map) end);drain();return v end
local function matches(t) local v;ExecuteInGameThread(function() v=mod.isTarget(t) end);drain();return v end

objects['/Script/UMG.ESlateVisibility']={IsValid=function() return true end,ForEachName=function(self,fn) fn({ToString=function() return 'Visible' end},0) end}
package.preload.base_teleport=function() return implementation end
'''
cases={
 'different player cannot start a second trip to an occupied base': 'ready();local t=sources[1];rpc(remote,false,nil,t);assert(creates==2 and requested==1 and t.IsInUse);rpc(pc,false,nil,t);assert(creates==2 and requested==1)',

 'map click reaches native travel through validated base target': 'ready();assert(creates==1 and button.visibility==0);hooks[MAP..":UGCTeleport"]({get=function() return map end});drain();assert(creates==2 and requested==1 and sources[1].owner==baseBuilding and sources[2].owner==pc and menu==false)',
 'remote reliable RPC accepts only the actual registered base target': 'ready();local t=sources[1];rpc(remote,false,nil,t);assert(creates==2 and requested==1 and sources[2].owner==remote and sources[2].Instigator==remotePawn)',
 'demolition races are rejected even before lifecycle tick': 'ready();local t=sources[1];baseBuilding.BuildingState=6;rpc(remote,false,nil,t);assert(creates==1 and requested==0 and logged("REJECTED"))',
 'forged native actor cannot impersonate a base': 'ready();local forged=departure(baseBuilding);rpc(remote,false,nil,forged);assert(creates==1 and requested==0 and logged("REJECTED"))',
 'stale map button cannot travel after demolition': 'ready();baseBuilding.BuildingState=6;hooks[MAP..":UGCTeleport"]({get=function() return map end});drain();assert(creates==1 and requested==0 and menu)',
 'rebuild uses fresh destination and retires demolished target': 'ready();local old=sources[1];baseBuilding.dead=true;baseBuildings={makeBase("Base2")};pulse();assert(creates==2 and old.dead);hooks[MAP..":UGCTeleport"]({get=function() return map end});drain();assert(creates==3 and requested==1 and sources[2].owner==baseBuildings[1])',
 'native base trip is not dispatched on ordinary trail marker': 'baseBuilding.BuildingData.RowName="MarkerBuilding";ready();hooks[MAP..":UGCTeleport"]({get=function() return map end});drain();assert(creates==0 and requested==0)',
}
for name,check in cases.items():
 code=fixture.replace('SCHEMAS',schemas).replace('GUARD','[====['+guard+']====]').replace('REGISTRY','[====['+registry+']====]').replace('BASE','[====['+source+']====]')+'\n'+main+'\nlocal checked,why=pcall(function() '+check+' end);if not checked then error(tostring(why).." LOGS: "..table.concat(logs," | ")) end'
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  r=lib.luaL_loadstring(state,code.encode())
  if not r:r=lib.lua_pcallk(state,0,0,0,0,None)
  if r:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
print(len(cases),'production map/base/RPC integration Lua groups passed; native Windows acceptance pending')
