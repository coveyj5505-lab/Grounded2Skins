-- Read-only installation receipt; this does not claim a file was mounted.
local M={}
local expected={
{name='Buzz',stem='zBuzzSkinV3UE57_99_P',head='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d08000000900000000f000000460100000c000000000000002000000000000100d003000001000000d2759f5447f325e4',sizes={pak=339,utoc=5722,ucas=20654410}},
{name='Woody',stem='zWoodySkinV3UE57_99_P',head='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d080000009000000015000000c80100000c0000000000000020000000000001001e05000001000000bb4c7319c6c110a1',sizes={pak=339,utoc=7892,ucas=28877945}},
{name='Jessie',stem='zJessieSkinV3UE57_99_P',head='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d080000009000000010000000f90000000c0000000000000020000000000001002e040000010000008a3057c92233f26b',sizes={pak=339,utoc=4938,ucas=15515703}},
{name='Crook',stem='zBoCrookHandV3UE57_99_P',head='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d080000009000000004000000090000000c000000000000002000000000000100b50100000100000047c6d493028fdaf2',sizes={pak=339,utoc=873,ucas=497106}},
{name='BoPeep',stem='zBoPeepSkinV3UE57_99_P',head='2d3d3d2d2d3d3d2d2d3d3d2d2d3d3d2d080000009000000011000000ee0000000c0000000000000020000000000001004e04000001000000233031d2e269fd64',sizes={pak=339,utoc=4884,ucas=14796144}},
}
local old={'zBuzzSkinV2UE57_P','zBoPeepSkinV2UE57_P','zWoodySkinV2UE57_P','zJessieSkinV2UE57_P','zBuzzUE57_P','zBoPeepUE57_P','zWoodyUE57_P','zJessieUE57_P','zBoCrookUE57_P','zBoCrookHandV2UE57_P'}
function M.run(log)
 if not io or type(io.open)~='function' then log('BUILD RECEIPT unavailable: file I/O disabled');return end
 local dirs={'../../Content/Paks/','Augusta/Content/Paks/','../../../Augusta/Content/Paks/'}
 for _,item in ipairs(expected) do
  local matched=false
  for _,dir in ipairs(dirs) do
   local f=io.open(dir..item.stem..'.utoc','rb')
   if f then
    local b=f:read(64);f:close();local hex=b and b:gsub('.',function(c)return string.format('%02x',string.byte(c))end) or '';local good=hex==item.head
    for _,ext in ipairs({'pak','utoc','ucas'}) do
     local input=io.open(dir..item.stem..'.'..ext,'rb');local size=input and input:seek('end') or nil;if input then input:close() end
     good=good and size==item.sizes[ext]
    end
    log('BUILD RECEIPT '..item.name..': '..(good and 'FILES MATCH V3' or 'MISSING/MISMATCHED TRIO')..'; '..dir..item.stem..'; file presence is not mount proof')
    matched=true;break
   end
  end
  if not matched then log('BUILD RECEIPT '..item.name..': MISSING '..item.stem..' trio') end
 end
 for _,stem in ipairs(old) do
  for _,dir in ipairs(dirs) do
   local f=io.open(dir..stem..'.utoc','rb')
   if f then f:close();log('BUILD RECEIPT OLD REPLACEMENT PRESENT: '..dir..stem..'; move its trio outside Paks');break end
  end
 end
end
return M

