"""Offline tests: real retoc selected reads plus failure/report transport behavior."""
import importlib.util,json,os,shutil,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
folder=Path(__file__).resolve().parent/'all-four-extractor';import sys;sys.path.insert(0,str(folder));spec=importlib.util.spec_from_file_location('allfour',folder/'extract_all_four.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def row(path,cid='01'*8+'00000001',size=3):return {'path':path,'type':'ExportBundleData','id':cid,'size':size,'toc_blake3_20':'0'*40,'owner':'Augusta-WinGDK'}
class Tests(unittest.TestCase):
 def test_selection_all_four_and_exclude_textures_animations(self):
  rows=[]
  for f in m.CHARACTERS.values():
   root='/Game/_Augusta/Art/Characters/'+f+'/'
   rows += [row(root+n) for n in ['SK_Body.uasset','SK_Body_w_BackPack.uasset','SK_Body_Skeleton.uasset','Hair/SK_Hair.uasset','Textures/MI_Apparel.uasset','Textures/T_Apparel.uasset','Animation/AM_Attack.uasset']]
  groups=m.select(rows)
  for n in m.CHARACTERS:self.assertEqual(len(groups[n]['selected']),5)
 def test_legacy_physics_and_shared_master(self):
  rs=[row('/Game/Art/Characters/Player_Male01/Mesh/SK_Male_Kid_01_PhysicsAsset.uasset'),row('/Game/_Augusta/Art/Characters/Materials/MM_Character.uasset'),row('/Game/Art/Characters/Ant/SK_Ant_PhysicsAsset.uasset')];self.assertEqual(len(m.select(rs)['Shared']['selected']),2)
 def test_failed_new_container_listing_produces_upload_report(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=r/'Paks/Augusta-WinGDK.utoc';s.parent.mkdir();s.write_bytes(b'index');s.with_suffix('.ucas').write_bytes(b'data');out=r/'result'
   with patch.object(m.subprocess,'check_output',return_value='retoc_cli 0.1.5'),patch.object(m.subprocess,'run'),patch.object(m,'listing',side_effect=RuntimeError('Unsupported new TOC fixture')):
    self.assertEqual(m.collect(Path('/usr/bin/true'),s,out),2)
   report=json.loads((out/'extraction-report.json').read_text());self.assertTrue(report['source_metadata_unchanged']);self.assertIn('Unsupported new TOC fixture',report['errors'][0]);self.assertTrue((r/'result-Report.zip').exists());self.assertEqual(s.read_bytes(),b'index')
 def test_refuses_output_in_paks_and_mod_index(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=r/'Augusta-WinGDK.utoc';s.write_bytes(b'i');s.with_suffix('.ucas').write_bytes(b'd')
   with self.assertRaises(ValueError):m.collect(Path('/usr/bin/true'),s,r/'output')
   with self.assertRaises(ValueError):m.collect(Path('/usr/bin/true'),r/'zMod_P.utoc',r/'output')
 def test_all_four_one_run_transport(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=r/'Paks/Augusta-WinGDK.utoc';s.parent.mkdir();s.write_bytes(b'index');s.with_suffix('.ucas').write_bytes(b'data');rs=[]
   for i,(n,f) in enumerate(m.CHARACTERS.items(),1):
    cid=f'{i:016x}'+'00000001';rs.append(row('/Game/_Augusta/Art/Characters/'+f+'/SK_Body.uasset',cid))
   rs.append(row('/Game/_Augusta/Art/Characters/Materials/MM_Character.uasset','05'*8+'00000001'))
   def run(args,**kw):
    if args[1]=='get':Path(args[-1]).write_bytes(b'raw')
   out=r/'result'
   with patch.object(m.subprocess,'check_output',return_value='retoc_cli 0.1.5'),patch.object(m.subprocess,'run',side_effect=run),patch.object(m,'listing',return_value=rs):self.assertEqual(m.collect(Path('/usr/bin/true'),s,out),0)
   report=json.loads((out/'extraction-report.json').read_text());self.assertEqual(set(report['characters']),set(m.CHARACTERS)|{'Shared'})
   for n in m.CHARACTERS:
    with zipfile.ZipFile(r/('result-'+n+'.zip')) as z:self.assertTrue(any(p.startswith(n+'/chunks/') for p in z.namelist()));self.assertIsNone(z.testzip())
 def test_real_retoc_positive_max_and_missing_others(self):
  src=Path('/workspace/mod-work/global-stage/input');retoc=Path('/workspace/mod-work/bin/retoc')
  if not retoc.exists():self.skipTest('Local retoc integration fixture unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);paks=r/'Paks';paks.mkdir()
   for suffix in ['utoc','ucas']:shutil.copyfile(src/('zCommander101_P.'+suffix),paks/('Augusta-WinGDK.'+suffix))
   for name in ['global.utoc','global.ucas']:shutil.copyfile(src/name,paks/name)
   out=r/'AllFour';self.assertEqual(m.collect(retoc,paks/'Augusta-WinGDK.utoc',out),2);report=json.loads((out/'extraction-report.json').read_text());self.assertTrue(report['source_metadata_unchanged']);self.assertEqual(report['characters']['Max']['status'],'complete');self.assertGreater(len(report['characters']['Max']['chunks']),0);self.assertEqual(report['characters']['Hoops']['status'],'partial');self.assertEqual(len(report['global_files']),2)
   for name in ['Max','Willow','Pete','Hoops','Shared','Report']:
    with zipfile.ZipFile(r/('AllFour-'+name+'.zip')) as z:self.assertIsNone(z.testzip())
   for e in report['characters']['Max']['chunks']:self.assertEqual(m.digest(out/'Max/chunks'/e['id']),e['sha256'])
if __name__=='__main__':unittest.main()
