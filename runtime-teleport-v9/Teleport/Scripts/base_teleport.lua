-- Saved native building + native marker. Backend targets are temporary runtime
-- actors, reconstructed from the saved building and excluded from save restore.
local M={}
local TP='/Game/_Dev/Art/Buildings/Proto/BP_Teleporter.BP_Teleporter_C'
local DOOR='/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door.BP_Teleporter_Door_C'
local ROW='RivetBaseTeleporter'
local BOTTOM='/Game/UI/Buttons/UI_BottomButton.UI_BottomButton_C'
local MAP='/Game/UI/Map/UI_Map.UI_Map_C'
local enum='ByteProperty|EnumProperty'
local schemas={
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Engine.Actor.GetOwner']={ReturnValue='ObjectProperty'},
 ['Engine.Controller.K2_GetPawn']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.GetTransform']={ReturnValue='StructProperty'},
 ['Engine.Actor.K2_GetRootComponent']={ReturnValue='ObjectProperty'},
 ['Engine.SceneComponent.SetMobility']={NewMobility=enum},
 ['Engine.Actor.K2_SetActorTransform']={NewTransform='StructProperty',bSweep='BoolProperty',SweepHitResult='StructProperty',bTeleport='BoolProperty',ReturnValue='BoolProperty'},
 ['Engine.Actor.SetLifeSpan']={InLifespan='FloatProperty'},
 ['Engine.Actor.K2_DestroyActor']={},
 ['Engine.Actor.SetReplicateMovement']={bInReplicateMovement='BoolProperty'},
 ['Engine.Actor.SetReplicates']={bInReplicates='BoolProperty'},
 ['Engine.Actor.K2_GetComponentsByClass']={ComponentClass='ClassProperty',ReturnValue='ArrayProperty'},
 ['Engine.SceneComponent.K2_GetComponentLocation']={ReturnValue='StructProperty'},
 ['Engine.GameplayStatics.BeginDeferredActorSpawnFromClass']={WorldContextObject='ObjectProperty',ActorClass='ClassProperty',SpawnTransform='StructProperty',CollisionHandlingOverride=enum,Owner='ObjectProperty',TransformScaleMethod=enum,ReturnValue='ObjectProperty'},
 ['Engine.GameplayStatics.FinishSpawningActor']={Actor='ObjectProperty',SpawnTransform='StructProperty',TransformScaleMethod=enum,ReturnValue='ObjectProperty'},
 [TP..'.SetTeleportDoorRef']={CallFunc_IsValid_ReturnValue='BoolProperty',K2Node_DynamicCast_AsBP_Teleporter_Door='ObjectProperty',K2Node_DynamicCast_bSuccess='BoolProperty'},
 ['Engine.KismetSystemLibrary.MakeSoftObjectPath']={PathString='StrProperty',ReturnValue='StructProperty'},
 ['Engine.KismetSystemLibrary.Conv_SoftObjPathToSoftObjRef']={SoftObjectPath='StructProperty',ReturnValue='SoftObjectProperty'},
 ['Engine.KismetSystemLibrary.LoadAsset_Blocking']={Asset='SoftObjectProperty',ReturnValue='ObjectProperty'},
 ['Engine.KismetSystemLibrary.IsServer']={WorldContextObject='ObjectProperty',ReturnValue='BoolProperty'},
 ['Engine.StaticMeshComponent.SetStaticMesh']={NewMesh='ObjectProperty',ReturnValue='BoolProperty'},
 ['Maine.MapPanelWidget.GetEntryUnderCursor']={ReturnValue='ObjectProperty'},
 ['Maine.HUDMarkerData.GetReferencedActor']={ReturnValue='ObjectProperty'},
 ['UMG.Widget.SetVisibility']={InVisibility=enum},
 ['UMG.TextBlock.SetText']={InText='TextProperty'},
 ['UMG.TextBlock.GetText']={ReturnValue='TextProperty'},
 ['Engine.KismetTextLibrary.Conv_StringToText']={InString='StrProperty',ReturnValue='TextProperty'},
 ['Maine.SurvivalGameplayStatics.IsEditMode']={WorldContextObject='ObjectProperty',ReturnValue='BoolProperty'},
}
local fields={
 BuildingData={owner='Maine.Building',type='StructProperty'},
 BuildingState={owner='Maine.Building',type='EnumProperty'},
 StaticMeshComponent={owner='Maine.Building',type='ObjectProperty'},
 StaticMesh={owner='Engine.StaticMeshComponent',type='ObjectProperty'},
 Instigator={owner='Engine.Actor',type='ObjectProperty'},
 POIDataAsset={owner=TP,type='ObjectProperty'},
 bCanBeInstanced={owner='Maine.Building',type='BoolProperty'},
 bShouldCreateLODActor={owner='Maine.Building',type='BoolProperty'},
 bCanActorEverProxy={owner='Maine.Building',type='BoolProperty'},
 bAlwaysRelevant={owner='Engine.Actor',type='BoolProperty'},
 bOnlyRelevantToOwner={owner='Engine.Actor',type='BoolProperty'},
 bNeverSpawnAsDynamicActor={owner='Maine.PersistenceComponent',type='BoolProperty'},
 bShouldEditModeSave={owner='Maine.PersistenceComponent',type='BoolProperty'},
 Teleporter_Door_Object_REF={owner=TP,type='ObjectProperty'},
 TeleporterOwner={owner=DOOR,type='ObjectProperty'},
 ArrivalAnchor={owner=TP,type='ObjectProperty'},
 IsInUse={owner=TP,type='BoolProperty'},
 MapPanel={owner='Maine.MapWidget',type='ObjectProperty'},
 HUDMarkerData={owner='Maine.MapMarkerWidget',type='ObjectProperty'},
 TeleportButton={owner=MAP,type='ObjectProperty'},
 ButtonTextBlock={owner=BOTTOM,type='ObjectProperty'},
 CustomNameFiltered={owner='Maine.MarkerBuilding',type='StrProperty'},
}
function M.new(env)
 local api=require('teleport_native_guard').new('Rivet-BaseTeleport',schemas,fields)
 local function call(o,c,m,...) return api.call(o,c,m,...) end
 local function text(v) return type(v)=='string' and v or v:ToString() end
 local function ours(b)
  if not api.isa(b,'Maine.MarkerBuilding') then return false end
  local h=api.field(b,'BuildingData')
  if not h or text(h.RowName)~=ROW then return false end
  local tableName=api.full(h.DataTable)
  return tableName=='CompositeDataTable /Game/Blueprints/Items/Table_AllBuildings.Table_AllBuildings' or tableName=='DataTable /Game/Rivet/Teleport/RivetBaseBuildingData.RivetBaseBuildingData'
 end
 local function eligible(b)
  if not ours(b) or api.field(b,'BuildingState')~=1 then return false end -- EBuildingState::Built
  return not call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','IsEditMode',b)
 end
 local function targetDoor(target) return api.field(target,'Teleporter_Door_Object_REF') end
 local function loadAsset(path)
  local existing=StaticFindObject(path)
  if api.valid(existing) then return existing end
  local k=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary')
  local soft=call(k,'Engine.KismetSystemLibrary','MakeSoftObjectPath',path)
  return call(k,'Engine.KismetSystemLibrary','LoadAsset_Blocking',call(k,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',soft))
 end
 local function destroy(target)
  if not api.valid(target) then return end
  local door=targetDoor(target)
  if api.valid(door) and api.full(api.field(door,'TeleporterOwner'))==api.full(target) then call(door,'Engine.Actor','K2_DestroyActor') end
  call(target,'Engine.Actor','K2_DestroyActor')
 end
 local function noSave(actor)
  local cls=StaticFindObject('/Script/Maine.PersistenceComponent');assert(api.valid(cls),'Persistence class unavailable')
  local parts=call(actor,'Engine.Actor','K2_GetComponentsByClass',cls);local count=0
  local function visit(_,wrapped)
   local part=api.unwrap(wrapped)
   assert(api.isa(part,'Maine.PersistenceComponent'),'Unexpected persistence wrapper')
   count=count+1;assert(count<=16,'Persistence component limit')
   api.write(part,'bNeverSpawnAsDynamicActor',true);api.write(part,'bShouldEditModeSave',false)
  end
  if type(parts)=='table' and type(parts.ForEach)~='function' then for i,p in ipairs(parts) do visit(i,p) end else parts:ForEach(visit) end
  assert(count>0,'Backend target has no save-persistence guard')
 end
 local function align(target,building)
  if api.field(target,'IsInUse') then return end
  local transform=call(building,'Engine.Actor','GetTransform')
  -- Preserve the native pod's full arrival-anchor offset. Do not guess a
  -- capsule height, flatten its arrival to the floor, or move any player.
  assert(call(target,'Engine.Actor','K2_SetActorTransform',transform,false,{},true)==true,'Base arrival alignment rejected')
 end
 local function create(building)
  local class=loadAsset(TP)
  if not api.valid(class) then return end
  local target,door
  local ok,why=pcall(function()
   local gameplay=StaticFindObject('/Script/Engine.Default__GameplayStatics')
   local transform=call(building,'Engine.Actor','GetTransform')
   local scale=env.enumValue('ESpawnActorScaleMethod','MultiplyWithRoot')
   target=call(gameplay,'Engine.GameplayStatics','BeginDeferredActorSpawnFromClass',building,class,transform,env.enumValue('ESpawnActorCollisionHandlingMethod','AlwaysSpawn'),building,scale)
   assert(api.isa(target,TP),'Base target creation failed')
   call(target,'Engine.Actor','SetLifeSpan',5)
   api.write(target,'bAlwaysRelevant',true);api.write(target,'bOnlyRelevantToOwner',false)
   call(target,'Engine.Actor','SetReplicateMovement',true);env.suppress(target)
   assert(api.full(call(gameplay,'Engine.GameplayStatics','FinishSpawningActor',target,transform,scale))==api.full(target),'Base target finish mismatch')
   call(target,'Engine.Actor','SetReplicates',true)
   noSave(target)
   local root=call(target,'Engine.Actor','K2_GetRootComponent')
   assert(api.isa(root,'Engine.SceneComponent'),'Base target root unavailable')
   call(root,'Engine.SceneComponent','SetMobility',env.enumValue('EComponentMobility','Movable'))
   call(target,TP,'SetTeleportDoorRef');door=targetDoor(target)
   assert(api.isa(door,DOOR) and api.full(api.field(door,'TeleporterOwner'))==api.full(target),'Base target door owner mismatch')
   call(door,'Engine.Actor','SetLifeSpan',5);call(door,'Engine.Actor','SetReplicates',true)
   api.write(door,'bAlwaysRelevant',true);api.write(door,'bOnlyRelevantToOwner',false)
   noSave(door);env.suppress(target);env.suppress(door)
   align(target,building)
  end)
  if not ok then
   if api.valid(target) then pcall(destroy,target) end
   error(why)
  end
  api.log('BASE_REGISTERED '..api.full(building)..'; backend='..api.full(target))
  return target
 end
 local registry=require('base_registry').new({eligible=eligible,key=api.full,valid=api.valid,create=create,
  busy=function(t) return api.field(t,'IsInUse')==true end,
  maintain=function(r)
   local busy=api.field(r.target,'IsInUse')==true
   for _,o in ipairs({r.target,targetDoor(r.target)}) do call(o,'Engine.Actor','SetLifeSpan',busy and 30 or 5);env.suppress(o) end
   align(r.target,r.building)
  end,
  retire=function(r)
   for _,o in ipairs({r.target,targetDoor(r.target)}) do call(o,'Engine.Actor','SetLifeSpan',30) end
   api.log('BASE_UNREGISTERED '..api.full(r.building)..'; no new requests accepted')
  end,
  destroy=function(r) destroy(r.target) end,
 })
 local mesh;local appearances={};local labels={}
 local function prepareAppearance(building)
  -- Instance-only change on our row; ordinary native trail markers stay intact.
  if not api.valid(mesh) then
   mesh=loadAsset('/Game/Art/World/ZN00_Global/UGC_Art_Assets/SM_Teleport_Pad.SM_Teleport_Pad')
   assert(api.isa(mesh,'Engine.StaticMesh'),'Native pad mesh failed to load')
  end
  local part=api.field(building,'StaticMeshComponent');assert(api.isa(part,'Engine.StaticMeshComponent'),'Building mesh unavailable')
  local signature=api.full(part)..':'..tostring(api.field(building,'BuildingState'))
  local previous=appearances[api.full(building)]
  if not previous or not api.valid(previous.owner) or previous.signature~=signature then
   -- UE returns false when SetStaticMesh is asked to assign the same mesh.
   -- A preview-to-built state change must not turn that benign case into a stop.
   if api.full(api.field(part,'StaticMesh'))~=api.full(mesh) then
    assert(call(part,'Engine.StaticMeshComponent','SetStaticMesh',mesh)==true,'Pad mesh assignment rejected')
   end
   appearances[api.full(building)]={owner=building,signature=signature}
  end
  api.write(building,'bCanBeInstanced',false);api.write(building,'bShouldCreateLODActor',false);api.write(building,'bCanActorEverProxy',false)
  local k=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary')
  if call(k,'Engine.KismetSystemLibrary','IsServer',building) and call(building,'Engine.Actor','HasAuthority') then
   call(building,'Engine.Actor','SetReplicates',true)
   api.write(building,'bAlwaysRelevant',true);api.write(building,'bOnlyRelevantToOwner',false)
  end
 end
 local base={}
 function base.tick()
  local authoritative={};local seen={}
  for i,b in ipairs(FindAllOf('MarkerBuilding') or {}) do
   assert(i<=1024,'Base building scan limit reached')
   if ours(b) then
    seen[api.full(b)]=true
    local ready,why=pcall(prepareAppearance,b)
    if not ready then
     -- A joining player's not-yet-initialized placement preview must not stop
     -- renewal/cleanup for every other player's completed base.
     api.once('appearance:'..api.full(b)..':'..tostring(why),'BASE_VISUAL_WAIT '..api.full(b)..' '..tostring(why))
    elseif call(StaticFindObject('/Script/Engine.Default__KismetSystemLibrary'),'Engine.KismetSystemLibrary','IsServer',b) and call(b,'Engine.Actor','HasAuthority') then authoritative[#authoritative+1]=b end
   end
  end
  for key in pairs(appearances) do if not seen[key] then appearances[key]=nil end end
  registry.tick(authoritative)
  -- Explicitly suppress the owning client's replicas too. Component visibility
  -- changes are not assumed to replicate, and native animation can reveal doors.
  for i,target in ipairs(FindAllOf('BP_Teleporter_C') or {}) do
   assert(i<=1024,'Backend replica scan limit reached')
   if api.isa(target,TP) then
    local owner=call(target,'Engine.Actor','GetOwner')
    local departure=false
    if api.isa(owner,'Engine.Controller') and not api.valid(api.field(target,'POIDataAsset')) then
     departure=api.full(api.field(target,'Instigator'))==api.full(call(owner,'Engine.Controller','K2_GetPawn'))
    end
    if ours(owner) or departure then
     env.suppress(target)
     local door=targetDoor(target)
     if api.isa(door,DOOR) and api.full(api.field(door,'TeleporterOwner'))==api.full(target) then env.suppress(door) end
    end
   end
  end
 end
 function base.isTarget(target) return registry.matches(target) end
 function base.guardTemporary(actor) noSave(actor) end
 local function selected(map)
  local panel=api.field(map,'MapPanel')
  if not api.isa(panel,'Maine.MapPanelWidget') then return end
  local entry=call(panel,'Maine.MapPanelWidget','GetEntryUnderCursor')
  if not api.isa(entry,'Maine.MapMarkerWidget') then return end
  local data=api.field(entry,'HUDMarkerData')
  if not api.isa(data,'Maine.HUDMarkerData') then return end
  local building=call(data,'Maine.HUDMarkerData','GetReferencedActor')
  if eligible(building) then return building end
 end
 function base.targetOnMap(map)
  if call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','IsEditMode',map) then return end
  local building=selected(map);if not building then return end
  local target=registry.target(building)
  if target then return target end
  -- Joining clients use only the actual server target owned by this building.
  local found
  for i,t in ipairs(FindAllOf('BP_Teleporter_C') or {}) do
   assert(i<=1024,'Base backend scan limit reached')
   if api.isa(t,TP) and api.full(call(t,'Engine.Actor','GetOwner'))==api.full(building) then
    assert(not found,'Multiple base backends; no target guess');found=t
   end
  end
  return found
 end
 function base.refreshButton(map)
  local editing=call(StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics'),'Maine.SurvivalGameplayStatics','IsEditMode',map)
  local target=not editing and base.targetOnMap(map) or nil
  local key=api.full(map);local previous=labels[key]
  if not target or api.field(target,'IsInUse') then
   if previous then
    if api.valid(previous.label) then call(previous.label,'UMG.TextBlock','SetText',previous.text) end
    if not editing and api.valid(previous.button) then call(previous.button,'UMG.Widget','SetVisibility',env.enumValue('ESlateVisibility','Collapsed','UMG')) end
    labels[key]=nil
   end
   return
  end
  local button=api.field(map,'TeleportButton');assert(api.isa(button,BOTTOM),'Map teleport button unavailable')
  local label=api.field(button,'ButtonTextBlock');assert(api.isa(label,'UMG.TextBlock'),'Map button label unavailable')
  if not previous then labels[key]={button=button,label=label,text=call(label,'UMG.TextBlock','GetText')} end
  local k=StaticFindObject('/Script/Engine.Default__KismetTextLibrary')
  local value=call(k,'Engine.KismetTextLibrary','Conv_StringToText','Travel to Base')
  call(label,'UMG.TextBlock','SetText',value)
  call(button,'UMG.Widget','SetVisibility',env.enumValue('ESlateVisibility','Visible','UMG'))
 end
 return base
end
return M
