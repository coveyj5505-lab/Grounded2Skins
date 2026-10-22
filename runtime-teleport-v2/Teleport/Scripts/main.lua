-- Native outpost travel with host-side RPC completion; no cooked Blueprint overrides.
local TELEPORTER='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local CONTROLLER='/Game/Blueprints/Player/BP_SurvivalPlayerController.BP_SurvivalPlayerController_C'
local RPC=CONTROLLER..':ServerRequestPTSTravel'
local enum='ByteProperty|EnumProperty'
local schemas={
 [CONTROLLER..'.ServerRequestPTSTravel']={RequestCancelled='BoolProperty',TeleporterDeparture='ObjectProperty',TeleporterDestinationOverride='ObjectProperty'},
 ['Engine.Controller.IsLocalController']={ReturnValue='BoolProperty'},
 ['Engine.Controller.K2_GetPawn']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Engine.Actor.GetTransform']={ReturnValue='StructProperty'},
 ['Engine.Actor.SetActorHiddenInGame']={bNewHidden='BoolProperty'},
 ['Engine.Actor.SetActorEnableCollision']={bNewActorEnableCollision='BoolProperty'},
 ['Engine.Actor.SetLifeSpan']={InLifespan='FloatProperty'},
 ['Engine.Actor.K2_DestroyActor']={},
 ['Engine.GameplayStatics.BeginDeferredActorSpawnFromClass']={WorldContextObject='ObjectProperty',ActorClass='ClassProperty',SpawnTransform='StructProperty',CollisionHandlingOverride=enum,Owner='ObjectProperty',TransformScaleMethod=enum,ReturnValue='ObjectProperty'},
 ['Engine.GameplayStatics.FinishSpawningActor']={Actor='ObjectProperty',SpawnTransform='StructProperty',TransformScaleMethod=enum,ReturnValue='ObjectProperty'},
 ['Maine.UserInterfaceStatics.GetWidgetManager']={WorldContextObject='ObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.WidgetManager.IsInGameMenuActive']={ReturnValue='BoolProperty'},
 ['Maine.WidgetManager.HideInGameMenu']={},
 ['UMG.Widget.IsVisible']={ReturnValue='BoolProperty'},
 ['UMG.Widget.GetParent']={ReturnValue='ObjectProperty'},
 ['Maine.MapPanelWidget.GetEntryUnderCursor']={ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameplayStatics.GetSurvivalGameState']={WorldContextObject='ObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameState.GetRegisteredPTSTravel']={POIData='ObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameState.IsPTSTravelLocked']={POIData='ObjectProperty',ReturnValue='BoolProperty'},
 [TELEPORTER..'.SetTeleportDoorRef']={CallFunc_IsValid_ReturnValue='BoolProperty',K2Node_DynamicCast_AsBP_Teleporter_Door='ObjectProperty',K2Node_DynamicCast_bSuccess='BoolProperty'},
 [TELEPORTER..'.OnTeleportRequested']={RequestCancelled='BoolProperty',OverrideDestination='ObjectProperty'},
 [DOOR..'.SetAndPrintInteractionInstigator']={InteractionInstigator='ObjectProperty',CallFunc_GetDisplayName_ReturnValue='StrProperty'},
}
local api=require('teleport_guard').new('Teleport UE57 V2',schemas,{
 MapPanel={owner='Maine.MapWidget',type='ObjectProperty'},
 POIData={owner='Maine.MapPOIWidget',type='ObjectProperty'},
 Teleporter_Door_Object_REF={owner=TELEPORTER,type='ObjectProperty'},
 POIDataAsset={owner=TELEPORTER,type='ObjectProperty'},
})
local busy=false;local lastRequest=0
local function enumValue(name,leaf)
 local e=StaticFindObject('/Script/Engine.'..name);assert(api.valid(e),'Missing enum '..name)
 local found
 e:ForEachName(function(n,value) if n:ToString():match('([^:]+)$')==leaf then found=value end end)
 assert(type(found)=='number','Missing enum value '..name..'.'..leaf);return found
end
local function visibleHierarchy(widget)
 for _=1,32 do
  if not api.valid(widget) then return true end
  if api.call(widget,'UMG.Widget','IsVisible')~=true then return false end
  widget=api.call(widget,'UMG.Widget','GetParent')
 end
 return false -- malformed/cyclic hierarchy; never treat as an open map
end
local function hideTemporary(actor)
 api.call(actor,'Engine.Actor','SetActorHiddenInGame',true)
 api.call(actor,'Engine.Actor','SetActorEnableCollision',false)
 api.call(actor,'Engine.Actor','SetLifeSpan',30)
end
local function performTravel(controller,destination,manager)
 local pawn=api.call(controller,'Engine.Controller','K2_GetPawn')
 if not api.isa(pawn,'Maine.SurvivalPlayerCharacter') or api.call(pawn,'Engine.Actor','HasAuthority')~=true then api.log('WAIT: only the authoritative server executes travel');return end
 assert(api.isa(destination,TELEPORTER),'Destination is not a native teleporter')
 local poi=api.field(destination,'POIDataAsset');assert(api.valid(poi),'Destination POI unavailable')
 local state=api.call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','GetSurvivalGameState',pawn)
 assert(api.valid(state),'Gameplay state unavailable')
 assert(api.call(state,'Maine.SurvivalGameState','IsPTSTravelLocked',poi)==false,'Destination is locked on server')
 local registered=api.call(state,'Maine.SurvivalGameState','GetRegisteredPTSTravel',poi)
 assert(api.valid(registered) and api.full(registered)==api.full(destination),'Destination is not the registered server outpost')
 local class=StaticFindObject(TELEPORTER);assert(api.valid(class),'Current native BP_Teleporter class not loaded')
 local transform=api.call(pawn,'Engine.Actor','GetTransform')
 local collision=enumValue('ESpawnActorCollisionHandlingMethod','AlwaysSpawn')
 local scale=enumValue('ESpawnActorScaleMethod','MultiplyWithRoot')
 local gameplay=StaticFindObject('/Script/Engine.Default__GameplayStatics')
 -- Validate every mutation signature before any actor is created.
 for _,method in ipairs({'SetActorHiddenInGame','SetActorEnableCollision','SetLifeSpan','K2_DestroyActor'}) do api.check(pawn,'Engine.Actor',method) end
 api.check(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass')
 api.check(gameplay,'Engine.GameplayStatics','FinishSpawningActor')
 if api.valid(manager) then api.check(manager,'Maine.WidgetManager','HideInGameMenu') end
 local sourceCDO=StaticFindObject('/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.Default__BP_Teleporter_C')
 local doorCDO=StaticFindObject('/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.Default__BP_Teleporter_Door_C')
 api.check(sourceCDO,TELEPORTER,'SetTeleportDoorRef');api.check(sourceCDO,TELEPORTER,'OnTeleportRequested')
 api.check(doorCDO,DOOR,'SetAndPrintInteractionInstigator')
 api.field(sourceCDO,'Teleporter_Door_Object_REF') -- metadata only; nil is fine
 local source,door
 local ok,why=pcall(function()
  source=api.call(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass',pawn,class,transform,collision,pawn,scale)
  assert(api.isa(source,TELEPORTER),'Deferred native teleporter creation failed')
  hideTemporary(source)
  local finished=api.call(gameplay,'Engine.GameplayStatics','FinishSpawningActor',source,transform,scale)
  assert(api.valid(finished) and api.full(finished)==api.full(source),'Finish native teleporter failed')
  hideTemporary(source)
  api.call(source,TELEPORTER,'SetTeleportDoorRef')
  door=api.field(source,'Teleporter_Door_Object_REF');assert(api.isa(door,DOOR),'Native departure door unavailable')
  hideTemporary(door)
  api.call(door,DOOR,'SetAndPrintInteractionInstigator',pawn)
  if api.valid(manager) then api.call(manager,'Maine.WidgetManager','HideInGameMenu') end
  api.call(source,TELEPORTER,'OnTeleportRequested',false,destination)
  api.log('REQUESTED native server outpost travel; destination='..api.full(destination)..'; source='..api.full(source)..'; verify arrival in game; no forced coordinates or old Blueprint overrides')
 end)
 if not ok then
  for _,o in pairs({door=door,source=source}) do if api.valid(o) then pcall(api.call,o,'Engine.Actor','K2_DestroyActor') end end
  error(why)
 end
end
local function action()
 local controller,pawn
 for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
  if i>16 then break end
  if api.isa(pc,'Engine.Controller') and api.call(pc,'Engine.Controller','IsLocalController') then controller=pc;break end
 end
 if not api.valid(controller) then api.log('WAIT: no local controller');return end
 pawn=api.call(controller,'Engine.Controller','K2_GetPawn')
 if not api.isa(pawn,'Maine.SurvivalPlayerCharacter') then api.log('WAIT: load a gameplay character');return end
 local ui=StaticFindObject('/Script/Maine.Default__UserInterfaceStatics')
 local manager=api.call(ui,'Maine.UserInterfaceStatics','GetWidgetManager',pawn)
 if not api.valid(manager) or api.call(manager,'Maine.WidgetManager','IsInGameMenuActive')~=true then api.log('WAIT: open the map and hover an unlocked outpost, then press F8');return end
 local map
 for i,w in ipairs(FindAllOf('MapWidget') or {}) do
  if i>32 then break end
  if api.isa(w,'Maine.MapWidget') and not api.full(w):find('Default__',1,true) and visibleHierarchy(w) then
   assert(map==nil,'More than one visible map; no destination guess');map=w
  end
 end
 if not api.valid(map) then api.log('WAIT: no visible map page');return end
 local panel=api.field(map,'MapPanel');assert(api.isa(panel,'Maine.MapPanelWidget'),'MapPanel unavailable')
 local entry=api.call(panel,'Maine.MapPanelWidget','GetEntryUnderCursor')
 if not api.isa(entry,'Maine.MapPOIWidget') then api.log('WAIT: hover an outpost map marker; terrain/waypoints are not destinations');return end
 local poi=api.field(entry,'POIData');assert(api.valid(poi),'POI data unavailable')
 local state=api.call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','GetSurvivalGameState',pawn)
 assert(api.valid(state),'Gameplay state unavailable')
 if api.call(state,'Maine.SurvivalGameState','IsPTSTravelLocked',poi)~=false then api.log('LOCKED: native outpost travel is locked; no unlock/save changes');return end
 local destination=api.call(state,'Maine.SurvivalGameState','GetRegisteredPTSTravel',poi)
 if not api.isa(destination,TELEPORTER) then api.log('WAIT: marker has no registered native outpost teleporter');return end
 if api.call(pawn,'Engine.Actor','HasAuthority') then
  performTravel(controller,destination,manager)
 else
  api.call(controller,CONTROLLER,'ServerRequestPTSTravel',false,nil,destination)
  api.call(manager,'Maine.WidgetManager','HideInGameMenu')
  api.log('CLIENT_SENT native travel RPC; host must run this same Teleport Lua mod. Arrival is not confirmed by sending a request.')
 end
end
RegisterKeyBind(Key.F8,function()
 if busy then return end
 local now=os.time();if now-lastRequest<2 then return end
 lastRequest=now;busy=true
 local queued,why=pcall(function()
  ExecuteInGameThread(function()
   local ok,err=pcall(action);busy=false
   if not ok then api.log('GUARDED STOP '..tostring(err)) end
  end)
 end)
 if not queued then busy=false;api.log('DISPATCH STOP '..tostring(why)) end
end)
-- Installed UE4SS83330635 script hooks run AFTER the Blueprint event. The
-- stock RPC sees a missing departure and does no travel; this posthook supplies
-- the same native temporary departure used by the old mod, on the server only.
-- Resolve live metadata on the game thread and perform hook registration from
-- LoopAsync, keeping registration outside the native travel callback itself.
local registrationReady,registered,checking=false,false,false
local serverLast={}
local function afterTravelRPC(context,cancelled,departure,destination)
 local ok,why=pcall(function()
  local controller=api.unwrap(context)
  local cancel=api.unwrap(cancelled)
  local source=api.unwrap(departure)
  local target=api.unwrap(destination)
  if cancel~=false or api.valid(source) or not api.valid(controller) or not api.valid(target) then return end
  ExecuteInGameThread(function()
   local good,err=pcall(function()
    if not api.isa(controller,CONTROLLER) or api.call(controller,'Engine.Actor','HasAuthority')~=true then return end
    local key=api.full(controller);local now=os.time()
    if now-(serverLast[key] or 0)<2 then return end
    for k,t in pairs(serverLast) do if now-t>30 then serverLast[k]=nil end end
    serverLast[key]=now
    performTravel(controller,target,nil)
   end)
   if not good then api.log('SERVER_GUARDED_STOP '..tostring(err)) end
  end)
 end)
 if not ok then api.log('RPC_HOOK_STOP '..tostring(why)) end
end
LoopAsync(1000,function()
 if registered then return false end
 if registrationReady then
  local ok,pre,post=pcall(RegisterHook,RPC,afterTravelRPC)
  if ok then registered=true;api.log('SERVER_RPC_HOOK_READY ids='..tostring(pre)..','..tostring(post)..'; script posthook, current Blueprint only; multiplayer travel still needs Windows testing')
  else registrationReady=false;api.once('hook:'..tostring(pre),'RPC_HOOK_WAIT '..tostring(pre)) end
  return false
 end
 if checking then return false end
 checking=true
 local queued,why=pcall(function()
  ExecuteInGameThread(function()
   local ok,err=pcall(function()
    for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
     if i>16 then break end
     if api.isa(pc,CONTROLLER) and api.call(pc,'Engine.Actor','HasAuthority') then
      local pawn=api.call(pc,'Engine.Controller','K2_GetPawn')
      if api.isa(pawn,'Maine.SurvivalPlayerCharacter') then api.check(pc,CONTROLLER,'ServerRequestPTSTravel');registrationReady=true;break end
     end
    end
   end)
   checking=false
   if not ok then api.once('schema:'..tostring(err),'RPC_SCHEMA_WAIT '..tostring(err)) end
  end)
 end)
 if not queued then checking=false;api.once('dispatch:'..tostring(why),'RPC_DISPATCH_WAIT '..tostring(why)) end
 return false
end)
api.log('READY V2: install the same Lua mod on host and clients; no Teleport Paks. Open map, hover an unlocked outpost and press F8. Host executes native outpost travel; client uses the existing reliable server RPC plus host posthook. No startup actor creation; multiplayer NOT WINDOWS VALIDATED.')
