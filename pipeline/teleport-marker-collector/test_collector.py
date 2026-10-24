"""Exercise selection, bounds, failures and preservation without game files."""
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('marker_collector', ROOT / 'collect_markers.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Tests(unittest.TestCase):
    def fixture(self, tmp):
        root = Path(tmp)
        source = root / 'Paks/Augusta-WinGDK.utoc'
        source.parent.mkdir()
        source.write_bytes(b'original index')
        source.with_suffix('.ucas').write_bytes(b'original data')
        source.with_suffix('.pak').write_bytes(b'original pak')
        retoc = root / 'retoc.exe'
        retoc.write_bytes(b'test tool')
        return root, source, retoc

    def rows(self, extras=()):
        paths = list(m.SEEDS) + list(extras)
        return [dict(path=p + '.uasset', id=f'{i:016x}00000001', type='ExportBundleData', size=3)
                for i, p in enumerate(paths, 1)]

    def run_mock(self, root, source, retoc, rows, fail=False, info=None):
        def extract(args, **kwargs):
            if fail:
                raise RuntimeError('decode failed')
            Path(args[-1]).write_bytes(b'raw')
        with patch.object(m.subprocess, 'check_output', return_value='retoc_cli 0.1.5'), \
             patch.object(m, 'listing', return_value=rows), \
             patch.object(m.subprocess, 'run', side_effect=extract), \
             patch.object(m, 'header', return_value=info or dict(name_map=[], imported_packages=[])):
            return m.collect(retoc, source, root / 'output')

    def test_pak_selection_uses_pair_and_preserves_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            rows = self.rows(['/Game/Buildings/BP_TrailMarker', '/Game/UI/Map/UI_MapPlayerWaypoint'])
            rows += [dict(path='/Game/Art/Textures/T_TrailMarker.uasset', id='ab'*12,
                          type='ExportBundleData', size=1_000_000)]
            result = self.run_mock(root, source.with_suffix('.pak'), retoc, rows)
            self.assertEqual(result['status'], 'EXTRACTED_READ_ONLY')
            self.assertEqual(len(result['packages']), 7)
            self.assertTrue(result['source_metadata_unchanged'])
            self.assertEqual(source.read_bytes(), b'original index')
            self.assertEqual(source.with_suffix('.ucas').read_bytes(), b'original data')
            self.assertEqual(source.with_suffix('.pak').read_bytes(), b'original pak')
            with zipfile.ZipFile(root / 'output.zip') as archive:
                self.assertIsNone(archive.testzip())
                self.assertNotIn('source-index.log', archive.namelist())
                self.assertIn('marker-report.json', archive.namelist())

    def test_marker_name_discovery_excludes_art_and_unrelated_logic(self):
        for path in ['/Game/A/BP_Trail_Marker', '/Game/A/BPC_WorldLabel', '/Game/UI/UI_MapMarker', '/Game/A/BP_Waypoint']:
            self.assertTrue(m.marker_candidate(path), path)
        for path in ['/Game/Textures/T_TrailMarker', '/Game/Meshes/SM_TrailMarker', '/Game/A/BP_Player', '/Engine/BP_MapMarker']:
            self.assertFalse(m.marker_candidate(path), path)

    def test_no_marker_match_is_reported_in_partial_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            result = self.run_mock(root, source, retoc, self.rows())
            self.assertEqual(result['status'], 'PARTIAL')
            self.assertTrue(result['errors'])
            self.assertTrue((root / 'output.zip').exists())

    def test_byte_limit_does_not_extract_oversize_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            rows = self.rows(['/Game/BP_TrailMarker'])
            rows[-1]['size'] = m.MAX_BYTES + 1
            result = self.run_mock(root, source, retoc, rows)
            self.assertEqual(result['status'], 'PARTIAL')
            self.assertEqual(result['decoded_bytes'], 15)
            self.assertEqual(len(result['omitted']), 1)

    def test_package_limit_records_omissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            result = self.run_mock(root, source, retoc, self.rows(
                [f'/Game/BP_TrailMarker_{i}' for i in range(40)]))
            self.assertEqual(len(result['packages']), m.MAX_PACKAGES)
            self.assertTrue(result['omitted'])
            self.assertEqual(result['status'], 'PARTIAL')

    def test_failure_keeps_report_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            result = self.run_mock(root, source, retoc, self.rows(['/Game/BP_TrailMarker']), fail=True)
            self.assertEqual(result['status'], 'PARTIAL')
            self.assertIn('decode failed', result['errors'])
            self.assertTrue(result['source_metadata_unchanged'])
            self.assertTrue((root / 'output.zip').exists())

    def test_discovery_imports_remain_bounded_to_marker_logic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            info = dict(name_map=[], imported_packages=['/Game/A/BP_TrailMarker', '/Game/Art/T_BigTexture'])
            result = self.run_mock(root, source, retoc, self.rows(['/Game/A/BP_TrailMarker']), info=info)
            self.assertEqual(len(result['packages']), 6)
            self.assertFalse(result['missing'])

    def test_missing_seed_or_duplicate_index_is_not_success(self):
        for duplicate in [False, True]:
            with self.subTest(duplicate=duplicate), tempfile.TemporaryDirectory() as tmp:
                root, source, retoc = self.fixture(tmp)
                rows = self.rows(['/Game/BP_TrailMarker'])
                rows = rows + rows[:1] if duplicate else rows[1:]
                result = self.run_mock(root, source, retoc, rows)
                self.assertEqual(result['status'], 'PARTIAL')
                self.assertTrue(result['errors'] if duplicate else result['missing'])

    def test_refuses_overwrite_or_output_inside_paks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, source, retoc = self.fixture(tmp)
            with self.assertRaises(ValueError):
                m.collect(retoc, source, source.parent / 'output')
            (root / 'output.zip').write_bytes(b'user archive')
            with self.assertRaises(ValueError):
                m.collect(retoc, source, root / 'output')
            self.assertEqual((root / 'output.zip').read_bytes(), b'user archive')


if __name__ == '__main__':
    unittest.main()
