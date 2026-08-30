import unittest, tempfile, os
from pathlib import Path
from repro_capsule import env_snapshot, manifests, compare

class T(unittest.TestCase):
    def test_redaction_manifest_compare(self):
        old=os.environ.get('DEMO_API_KEY'); os.environ['DEMO_API_KEY']='secret-value'
        try:
            self.assertEqual(env_snapshot(True)['DEMO_API_KEY'],'<redacted>')
        finally:
            if old is None: os.environ.pop('DEMO_API_KEY',None)
            else: os.environ['DEMO_API_KEY']=old
        d=Path(tempfile.mkdtemp()); (d/'pyproject.toml').write_text('[project]\nname="x"')
        self.assertIn('pyproject.toml',manifests(d))
        self.assertEqual(compare({'system':1},{'system':2})[0]['section'],'system')

    def test_manifest_symlink_outside_repo_is_skipped(self):
        d=Path(tempfile.mkdtemp())
        outside=Path(tempfile.mktemp())
        outside.write_text('outside dependency')
        (d/'requirements.txt').symlink_to(outside)
        self.assertNotIn('requirements.txt',manifests(d))
