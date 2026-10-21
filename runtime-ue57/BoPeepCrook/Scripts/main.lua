-- Crook carry test: independent local cosmetic component; no equipment/combat/skin changes.
local function log(s) print('[BoPeepCrook] '..s..'\n') end
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
spec('Engine.Actor','AddComponentByClass',{Class='ClassProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty',bDeferredFinish='BoolProperty',ReturnValue='ObjectProperty'})
spec('Engine.Actor','FinishAddComponent',{Component='ObjectProperty',bManualAttachment='BoolProperty',RelativeTransform='StructProperty'})
spec('Engine.ActorComponent','K2_DestroyComponent',{Object='ObjectProperty'})
spec('Engine.SceneComponent','IsVisible',{ReturnValue='BoolProperty'})
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
spec('Maine.SurvivalCharacter','GetFirstPersonCamera',{ReturnValue='ObjectProperty'})
spec('Engine.Actor','K2_GetActorRotation',{ReturnValue='StructProperty'})
spec('Engine.SceneComponent','SetAbsolute',{bNewAbsoluteLocation='BoolProperty',bNewAbsoluteRotation='BoolProperty',bNewAbsoluteScale='BoolProperty'})
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
    lastCall=owner..'.'..method
    if method~='GetItemInSlot' and method~='GetIsFirstPerson' and method~='GetSkeletalMeshAsset' and method~='GetSocketTransform' and method~='K2_GetActorRotation' and method~='K2_SetRelativeTransform' then log('CALL '..owner..'.'..method) end
    return o[method](o,...)
end
local function engineEnum(name,leaf)
    local e=StaticFindObject('/Script/Engine.'..name);assert(valid(e),'Missing enum '..name)
    local result
    e:ForEachName(function(n,v) if n:ToString():match('([^:]+)$')==leaf then result=v end end)
    assert(result~=nil,'Missing enum value '..name..'.'..leaf);return result
end
local assetPath='/Game/_BoCrTP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
local fpPath='/Game/_BoCrFP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
local fpBarePath='/Game/_BoCrFN1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01'
local viewAssets={}
local component,ownerPawn,meshAsset
local enabled=true;local failed=false;local lastVisible=nil;local lastFirst=nil;local busy=false
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
    phase='visibility'
    -- Hide first, show last; never propagate into any native character components.
    invoke(component,'Engine.SceneComponent','SetHiddenInGame',not value,false)
    invoke(component,'Engine.SceneComponent','SetVisibility',value,false)
    local actual=invoke(component,'Engine.SceneComponent','IsVisible')
    assert(actual==value,'Component visibility read-back differs from requested state')
    lastVisible=value;log(value and 'MILESTONE 5/6 VISIBILITY ENABLED (IsVisible=true); both actual hand slots empty' or 'VISIBILITY HIDDEN (IsVisible=false)')
end
local lastPresentation,lastAttack,firstPersonCamera
local presentations={}
local function cleanup()
    local seen={}
    local function dispose(o)
        if valid(o) and not seen[o] then
            seen[o]=true
            pcall(function() invoke(o,'Engine.SceneComponent','SetHiddenInGame',true,false) end)
            pcall(function() invoke(o,'Engine.ActorComponent','K2_DestroyComponent',ownerPawn) end)
        end
    end
    for _,view in pairs(presentations) do dispose(view.component) end
    dispose(component)
    presentations={}
    component=nil;lastPresentation=nil;lastAttack=nil;firstPersonCamera=nil;ownerPawn=nil;lastVisible=nil;lastFirst=nil
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
        local f=io.open(dir..'zBoCrookHandV2UE57_P.utoc','rb')
        if f then
            local header=f:read(64);local size=f:seek('end');f:close()
            local hex=header and header:gsub('.',function(c) return string.format('%02x',string.byte(c)) end) or ''
            local good=hex=='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d080000009000000004000000090000000c000000000000002000000000000100b501000001000000914dc8e13c2794e4' and size==873
            log('DISK CHECK zBoCrookHandV2UE57_P.utoc expected header/size match='..tostring(good)..'; bytes='..tostring(size)..'; path='..dir)
            assert(good,'Wrong container revision installed: zBoCrookHandV2UE57_P.utoc')
            return
        end
    end
    log('DISK CHECK zBoCrookHandV2UE57_P.utoc not found in standard paths; native load result will determine availability')
end
local function create(p,body,presentationMesh)
    phase='preflight'
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
    phase='disk-package-check';verifyInstalledContainer()
    phase='package-path'
    log('MILESTONE 1/6 PACKAGE/OBJECT REQUEST '..assetPath..' (matches cooked package/export offline; runtime load pending)')
    if not valid(meshAsset) then
        phase='asset-load'
        -- Beta LoadAsset() queries AssetRegistry first; new private packages may have no registry entry.
        -- Native soft loading resolves the mounted package directly, without modifying the registry.
        local system=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary')
        assert(valid(system),'KismetSystemLibrary default object unavailable')
        local path=invoke(system,'Engine.KismetSystemLibrary','MakeSoftObjectPath',assetPath)
        local soft=invoke(system,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',path)
        log('LOAD PRIVATE PACKAGE '..assetPath)
        meshAsset=invoke(system,'Engine.KismetSystemLibrary','LoadAsset_Blocking',soft)
        log('LOAD RESULT '..full(meshAsset))
    end
    assert(valid(meshAsset),'Direct crook loader returned no valid UObject for '..assetPath..'; package missing/unmounted or loading/dependency failure; send log')
    assert(full(meshAsset)=='SkeletalMesh '..assetPath,'Loaded object identity differs from requested skeletal mesh: '..full(meshAsset))
    log('MILESTONE 2/6 MESH LOADED '..full(meshAsset))
    local class=StaticFindObject('/Script/Engine.SkeletalMeshComponent');assert(valid(class),'Missing component class')
    -- Derive an initial upright offset from the current hand frame. Retained as a rigid hand attachment.
    local socket=invoke(body,'Engine.SceneComponent','GetSocketTransform',bone,worldSpace)
    local q=socket.Rotation;local norm=q.X*q.X+q.Y*q.Y+q.Z*q.Z+q.W*q.W
    assert(norm>0.9 and norm<1.1,'Invalid hand rotation')
    local offset=transform({X=-q.X/norm,Y=-q.Y/norm,Z=-q.Z/norm,W=q.W/norm})
    ownerPawn=p
    phase='component-create'
    component=invoke(p,'Engine.Actor','AddComponentByClass',class,true,transform(),true)
    assert(valid(component),'Deferred component creation failed')
    log('MILESTONE 3/6 COMPONENT CREATED '..full(component))
    phase='component-configure'
    lastVisible=nil;visible(false)
    phase='component-configure'
    invoke(component,'Engine.PrimitiveComponent','SetCollisionEnabled',noCollision)
    invoke(component,'Engine.PrimitiveComponent','SetSimulatePhysics',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetAllowClothActors',false)
    invoke(component,'Engine.PrimitiveComponent','SetOnlyOwnerSee',false)
    invoke(component,'Engine.PrimitiveComponent','SetOwnerNoSee',false)
    invoke(component,'Engine.SkeletalMeshComponent','SetSkeletalMeshAsset',presentationMesh or meshAsset)
    invoke(component,'Engine.SkeletalMeshComponent','SetDisablePostProcessBlueprint',true)
    invoke(component,'Engine.SkeletalMeshComponent','SetEnableAnimation',false)
    invoke(p,'Engine.Actor','FinishAddComponent',component,true,transform())
    phase='hand-attachment'
    assert(invoke(component,'Engine.SceneComponent','K2_AttachToComponent',body,bone,snap,snap,snap,false)==true,'Hand attachment rejected')
    log('MILESTONE 4/6 ATTACH CALL SUCCEEDED parent='..full(body)..'; bone=r_hand_JNT')
    phase='grip-transform'
    invoke(component,'Engine.SceneComponent','K2_SetRelativeTransform',offset,false,{},true)
    needsResult=true
    log('ATTACHED r_hand_JNT; upright-at-activation offset. Local cosmetic only; no combat changes.')
end
-- Camera-relative presentation changes ONLY the cosmetic, never the native camera/body.
-- Shaft contact moves35% from the measured palm toward the native middle-finger root.
local palm={X=6.34267822,Y=0.00091054,Z=-0.88787583}
local function rotate(q,v)
    local tx=2*(q.Y*v.Z-q.Z*v.Y);local ty=2*(q.Z*v.X-q.X*v.Z);local tz=2*(q.X*v.Y-q.Y*v.X)
    return {X=v.X+q.W*tx+q.Y*tz-q.Z*ty,Y=v.Y+q.W*ty+q.Z*tx-q.X*tz,Z=v.Z+q.W*tz+q.X*ty-q.Y*tx}
end
local attackGetterWarning=false
local function cosmeticAttack(p)
    local ok,result=pcall(function() return unsafeProperty(p,'bIsAttacking','BoolProperty') end)
    if ok and type(result)=='boolean' then return result end
    if not attackGetterWarning then log('OPTIONAL jab unavailable: native attack state not readable; carry and equipment visibility continue');attackGetterWarning=true end
    return false
end
local function loadView(path)
    if valid(viewAssets[path]) then return viewAssets[path] end
    phase='first-person-asset-load'
    local system=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary')
    local softpath=invoke(system,'Engine.KismetSystemLibrary','MakeSoftObjectPath',path)
    local soft=invoke(system,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',softpath)
    local mesh=invoke(system,'Engine.KismetSystemLibrary','LoadAsset_Blocking',soft)
    assert(valid(mesh) and full(mesh)=='SkeletalMesh '..path,'FP accessory failed to load: '..path)
    viewAssets[path]=mesh;log('FP ASSET LOADED '..path);return mesh
end
local handVisibilityWarning=false
local function needsCopiedHand(p,body)
    -- Existing scene-transform API only; no visibility flags on the native body are written.
    local ok,needed=pcall(function()
        if not valid(firstPersonCamera) then firstPersonCamera=invoke(p,'Maine.SurvivalCharacter','GetFirstPersonCamera') end
        local eye=invoke(firstPersonCamera,'Engine.SceneComponent','GetSocketTransform',FName('None'),worldSpace)
        local hand=invoke(body,'Engine.SceneComponent','GetSocketTransform',FName('r_hand_JNT'),worldSpace)
        local q=eye.Rotation;local n=q.X*q.X+q.Y*q.Y+q.Z*q.Z+q.W*q.W
        assert(n>.9 and n<1.1,'Camera quaternion unavailable')
        local d={X=hand.Translation.X-eye.Translation.X,Y=hand.Translation.Y-eye.Translation.Y,Z=hand.Translation.Z-eye.Translation.Z}
        local v=rotate({X=-q.X/n,Y=-q.Y/n,Z=-q.Z/n,W=q.W/n},d)
        -- Conservative view cone: omit proxy before an actual hand can enter the frame.
        local nativeInView=v.X>0 and math.abs(v.Y)<v.X*1.35 and math.abs(v.Z)<v.X*.85
        return not nativeInView
    end)
    if ok then return needed end
    if not handVisibilityWarning then log('OPTIONAL FP hand check unavailable; staff-only fallback avoids duplicate limbs; '..tostring(needed));handVisibilityWarning=true end
    return false
end
local function present(p,body,fp)
    assert(type(fp)=='boolean','Camera mode getter did not return bool')
    local attack=cosmeticAttack(p)
    local copyHand=fp and not attack and needsCopiedHand(p,body)
    local mode=fp and (copyHand and 'FP_GRIP' or 'FP_STAFF') or 'TP'
    if mode~=lastPresentation then
        visible(false)
        if lastPresentation then
            presentations[lastPresentation]={component=component,attached=true}
        elseif valid(component) then
            -- Initial TP creation stays alive and keeps its asset referenced.
            presentations.TP={component=component,attached=false}
        end
        local saved=presentations[mode]
        if saved and valid(saved.component) then
            component=saved.component
            lastFirst=nil
            if saved.attached then lastFirst=fp end
            lastVisible=false
            log('PRESENTATION REUSE '..mode..'; visibility-only selection; no mesh assignment/destruction')
        else
            local mesh=fp and loadView(copyHand and fpPath or fpBarePath) or meshAsset
            create(p,body,mesh)
            lastFirst=nil
            presentations[mode]={component=component,attached=false}
            log('PRESENTATION CREATED ONCE '..mode..'; retained for later view changes')
        end
        lastPresentation=mode
        if fp then log('FP HAND PRESENTATION '..mode..'; native hand visibility cone/attack state; native body untouched') end
    end
    phase=fp and 'first-person-grip-placement' or 'palm-grip-placement'
    local offset=transform()
    if fp then
        if lastFirst~=fp then
            local camera=firstPersonCamera or invoke(p,'Maine.SurvivalCharacter','GetFirstPersonCamera')
            firstPersonCamera=camera
            assert(valid(camera),'First-person camera unavailable for accessory placement')
            assert(invoke(component,'Engine.SceneComponent','K2_AttachToComponent',camera,FName('None'),snap,snap,snap,false)==true,'FP cosmetic attachment failed')
            invoke(component,'Engine.SceneComponent','SetAbsolute',false,false,false)
            log('ACCESSORY VIEW FP: source hand/forearm grip; forward65/right50/down32cm; closer perspective for taller appearance; native camera/body unchanged')
        end
        offset.Translation={X=attack and 75 or 65,Y=50,Z=-32}
        local angle=attack and math.rad(75)/2 or 0
        offset.Rotation={X=0,Y=math.sin(angle),Z=0,W=math.cos(angle)}
    else
        if lastFirst~=fp then
            assert(invoke(component,'Engine.SceneComponent','K2_AttachToComponent',body,FName('r_hand_JNT'),snap,snap,snap,false)==true,'Third-person hand reattachment failed')
            invoke(component,'Engine.SceneComponent','SetAbsolute',false,true,false)
            log('ACCESSORY VIEW TP: grip-local origin at actual shaft contact; upright carry; hook-forward cosmetic jab')
        end
        offset.Translation=palm
        local yaw=math.rad(invoke(p,'Engine.Actor','K2_GetActorRotation').Yaw+180)/2
        local pitch=attack and -math.rad(75)/2 or 0
        offset.Rotation={X=-math.sin(yaw)*math.sin(pitch),Y=math.cos(yaw)*math.sin(pitch),Z=math.sin(yaw)*math.cos(pitch),W=math.cos(yaw)*math.cos(pitch)}
    end
    invoke(component,'Engine.SceneComponent','K2_SetRelativeTransform',offset,false,{},true)
    if attack~=lastAttack then log('COSMETIC JAB '..tostring(attack)..'; native unarmed montage/gameplay untouched; FP proxy hand omitted during native punch');lastAttack=attack end
    lastFirst=fp
    presentations[mode]={component=component,attached=true}
end
local function slotEmpty(value)
    if value==nil then return true end
    local ok,fn=pcall(function() return value.IsValid end)
    assert(ok and type(fn)=='function','Unknown equipment item wrapper; no empty-slot guess')
    local good,result=pcall(fn,value)
    assert(good and type(result)=='boolean','Equipment item validity unavailable; no empty-slot guess')
    return not result
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
    if not valid(p) then
        cleanup();eligibility('WAIT: no valid local player pawn. Load into gameplay, then leave the test enabled.');return
    end
    if not survivalPawn(p) then cleanup();eligibility('WAIT: gameplay SurvivalCharacter required; menu/preview pawn skipped');return end
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
    local empty=slotEmpty(main) and slotEmpty(off)
    local fp=invoke(p,'Maine.SurvivalCharacter','GetIsFirstPerson')
    present(p,body,fp)
    visible(empty)
    if needsResult then
        needsResult=false;phase='attached'
        log('MILESTONE 6/6 RESULT SUCCESS: asset='..assetPath..'; component='..full(component)..'; presentation='..(fp and 'camera-relative' or 'r_hand_JNT palm/upright')..'; visible='..tostring(lastVisible)..'; main='..full(main)..'; off='..full(off)..'; rendered appearance awaits user inspection')
    end
end
local function dispatch(fn)
    if busy then return end
    busy=true
    ExecuteInGameThread(function()
        local ok,why=pcall(fn);busy=false
        if not ok then
            enabled=false;failed=true
            local failedPhase=phase;local failedCall=lastCall
            log('MILESTONE 6/6 RESULT ERROR: phase='..failedPhase..'; lastCall='..failedCall..'; asset='..assetPath..'; error='..tostring(why))
            cleanup();log('STOP: accessory cleanup attempted; no further native attempts. Send UE4SS.log.')
        end
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
log('Loaded crook persistent-view candidate: AUTOMATIC empty-hand carry. Requires zBoCrookHandV2UE57_P trio. F9 is debug suspend/resume only. FP source-hand viewmodel, TP shaft grip origin, cosmetic hook-first jab; native spear montage NOT substituted.')
