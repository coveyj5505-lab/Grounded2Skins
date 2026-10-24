-- One target per actual completed building instance, never per location/name.
local M={}
function M.new(adapter)
 local records={};local retired={}
 local function retire(record)
  if not record.retiring then record.retiring=true;adapter.retire(record) end
  retired[#retired+1]=record
 end
 local registry={}
 function registry.tick(buildings)
  local seen={}
  for _,building in ipairs(buildings) do
   if adapter.eligible(building) then
    local key=adapter.key(building);seen[key]=true
    local record=records[key]
    if record and not adapter.eligible(record.building) then retire(record);records[key]=nil;record=nil end
    if record and not adapter.valid(record.target) then records[key]=nil;record=nil end
    if not record then
     local target=adapter.create(building)
     if target then record={building=building,target=target};records[key]=record end
    end
    if record then adapter.maintain(record) end
   end
  end
  for key,record in pairs(records) do
   if not seen[key] or not adapter.eligible(record.building) then
    retire(record);records[key]=nil
   end
  end
  for i=#retired,1,-1 do
   local record=retired[i]
   if not adapter.valid(record.target) or not adapter.busy(record.target) then adapter.destroy(record);table.remove(retired,i) end
  end
 end
 function registry.target(building)
  if not adapter.eligible(building) then return end
  local record=records[adapter.key(building)]
  if record and not record.retiring and adapter.valid(record.target) then return record.target end
 end
 function registry.matches(target)
  if not adapter.valid(target) then return false end
  for _,record in pairs(records) do
   if not record.retiring and adapter.valid(record.target) and adapter.eligible(record.building) and adapter.key(record.target)==adapter.key(target) then return true end
  end
  return false
 end
 return registry
end
return M
