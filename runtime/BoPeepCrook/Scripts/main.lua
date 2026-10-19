-- Crook carry test: independent local cosmetic component; no equipment/combat/skin changes.
local function log(s) print('[BoPeepCrook] '..s..'\n') end
local function valid(o) return o~=nil and o:IsValid() end
local function full(o) if valid(o) then return o:GetFullName() end return 'NONE' end
local signatures={};local enums={};local busy=false;local recording=false
local untilTime=0;local sequence=0;local lastState=nil;local fault=false
local lastEligibility=nil
local lastMeshCheck=nil
local function eligibility(message)
    if message~=lastEligibility then log(message);lastEligibility=message end
end
local function checked(tag,fn)
    log('BEFORE '..tag)
    local value=fn()
    log('AFTER '..tag)
    return value
end
local function signature(class,method,expected)
    local key='/Script/'..class..':'..method
    if signatures[key]~=nil then return signatures[key] end
    local f=checked('resolve '..key,function() return StaticFindObject(key) end)
    if not valid(f) then log('MISSING FUNCTION '..key);signatures[key]=false;return false end
    local actual={};local count=0
    checked('signature '..key,function()
        f:ForEachProperty(function(p)
            count=count+1
            if count>12 then return true end
            local descriptor=p:GetFullName()
            local typ,name=descriptor:match('^(%S+)%s+.*:([^:]+)$')
            if typ and name then actual[name]=typ else actual['invalid'..count]=descriptor end
        end)
    end)
    local ok=count<=12;local n=0
    for name,typ in pairs(expected) do
        n=n+1
        local alternatives='|'..typ..'|'
        if not actual[name] or not alternatives:find('|'..actual[name]..'|',1,true) then ok=false end
    end
    if count~=n then ok=false end
    signatures[key]=ok
    log((ok and 'SIGNATURE OK ' or 'SIGNATURE REJECTED ')..key)
    return ok
end
local function unsafeCall(o,class,method,expected,...)
    if not valid(o) or not signature(class,method,expected) then return nil end
    -- Validate exact runtime identity first; do not assume every returned wrapper has GetClass.
    local identity=full(o)
    local kind=identity:match('^(%S+) ')
    local match=kind==class:match('([^%.]+)$')
    if not match then
        local getter=o.GetClass
        if type(getter)=='function' then
            local cls=checked('receiver.GetClass '..class,function() return getter(o) end)
            for depth=0,11 do
                if not valid(cls) then break end
                if cls:GetFullName():match('^%S+ (.+)$')=='/Script/'..class then match=true;break end
                cls=checked('receiver.GetSuperStruct '..depth,function() return cls:GetSuperStruct() end)
            end
        end
    end
    if not match then log('REJECTED RECEIVER '..class..'.'..method..' actual='..identity);return nil end
    local args={...}
    return checked('CALL '..class..'.'..method,function() return o[method](o,table.unpack(args)) end)
end
-- Never call Reflection(): this Beta can seed the shared UObject metatable as RemoteObjectBase.
-- Resolve ONLY these known native fields via UClass metadata (the V2 metadata path).
local fieldOwners={CharMovementComponent='Maine.SurvivalCharacter',EquipmentComponent='Maine.SurvivalCharacter',
    bIsAttacking='Maine.SurvivalCharacter',bIsChargingAttack='Maine.SurvivalCharacter',
    bHasMainHand='Maine.EquipmentComponent',bHasOffHand='Maine.EquipmentComponent'}
fieldOwners.Mesh='Engine.Character'
local fieldKinds={}
local function unsafeProperty(o,name,expected)
    if not valid(o) then return nil end
    local owner=fieldOwners[name]
    if not owner then log('UNAPPROVED FIELD '..name);return nil end
    if fieldKinds[name]==nil then
        local cls=checked('field class '..owner,function() return StaticFindObject('/Script/'..owner) end)
        if not valid(cls) then log('MISSING FIELD CLASS '..owner);return nil end
        local kind=false;local count=0
        checked('find exact field '..name,function()
            cls:ForEachProperty(function(p)
                count=count+1
                if count>512 then return true end
                local description=p:GetFullName()
                local typ,leaf=description:match('^(%S+)%s+.*:([^:]+)$')
                if leaf==name then kind=typ;return true end
            end)
        end)
        fieldKinds[name]=kind
    end
    if fieldKinds[name]~=expected then log('PROPERTY TYPE REJECTED '..name..' '..tostring(fieldKinds[name]));return nil end
    local value=checked('READ DIRECT '..name,function() return o[name] end)
    if expected=='ObjectProperty' and value~=nil then
        local tag=value.type
        local wrapper=type(tag)=='function' and tag(value) or 'UNKNOWN'
        log('REFERENCE '..name..' WRAPPER='..wrapper)
        if wrapper~='UObject' and wrapper~='AActor' then log('REJECTED WRAPPER '..name..' '..wrapper);return nil end
    end
    return value
end
local function unsafeEnumValue(name,leaf)
    local key=name..':'..leaf
    if enums[key]~=nil then return enums[key] end
    local e=checked('enum '..name,function() return StaticFindObject('/Script/Maine.'..name) end)
    if not valid(e) then return nil end
    local found=nil;local count=0
    e:ForEachName(function(n,v)
        count=count+1;if count>64 then return true end
        local s=n:ToString();if s:match('([^:]+)$')==leaf then found=v end
    end)
    if found~=nil then enums[key]=found;log('ENUM '..key..'='..found) end
    return found
end

local S={}
local function spec(owner,method,args)
    S[owner..'.'..method]=args
end
local enum='EnumProperty|ByteProperty'
spec('Engine.SkeletalMeshComponent','GetSkeletalMeshAsset',{ReturnValue='ObjectProperty'})
spec('Engine.Actor','K2_GetComponentsByClass',{ComponentClass='ClassProperty',ReturnValue='ArrayProperty'})
spec('Engine.Actor','AddComponentByClass',{Class='ClassProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty',bDeferredFinish='BoolProperty',ReturnValue='ObjectProperty'})
spec('Engine.Actor','FinishAddComponent',{Component='ObjectProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty'})
spec('Engine.ActorComponent','K2_DestroyComponent',{Object='ObjectProperty'})
spec('Engine.SceneComponent','DoesSocketExist',{InSocketName='NameProperty',ReturnValue='BoolProperty'})
spec('Engine.SceneComponent','GetSocketTransform',{InSocketName='NameProperty',TransformSpace=enum,ReturnValue='StructProperty'})
spec('Engine.SceneComponent','K2_AttachToComponent',{Parent='ObjectProperty',SocketName='NameProperty',LocationRule=enum,RotationRule=enum,ScaleRule=enum,bWeldSimulatedBodies='BoolProperty',ReturnValue='BoolProperty'})
spec('Engine.SceneComponent','K2_SetRelativeTransform',{NewTransform='StructProperty',bSweep='BoolProperty',SweepHitResult='StructProperty',bTeleport='BoolProperty'})
spec('Engine.SceneComponent','SetVisibility',{bNewVisibility='BoolProperty',bPropagateToChildren='BoolProperty'})
spec('Engine.SceneComponent','SetHiddenInGame',{NewHidden='BoolProperty',bPropagateToChildren='BoolProperty'})
spec('Engine.PrimitiveComponent','SetCollisionEnabled',{NewType=enum})
spec('Engine.PrimitiveComponent','SetSimulatePhysics',{bSimulate='BoolProperty'})
spec('Engine.PrimitiveComponent','SetOnlyOwnerSee',{bNewOnlyOwnerSee='BoolProperty'})
spec('Engine.PrimitiveComponent','SetOwnerNoSee',{bNewOwnerNoSee='BoolProperty'})
spec('Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',{bInDisablePostProcess='BoolProperty'})
spec('Engine.SkeletalMeshComponent','SetEnableAnimation',{bNewEnableAnimation='BoolProperty'})
spec('Engine.SkeletalMeshComponent','SetAllowClothActors',{bInAllow='BoolProperty'})
spec('Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',{NewMesh='ObjectProperty'})
spec('Maine.EquipmentComponent','GetItemInSlot',{Slot=enum,ReturnValue='ObjectProperty'})
spec('Maine.SurvivalCharacter','GetIsFirstPerson',{ReturnValue='BoolProperty'})
local function invoke(o,owner,method,...)
    assert(valid(o),'Invalid receiver '..method)
    assert(signature(owner,method,S[owner..'.'..method]),'Unsupported signature '..owner..'.'..method)
    -- Values created/selected below have native UObject wrappers; verify native ancestry before every mutation.
    local cls=o:GetClass();local matched=false
    for i=1,16 do
        if not valid(cls) then break end
        if cls:GetFullName():match('^%S+ (.+)$')=='/Script/'..owner then matched=true;break end
        cls=cls:GetSuperStruct()
    end
    assert(matched,'Wrong receiver for '..owner..'.'..method)
    if method~='GetItemInSlot' and method~='GetIsFirstPerson' and method~='GetSkeletalMeshAsset' then log('CALL '..owner..'.'..method) end
    return o[method](o,...)
end
local function engineEnum(name,leaf)
    local e=StaticFindObject('/Script/Engine.'..name);assert(valid(e),'Missing enum '..name)
    local result
    e:ForEachName(function(n,v) if n:ToString():match('([^:]+)$')==leaf then result=v end end)
    assert(result~=nil,'Missing enum value '..name..'.'..leaf);return result
end
local assetPath='/Game/_BoCrook/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
local component,ownerPawn,meshAsset
local enabled=false;local failed=false;local lastVisible=nil;local lastFirst=nil;local busy=false
local mainSlot,offSlot,noCollision,snap,worldSpace
local function transform(q)
    return {Rotation=q or {X=0,Y=0,Z=0,W=1},Translation={X=0,Y=0,Z=0},Scale3D={X=1,Y=1,Z=1}}
end
local function pawn()
    for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
        if i>16 then break end
        if valid(pc) and pc:IsLocalController() then
            local p=pc.Pawn;if valid(p) then return p end
        end
    end
end
local function visible(value)
    if not valid(component) or value==lastVisible then return end
    -- Hide first, show last; never propagate into any native character components.
    invoke(component,'Engine.SceneComponent','SetHiddenInGame',not value,false)
    invoke(component,'Engine.SceneComponent','SetVisibility',value,false)
    lastVisible=value;log(value and 'CROOK VISIBLE: both actual hand slots empty' or 'CROOK HIDDEN')
end
local function cleanup()
    if valid(component) then
        -- Best effort rollback touches only our new component.
        pcall(function() invoke(component,'Engine.SceneComponent','SetHiddenInGame',true,false) end)
        pcall(function() invoke(component,'Engine.ActorComponent','K2_DestroyComponent',ownerPawn) end)
    end
    component=nil;ownerPawn=nil;lastVisible=nil;lastFirst=nil
end
local function create(p,body)
    -- Complete signature/enum/asset/socket checks BEFORE creating a component.
    for key,args in pairs(S) do
        local class,method=key:match('^(.*)%.([^%.]+)$')
        assert(signature(class,method,args),'Preflight rejected '..key)
    end
    mainSlot=unsafeEnumValue('EEquipmentSlot','MainHand');offSlot=unsafeEnumValue('EEquipmentSlot','OffHand')
    assert(mainSlot and offSlot,'Equipment enum unavailable')
    noCollision=engineEnum('ECollisionEnabled','NoCollision')
    snap=engineEnum('EAttachmentRule','SnapToTarget')
    worldSpace=engineEnum('ERelativeTransformSpace','RTS_World')
    assert(valid(body),'Character Mesh unavailable')
    -- Validate the existing player mesh without altering it. Use this test with the Bo Peep skin installed.
    local active=invoke(body,'Engine.SkeletalMeshComponent','GetSkeletalMeshAsset')
    assert(valid(active),'Character mesh asset unavailable')
    log('BODY '..full(active))
    -- Eligibility was checked against the actual cooked Willow mesh path, not a guessed Blueprint name.
    local bone=FName('r_hand_JNT')
    assert(invoke(body,'Engine.SceneComponent','DoesSocketExist',bone)==true,'r_hand_JNT missing')
    if not valid(meshAsset) then
        LoadAsset(assetPath)
        meshAsset=StaticFindObject(assetPath)
    end
    assert(valid(meshAsset),'Crook asset missing: install zBoCrookAsset_P trio and restart')
    local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent');assert(valid(class),'Missing component class')
    -- Derive an initial upright offset from the current hand frame. Retained as a rigid hand attachment.
    local socket=invoke(body,'Engine.SceneComponent','GetSocketTransform',bone,worldSpace)
    local q=socket.Rotation;local norm=q.X*q.X+q.Y*q.Y+q.Z*q.Z+q.W*q.W
    assert(norm>0.9 and norm<1.1,'Invalid hand rotation')
    local offset=transform({X=-q.X/norm,Y=-q.Y/norm,Z=-q.Z/norm,W=q.W/norm})
    ownerPawn=p
    component=invoke(p,'Engine.Actor','AddComponentByClass',class,true,transform(),true)
    assert(valid(component),'Deferred component creation failed')
    lastVisible=nil;visible(false)
    invoke(component,'Engine.PrimitiveComponent','SetCollisionEnabled',noCollision)
    invoke(component,'Engine.PrimitiveComponent','SetSimulatePhysics',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetAllowClothActors',false)
    invoke(component,'Engine.PrimitiveComponent','SetOnlyOwnerSee',false)
    invoke(component,'Engine.PrimitiveComponent','SetOwnerNoSee',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',meshAsset)
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(p,'Engine.Actor','FinishAddComponent',component,true,transform())
    assert(invoke(component,'Engine.SceneComponent','K2_AttachToComponent',body,bone,snap,snap,snap,false)==true,'Hand attachment rejected')
    invoke(component,'Engine.SceneComponent','K2_SetRelativeTransform',offset,false,{},true)
    log('ATTACHED r_hand_JNT; upright-at-activation offset. Local cosmetic only; no combat changes.')
end
local function update()
    local p=pawn()
    if not valid(p) then
        cleanup();eligibility('WAIT: no valid local player pawn. Load into gameplay, then leave the test enabled.');return
    end
    local body=unsafeProperty(p,'Mesh','ObjectProperty')
    local willow='/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01'
    local identity='NONE'
    local function matches(candidate)
        if not valid(candidate) then return false end
        local active=invoke(candidate,'Engine.SkeletalMeshComponent','GetSkeletalMeshAsset')
        local name=full(active)
        local check=full(candidate)..'; asset='..name
        if check~=lastMeshCheck then log('CHECK: pawn='..full(p)..'; component='..check);lastMeshCheck=check end
        if name:find(willow,1,true) then identity=name;return true end
        return false
    end
    if not matches(body) then
        body=nil
        local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent')
        assert(valid(class),'Missing SkeletalMeshComponent class')
        local components=invoke(p,'Engine.Actor','K2_GetComponentsByClass',class)
        assert(components~=nil,'Owned skeletal component list unavailable')
        for i=1,math.min(#components,32) do
            local candidate=components[i]
            if matches(candidate) then body=candidate;break end
        end
    end
    if not valid(body) then
        cleanup();eligibility('WAIT: no owned component uses verified Willow mesh; pawn='..full(p));return
    end
    eligibility('ELIGIBLE: pawn='..full(p)..'; mesh='..identity)
    if valid(ownerPawn) and full(ownerPawn)~=full(p) then cleanup() end
    if not valid(component) then create(p,body) end
    local eq=unsafeProperty(p,'EquipmentComponent','ObjectProperty');assert(valid(eq),'Equipment unavailable')
    local main=invoke(eq,'Maine.EquipmentComponent','GetItemInSlot',mainSlot)
    local off=invoke(eq,'Maine.EquipmentComponent','GetItemInSlot',offSlot)
    -- Only the actual returned item identities determine occupancy; bHas* flags are deliberately absent.
    local empty=not valid(main) and not valid(off)
    visible(empty)
    local fp=invoke(p,'Maine.SurvivalCharacter','GetIsFirstPerson')
    if fp~=lastFirst then log('VIEW '..tostring(fp)..' (true=first person); crook remains eligible in both views');lastFirst=fp end
end
local function dispatch(fn)
    if busy then return end
    busy=true
    ExecuteInGameThread(function()
        local ok,why=pcall(fn);busy=false
        if not ok then enabled=false;failed=true;cleanup();log('STOP '..tostring(why)..'; cosmetic removed. Send UE4SS.log.') end
    end)
end
RegisterKeyBind(Key.F9,function()
    dispatch(function()
        if enabled then enabled=false;cleanup();log('OFF: cosmetic removed');return end
        if failed then log('Restart game after preserving log; no repeated native attempts');return end
        lastEligibility=nil;enabled=true;log('ON: stand upright as Bo Peep with empty hands for initial orientation');update()
    end)
end)
LoopAsync(200,function() if enabled then dispatch(update) end return false end)
log('Loaded carry test v0.1.2 (native mesh getter; owned-component fallback). As Bo Peep, stand upright with empty hands, F9 once. F9 again removes crook. Disable old F9 probes. No spear animation substitution yet.')
