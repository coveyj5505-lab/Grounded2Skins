-- Single-shot wrapper identification only. NO reflected gameplay getter invocation.
local function log(s) print('[ToyStoryObjectAccess] '..s..'\n') end
local busy=false
local done=false
local function attempt(label,fn)
    log('BEFORE '..label)
    local ok,value=pcall(fn)
    if not ok then log('LUA ERROR '..label..': '..tostring(value));return false,nil end
    log('AFTER '..label)
    return true,value
end
local function member(o,name)
    if o==nil then return nil end
    local ok,value=pcall(function() return o[name] end)
    if ok then return value end
end
local function describe(label,o)
    log('VALUE '..label..' LuaType='..type(o))
    if type(o)~='table' and type(o)~='userdata' then
        if type(o)=='string' or type(o)=='boolean' or type(o)=='number' then log('SCALAR '..label..' '..tostring(o)) end
        return
    end
    local methods={'type','IsValid','GetFullName','GetClass','IsA','get','GetPropertyValue','GetPropertyClass'}
    for _,name in ipairs(methods) do log('METHOD '..label..'.'..name..' LuaType='..type(member(o,name))) end
    local tag=member(o,'type')
    if type(tag)=='function' then
        local ok,value=attempt(label..':type()',function() return tag(o) end)
        if ok and type(value)=='string' then log('WRAPPER '..label..' = '..value) end
    end
    local valid=member(o,'IsValid')
    if type(valid)=='function' then
        local ok,value=attempt(label..':IsValid()',function() return valid(o) end)
        if not ok or value~=true then log('NOT VALID '..label);return end
    else return end
    local full=member(o,'GetFullName')
    if type(full)=='function' then
        local ok,value=attempt(label..':GetFullName()',function() return full(o) end)
        if ok and type(value)=='string' then log('IDENTITY '..label..' = '..value) end
    end
end
local function snapshot()
    log('BEGIN single-shot wrapper check; no actions required')
    local controllers=FindAllOf('PlayerController') or {}
    for i,pc in ipairs(controllers) do
        if i>16 then break end
        if pc:IsValid() and pc:IsLocalController() then
            local pawn=pc.Pawn
            if pawn and pawn:IsValid() then
                describe('pawn_V2_direct',pawn)
                for _,name in ipairs({'CharMovementComponent','EquipmentComponent'}) do
                    local ok,metadata=attempt(name..' descriptor',function() return pawn:Reflection():GetProperty(name) end)
                    if ok then describe(name..'.descriptor',metadata) end
                    local got,value=attempt(name..' GetPropertyValue',function() return pawn:GetPropertyValue(name) end)
                    if got then describe(name..'.GetPropertyValue',value) end
                    local direct,value2=attempt(name..' direct __index',function() return pawn[name] end)
                    if direct then describe(name..'.direct',value2) end
                end
                done=true;log('END complete; save UE4SS.log. No gameplay sequence needed.');return
            end
        end
    end
    log('No local pawn; load a save and press F9 again.')
end
RegisterKeyBind(Key.F9,function()
    if done then log('Already complete. Send UE4SS.log; no repeat needed.');return end
    if busy then return end
    busy=true
    local ok,why=pcall(function()
        ExecuteInGameThread(function()
            local success,reason=pcall(snapshot);busy=false
            if not success then log('SNAPSHOT LUA ERROR '..tostring(reason)) end
        end)
    end)
    if not ok then busy=false;log('DISPATCH ERROR '..tostring(why)) end
end)
log('Loaded. Stand still in loaded save, press F9 ONCE. No attacks, equipment changes or gliding.')
