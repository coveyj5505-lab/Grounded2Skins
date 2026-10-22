-- Pure attack-table normalization. Never assumes a helper's zero is fist damage.
-- No object writes or row-struct CustomThunk calls. Used by the native spear preparation.
local M={}
local function text(value)
    if type(value)=='string' then return value end
    assert(value~=nil,'Missing table value')
    if type(value.get)=='function' then value=value:get() end
    if type(value)=='string' then return value end
    assert(type(value.ToString)=='function','Expected native string/name')
    return value:ToString()
end
function M.damage(value)
    local s=text(value);assert(#s<65536,'Oversized damage field')
    -- FDamageData exported as (Damage=..., ...). Match the exact field, not
    -- ChargedDamage, DamageMultiplier, nested status metadata or a substring.
    local values={}
    for key,n in s:gmatch('([%a_][%w_]*)%s*=%s*([%+%-]?[%d%.]+[eE]?[%+%-]?%d*)') do
        if key=='Damage' then values[#values+1]=tonumber(n) end
    end
    assert(#values==1,'Expected exactly one Damage field')
    local v=values[1]
    assert(type(v)=='number' and v==v and math.abs(v)<math.huge and v>=0,'Invalid native damage')
    return v
end
function M.select(names,columns,wanted)
    assert(type(names)=='table' and #names>0 and #names<=8192,'Invalid row names')
    local index={}
    for i,name in ipairs(names) do
        local n=text(name);assert(not index[n],'Duplicate row name');index[n]=i
    end
    for _,key in ipairs({'DamageData','ChargedDamageData','PerfectChargedDamageData'}) do
        assert(type(columns[key])=='table' and #columns[key]==#names,'Mismatched column '..key)
    end
    local rows={}
    for _,name in ipairs(wanted) do
        local i=index[name]
        if i then
            rows[name]={}
            for _,key in ipairs({'DamageData','ChargedDamageData','PerfectChargedDamageData'}) do rows[name][key]=M.damage(columns[key][i]) end
        end
    end
    return rows
end
function M.uniformMultiplier(unarmed,spearRows)
    assert(unarmed and unarmed.DamageData>0,'Positive native unarmed damage required')
    local ratio,count=nil,0
    for _,row in pairs(spearRows) do
        -- A single item multiplier can only preserve unarmed-level damage if it
        -- works for every active combo/charge profile. Otherwise require a
        -- different implementation; never silently ship full spear damage.
        for _,key in ipairs({'DamageData','ChargedDamageData','PerfectChargedDamageData'}) do
            local value=row[key];assert(type(value)=='number' and value>=0,'Unknown spear damage')
            if value>0 then
                local candidate=unarmed.DamageData/value
                if ratio then assert(math.abs(candidate-ratio)<1e-6,'Nonuniform native combo/charge damage requires per-attack implementation') else ratio=candidate end
                count=count+1
            end
        end
    end
    assert(ratio and count>0,'Missing native spear damage rows')
    return ratio
end
return M
