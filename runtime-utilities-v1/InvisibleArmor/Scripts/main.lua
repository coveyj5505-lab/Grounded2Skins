-- Hide only dedicated player armor render components; preserve all equipment stats.
local api=require('native_guard').new('InvisibleArmor UE57',{
 ['Engine.SceneComponent.IsVisible']={ReturnValue='BoolProperty'},
 ['Engine.SceneComponent.SetVisibility']={bNewVisibility='BoolProperty',bPropagateToChildren='BoolProperty'},
}, {
 HeadArmorMeshComponent={owner='Maine.SurvivalPlayerCharacter',type='ObjectProperty'},
 ChestArmorMeshComponent={owner='Maine.SurvivalPlayerCharacter',type='ObjectProperty'},
 ArmsArmorMeshComponent={owner='Maine.SurvivalPlayerCharacter',type='ObjectProperty'},
 LegsArmorMeshComponent={owner='Maine.SurvivalPlayerCharacter',type='ObjectProperty'},
})
local fields={'HeadArmorMeshComponent','ChestArmorMeshComponent','ArmsArmorMeshComponent','LegsArmorMeshComponent'}
local busy=false
local function update()
    local count=0
    for i,pawn in ipairs(FindAllOf('SurvivalPlayerCharacter') or {}) do
        if i>64 then break end
        if api.isa(pawn,'Maine.SurvivalPlayerCharacter') and not api.full(pawn):find('Default__',1,true) then
            count=count+1
            for _,name in ipairs(fields) do
                local component=api.field(pawn,name)
                if api.valid(component) then
                    if api.call(component,'Engine.SceneComponent','IsVisible') then
                        api.call(component,'Engine.SceneComponent','SetVisibility',false,false)
                        assert(api.call(component,'Engine.SceneComponent','IsVisible')==false,'Armor visibility readback mismatch '..name)
                    end
                end
            end
        end
    end
    if count>0 then api.once('active','ACTIVE: player head/chest/arms/legs armor render components hidden locally; native stats, items, character skins and SCAB unchanged')
    else api.once('waiting','WAIT: no gameplay SurvivalPlayerCharacter found yet') end
end
LoopAsync(250,function()
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
api.log('Loaded: render-only armor hiding; remove old zInvisibleArmor_P pak/utoc/ucas before use; no body/head skin mesh, SCAB, equipment or combat changes')
