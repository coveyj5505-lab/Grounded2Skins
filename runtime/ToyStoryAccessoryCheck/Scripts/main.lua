-- AccessoryCheck1.1: read-only exact SDK getter validation; NO camera/mesh/visibility/combat writes.
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
local function call(o,class,method,expected,...)
    if not valid(o) or not signature(class,method,expected) then return nil end
    -- This Beta returned nil for UObject:IsA. Use the class methods proven by V2.
    local cls=checked('receiver.GetClass '..class,function() return o:GetClass() end)
    local match=false
    for depth=0,11 do
        if not valid(cls) then break end
        local name=cls:GetFullName()
        if name:match('^%S+ (.+)$')=='/Script/'..class then match=true;break end
        cls=checked('receiver.GetSuperStruct '..depth,function() return cls:GetSuperStruct() end)
    end
    if not match then log('REJECTED RECEIVER '..class..'.'..method);return nil end
    local args={...}
    return checked('CALL '..class..'.'..method,function() return o[method](o,table.unpack(args)) end)
end
local function property(o,name,expected)
    if not valid(o) then return nil end
    local p=checked('metadata '..name,function() return o:Reflection():GetProperty(name) end)
    if not valid(p) then log('MISSING PROPERTY '..name);return nil end
    local description=p:GetFullName();local typ=description:match('^(%S+)')
    if typ~=expected then log('PROPERTY TYPE REJECTED '..name..' '..tostring(typ));return nil end
    return checked('READ '..name,function() return o:GetPropertyValue(name) end)
end
local function enumValue(name,leaf)
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
local function sample(force)
    local p=pawn();if not p then log('WAIT local pawn unavailable');return end
    local movement=property(p,'CharMovementComponent','ObjectProperty')
    local equipment=property(p,'EquipmentComponent','ObjectProperty')
    local glide=call(movement,'Maine.MaineCharMovementComponent','IsGliding',boolret)
    local style=call(movement,'Maine.MaineCharMovementComponent','GetGlidingStyle',enumret)
    local main=property(equipment,'bHasMainHand','BoolProperty')
    local off=property(equipment,'bHasOffHand','BoolProperty')
    local first=call(p,'Maine.SurvivalCharacter','GetIsFirstPerson',boolret) -- future accessory suppression only
    local stance=call(equipment,'Maine.EquipmentComponent','GetStance',{ReturnValue='IntProperty'})
    local offstance=call(equipment,'Maine.EquipmentComponent','GetOffhandStance',{ReturnValue='IntProperty'})
    local attacking=property(p,'bIsAttacking','BoolProperty')
    local state={'pawn='..full(p),'gliding='..scalar(glide),'glideStyle='..scalar(style),
        'main='..scalar(main),'off='..scalar(off),'first='..scalar(first),
        'stance='..scalar(stance),'offstance='..scalar(offstance),'attacking='..scalar(attacking)}
    for _,slot in ipairs({'MainHand','OffHand'}) do
        local value=enumValue('EEquipmentSlot',slot)
        if value~=nil then
            local item=call(equipment,'Maine.EquipmentComponent','GetItemInSlot',{Slot='EnumProperty|ByteProperty',ReturnValue='ObjectProperty'},value)
            state[#state+1]=slot..'='..full(item)
        end
    end
    if attacking==true then
        local attack=call(p,'Maine.SurvivalCharacter','GetCurrentAttack',objret)
        local montage=call(attack,'Maine.Attack','GetAnimMontage',objret)
        state[#state+1]='attackMontage='..full(montage)
    end
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
log('Loaded v1.1 (no IsA dependency). F9 starts/stops read-only automatic targeted recording. No first-person retest or rendering changes.')
