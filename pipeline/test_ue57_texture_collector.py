"""Read-only collector transport tests; no Windows/game compatibility claim."""
import importlib.util,sys,tempfile,json,zipfile,unittest
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parent/'ue57-texture-extractor';sys.path.insert(0,str(root));spec=importlib.util.spec_from_file_location('texturecollect',root/'collect_textures.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_success_four_headers_and_bulk(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'Paks/Augusta-WinGDK.utoc';source.parent.mkdir();source.write_bytes(b'index');source.with_suffix('.ucas').write_bytes(b'bulk');rows=[]
   for i,t in enumerate(m.TARGETS,1):
    for suffix,kind in [('00000001','ExportBundleData'),('00000002','BulkData')]:rows.append({'id':f'{i:016x}'+suffix,'path':t+('.uasset' if suffix.endswith('1') else '.ubulk'),'type':kind,'size':3})
   def run(args,**kw):Path(args[-1]).write_bytes(b'raw')
   out=root/'Textures'
   with patch.object(m,'listing',return_value=rows),patch.object(m.subprocess,'check_output',return_value='retoc_cli 0.1.5'),patch.object(m.subprocess,'run',side_effect=run):self.assertEqual(m.collect('/usr/bin/true',source,out),0)
   r=json.loads((out/'texture-report.json').read_text());self.assertEqual(len(r['packages']),4);self.assertEqual(len(r['chunks']),8);self.assertTrue(r['source_size_and_mtime_unchanged']);self.assertEqual(source.read_bytes(),b'index')
   with zipfile.ZipFile(out.with_suffix('.zip')) as z:self.assertIsNone(z.testzip());self.assertIn('texture-report.json',z.namelist());self.assertEqual(len([n for n in z.namelist() if n.startswith('chunks/')]),8)
 def test_failure_report_survives(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'Paks/Augusta-WinGDK.utoc';source.parent.mkdir();source.write_bytes(b'i');source.with_suffix('.ucas').write_bytes(b'b');out=root/'Textures'
   with patch.object(m,'listing',side_effect=RuntimeError('fixture listing failure')),patch.object(m.subprocess,'check_output',return_value='retoc_cli 0.1.5'):self.assertEqual(m.collect('/usr/bin/true',source,out),2)
   with zipfile.ZipFile(out.with_suffix('.zip')) as z:self.assertIn('fixture listing failure',z.read('texture-report.json').decode())
 def test_output_protection(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'Augusta-WinGDK.utoc';source.write_bytes(b'i');source.with_suffix('.ucas').write_bytes(b'b')
   with self.assertRaises(ValueError):m.collect('/usr/bin/true',source,root/'out')
if __name__=='__main__':unittest.main()
