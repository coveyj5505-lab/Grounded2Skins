-- Automatic building completion only, on the authoritative host.
local api=require('native_guard').new('FreeBuild UE57',{
 ['Engine.ActorComponent.GetOwner']={ReturnValue='ObjectProperty'},
 ['Engine.Actor.HasAuthority']={ReturnValue='BoolProperty'},
 ['Maine.SurvivalModeManagerComponent.GetGameModeSettings']={ReturnValue='ObjectProperty'},
},{bAutoCompleteBuildings={owner='Maine.SurvivalGameModeSettings',type='BoolProperty'}})
local busy=false
local function update()
    local count=0
    for i,manager in ipairs(FindAllOf('SurvivalModeManagerComponent') or {}) do
        if i>32 then break end
        if api.isa(manager,'Maine.SurvivalModeManagerComponent') and not api.full(manager):find('Default__',1,true) then
            local owner=api.call(manager,'Engine.ActorComponent','GetOwner')
            if api.valid(owner) then
                if api.call(owner,'Engine.Actor','HasAuthority')==true then
                    local settings=api.call(manager,'Maine.SurvivalModeManagerComponent','GetGameModeSettings')
                    if api.valid(settings) then
                        local old=api.field(settings,'bAutoCompleteBuildings');assert(type(old)=='boolean','Unknown building flag')
                        if not old then api.write(settings,'bAutoCompleteBuildings',true);api.log('ACTIVE building autocomplete enabled; crafting unchanged; '..api.full(manager)) end
                        count=count+1
                    end
                else api.once('client','WAIT_HOST: install FreeBuild on the host; no client-only gameplay setting writes') end
            end
        end
    end
    if count==0 then api.once('waiting','WAIT: authoritative world game-mode settings not available yet') end
end
LoopAsync(3000,function()
    if busy then return false end;busy=true
    local queued,why=pcall(function()
        ExecuteInGameThread(function()
            local ok,err=pcall(update);busy=false
            if not ok then api.once('error:'..tostring(err),'GUARDED WAIT '..tostring(err)) end
        end)
    end)
    if not queued then busy=false;api.once('dispatch:'..tostring(why),'DISPATCH WAIT '..tostring(why)) end
    return false
end)
api.log('Loaded: game-thread native building autocomplete; host authority and live bool schema required; no free crafting, inventory or Blueprint modifications')
