-- Crook carry test: independent local cosmetic component; no equipment/combat/skin changes.
local function log(s) print('[SpearReferenceProbe] '..s..'\n') end
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
local traced={}
local function checked(tag,fn)
    local first=not traced[tag]
    if first then log('BEFORE '..tag) end
    local value=fn()
    if first then log('AFTER '..tag);traced[tag]=true end
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
        local note='REFERENCE '..name..' WRAPPER='..wrapper
        if not traced[note] then log(note);traced[note]=true end
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


fieldOwners.StaticMesh="Engine.StaticMeshComponent"
fieldOwners.AttackCombo='Maine.Item'
fieldOwners.Attacks='Maine.AttackCombo'
fieldOwners.FieldOfView='Engine.CameraComponent'
fieldOwners.Stance='Maine.CharacterAnimInstance'
fieldOwners.OffhandStance='Maine.CharacterAnimInstance'
fieldOwners.CustomAttackMultiplier='Maine.Item' 
-- Read-only, live-schema-gated probe. No cosmetic creation or native state writes.
local schemas={
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Engine.PlayerController.GetViewportSize']={SizeX='IntProperty',SizeY='IntProperty'},
 ['Engine.KismetSystemLibrary.Conv_ClassToSoftClassReference']={Class='ClassProperty',ReturnValue='SoftClassProperty'},
 ['Maine.UserInterfaceStatics.GetDefaultBaseDamageFirstAttackOfCharacter']={WorldContextObject='ObjectProperty',SurvivalCharacterClass='SoftClassProperty',ReturnValue='FloatProperty|DoubleProperty'},
 ['Maine.SurvivalCharacter.GetCurrentAttack']={ReturnValue='ObjectProperty'},
 ['Maine.SurvivalCharacter.GetDefaultAttack']={ReturnValue='ObjectProperty'},
 ['Maine.Item.GetItemDataRowHandle']={ReturnValue='StructProperty'},
 ['Maine.Item.GetAttackDamageModifier']={ReturnValue='FloatProperty|DoubleProperty'},
 ['Maine.Attack.GetAttackDataRowHandle']={ReturnValue='StructProperty'},
 ['Maine.Attack.GetAttackRange']={ReturnValue='FloatProperty|DoubleProperty'},
 ['Maine.Attack.GetChargedAttackRange']={ReturnValue='FloatProperty|DoubleProperty'},
 ['Maine.Attack.GetAnimMontage']={ReturnValue='ObjectProperty'},
 ['Engine.SkeletalMeshComponent.GetSkeletalMeshAsset']={ReturnValue='ObjectProperty'},
 ['Engine.SkeletalMeshComponent.GetAnimInstance']={ReturnValue='ObjectProperty'},
 ['Engine.AnimInstance.GetCurrentActiveMontage']={ReturnValue='ObjectProperty'},
 ['Engine.AnimInstance.Montage_GetPosition']={Montage='ObjectProperty',ReturnValue='FloatProperty|DoubleProperty'},
 ['Engine.Actor.K2_GetComponentsByClass']={ComponentClass='ClassProperty',ReturnValue='ArrayProperty'},
 ['Engine.SceneComponent.GetSocketTransform']={InSocketName='NameProperty',TransformSpace='ByteProperty|EnumProperty',ReturnValue='StructProperty'},
 ['Engine.SceneComponent.DoesSocketExist']={InSocketName='NameProperty',ReturnValue='BoolProperty'},
 ['Engine.SceneComponent.GetAttachParent']={ReturnValue='ObjectProperty'},
 ['Engine.SceneComponent.GetAttachSocketName']={ReturnValue='NameProperty'},
 ['Engine.StaticMeshComponent.GetLocalBounds']={Min='StructProperty',Max='StructProperty'},
 ['Maine.SurvivalCharacter.GetIsFirstPerson']={ReturnValue='BoolProperty'},
 ['Maine.SurvivalCharacter.GetFirstPersonCamera']={ReturnValue='ObjectProperty'},
 ['Maine.EquipmentComponent.GetItemInSlot']={Slot='ByteProperty|EnumProperty',ReturnValue='ObjectProperty'},
 ['Maine.Item.GetItemVisuals']={ReturnValue='ObjectProperty'},
 ['Engine.GameplayStatics.GetTimeSeconds']={WorldContextObject='ObjectProperty',ReturnValue='FloatProperty|DoubleProperty'},
}
local function read(o,owner,method,...)
    return unsafeCall(o,owner,method,assert(schemas[owner..'.'..method],'Unapproved read'),...)
end
local function isa(o,name)
    if not valid(o) then return false end
    local cls=o:GetClass()
    for _=1,20 do
        if not valid(cls) then break end
        if full(cls)=='Class /Script/'..name then return true end
        cls=cls:GetSuperStruct()
    end
    return false
end
local function unwrap(o)
    if o==nil then return nil end
    local kind=type(o.type)=='function' and o:type() or nil
    if kind=='RemoteUnrealParam' or kind=='LocalUnrealParam' then return o:get() end
    return o
end
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<math.huge end
local function vec(v)
    assert(v and finite(v.X) and finite(v.Y) and finite(v.Z),'Unknown vector')
    return {X=v.X,Y=v.Y,Z=v.Z}
end
local function transform(t)
    local p=vec(t.Translation);local q=vec(t.Rotation);assert(finite(t.Rotation.W),'Unknown quaternion');q.W=t.Rotation.W
    return {Translation=p,Rotation=q,Scale3D=vec(t.Scale3D)}
end
local function quote(s)
    return '"'..s:gsub('[%z\1-\31\\"]',function(c)
        if c=='"' then return '\\"' elseif c=='\\' then return '\\\\' end
        return string.format('\\u%04x',string.byte(c))
    end)..'"'
end
local function json(v)
    if type(v)=='string' then return quote(v) end
    if type(v)=='boolean' then return tostring(v) end
    if type(v)=='number' then assert(finite(v),'Nonfinite JSON number');return string.format('%.9g',v) end
    assert(type(v)=='table','Non-owned value in JSON')
    local keys={};for k in pairs(v) do keys[#keys+1]=k end
    local array=#keys>0 and type(keys[1])=='number'
    local out={}
    if array then for i=1,#v do out[#out+1]=json(v[i]) end;return '['..table.concat(out,',')..']' end
    table.sort(keys)
    for _,k in ipairs(keys) do out[#out+1]=quote(k)..':'..json(v[k]) end
    return '{'..table.concat(out,',')..'}'
end
local notices={}
local function optional(tag,fn)
    local ok,result=pcall(fn)
    if not ok and not notices[tag] then log('OPTIONAL '..tag..': '..tostring(result));notices[tag]=true end
    if ok then return result end
    return nil
end
local worldSpace=nil;local slot=nil;local offSlot=nil
local function worldEnum()
    if worldSpace~=nil then return worldSpace end
    local e=StaticFindObject('/Script/Engine.ERelativeTransformSpace');assert(valid(e),'Missing transform enum')
    e:ForEachName(function(n,v) if n:ToString():match('([^:]+)$')=='RTS_World' then worldSpace=v end end)
    assert(worldSpace~=nil,'Missing world-space enum');return worldSpace
end
local function world(o,bone)
    return transform(read(o,'Engine.SceneComponent','GetSocketTransform',FName(bone or 'None'),worldEnum()))
end
local function components(actor)
    local out={};local cls=StaticFindObject('/Script/Engine.PrimitiveComponent');assert(valid(cls),'Missing primitive class')
    local list=read(actor,'Engine.Actor','K2_GetComponentsByClass',cls) or {}
    for i=1,math.min(#list,24) do local o=unwrap(list[i]);if valid(o) then out[#out+1]=o end end
    return out
end
local function mesh(o)
    if isa(o,'Engine.SkeletalMeshComponent') then return full(read(o,'Engine.SkeletalMeshComponent','GetSkeletalMeshAsset')) end
    if isa(o,'Engine.StaticMeshComponent') then return full(unsafeProperty(o,'StaticMesh','ObjectProperty')) end
    return 'OTHER_RENDER_COMPONENT'
end
local function montage(body)
    local instance=read(body,'Engine.SkeletalMeshComponent','GetAnimInstance')
    if not valid(instance) then return {instance='NONE'} end
    local active=read(instance,'Engine.AnimInstance','GetCurrentActiveMontage')
    local out={instance=full(instance),asset=full(active)}
    out.stance=optional('native stance',function() return unsafeProperty(instance,'Stance','IntProperty') end)
    out.offhandStance=optional('offhand stance',function() return unsafeProperty(instance,'OffhandStance','IntProperty') end)
    if valid(active) then out.position=read(instance,'Engine.AnimInstance','Montage_GetPosition',active) end
    return out
end
local function row(value)
    assert(value~=nil,'No row handle returned')
    return {table=full(value.DataTable),row=value.RowName:ToString()}
end
local function attackSource(attack)
    if not valid(attack) then return {object='NONE'} end
    return {object=full(attack),row=optional('attack row',function() return row(read(attack,'Maine.Attack','GetAttackDataRowHandle')) end),
        range=optional('attack range',function() return read(attack,'Maine.Attack','GetAttackRange') end),
        chargedRange=optional('charged range',function() return read(attack,'Maine.Attack','GetChargedAttackRange') end),
        montage=optional('attack montage',function() return full(read(attack,'Maine.Attack','GetAnimMontage')) end)}
end
local function combatSources(pawn,item)
    local result={defaultAttack=optional('default attack',function() return attackSource(read(pawn,'Maine.SurvivalCharacter','GetDefaultAttack')) end)}
    result.baseUnarmedDamage=optional('default unarmed damage',function()
        local cls=read(StaticFindObject('/Script/Engine.Default__KismetSystemLibrary'),'Engine.KismetSystemLibrary','Conv_ClassToSoftClassReference',pawn:GetClass())
        assert(cls~=nil,'Native soft-class conversion unavailable')
        return read(StaticFindObject('/Script/Maine.Default__UserInterfaceStatics'),'Maine.UserInterfaceStatics','GetDefaultBaseDamageFirstAttackOfCharacter',pawn,cls)
    end)
    if valid(item) then
        result.itemRow=optional('item row',function() return row(read(item,'Maine.Item','GetItemDataRowHandle')) end)
        result.itemDamageModifier=optional('item damage modifier',function() return read(item,'Maine.Item','GetAttackDamageModifier') end)
        result.customAttackMultiplier=optional('item multiplier',function() return unsafeProperty(item,'CustomAttackMultiplier','FloatProperty') end)
        result.attacks=optional('item attack combo',function()
            local combo=unsafeProperty(item,'AttackCombo','ObjectProperty');if not valid(combo) then return {} end
            local array=unsafeProperty(combo,'Attacks','ArrayProperty');assert(array~=nil,'No attack array');local out={}
            array:ForEach(function(index,value)
                if #out>=8 then return true end
                out[#out+1]=attackSource(unwrap(value))
            end)
            return out
        end)
    end
    return result
end
local seen={};local frames=0;local polls=0;local armed=false;local stopped=false;local busy=false
local lastState=nil;local lastAttack=false;local dumpDone=false;local dumpFailed=false
local previousState=nil;local previousItem=nil
local function snapshot()
    local pawn,controller
    for i,pc in ipairs(FindAllOf('PlayerController') or {}) do
        if i>16 then break end
        if valid(pc) and pc:IsLocalController() then pawn=pc.Pawn;controller=pc;break end
    end
    if not isa(pawn,'Maine.SurvivalCharacter') then return end
    local body=unsafeProperty(pawn,'Mesh','ObjectProperty');if not valid(body) then return end
    local eq=unsafeProperty(pawn,'EquipmentComponent','ObjectProperty');if not valid(eq) then return end
    slot=slot or unsafeEnumValue('EEquipmentSlot','MainHand');offSlot=offSlot or unsafeEnumValue('EEquipmentSlot','OffHand')
    assert(slot~=nil and offSlot~=nil,'Missing actual equipment enums')
    local item=read(eq,'Maine.EquipmentComponent','GetItemInSlot',slot)
    local off=read(eq,'Maine.EquipmentComponent','GetItemInSlot',offSlot)
    if not armed and not valid(item) then return end
    armed=true;polls=polls+1
    -- Builtin's exact implementation/output naming verified at installed83330635.
    -- Dump only once, after an actual equipped item is present. No setting or
    -- gameplay writes; this writes a native type-layout .usmap diagnostic file.
    if not dumpDone then
        dumpDone=true
        if type(DumpUSMAP)=='function' then
            log('MAPPINGS BEGIN native types only; a brief pause is possible')
            local ok,why=pcall(DumpUSMAP,false)
            dumpFailed=not ok
            log(ok and 'MAPPINGS REQUEST COMPLETE; send the newly generated .usmap named in UE4SS output' or 'MAPPINGS FAILED '..tostring(why))
        else dumpFailed=true;log('MAPPINGS UNAVAILABLE: installed loader has no DumpUSMAP global') end
    end
    local fp=read(pawn,'Maine.SurvivalCharacter','GetIsFirstPerson')
    local attack=unsafeProperty(pawn,'bIsAttacking','BoolProperty')
    assert(type(fp)=='boolean' and type(attack)=='boolean','Unknown view/attack state')
    local state=full(pawn)..'|'..tostring(fp)..'|'..full(item)..'|'..full(off)
    local changed=state~=lastState or attack~=lastAttack
    if state~=lastState then
        log('SPEAR_COMBAT_SOURCE '..json(combatSources(pawn,item)))
    end
    local camera=read(pawn,'Maine.SurvivalCharacter','GetFirstPersonCamera')
    local visual=optional('item visual',function() return read(item,'Maine.Item','GetItemVisuals') end)
    if valid(visual) then
        optional('visual metadata',function()
            for _,o in ipairs(components(visual)) do
                local key=full(o)
                if not seen[key] then
                    local parent=read(o,'Engine.SceneComponent','GetAttachParent')
                    local socket=read(o,'Engine.SceneComponent','GetAttachSocketName')
                    local bounds=optional('local mesh bounds',function()
                        if not isa(o,'Engine.StaticMeshComponent') then return nil end
                        local lo,hi={},{};read(o,'Engine.StaticMeshComponent','GetLocalBounds',lo,hi)
                        return {min=vec(lo.Min or lo),max=vec(hi.Max or hi)}
                    end)
                    local record={component=key,asset=mesh(o),parent=full(parent),socket=socket:ToString(),world=world(o),localBounds=bounds}
                    log('SPEAR_COMPONENT '..json(record));seen[key]=true
                end
            end
        end)
    end
    --20Hz during attacks;2Hz resting, plus every equipment/view/state change.
    if changed or attack or polls%10==0 then
        local record={frame=frames+1,pawn=full(pawn),body=full(body),bodyAsset=mesh(body),firstPerson=fp,attack=attack,main=full(item),off=full(off),visual=full(visual)}
        record.gameTime=optional('game clock',function() return read(StaticFindObject('/Script/Engine.Default__GameplayStatics'),'Engine.GameplayStatics','GetTimeSeconds',pawn) end)
        record.camera=optional('camera transform',function() return world(camera) end)
        if state~=lastState then
            record.authority=optional('network authority',function() return read(pawn,'Engine.Actor','HasAuthority') end)
            record.cameraFov=optional('camera FOV',function() return unsafeProperty(camera,'FieldOfView','FloatProperty') end)
            record.viewport=optional('viewport',function()
                local x,y={},{};read(controller,'Engine.PlayerController','GetViewportSize',x,y)
                assert(type(x.SizeX)=='number' and type(y.SizeY)=='number','No viewport output')
                return {width=x.SizeX,height=y.SizeY}
            end)
        end
        record.animation=optional('active montage',function() return montage(body) end)
        record.currentAttack=optional('current attack',function() return attackSource(read(pawn,'Maine.SurvivalCharacter','GetCurrentAttack')) end)
        record.bodyWorld=optional('body transform',function() return world(body) end)
        record.hands={}
        for _,bone in ipairs({'r_hand_JNT','l_hand_JNT','r_wrist_JNT','l_wrist_JNT'}) do
            local point=optional(bone,function()
                if read(body,'Engine.SceneComponent','DoesSocketExist',FName(bone))~=true then return nil end
                return world(body,bone)
            end)
            record.hands[bone]=point
        end
        record.weapon={}
        if valid(visual) then
            optional('weapon frame',function()
                for _,o in ipairs(components(visual)) do record.weapon[#record.weapon+1]={component=full(o),world=world(o)} end
            end)
        end
        frames=frames+1;log('SPEAR_FRAME '..json(record))
    end
    lastState=state;lastAttack=attack
    if frames>=600 or polls>=2400 then
        stopped=true;log('COMPLETE frames='..frames..'; polls='..polls..'; mappingsFailed='..tostring(dumpFailed)..'; send UE4SS.log and new .usmap. Remove this probe after collection.')
    end
end
LoopAsync(50,function()
    if stopped then return false end
    if busy then return false end
    busy=true
    local ok,why=pcall(function()
        ExecuteInGameThread(function()
            local good,err=pcall(snapshot);busy=false
            if not good then stopped=true;log('PROBE STOP '..tostring(err)..'; no gameplay/cosmetic state was changed') end
        end)
    end)
    if not ok then busy=false;stopped=true;log('DISPATCH STOP '..tostring(why)) end
    return false
end)
log('READY: read-only spear pose/attachment/montage/type-layout probe. Equip the reference spear, stand2s, do3 FP jabs, switch TP and do3 jabs, then unequip and do2 unarmed attacks. Stop after about30s and send UE4SS.log plus newly generated .usmap. No Paks, skin changes, combat writes, hotkeys, or repeated animation-asset extraction.')
