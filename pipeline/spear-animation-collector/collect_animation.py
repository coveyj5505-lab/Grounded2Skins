"""Targeted, read-only dependency collection; original game files stay intact."""
import argparse,sys,json,zipfile
from pathlib import Path
from extract_animation_dependencies import extract
p=argparse.ArgumentParser();p.add_argument('--retoc',required=True);p.add_argument('--utoc',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output)
try:
 report=extract(a.retoc,a.utoc,out)
except Exception as e:
 out.mkdir(parents=True,exist_ok=True);report={'status':'INCOMPLETE','errors':[str(e)]};(out/'collector-error.json').write_text(json.dumps(report,indent=2))
archive=out.with_suffix('.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file() and (f.name!='source-index.log' or report['status']!='EXTRACTED_READ_ONLY'):z.write(f,f.relative_to(out))
print('UPLOAD ONE ZIP: '+str(archive),flush=True)
sys.exit(0 if report['status']=='EXTRACTED_READ_ONLY' else 2)
