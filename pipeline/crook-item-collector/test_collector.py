import importlib.util,json,shutil,struct,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('crook_collector',Path(__file__).with_name('collect_crook_items.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def chunk(classid):
 b=bytearray(132);s=[0]*15;s[1]=132;s[8]=60;s[9]=132;struct.pack_into('<15I',b,0,*s);struct.pack_into('<Q',b,92,classid);return bytes(b)
class Tests(unittest.TestCase):
 def setup_tree(self,root):
  s=root/'Paks/Augusta-WinGDK.utoc';s.parent.mkdir();s.write_bytes(b'original-index');s.with_suffix('.ucas').write_bytes(b'original-data');return s
 def mock_run(self,r,s,missing=False):
  root=m.canonical(m.ROOT);leaf=m.canonical('/Game/_Augusta/Blueprints/Items/Table_Weapons');mesh=m.canonical('/Game/Blueprints/Items/BP_NotATable')
  entries=[{'id':f'{i:016x}00000001','type':'ExportBundleData','path':p+'.uasset','size':132} for i,p in enumerate([root,leaf,mesh],1)]
  if missing:entries=entries[:1]
  def run(args,**kwargs):Path(args[-1]).write_bytes(chunk(0x4834f6301fd65d7d if args[-2]==entries[0]['id'] else 0x71e24a29987bd1ed if args[-2].startswith('0000000000000002') else 123))
  def hdr(b):return {'name_map':[],'imported_packages':[leaf,mesh] if struct.unpack_from('<Q',b,92)[0]==0x4834f6301fd65d7d else ['/Game/Art/Textures/HugeAtlas']}
  with patch.object(m.subprocess,'check_output',return_value='retoc_cli 0.1.5'),patch.object(m,'listing',return_value=entries),patch.object(m.subprocess,'run',side_effect=run),patch.object(m,'header',side_effect=hdr):return m.collect('/usr/bin/true',s,r/'result')
 def test_actual_dependency_traversal_class_filter_and_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=self.setup_tree(r);x=self.mock_run(r,s);self.assertEqual(x['status'],'EXTRACTED_READ_ONLY');self.assertEqual(len(x['packages']),2);self.assertEqual(len(x['skipped']),1);self.assertEqual(len(x['chunks']),2);self.assertEqual(x['decoded_bytes'],396);self.assertTrue(x['source_metadata_unchanged']);self.assertEqual(s.read_bytes(),b'original-index')
   with zipfile.ZipFile(r/'result.zip') as z:self.assertIsNone(z.testzip());self.assertNotIn('source-index.log',z.namelist());self.assertEqual(sum(n.startswith('chunks/') for n in z.namelist()),2)
 def test_missing_dependencies_make_useful_partial_zip(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=self.setup_tree(r);x=self.mock_run(r,s,True);self.assertEqual(x['status'],'INCOMPLETE');self.assertTrue(x['missing']);self.assertTrue((r/'result.zip').exists())
 def test_read_budget_enforced_before_extract(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=self.setup_tree(r)
   with patch.object(m,'MAX_BYTES',131):x=self.mock_run(r,s)
   self.assertEqual(x['status'],'INCOMPLETE');self.assertEqual(x['decoded_bytes'],0);self.assertTrue(x['errors'])
 def test_never_write_in_game_or_select_mod(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=self.setup_tree(r)
   with self.assertRaises(ValueError):m.collect('/usr/bin/true',s,s.parent/'new')
   mod=s.with_name('zMod.utoc');mod.write_bytes(b'x');mod.with_suffix('.ucas').write_bytes(b'x')
   with self.assertRaises(ValueError):m.collect('/usr/bin/true',mod,r/'out')
 def test_actual_parent_names_not_folder_guesses(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=self.setup_tree(r);x=self.mock_run(r,s);self.assertFalse(any('HugeAtlas' in p for p in x['missing']));self.assertEqual(len(x['packages']),2)
 def test_real_retoc_native_table_transport(self):
  folder=Path('/tmp/crook-native-item/package/mod');retoc=Path('/workspace/mod-work/bin/retoc')
  if not folder.exists():self.skipTest('Native private-table transport fixture absent')
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);s=self.setup_tree(r)
   for ext in ['utoc','ucas']:shutil.copyfile(folder/('zBoCrookNativeUE57_P.'+ext),s.with_suffix('.'+ext))
   with patch.object(m,'ROOT','/Game/Blueprints/Attacks/BoPkItemTbl'):x=m.collect(retoc,s,r/'result')
   self.assertEqual(x['status'],'EXTRACTED_READ_ONLY');self.assertEqual(len(x['packages']),1);self.assertTrue(x['source_metadata_unchanged'])
if __name__=='__main__':unittest.main()
