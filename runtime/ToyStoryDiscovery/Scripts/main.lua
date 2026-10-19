-- Read-only diagnostic. No actor spawning, attachments, gameplay writes or attack calls.
local function log(s) print('[ToyStoryDiscovery] '..tostring(s)) end
local function safe(f) local ok,v=pcall(f); if ok then return v end return nil end
local function valid(o) return o and safe(function() return o:IsValid() end) end
local function label(o) return safe(function() return o:GetFullName() end) or tostring(o) end
local patterns={'equip','weapon','shield','unarmed','spear','attack','anim','montage','glid','tuft','socket','attach','firstperson','camera','visible','carry'}
local function interesting(n) n=string.lower(n); for _,p in ipairs(patterns) do if string.find(n,p,1,true) then return true end end return false end
local function inspect(o)
    log('OBJECT '..label(o)); local cls=safe(function() return o:GetClass() end);local count=0
    for depth=1,8 do
        if not valid(cls) then break end
        safe(function() cls:ForEachProperty(function(p)
            local n=safe(function() return p:GetFName():ToString() end)
            if n and interesting(n) and count<100 then
                count=count+1;local value=safe(function() return o:GetPropertyValue(n) end)
                log('PROPERTY '..n..' = '..label(value))
            end
        end) end)
        safe(function() cls:ForEachFunction(function(f)
            local n=safe(function() return f:GetFName():ToString() end)
            if n and interesting(n) and count<180 then count=count+1;log('FUNCTION (not called) '..n) end
        end) end)
        cls=safe(function() return cls:GetSuperStruct() end)
    end
end
local function snapshot()
    log('SNAPSHOT BEGIN')
    local controllers=safe(function() return FindAllOf('PlayerController') end) or {}
    for _,pc in ipairs(controllers) do
        if valid(pc) and safe(function() return pc:IsLocalController() end)==true then
            inspect(pc);local pawn=safe(function() return pc.Pawn end)
            if valid(pawn) then
                inspect(pawn)
                for _,kind in ipairs({'SkeletalMeshComponent','CameraComponent'}) do
                    local components=safe(function() return FindAllOf(kind) end) or {}
                    local total=0
                    for _,component in ipairs(components) do
                        if valid(component) and safe(function() return component:GetOwner()==pawn end) and total<12 then
                            total=total+1;inspect(component)
                            local anim=safe(function() return component:GetAnimInstance() end)
                            if valid(anim) then inspect(anim) end
                        end
                    end
                end
            else log('No valid pawn (menu/loading)') end
        end
    end
    log('SNAPSHOT END')
end
RegisterKeyBind(Key.F8,{ModifierKey.CONTROL},function() ExecuteInGameThread(snapshot) end)
log('Read-only discovery ready: Ctrl+F8 captures current local character state')
