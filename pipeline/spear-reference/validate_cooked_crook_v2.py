"""Compare native readback to source and assert the private combat profile."""
import json,sys,hashlib
from pathlib import Path
source,decoded,out=map(Path,sys.argv[1:])
a=json.load(open(decoded/'Table_Items_Tools.json'))['Rows'];b=json.load(open(decoded/'BoPkItemTbl.json'))['Rows']
def norm(x):
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 if isinstance(x,list):return [norm(v) for v in x]
 if isinstance(x,str):return x.replace('BoPkAttacks','ItemAttacks')
 return x
c=norm(b);c['Spear']['ThrowData']['bCanThrow']=True;c['Spear']['ThrowData']['bCanThrowUnderWater']=True
assert a==c
attacks=json.load(open(decoded/'BoPkAttacks.json'))['Rows']
for n in ('Spear','Spear2','Spear3'):
 r=attacks[n];assert r['DamageData']['Damage']==8 and r['Range']==275 and r['ChargeTime']==0
 assert r['ChargedDamageData']['Damage']==0 and r['PerfectChargedDamageData']['Damage']==0
for field in ('AttackComboData','SwimmingAttackComboData'):
 handles=b['Spear'][field]['Attacks'];assert [h['RowName'] for h in handles]==['Spear','Spear2','Spear3']
 assert all(h['DataTable']['ObjectPath']=='/Game/Blueprints/Attacks/BoPkAttacks.0' for h in handles)
report=json.load(open(source/'crook-items-report.json'))
for chunk in report['chunks']:assert hashlib.sha256((source/'chunks'/chunk['id']).read_bytes()).hexdigest()==chunk['sha256']
result={'collection_status':report['status'],'collection_errors':report.get('errors',[]),'collected_chunk_hashes_verified':True,'source_rows':len(a),'private_rows':len(b),'all_decoded_source_fields_match_except_private_attack_references_and_two_throw_flags':True,'normal_damage':8,'reach':275,'charge_time':0,'throw':False,'native_packages_overridden':False,'runtime_struct_copy':False,'windows_tested':False}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
