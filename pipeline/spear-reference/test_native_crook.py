"""Run production native-crook Lua with native reference/lifecycle fixtures.
This does not emulate Unreal networking, saving, rendering or montage playback.
"""
import ctypes
from pathlib import Path
root=Path(__file__).resolve().parents[2]
scripts=root/'runtime-native-spear-next/BoPeepNativeSpear/Scripts'
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p
for n,a in {'luaL_openlibs':[ctypes.c_void_p],'luaL_loadstring':[ctypes.c_void_p,ctypes.c_char_p],'lua_pcallk':[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p],'lua_close':[ctypes.c_void_p]}.items():getattr(lib,n).argtypes=a
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p
fixture=r'''
local thread=false
local function object(full,class)
 return {full=full,class=class,IsValid=function(s) return not s.dead end,GetFullName=function(s) return s.full end}
end
local function array(t)
 t.ForEach=function(self,fn) for i,v in ipairs(self) do if fn(i,{get=function() return v end})==true then break end end end
 return t
end
local function copy(t)
 if type(t)~='table' then return t end
 if t.full then return t end
 local n={};for k,v in pairs(t) do n[k]=copy(v) end;return n
end
FName=function(n) return {ToString=function() return n end} end
local function name(n) return type(n)=='string' and n or n:ToString() end
local logs={};local api={}
function api.log(s) logs[#logs+1]=s end
function api.valid(o) return o~=nil and o.IsValid and o:IsValid() or false end
function api.full(o) return api.valid(o) and o.full or 'NONE' end
local parents={['Maine.SurvivalPlayerCharacter']={['Maine.SurvivalCharacter']=true,['Engine.Actor']=true},['Engine.PlayerController']={['Engine.Controller']=true},['Engine.SkeletalMeshComponent']={['Engine.SceneComponent']=true,['Engine.PrimitiveComponent']=true},['Engine.StaticMeshComponent']={['Engine.SceneComponent']=true,['Engine.PrimitiveComponent']=true}}
function api.isa(o,c) return api.valid(o) and (o.class==c or parents[o.class] and parents[o.class][c]) or false end
function api.field(o,k) assert(thread);assert(api.valid(o));return o[k] end
function api.check(o,owner,method) assert(thread and api.isa(o,owner) and type(o[method])=='function') end
function api.structFields(owner,fields) assert(thread);assert(owner and next(fields)) end
function api.unwrap(v) return v.get and v:get() or v end
function api.call(o,owner,method,...) assert(thread,'Native call off game thread');assert(api.isa(o,owner),'Bad receiver '..owner..':'..method);assert(type(o[method])=='function','Missing '..method);return o[method](o,...) end
local module=assert(load(ROWS))()
local nativeAttacks=object('DataTable /Game/Blueprints/Attacks/ItemAttacks.ItemAttacks')
local attackTable=object('DataTable '..module.attacks)
function attackTable:GetRowStruct() return object('ScriptStruct /Script/Maine.AttackData') end
local badDamage=false
function attackTable:FindRow(n) return {DamageData={Damage=badDamage and 20 or 8},Range=275,ChargeTime=0} end
local function combo(names)
 local a={};for _,n in ipairs(names) do a[#a+1]={DataTable=nativeAttacks,RowName=FName(n)} end
 return {Attacks=array(a),bLoop=true,ScalingType={TagName=FName('Spear.Scaling')}}
end
local native={AttackComboData=combo({'Spear','Spear2','Spear3'}),AlternateAttackComboData=combo({}),SwimmingAttackComboData=combo({}),ThrowData={bCanThrow=true,bCanThrowUnderWater=true},untouched={a=1,b={2,3}}}
local source=object('CompositeDataTable '..module.source)
function source:GetRowStruct() return object('ScriptStruct /Script/Maine.BaseItemData') end
function source:FindRow(n) assert(n=='Spear');return native end
local items=object('DataTable '..module.items);local added={};local removes=0;local wrongStruct=false
function items:GetRowStruct() return object('ScriptStruct /Script/Maine.'..(wrongStruct and 'AttackData' or 'BaseItemData')) end
function items:FindRow(n) return added[n] end
function items:AddRow(n,row) assert(not added[n]);added[n]=copy(row) end
function items:RemoveRow(n) added[n]=nil;removes=removes+1 end
local function prepare() thread=true;local ok,h=pcall(module.prepare,source,items,attackTable,api);thread=false;return ok,h end
'''
main_fixture=r'''
local key,poll;local creates,equips,removed,assigned,finished,attached=0,0,0,0,0,0
local host=true;local character=true;local charge=false;local badRange=false;local badMultiplier=false;local privateCached=true;local bindFailure=false;local desiredMain,desiredOff=nil,nil
local global={}
global[module.source]=source;global[module.items]=items;global[module.attacks]=attackTable
local crookmesh=object('SkeletalMesh /Game/_BoCrTP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01')
global['/Game/_BoCrTP1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01']=crookmesh
local body=object('Body','Engine.SkeletalMeshComponent')
function body:GetSkeletalMeshAsset() return object('SkeletalMesh '..(character and '/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01' or '/Game/Other.Other')) end
local eq=object('Equipment','Maine.EquipmentComponent')
function eq:GetItemInSlot(s) if s==17 then return desiredMain else assert(s==29);return desiredOff end end
function eq:ServerEquipItem(item,a,b,c,d) assert(a==false and b==false and c==false and d==false);equips=equips+1;desiredMain=item end
function eq:ServerRemoveItem(item,count) assert(count==1 and desiredMain==item);removed=removed+1;desiredMain=nil end
local pawn=object('Pawn','Maine.SurvivalPlayerCharacter');pawn.Mesh=body;pawn.EquipmentComponent=eq
function pawn:HasAuthority() return host end
local pc=object('PC','Engine.PlayerController')
function pc:IsLocalController() return true end
function pc:K2_GetPawn() return pawn end
local function primitive(o)
 o.bRenderInMainPass=true;o.bRenderInDepthPass=true;o.CastShadow=true;o.bOnlyOwnerSee=false;o.bOwnerNoSee=false;o.bHiddenInGame=false;o.visible=true
 function o:IsVisible() return self.visible end
 function o:SetVisibility(v,propagate) assert(propagate==false);self.visible=v end
 function o:SetHiddenInGame(v,propagate) assert(propagate==false);self.bHiddenInGame=v end
 function o:SetOnlyOwnerSee(v) self.bOnlyOwnerSee=v end
 function o:SetOwnerNoSee(v) self.bOwnerNoSee=v end
 function o:SetRenderInMainPass(v) self.bRenderInMainPass=v end
 function o:SetRenderInDepthPass(v) self.bRenderInDepthPass=v end
 function o:SetCastShadow(v) self.CastShadow=v end
 return o
end
local smc=primitive(object('NativeSpearSMC','Engine.StaticMeshComponent'));smc.StaticMesh=object('StaticMesh /Game/Art/Items/Weapons/Spear02/Spear02.Spear02')
local visual=object('NativeEquippedActor','Engine.Actor');local proxies={}
function visual:K2_GetComponentsByClass(cls) assert(cls==global['/Script/Engine.StaticMeshComponent']);return array({smc}) end
function visual:AddComponentByClass(cls,manual,t,deferred)
 assert(cls==global['/Script/Engine.SkeletalMeshComponent'] and manual and deferred)
 local p=primitive(object('Proxy'..(#proxies+1),'Engine.SkeletalMeshComponent'));proxies[#proxies+1]=p
 function p:SetCollisionEnabled(v) assert(v==0);self.noCollision=true end
 function p:SetSimulatePhysics(v) assert(v==false);self.noPhysics=true end
 function p:SetDisablePostProcessBlueprint(v) assert(v) end
 function p:SetEnableAnimation(v) assert(v==false) end
 function p:SetAllowClothActors(v) assert(v==false);assert(not bindFailure,'simulated component configuration failure') end
 function p:SetSkeletalMeshAsset(v) assert(not self.registered,'Registered mesh reassignment!');assert(v==crookmesh);assigned=assigned+1 end
 function p:K2_AttachToComponent(parent,socket,l,r,s,weld) assert(parent==smc and name(socket)=='None' and l==2 and r==2 and s==2 and weld==false);attached=attached+1;return true end
 function p:K2_SetRelativeTransform(t,sweep,hit,teleport) assert(t.Scale3D.X==1.35 and t.Scale3D.Y==1.35 and t.Translation.Z>18 and sweep==false and teleport==true);self.fit=t end
 return p
end
function visual:FinishAddComponent(p,manual,t) assert(not p.registered and manual);p.registered=true;finished=finished+1 end
local item=object('PrivateItem','Maine.Item')
function item:GetItemDataRowHandle() return {DataTable=items,RowName=FName(module.row)} end
function item:GetItemVisuals() return visual end
function item:GetAttackDamageModifier() return badMultiplier and .4 or 1 end
function item:CanThrow() return false end
local attacks={}
for i,n in ipairs({'Spear','Spear2','Spear3'}) do
 local a=object('Attack'..i,'Maine.Attack')
 function a:GetAttackDataRowHandle() return {DataTable=privateCached and attackTable or nativeAttacks,RowName=FName(n)} end
 function a:GetAttackRange() return badRange and 150 or 275 end
 function a:CanCharge() return charge end
 attacks[#attacks+1]=a
end
item.AttackCombo=object('Combo','Maine.AttackCombo');item.AttackCombo.Attacks=array(attacks)
local statics=object('Statics','Maine.SurvivalGameplayStatics')
function statics:CreateItem(world,handle) assert(world==pawn and handle.DataTable==items and name(handle.RowName)==module.row);creates=creates+1;return item end
global['/Script/Maine.Default__SurvivalGameplayStatics']=statics
global['/Script/Engine.StaticMeshComponent']=object('SMCClass');global['/Script/Engine.SkeletalMeshComponent']=object('SKCClass')
for _,spec in ipairs({{'Maine.EEquipmentSlot',{MainHand=17,OffHand=29}},{'Engine.ECollisionEnabled',{NoCollision=0}},{'Engine.EAttachmentRule',{SnapToTarget=2}}}) do
 local e=object('Enum');function e:ForEachName(fn) for n,v in pairs(spec[2]) do fn(FName(n),v) end end;global['/Script/'..spec[1]]=e
end
function StaticFindObject(path) return global[path] end
function FindAllOf(cls) assert(cls=='PlayerController');return {pc} end
Key={F10=121};function RegisterKeyBind(k,fn) assert(k==Key.F10);key=fn end
function ExecuteInGameThread(fn) assert(not thread);thread=true;fn();thread=false end
function LoopAsync(ms,fn) assert(ms==100);poll=fn end
package.preload.item_rows=function() return module end
package.preload.crook_guard=function() return {new=function() return api end} end
assert(load(MAIN))()
local function tick() poll() end
local function press() key() end
local function hasLog(s) for _,l in ipairs(logs) do if l:find(s,1,true) then return true end end;return false end
'''
cases={
 'typed deep copy preserves source and native row data': "local ok,h=prepare();assert(ok,h);assert(h.DataTable==items and name(h.RowName)==module.row);local p=added[module.row];assert(p.AttackComboData~=native.AttackComboData and p.untouched.b~=native.untouched.b and p.untouched.b[2]==3);assert(p.ThrowData.bCanThrow==false and native.ThrowData.bCanThrow==true);for i,v in ipairs(p.AttackComboData.Attacks) do assert(v.DataTable==attackTable and native.AttackComboData.Attacks[i].DataTable==nativeAttacks) end;assert(p.AttackComboData.bLoop and name(p.AttackComboData.ScalingType.TagName)=='Spear.Scaling')",
 'wrong native row struct rejected before copy': "wrongStruct=true;local ok=prepare();assert(not ok and next(added)==nil)",
 'wrong damage rejected before copy': "badDamage=true;local ok=prepare();assert(not ok and next(added)==nil)",
 'unsupported alternate attack removes unpublished private row': "native.AlternateAttackComboData=combo({'SpearThrow'});local ok=prepare();assert(not ok and next(added)==nil and removes==1);assert(native.AttackComboData.Attacks[1].DataTable==nativeAttacks)",
 'published private row never overwritten': "assert(prepare());local old=added[module.row];assert(not prepare());assert(added[module.row]==old and removes==0)",
 'unexpected combo size rejected with rollback': "native.AttackComboData=combo({'Spear'});assert(not prepare());assert(next(added)==nil and removes==1)",
 'swimming spear rows receive private normal-only data': "native.SwimmingAttackComboData=combo({'Spear'});assert(prepare());assert(added[module.row].SwimmingAttackComboData.Attacks[1].DataTable==attackTable and native.SwimmingAttackComboData.Attacks[1].DataTable==nativeAttacks)",
}
main_cases={
 'no automatic item creation; native combo and weapon frame on F10': "tick();assert(creates==0 and hasLog('READY'));press();assert(creates==1 and equips==1 and assigned==1 and finished==1 and attached==1 and hasLog('ITEM VERIFIED') and hasLog('BOUND TO NATIVE WEAPON'));assert(desiredMain==item and smc.bRenderInMainPass==false and proxies[1].noCollision and proxies[1].noPhysics)",
 'offhand item never displaced': "tick();desiredOff=object('Shield','Maine.Item');press();assert(creates==0 and equips==0 and desiredOff.full=='Shield');desiredOff=nil;press();assert(equips==1)",
 'ordinary spear never displaced': "tick();desiredMain=object('OrdinarySpear','Maine.Item');function desiredMain:GetItemDataRowHandle() return {DataTable=source,RowName=FName('Spear')} end;press();assert(creates==0 and equips==0 and removed==0)",
 'client never creates or locally equips': "host=false;tick();press();assert(creates==0 and equips==0 and removed==0)",
 'other characters are untouched': "character=false;tick();press();assert(creates==0 and equips==0 and removed==0)",
 'charge-enabled native cache is removed before input returns': "tick();charge=true;press();assert(equips==1 and removed==1 and desiredMain==nil and assigned==0 and hasLog('STOPPED SAFELY'))",
 'wrong attack table in cache removed': "tick();privateCached=false;press();assert(removed==1 and desiredMain==nil and assigned==0)",
 'wrong native reach removed': "tick();badRange=true;press();assert(removed==1 and desiredMain==nil and assigned==0)",
 'double damage multiplier rejected and item removed': "tick();badMultiplier=true;press();assert(removed==1 and desiredMain==nil and assigned==0)",
 'native view visibility follows without registered mesh reassignment': "tick();press();for i=1,8 do smc.bHiddenInGame=i%2==1;smc.bOwnerNoSee=i%2==0;tick();assert(proxies[1].visible==not smc.bHiddenInGame and proxies[1].bOwnerNoSee==smc.bOwnerNoSee) end;assert(assigned==1 and finished==1 and attached==1)",
 'remove restores native rendering; persistent proxy reused': "tick();press();press();assert(removed==1 and desiredMain==nil and smc.bRenderInMainPass and smc.bRenderInDepthPass and smc.CastShadow and not proxies[1].visible);press();assert(equips==2 and assigned==1 and finished==1 and attached==1 and proxies[1].visible)",
 'native equipment change restores render without altering replacement': "tick();press();desiredMain=object('Axe','Maine.Item');function desiredMain:GetItemDataRowHandle() return {DataTable=source,RowName=FName('Axe')} end;tick();assert(smc.bRenderInMainPass and not proxies[1].visible and removed==0 and desiredMain.full=='Axe')",
 'component configuration failure rolls back equipped item': "tick();bindFailure=true;press();assert(removed==1 and desiredMain==nil and smc.bRenderInMainPass and not proxies[1].visible and assigned==0 and hasLog('ROLLBACK:'))",
 'new native view component gets one deferred proxy; old view restores': "tick();press();local old=smc;smc=primitive(object('SecondNativeSpearSMC','Engine.StaticMeshComponent'));smc.StaticMesh=old.StaticMesh;tick();assert(assigned==2 and finished==2 and attached==2 and old.bRenderInMainPass and not smc.bRenderInMainPass and not proxies[1].visible and proxies[2].visible);for i=1,4 do tick() end;assert(assigned==2 and finished==2)",
 'lost proxy can be replaced without losing original native render state': "tick();press();proxies[1].dead=true;tick();assert(assigned==2 and finished==2 and attached==2);press();assert(smc.bRenderInMainPass and smc.bRenderInDepthPass and smc.CastShadow and not proxies[2].visible)",
}
guard_fixture=r'''
local delimiter='.';local propertyType='ArrayProperty'
local metadata=object('ScriptStruct /Script/Maine.AttackComboData')
function metadata:ForEachProperty(fn)
 fn({GetFullName=function() return propertyType..' /Script/Maine.AttackComboData'..delimiter..'Attacks' end})
end
function StaticFindObject(path) assert(path=='/Script/Maine.AttackComboData');return metadata end
local checked=assert(load(GUARD))().new('NativeCrookFixture',{}, {})
'''
guard_cases={
 'actual guard accepts dotted native struct property metadata': "checked.structFields('Maine.AttackComboData',{Attacks='ArrayProperty'})",
 'actual guard accepts colon native struct property metadata': "delimiter=':';checked.structFields('Maine.AttackComboData',{Attacks='ArrayProperty'})",
 'actual guard rejects changed native field kind': "propertyType='ObjectProperty';assert(not pcall(checked.structFields,'Maine.AttackComboData',{Attacks='ArrayProperty'}))",
}
for title,test in list(cases.items())+list(main_cases.items())+list(guard_cases.items()):
 code=fixture.replace('ROWS','[====['+(scripts/'item_rows.lua').read_text()+']====]')
 if title in main_cases:code+='\n'+main_fixture.replace('MAIN','[====['+(scripts/'main.lua').read_text()+']====]')
 if title in guard_cases:code+='\n'+guard_fixture.replace('GUARD','[====['+(scripts/'crook_guard.lua').read_text()+']====]')
 code+='\n'+test
 state=lib.luaL_newstate();lib.luaL_openlibs(state)
 try:
  result=lib.luaL_loadstring(state,code.encode())
  if not result:result=lib.lua_pcallk(state,0,0,0,0,None)
  if result:raise AssertionError(title+': '+lib.lua_tolstring(state,-1,None).decode())
  print('PASS',title)
 finally:lib.lua_close(state)
print(f'{len(cases)+len(main_cases)+len(guard_cases)} production-Lua groups passed; Windows native execution remains unverified')
