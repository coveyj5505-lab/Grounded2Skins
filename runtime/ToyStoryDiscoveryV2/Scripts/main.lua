-- Staged metadata ONLY. No arbitrary property values, gameplay writes or event hooks.
-- Native access violations cannot be caught by Lua; this is not Windows-validated.
local PREFIX='[ToyStoryDiscoveryV2] '
local function log(s) print(PREFIX..s..'\n') end
local busy=false
local nextDepth=-1
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
local function step()
    log('STEP BEGIN depth='..nextDepth)
    local pawn=localPawn()
    if pawn==nil then log('STEP END no pawn; stage unchanged');return end
    if nextDepth<0 then
        nextDepth=0
        log('STEP END identity complete. Next press lists immediate-class property names only.')
        return
    end
    if nextDepth>=8 then log('STEP END depth limit reached. Send log; no more presses needed.');return end
    local cls=native('pawn.GetClass',function() return pawn:GetClass() end)
    for depth=1,nextDepth do
        if not valid(cls,'class') then log('STEP END hierarchy exhausted');nextDepth=8;return end
        cls=native('class.GetSuperStruct '..depth,function() return cls:GetSuperStruct() end)
    end
    if not valid(cls,'target class') then log('STEP END hierarchy exhausted');nextDepth=8;return end
    local className=native('class.GetFullName',function() return cls:GetFullName() end)
    log('CLASS '..className)
    local count=0
    native('class.ForEachProperty',function()
        cls:ForEachProperty(function(property)
            count=count+1
            -- Property descriptor only: do NOT call pawn:GetPropertyValue or inspect its value.
            local name=native('property descriptor '..count..'.GetFullName',function() return property:GetFullName() end)
            log('PROPERTY METADATA '..name)
            if count>=128 then return true end
        end)
    end)
    nextDepth=nextDepth+1
    log('STEP END metadata count='..count..'; next depth='..nextDepth)
end
RegisterKeyBind(Key.F9,{ModifierKey.CONTROL},function()
    if busy then log('BUSY: wait for STEP END');return end
    busy=true
    log('KEY Ctrl+F9; requesting one game-thread step')
    local ok,err=pcall(function()
        ExecuteInGameThread(function()
            log('GAME THREAD ENTER')
            local success,why=pcall(step)
            if not success then log('STEP ERROR '..tostring(why)) end
            busy=false
        end)
    end)
    if not ok then busy=false;log('DISPATCH LUA ERROR '..tostring(err)) end
end)
log('Loaded. Ctrl+F9: first press identity, later presses one class of PROPERTY NAMES ONLY. No glide recording yet.')
