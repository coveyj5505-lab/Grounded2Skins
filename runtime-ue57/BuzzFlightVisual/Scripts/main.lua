-- Isolated third-person flight visual. Native asset data, equipment, camera and physics stay unchanged.
local function log(s) print('[BuzzFlightVisual] '..s..'\n') end
local function valid(o)
    if o==nil then return false end
    local ok,fn=pcall(function() return o.IsValid end)
    if not ok or type(fn)~='function' then return false end
    local good,result=pcall(fn,o)
    return good and result==true
end
local function full(o) if valid(o) then return o:GetFullName() end return 'NONE' end
local signatures={};local enums={};local busy=false;local recording=false
local untilTime=0;local sequence=0;local lastState=nil;local fault=false
local lastEligibility=nil
local lastMeshCheck=nil
local phase='idle';local lastCall='NONE';local needsResult=false
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
spec('Engine.KismetSystemLibrary','MakeSoftObjectPath',{PathString='StrProperty',ReturnValue='StructProperty'})
spec('Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',{SoftObjectPath='StructProperty',ReturnValue='SoftObjectProperty'})
spec('Engine.KismetSystemLibrary','LoadAsset_Blocking',{Asset='SoftObjectProperty',ReturnValue='ObjectProperty'})
spec('Engine.SkeletalMeshComponent','GetSkeletalMeshAsset',{ReturnValue='ObjectProperty'})
spec('Engine.Actor','K2_GetComponentsByClass',{ComponentClass='ClassProperty',ReturnValue='ArrayProperty'})
spec('Maine.MaineCharMovementComponent','IsGliding',{ReturnValue='BoolProperty'})
spec('Engine.Actor','AddComponentByClass',{Class='ClassProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty',bDeferredFinish='BoolProperty',ReturnValue='ObjectProperty'})
spec('Engine.Actor','FinishAddComponent',{Component='ObjectProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty'})
spec('Engine.ActorComponent','K2_DestroyComponent',{Object='ObjectProperty'})
spec('Engine.SceneComponent','IsVisible',{ReturnValue='BoolProperty'})
spec('Engine.SceneComponent','DoesSocketExist',{InSocketName='NameProperty',ReturnValue='BoolProperty'})
spec('Engine.SceneComponent','K2_AttachToComponent',{Parent='ObjectProperty',SocketName='NameProperty',LocationRule=enum,RotationRule=enum,ScaleRule=enum,bWeldSimulatedBodies='BoolProperty',ReturnValue='BoolProperty'})
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
    lastCall=owner..'.'..method
    if method~='GetItemInSlot' and method~='GetIsFirstPerson' and method~='GetSkeletalMeshAsset' then log('CALL '..owner..'.'..method) end
    return o[method](o,...)
end
local function engineEnum(name,leaf)
    local e=StaticFindObject('/Script/Engine.'..name);assert(valid(e),'Missing enum '..name)
    local result
    e:ForEachName(function(n,v) if n:ToString():match('([^:]+)$')==leaf then result=v end end)
    assert(result~=nil,'Missing enum value '..name..'.'..leaf);return result
end

-- Experimental isolated adapter. No enabled.txt or install ZIP is released.
spec('Maine.SurvivalCharacter','GetIsFirstPerson',{ReturnValue='BoolProperty'})
local modelPath='/Game/_BzFlit1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
local cfg={Enabled=false,DebugToggleKey=nil}
local good,value=pcall(require,'flight_config')
if good and type(value)=='table' then cfg=value end
local controllerModule=require('flight_controller')
local enabled=cfg.Enabled==true;local localBusy=false;local api={};local owner=nil
local stableObjects={};local nativeBodies={};local tickBefore={};local lastMessage=nil
local noCollision,snap,alwaysTick;local asset
local function message(s) if s~=lastMessage then log(s);lastMessage=s end end
local function stable(o)
    if not valid(o) then return nil end
    local name=full(o);local saved=stableObjects[name]
    if not valid(saved) then stableObjects[name]=o;return o end
    return saved
end
local function identity()
    return {Rotation={X=0,Y=0,Z=0,W=1},Translation={X=0,Y=0,Z=0},Scale3D={X=1,Y=1,Z=1}}
end
local function propertyKind(owner,name)
    local class=StaticFindObject('/Script/'..owner);assert(valid(class),'Missing class '..owner)
    local found;local n=0
    class:ForEachProperty(function(p)
        n=n+1;if n>512 then return true end
        local typ,leaf=p:GetFullName():match('^(%S+)%s+.*:([^:]+)$')
        if leaf==name then found=typ;return true end
    end)
    return found
end
local function ensureSourceTick(component,purpose)
    if not nativeBodies[component] then return end
    if purpose=='restore' then
        if tickBefore[component]~=nil then
            if component.VisibilityBasedAnimTickOption~=tickBefore[component] then component.VisibilityBasedAnimTickOption=tickBefore[component] end
            assert(component.VisibilityBasedAnimTickOption==tickBefore[component],'Source tick-policy restore readback mismatch')
            tickBefore[component]=nil
        end
        return
    end
    if tickBefore[component]==nil then
        local kind=propertyKind('Engine.SkinnedMeshComponent','VisibilityBasedAnimTickOption')
        assert(kind=='EnumProperty' or kind=='ByteProperty','Unexpected source tick-policy property kind')
        local current=component.VisibilityBasedAnimTickOption
        assert(type(current)=='number','Unknown source animation-tick policy')
        local enum=StaticFindObject('/Script/Engine.EVisibilityBasedAnimTickOption');assert(valid(enum),'Missing live animation-tick enum')
        local known=false
        enum:ForEachName(function(n,v) if v==current then known=true end end)
        assert(known,'Unrecognized original animation-tick enum value')
        tickBefore[component]=current
    end
    component.VisibilityBasedAnimTickOption=alwaysTick
    assert(component.VisibilityBasedAnimTickOption==alwaysTick,'Source tick-policy write readback mismatch')
end
api.valid=valid;api.log=log
api.getVisibility=function(o) return invoke(o,'Engine.SceneComponent','IsVisible') end
api.setVisibility=function(o,show,purpose)
    if purpose=='suppress' then ensureSourceTick(o,purpose) end
    invoke(o,'Engine.SceneComponent','SetVisibility',show,false)
    assert(invoke(o,'Engine.SceneComponent','IsVisible')==show,'Visibility readback mismatch')
    if purpose=='restore' then ensureSourceTick(o,purpose) end
end
api.destroyVisual=function(o) invoke(o,'Engine.ActorComponent','K2_DestroyComponent',owner) end
api.createHiddenVisual=function(path,p,body)
    owner=p;phase='flight-preflight'
    for key,args in pairs(S) do local class,method=key:match('^(.*)%.([^%.]+)$');assert(signature(class,method,args),'Rejected function '..key) end
    noCollision=engineEnum('ECollisionEnabled','NoCollision');snap=engineEnum('EAttachmentRule','SnapToTarget')
    alwaysTick=engineEnum('EVisibilityBasedAnimTickOption','AlwaysTickPoseAndRefreshBones')
    if not valid(asset) then
        local system=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary');assert(valid(system),'Kismet object unavailable')
        local softPath=invoke(system,'Engine.KismetSystemLibrary','MakeSoftObjectPath',path)
        local soft=invoke(system,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',softPath)
        asset=invoke(system,'Engine.KismetSystemLibrary','LoadAsset_Blocking',soft)
    end
    assert(valid(asset) and full(asset)=='SkeletalMesh '..path,'Flight asset load failed: '..path)
    log('FLIGHT ASSET LOADED '..path)
    local component
    local ok,why=pcall(function()
        phase='flight-component-create';local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent');assert(valid(class),'Missing SkeletalMeshComponent class')
        component=invoke(p,'Engine.Actor','AddComponentByClass',class,true,identity(),true);assert(valid(component),'Flight component creation failed')
        invoke(component,'Engine.SceneComponent','SetVisibility',false,false)
        invoke(component,'Engine.PrimitiveComponent','SetCollisionEnabled',noCollision)
        invoke(component,'Engine.PrimitiveComponent','SetSimulatePhysics',false)
        invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
        invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
        invoke(component,'Engine.SkeletalMeshComponent','SetAllowClothActors',false)
        invoke(component,'Engine.PrimitiveComponent','SetOnlyOwnerSee',false)
        invoke(component,'Engine.PrimitiveComponent','SetOwnerNoSee',false)
        invoke(component,'Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',asset)
        invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
        invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
        invoke(p,'Engine.Actor','FinishAddComponent',component,true,identity())
        phase='flight-attachment'
        assert(invoke(component,'Engine.SceneComponent','K2_AttachToComponent',body,FName('None'),snap,snap,snap,false)==true,'Flight component attachment failed')
        assert(invoke(component,'Engine.SceneComponent','IsVisible')==false,'Flight component became visible before native rollback capture')
    end)
    if not ok then
        if valid(component) then pcall(function() invoke(component,'Engine.ActorComponent','K2_DestroyComponent',p) end) end
        error(why)
    end
    log('FLIGHT COMPONENT READY hidden; collision/physics/animation disabled; body-local identity attachment')
    return stable(component)
end
local controller=controllerModule.new(api,modelPath)
local function isSurvival(p)
    if not valid(p) or type(p.GetClass)~='function' then return false end
    local c=p:GetClass()
    for i=1,16 do
        if not valid(c) then break end
        if c:GetFullName()=='Class /Script/Maine.SurvivalCharacter' then return true end
        if type(c.GetSuperStruct)~='function' then break end;c=c:GetSuperStruct()
    end
    return false
end
local function localPawn()
    for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
        if i>16 then break end
        -- Reflected UFunctions can be callable userdata/tables, not Lua functions.
        -- Use the same local-controller invocation as the Windows-working wing adapter.
        if valid(pc) and pc:IsLocalController() then return stable(pc.Pawn) end
    end
end
local function components(p)
    local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent');assert(valid(class),'Missing skeletal component class')
    local list=invoke(p,'Engine.Actor','K2_GetComponentsByClass',class);local bodies,wings={},{};local body
    if list then
        for i=1,math.min(#list,48) do
            local o=stable(list[i])
            if o then
                local mesh=invoke(o,'Engine.SkeletalMeshComponent','GetSkeletalMeshAsset');local name=full(mesh)
                local native=name=='SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01'
                    or name=='SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01_w_BackPack.SK_Male_Teen_01_w_BackPack'
                if native then
                    bodies[#bodies+1]=o;nativeBodies[o]=true
                    if o==controller.body then body=o elseif not body and api.getVisibility(o)==true then body=o end
                elseif name:find('/Game/_BzWExt1/',1,true) or name:find('/Game/_BzWRet1/',1,true) then wings[#wings+1]=o end
            end
        end
    end
    return body or bodies[1],bodies,wings
end
local function update()
    local p=localPawn()
    if not isSurvival(p) then controller.stop();message('WAIT: local gameplay character');return end
    local body,bodies,wings=components(p)
    if not valid(body) then controller.stop();message('WAIT: Buzz/Max source mesh');return end
    local movement=unsafeProperty(p,'CharMovementComponent','ObjectProperty')
    local glide=unsafeCall(movement,'Maine.MaineCharMovementComponent','IsGliding',{ReturnValue='BoolProperty'})
    local first=invoke(p,'Maine.SurvivalCharacter','GetIsFirstPerson')
    assert(type(glide)=='boolean' and type(first)=='boolean','Unknown glide or view state; keep native presentation')
    local active,state=controller.tick({owner=p,body=body,bodies=bodies,wings=wings,isBuzz=true,isGliding=glide,isFirstPerson=first})
    if state=='FALLBACK' then enabled=false end
    message(state..'; IsGliding='..tostring(glide)..'; firstPerson='..tostring(first)..'; visual='..tostring(active))
end
local function dispatch(fn)
    if localBusy then return end;localBusy=true
    local ok,why=pcall(function()
        ExecuteInGameThread(function()
            local good,errorMessage=pcall(fn);localBusy=false
            if not good then enabled=false;log('FLIGHT FALLBACK phase='..phase..'; '..tostring(errorMessage));controller.stop() end
        end)
    end)
    if not ok then localBusy=false;enabled=false;log('DISPATCH ERROR '..tostring(why)) end
end
LoopAsync(200,function()
    if enabled then dispatch(update)
    elseif controller.restorePending or controller.visualCleanupPending or controller.active then dispatch(function() controller.stop() end) end
    return false
end)
if type(cfg.DebugToggleKey)=='string' and Key[cfg.DebugToggleKey] then
    RegisterKeyBind(Key[cfg.DebugToggleKey],function() dispatch(function() enabled=not enabled;if not enabled then controller.stop() end;log('EXPERIMENT ENABLED '..tostring(enabled)) end) end)
end
log('Prepared flight visual adapter: enabled='..tostring(enabled)..'; NOT WINDOWS VALIDATED. No default key. Requires private zBuzzFlightUE57_P assets. Third-person gliding only; no actor/camera/movement writes. v0.3 untouched.')
