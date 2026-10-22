-- Native crook V2.7: automatic empty-hand native item on authoritative Willow.
-- Native equipment/combat supplies stance, arms, montage, reach and hit traces.
-- No montage playback, movement/camera edits, attack timers or fake FP limbs.
local rows=require('item_rows')
local enum='ByteProperty|EnumProperty'
local schemas={
 ['Engine.Controller.IsLocalController']={ReturnValue='BoolProperty'},
 ['Engine.Controller.K2_GetPawn']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Engine.Actor.K2_GetComponentsByClass']={ComponentClass='ClassProperty',ReturnValue='ArrayProperty'},
 ['Engine.Actor.AddComponentByClass']={Class='ClassProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty',bDeferredFinish='BoolProperty',ReturnValue='ObjectProperty'},
 ['Engine.Actor.FinishAddComponent']={Component='ObjectProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty'},
 ['Engine.SkeletalMeshComponent.GetSkeletalMeshAsset']={ReturnValue='ObjectProperty'},
 ['Engine.SkeletalMeshComponent.SetSkeletalMeshAsset']={NewMesh='ObjectProperty'},
 ['Engine.SkeletalMeshComponent.SetDisablePostProcessBlueprint']={bInDisablePostProcess='BoolProperty'},
 ['Engine.SkeletalMeshComponent.SetEnableAnimation']={bNewEnableAnimation='BoolProperty'},
 ['Engine.SkeletalMeshComponent.SetAllowClothActors']={bInAllow='BoolProperty'},
 ['Engine.SceneComponent.K2_AttachToComponent']={Parent='ObjectProperty',SocketName='NameProperty',LocationRule=enum,RotationRule=enum,ScaleRule=enum,bWeldSimulatedBodies='BoolProperty',ReturnValue='BoolProperty'},
 ['Engine.SceneComponent.K2_SetRelativeRotation']={NewRotation='StructProperty',bSweep='BoolProperty',SweepHitResult='StructProperty',bTeleport='BoolProperty'},
 ['Engine.SceneComponent.K2_SetRelativeTransform']={NewTransform='StructProperty',bSweep='BoolProperty',SweepHitResult='StructProperty',bTeleport='BoolProperty'},
 ['Engine.SceneComponent.SetVisibility']={bNewVisibility='BoolProperty',bPropagateToChildren='BoolProperty'},
 ['Engine.SceneComponent.IsVisible']={ReturnValue='BoolProperty'},
 ['Engine.SceneComponent.SetHiddenInGame']={NewHidden='BoolProperty',bPropagateToChildren='BoolProperty'},
 ['Engine.PrimitiveComponent.SetCollisionEnabled']={NewType=enum},
 ['Engine.PrimitiveComponent.SetSimulatePhysics']={bSimulate='BoolProperty'},
 ['Engine.PrimitiveComponent.SetCastShadow']={NewCastShadow='BoolProperty'},
 ['Engine.PrimitiveComponent.SetRenderInMainPass']={bValue='BoolProperty'},
 ['Engine.PrimitiveComponent.SetRenderInDepthPass']={bValue='BoolProperty'},
 ['Engine.PrimitiveComponent.SetOnlyOwnerSee']={bNewOnlyOwnerSee='BoolProperty'},
 ['Engine.PrimitiveComponent.SetOwnerNoSee']={bNewOwnerNoSee='BoolProperty'},
 ['Engine.KismetSystemLibrary.MakeSoftObjectPath']={PathString='StrProperty',ReturnValue='StructProperty'},
 ['Engine.KismetSystemLibrary.Conv_SoftObjPathToSoftObjRef']={SoftObjectPath='StructProperty',ReturnValue='SoftObjectProperty'},
 ['Engine.KismetSystemLibrary.LoadAsset_Blocking']={Asset='SoftObjectProperty',ReturnValue='ObjectProperty'},
 ['Maine.SurvivalGameplayStatics.CreateItem']={WorldContextObject='ObjectProperty',ItemType='StructProperty',ReturnValue='ObjectProperty'},
 ['Maine.Item.GetItemDataRowHandle']={ReturnValue='StructProperty'},
 ['Maine.Item.GetItemVisuals']={ReturnValue='ObjectProperty'},
 ['Maine.Item.GetAttackDamageModifier']={ReturnValue='FloatProperty'},
 ['Maine.Item.CanThrow']={ReturnValue='BoolProperty'},
 ['Maine.EquipmentComponent.GetItemInSlot']={Slot=enum,ReturnValue='ObjectProperty'},
 ['Maine.EquipmentComponent.ServerEquipItem']={Equippable='ObjectProperty',bCheckInventory='BoolProperty',bAddToInventoryCurrentlyEquippedItem='BoolProperty',bCheckToEquipPreviousOffHandItem='BoolProperty',bForceEquip='BoolProperty'},
 ['Maine.EquipmentComponent.ServerRemoveItem']={Item='ObjectProperty',Count='IntProperty'},
 ['Maine.Attack.GetAttackDataRowHandle']={ReturnValue='StructProperty'},
 ['Maine.Attack.GetAttackRange']={ReturnValue='FloatProperty'},
 ['Maine.Attack.CanCharge']={ReturnValue='BoolProperty'},
}
local fields={
 EquipmentComponent={owner='Maine.SurvivalCharacter',type='ObjectProperty'},
 Mesh={owner='Engine.Character',type='ObjectProperty'},
 AttackCombo={owner='Maine.Item',type='ObjectProperty'},
 Attacks={owner='Maine.AttackCombo',type='ArrayProperty'},
 RelativeRotation={owner='Engine.SceneComponent',type='StructProperty'},
 StaticMesh={owner='Engine.StaticMeshComponent',type='ObjectProperty'},
 bHiddenInGame={owner='Engine.SceneComponent',type='BoolProperty'},
 bRenderInMainPass={owner='Engine.PrimitiveComponent',type='BoolProperty'},
 bRenderInDepthPass={owner='Engine.PrimitiveComponent',type='BoolProperty'},
 CastShadow={owner='Engine.PrimitiveComponent',type='BoolProperty'},
 bOnlyOwnerSee={owner='Engine.PrimitiveComponent',type='BoolProperty'},
 bOwnerNoSee={owner='Engine.PrimitiveComponent',type='BoolProperty'},
}
local api=require('crook_guard').new('BoPeepNativeSpear',schemas,fields)
local function call(o,owner,method,...) return api.call(o,owner,method,...) end
local meshPath='/Game/_BoCrTP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
local spearPath='StaticMesh /Game/Art/Items/Weapons/Spear02/Spear02.Spear02'
-- Half-turn around the mesh-local +Z shaft: flip hook roll, retain grip/length.
local fit={Translation={X=0,Y=0,Z=18.883807460713253},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1.35,Y=1.35,Z=.9517943985589026}}
local function identity() return {Translation={X=0,Y=0,Z=0},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=1,Y=1,Z=1}} end
local function text(v) return type(v)=='string' and v or v:ToString() end
local function values(a)
    assert(a~=nil,'Missing native array');local out={}
    if type(a)=='table' and type(a.ForEach)~='function' then
        for i,v in ipairs(a) do assert(i<=128,'Native array too large');out[#out+1]=api.unwrap(v) end
        return out
    end
    a:ForEach(function(_,v) assert(#out<128,'Native array too large');out[#out+1]=api.unwrap(v) end)
    return out
end
local function enumValue(owner,leaf)
    local e=StaticFindObject('/Script/'..owner);assert(api.valid(e),'Missing enum '..owner);local found
    e:ForEachName(function(n,v) if text(n):match('([^:]+)$')==leaf then found=v end end)
    assert(found~=nil,'Missing enum member '..leaf);return found
end
local function loadAsset(path)
    local existing=StaticFindObject(path);if api.valid(existing) then return existing end
    local k=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary')
    local softpath=call(k,'Engine.KismetSystemLibrary','MakeSoftObjectPath',path)
    local soft=call(k,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',softpath)
    local asset=call(k,'Engine.KismetSystemLibrary','LoadAsset_Blocking',soft)
    assert(api.valid(asset),'Package missing or failed to load: '..path);return asset
end
local ready=false;local disabled=false;local busy=false;local handle,mesh,mainSlot,offSlot,noCollision,snap
local liveEquipment,liveItem,livePawn
local bindings={}
local function prepare()
    if ready and api.valid(handle.DataTable) then
        -- Lua wrappers alone are not a native GC root. Reload the mesh after
        -- menu/world garbage collection instead of dereferencing a stale asset.
        if not api.valid(mesh) then mesh=loadAsset(meshPath) end
        return
    end
    local items=loadAsset(rows.items);local attacks=loadAsset(rows.attacks)
    handle=rows.prepare(nil,items,attacks,api)
    mesh=loadAsset(meshPath);assert(api.full(mesh)=='SkeletalMesh '..meshPath,'Wrong crook mesh')
    mainSlot=enumValue('Maine.EEquipmentSlot','MainHand');offSlot=enumValue('Maine.EEquipmentSlot','OffHand')
    noCollision=enumValue('Engine.ECollisionEnabled','NoCollision');snap=enumValue('Engine.EAttachmentRule','SnapToTarget')
    ready=true;api.log('READY: private native spear item, three damage8/range275/no-charge jabs. automatic empty-hand carry; host Willow.')
end
local function localPawn()
    for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
        if i>16 then break end
        if api.isa(pc,'Engine.PlayerController') and call(pc,'Engine.Controller','IsLocalController') then
            local p=call(pc,'Engine.Controller','K2_GetPawn')
            if api.isa(p,'Maine.SurvivalPlayerCharacter') then return p end
        end
    end
end
local function willow(p)
    local body=api.field(p,'Mesh');if not api.valid(body) then return false end
    local asset=call(body,'Engine.SkeletalMeshComponent','GetSkeletalMeshAsset')
    return api.full(asset):find('/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01',1,true)~=nil
end
local function isCrook(item)
    if not api.isa(item,'Maine.Item') then return false end
    local h=call(item,'Maine.Item','GetItemDataRowHandle')
    return api.full(h.DataTable)=='DataTable '..rows.items and text(h.RowName)==rows.row
end
local function verifyItem(item)
    assert(isCrook(item),'Native item was not created from the private row')
    assert(call(item,'Maine.Item','GetAttackDamageModifier')==1,'Unexpected item damage multiplier; refuse double scaling')
    assert(call(item,'Maine.Item','CanThrow')==false,'Private crook unexpectedly permits throwing')
    local combo=api.field(item,'AttackCombo');assert(api.valid(combo),'Native spear combo was not initialized')
    local attacks=values(api.field(combo,'Attacks'));assert(#attacks==3,'Native item must have three attacks')
    for i,a in ipairs(attacks) do
        local h=call(a,'Maine.Attack','GetAttackDataRowHandle')
        assert(api.full(h.DataTable)=='DataTable '..rows.attacks,'Native attack uses an ordinary spear table')
        assert(text(h.RowName)==({'Spear','Spear2','Spear3'})[i],'Unexpected native jab order')
        assert(call(a,'Maine.Attack','GetAttackRange')==275,'Native attack range mismatch')
        assert(call(a,'Maine.Attack','CanCharge')==false,'Native attack charging is still enabled')
    end
    api.log('ITEM VERIFIED: native combo3, private damage8 rows, range275, CanCharge=false, no multiplier, no throw')
end
local function show(proxy,native)
    local shown=call(native,'Engine.SceneComponent','IsVisible') and not api.field(native,'bHiddenInGame')
    call(proxy,'Engine.SceneComponent','SetVisibility',shown,false)
    call(proxy,'Engine.SceneComponent','SetHiddenInGame',not shown,false)
    call(proxy,'Engine.PrimitiveComponent','SetOnlyOwnerSee',api.field(native,'bOnlyOwnerSee'))
    call(proxy,'Engine.PrimitiveComponent','SetOwnerNoSee',api.field(native,'bOwnerNoSee'))
end
local function restore(b)
    if api.valid(b.proxy) then call(b.proxy,'Engine.SceneComponent','SetVisibility',false,false) end
    if api.valid(b.native) then
        call(b.native,'Engine.PrimitiveComponent','SetRenderInMainPass',b.main)
        call(b.native,'Engine.PrimitiveComponent','SetRenderInDepthPass',b.depth)
        call(b.native,'Engine.PrimitiveComponent','SetCastShadow',b.shadow)
    end
end
local function bind(actor,native)
    local b={actor=actor,native=native,main=api.field(native,'bRenderInMainPass'),depth=api.field(native,'bRenderInDepthPass'),shadow=api.field(native,'CastShadow')}
    -- Track before configuring, so failure can restore native rendering.
    bindings[api.full(native)]=b
    local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent')
    b.proxy=call(actor,'Engine.Actor','AddComponentByClass',class,true,identity(),true)
    assert(api.valid(b.proxy),'Deferred crook component creation failed')
    call(b.proxy,'Engine.SceneComponent','SetVisibility',false,false)
    call(b.proxy,'Engine.PrimitiveComponent','SetCollisionEnabled',noCollision)
    call(b.proxy,'Engine.PrimitiveComponent','SetSimulatePhysics',false)
    call(b.proxy,'Engine.PrimitiveComponent','SetCastShadow',false)
    call(b.proxy,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    call(b.proxy,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    call(b.proxy,'Engine.SkeletalMeshComponent','SetAllowClothActors',false)
    call(b.proxy,'Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',mesh)
    call(actor,'Engine.Actor','FinishAddComponent',b.proxy,true,identity())
    assert(call(b.proxy,'Engine.SceneComponent','K2_AttachToComponent',native,FName('None'),snap,snap,snap,false),'Native spear component attachment failed')
    call(b.proxy,'Engine.SceneComponent','K2_SetRelativeTransform',fit,false,{},true)
    -- Use explicit reflected Euler parameters; verify the actual component,
    -- not just a requested quaternion in an input transform table.
    call(b.proxy,'Engine.SceneComponent','K2_SetRelativeRotation',{Pitch=0,Yaw=180,Roll=0},false,{},true)
    local actual=api.field(b.proxy,'RelativeRotation')
    local yaw,pitch,roll=actual.Yaw,actual.Pitch,actual.Roll
    assert(type(yaw)=='number' and type(pitch)=='number' and type(roll)=='number','Crook relative rotation unreadable')
    assert(math.abs(((yaw-180+180)%360)-180)<.5 and math.abs(pitch)<.5 and math.abs(roll)<.5,'Crook shaft roll was not applied')
    api.log('CROOK ROTATION VERIFIED: relative Pitch='..pitch..' Yaw='..yaw..' Roll='..roll..'; hook shaft roll180')
    call(native,'Engine.PrimitiveComponent','SetRenderInMainPass',false)
    call(native,'Engine.PrimitiveComponent','SetRenderInDepthPass',false)
    call(native,'Engine.PrimitiveComponent','SetCastShadow',false)
    show(b.proxy,native)
    api.log('BOUND TO NATIVE WEAPON: '..api.full(native)..'; native arms/animations/collision retained; shaft radial scale1.35')
end
local function update()
    local p=localPawn();local item
    if p and willow(p) then
        local eq=api.field(p,'EquipmentComponent')
        if api.valid(eq) then item=call(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot) end
    end
    local actor=isCrook(item) and call(item,'Maine.Item','GetItemVisuals') or nil
    local active={}
    if api.valid(actor) then
        local class=StaticFindObject('/Script/Engine.StaticMeshComponent')
        for _,native in ipairs(values(call(actor,'Engine.Actor','K2_GetComponentsByClass',class))) do
            if api.isa(native,'Engine.StaticMeshComponent') and api.full(api.field(native,'StaticMesh'))==spearPath then
                api.once('native-visual:'..api.full(native),'NATIVE SPEAR COMPONENT: '..api.full(native))
                local key=api.full(native);active[key]=true
                local b=bindings[key]
                if not b or not api.valid(b.proxy) then
                    if b then restore(b) end
                    bind(actor,native)
                else
                    call(native,'Engine.PrimitiveComponent','SetRenderInMainPass',false)
                    call(native,'Engine.PrimitiveComponent','SetRenderInDepthPass',false)
                    call(native,'Engine.PrimitiveComponent','SetCastShadow',false)
                    show(b.proxy,native)
                end
            elseif not api.isa(native,'Engine.StaticMeshComponent') then
                api.once('skip-component:'..api.full(native),'VISUAL COMPONENT SKIPPED: '..api.full(native))
            end
        end
    end
    if api.valid(actor) and next(active)==nil then api.once('visual-wait:'..api.full(actor),'WAIT: native spear mesh not available yet on '..api.full(actor)) end
    for key,b in pairs(bindings) do
        if not active[key] then restore(b) end
        if not api.valid(b.actor) then bindings[key]=nil end
    end
end
local function toggle()
    prepare()
    local p=localPawn()
    if not p or not willow(p) then api.log('WAIT: load as Bo Peep/Willow for this test');return end
    if not call(p,'Engine.Actor','HasAuthority') then api.log('WAIT: first native-item test is host-only; no client-local equipment writes');return end
    local eq=api.field(p,'EquipmentComponent');assert(api.valid(eq),'Equipment component missing')
    local main=call(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)
    local off=call(eq,'Maine.EquipmentComponent','GetItemInSlot',offSlot)
    if isCrook(main) then
        for _,b in pairs(bindings) do restore(b) end
        call(eq,'Maine.EquipmentComponent','ServerRemoveItem',main,1)
        assert(not isCrook(call(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)),'Native crook removal did not clear slot')
        liveEquipment=nil;liveItem=nil;livePawn=nil
        api.log('REMOVED: crook native item removed; ordinary equipment untouched');return
    end
    if api.valid(main) or api.valid(off) then api.log('WAIT: empty BOTH actual hand slots before F7; no gear will be replaced');return end
    local statics=StaticFindObject('/Script/Maine.Default__SurvivalGameplayStatics')
    api.check(eq,'Maine.EquipmentComponent','ServerRemoveItem')
    api.check(eq,'Maine.EquipmentComponent','ServerEquipItem')
    local item=call(statics,'Maine.SurvivalGameplayStatics','CreateItem',p,handle)
    assert(api.isa(item,'Maine.Item'),'Native item creation failed')
    call(eq,'Maine.EquipmentComponent','ServerEquipItem',item,false,false,false,false)
    assert(isCrook(call(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)),'Native equip failed')
    liveEquipment=eq;liveItem=item;livePawn=p
    -- Native equipment initializes owner-bound attack objects. Validate in the
    -- same game-thread operation, before control returns to player input.
    local ok,err=pcall(verifyItem,item)
    if not ok then
        call(eq,'Maine.EquipmentComponent','ServerRemoveItem',item,1)
        liveEquipment=nil;liveItem=nil;livePawn=nil
        assert(not isCrook(call(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)),'Rejected item removal failed')
        error(err)
    end
    api.log('EQUIPPED: use normal attack; native spear arms/grip/stance. automatic equipment hand checks active.')
    update()
end
local function automaticCarry()
    local p=localPawn()
    -- Retire this mod's exact item on character/world change or when native
    -- equipment replaced it. Do not alter the player's replacement equipment.
    if api.valid(liveEquipment) and api.valid(liveItem) and api.valid(livePawn) and call(livePawn,'Engine.Actor','HasAuthority') then
        local current=call(liveEquipment,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)
        if not p or not willow(p) or api.full(p)~=api.full(livePawn) or api.full(current)~=api.full(liveItem) then
            for _,b in pairs(bindings) do restore(b) end
            -- Once ordinary gear replaced it, the native equipment operation
            -- already unequipped our item. Never remove through the new slot.
            if api.full(current)==api.full(liveItem) then call(liveEquipment,'Maine.EquipmentComponent','ServerRemoveItem',liveItem,1) end
            liveEquipment=nil;liveItem=nil;livePawn=nil
        end
    end
    if not p or not willow(p) then return end
    if not call(p,'Engine.Actor','HasAuthority') then
        api.once('automatic-client','WAIT: automatic native equipment requires host authority; client support remains pending')
        return
    end
    local eq=api.field(p,'EquipmentComponent');if not api.valid(eq) then return end
    local main=call(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)
    local off=call(eq,'Maine.EquipmentComponent','GetItemInSlot',offSlot)
    if isCrook(main) then
        if not api.valid(liveItem) then
            verifyItem(main);liveEquipment=eq;liveItem=main;livePawn=p
        end
        if api.valid(off) then toggle() end
    elseif not api.valid(main) and not api.valid(off) then
        toggle()
    end
end
local function run(fn)
    if busy or disabled then return end
    busy=true
    local ok,err=pcall(fn)
    if not ok then
        disabled=true
        for _,b in pairs(bindings) do pcall(restore,b) end
        local clean,cleanupError=pcall(function()
            if api.valid(liveEquipment) and api.valid(liveItem) then
                local equipped=call(liveEquipment,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)
                if api.full(equipped)==api.full(liveItem) then
                    call(liveEquipment,'Maine.EquipmentComponent','ServerRemoveItem',liveItem,1)
                    api.log('ROLLBACK: removed test item after runtime failure')
                end
            end
        end)
        if not clean then api.log('ROLLBACK INCOMPLETE: '..tostring(cleanupError)..'; remove the test item through equipment before saving') end
        api.log('STOPPED SAFELY: '..tostring(err))
    end
    busy=false
end
-- F7 is development-only; normal use has no hotkey dependency.
local DEVELOPMENT_F7=false
if DEVELOPMENT_F7 then RegisterKeyBind(Key.F7,function() ExecuteInGameThread(function() run(toggle) end) end) end
LoopAsync(100,function()
    if disabled then return true end
    ExecuteInGameThread(function() run(function() prepare();automaticCarry();update() end) end)
    return false
end)
api.log('Loaded native crook V2.7 candidate. Preparing private tables; automatic empty-hand carry enabled.')
