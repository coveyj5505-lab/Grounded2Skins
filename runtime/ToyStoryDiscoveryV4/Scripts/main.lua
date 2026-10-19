-- Metadata-gated scalar snapshots. No arrays, delegates, structs or arbitrary object values.
-- Native access violations cannot be caught by Lua; this is not Windows-validated.
local PREFIX='[ToyStoryDiscoveryV4] '
local function log(s) print(PREFIX..s..'\n') end
local busy=false
local cached={}
local snapshotId=0
local function native(tag,fn)
    log('BEFORE '..tag)
    local ok,result=pcall(fn)
    if not ok then log('LUA ERROR '..tag..': '..tostring(result));error('Step aborted') end
    log('AFTER '..tag)
    return result
end
local function valid(o,tag)
    if o==nil then return false end
    return native(tag..'.IsValid',function() return o:IsValid() end)==true
end
local function localPawn()
    local controllers=native('FindAllOf PlayerController',function() return FindAllOf('PlayerController') end) or {}
    for i,pc in ipairs(controllers) do
        if i>16 then break end
        if valid(pc,'controller '..i) and native('controller.IsLocalController',function() return pc:IsLocalController() end)==true then
            local pawn=native('controller.Pawn',function() return pc.Pawn end)
            if valid(pawn,'pawn') then
                local name=native('pawn.GetFullName',function() return pawn:GetFullName() end)
                log('PAWN '..name)
                return pawn
            end
        end
    end
    log('No local pawn; load a save before trying again.')
    return nil
end
local allowed={BoolProperty=true,ByteProperty=true,IntProperty=true,Int64Property=true,FloatProperty=true,DoubleProperty=true}
local needles={'glid','tuft','equip','unarmed','weapon','shield','attack','crouch','fall','movemode','movementmode','jump','sitting','sprint','camera','combat','carry','parachute'}
local function relevant(n)
    n=string.lower(n)
    for _,term in ipairs(needles) do if string.find(n,term,1,true) then return true end end
    return false
end
local function discover(pawn,scope)
    local cls=native('pawn.GetClass',function() return pawn:GetClass() end)
    local identity=native('pawn class.GetFullName',function() return cls:GetFullName() end)
    local cacheKey=scope..'|'..identity
    if cached[cacheKey] then return cached[cacheKey] end
    local found={};local seen={}
    for depth=0,7 do
        if not valid(cls,'class '..depth) then break end
        local name=native('class.GetFullName '..depth,function() return cls:GetFullName() end)
        log('CLASS '..name)
        local count=0
        native('class.ForEachProperty '..depth,function()
            cls:ForEachProperty(function(p)
                count=count+1
                local full=native('descriptor '..depth..'/'..count,function() return p:GetFullName() end)
                log('METADATA '..full)
                local typ,leaf=string.match(full,'^(%S+)%s+.*:([^:]+)$')
                if typ and leaf and allowed[typ] and (scope~='player' or relevant(leaf)) and not seen[leaf] and #found<128 then
                    seen[leaf]=true;table.insert(found,{name=leaf,kind=typ})
                end
                if count>=512 then log('TRUNCATED class descriptor cap=512');return true end
            end)
        end)
        cls=native('class.GetSuperStruct '..depth,function() return cls:GetSuperStruct() end)
    end
    cached[cacheKey]=found
    log('DISCOVERY END scope='..scope..' scalar candidates='..#found)
    return found
end
local function readScalars(object,scope)
    local fields=discover(object,scope)
    for _,field in ipairs(fields) do
        local value=native('READ SCALAR '..scope..'.'..field.name,function() return object:GetPropertyValue(field.name) end)
        local t=type(value)
        if t=='number' or t=='boolean' then
            log('VALUE '..scope..'.'..field.name..' = '..tostring(value))
        elseif t=='nil' then log('UNAVAILABLE '..scope..'.'..field.name)
        else log('SKIPPED NONSCALAR '..scope..'.'..field.name..' Lua type='..t) end
    end
end
local function snapshot()
    log('SNAPSHOT BEGIN')
    local pawn=localPawn()
    if not pawn then log('SNAPSHOT END no pawn');return end
    snapshotId=snapshotId+1
    log('SNAPSHOT ID '..snapshotId..' (state identified by your test order)')
    log('SCOPE player')
    readScalars(pawn,'player')
    -- These TWO ObjectProperty names were observed in the user's V3 runtime metadata.
    -- No arbitrary object traversal or equipment item/container conversion.
    for _,name in ipairs({'CharMovementComponent','EquipmentComponent'}) do
        log('SCOPE '..name)
        local component=native('READ VERIFIED COMPONENT '..name,function() return pawn:GetPropertyValue(name) end)
        if valid(component,name) then
            local full=native(name..'.GetFullName',function() return component:GetFullName() end)
            log('COMPONENT '..name..' = '..full)
            readScalars(component,name)
        else log('UNAVAILABLE COMPONENT '..name) end
    end
    log('SNAPSHOT END id='..snapshotId)
end
RegisterKeyBind(Key.F9,function()
    if busy then log('BUSY: wait for SNAPSHOT END');return end
    busy=true
    log('KEY F9; requesting game-thread snapshot')
    local ok,err=pcall(function()
        ExecuteInGameThread(function()
            local success,why=pcall(snapshot)
            if not success then log('SNAPSHOT ERROR '..tostring(why)) end
            busy=false
        end)
    end)
    if not ok then busy=false;log('DISPATCH LUA ERROR '..tostring(err)) end
end)
log('Loaded. F9 ALONE. First snapshot discovers player/movement/equipment metadata, then reads typed bool/numeric fields only. No gameplay changes. Windows validation pending.')
