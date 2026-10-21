-- Isolated rigid wing visual states; no player mesh, equipment, camera or gliding-physics changes.
local function log(s) print('[BuzzWings] '..s..'\n') end
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
local assetPaths={
    RETRACTED='/Game/_BzWRet1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01',
    DEPLOYED='/Game/_BzWExt1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
}
local assets={};local component,ownerPawn,bodyMesh
local enabled=true;local failed=false;local busy=false;local lastState=nil
local noCollision,snap
local function identityTransform()
    return {Rotation={X=0,Y=0,Z=0,W=1},Translation={X=0,Y=0,Z=0},Scale3D={X=1,Y=1,Z=1}}
end
local function pawn()
    for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
        if i>16 then break end
        if valid(pc) and pc:IsLocalController() then local p=pc.Pawn;if valid(p) then return p end end
    end
end
local function visibility(show)
    invoke(component,'Engine.SceneComponent','SetHiddenInGame',not show,false)
    invoke(component,'Engine.SceneComponent','SetVisibility',show,false)
    assert(invoke(component,'Engine.SceneComponent','IsVisible')==show,'Wing visibility flag read-back mismatch')
end
local function cleanup()
    if valid(component) then
        pcall(function() invoke(component,'Engine.SceneComponent','SetHiddenInGame',true,false) end)
        pcall(function() invoke(component,'Engine.ActorComponent','K2_DestroyComponent',ownerPawn) end)
    end
    component=nil;ownerPawn=nil;bodyMesh=nil;lastState=nil
end
local config={ManualWingsExtended=false,ManualToggleKey=nil}
local loaded,user=pcall(require,'wing_config')
if loaded and type(user)=='table' then config=user end
local manualWingsExtended=config.ManualWingsExtended==true
local function state(gliding)
    assert(type(gliding)=='boolean','IsGliding did not return a bool; no state guessed')
    return (manualWingsExtended or gliding) and 'DEPLOYED' or 'RETRACTED'
end
local function showState(desired)
    if lastState==desired then return end
    phase='state-swap '..desired
    visibility(false)
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',assets[desired])
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(component,'Engine.PrimitiveComponent','SetCollisionEnabled',noCollision)
    visibility(true);lastState=desired
    log('STATE '..desired..'; source=IsGliding(); mesh='..full(assets[desired])..'; visible=true')
end
local function verifyInstalledContainer()
    if not io or type(io.open)~='function' then log('DISK CHECK unavailable; native loading remains authoritative');return end
    local dirs={'../../Content/Paks/','Augusta/Content/Paks/','../../../Augusta/Content/Paks/'}
    if debug and type(debug.getinfo)=='function' then
        local ok,info=pcall(debug.getinfo,1,'S')
        if ok and info and type(info.source)=='string' then
            local path=info.source:gsub('^@',''):gsub('\\','/')
            local bin=path:match('^(.-)/[Uu][Ee]4[Ss][Ss]/Mods/')
            if bin then table.insert(dirs,1,bin..'/../../Content/Paks/') end
        end
    end
    for _,dir in ipairs(dirs) do
        local f=io.open(dir..'zBuzzWingsUE57_P.utoc','rb')
        if f then
            local header=f:read(64);local size=f:seek('end');f:close()
            local hex=header and header:gsub('.',function(c) return string.format('%02x',string.byte(c)) end) or ''
            local good=hex=='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d08000000900000000c000000c70000000c000000000000002000000000000100650300000100000036cdd811f6bce109' and size==3953
            log('DISK CHECK zBuzzWingsUE57_P.utoc expected header/size match='..tostring(good)..'; bytes='..tostring(size)..'; path='..dir)
            assert(good,'Wrong container revision installed: zBuzzWingsUE57_P.utoc')
            return
        end
    end
    log('DISK CHECK zBuzzWingsUE57_P.utoc not found in standard paths; native load result will determine availability')
end
local function create(p,body,desired)
    phase='preflight'
    for key,args in pairs(S) do local class,method=key:match('^(.*)%.([^%.]+)$');assert(signature(class,method,args),'Preflight rejected '..key) end
    noCollision=engineEnum('ECollisionEnabled','NoCollision');snap=engineEnum('EAttachmentRule','SnapToTarget')
    local bone=FName('chest_JNT');assert(invoke(body,'Engine.SceneComponent','DoesSocketExist',bone)==true,'chest_JNT missing')
    phase='disk-package-check';verifyInstalledContainer()
    phase='wing-assets-load'
    local system=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary');assert(valid(system),'Kismet default object unavailable')
    for _,name in ipairs({'RETRACTED','DEPLOYED'}) do
        log('MILESTONE 1/6 PATH '..name..' '..assetPaths[name]..' (cooked package/export independently verified offline)')
        if not valid(assets[name]) then
            local path=invoke(system,'Engine.KismetSystemLibrary','MakeSoftObjectPath',assetPaths[name])
            local soft=invoke(system,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',path)
            assets[name]=invoke(system,'Engine.KismetSystemLibrary','LoadAsset_Blocking',soft)
        end
        assert(valid(assets[name]),'Native wing load returned invalid: '..assetPaths[name])
        assert(full(assets[name])=='SkeletalMesh '..assetPaths[name],'Unexpected loaded asset '..full(assets[name]))
        log('MILESTONE 2/6 LOADED '..name..' '..full(assets[name]))
    end
    phase='component-create';ownerPawn=p;bodyMesh=body
    local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent');assert(valid(class),'Skeletal component class missing')
    component=invoke(p,'Engine.Actor','AddComponentByClass',class,true,identityTransform(),true);assert(valid(component),'Wing component not created')
    log('MILESTONE 3/6 COMPONENT '..full(component));visibility(false);phase='component-configure'
    invoke(component,'Engine.PrimitiveComponent','SetCollisionEnabled',noCollision)
    invoke(component,'Engine.PrimitiveComponent','SetSimulatePhysics',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetAllowClothActors',false)
    invoke(component,'Engine.PrimitiveComponent','SetOnlyOwnerSee',false)
    invoke(component,'Engine.PrimitiveComponent','SetOwnerNoSee',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',assets[desired])
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(p,'Engine.Actor','FinishAddComponent',component,true,identityTransform())
    phase='chest-attachment'
    assert(invoke(component,'Engine.SceneComponent','K2_AttachToComponent',body,bone,snap,snap,snap,false)==true,'Chest attachment failed')
    log('MILESTONE 4/6 ATTACHED parent='..full(body)..'; bone=chest_JNT; identity offset; chest-local authored geometry')
    visibility(true);lastState=desired;log('MILESTONE 5/6 VISIBILITY true; initial state='..desired)
    log('MILESTONE 6/6 RESULT SUCCESS: attached; state='..desired..'; no physics/camera/body/equipment changes')
end
local function findBody(p)
    local target='/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01'
    local function matches(body)
        if not valid(body) then return false end
        local mesh=invoke(body,'Engine.SkeletalMeshComponent','GetSkeletalMeshAsset')
        return full(mesh):find(target,1,true)~=nil
    end
    local body=unsafeProperty(p,'Mesh','ObjectProperty');if matches(body) then return body end
    local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent');assert(valid(class),'Skeletal component class unavailable')
    local components=invoke(p,'Engine.Actor','K2_GetComponentsByClass',class)
    if components then for i=1,math.min(#components,32) do if matches(components[i]) then return components[i] end end end
end
local function survivalPawn(p)
    if not valid(p) then return false end
    local getter=p.GetClass
    if type(getter)~='function' then return false end
    local cls=getter(p)
    for depth=1,16 do
        if not valid(cls) then break end
        if cls:GetFullName()=='Class /Script/Maine.SurvivalCharacter' then return true end
        local super=cls.GetSuperStruct
        if type(super)~='function' then break end
        cls=super(cls)
    end
    return false
end
local function update()
    local p=pawn()
    if not valid(p) then cleanup();eligibility('WAIT: enter gameplay as Buzz/Max');return end
    if valid(ownerPawn) and full(ownerPawn)~=full(p) then cleanup() end
    if not survivalPawn(p) then cleanup();eligibility('WAIT: gameplay SurvivalCharacter required; menu/preview pawn skipped');return end
    local body=findBody(p)
    if not valid(body) then cleanup();eligibility('WAIT: Buzz/Max mesh required; pawn='..full(p));return end
    eligibility('ELIGIBLE Buzz/Max; pawn='..full(p)..'; body='..full(body))
    if valid(bodyMesh) and full(bodyMesh)~=full(body) then cleanup() end
    phase='glide-read'
    local movement=unsafeProperty(p,'CharMovementComponent','ObjectProperty');assert(valid(movement),'Movement component unavailable')
    local gliding=invoke(movement,'Maine.MaineCharMovementComponent','IsGliding');local desired=state(gliding)
    if desired~=lastState then log('GLIDE OBSERVED '..tostring(gliding)..'; requested='..desired) end
    if not valid(component) then create(p,body,desired) else showState(desired) end
end
local function dispatch(fn)
    if busy then return end;busy=true
    local ok,err=pcall(function()
        ExecuteInGameThread(function()
            local good,why=pcall(fn);busy=false
            if not good then
                enabled=false;failed=true;log('MILESTONE 6/6 RESULT ERROR: phase='..phase..'; lastCall='..lastCall..'; retracted='..assetPaths.RETRACTED..'; deployed='..assetPaths.DEPLOYED..'; error='..tostring(why));cleanup()
            end
        end)
    end)
    if not ok then busy=false;enabled=false;failed=true;log('DISPATCH ERROR '..tostring(err)) end
end
RegisterKeyBind(Key.F6,function()
    dispatch(function()
        if enabled then enabled=false;cleanup();log('OFF: wing accessory removed; stable Buzz unchanged');return end
        if failed then log('Stopped after error. Preserve UE4SS.log and restart before another attempt.');return end
        enabled=true;log('ON: automatic IsGliding visual states. F6 again removes accessory.');update()
    end)
end)
if type(config.ManualToggleKey)=='string' and config.ManualToggleKey~='F6' and config.ManualToggleKey~='F9' and Key[config.ManualToggleKey] then
    RegisterKeyBind(Key[config.ManualToggleKey],function()
        dispatch(function() manualWingsExtended=not manualWingsExtended;log('MANUAL PREFERENCE '..tostring(manualWingsExtended)..'; active glide always overrides folded preference');if enabled then update() end end)
    end)
else log('Manual wing key unassigned (wing_config.lua); F6 remains debug suspend/resume only') end
LoopAsync(200,function() if enabled then dispatch(update) end return false end)
log('Loaded wings v0.2 stock-accessory layout: AUTOMATIC startup; deployed=manual preference OR IsGliding; landing restores preference. F6 debug suspend/resume only. Requires NEW zBuzzWingsUE57_P trio; remove old zBuzzWings_P trio. Local-client only; native loading/attachment Windows pending. No tuft visual hiding yet.')
