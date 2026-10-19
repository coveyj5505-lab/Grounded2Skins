-- AccessoryCheck2.0: source-backed no-Reflection workaround; read-only exact SDK getter validation; NO camera/mesh/visibility/combat writes.
local function log(s) print('[ToyStoryAccessoryCheck] '..s..'\n') end
local function valid(o) return o~=nil and o:IsValid() end
local function full(o) if valid(o) then return o:GetFullName() end return 'NONE' end
local signatures={};local enums={};local busy=false;local recording=false
local untilTime=0;local sequence=0;local lastState=nil;local fault=false
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
-- Optional Lua failures disable only that getter/property, never sibling lanes.
-- Native access violations cannot be contained by pcall.
local disabled={}
local function optional(key,fn)
    if disabled[key] then return nil end
    local ok,value=pcall(fn)
    if ok then return value end
    disabled[key]=true;log('LANE DISABLED '..key..': '..tostring(value));return nil
end
local function call(o,class,method,expected,...)
    local args=table.pack(...)
    return optional('getter '..class..'.'..method,function() return unsafeCall(o,class,method,expected,table.unpack(args,1,args.n)) end)
end
local function property(o,name,expected)
    return optional('property '..name,function() return unsafeProperty(o,name,expected) end)
end
local function enumValue(name,leaf)
    return optional('enum '..name..'.'..leaf,function() return unsafeEnumValue(name,leaf) end)
end
local function itemName(item)
    return optional('item identity',function() return full(item) end) or 'UNAVAILABLE'
end
local function pawn()
    local controllers=FindAllOf('PlayerController') or {}
    for i,pc in ipairs(controllers) do
        if i>16 then break end
        if valid(pc) and pc:IsLocalController() then
            local p=pc.Pawn;if valid(p) then return p end
        end
    end
end
local boolret={ReturnValue='BoolProperty'}
local enumret={ReturnValue='EnumProperty|ByteProperty'}
local objret={ReturnValue='ObjectProperty'}
local function scalar(v) if type(v)=='boolean' or type(v)=='number' then return tostring(v) end return 'UNAVAILABLE' end
local scriptSource=debug.getinfo(1,'S').source
local scriptPath=scriptSource:sub(1,1)=='@' and scriptSource:sub(2) or nil
local scriptDir=scriptPath and scriptPath:match('^(.*[/\\])')
local lastReadiness=nil
local function readiness(equipmentReady,glideReady)
    local status=equipmentReady and (glideReady and 'READY' or 'PARTIAL READY: EQUIPMENT ONLY') or (glideReady and 'PARTIAL READY: GLIDE ONLY' or 'STOP: NO VERIFIED STATE VALUES')
    if status==lastReadiness then return end
    lastReadiness=status;log('READINESS '..status)
    if scriptDir then
        local ok=pcall(function()
            local f=io.open(scriptDir..'AccessoryCheck-status.txt','w')
            if f then
                f:write(status..'\nEquipment getter values: '..tostring(equipmentReady)..'\nGlide getter value: '..tostring(glideReady)..'\nIf READY, continue the equipment/attack/glide sequence within3minutes. PARTIAL: collect only the working lane. STOP: send UE4SS.log without repeating gameplay.\n')
                f:close()
            end
        end)
        if not ok then log('Status file unavailable; READINESS remains in UE4SS.log') end
    end
end
local function sample(force)
    local p=pawn();if not p then log('WAIT local pawn unavailable');return end
    local movement=property(p,'CharMovementComponent','ObjectProperty')
    local equipment=property(p,'EquipmentComponent','ObjectProperty')
    local glide=call(movement,'Maine.MaineCharMovementComponent','IsGliding',boolret)
    local style=call(movement,'Maine.MaineCharMovementComponent','GetGlidingStyle',enumret)
    local main=property(equipment,'bHasMainHand','BoolProperty')
    local off=property(equipment,'bHasOffHand','BoolProperty')
    local first=call(p,'Maine.SurvivalCharacter','GetIsFirstPerson',boolret) -- future FP/TP placement only; crook remains visible
    local stance=call(equipment,'Maine.EquipmentComponent','GetStance',{ReturnValue='IntProperty'})
    local offstance=call(equipment,'Maine.EquipmentComponent','GetOffhandStance',{ReturnValue='IntProperty'})
    local attacking=property(p,'bIsAttacking','BoolProperty')
    local charging=property(p,'bIsChargingAttack','BoolProperty')
    local state={'pawn='..full(p),'gliding='..scalar(glide),'glideStyle='..scalar(style),
        'main='..scalar(main),'off='..scalar(off),'first='..scalar(first),
        'stance='..scalar(stance),'offstance='..scalar(offstance),'attacking='..scalar(attacking),'charging='..scalar(charging)}
    for _,slot in ipairs({'MainHand','OffHand'}) do
        local value=enumValue('EEquipmentSlot',slot)
        if value~=nil then
            local item=call(equipment,'Maine.EquipmentComponent','GetItemInSlot',{Slot='EnumProperty|ByteProperty',ReturnValue='ObjectProperty'},value)
            state[#state+1]=slot..'='..itemName(item)
        end
    end
    if attacking==true or charging==true then
        local attack=call(p,'Maine.SurvivalCharacter','GetCurrentAttack',objret)
        local montage=call(attack,'Maine.Attack','GetAnimMontage',objret)
        state[#state+1]='attackMontage='..itemName(montage)
    end
    readiness(type(main)=='boolean' and type(off)=='boolean',type(glide)=='boolean')
    local line=table.concat(state,' | ')
    if force or line~=lastState then sequence=sequence+1;log('STATE '..sequence..' '..line);lastState=line end
end
local function run(fn)
    if busy then return end
    busy=true
    local ok,err=pcall(function()
        ExecuteInGameThread(function()
            local success,why=pcall(fn);busy=false
            if not success then fault=true;recording=false;log('STOP LUA ERROR '..tostring(why)) end
        end)
    end)
    if not ok then busy=false;fault=true;recording=false;log('STOP DISPATCH ERROR '..tostring(err)) end
end
RegisterKeyBind(Key.F9,function()
    if recording then recording=false;log('RECORDING STOP requested');return end
    if fault then log('Recording stopped after an error. Preserve log.');return end
    recording=true;untilTime=os.time()+180;log('RECORDING START 180seconds; F9alone, no airborne keypresses needed')
    run(function() sample(true) end)
end)
LoopAsync(500,function()
    if fault then return true end
    if recording and os.time()>=untilTime then recording=false;log('RECORDING COMPLETE 180seconds') end
    if recording then run(function() sample(false) end) end
    return false
end)
log('Loaded v2.0 (NO Reflection; native class metadata; isolated getters). F9 starts/stops read-only automatic targeted recording. No first-person retest or rendering changes.')
