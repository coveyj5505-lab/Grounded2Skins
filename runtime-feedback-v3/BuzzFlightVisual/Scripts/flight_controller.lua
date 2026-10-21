-- Prepared flight-visual transaction controller, NOT an installed UE4SS mod.
-- Adapter must execute on the game thread and only manipulate cosmetic
-- components / native render visibility. No actor, camera or movement writes.
local M={}
function M.new(adapter,asset)
    assert(type(asset)=='string' and asset~='','Exact private flight asset required')
    for _,name in ipairs({'valid','createHiddenVisual','destroyVisual','setVisibility','getVisibility','log'}) do
        assert(type(adapter[name])=='function','Missing adapter function '..name)
    end
    local self={visual=nil,owner=nil,body=nil,suppressed={},restorePending=false,active=false}
    local function restore()
        local pending={}
        for _,entry in ipairs(self.suppressed) do
            if adapter.valid(entry.component) then
                local ok,why=pcall(adapter.setVisibility,entry.component,entry.visible,'restore')
                if not ok then pending[#pending+1]=entry;adapter.log('RESTORE RETRY '..tostring(why)) end
            end
        end
        self.suppressed=pending;self.restorePending=#pending>0;self.active=false
        return not self.restorePending
    end
    function self.stop()
        -- Hide the visual before restoring the complete native presentation.
        if adapter.valid(self.visual) then
            local ok,why=pcall(adapter.setVisibility,self.visual,false,'visual')
            if not ok then adapter.log('PROXY HIDE ERROR '..tostring(why)) end
            local destroyed,err=pcall(adapter.destroyVisual,self.visual)
            if not destroyed then adapter.log('PROXY DESTROY RETRY '..tostring(err));self.visualCleanupPending=true else self.visual=nil;self.visualCleanupPending=false end
        else self.visual=nil;self.visualCleanupPending=false end
        local restored=restore();self.owner=nil;self.body=nil
        return restored and not self.visualCleanupPending
    end
    local function sameComponents(snapshot)
        local current={}
        for _,c in ipairs(snapshot.bodies or {}) do current[c]=true end
        for _,c in ipairs(snapshot.wings or {}) do current[c]=true end
        for _,c in ipairs(snapshot.tufts or {}) do current[c]=true end
        for _,entry in ipairs(self.suppressed) do if not current[entry.component] then return false end;current[entry.component]=nil end
        return next(current)==nil
    end
    function self.tick(snapshot)
        assert(type(snapshot)=='table','Read-only state snapshot required')
        if self.restorePending or self.visualCleanupPending then
            if not self.stop() then return false,'RESTORATION_PENDING' end
        end
        -- Cosmetic manual wing preference deliberately has no role here.
        local eligible=snapshot.isBuzz==true and snapshot.isGliding==true and snapshot.isFirstPerson==false
            and adapter.valid(snapshot.owner) and adapter.valid(snapshot.body)
        if not eligible then self.stop();return false,'NATIVE_PRESENTATION' end
        if self.owner~=snapshot.owner or self.body~=snapshot.body or (self.active and not sameComponents(snapshot)) then
            if not self.stop() then return false,'RESTORATION_PENDING' end
        end
        if self.active and not adapter.valid(self.visual) then
            if not self.stop() then return false,'RESTORATION_PENDING' end
        end
        if self.active then
            -- The independent wing mod can change its mesh/visibility on the
            -- same glide transition. Reassert suppression after that update;
            -- preserve the original rollback snapshot rather than recapturing.
            local ok,why=pcall(function()
                for _,entry in ipairs(self.suppressed) do
                    if adapter.getVisibility(entry.component)~=false then adapter.setVisibility(entry.component,false,'suppress') end
                end
                if adapter.getVisibility(self.visual)~=true then adapter.setVisibility(self.visual,true,'visual') end
            end)
            if not ok then adapter.log('FLIGHT FALLBACK '..tostring(why));self.stop();return false,'FALLBACK' end
            return true,'FLIGHT_VISUAL'
        end
        local ok,why=pcall(function()
            self.owner=snapshot.owner;self.body=snapshot.body
            -- Loading, creation, attachment, collision-off configuration and
            -- expected-asset verification must all succeed before any native
            -- visibility changes. Adapter returns a hidden independent visual.
            self.visual=adapter.createHiddenVisual(asset,snapshot.owner,snapshot.body)
            assert(adapter.valid(self.visual),'Flight visual creation failed')
            local seen={};local captured={}
            for _,list in ipairs({snapshot.bodies or {},snapshot.wings or {},snapshot.tufts or {}}) do
                for _,component in ipairs(list) do
                    assert(adapter.valid(component),'Invalid native component before suppression')
                    if not seen[component] then
                        seen[component]=true;local v=adapter.getVisibility(component)
                        assert(type(v)=='boolean','Unknown prior visibility')
                        captured[#captured+1]={component=component,visible=v}
                    end
                end
            end
            assert(seen[snapshot.body],'Main native body must be included in restoration set')
            -- Store the complete rollback set BEFORE the first native write.
            self.suppressed=captured
            for _,entry in ipairs(captured) do adapter.setVisibility(entry.component,false,'suppress') end
            adapter.setVisibility(self.visual,true,'visual');self.active=true
        end)
        if not ok then adapter.log('FLIGHT FALLBACK '..tostring(why));self.stop();return false,'FALLBACK' end
        return true,'FLIGHT_VISUAL'
    end
    return self
end
return M
