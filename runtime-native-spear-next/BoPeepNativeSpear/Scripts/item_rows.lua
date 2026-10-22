-- Native UDataTable deep-copy binding. Never edit the source Spear row.
-- Called on the game thread after both cooked private tables have loaded.
local M={}
M.source='/Game/Blueprints/Items/Table_AllItems.Table_AllItems'
M.items='/Game/Blueprints/Attacks/BoPkItemTbl.BoPkItemTbl'
M.attacks='/Game/Blueprints/Attacks/BoPkAttacks.BoPkAttacks'
-- Reuse an existing native row FName in our PRIVATE table. The table identity
-- distinguishes this item; no new row-name CRC needs to be invented.
M.row='Spear'
local comboNames={'AttackComboData','AlternateAttackComboData','SwimmingAttackComboData'}
local supported={Spear=true,Spear2=true,Spear3=true}
local function name(v)
    if type(v)=='string' then return v end
    assert(v and type(v.ToString)=='function','Expected native FName')
    return v:ToString()
end
local function each(array,fn)
    -- UE4SS native arrays expose reference wrappers; do not replace the array
    -- with a Lua table or keep references past an AddRow/RemoveRow operation.
    assert(array and type(array.ForEach)=='function','Expected native attack array')
    local count=0
    array:ForEach(function(_,v)
        count=count+1;assert(count<=3,'Unexpected spear combo length')
        if type(v.get)=='function' then v=v:get() end
        fn(v,count)
    end)
    return count
end
local function snapshot(row,api)
    local out={}
    for _,key in ipairs(comboNames) do
        local rows={};each(row[key].Attacks,function(h) rows[#rows+1]=api.full(h.DataTable)..':'..name(h.RowName) end)
        out[#out+1]=key..'='..table.concat(rows,',')
    end
    return table.concat(out,';')
end
function M.prepare(source,items,attacks,api)
    assert(api.full(source)=='CompositeDataTable '..M.source,'Wrong source item table')
    assert(api.full(items)=='DataTable '..M.items,'A cooked private item table is required')
    assert(api.full(attacks)=='DataTable '..M.attacks,'Wrong private attack table')
    assert(api.full(source:GetRowStruct())=='ScriptStruct /Script/Maine.BaseItemData','Wrong source row type')
    assert(api.full(items:GetRowStruct())=='ScriptStruct /Script/Maine.BaseItemData','Wrong destination row type')
    assert(api.full(attacks:GetRowStruct())=='ScriptStruct /Script/Maine.AttackData','Wrong attack row type')
    api.structFields('Maine.BaseItemData',{AttackComboData='StructProperty',AlternateAttackComboData='StructProperty',SwimmingAttackComboData='StructProperty',ThrowData='StructProperty'})
    api.structFields('Maine.AttackComboData',{Attacks='ArrayProperty'})
    api.structFields('Engine.DataTableRowHandle',{DataTable='ObjectProperty',RowName='NameProperty'})
    api.structFields('Maine.AttackData',{DamageData='StructProperty',Range='FloatProperty',ChargeTime='FloatProperty'})
    api.structFields('Maine.DamageData',{Damage='FloatProperty'})
    api.structFields('Maine.ThrowData',{bCanThrow='BoolProperty',bCanThrowUnderWater='BoolProperty'})
    for row in pairs(supported) do
        local a=assert(attacks:FindRow(row),'Private attack missing: '..row)
        assert(a.DamageData.Damage==8 and a.Range==275 and a.ChargeTime==0,'Private attack profile mismatch: '..row)
    end
    local native=assert(source:FindRow('Spear'),'Native spear row missing')
    local before=snapshot(native,api)
    -- No update/removal of a published private row: live UItem caches can hold
    -- references into it. Preparation is once per loaded table lifetime.
    assert(items:FindRow(M.row)==nil,'Private item row already exists; refuse to replace live row')
    api.log('PRIVATE ROW: native BaseItemData verified; beginning typed Spear deep copy')
    items:AddRow(M.row,native) -- installed UE4SS CopyScriptStruct, deep copy
    local ok,result=pcall(function()
        local copy=assert(items:FindRow(M.row),'Native deep copy failed')
        for _,key in ipairs(comboNames) do
            local n=each(copy[key].Attacks,function(handle)
                local row=name(handle.RowName)
                assert(supported[row],'Unsupported native attack in '..key..': '..row)
                assert(api.full(handle.DataTable)=='DataTable /Game/Blueprints/Attacks/ItemAttacks.ItemAttacks','Unexpected source attack table')
                handle.DataTable=attacks
                assert(api.full(handle.DataTable)=='DataTable '..M.attacks,'Attack handle write did not persist')
            end)
            if key=='AttackComboData' then assert(n==3,'Expected three native spear jabs') end
        end
        copy.ThrowData.bCanThrow=false
        copy.ThrowData.bCanThrowUnderWater=false
        assert(copy.ThrowData.bCanThrow==false and copy.ThrowData.bCanThrowUnderWater==false,'Throw disabling failed')
        assert(snapshot(native,api)==before,'Source spear changed during private copy')
        return {DataTable=items,RowName=FName(M.row)}
    end)
    if not ok then
        -- No native item exists yet; safe to discard this unpublished copy.
        items:RemoveRow(M.row)
        error(result)
    end
    api.log('PRIVATE ROW READY: three spear jabs use private attacks; native source row retained')
    return result
end
return M
