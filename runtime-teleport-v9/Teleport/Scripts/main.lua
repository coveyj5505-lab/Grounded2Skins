-- On-demand native map travel. No startup/follower actors or player position writes.
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local MAP='/Game/UI/Map/UI_Map.UI_Map_C'
local CONTROLLER='/Game/Blueprints/Player/BP_SurvivalPlayerController.BP_SurvivalPlayerController_C'
local enum='ByteProperty|EnumProperty'
local schemas={
 [CONTROLLER..'.ServerRequestPTSTravel']={RequestCancelled='BoolProperty',TeleporterDeparture='ObjectProperty',TeleporterDestinationOverride='ObjectProperty'},
 [TP..'.OnTeleportRequested']={RequestCancelled='BoolProperty',OverrideDestination='ObjectProperty'},
 ['Maine.WidgetManager.HideInGameMenu']={},
 ['Engine.KismetSystemLibrary.IsServer']={WorldContextObject='ObjectProperty',ReturnValue='BoolProperty'},
 ['Engine.Actor.SetReplicates']={bInReplicates='BoolProperty'},
 ['Engine.Actor.SetReplicateMovement']={bInReplicateMovement='BoolProperty'},
 ['Engine.Controller.IsLocalController']={ReturnValue='BoolProperty'},
 ['Engine.Controller.K2_GetPawn']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Engine.Actor.K2_GetComponentsByClass']={ComponentClass='ClassProperty',ReturnValue='ArrayProperty'},
 ['Engine.SceneComponent.SetVisibility']={bNewVisibility='BoolProperty',bPropagateToChildren='BoolProperty'},
 ['Engine.PrimitiveComponent.SetRenderInMainPass']={bValue='BoolProperty'},
 ['Engine.PrimitiveComponent.SetRenderInDepthPass']={bValue='BoolProperty'},
 ['Engine.PrimitiveComponent.SetCastShadow']={NewCastShadow='BoolProperty'},
 ['Engine.Actor.GetTransform']={ReturnValue='StructProperty'},
 ['Engine.Actor.SetActorHiddenInGame']={bNewHidden='BoolProperty'},
 ['Engine.Actor.SetActorEnableCollision']={bNewActorEnableCollision='BoolProperty'},
 ['Engine.Actor.SetLifeSpan']={InLifespan='FloatProperty'},
 ['Engine.Actor.K2_DestroyActor']={},
 ['Engine.GameplayStatics.BeginDeferredActorSpawnFromClass']={WorldContextObject='ObjectProperty',ActorClass='ClassProperty',SpawnTransform='StructProperty',CollisionHandlingOverride=enum,Owner='ObjectProperty',TransformScaleMethod=enum,ReturnValue='ObjectProperty'},
 ['Engine.GameplayStatics.FinishSpawningActor']={Actor='ObjectProperty',SpawnTransform='StructProperty',TransformScaleMethod=enum,ReturnValue='ObjectProperty'},
 ['Maine.UserInterfaceStatics.GetWidgetManager']={WorldContextObject='ObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.WidgetManager.IsInGameMenuActive']={ReturnValue='BoolProperty'},
 ['UMG.Widget.IsVisible']={ReturnValue='BoolProperty'},
 ['UMG.Widget.GetParent']={ReturnValue='ObjectProperty'},
 ['Maine.MapPanelWidget.GetEntryUnderCursor']={ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameplayStatics.GetSurvivalGameState']={WorldContextObject='ObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameState.GetRegisteredPTSTravel']={POIData='ObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameState.IsPTSTravelLocked']={POIData='ObjectProperty',ReturnValue='BoolProperty'},
 ['Maine.SurvivalGameState.CanPTSTravel']={POIData='ObjectProperty',ReturnValue='BoolProperty'},
 [MAP..'.RefreshPTSButton']={CallFunc_GetSurvivalGameState_ReturnValue='ObjectProperty',CallFunc_GetSurvivalGameState_ReturnValue_1='ObjectProperty',CallFunc_GetEntryUnderCursor_ReturnValue='ObjectProperty',K2Node_DynamicCast_AsMap_POIWidget='ObjectProperty',K2Node_DynamicCast_bSuccess='BoolProperty',CallFunc_GetRegisteredPTSTravel_ReturnValue='ObjectProperty',CallFunc_IsPTSTravelLocked_ReturnValue='BoolProperty',CallFunc_NotEqual_ObjectObject_ReturnValue='BoolProperty',K2Node_DynamicCast_AsBP_Teleporter_Door='ObjectProperty',K2Node_DynamicCast_bSuccess_1='BoolProperty',CallFunc_IsDestinationPTSInUse_IsInUse='BoolProperty',CallFunc_Not_PreBool_ReturnValue='BoolProperty'},
 [TP..'.SetTeleportDoorRef']={CallFunc_IsValid_ReturnValue='BoolProperty',K2Node_DynamicCast_AsBP_Teleporter_Door='ObjectProperty',K2Node_DynamicCast_bSuccess='BoolProperty'},
}
local api=require('teleport_native_guard').new('Rivet-Teleport V9',schemas,{
 MapPanel={owner='Maine.MapWidget',type='ObjectProperty'},
 POIData={owner='Maine.MapPOIWidget',type='ObjectProperty'},
 IsInPTSView={owner=MAP,type='BoolProperty'},
 InteractableItem={owner=MAP,type='ObjectProperty'},
 PTSTravelRequested={owner=MAP,type='BoolProperty'},
 Teleporter_Door_Object_REF={owner=TP,type='ObjectProperty'},
 TeleporterOwner={owner=DOOR,type='ObjectProperty'},
 POIDataAsset={owner=TP,type='ObjectProperty'},
 IsInUse={owner=TP,type='BoolProperty'},
 Instigator={owner='Engine.Actor',type='ObjectProperty'},
 bAlwaysRelevant={owner='Engine.Actor',type='BoolProperty'},
 bOnlyRelevantToOwner={owner='Engine.Actor',type='BoolProperty'},
 ['Interaction Instigator']={owner=DOOR,type='ObjectProperty'},
 PersistenceComponent={owner='Maine.Switch',type='ObjectProperty'},
 bNeverSpawnAsDynamicActor={owner='Maine.PersistenceComponent',type='BoolProperty'},
 bShouldEditModeSave={owner='Maine.PersistenceComponent',type='BoolProperty'},
})
local function call(o,c,m,...) return api.call(o,c,m,...) end
local views,requests,active={},{},{}
local hooksReady=false;local baseHooksReady=false;local bases
local ticking=false
local function enumValue(name,leaf,namespace)
 local e=StaticFindObject('/Script/'..(namespace or 'Engine')..'.'..name)
 assert(api.valid(e),'Missing enum '..name)
 local value
 e:ForEachName(function(n,v) if n:ToString():match('([^:]+)$')==leaf then value=v end end)
 assert(type(value)=='number','Missing enum member '..leaf)
 return value
end
local function stateFor(pawn)
 return call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','GetSurvivalGameState',pawn)
end
local function serverWorld(context)
 return call(StaticFindObject('/Script/Engine.Default__KismetSystemLibrary'),'Engine.KismetSystemLibrary','IsServer',context)==true
end
local function destinationFor(state,poi)
 if not api.isa(state,'Maine.SurvivalGameState') or not api.valid(poi) then return end
 if call(state,'Maine.SurvivalGameState','IsPTSTravelLocked',poi)~=false or call(state,'Maine.SurvivalGameState','CanPTSTravel',poi)~=true then return end
 local door=call(state,'Maine.SurvivalGameState','GetRegisteredPTSTravel',poi)
 if not api.isa(door,DOOR) then return end
 local target=api.field(door,'TeleporterOwner')
 if not api.isa(target,TP) or api.field(target,'IsInUse')~=false then return end
 return target
end
local function suppress(actor)
 call(actor,'Engine.Actor','SetActorHiddenInGame',true)
 call(actor,'Engine.Actor','SetActorEnableCollision',false)
 local cls=StaticFindObject('/Script/Engine.SceneComponent')
 assert(api.valid(cls),'Missing scene component class')
 local parts=call(actor,'Engine.Actor','K2_GetComponentsByClass',cls)
 local count=0
 local function hide(_,wrapped)
  count=count+1;assert(count<=256,'Temporary component limit exceeded')
  local c=api.unwrap(wrapped)
  if api.isa(c,'Engine.SceneComponent') then call(c,'Engine.SceneComponent','SetVisibility',false,true) end
  if api.isa(c,'Engine.PrimitiveComponent') then
   call(c,'Engine.PrimitiveComponent','SetRenderInMainPass',false)
   call(c,'Engine.PrimitiveComponent','SetRenderInDepthPass',false)
   call(c,'Engine.PrimitiveComponent','SetCastShadow',false)
  end
 end
 if type(parts)=='table' and type(parts.ForEach)~='function' then
  for i,c in ipairs(parts) do hide(i,c) end
 else
  assert(parts and type(parts.ForEach)=='function','Missing component array')
  parts:ForEach(hide)
 end
end
bases=require('base_teleport').new({enumValue=enumValue,suppress=suppress})
local function performTravel(pc,target)
 if not api.isa(pc,CONTROLLER) then return end
 local pawn=call(pc,'Engine.Controller','K2_GetPawn')
 if not api.isa(pawn,'Maine.SurvivalPlayerCharacter') or not serverWorld(pawn) or call(pawn,'Engine.Actor','HasAuthority')~=true then return end
 if not api.isa(target,TP) then return end
 if api.field(target,'IsInUse')~=false then return end
 -- Revalidate the remote request against the SERVER registry. Never trust a
 -- client-provided actor merely because it has the teleporter class.
 local poi=api.field(target,'POIDataAsset')
 if not bases.isTarget(target) and api.full(destinationFor(stateFor(pawn),poi))~=api.full(target) then
  api.log('REJECTED: destination is not a registered outpost or a live completed Rivet base');return
 end
 local key=api.full(pc);local now=os.time()
 for k,t in pairs(requests) do if now-t>60 then requests[k]=nil;active[k]=nil end end
 if now-(requests[key] or -100)<2 then return end
 local previous=active[key]
 if previous and api.valid(previous.source) and api.field(previous.source,'IsInUse')==true then return end
 local class=StaticFindObject(TP)
 if not api.valid(class) then api.log('WAIT: native teleporter class has not loaded');return end
 local cdo=StaticFindObject('/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.Default__BP_Teleporter_C')
 local dcdo=StaticFindObject('/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.Default__BP_Teleporter_Door_C')
 assert(not api.valid(api.field(cdo,'POIDataAsset')),'Temporary source must not claim an outpost')
 api.check(cdo,TP,'SetTeleportDoorRef');api.check(cdo,TP,'OnTeleportRequested')
 api.field(dcdo,'Interaction Instigator')
 local gameplay=StaticFindObject('/Script/Engine.Default__GameplayStatics')
 api.check(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass')
 api.check(gameplay,'Engine.GameplayStatics','FinishSpawningActor')
 for _,m in ipairs({'SetActorHiddenInGame','SetActorEnableCollision','SetLifeSpan','K2_DestroyActor','K2_GetComponentsByClass'}) do api.check(pawn,'Engine.Actor',m) end
 local transform=call(pawn,'Engine.Actor','GetTransform')
 local collision=enumValue('ESpawnActorCollisionHandlingMethod','AlwaysSpawn')
 local scale=enumValue('ESpawnActorScaleMethod','MultiplyWithRoot')
 requests[key]=now
 local source,door,started
 local ok,why=pcall(function()
  source=call(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass',pawn,class,transform,collision,pc,scale)
  assert(api.isa(source,TP),'Temporary source creation failed')
  -- Bound lifetime even if later initialization fails. No follow or movement
  -- replication is needed: the source is created at the request position.
  call(source,'Engine.Actor','SetLifeSpan',30)
  api.writeObject(source,'Instigator',pawn,'Engine.Pawn');suppress(source)
  local finished=call(gameplay,'Engine.GameplayStatics','FinishSpawningActor',source,transform,scale)
  assert(api.full(finished)==api.full(source),'Temporary source finish failed')
  call(source,'Engine.Actor','SetReplicates',true);call(source,'Engine.Actor','SetReplicateMovement',true)
  api.write(source,'bAlwaysRelevant',true);api.write(source,'bOnlyRelevantToOwner',false)
  bases.guardTemporary(source)
  call(source,'Engine.Actor','SetLifeSpan',30);suppress(source)
  call(source,TP,'SetTeleportDoorRef')
  door=api.field(source,'Teleporter_Door_Object_REF')
  assert(api.isa(door,DOOR),'Temporary departure door unavailable')
  assert(api.full(api.field(door,'TeleporterOwner'))==api.full(source),'Temporary door owner mismatch')
  call(door,'Engine.Actor','SetLifeSpan',30)
  call(door,'Engine.Actor','SetReplicates',true)
  api.write(door,'bAlwaysRelevant',true);api.write(door,'bOnlyRelevantToOwner',false)
  bases.guardTemporary(door)
  local persistence=api.field(door,'PersistenceComponent')
  assert(api.isa(persistence,'Maine.PersistenceComponent'),'Temporary door persistence unavailable')
  api.write(persistence,'bNeverSpawnAsDynamicActor',true)
  api.write(persistence,'bShouldEditModeSave',false)
  api.writeObject(door,'Interaction Instigator',pawn,'Maine.SurvivalPlayerCharacter')
  suppress(door)
  assert(not api.valid(api.field(source,'POIDataAsset')),'Temporary source unexpectedly registered as an outpost')
  active[key]={source=source}
  -- Once the native event starts, do not destroy its actors on a later error.
  -- Both have a fixed expiry; no periodic lifespan renewal or pawn tracking.
  started=true
  call(source,TP,'OnTeleportRequested',false,target)
 end)
 if not ok then
  if not started then
   -- Construction can create the child before FinishSpawningActor fails.
   -- Recover only a child whose TeleporterOwner identifies our new source.
   if not api.valid(door) and api.valid(source) then
    pcall(function()
     local child=api.field(source,'Teleporter_Door_Object_REF')
     if api.isa(child,DOOR) and api.full(api.field(child,'TeleporterOwner'))==api.full(source) then door=child end
    end)
   end
   for _,o in pairs({source=source,door=door}) do if api.valid(o) then pcall(call,o,'Engine.Actor','K2_DestroyActor') end end
   active[key]=nil
  end
  error(why)
 end
 -- Native startup can restore actor rendering; suppress once more without a
 -- follower loop. Delayed animation/replica visibility still needs game tests.
 for _,o in ipairs({source,door}) do
  local hidden,err=pcall(suppress,o)
  if not hidden then api.log('HIDE_WARNING '..tostring(err)) end
 end
 api.log('ON_DEMAND_REQUESTED pc='..key..'; destination='..api.full(target)..'; fixed 30s source/door; no follower. Arrival is not confirmed.')
end
local function visible(widget)
 for _=1,32 do
  if not api.valid(widget) then return true end
  if not call(widget,'UMG.Widget','IsVisible') then return false end
  widget=call(widget,'UMG.Widget','GetParent')
 end
 return false
end
local function restore(record)
 -- We never supply InteractableItem. If a real pod takes over, leave its view
 -- alone rather than overwriting the native interaction's new context.
 if api.valid(record.map) and not api.valid(api.field(record.map,'InteractableItem')) then
  api.write(record.map,'IsInPTSView',record.originalView)
 end
end
local function localPlayer()
 local found,pawn
 for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
  if i>16 then break end
  if api.isa(pc,CONTROLLER) and call(pc,'Engine.Controller','IsLocalController') then
   if found then return end -- ambiguous split-screen; do not borrow a map
   found=pc;pawn=call(pc,'Engine.Controller','K2_GetPawn')
  end
 end
 if api.isa(pawn,'Maine.SurvivalPlayerCharacter') then return found,pawn end
end
local function managerFor(pawn)
 return call(StaticFindObject('/Script/Maine.Default__UserInterfaceStatics'),'Maine.UserInterfaceStatics','GetWidgetManager',pawn)
end
local function targetUnderCursor(map,state)
 local panel=api.field(map,'MapPanel')
 if not api.isa(panel,'Maine.MapPanelWidget') then return end
 local entry=call(panel,'Maine.MapPanelWidget','GetEntryUnderCursor')
 if not api.isa(entry,'Maine.MapPOIWidget') then return end
 return destinationFor(state,api.field(entry,'POIData'))
end
local function afterMapTravel(context)
 local map=api.unwrap(context)
 ExecuteInGameThread(function()
  local ok,why=pcall(function()
   -- The stock function does nothing without a real InteractableItem. Extend
   -- only that route AFTER native hold completion; never double a real-pod trip.
   local record=views[api.full(map)]
   if not hooksReady or not record or not api.valid(map) or api.valid(api.field(map,'InteractableItem')) or not visible(map) then return end
   local pc,pawn=localPlayer();if not pc then return end
   local manager=managerFor(pawn)
   if not api.valid(manager) or not call(manager,'Maine.WidgetManager','IsInGameMenuActive') then return end
   if api.field(map,'IsInPTSView')~=true then return end
   local target=targetUnderCursor(map,stateFor(pawn));if not target then return end
   call(manager,'Maine.WidgetManager','HideInGameMenu')
   if serverWorld(pawn) then
    performTravel(pc,target)
   else
    call(pc,CONTROLLER,'ServerRequestPTSTravel',false,nil,target)
    api.log('CLIENT_REQUEST_SENT: host must run V8; arrival is not confirmed')
   end
  end)
  if not ok then api.log('MAP_REQUEST_STOP '..tostring(why)) end
 end)
end
local function afterTravelRPC(context,cancelled,departure,destination)
 local pc=api.unwrap(context);local cancel=api.unwrap(cancelled)
 local source=api.unwrap(departure);local target=api.unwrap(destination)
 if cancel~=false or api.valid(source) or not api.valid(target) then return end
 ExecuteInGameThread(function()
  local ok,why=pcall(performTravel,pc,target)
  if not ok then api.log('SERVER_REQUEST_STOP '..tostring(why)) end
 end)
end
local function afterBaseTravel(context)
 local map=api.unwrap(context)
 ExecuteInGameThread(function()
  local ok,why=pcall(function()
   if not baseHooksReady or not api.isa(map,MAP) or not visible(map) then return end
   local pc,pawn=localPlayer();if not pc then return end
   local manager=managerFor(pawn)
   if not api.valid(manager) or not call(manager,'Maine.WidgetManager','IsInGameMenuActive') then return end
   local target=bases.targetOnMap(map)
   if not api.valid(target) or api.field(target,'IsInUse')~=false then return end
   call(manager,'Maine.WidgetManager','HideInGameMenu')
   if serverWorld(pawn) then performTravel(pc,target)
   else call(pc,CONTROLLER,'ServerRequestPTSTravel',false,nil,target);api.log('CLIENT_BASE_REQUEST_SENT; host acceptance/arrival not confirmed') end
  end)
  if not ok then api.log('BASE_REQUEST_STOP '..tostring(why)) end
 end)
end
local function afterBaseButton(context)
 local map=api.unwrap(context)
 ExecuteInGameThread(function()
  if baseHooksReady then
   local ok,why=pcall(bases.refreshButton,map)
   if not ok then api.once('base-button:'..tostring(why),'BASE_BUTTON_STOP '..tostring(why)) end
  end
 end)
end
local hookState={}
local hookMetadata={}
local function registerHooks()
 -- UE4SS Blueprint hooks are posthooks in the supported build. Registration
 -- stays outside ExecuteInGameThread and outside the callbacks themselves.
 for _,item in ipairs({{MAP..':PTSTravel',afterMapTravel},{CONTROLLER..':ServerRequestPTSTravel',afterTravelRPC},{MAP..':UGCTeleport',afterBaseTravel},{MAP..':RefreshTeleportButton',afterBaseButton}}) do
  if hookMetadata[item[1]] and not hookState[item[1]] then
   local callback=item[2]
   local ok,pre,post=pcall(RegisterHook,item[1],function(...)
    local good,why=pcall(callback,...)
    if not good then api.log('HOOK_CALLBACK_STOP '..tostring(why)) end
   end)
   if ok and type(pre)=='number' and type(post)=='number' then
    hookState[item[1]]=true;api.log('HOOK_READY '..item[1])
   else
    api.once('hook:'..item[1]..':'..tostring(pre),'HOOK_WAIT '..item[1]..' '..tostring(pre))
   end
  end
 end
 hooksReady=hookState[MAP..':PTSTravel'] and hookState[CONTROLLER..':ServerRequestPTSTravel'] or false
 baseHooksReady=hooksReady and hookState[MAP..':UGCTeleport'] and hookState[MAP..':RefreshTeleportButton'] or false
end
local function tick()
 local baseOK,baseWhy=pcall(bases.tick)
 if not baseOK then api.once('base-lifecycle:'..tostring(baseWhy),'BASE_LIFECYCLE_STOP '..tostring(baseWhy)) end
 -- A server must install its RPC extension even when it has never opened its
 -- own map (and even when only a remote player's controller is present).
 for i,controller in ipairs(FindAllOf('PlayerController') or {}) do
  if i>16 then break end
  if api.isa(controller,CONTROLLER) then
   api.check(controller,CONTROLLER,'ServerRequestPTSTravel')
   hookMetadata[CONTROLLER..':ServerRequestPTSTravel']=true;break
  end
 end
 local pc,pawn=localPlayer()
 for _,record in pairs(views) do record.seen=false end
 if pc then
  local manager=managerFor(pawn)
  if api.valid(manager) and call(manager,'Maine.WidgetManager','IsInGameMenuActive') then
   local maps={}
   for i,map in ipairs(FindAllOf('MapWidget') or {}) do
    if i>32 then break end
    if api.isa(map,MAP) and not api.full(map):find('Default__',1,true) and visible(map) then maps[#maps+1]=map end
   end
   -- A single visible map is required. Do not bind another player's widget.
   if #maps==1 then
    local map=maps[1]
    if not api.valid(api.field(map,'InteractableItem')) then
     api.check(pc,CONTROLLER,'ServerRequestPTSTravel')
     api.check(map,MAP,'RefreshPTSButton')
     for _,method in ipairs({'PTSTravel','UGCTeleport','RefreshTeleportButton'}) do if api.valid(StaticFindObject(MAP..':'..method)) then hookMetadata[MAP..':'..method]=true end end
     if hooksReady then
      local key=api.full(map);local record=views[key]
      if not record then record={map=map,originalView=api.field(map,'IsInPTSView')};views[key]=record end
      local target=targetUnderCursor(map,stateFor(pawn))
      local signature=api.full(target)
      if record.signature~=signature then
       api.write(map,'IsInPTSView',api.valid(target) or record.originalView)
       call(map,MAP,'RefreshPTSButton');record.signature=signature
       api.log(api.valid(target) and 'NATIVE_HOLD_READY: on-demand departure' or 'NATIVE_HOLD_INELIGIBLE')
      end
      record.seen=true
      if baseHooksReady then afterBaseButton(map) end
     end
    end
   end
  end
 end
 for key,record in pairs(views) do if not record.seen then restore(record);views[key]=nil end end
end
LoopAsync(250,function()
 if not baseHooksReady then registerHooks() end
 if ticking then return false end
 ticking=true
 local queued,why=pcall(ExecuteInGameThread,function()
  local ok,err=pcall(tick);ticking=false
  if not ok then
   for key,record in pairs(views) do pcall(restore,record);views[key]=nil end
   api.once('tick:'..tostring(err),'UI_GUARDED_STOP '..tostring(err))
  end
 end)
 if not queued then ticking=false;api.once('dispatch:'..tostring(why),'DISPATCH_WAIT '..tostring(why)) end
 return false
end)
api.log('READY V9 base-building candidate: native map hold creates a fixed 30s departure only on request. No player follower or ordinary trail-marker travel; completed Rivet buildings supply saved base destinations. Install on host and clients; Windows/save/reload validation pending.')
