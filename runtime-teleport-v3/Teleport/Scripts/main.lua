-- Native map hold-to-travel. No key binding, custom hold timer or coordinates.
-- Server-owned portable native departure; current map/controller do the travel.
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local MAP='/Game/UI/Map/UI_Map.UI_Map_C'
local enum='ByteProperty|EnumProperty'
local schemas={
 ['Engine.Controller.IsLocalController']={ReturnValue='BoolProperty'},
 ['Engine.Controller.K2_GetPawn']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Engine.Actor.GetOwner']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.GetTransform']={ReturnValue='StructProperty'},
 ['Engine.Actor.K2_SetActorTransform']={NewTransform='StructProperty',bSweep='BoolProperty',SweepHitResult='StructProperty',bTeleport='BoolProperty',ReturnValue='BoolProperty'},
 ['Engine.Actor.SetActorHiddenInGame']={bNewHidden='BoolProperty'},
 ['Engine.Actor.SetActorEnableCollision']={bNewActorEnableCollision='BoolProperty'},
 ['Engine.Actor.SetLifeSpan']={InLifespan='FloatProperty'},
 ['Engine.Actor.SetReplicateMovement']={bInReplicateMovement='BoolProperty'},
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
local api=require('teleport_native_guard').new('Teleport Native V3',schemas,{
 MapPanel={owner='Maine.MapWidget',type='ObjectProperty'},
 POIData={owner='Maine.MapPOIWidget',type='ObjectProperty'},
 IsInPTSView={owner=MAP,type='BoolProperty'},
 InteractableItem={owner=MAP,type='ObjectProperty'},
 PTSTravelRequested={owner=MAP,type='BoolProperty'},
 Teleporter_Door_Object_REF={owner=TP,type='ObjectProperty'},
 TeleporterOwner={owner=DOOR,type='ObjectProperty'},
 POIDataAsset={owner=TP,type='ObjectProperty'},
 IsInUse={owner=TP,type='BoolProperty'},
 bOnlyRelevantToOwner={owner='Engine.Actor',type='BoolProperty'},
 bAlwaysRelevant={owner='Engine.Actor',type='BoolProperty'},
 Instigator={owner='Engine.Actor',type='ObjectProperty'},
 ['Interaction Instigator']={owner=DOOR,type='ObjectProperty'},
})
local function call(o,c,m,...) return api.call(o,c,m,...) end
local serverSources={};local views={};local busy=false;local stopped=false
local function enumValue(name,leaf)
 local e=StaticFindObject('/Script/Engine.'..name);assert(api.valid(e),'Missing enum '..name);local v
 e:ForEachName(function(n,x) if n:ToString():match('([^:]+)$')==leaf then v=x end end)
 assert(v~=nil,'Missing enum member '..leaf);return v
end
local function suppress(actor)
 call(actor,'Engine.Actor','SetActorHiddenInGame',true)
 call(actor,'Engine.Actor','SetActorEnableCollision',false)
end
local function spawnSource(pc,pawn)
 local class=StaticFindObject(TP)
 if not api.valid(class) then api.once('class-wait','WAIT: native teleporter class has not loaded yet');return nil end
 local cdo=StaticFindObject('/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.Default__BP_Teleporter_C')
 local dcdo=StaticFindObject('/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.Default__BP_Teleporter_Door_C')
 assert(not api.valid(api.field(cdo,'POIDataAsset')),'Portable source must not register as an actual outpost')
 api.check(cdo,TP,'SetTeleportDoorRef');api.field(dcdo,'Interaction Instigator')
 local gameplay=StaticFindObject('/Script/Engine.Default__GameplayStatics')
 api.check(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass')
 api.check(gameplay,'Engine.GameplayStatics','FinishSpawningActor')
 for _,m in ipairs({'SetActorHiddenInGame','SetActorEnableCollision','SetLifeSpan','SetReplicateMovement','K2_DestroyActor','K2_SetActorTransform'}) do api.check(pawn,'Engine.Actor',m) end
 local transform=call(pawn,'Engine.Actor','GetTransform')
 local source,door
 local ok,err=pcall(function()
  source=call(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass',pawn,class,transform,enumValue('ESpawnActorCollisionHandlingMethod','AlwaysSpawn'),pc,enumValue('ESpawnActorScaleMethod','MultiplyWithRoot'))
  assert(api.isa(source,TP),'Native source creation failed')
  api.write(source,'bAlwaysRelevant',false)
  api.write(source,'bOnlyRelevantToOwner',true)
  api.writeObject(source,'Instigator',pawn,'Engine.Pawn')
  call(source,'Engine.Actor','SetReplicateMovement',true)
  suppress(source);call(source,'Engine.Actor','SetLifeSpan',120)
  local finished=call(gameplay,'Engine.GameplayStatics','FinishSpawningActor',source,transform,enumValue('ESpawnActorScaleMethod','MultiplyWithRoot'))
  assert(api.full(finished)==api.full(source),'Native source finish failed')
  suppress(source);call(source,TP,'SetTeleportDoorRef')
  door=api.field(source,'Teleporter_Door_Object_REF');assert(api.isa(door,DOOR),'Native departure door unavailable')
  assert(api.full(api.field(door,'TeleporterOwner'))==api.full(source),'Departure door owner was not initialized')
  suppress(door)
  -- The native SetAndPrintInteractionInstigator event does this assignment
  -- followed by debug PrintString. Use the checked field to avoid screen text.
  api.writeObject(door,'Interaction Instigator',pawn,'Maine.SurvivalPlayerCharacter')
  assert(not api.valid(api.field(source,'POIDataAsset')),'Portable source unexpectedly claims an outpost POI')
 end)
 if not ok then
  for _,o in pairs({source=source,door=door}) do if api.valid(o) then pcall(call,o,'Engine.Actor','K2_DestroyActor') end end
  error(err)
 end
 api.log('SERVER_SOURCE_READY pc='..api.full(pc)..'; door='..api.full(door)..'; native replicated source; no unlock changes')
 return {pc=pc,pawn=pawn,source=source,door=door}
end
local function prepareServer(controllers)
 local active={}
 for i,pc in ipairs(controllers) do
  if i>16 then break end
  if api.isa(pc,'Engine.Controller') then
   local pawn=call(pc,'Engine.Controller','K2_GetPawn')
   if api.isa(pawn,'Maine.SurvivalPlayerCharacter') and call(pawn,'Engine.Actor','HasAuthority') then
    local key=api.full(pc);active[key]=true;local record=serverSources[key]
    if not record or not api.valid(record.source) or api.full(record.pawn)~=api.full(pawn) then
     if record and api.valid(record.source) then call(record.source,'Engine.Actor','SetLifeSpan',30) end
     local state=call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','GetSurvivalGameState',pawn)
     if api.isa(state,'Maine.SurvivalGameState') then record=spawnSource(pc,pawn) end
     serverSources[key]=record
    end
    if record then call(record.source,'Engine.Actor','SetLifeSpan',120) end
    if record and api.field(record.source,'IsInUse')==false then
     call(record.source,'Engine.Actor','K2_SetActorTransform',call(pawn,'Engine.Actor','GetTransform'),false,{},true)
    end
   end
  end
 end
 for key,r in pairs(serverSources) do
  if not active[key] then
   if api.valid(r.source) then call(r.source,'Engine.Actor','SetLifeSpan',30) end
   serverSources[key]=nil
  end
 end
end
local function ownedSource(pc)
 local record=serverSources[api.full(pc)]
 if record and api.valid(record.door) then return record.source,record.door end
 -- Clients only use an already replicated server source owned by their actual
 -- local controller. No client-local actor, forged RPC or movement operation.
 local found,door
 local pawn=call(pc,'Engine.Controller','K2_GetPawn')
 for i,a in ipairs(FindAllOf('BP_Teleporter_C') or {}) do
  if i>256 then break end
  if api.isa(a,TP) and api.full(call(a,'Engine.Actor','GetOwner'))==api.full(pc) and api.full(api.field(a,'Instigator'))==api.full(pawn) and not api.valid(api.field(a,'POIDataAsset')) then
   local d=api.field(a,'Teleporter_Door_Object_REF')
   if api.isa(d,DOOR) and api.full(api.field(d,'TeleporterOwner'))==api.full(a) then
    assert(not found,'Multiple owned portable sources; no departure guess');found=a;door=d
   end
  end
 end
 return found,door
end
local function visible(widget)
 for _=1,32 do
  if not api.valid(widget) then return true end
  if not call(widget,'UMG.Widget','IsVisible') then return false end
  widget=call(widget,'UMG.Widget','GetParent')
 end
 return false
end
local function restoreView(record)
 if api.valid(record.map) then
  -- Restore only our own injected departure. Do not erase a real pod chosen
  -- by another native interaction while the map was closing.
  if api.full(api.field(record.map,'InteractableItem'))==api.full(record.door) then
   api.writeObject(record.map,'InteractableItem',api.valid(record.originalItem) and record.originalItem or nil,'Engine.Actor')
   api.write(record.map,'IsInPTSView',record.originalView)
  end
 end
end
local function updateMap(pc,pawn,map,state)
 local current=api.field(map,'InteractableItem')
 local key=api.full(map);local record=views[key]
 -- A real departure pod already supplied by the game keeps the entire native
 -- flow unchanged. Our previous injection is recognized by identity.
 if api.valid(current) and (not record or api.full(current)~=api.full(record.door)) then return end
 local source,door=ownedSource(pc)
 if not api.valid(source) or not api.valid(door) then api.once('replica:'..api.full(pc),'WAIT: portable native departure has not replicated; host and client need V3');return end
 suppress(source);suppress(door)
 if record and api.full(record.door)~=api.full(door) then
  restoreView(record);views[key]=nil;record=nil;current=api.field(map,'InteractableItem')
 end
 if not record then
  record={map=map,door=door,originalItem=current,originalView=api.field(map,'IsInPTSView')};views[key]=record
  api.writeObject(map,'InteractableItem',door,'Engine.Actor')
 end
 local panel=api.field(map,'MapPanel')
 local entry=call(panel,'Maine.MapPanelWidget','GetEntryUnderCursor')
 local eligible=false;local destination;local poi
 if api.isa(entry,'Maine.MapPOIWidget') then
  poi=api.field(entry,'POIData')
  if api.valid(poi) and call(state,'Maine.SurvivalGameState','IsPTSTravelLocked',poi)==false and call(state,'Maine.SurvivalGameState','CanPTSTravel',poi)==true then
   -- Current UI_Map casts this registry result to BP_Teleporter_Door, NOT
   -- BP_Teleporter_C. Its TeleporterOwner is the native RPC destination.
   destination=call(state,'Maine.SurvivalGameState','GetRegisteredPTSTravel',poi)
   eligible=api.isa(destination,DOOR) and api.isa(api.field(destination,'TeleporterOwner'),TP) and api.full(destination)~=api.full(door)
  end
 end
 local signature=tostring(eligible)..';'..api.full(poi)..';'..api.full(destination)
 if record.signature~=signature then
  api.write(map,'IsInPTSView',eligible or record.originalView)
  call(map,MAP,'RefreshPTSButton')
  record.signature=signature
  api.log((eligible and 'NATIVE_HOLD_READY' or 'NATIVE_HOLD_INELIGIBLE')..' poi='..api.full(poi)..'; registry='..api.full(destination)..'; original lock/busy/hold/travel logic retained')
 end
 record.seen=true
end
local function tick()
 local controllers=FindAllOf('PlayerController') or {};prepareServer(controllers)
 for _,r in pairs(views) do r.seen=false end
 local pc,pawn
 for i,p in ipairs(controllers) do
  if i>16 then break end
  if api.isa(p,'Engine.Controller') and call(p,'Engine.Controller','IsLocalController') then pc=p;pawn=call(p,'Engine.Controller','K2_GetPawn');break end
 end
 if pc and api.isa(pawn,'Maine.SurvivalPlayerCharacter') then
  -- Keep the owner's replica hidden/noncolliding even with the map closed.
  local ownSource,ownDoor=ownedSource(pc)
  if api.valid(ownSource) and api.valid(ownDoor) then suppress(ownSource);suppress(ownDoor) end
  local ui=StaticFindObject('/Script/Maine.Default__UserInterfaceStatics')
  local manager=call(ui,'Maine.UserInterfaceStatics','GetWidgetManager',pawn)
  if api.valid(manager) and call(manager,'Maine.WidgetManager','IsInGameMenuActive') then
   local state=call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','GetSurvivalGameState',pawn)
   if api.valid(state) then
    for i,map in ipairs(FindAllOf('MapWidget') or {}) do
     if i>32 then break end
     if api.isa(map,MAP) and not api.full(map):find('Default__',1,true) and visible(map) then updateMap(pc,pawn,map,state) end
    end
   end
  end
 end
 for key,r in pairs(views) do if not r.seen then restoreView(r);views[key]=nil end end
end
LoopAsync(250,function()
 if stopped then return true end
 ExecuteInGameThread(function()
  if busy or stopped then return end;busy=true
  local ok,err=pcall(tick);busy=false
  if not ok then
   stopped=true
   for _,r in pairs(views) do pcall(restoreView,r) end
   for _,r in pairs(serverSources) do if api.valid(r.source) then pcall(call,r.source,'Engine.Actor','SetLifeSpan',30) end end
   api.log('GUARDED STOP '..tostring(err))
  end
 end)
 return false
end)
api.log('READY: native map hold-Space candidate V3. No F8 command. Host supplies owned native departure; original UI/controller handles progress, cancellation and travel. Windows validation pending.')
