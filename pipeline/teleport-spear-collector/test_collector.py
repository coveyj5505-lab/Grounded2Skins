"""Bounded collector/source protection tests; native source files are not available here."""
import importlib.util,tempfile,unittest,json,zipfile,shutil
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_collector',root/'collect_native_baselines.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def fixture(self,tmp):
  r=Path(tmp);s=r/'Paks/Augusta-WinGDK.utoc';s.parent.mkdir();s.write_bytes(b'index');s.with_suffix('.ucas').write_bytes(b'data');return r,s
 def run_mock(self,r,s,rows,**kwargs):
  def run(args,**_):Path(args[-1]).write_bytes(b'raw')
  with patch.object(m.subprocess,'check_output',return_value='retoc_cli 0.1.5'),patch.object(m,'listing',return_value=rows),patch.object(m.subprocess,'run',side_effect=run),patch.object(m,'header',return_value={'name_map':[],'imported_packages':[]}):
   return m.collect('/usr/bin/true',s,r/'output')
 def rows(self):return [dict(path=p+'.uasset',id=f'{i:016x}00000001',type='ExportBundleData',size=3) for i,p in enumerate(m.TARGETS,1)]
 def test_exact_eight_and_source_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   r,s=self.fixture(tmp);rows=self.rows();rows.append(dict(path='/Game/UnrelatedTexture.uasset',id='ff'*8+'00000001',type='ExportBundleData',size=1000000));x=self.run_mock(r,s,rows)
   self.assertEqual(x['status'],'EXTRACTED_READ_ONLY');self.assertEqual(len(x['packages']),8);self.assertEqual(x['decoded_bytes'],24);self.assertTrue(x['source_metadata_unchanged']);self.assertEqual(s.read_bytes(),b'index')
   with zipfile.ZipFile(r/'output.zip') as z:self.assertIsNone(z.testzip());self.assertNotIn('source-index.log',z.namelist())
 def test_missing_package_partial_zip(self):
  with tempfile.TemporaryDirectory() as tmp:
   r,s=self.fixture(tmp);x=self.run_mock(r,s,self.rows()[:-1]);self.assertEqual(x['status'],'INCOMPLETE');self.assertEqual(len(x['missing']),1);self.assertTrue((r/'output.zip').exists())
 def test_budget_does_not_expand(self):
  with tempfile.TemporaryDirectory() as tmp:
   r,s=self.fixture(tmp);rows=self.rows();rows[0]['size']=m.MAX_BYTES+1;x=self.run_mock(r,s,rows);self.assertEqual(x['status'],'INCOMPLETE');self.assertEqual(x['decoded_bytes'],0);self.assertTrue(x['errors'])
 def test_reject_mod_or_output_in_game(self):
  with tempfile.TemporaryDirectory() as tmp:
   r,s=self.fixture(tmp)
   with self.assertRaises(ValueError):m.collect('/usr/bin/true',s,s.parent/'output')
   mod=r/'Paks/zMod_P.utoc';mod.write_bytes(b'index');mod.with_suffix('.ucas').write_bytes(b'data')
   with self.assertRaises(ValueError):m.collect('/usr/bin/true',mod,r/'output')
 def test_real_retoc_transport(self):
  original=Path('/tmp/utility-mod-updates/Teleport/original');retoc=Path('/workspace/mod-work/bin/retoc')
  if not original.exists() or not retoc.exists():self.skipTest('Offline old Teleport transport fixture absent')
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);p=r/'Paks';p.mkdir()
   for ext in ['utoc','ucas']:shutil.copyfile(original/('Xingxing_OutpostMapTeleport_905_P.'+ext),p/('Augusta-WinGDK.'+ext))
   with patch.object(m,'TARGETS',m.TARGETS[:2]):x=m.collect(retoc,p/'Augusta-WinGDK.utoc',r/'output')
   self.assertEqual(x['status'],'EXTRACTED_READ_ONLY');self.assertEqual(len(x['packages']),2);self.assertTrue(x['source_metadata_unchanged'])
if __name__=='__main__':unittest.main()
