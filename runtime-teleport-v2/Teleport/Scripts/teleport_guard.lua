-- Native reflection guard shared by standalone utility mods. No offsets/Reflection().
local M={}
function M.new(tag,schemas,fields)
    local function path(owner) return owner:sub(1,1)=='/' and owner or '/Script/'..owner end
    local api={};local signatures,properties,notices={},{},{}
    function api.log(s) print('['..tag..'] '..tostring(s)..'\n') end
    function api.valid(o)
        if o==nil then return false end
        local ok,v=pcall(function() return type(o.IsValid)=='function' and o:IsValid()==true end)
        return ok and v==true
    end
    function api.full(o) if api.valid(o) then return o:GetFullName() end;return 'NONE' end
    function api.isa(o,owner)
        if not api.valid(o) then return false end
        local cls=o:GetClass()
        for _=1,24 do
            if not api.valid(cls) then break end
            if cls:GetFullName():match('^[^ ]+ (.+)$')==path(owner) then return true end
            cls=cls:GetSuperStruct()
        end
        return false
    end
    function api.unwrap(o)
        if o==nil then return nil end
        if type(o)~='table' and type(o)~='userdata' then return o end
        local t=type(o.type)=='function' and o:type() or nil
        if t=='RemoteUnrealParam' or t=='LocalUnrealParam' then return o:get() end
        return o
    end
    local function kind(owner,name)
        local key=owner..'.'..name
        if properties[key]~=nil then return properties[key] end
        local cls=StaticFindObject(path(owner));assert(api.valid(cls),'Missing field class '..owner)
        local found=false;local n=0
        cls:ForEachProperty(function(p)
            n=n+1;if n>1024 then return true end
            local typ,leaf=p:GetFullName():match('^(%S+)%s+.*:([^:]+)$')
            if leaf==name then found=typ;return true end
        end)
        properties[key]=found;return found
    end
    local function fieldCheck(o,name)
        local f=assert(fields[name],'Unapproved field '..name)
        assert(api.isa(o,f.owner),'Wrong field receiver '..name)
        assert(kind(f.owner,name)==f.type,'Rejected field schema '..f.owner..'.'..name)
    end
    function api.field(o,name) fieldCheck(o,name);return o[name] end
    function api.write(o,name,value)
        fieldCheck(o,name)
        local expected=fields[name].type
        assert(expected=='BoolProperty' and type(value)=='boolean' or expected=='FloatProperty' and type(value)=='number' and value==value and math.abs(value)<math.huge,'Rejected field value '..name)
        o[name]=value;assert(o[name]==value,'Field write readback mismatch '..name)
    end
    function api.check(o,owner,method)
        local key=owner..'.'..method;local expected=assert(schemas[key],'Unapproved function '..key)
        assert(api.isa(o,owner),'Wrong function receiver '..key)
        if signatures[key]==nil then
            local func=StaticFindObject(path(owner)..':'..method);local actual={};local count=0
            assert(api.valid(func),'Missing function '..key)
            func:ForEachProperty(function(p)
                count=count+1;if count>16 then return true end
                local t,n=p:GetFullName():match('^(%S+)%s+.*:([^:]+)$');if t and n then actual[n]=t end
            end)
            local required=0;local ok=count<=16
            for n,t in pairs(expected) do required=required+1;if not actual[n] or not ('|'..t..'|'):find('|'..actual[n]..'|',1,true) then ok=false end end
            signatures[key]=ok and count==required
            api.log((signatures[key] and 'SCHEMA OK ' or 'SCHEMA REJECTED ')..key)
        end
        assert(signatures[key],'Rejected function schema '..key)
    end
    function api.call(o,owner,method,...)
        api.check(o,owner,method)
        return o[method](o,...)
    end
    function api.once(key,message) if not notices[key] then notices[key]=true;api.log(message) end end
    return api
end
return M
