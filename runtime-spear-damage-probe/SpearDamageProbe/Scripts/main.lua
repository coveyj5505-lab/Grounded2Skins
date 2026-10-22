-- One-shot read-only damage-table inspection. No attacks or mappings dump needed.
local api=require('native_guard').new('SpearDamageProbe',{
 ['Engine.KismetSystemLibrary.MakeSoftObjectPath']={PathString='StrProperty',ReturnValue='StructProperty'},
 ['Engine.KismetSystemLibrary.Conv_SoftObjPathToSoftObjRef']={SoftObjectPath='StructProperty',ReturnValue='SoftObjectProperty'},
 ['Engine.KismetSystemLibrary.LoadAsset_Blocking']={Asset='SoftObjectProperty',ReturnValue='ObjectProperty'},
 ['Engine.DataTableFunctionLibrary.GetDataTableRowNames']={Table='ObjectProperty',OutRowNames='ArrayProperty'},
 ['Engine.DataTableFunctionLibrary.GetDataTableColumnAsString']={DataTable='ObjectProperty',PropertyName='NameProperty',ReturnValue='ArrayProperty'},
}, {})
local rows=require('damage_rows')
local function values(array)
    local out={}
    local function add(v)
        assert(#out<8192,'Table row bound exceeded')
        v=api.unwrap(v)
        if type(v)=='string' then out[#out+1]=v else assert(v and type(v.ToString)=='function','Expected string/name row data');out[#out+1]=v:ToString() end
    end
    if type(array)=='table' then for _,v in ipairs(array) do add(v) end
    else assert(array and type(array.ForEach)=='function','Missing native array iterator');array:ForEach(function(_,v) add(v) end) end
    return out
end
local function loadTable(path)
    local existing=StaticFindObject(path)
    if api.valid(existing) then assert(api.isa(existing,'Engine.DataTable'),'Wrong table class');return existing end
    local system=StaticFindObject('/Script/Engine.Default__KismetSystemLibrary')
    local softPath=api.call(system,'Engine.KismetSystemLibrary','MakeSoftObjectPath',path)
    local soft=api.call(system,'Engine.KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef',softPath)
    local table_=api.call(system,'Engine.KismetSystemLibrary','LoadAsset_Blocking',soft)
    assert(api.valid(table_) and api.isa(table_,'Engine.DataTable'),'Could not load attack table '..path)
    return table_
end
local function collect(path,wanted)
    local table_=loadTable(path)
    local library=StaticFindObject('/Script/Engine.Default__DataTableFunctionLibrary')
    local out={};api.call(library,'Engine.DataTableFunctionLibrary','GetDataTableRowNames',table_,out)
    local names=values(out);local columns={}
    for _,field in ipairs({'DamageData','ChargedDamageData','PerfectChargedDamageData'}) do
        columns[field]=values(api.call(library,'Engine.DataTableFunctionLibrary','GetDataTableColumnAsString',table_,FName(field)))
    end
    local selected=rows.select(names,columns,wanted)
    local check={};api.call(library,'Engine.DataTableFunctionLibrary','GetDataTableRowNames',table_,check)
    check=values(check);assert(#check==#names,'Table changed during read')
    for i,n in ipairs(names) do assert(check[i]==n,'Table order changed during read') end
    for _,name in ipairs(wanted) do
        local r=selected[name]
        if r then api.log(string.format('NATIVE_DAMAGE table=%s row=%s normal=%.9g charged=%.9g perfect=%.9g',path,name,r.DamageData,r.ChargedDamageData,r.PerfectChargedDamageData))
        else api.log('ROW_ABSENT table='..path..' row='..name) end
    end
    return selected
end
local busy,done=false,false
LoopAsync(2000,function()
    if done or busy then return false end
    busy=true
    local queued,why=pcall(function()
        ExecuteInGameThread(function()
            local ok,err=pcall(function()
                local ready=false
                for i,p in ipairs(FindAllOf('SurvivalPlayerCharacter') or {}) do
                    if i>64 then break end
                    if api.isa(p,'Maine.SurvivalPlayerCharacter') and not api.full(p):find('Default__',1,true) then ready=true;break end
                end
                if not ready then api.once('waiting','WAIT: load a world, any character; no attacks needed');return end
                -- Do not repeat failed native reads indefinitely.
                done=true
                local fists=collect('/Game/Blueprints/Attacks/CreatureAttacks.CreatureAttacks',{'Player','Player2','Player3'})
                local spears=collect('/Game/Blueprints/Attacks/ItemAttacks.ItemAttacks',{'Spear','Spear2','Spear3'})
                local compatible,multiplier=pcall(rows.uniformMultiplier,fists.Player,spears)
                api.log(compatible and ('UNIFORM_MULTIPLIER_CANDIDATE '..tostring(multiplier)..'; read-only, NOT applied') or ('PER_ATTACK_REQUIRED '..tostring(multiplier)))
                api.log('COMPLETE: send UE4SS.log; no target, attacks, screenshots or new .usmap needed. Remove probe afterward.')
            end)
            busy=false
            if not ok then done=true;api.log('STOP '..tostring(err)..'; no combat/equipment changes made') end
        end)
    end)
    if not queued then done=true;busy=false;api.log('DISPATCH STOP '..tostring(why)) end
    return false
end)
api.log('READY: one-shot native damage rows only; load any character and wait several seconds. Read-only; no inventory, damage, movement, camera or save writes.')
