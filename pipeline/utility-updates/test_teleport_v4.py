"""Production Lua native-map candidate, with server/replica/UI ownership fixtures."""
import ctypes,re
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=(root/'runtime-teleport-v4/Teleport/Scripts/main.lua').read_text()
guard=(root/'runtime-teleport-v4/Teleport/Scripts/teleport_native_guard.lua').read_text()
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
schemas=source.split('local schemas=',1)[1].split('local api=',1)[0].strip()
fixture=r'''
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local MAP='/Game/UI/Map/UI_Map.UI_Map_C'
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
 o.portable=portable;o.bAlwaysRelevant=true;o.bOnlyRelevantToOwner=false
 function o:HasAuthority() assert(thread);return host end
 function o:GetOwner() assert(thread);return self.owner end
 function o:GetTransform() assert(thread);if self.transform then return self.transform end;return {Translation={X=self.position or 1,Y=2,Z=3},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end
 function o:K2_SetActorTransform(t,sweep,hit,teleport) assert(thread and self.portable and sweep==false and teleport);moves=moves+1;if moveFail then return false end;self.transform=t;return true end
 function o:SetActorHiddenInGame(v) assert(thread and self.portable and v);self.hidden=v end
 function o:SetActorEnableCollision(v) assert(thread and self.portable and v==false);self.collision=v end
 function o:SetReplicateMovement(v) assert(thread and self.portable and v==true);self.movementReplicates=v end
 function o:SetLifeSpan(v) assert(thread and self.portable and (v==120 or v==30));self.lifespan=v end
 function o:K2_DestroyActor() assert(thread and self.portable);self.dead=true;destroyed=destroyed+1 end
 return o
end
local pawn=actor(object('Pawn',{'Maine.SurvivalPlayerCharacter','Engine.Pawn','Engine.Actor'}),false)
local pc=actor(object('LocalPC',{'Maine.SurvivalPlayerController','Engine.Controller','Engine.Actor'}),false)
function pc:K2_GetPawn() assert(thread);return pawn end
function pc:IsLocalController() assert(thread);return true end
local remotePawn=actor(object('RemotePawn',{'Maine.SurvivalPlayerCharacter','Engine.Pawn','Engine.Actor'}),false)
local remote=actor(object('RemotePC',{'Maine.SurvivalPlayerController','Engine.Controller','Engine.Actor'}),false)
function remote:K2_GetPawn() return remotePawn end
function remote:IsLocalController() return false end
local controllers={pc}
local function departure(owner)
 local a=actor(object('Portable'..(#sources+1),{TP,'Engine.Actor'}),true);a.owner=owner;a.Instigator=owner==pc and pawn or remotePawn;a.IsInUse=false;a.POIDataAsset=nil
 local r=object('PortableRoot',{'Engine.SceneComponent'});function r:SetMobility(v) assert(thread and v==1);self.movable=true end;function a:K2_GetRootComponent() return r end
 local d=actor(object('PortableDoor'..(#sources+1),{DOOR,'Engine.Actor'}),true);a.Teleporter_Door_Object_REF=d;d.TeleporterOwner=a
 function a:SetTeleportDoorRef() assert(thread);assert(self.Teleporter_Door_Object_REF.TeleporterOwner==self) end
 function d:SetAndPrintInteractionInstigator(p) assert(thread);self.instigator=p end
 sources[#sources+1]=a;return a
end
local destination=actor(object('OutpostParent',{TP,'Engine.Actor'}),false)
local door=actor(object('RegisteredDoor',{DOOR,'Engine.Actor'}),false);door.TeleporterOwner=destination
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
local maine=object('Statics',{'Maine.SurvivalGameplayStatics'})
function maine:GetSurvivalGameState(p) assert(thread and (p==pawn or p==remotePawn));return state end
local gameplay=object('Gameplay',{'Engine.GameplayStatics'})
function gameplay:BeginDeferredActorSpawnFromClass(p,cls,t,collision,owner,scale)
 assert(thread and host and (p==pawn or p==remotePawn) and cls==objects[TP] and collision==1 and scale==1 and (owner==pc or owner==remote));creates=creates+1;return departure(owner)
end
function gameplay:FinishSpawningActor(a,t,scale) assert(thread and scale==1 and a.portable);assert(not spawnFail,'Simulated finish failure');return a end
local function meta(class,fieldTypes)
 local o=object('Class '..path(class))
 function o:ForEachProperty(fn)
  for n,t in pairs(fieldTypes) do fn({GetFullName=function() return (metadataBad and n=='IsInPTSView' and 'ObjectProperty' or t)..' '..path(class)..'.'..n end}) end
 end
 return o
end
local fieldSpecs={['Engine.Actor']={bOnlyRelevantToOwner='BoolProperty',bAlwaysRelevant='BoolProperty',Instigator='ObjectProperty'},['Maine.MapWidget']={MapPanel='ObjectProperty'},['Maine.MapPOIWidget']={POIData='ObjectProperty'},[MAP]={IsInPTSView='BoolProperty',InteractableItem='ObjectProperty',PTSTravelRequested='BoolProperty'},[TP]={Teleporter_Door_Object_REF='ObjectProperty',POIDataAsset='ObjectProperty',IsInUse='BoolProperty'},[DOOR]={TeleporterOwner='ObjectProperty',['Interaction Instigator']='ObjectProperty'}}
for c,f in pairs(fieldSpecs) do objects[path(c)]=meta(c,f) end
local cdo=actor(object('TP_CDO',{TP,'Engine.Actor'}),false);cdo.POIDataAsset=nil
objects['/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.Default__BP_Teleporter_C']=cdo
objects['/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.Default__BP_Teleporter_Door_C']=actor(object('DOOR_CDO',{DOOR,'Engine.Actor'}),false)
objects['/Script/Engine.Default__GameplayStatics']=gameplay;objects['/Script/Maine.Default__UserInterfaceStatics']=ui;objects['/Script/Maine.Default__SurvivalGameplayStatics']=maine
for _,en in ipairs({'ESpawnActorCollisionHandlingMethod','ESpawnActorScaleMethod','EComponentMobility'}) do
 local e=object('Enum');function e:ForEachName(fn) fn({ToString=function() return en=='EComponentMobility' and 'Movable' or en=='ESpawnActorScaleMethod' and 'MultiplyWithRoot' or 'AlwaysSpawn' end},1) end;objects['/Script/Engine.'..en]=e
end
function StaticFindObject(p)
 if not classReady and p==TP then return nil end
 local o=objects[p];if o then return o end
 for key,s in pairs(specs) do
  local c,m=key:match('^(.*)%.([^%.]+)$')
  if p==path(c)..':'..m then return meta(c..':'..m,s) end
 end
end
function FindAllOf(c)
 assert(thread)
 if c=='PlayerController' then return controllers elseif c=='MapWidget' then return {map} elseif c=='BP_Teleporter_C' then return sources end
 error('Unexpected class scan '..c)
end
function ExecuteInGameThread(fn) assert(not thread);thread=true;fn();thread=false end
function LoopAsync(ms,fn) assert(ms==250);timer=fn end
function RegisterKeyBind() error('Native travel must not bind a key') end
function RegisterHook() error('Native travel must not intercept or replace RPCs') end
local function pulse() timer() end
local function logged(s) for _,v in ipairs(logs) do if v:find(s,1,true) then return true end end;return false end
'''
cases={
 'successive departures follow current pawn after each native arrival': 'pulse();for _,position in ipairs({10000,25000,-3000}) do sources[1].IsInUse=true;local old=sources[1].transform.Translation.X;pawn.position=position;pulse();assert(sources[1].transform.Translation.X==old);sources[1].IsInUse=false;pulse();assert(sources[1].transform.Translation.X==position) end;assert(creates==1 and logged("SOURCE_BUSY") and logged("SOURCE_IDLE"))',
 'rejected native departure movement stops instead of reusing stale source': 'moveFail=true;pulse();assert(logged("GUARDED STOP") and logged("Portable departure move rejected") and map.InteractableItem==nil)',

 'door registry restores native hold UI without invoking travel': 'pulse();assert(creates==1 and map.InteractableItem==sources[1].Teleporter_Door_Object_REF and map.IsInPTSView and map.nativeButtonVisible and logged("NATIVE_HOLD_READY"));assert(sources[1].owner==pc and sources[1].Teleporter_Door_Object_REF["Interaction Instigator"]==pawn and sources[1].bOnlyRelevantToOwner and not sources[1].bAlwaysRelevant and sources[1].movementReplicates)',
 'stable hover does not repeatedly refresh/reset native hold': 'pulse();local n=refreshes;for i=1,12 do pulse() end;assert(refreshes==n and creates==1)',
 'locked destinations stay unavailable': 'locked=true;pulse();assert(not map.IsInPTSView and not map.nativeButtonVisible and not logged("NATIVE_HOLD_READY"))',
 'native CanPTSTravel restriction is respected': 'canTravel=false;pulse();assert(not map.IsInPTSView and not map.nativeButtonVisible)',
 'unregistered markers stay unavailable': 'emptyRegistry=true;pulse();assert(not map.IsInPTSView and not map.nativeButtonVisible)',
 'parent actor returned instead of native door is rejected': 'wrongRegistry=true;pulse();assert(not map.IsInPTSView and not map.nativeButtonVisible)',
 'terrain has no native travel prompt': 'terrain=true;pulse();assert(not map.IsInPTSView and not map.nativeButtonVisible)',
 'closed map restores original fields and does not destroy departure mid-animation': 'pulse();map.PTSTravelRequested=true;menu=false;pulse();assert(map.InteractableItem==nil and map.IsInPTSView==false and destroyed==0 and sources[1].lifespan==120)',
 'normal real-pod map interaction remains unchanged': 'map.InteractableItem=door;map.IsInPTSView=true;pulse();assert(map.InteractableItem==door and map.IsInPTSView and refreshes==0)',
 'two authoritative players get distinct owned native departures': 'controllers={pc,remote};pulse();assert(creates==2 and sources[1].owner==pc and sources[2].owner==remote and sources[1].Teleporter_Door_Object_REF["Interaction Instigator"]==pawn and sources[2].Teleporter_Door_Object_REF["Interaction Instigator"]==remotePawn);assert(map.InteractableItem==sources[1].Teleporter_Door_Object_REF)',
 'client never spawns; uses own replicated source': 'host=false;local other=departure(remote);local own=departure(pc);pulse();assert(creates==0 and moves==0 and map.InteractableItem==own.Teleporter_Door_Object_REF and map.IsInPTSView)',
 'client replica is hidden and noncolliding even with map closed': 'host=false;menu=false;local own=departure(pc);pulse();assert(creates==0 and own.hidden and own.collision==false and own.Teleporter_Door_Object_REF.hidden and own.Teleporter_Door_Object_REF.collision==false and map.InteractableItem==nil)',
 'client ignores stale source for previous pawn after respawn': 'host=false;local old=departure(pc);old.Instigator=remotePawn;local own=departure(pc);pulse();assert(creates==0 and map.InteractableItem==own.Teleporter_Door_Object_REF)',
 'client cannot borrow another players source': 'host=false;departure(remote);pulse();assert(creates==0 and map.InteractableItem==nil and not map.IsInPTSView and logged("WAIT: portable"))',
 'temporary native source does not move while in use': 'pulse();sources[1].IsInUse=true;local n=moves;pulse();assert(moves==n)',
 'native class loading waits and retries': 'classReady=false;pulse();assert(creates==0 and not logged("GUARDED STOP"));classReady=true;pulse();assert(creates==1 and map.IsInPTSView)',
 'schema mismatch refuses field mutation': 'metadataBad=true;pulse();assert(logged("GUARDED STOP") and map.InteractableItem==nil)',
 'source setup failure destroys only portable objects': 'spawnFail=true;pulse();assert(logged("GUARDED STOP") and destroyed==1 and sources[1].dead and map.InteractableItem==nil)',
 'lock change hides native prompt once': 'pulse();local n=refreshes;locked=true;pulse();assert(refreshes==n+1 and not map.IsInPTSView and not map.nativeButtonVisible);pulse();assert(refreshes==n+1)',
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
print(len(cases),'native map Lua fixture groups passed; Windows travel/replication not proven')
