"""Extract bounded diagnostic evidence without publishing the original Windows log."""
import argparse, hashlib, json, re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
b=a.log.read_bytes();s=b.decode('utf-8',errors='replace');entries=re.split(r'(?=\[\d{4}-\d\d-\d\d )',s)
probe=[r.strip() for r in entries if '[ToyStoryDiscovery]' in r]
objects=[re.search(r'OBJECT ([^ ]+)',r).group(1) for r in probe if ' OBJECT ' in r]
last=probe[-1] if probe else None
report={'log_sha256':hashlib.sha256(b).hexdigest(),'log_bytes':len(b),'ue4ss_build':next((r.splitlines()[0].split('] ',1)[-1] for r in entries if 'UE4SS - v' in r),None),'probe_records':len(probe),'snapshot_begin_count':sum('SNAPSHOT BEGIN' in r for r in probe),'snapshot_end_count':sum('SNAPSHOT END' in r for r in probe),'object_classes_observed':objects,'last_probe_record':last,'evidence_scope':'Last recorded entry identifies progress, not necessarily the exact crashing operation. Log buffering may omit subsequent operations.','glide_state_captured':False,'native_failure_stage':'Character property scan' if objects and objects[-1].startswith('BP_SurvivalPlayerCharacter') and last and ' PROPERTY ' in last else 'Not localized','next_strategy':'Do not enumerate or convert arbitrary property values. Use names/type metadata only in bounded explicitly logged steps before reading whitelisted simple scalar state. Do not call event delegates or arbitrary functions.'}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['probe_records','snapshot_begin_count','snapshot_end_count','object_classes_observed','native_failure_stage']},indent=2))
