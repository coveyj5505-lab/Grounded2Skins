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
schemas=source.split('local schemas=',1)[1].split('local fields=',1)[0].strip()
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
local fieldSpecs={['Maine.Switch']={PersistenceComponent='ObjectProperty'},['Maine.PersistenceComponent']={bNeverSpawnAsDynamicActor='BoolProperty',bShouldEditModeSave='BoolProperty'},['Engine.Actor']={bOnlyRelevantToOwner='BoolProperty',bAlwaysRelevant='BoolProperty',Instigator='ObjectProperty'},['Maine.MapWidget']={MapPanel='ObjectProperty'},['Maine.MapPOIWidget']={POIData='ObjectProperty'},[MAP]={IsInPTSView='BoolProperty',InteractableItem='ObjectProperty',PTSTravelRequested='BoolProperty'},[TP]={PersistenceComponent='ObjectProperty',Teleporter_Door_Object_REF='ObjectProperty',POIDataAsset='ObjectProperty',IsInUse='BoolProperty'},[DOOR]={TeleporterOwner='ObjectProperty',['Interaction Instigator']='ObjectProperty'}}
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
 if p==MAP..':PTSTravel' then return object('MapTravelFunction') end
 for key,s in pairs(specs) do
  local c,m=key:match('^(.*)%.([^%.]+)$')
  if p==path(c)..':'..m then return meta(c..':'..m,s) end
 end
end
function FindAllOf(c)
 assert(thread)
 if c=='MarkerBuilding' or c=='BP_MarkerBuilding_C' then return baseBuildings elseif c=='PlayerController' then return controllers elseif c=='MapWidget' then return {map} elseif c=='BP_Teleporter_C' then return sources end
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
 assert(p==MAP..':PTSTravel' or p==CONTROLLER..':ServerRequestPTSTravel')
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
'''
cases={
 'exact blueprint scan finds bases when native class scan is empty': 'local original=FindAllOf;FindAllOf=function(c) if c=="MarkerBuilding" then return {} end;return original(c) end;tickBases();assert(creates==1 and logged("BASE_IDENTITY"))',

 'zero-indexed persistence array is guarded': 'local native=objects["/Script/Engine.Default__GameplayStatics"].FinishSpawningActor;objects["/Script/Engine.Default__GameplayStatics"].FinishSpawningActor=function(self,a,t,s) local r=native(self,a,t,s);local original=a.K2_GetComponentsByClass;a.K2_GetComponentsByClass=function(self,cls) if cls==objects["/Script/Maine.PersistenceComponent"] then return {[0]=self.persistence} end;return original(self,cls) end;return r end;tickBases();assert(creates==1 and sources[1].persistence.bNeverSpawnAsDynamicActor)',
 'empty component array uses guarded blueprint reference': 'local native=objects["/Script/Engine.Default__GameplayStatics"].FinishSpawningActor;objects["/Script/Engine.Default__GameplayStatics"].FinishSpawningActor=function(self,a,t,s) local r=native(self,a,t,s);a.PersistenceComponent=a.persistence;local original=a.K2_GetComponentsByClass;a.K2_GetComponentsByClass=function(self,cls) if cls==objects["/Script/Maine.PersistenceComponent"] then return {} end;return original(self,cls) end;return r end;tickBases();assert(creates==1 and sources[1].persistence.bNeverSpawnAsDynamicActor and logged("PERSISTENCE_LOOKUP"))',
 'missing persistence array and reference still reject travel': 'local native=objects["/Script/Engine.Default__GameplayStatics"].FinishSpawningActor;objects["/Script/Engine.Default__GameplayStatics"].FinishSpawningActor=function(self,a,t,s) local r=native(self,a,t,s);local original=a.K2_GetComponentsByClass;a.K2_GetComponentsByClass=function(self,cls) if cls==objects["/Script/Maine.PersistenceComponent"] then return {} end;return original(self,cls) end;return r end;local ok=pcall(tickBases);assert(not ok and sources[1].dead and logged("PERSISTENCE_LOOKUP"))',

 'uninitialized preview cannot block another players completed base': 'baseBuilding.BuildingState=2;baseBuilding.StaticMeshComponent=nil;local other=makeBase("OtherPlayersBase");baseBuildings={baseBuilding,other};tickBases();assert(creates==1 and sources[1].owner==other and matches(sources[1]) and logged("BASE_VISUAL_WAIT"))',

 'preview-to-built transition accepts an already assigned pad mesh': 'baseBuilding.BuildingState=2;tickBases();baseBuilding.BuildingState=1;tickBases();assert(creates==1 and target()==sources[1])',
 'client replicas stay hidden with the map closed': 'host=false;menu=false;local a=departure(baseBuilding);a.hidden=false;a.collision=true;a.Teleporter_Door_Object_REF.hidden=false;tickBases();assert(creates==0 and a.hidden and not a.collision and a.Teleporter_Door_Object_REF.hidden)',

 'client-local authority never creates server targets': 'host=false;baseBuilding.HasAuthority=function() return true end;tickBases();assert(creates==0 and not baseBuilding.replicates)',
 'host explicitly replicates building target and door': 'tickBases();assert(baseBuilding.replicates and sources[1].replicates and sources[1].Teleporter_Door_Object_REF.replicates)',

 'changing marker restores native map button text and visibility': 'tickBases();ExecuteInGameThread(function() mod.refreshButton(map) end);drain();assert(label.text=="Travel to Base");terrain=true;ExecuteInGameThread(function() mod.refreshButton(map) end);drain();assert(label.text=="Teleport" and button.visibility==1)',
 'busy base hides its travel button': 'tickBases();ExecuteInGameThread(function() mod.refreshButton(map) end);drain();sources[1].IsInUse=true;ExecuteInGameThread(function() mod.refreshButton(map) end);drain();assert(label.text=="Teleport" and button.visibility==1)',

 'completed building creates one guarded server target': 'tickBases();assert(creates==1 and target()==sources[1] and matches(sources[1]));assert(sources[1].owner==baseBuilding and sources[1].hidden and not sources[1].collision)',
 'native trail markers stay unchanged': 'baseBuilding.BuildingData.RowName="MarkerBuilding";tickBases();assert(creates==0 and not baseBuilding.part.mesh and target()==nil)',
 'placement preview gets a pad mesh but no target': 'baseBuilding.BuildingState=2;tickBases();assert(creates==0 and baseBuilding.part.mesh==meshAsset and target()==nil)',
 'incomplete building is not a travel destination': 'baseBuilding.BuildingState=4;tickBases();assert(creates==0 and target()==nil)',
 'repeated ticks do not duplicate native backend': 'tickBases();for i=1,8 do tickBases() end;assert(creates==1 and target()==sources[1])',
 'parent and child are excluded from saved dynamic restore': 'tickBases();local a=sources[1];assert(a.persistence.bNeverSpawnAsDynamicActor and not a.persistence.bShouldEditModeSave and a.Teleporter_Door_Object_REF.persistence.bNeverSpawnAsDynamicActor)',
 'demolition unregisters and destroys idle target': 'tickBases();baseBuilding.BuildingState=6;tickBases();assert(target()==nil and not matches(sources[1]) and sources[1].dead and sources[1].Teleporter_Door_Object_REF.dead and destroyed==2)',
 'destroy and rebuild at same position creates a fresh target': 'tickBases();local old=sources[1];baseBuilding.dead=true;baseBuildings={makeBase("Base2")};tickBases();assert(creates==2 and old.dead and target()==sources[2] and sources[2].owner==baseBuildings[1])',
 'busy target retires immediately from selection but waits for native travel': 'tickBases();local a=sources[1];a.IsInUse=true;baseBuilding.dead=true;tickBases();assert(target()==nil and not matches(a) and not a.dead and a.lifespan==30);a.IsInUse=false;tickBases();assert(a.dead)',
 'rebuild does not inherit the old in-use target': 'tickBases();local old=sources[1];old.IsInUse=true;baseBuilding.dead=true;baseBuildings={makeBase("Base2")};tickBases();assert(creates==2 and not old.dead and target()==sources[2] and not matches(old));old.IsInUse=false;tickBases();assert(old.dead)',
 'same name after destruction does not revive stale target': 'tickBases();local old=sources[1];old.IsInUse=true;baseBuilding.dead=true;baseBuildings={makeBase("Base1")};tickBases();assert(creates==2 and target()==sources[2] and not matches(old) and baseBuildings[1].part.mesh==meshAsset);old.IsInUse=false;tickBases();assert(old.dead)',
 'disappearing source is recreated for the actual building': 'tickBases();sources[1].dead=true;tickBases();assert(creates==2 and target()==sources[2])',
 'clients never spawn a local backend': 'host=false;tickBases();assert(creates==0);local replicated=departure(baseBuilding);assert(target()==replicated)',
 'clients never borrow another buildings target': 'host=false;tickBases();departure(makeBase("DifferentBase"));assert(target()==nil)',
 'ambiguous client backends are rejected': 'host=false;tickBases();departure(baseBuilding);departure(baseBuilding);local ok=pcall(target);assert(not ok)',
 'base target follows building relocation, never player movement': 'tickBases();local a=sources[1];baseBuilding.position=500;tickBases();assert(a.transform.Translation.X==500);pawn.position=9000;tickBases();assert(a.transform.Translation.X==500)',
 'in-use arrival target never moves during relocation': 'tickBases();local a=sources[1];a.IsInUse=true;local x=a.transform.Translation.X;baseBuilding.position=500;tickBases();assert(a.transform.Translation.X==x);a.IsInUse=false;tickBases();assert(a.transform.Translation.X==500)',
 'creative edit mode does not create survival destinations': 'editing=true;tickBases();assert(creates==0 and target()==nil)',
 'map button addresses only the completed base target': 'tickBases();ExecuteInGameThread(function() mod.refreshButton(map) end);drain();assert(button.visibility==0 and label.text=="Travel to Base")',
 'failed native construction destroys only temporary target and door': 'spawnFail=true;local ok=pcall(tickBases);assert(not ok and creates==1 and destroyed==2 and not baseBuilding.dead)',
}
for name,check in cases.items():
 code=fixture.replace('SCHEMAS',schemas).replace('GUARD','[====['+guard+']====]').replace('REGISTRY','[====['+registry+']====]').replace('BASE','[====['+source+']====]')+'\nlocal checked,why=pcall(function() '+check+' end);if not checked then error(tostring(why).." LOGS: "..table.concat(logs," | ")) end'
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  r=lib.luaL_loadstring(state,code.encode())
  if not r:r=lib.lua_pcallk(state,0,0,0,0,None)
  if r:raise AssertionError(name+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',name)
 finally:lib.lua_close(state)
print(len(cases),'production base-module Lua fixture groups passed; Windows building/travel/save behavior not proven')
