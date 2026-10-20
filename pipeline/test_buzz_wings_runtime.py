"""Execute the wing state controller under Lua mocks; no native Unreal safety claim."""
import ast,ctypes,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
# Reuse the established component fixture without executing its crook tests.
mod=ast.parse((root/'pipeline/test_crook_carry.py').read_text());node=next(n for n in mod.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pre' for t in n.targets))
pre=ast.literal_eval(node.value.func.value)
source=(root/'runtime/BuzzWings/Scripts/main.lua').read_text()
specs=["['/Script/"+owner+':'+method+"']="+args for owner,method,args in re.findall(r"spec\('([^']+)','([^']+)',(\{[^\n]+\})\)",source)]
pre=pre.replace('SPECS',',\n'.join(specs)).replace('Key={F9=120}','Key={F6=117}')
pre=pre.replace('/Game/_BoCrook/','/Game/_BzW')
pre=pre.replace("return missingAsset and invalid or asset", "return missingAsset and invalid or obj('SkeletalMesh '..soft.SoftPath,{'Engine.SkeletalMesh'})")
pre=pre.replace("assert(v==asset);meshSet=true", "assert(v:GetFullName():find('/Game/_BzW',1,true));meshSet=true;self.asset=v:GetFullName();swaps=swaps+1")
pre=pre.replace('local events={}', 'local events={};local swaps=0;local glide=false')
pre=pre.replace("assert(b=='r_hand_JNT')", "assert(b=='chest_JNT')").replace("bone=='r_hand_JNT'", "bone=='chest_JNT'")
pre=pre.replace("/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01", "/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01")
# Wrong-character branch must now be Pete, rather than the target Max path.
pre=pre.replace("or 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01.SK_Male_Teen_01'", "or 'SkeletalMesh /Game/_Augusta/Art/Characters/Player_Male02/SK_Male_Teen_02.SK_Male_Teen_02'")
pre=pre.replace("{EquipmentComponent='ObjectProperty'}", "{EquipmentComponent='ObjectProperty',CharMovementComponent='ObjectProperty'}")
pre+='''
local movement=obj('MaineCharMovementComponent Movement',{'Maine.MaineCharMovementComponent'})
movement.IsGliding=function() return glide end;p.CharMovementComponent=movement
eq.GetItemInSlot=function() error('Wings must not inspect or modify equipment') end
'''
checks=[
 ('stored -> deployed -> stored and stable-frame no redundant swap',"key();assert(show and c.asset:find('_BzWRet0',1,true));local firstSwaps=swaps;timer();assert(swaps==firstSwaps);glide=true;timer();assert(show and c.asset:find('_BzWExt0',1,true));glide=false;timer();assert(show and c.asset:find('_BzWRet0',1,true));assert(swaps==firstSwaps+2);key();assert(destroyed==1 and not show)"),
 ('activation while already gliding',"glide=true;key();assert(show and c.asset:find('_BzWExt0',1,true))"),
 ('unknown glide value stops before component creation',"movement.IsGliding=function() return nil end;key();assert(made==0);assert(table.concat(events,'\\n'):find('RESULT ERROR',1,true))"),
 ('missing asset stops before creation',"missingAsset=true;key();assert(made==0)"),
 ('wrong player never receives wings',"female=false;key();assert(made==0)"),
 ('changing player removes wing component',"key();female=false;timer();assert(destroyed==1 and not show)"),
 ('signature mismatch prevents mutation',"bad=true;key();assert(made==0)"),
 ('glide failure removes existing cosmetic only',"key();movement.IsGliding=function() error('getter failed') end;timer();assert(destroyed==1 and not show)"),
]
lib=ctypes.CDLL('liblua5.4.so.0');lib.luaL_newstate.restype=ctypes.c_void_p;lib.luaL_openlibs.argtypes=[ctypes.c_void_p];lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];lib.lua_tolstring.restype=ctypes.c_char_p;lib.lua_close.argtypes=[ctypes.c_void_p]
for name,tail in checks:
 state=lib.luaL_newstate();lib.luaL_openlibs(state);result=lib.luaL_loadstring(state,(pre+'\n'+source+'\n'+tail).encode())
 if not result:result=lib.lua_pcallk(state,0,0,0,0,None)
 error=lib.lua_tolstring(state,-1,None) if result else None;lib.lua_close(state);assert not result,(name,error);print('PASS',name)
