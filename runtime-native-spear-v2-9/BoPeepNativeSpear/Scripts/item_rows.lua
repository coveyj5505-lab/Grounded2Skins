-- V2 requires an OFFLINE COOKED item row. No runtime struct copy or AddRow.
local M={}
M.source='/Game/Blueprints/Items/Table_AllItems.Table_AllItems'
M.items='/Game/Blueprints/Attacks/BoPkItemTbl.BoPkItemTbl'
M.attacks='/Game/Blueprints/Attacks/BoPkAttacks.BoPkAttacks'
M.row='RivetBoPeepCrook'
local function name(v) return type(v)=='string' and v or v:ToString() end
function M.prepare(_,items,attacks,api)
    assert(api.full(items)=='DataTable '..M.items,'Wrong private item table')
    assert(api.full(attacks)=='DataTable '..M.attacks,'Wrong private attack table')
    assert(api.full(items:GetRowStruct())=='ScriptStruct /Script/Maine.BaseItemData','Wrong item row struct')
    assert(api.full(attacks:GetRowStruct())=='ScriptStruct /Script/Maine.AttackData','Wrong attack row struct')
    local item=assert(items:FindRow(M.row),'Cooked item row missing. V1 empty-table asset is incompatible; replace all three zBoCrookNativeUE57_P asset files with V2.')
    api.structFields('Maine.BaseItemData',{AttackComboData='StructProperty',ThrowData='StructProperty'})
    api.structFields('Maine.AttackComboData',{Attacks='ArrayProperty'})
    local n=0
    item.AttackComboData.Attacks:ForEach(function(_,wrapped)
        n=n+1;assert(n<=3,'Unexpected native combo size')
        local h=api.unwrap(wrapped)
        assert(api.full(h.DataTable)=='DataTable '..M.attacks,'Cooked crook references an ordinary spear attack table')
        assert(name(h.RowName)==({'RivetCrookJab1','RivetCrookJab2','RivetCrookJab3'})[n],'Unexpected cooked jab order')
        local a=assert(attacks:FindRow(name(h.RowName)),'Missing private jab')
        assert(a.DamageData.Damage==8 and a.Range==275 and a.ChargeTime==0,'Wrong cooked jab profile')
    end)
    assert(n==3 and item.ThrowData.bCanThrow==false and item.ThrowData.bCanThrowUnderWater==false,'Invalid normal-jab-only cooked item')
    api.log('COOKED ITEM VERIFIED: no runtime struct copy; native damage8/range275/no-charge profiles')
    return {DataTable=items,RowName=FName(M.row)}
end
return M
